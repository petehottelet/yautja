"""Opacity controls preserve color, isolate HUD artwork, and include all states."""
import io
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from yautja.cli import main
from yautja.hud import OPACITY_ELEMENTS, hud_opacities, opacity_layer
from yautja.render import Renderer
from yautja.semantic import Subject
from yautja.target import TargetOverlay


class HudOpacityTests(unittest.TestCase):
    targets = [{'id': 'S001-F001', 'bbox': [.4, .25, .6, .8]}]

    def test_zero_hides_all_ink_outline_and_glow_in_every_compositing_mode(self):
        field = np.random.default_rng(12).integers(40, 180, (270, 480), dtype=np.uint8)
        mask = np.zeros(field.shape, np.float32)
        mask[70:250, 210:300] = 1
        subjects = [Subject(mask, 'person', .95, track_id=1)]
        for colors in ({}, {'palette': 'black-hot'}, {'hud_theme': 'custom', 'hud_colors': 'waveform=#f00'}):
            for style in ('trace', 'rorschach'):
                options = dict(**colors, wave_style=style, hud_blur=5, target_stroke=5, target_stroke_colors='#0f0',
                               show_timecode=True, verbose=True)
                with self.subTest(colors=colors, style=style):
                    hidden = Renderer(480, 270, **options, hud=False).render_field(field, 0)
                    transparent = Renderer(480, 270, **options, hud_opacity=0).render_field(
                        field, 0, subjects=subjects, targets=self.targets, target_static=True)
                    np.testing.assert_array_equal(np.asarray(hidden), np.asarray(transparent))

    def test_full_opacity_is_default_and_explicit_overrides_win(self):
        field = np.full((270, 480), 100, np.uint8)
        all_full = ','.join(key + '=1' for key in OPACITY_ELEMENTS)
        for options in ({}, {'palette': 'black-hot'}, {'hud_blur': 5}):
            sharp = Renderer(480, 270, **options).render_field(field, 1, targets=self.targets, target_static=True)
            full = Renderer(480, 270, **options, hud_opacity=0, hud_opacity_elements=all_full).render_field(
                field, 1, targets=self.targets, target_static=True)
            np.testing.assert_array_equal(np.asarray(sharp), np.asarray(full))

    def test_each_element_has_an_independent_visibility_control(self):
        field = np.full((540, 960), 100, np.uint8)
        mask = np.zeros(field.shape, np.float32)
        mask[130:470, 400:580] = 1
        subjects = [Subject(mask, 'person', .95, track_id=1)]
        def picture(key=None, analysis=False):
            renderer = Renderer(960, 540, show_timecode=True, verbose=True,
                                analysis=analysis,
                                subject_outline=True, subject_code=True, subject_labels=True,
                                hud_opacity_elements=None if key is None else key + '=0')
            return np.asarray(renderer.render_field(field, 1, subjects=subjects,
                              targets=self.targets, target_static=True))
        baseline = picture()
        for key in OPACITY_ELEMENTS:
            if key == 'target-flash':
                continue  # Its animated state is checked separately below.
            with self.subTest(element=key):
                hidden = picture(key, analysis=key.startswith('analysis-'))
                active = picture(analysis=True) if key.startswith('analysis-') else baseline
                self.assertGreater(np.count_nonzero(active != hidden), 10)
                if key.startswith('waveform'):
                    np.testing.assert_array_equal(baseline[:, 150:], hidden[:, 150:])

    def test_opacity_preserves_rgb_and_multiplies_existing_tracking_alpha(self):
        tile = Image.new('RGBA', (10, 10), (240, 32, 10, 128))
        self.assertEqual(opacity_layer(tile, .5).getpixel((0, 0)), (240, 32, 10, 64))
        background = Image.new('RGB', (480, 270), (10, 20, 30))
        colors = ((255, 48, 43),) * 2
        tracked = [dict(self.targets[0], opacity=.5)]
        a = TargetOverlay(stroke=5, blur=5).draw(background, 0, tracked, colors, static=True)
        b = TargetOverlay(stroke=5, blur=5, opacity=.5).draw(background, 0, self.targets, colors, static=True)
        np.testing.assert_array_equal(np.asarray(a), np.asarray(b))

    def test_flash_inherits_target_opacity_or_uses_its_own_override(self):
        self.assertEqual(hud_opacities(.8, 'target=.3')['target-flash'], .3)
        self.assertEqual(hud_opacities(.8, 'target-flash=.6,target=.3')['target-flash'], .6)
        background = Image.new('RGB', (480, 270))
        overlay = TargetOverlay(opacity=.7, flash_opacity=0, stroke=6, blur=4)
        for time in (0, .3, .6, .9, 1.2, 1.4):
            frame = np.asarray(overlay.draw(background, time, self.targets, ((255, 0, 0), (255, 255, 255))))
            if time == .9:
                self.assertGreater(frame.max(), 100)
            if time == 1.4:
                self.assertEqual(frame.max(), 0)

    def test_invalid_values_fail_before_media_is_opened(self):
        for args in (['--hud-opacity', 'nan'], ['--hud-opacity', '1.1'], ['--hud-opacity', '-0.1'],
                     ['--hud-opacity-elements', 'waveform=inf'], ['--hud-opacity-elements', 'target=-1'],
                     ['--hud-opacity-elements', 'timecode=2'], ['--hud-opacity-elements', 'waveform=.5,waveform=.6'],
                     ['--hud-opacity-elements', 'typo=.5'], ['--hud-opacity-elements', '']):
            with self.subTest(args=args), patch('yautja.cli.load_image') as read, patch('sys.stderr', new_callable=io.StringIO):
                self.assertEqual(main(['missing.png', 'out.png', *args]), 1)
                read.assert_not_called()
