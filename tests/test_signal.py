"""Cyber glyph selection, source scenes, mask clipping, and temporal code motion."""
import io
import importlib.util
import json
from importlib.resources import files
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from yautja.cli import main, parser, EFFECT_OPTIONS
from yautja.colors import HUD_DEFAULTS
from yautja.render import Renderer
from yautja.semantic import Subject, SemanticTracker
from yautja.signal import SignalStyle, code_glyph, stable_number


class SignalTests(unittest.TestCase):
    size = (320, 180)

    def subject(self, label='person', opacity=1., track_id=1):
        mask = np.zeros((180, 320), np.float32)
        mask[40:170, 125:195] = 1
        mask[85:115, 145:175] = 0  # A hole that must remain free of glyph ink.
        return Subject(mask, label, .9, track_id=track_id, opacity=opacity)

    def renderer(self, **kwargs):
        return Renderer(*self.size, **{'scene_mode': 'source', 'glow': 0, 'hud_glyphs': 'cyber',
            'hud_opacity': 0, 'hud_opacity_elements': 'subject-code=1', 'subject_code': True,
            'code_density': 1, **kwargs})

    def test_cyber_catalog_rasterizes_all_contours_and_keeps_counters(self):
        data = json.loads(files('yautja').joinpath('assets/cyber-glyphs.json').read_text())
        self.assertEqual(data['count'], 192)
        self.assertEqual(len({g['svg_sha256'] for g in data['glyphs']}), 192)
        self.assertIn('Permission is hereby granted', data['license'])
        for i in range(192):
            self.assertIsNotNone(code_glyph(i, 16).getbbox())
        # 017 has a detached center bar and the gap immediately below it.
        glyph = np.asarray(code_glyph(17, 100))
        self.assertGreater(glyph[50, 40], 240)
        self.assertEqual(glyph[62, 40], 0)

    def test_cli_cyber_choice_applies_everywhere_and_timecode_stays_numeric(self):
        for order in (['--stylepreset', 'ghost-signal', '--HUDglyphs', 'yautja'],
                      ['--HUDglyphs', 'yautja', '--stylepreset', 'ghost-signal']):
            self.assertEqual(parser().parse_args(order).hud_glyphs, 'yautja')
        args = parser().parse_args(['--stylepreset', 'ghost-signal'])
        self.assertEqual((args.hud_glyphs, args.preset_kind), ('cyber', 'look'))
        renderers = [Renderer(320, 180, hud_glyphs=g) for g in ('yautja', 'cyber')]
        self.assertNotEqual(renderers[0].glyph(17, 20).tobytes(), renderers[1].glyph(17, 20).tobytes())
        np.testing.assert_array_equal(renderers[1].callout_glyph(17, 20), code_glyph(17, 20))
        np.testing.assert_array_equal(renderers[1].code_mask(17, 20), code_glyph(17, 20))
        with patch('sys.stderr', new_callable=io.StringIO), self.assertRaises(SystemExit):
            parser().parse_args(['--HUDglyphs', 'invalid'])
        source = Image.new('RGB', self.size, (80, 90, 100))
        options = dict(hud_opacity=0, hud_opacity_elements='timecode=1', show_timecode=True)
        a, b = [Renderer(*self.size, hud_glyphs=g, **options).render(source, 1.25) for g in ('yautja', 'cyber')]
        np.testing.assert_array_equal(a, b)

    def test_source_mode_preserves_structure_and_ignores_thermal_palette(self):
        rng = np.random.default_rng(2)
        source = Image.fromarray(rng.integers(0, 255, (180, 320, 3), dtype=np.uint8))
        a = Renderer(*self.size, scene_mode='source', hud=False, scene_tint_strength=0, scene_exposure=1).render(source, 0)
        np.testing.assert_array_equal(a, source)
        a, b = [Renderer(*self.size, scene_mode='source', hud=False, palette=p).render(source, 0) for p in ('yautja', 'virtualboy')]
        np.testing.assert_array_equal(a, b)
        self.assertGreater(np.asarray(a)[..., 1].mean(), np.asarray(a)[..., 0].mean())
        with self.assertRaisesRegex(ValueError, 'RGB frame'):
            Renderer(*self.size, scene_mode='source').render_field(np.zeros((180, 320), np.uint8), 0)

    def test_people_and_animals_code_is_clipped_to_mask_and_holes(self):
        source = Image.new('RGB', self.size)
        frames = []
        for label in ('person', 'dog'):
            subject = self.subject(label)
            image = np.asarray(self.renderer().render(source, 1., subjects=[subject]))
            self.assertGreater(image.sum(), 1000)
            self.assertEqual(image[subject.mask == 0].sum(), 0)
            frames.append(image)
        np.testing.assert_array_equal(*frames)
        none = self.renderer().render(source, 1., subjects=[])
        hidden = self.renderer().render(source, 1., subjects=[self.subject(opacity=0)])
        np.testing.assert_array_equal(none, hidden)

    def test_code_moves_upward_and_is_independent_of_call_order(self):
        style = SignalStyle(code_size=40, code_speed=1, code_density=1)
        size, bounds, anchor = (360, 540), (0, 0, 360, 540), (0, 0)
        cell = max(5, round(40 * min(size) / 1080))
        number = stable_number(42, 1, 4)
        speed = 5 + number % 997 / 997 * 6
        # Use solid cells to measure illumination independently of glyph cycling.
        solid = lambda index, size: Image.new('L', (size, size), 255)
        a = np.asarray(style.streams(size, bounds, anchor, 0, 42, 1, solid))
        b = np.asarray(style.streams(size, bounds, anchor, 1 / speed, 42, 1, solid))
        x = round(4 * cell * 1.15) + cell // 2
        for row in range(2, 25):
            before, after = round(row * cell * 1.45), round((row - 1) * cell * 1.45)
            self.assertAlmostEqual(int(a[before, x]), int(b[after, x]), delta=1)
        np.testing.assert_array_equal(a, style.streams(size, bounds, anchor, 0, 42, 1, solid))
        frozen = SignalStyle(code_speed=0, code_density=1)
        np.testing.assert_array_equal(frozen.streams(size, bounds, anchor, 0, 42, 1),
                                      frozen.streams(size, bounds, anchor, 5, 42, 1))

    def test_title_and_caret_are_centered_with_consistent_clearance(self):
        size = (640, 360)
        mask = np.zeros((360, 640), np.float32)
        mask[100:330, 270:370] = 1
        options = dict(look_preset='ghost-signal', neon=False, glow=0, subject_code=False, subject_outline=False,
                       hud_opacity=0, hud_opacity_elements='subject-labels=1,subject-carets=1')
        frame = Image.new('RGB', size)
        renderer = Renderer(*size, **options)
        image = np.asarray(renderer.render(frame, 0, subjects=[Subject(mask, 'person', .9, track_id=1)]))
        cyan = (image[..., 1] > 180) & (image[..., 2] > 180) & (image[..., 0] < 100)
        yellow = (image[..., 0] > 180) & (image[..., 1] > 130) & (image[..., 2] < 100)
        ty, tx = np.nonzero(cyan)
        cy, cx = np.nonzero(yellow)
        self.assertGreater(len(tx), 10)
        self.assertGreater(len(cx), 5)
        self.assertAlmostEqual((tx.min() + tx.max()) / 2, (cx.min() + cx.max()) / 2, delta=1.5)
        self.assertGreaterEqual(100 - cy.max(), 7)
        self.assertGreaterEqual(cy.min() - ty.max(), 5)
        self.assertEqual(renderer.signal.subject_caret_scale, 1.35)

    def test_outline_ignores_interior_segmentation_holes(self):
        subject = self.subject()
        renderer = self.renderer(subject_code=False, subject_outline=True,
                                 hud_opacity_elements='subject-outline=1')
        image = np.asarray(renderer.render(Image.new('RGB', self.size), 0, subjects=[subject]))
        self.assertEqual(image[80:120, 140:180].sum(), 0)
        self.assertGreater(image[50:80, 123:128].sum(), 0)

    @unittest.skipUnless(importlib.util.find_spec('cv2'), 'Optional tracking runtime is not installed')
    def test_outline_refresh_corrects_flow_error_on_the_current_frame(self):
        # Deliberately zero flow leaves the old contour behind a moving subject.
        # Current-frame refinement must replace it without changing the track ID.
        initial = self.subject()
        moved_mask = np.roll(initial.mask, 14, axis=1)
        class Detector:
            def detect(self, frame):
                return [initial]
            def refine(self, frame, tracks):
                tracks[0].mask = moved_mask.copy()
        tracker = SemanticTracker(Detector(), interval=.5, refine_masks=True)
        source = Image.new('RGB', self.size, (70, 80, 75))
        track_id = tracker.update(source, 0)[0].track_id
        zero_flow = np.zeros((180, 320, 2), np.float32)
        with patch.object(tracker.cv2, 'calcOpticalFlowFarneback', return_value=zero_flow):
            current = tracker.update(source, .1)[0]
        self.assertEqual(current.track_id, track_id)
        np.testing.assert_array_equal(current.mask, moved_mask)
        self.assertEqual(tracker.refinement_frames, 1)
        renderer = self.renderer(subject_code=False, subject_outline=True,
                                 hud_opacity_elements='subject-outline=1')
        image = np.asarray(renderer.render(Image.new('RGB', self.size), .1, subjects=[current]))
        self.assertEqual(image[50:80, 123:128].sum(), 0)
        self.assertGreater(image[50:80, 137:141].sum(), 0)

    def test_subject_effects_hide_together_and_reset_when_track_disappears(self):
        source = Image.new('RGB', self.size, (70, 95, 80))
        renderer = Renderer(*self.size, look_preset='ghost-signal')
        renderer.render(source, 0, subjects=[self.subject()], shot_id=1)
        self.assertEqual(set(renderer.signal.anchors), {1})
        renderer.render(source, .1, subjects=[], shot_id=1)
        self.assertEqual(renderer.signal.anchors, {})
        image = Renderer(*self.size, look_preset='ghost-signal', hud=False).render(source, 1, subjects=[self.subject()])
        np.testing.assert_array_equal(image, renderer.signal.grade(source))
        silent = Renderer(*self.size, look_preset='ghost-signal', hud_opacity=0,
                          hud_opacity_elements=','.join(k + '=0' for k in HUD_DEFAULTS))
        np.testing.assert_array_equal(silent.render(source, 1, subjects=[self.subject()]), renderer.signal.grade(source))

    def test_preset_saves_and_restores_new_options_without_loading_models(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / 'cyber.json')
            with patch('sys.stdout', new_callable=io.StringIO), patch('yautja.cli.semantic_tracker') as models:
                self.assertEqual(main(['--stylepreset', 'ghost-signal', '--code-speed', '2', '--save-preset', path]), 0)
                models.assert_not_called()
            args = parser().parse_args(['--preset-file', path])
            self.assertEqual((args.hud_glyphs, args.code_speed, args.subject_code), ('cyber', 2, True))
            self.assertEqual(args.neon_core_whiten, 0)
            # Exercise the exact CLI option mapping used by actual conversions.
            renderer = Renderer(*self.size, thermal=args.thermal,
                                **{k: getattr(args, k) for k in EFFECT_OPTIONS})
            self.assertEqual(renderer.signal.scene_mode, 'source')

    def test_invalid_values_rejected_before_media_or_models(self):
        for flags in (['--code-speed', '-1'], ['--scene-exposure', 'nan'], ['--code-density', '2'],
                      ['--scene-tint', 'badcolor'], ['--neon-core-whiten', '2'], ['--subject-code']):
            with self.subTest(flags=flags), patch('sys.stderr', new_callable=io.StringIO), \
                    patch('yautja.cli.convert') as convert:
                try:
                    status = main(['missing.png', 'out.png', *flags])
                except SystemExit as exc:
                    status = exc.code
                self.assertIn(status, (1, 2))
                convert.assert_not_called()


if __name__ == '__main__':
    unittest.main()
