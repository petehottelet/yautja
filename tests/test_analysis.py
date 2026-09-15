"""Fremont lifecycle, safe typography, source detail and preset integration."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from yautja.analysis import AnalysisHUD, analysis_font, category
from yautja.cli import main, parser, extra_report
from yautja.render import Renderer
from yautja.semantic import Subject
from yautja.signal import SignalStyle


class AnalysisTests(unittest.TestCase):
    def subject(self, size=(320, 180), bounds=(120, 30, 200, 170), label='person', track=1):
        mask = np.zeros((size[1], size[0]), np.float32)
        x0, y0, x1, y1 = bounds
        mask[y0:y1, x0:x1] = 1
        return Subject(mask, label, .95, track_id=track)

    def test_search_acquire_analysis_hold_loss_cut_and_still(self):
        hud, subject = AnalysisHUD(analysis=True), self.subject()
        for time, expected in [(0, 'SEARCH'), (1, 'ACQUIRE'), (2, 'ANALYSIS'), (4, 'HOLD')]:
            selected, _, _ = hud.state([subject], time, 0)
            self.assertEqual(hud.phase, expected)
            self.assertEqual(selected is not None, time > 0)
        hud.state([], 4.1, 0)
        self.assertEqual((hud.phase, hud.selected), ('SEARCH', None))
        hud.state([subject], 5.5, 0)
        self.assertEqual(hud.selected, 1)
        hud.state([subject], 5.6, 1)
        self.assertEqual((hud.phase, hud.selected), ('SEARCH', None))
        hud.state([subject], 0, 1, static=True)
        self.assertEqual((hud.phase, hud.selected), ('HOLD', 1))
        hud.state([], 0, 1, static=True)
        self.assertEqual(hud.phase, 'SEARCH')

    def test_selection_is_stable_until_next_cycle(self):
        a, b = self.subject(), self.subject(bounds=(10, 40, 100, 170), track=2)
        hud = AnalysisHUD(analysis=True)
        hud.state([a], 0, 0)
        hud.state([a], 1, 0)
        hud.state([a, b], 2, 0)
        self.assertEqual(hud.selected, 1)
        hud.state([a, b], 6.1, 0)
        self.assertEqual(hud.phase, 'SEARCH')
        hud.state([a, b], 7, 0)
        self.assertEqual(hud.selected, 2)

    def test_grid_moves_deterministically_and_zero_speed_freezes(self):
        frame = Image.new('RGB', (320, 180))
        options = dict(look_preset='fremont', hud_opacity=0, hud_opacity_elements='analysis-grid=1')
        a, b = Renderer(320, 180, **options), Renderer(320, 180, **options)
        images = []
        for time in (0, .3, .7):
            image = a.render(frame, time)
            self.assertEqual(image.tobytes(), b.render(frame, time).tobytes())
            images.append(image.tobytes())
        self.assertEqual(len(set(images)), 3)
        frozen = Renderer(320, 180, **options, analysis_speed=0)
        self.assertEqual(frozen.render(frame, 0).tobytes(), frozen.render(frame, 2).tobytes())

    def test_outline_blinks_then_holds_and_follows_current_mask(self):
        frame = Image.new('RGB', (320, 180))
        options = dict(look_preset='fremont', hud_opacity=0, hud_opacity_elements='analysis-outline=1')
        r = Renderer(320, 180, **options)
        subject = self.subject()
        r.render(frame, 0, subjects=[subject])
        on = np.asarray(r.render(frame, 1.5, subjects=[subject]))
        off = np.asarray(r.render(frame, 1.75, subjects=[subject]))
        self.assertGreater(on.sum(), 0)
        self.assertEqual(off.sum(), 0)
        moved = self.subject(bounds=(15, 20, 80, 150))
        held = np.asarray(r.render(frame, 4, subjects=[moved]))
        self.assertEqual(held[:, 120:200].sum(), 0)
        self.assertGreater(held[:, 15:80].sum(), 0)
        steady = Renderer(320, 180, **options, analysis_blink_rate=0)
        steady.render(frame, 0, subjects=[subject])
        self.assertGreater(np.asarray(steady.render(frame, 1.75, subjects=[subject])).sum(), 0)

    def test_descriptions_stay_inside_safe_area_at_all_edges_and_aspects(self):
        for size in [(960, 540), (540, 960), (360, 360), (128, 72), (72, 128)]:
            w, h = size
            r = Renderer(w, h, look_preset='fremont')
            for x, y in [(0, 0), (w * 2 // 3, 0), (0, h // 2), (w * 2 // 3, h // 2)]:
                subject = self.subject(size, (x, y, min(w, x + w // 3), min(h, y + h // 2)),
                                       label='a very long motorcycle category')
                r.render(Image.new('RGB', size), 0, subjects=[subject], target_static=True)
                self.assertEqual(len(r.analysis.text_boxes), 3)
                margin = max(2, round(min(size) * r.analysis.analysis_margin))
                for x0, y0, x1, y1 in r.analysis.text_boxes:
                    self.assertGreaterEqual(x0, margin)
                    self.assertGreaterEqual(y0, margin)
                    self.assertLessEqual(x1, w - margin)
                    self.assertLessEqual(y1, h - margin)

    def test_grading_preserves_detail_burgundy_shadows_and_pale_highlights(self):
        ramp = np.tile(np.arange(256, dtype=np.uint8), (80, 1))
        frame = Image.fromarray(ramp).convert('RGB')
        image = np.asarray(Renderer(256, 80, look_preset='fremont', hud=False).render(frame, 0))
        self.assertGreater(len(np.unique(image[0], axis=0)), 200)
        self.assertGreater(image[0, 85, 0], image[0, 85, 1] * 3)
        self.assertGreater(image[0, 240].min(), 225)
        self.assertLess(image[0, 15].max(), 30)
        self.assertEqual(SignalStyle().scene_highlights, 0)

    def test_hud_controls_and_no_hud_apply_to_every_analysis_element(self):
        frame, subject = Image.new('RGB', (320, 180)), self.subject()
        hidden = Renderer(320, 180, look_preset='fremont', hud=False)
        self.assertEqual(np.asarray(hidden.render(frame, 0, subjects=[subject], target_static=True)).sum(), 0)
        self.assertFalse(extra_report(hidden, None)['analysis'])
        for key in ('analysis-grid', 'analysis-text', 'analysis-outline'):
            options = dict(look_preset='fremont', hud_opacity=0,
                           hud_opacity_elements=f'{key}=1', hud_colors=f'{key}=#00FF00',
                           neon=True, neon_elements=f'{key}=.6', hud_blur_elements=f'{key}=1')
            visible = np.asarray(Renderer(320, 180, **options).render(frame, 0, subjects=[subject], target_static=True))
            self.assertGreater(visible[..., 1].sum(), 0)
            self.assertGreater(visible[..., 1].sum(), visible[..., 0].sum())
            options['hud_opacity_elements'] = f'{key}=0'
            blank = Renderer(320, 180, **options).render(frame, 0, subjects=[subject], target_static=True)
            self.assertEqual(np.asarray(blank).sum(), 0)

    def test_seeded_numbers_font_labels_and_preset_roundtrip(self):
        frame, subject = Image.new('RGB', (320, 180)), self.subject(label='motorcycle')
        render = lambda seed: Renderer(320, 180, look_preset='fremont', seed=seed).render(
            frame, 0, subjects=[subject], target_static=True).tobytes()
        self.assertEqual(render(14), render(14))
        self.assertNotEqual(render(14), render(15))
        self.assertEqual(category('motorcycle'), 'MOTORCYCLE')
        self.assertEqual(analysis_font(14).getname()[0], 'Michroma')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fremont.json'
            with patch('sys.stdout', new_callable=io.StringIO):
                self.assertEqual(main(['--stylepreset', 'fremont', '--save-preset', str(path)]), 0)
            self.assertTrue(json.loads(path.read_text())['settings']['analysis'])
            loaded = parser().parse_args(['--preset-file', str(path), '--analysis-blink-rate', '0'])
            self.assertEqual(loaded.analysis_blink_rate, 0)
            self.assertTrue(loaded.analysis)

    def test_validation_happens_before_media(self):
        for name, value in [('analysis_speed', -1), ('analysis_blink_rate', 5), ('analysis_margin', .3)]:
            with self.assertRaisesRegex(ValueError, name.replace('_', '-')):
                AnalysisHUD(**{name: value})
        with patch('sys.stderr', new_callable=io.StringIO), patch('yautja.cli.convert') as convert:
            with self.assertRaises(SystemExit) as result:
                main(['missing.mp4', 'out.mp4', '--analysis', '--thermal', 'classic'])
            self.assertEqual(result.exception.code, 2)
            convert.assert_not_called()
