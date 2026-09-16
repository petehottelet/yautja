"""The global HUD switch removes every overlay without changing media effects."""
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from yautja.render import Renderer, vhs_frame
from yautja.semantic import Subject
from yautja.cli import main, parser


class HudTests(unittest.TestCase):
    def test_waveform_axis_is_centered_under_middle_glyph(self):
        for width, height in ((320, 180), (960, 540), (1920, 1080)):
            with self.subTest(width=width):
                renderer = Renderer(width, height, glow=0, hud_theme='custom',
                                    hud_colors='waveform=#f00,waveform-axis=#f00,waveform-glyphs=#fff,waveform-ticks=#000')
                field = np.full((height, width), 100, np.uint8)
                picture = Image.new('RGB', (width, height))
                renderer.draw_hud(picture, field, 0, wave=(np.zeros(32), np.zeros(32)))
                pixels = np.asarray(picture)
                row = pixels[height // 2]
                axis = np.flatnonzero((row[:, 0] > 200) & (row[:, 1] == 0))
                self.assertGreater(len(axis), 0)
                s = renderer.scale
                y = max(round(24 * s), round(height * .12))
                left, right = round(42 * s), round(68 * s)
                tile = pixels[y:y + max(10, round(25 * s)), left:right]
                visible = np.where((tile[..., 0] > 30) & (tile[..., 1] > 30))[1]
                self.assertGreater(len(visible), 0)
                self.assertAlmostEqual(float(axis.mean()), left + (visible.min() + visible.max()) / 2, delta=1.5)

    def test_hud_is_enabled_by_default_and_last_toggle_wins(self):
        self.assertTrue(parser().parse_args([]).hud)
        self.assertFalse(parser().parse_args(['--hud', '--no-hud']).hud)
        self.assertTrue(parser().parse_args(['--no-hud', '--hud']).hud)
        frame = Image.new('RGB', (320, 180), (100, 100, 100))
        np.testing.assert_array_equal(np.asarray(Renderer(320, 180).render(frame, 0)),
                                      np.asarray(Renderer(320, 180, hud=True).render(frame, 0)))

    def test_hidden_hud_is_only_the_heat_field_in_every_style(self):
        frame = Image.new('RGB', (320, 240), (100, 100, 100))
        mask = np.zeros((240, 320), np.float32)
        mask[40:210, 120:190] = 1
        subjects = [Subject(mask, 'person', .95, track_id=1)]
        for mode in ('luminance', 'silhouette', 'cinematic', 'detailed'):
            with self.subTest(mode=mode), patch('yautja.render.load_glyph_font') as font:
                renderer = Renderer(320, 240, hud=False, show_timecode=True, verbose=True, thermal=mode,
                                    palette='green-phosphor', hud_theme='random')
                field = renderer.heat_field.build(frame, subjects) if mode != 'luminance' else np.full((240, 320), 97, np.uint8)
                np.testing.assert_array_equal(np.asarray(renderer.render(frame, .5, subjects=subjects)), renderer.palette[field])
                font.assert_not_called()
                self.assertEqual(renderer.annotation_positions, {})
                self.assertFalse(renderer.show_timecode)
                self.assertFalse(renderer.verbose)

    def test_hidden_hud_preserves_grain_pixels_crt_and_vhs(self):
        field = np.random.default_rng(42).integers(0, 256, (180, 320), dtype=np.uint8)
        options = dict(hud=False, palette='ironbow', grain=.06, pixelation=80, seed=137)
        textured = Renderer(320, 180, **options).render_field(field, .5)
        expected = np.asarray(vhs_frame(textured, .5, 137), np.float32).copy()
        expected[::2] *= .88
        result = Renderer(320, 180, **options, scanlines=True, vhs=True).render_field(field, .5)
        np.testing.assert_array_equal(np.asarray(result), np.uint8(expected))
        clean = Renderer(320, 180, hud=False, palette='ironbow').render_field(field, .5)
        self.assertFalse(np.array_equal(np.asarray(textured), np.asarray(clean)))
        # Hidden custom HUD choices cannot introduce non-red Virtual Boy pixels.
        red = Renderer(320, 180, hud=False, palette='virtualboy', hud_theme='custom',
                       hud_colors='waveform=#00f', vhs=True).render_field(field, .5)
        self.assertEqual(np.asarray(red)[..., 1:].max(), 0)

    def test_image_cli_overrides_timecode_and_annotations_and_reports_effective_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / 'source.png', root / 'out.png'
            Image.new('RGB', (320, 180), (100, 100, 100)).save(source)
            with patch('sys.stdout', new_callable=io.StringIO) as report:
                status = main([str(source), str(output), '--no-hud', '--timecode', '--verbose', '--no-crt-lines'])
            self.assertEqual(status, 0)
            data = json.loads(report.getvalue())
            self.assertEqual((data['hud'], data['timecode'], data['verbose'], data['waveform']), (False, False, False, 'off'))
            self.assertTrue(data['settings']['timecode'])
            self.assertTrue(data['settings']['verbose'])
            with Image.open(output) as image:
                pixels = np.asarray(image)
                self.assertEqual(len(np.unique(pixels.reshape(-1, 3), axis=0)), 1)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg unavailable')
    def test_video_without_hud_preserves_soundtrack_and_skips_waveform_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=24',
                            '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '0.5',
                            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(source)], check=True)
            decoded = []
            for enabled in (True, False):
                output = root / ('hud.mp4' if enabled else 'no-hud.mp4')
                with patch('sys.stdout', new_callable=io.StringIO) as report, patch('sys.stderr', new_callable=io.StringIO):
                    if enabled:
                        status = main([str(source), str(output), '--timecode'])
                    else:
                        with patch('yautja.cli.AudioAnalysis', side_effect=AssertionError('Unused waveform analysis')):
                            status = main([str(source), str(output), '--timecode', '--no-hud'])
                self.assertEqual(status, 0)
                data = json.loads(report.getvalue())
                self.assertEqual(data['hud'], enabled)
                self.assertEqual(data['timecode'], enabled)
                self.assertEqual(data['waveform'], 'audio' if enabled else 'off')
                self.assertTrue(data['audio_preserved'])
                self.assertEqual((data['width'], data['height'], data['frames']), (320, 180, 12))
                decoded.append(subprocess.run(['ffmpeg', '-v', 'error', '-i', str(output), '-map', '0:a:0',
                                '-f', 'f32le', '-ac', '1', '-ar', '8000', '-'], capture_output=True, check=True).stdout)
            self.assertEqual(decoded[0], decoded[1])


if __name__ == '__main__':
    unittest.main()
