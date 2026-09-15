"""Persistent scan geometry, continuous focus handoffs and public controls."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from yautja.analysis import AnalysisHUD
from yautja.analysis_target import AnalysisTarget
from yautja.cli import extra_report, main, parser
from yautja.render import Renderer
from yautja.semantic import Subject


class AnalysisTargetTests(unittest.TestCase):
    size = (320, 180)

    def subjects(self):
        result = []
        for track, (left, right, top) in enumerate(((30, 110, 20), (225, 285, 45)), 1):
            mask = np.zeros(self.size[::-1], np.float32)
            mask[top:170, left:right] = 1
            result.append(Subject(mask, 'person', .9, track_id=track))
        return result

    def renderer(self, **options):
        return Renderer(*self.size, **dict(dict(look_preset='fremont', analysis=False, glow=0,
                        hud_opacity=0, hud_opacity_elements='analysis-target-fill=1,analysis-target=1'), **options))

    def test_translucent_disk_and_dark_marks_preserve_scene_at_fixed_size(self):
        renderer = self.renderer(scene_mode='thermal', palette='white-hot')
        targets = renderer.analysis.target
        images = []
        for time in (0, .1, .5, 1., 3.):
            image = Image.new('RGB', self.size, (200, 100, 60))
            renderer.analysis.draw(renderer, image, [], time, 0)
            self.assertAlmostEqual(targets.radius, 180 * .36 / 2)
            self.assertGreater(np.count_nonzero(np.asarray(image) != [200, 100, 60]), 1000)
            images.append(image)
        pixels = np.asarray(images[0])
        # Away from the crosshair: native alpha 0.4, never an opaque replacement.
        expected = np.rint(.6 * np.array([200, 100, 60]) + .4 * np.array([143, 161, 176]))
        np.testing.assert_allclose(pixels[97, 168], expected, atol=1)
        self.assertLess(pixels[90, 160].max(), 60)
        np.testing.assert_array_equal(pixels[0, 0], [200, 100, 60])

    def test_exact_spring_is_frame_rate_independent_and_response_has_time_units(self):
        end = []
        for fps in (12, 24, 60):
            target = AnalysisTarget(response=.6)
            target.advance((.2, .5), 0, 0, self.size)
            for index in range(1, fps + 1):
                target.advance((.8, .5), index / fps, 0, self.size)
            end.append(target.position)
        np.testing.assert_allclose(end, [end[0]] * 3, atol=1e-12)
        target = AnalysisTarget(response=.6)
        target.advance((.2, .5), 0, 0, self.size)
        at_response = target.advance((.8, .5), .6, 0, self.size)
        self.assertAlmostEqual((at_response[0] - .2) / .6, .95, places=3)

    def test_focus_handoff_keeps_position_and_velocity_continuous(self):
        target = AnalysisTarget()
        target.advance((.2, .5), 0, 0, self.size)
        target.advance((.8, .5), .2, 0, self.size)
        position, velocity = target.position.copy(), target.velocity.copy()
        target.advance((.3, .3), .2, 0, self.size)
        np.testing.assert_allclose(target.position, position)
        np.testing.assert_allclose(target.velocity, velocity)
        target.advance((.3, .3), .200001, 0, self.size)
        self.assertLess(np.linalg.norm(target.position-position), 1e-5)
        self.assertLess(np.linalg.norm(target.velocity-velocity), .001)

    def test_single_shared_focus_visits_next_subject_and_persists_through_search_and_loss(self):
        r, subjects = self.renderer(), self.subjects()
        frame = Image.new('RGB', self.size)
        positions, tracks = [], []
        for index in range(100):
            time = index / 12
            # An explicit empty legacy target list does not suppress this scanner.
            image = r.render(frame, time, subjects=subjects, targets=[])
            self.assertGreater(np.asarray(image).sum(), 0)
            positions.append(r.analysis.target.position.copy())
            tracks.append(r.analysis.selected)
        self.assertEqual(tracks[30], 1)
        self.assertIsNone(tracks[75])
        self.assertEqual(tracks[90], 2)
        self.assertLess(positions[50][0], .25)
        self.assertGreater(positions[99][0], .75)
        self.assertLess(np.max(np.linalg.norm(np.diff(positions, axis=0), axis=1)), .16)
        for time in (8.4, 8.5, 9):
            self.assertGreater(np.asarray(r.render(frame, time, subjects=[])).sum(), 0)
            self.assertEqual(r.analysis.phase, 'SEARCH')

    def test_cut_rewind_and_still_reset_without_acquisition_and_freeze_is_stable(self):
        r, subjects = self.renderer(), self.subjects()
        frame = Image.new('RGB', self.size)
        initial = r.render(frame, 0, subjects=subjects)
        r.render(frame, 2, subjects=subjects)
        cut = r.render(frame, 3, subjects=subjects, shot_id=2)
        self.assertEqual(cut.tobytes(), initial.tobytes())
        rewind = r.render(frame, 0, subjects=subjects, shot_id=2)
        self.assertEqual(rewind.tobytes(), initial.tobytes())
        r.render(frame, 0, subjects=subjects, target_static=True)
        self.assertEqual(r.analysis.selected, 1)
        self.assertLess(r.analysis.target.position[0], .25)
        frozen = self.renderer(analysis_speed=0)
        self.assertEqual(frozen.render(frame, 0).tobytes(), frozen.render(frame, 5).tobytes())

    def test_circle_stays_in_frame_in_portrait_landscape_and_tiny_outputs(self):
        for size in ((960, 540), (540, 960), (128, 72), (72, 128)):
            target = AnalysisTarget(size=.8, response=0)
            for destination in ((0, 0), (1, 1), (0, 1), (1, 0)):
                target.advance(destination, 0, 0, size)
                center = target.position * size
                self.assertTrue(np.all(center-target.radius >= -1e-10))
                self.assertTrue(np.all(center+target.radius <= np.array(size)+1e-10))

    def test_controls_are_independent_and_hud_off_is_effective_in_report(self):
        frame, subjects = Image.new('RGB', self.size), self.subjects()
        for key in ('analysis-target-fill', 'analysis-target'):
            r = self.renderer(hud_colors=f'{key}=#00FF00', hud_opacity_elements=f'{key}=1',
                              neon=True, neon_elements=f'{key}=.5', hud_blur_elements=f'{key}=2')
            image = np.asarray(r.render(frame, 0, subjects=subjects, target_static=True))
            self.assertGreater(image[..., 1].sum(), image[..., 0].sum())
            for options in (dict(hud=False), dict(analysis_target=False), dict(hud_opacity_elements=f'{key}=0')):
                hidden = self.renderer(**options).render(frame, 0, subjects=subjects, target_static=True)
                self.assertEqual(np.asarray(hidden).sum(), 0)
        report = extra_report(self.renderer(hud=False), None)
        self.assertFalse(report['analysis_target'])
        self.assertEqual(report['analysis_phase'], 'OFF')
        self.assertIsNone(report['analysis_target_position'])
        report = extra_report(r, None)
        self.assertFalse(report['analysis'])
        self.assertTrue(report['analysis_target'])
        self.assertEqual(report['analysis_track'], 1)

    def test_portable_schema_and_explicit_options_override_in_either_order(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'scan.json'
            with patch('sys.stdout', new_callable=io.StringIO):
                self.assertEqual(main(['--stylepreset', 'fremont', '--analysis-target-size', '.5',
                                       '--analysis-target-response', '.9', '--save-preset', str(path)]), 0)
            data = json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(data['schema_version'], 1)
            self.assertTrue(data['settings']['analysis_target'])
            for flags in (['--no-analysis-target', '--preset-file', str(path)],
                          ['--preset-file', str(path), '--no-analysis-target']):
                args = parser().parse_args(flags)
                self.assertFalse(args.analysis_target)
                self.assertEqual(args.analysis_target_size, .5)
                self.assertEqual(args.analysis_target_response, .9)
            for style in ('focus', 'relic', 'murphy', 'netrunner'):
                self.assertFalse(parser().parse_args(['--stylepreset', style]).analysis_target)

    def test_invalid_controls_and_classic_mode_fail_before_opening_media(self):
        for options in ({'analysis_target_size': .09}, {'analysis_target_size': float('nan')},
                        {'analysis_target_response': -1}, {'analysis_target_response': float('inf')}):
            with self.assertRaisesRegex(ValueError, 'analysis-target'):
                AnalysisHUD(**options)
        with patch('sys.stderr', new_callable=io.StringIO), patch('yautja.cli.convert') as convert:
            with self.assertRaises(SystemExit):
                main(['missing.mp4', 'out.mp4', '--thermal', 'classic', '--analysis-target'])
            convert.assert_not_called()
