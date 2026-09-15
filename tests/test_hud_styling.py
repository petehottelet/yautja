"""HUD softness is isolated from the scene and independently selectable."""
import io
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from yautja.cli import main
from yautja.hud import BLUR_ELEMENTS, blur_layer, hud_blurs
from yautja.render import Renderer
from yautja.semantic import Subject
from yautja.target import TargetOverlay


class HudStylingTests(unittest.TestCase):
    size = (960, 540)
    targets = [{'id': 'S001-F001', 'bbox': [.4, .25, .6, .8]}]

    def picture(self, **options):
        field = np.random.default_rng(7).integers(80, 160, (540, 960), dtype=np.uint8)
        renderer = Renderer(*self.size, show_timecode=True, **options)
        return np.asarray(renderer.render_field(field, 1, targets=self.targets, target_static=True))

    def test_zero_overrides_restore_sharp_defaults_in_all_compositing_modes(self):
        zeroes = ','.join(key + '=0' for key in BLUR_ELEMENTS)
        for options in ({}, {'palette': 'black-hot'}, {'hud_theme': 'custom', 'hud_colors': 'waveform=#080'}):
            with self.subTest(options=options):
                np.testing.assert_array_equal(self.picture(**options), self.picture(**options, hud_blur=8,
                    hud_blur_elements=zeroes, target_stroke=0, target_stroke_colors='#0f0,#00f'))

    def test_target_only_blur_preserves_every_pixel_outside_the_target_neighborhood(self):
        sharp = self.picture()
        soft = self.picture(hud_blur_elements='target=8')
        y, x = np.nonzero(np.any(sharp != soft, axis=2))
        self.assertGreater(len(y), 100)
        self.assertGreater(x.min(), 380)
        self.assertLess(x.max(), 580)
        self.assertGreater(y.min(), 190)
        self.assertLess(y.max(), 340)

    def test_waveform_blur_does_not_change_scene_readout_or_target_elsewhere(self):
        for style in ('trace', 'rorschach', 'rorschach-split', 'rorschach-hollow'):
            with self.subTest(style=style):
                sharp = self.picture(wave_style=style)
                soft = self.picture(wave_style=style, hud_blur_elements='waveform=8')
                self.assertGreater(np.count_nonzero(sharp[:, :160] != soft[:, :160]), 100)
                np.testing.assert_array_equal(sharp[:, 160:], soft[:, 160:])

    def test_each_non_target_element_has_a_working_independent_override(self):
        field = np.full((540, 960), 100, np.uint8)
        mask = np.zeros(field.shape, np.float32)
        mask[130:470, 400:580] = 1
        subjects = [Subject(mask, 'person', .95, track_id=1),
                    Subject(np.roll(mask, -150, axis=1), 'person', .95, track_id=2)]
        def render(element=None, analysis=False):
            renderer = Renderer(*self.size, show_timecode=True, verbose=True, glow=0,
                                analysis=analysis, analysis_target=analysis,
                                geo_grid=True, target_outline=True, target_motif='triangles', target_label='TARGETING',
                                subject_outline=True, subject_code=True, subject_labels=True,
                                hud_blur_elements=None if element is None else element + '=8')
            image = Image.new('RGB', self.size)
            renderer.draw_hud(image, field, 1, subjects=subjects, static=True)
            image = renderer.draw_targets(image, 1, subjects, self.targets,
                                          (renderer.hud_colors['target'], renderer.hud_colors['target-flash']), static=True)
            self.assertTrue(renderer.annotation_positions)
            return np.asarray(image)
        sharp = render()
        for key in BLUR_ELEMENTS:
            if key != 'target':
                with self.subTest(element=key):
                    active = render(analysis=True) if key.startswith('analysis-') else sharp
                    self.assertGreater(np.count_nonzero(active != render(key, analysis=key.startswith('analysis-'))), 10)

    def test_hud_off_suppresses_stroke_and_blur_without_softening_the_scene(self):
        np.testing.assert_array_equal(self.picture(hud=False), self.picture(hud=False, hud_blur=20,
                                      target_stroke=12, target_stroke_colors='#0f0'))

    def test_blur_of_hidden_elements_has_no_effect(self):
        field = np.full((180, 320), 100, np.uint8)
        sharp = Renderer(320, 180, wave_style='rorschach').render_field(field, 0)
        soft = Renderer(320, 180, wave_style='rorschach', hud_blur_elements=
                        'timecode=20,callouts=20,target=20,waveform-glyphs=20').render_field(field, 0)
        np.testing.assert_array_equal(np.asarray(sharp), np.asarray(soft))

    def test_alpha_blur_retains_ink_hue_and_black_ink_stays_visible(self):
        ink = Image.new('RGBA', (40, 40))
        ink.paste((255, 30, 0, 255), (15, 15, 25, 25))
        pixels = np.asarray(blur_layer(ink, 3))
        visible = pixels[..., 3] > 30
        self.assertEqual(pixels[..., 0][visible].min(), 255)
        self.assertEqual(pixels[..., 2].max(), 0)
        background = Image.new('RGB', (320, 180), 'white')
        frame = np.asarray(TargetOverlay(blur=10).draw(background, 0, self.targets, ((0, 0, 0),) * 2, static=True))
        self.assertLess(frame.min(), 220)
        self.assertTrue(np.any((frame[..., 0] > 0) & (frame[..., 0] < 255)))
        self.assertTrue(np.array_equal(frame[..., 0], frame[..., 1]))
        self.assertEqual(frame[0, 0, 0], 255)

    def test_outline_is_inward_and_follows_custom_flash_colors(self):
        background = Image.new('RGB', self.size)
        colors = ((255, 0, 0), (255, 255, 255))
        sharp = np.asarray(TargetOverlay().draw(background, 0, self.targets, colors, static=True))
        overlay = TargetOverlay(stroke=6, stroke_colors='#00ff00,#0000ff')
        for t in (0, .3, .6, .9, 1.2, 1.4):
            frame = np.asarray(overlay.draw(background, t, self.targets, colors))
            if t not in (.9, 1.4):
                continue
            expected = (0, 255, 0) if t == .9 else (0, 0, 255)
            self.assertGreater(np.count_nonzero(np.all(frame == expected, axis=2)), 30)
            for picture in (sharp, frame):
                y, x = np.nonzero(picture.max(axis=2) > 64)
                bounds = (x.min(), y.min(), x.max(), y.max())
                if picture is sharp:
                    original_bounds = bounds
                else:
                    self.assertEqual(bounds, original_bounds)

    def test_explicit_stroke_colors_override_virtualboy_only_when_enabled(self):
        field = np.full((540, 960), 100, np.uint8)
        for width in (0, 6):
            renderer = Renderer(*self.size, palette='virtualboy', target_stroke=width, target_stroke_colors='#0f0')
            frame = np.asarray(renderer.render_field(field, 0, targets=self.targets, target_static=True))
            self.assertEqual(frame[..., 1].max() > 200, bool(width))

    def test_invalid_radii_and_assignments_fail_before_opening_media(self):
        for args in (['--hud-blur', 'nan'], ['--hud-blur', '-1'], ['--target-stroke', '13'],
                     ['--target-stroke-colors', '#fff,,#000']):
            with self.subTest(args=args), patch('sys.stderr', new_callable=io.StringIO), patch('yautja.cli.load_image') as read:
                try:
                    self.assertEqual(main(['missing.png', 'out.png', *args]), 1)
                except SystemExit as error:
                    self.assertEqual(error.code, 2)
                read.assert_not_called()
        for value in ('target=nan', 'waveform=inf', 'target=-1', 'timecode=21', 'target=2,target=3',
                      'typo=2', 'target=2,', '', 'target=two'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                hud_blurs(0, value)
        for value in (-1, math.nan, math.inf, 13):
            with self.subTest(stroke=value), self.assertRaises(ValueError):
                TargetOverlay(stroke=value)

    def test_still_cli_records_resolved_independent_values(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / 'source.png', Path(directory) / 'out.png'
            Image.new('RGB', (320, 180), (100, 100, 100)).save(source)
            with patch('sys.stdout', new_callable=io.StringIO) as report:
                self.assertEqual(main([str(source), str(output), '--timecode', '--hud-blur', '2',
                    '--hud-blur-elements', 'waveform=5,timecode=0,target=8',
                    '--target-stroke', '4', '--target-stroke-colors', '#123456,#abcdef',
                    '--hud-opacity', '.7', '--hud-opacity-elements', 'waveform=.3,target=.5,timecode=1']), 0)
            data = json.loads(report.getvalue())
            self.assertEqual(data['hud_blur_elements']['timecode'], 0)
            self.assertEqual(data['hud_blur_elements']['readout'], 2)
            self.assertEqual(data['hud_blur_elements']['target'], 8)
            self.assertEqual(data['target_stroke_colors'], ['#123456', '#abcdef'])
            self.assertEqual(data['settings']['target_stroke'], 4)
            self.assertEqual(data['hud_opacity_elements']['waveform'], .3)
            self.assertEqual(data['hud_opacity_elements']['readout'], .7)
            self.assertEqual(data['hud_opacity_elements']['target-flash'], .5)
            self.assertEqual(data['settings']['hud_opacity'], .7)
            with Image.open(output) as image:
                image.verify()

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg unavailable')
    def test_video_cli_uses_new_controls_and_preserves_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / 'source.mp4', Path(directory) / 'out.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=12',
                            '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '0.5',
                            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(source)], check=True)
            with patch('sys.stdout', new_callable=io.StringIO) as report, patch('sys.stderr', new_callable=io.StringIO):
                self.assertEqual(main([str(source), str(output), '--hud-blur', '2',
                                       '--hud-blur-elements', 'waveform=5,timecode=0', '--target-stroke',
                                       '--hud-opacity', '.6', '--hud-opacity-elements', 'waveform=.25']), 0)
            data = json.loads(report.getvalue())
            self.assertEqual(data['frames'], 6)
            self.assertTrue(data['audio_preserved'])
            self.assertEqual(data['hud_blur_elements']['waveform'], 5)
            self.assertEqual(data['target_stroke'], 2)
            self.assertEqual(data['hud_opacity_elements']['waveform'], .25)
            self.assertEqual(data['hud_opacity_elements']['timecode'], .6)
            subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(output), '-f', 'null', '-'], check=True, capture_output=True)
