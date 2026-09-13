"""Red-only output and optional full-frame CRT/VHS treatments."""
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
from yautja.cli import main, parser


class AnalogTests(unittest.TestCase):
    def test_virtualboy_is_red_only_including_hud_and_all_effects(self):
        frame = Image.fromarray(np.random.default_rng(5).integers(0, 255, (180, 320, 3), dtype=np.uint8))
        for options in ({}, {'grain': .04, 'pixelation': 80, 'scanlines': True, 'vhs': True}):
            renderer = Renderer(320, 180, palette='virtualboy', show_timecode=True, **options)
            image = np.array(renderer.render(frame, .5))
            self.assertEqual(image[..., 1:].max(), 0)
            self.assertGreater(len(np.unique(image[..., 0])), 32)
            self.assertGreater(image[:70, 200:, 0].max(), 50)

    def test_crt_lines_cover_the_finished_picture_and_hud_without_changing_odd_rows(self):
        frame = Image.new('RGB', (320, 180), (100, 100, 100))
        before = np.array(Renderer(320, 180, show_timecode=True).render(frame, 0))
        after = np.array(Renderer(320, 180, scanlines=True, show_timecode=True).render(frame, 0))
        np.testing.assert_array_equal(after[1::2], before[1::2])
        np.testing.assert_array_equal(after[::2], np.uint8(before[::2].astype(np.float32) * .88))
        self.assertTrue(np.any(after[:60, 220:] != before[:60, 220:]))

    def test_vhs_is_deterministic_time_varying_and_does_not_mutate_source(self):
        pixels = np.zeros((180, 320, 3), np.uint8)
        pixels[:, :160] = (220, 35, 20)
        pixels[:, 160:] = (20, 40, 230)
        image = Image.fromarray(pixels)
        a, again, later = [np.array(vhs_frame(image, t, 42)) for t in (0, 0, .5)]
        np.testing.assert_array_equal(a, again)
        np.testing.assert_array_equal(np.array(image), pixels)
        self.assertFalse(np.array_equal(a, pixels))
        self.assertFalse(np.array_equal(a, later))
        self.assertFalse(np.array_equal(a, np.array(vhs_frame(image, 0, 43))))
        # Chroma spreads at a hard red/blue boundary; the far edge never wraps.
        self.assertGreater(np.abs(a[30:120, 160:170].astype(float) - pixels[30:120, 160:170]).mean(),
                           np.abs(a[30:120, 260:280].astype(float) - pixels[30:120, 260:280]).mean() * 2)
        self.assertGreater(a[50, 0, 0], a[50, 0, 2] * 4)

    def test_vhs_preserves_dimensions_on_portrait_and_tiny_frames(self):
        for size in ((2, 2), (9, 17), (180, 320)):
            image = vhs_frame(Image.new('RGB', size, 'white'), 0, 42)
            self.assertEqual(image.size, size)
            self.assertEqual(image.mode, 'RGB')
            self.assertEqual(np.asarray(image).dtype, np.uint8)

    def test_vhs_and_crt_flags_are_independent_and_legacy_aliases_work(self):
        self.assertFalse(parser().parse_args([]).vhs)
        self.assertIsNone(parser().parse_args([]).scanlines)
        for flag in ('--crt-lines', '--scanlines'):
            self.assertTrue(parser().parse_args([flag]).scanlines)
        for flag in ('--no-crt-lines', '--no-scanlines'):
            self.assertFalse(parser().parse_args(['--crt-lines', flag]).scanlines)
        self.assertFalse(parser().parse_args(['--vhs', '--no-vhs']).vhs)
        renderer = Renderer(320, 180, vhs=True)
        self.assertEqual((renderer.grain, renderer.pixelation, renderer.scanlines), (0, 0, False))
        self.assertFalse(Renderer(320, 180, sensor_texture=True).vhs)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg unavailable')
    def test_video_cli_reports_analog_effects_and_preserves_same_soundtrack(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=24',
                            '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '0.5',
                            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(source)], check=True)
            decoded = []
            for name, options in [('clean', []), ('analog', ['--vhs', '--crt-lines', '--palette', 'virtualboy'])]:
                output = root / (name + '.mp4')
                with patch('sys.stdout', new_callable=io.StringIO) as report, patch('sys.stderr', new_callable=io.StringIO):
                    status = main([str(source), str(output), *options])
                self.assertEqual(status, 0)
                data = json.loads(report.getvalue())
                self.assertEqual(data['frames'], 12)
                self.assertTrue(data['audio_preserved'])
                self.assertEqual(data['vhs'], name == 'analog')
                self.assertEqual(data['crt_lines'], name == 'analog')
                decoded.append(subprocess.run(['ffmpeg', '-v', 'error', '-i', str(output), '-map', '0:a:0',
                               '-f', 'f32le', '-ac', '1', '-ar', '8000', '-'], capture_output=True, check=True).stdout)
            self.assertEqual(decoded[0], decoded[1])


if __name__ == '__main__':
    unittest.main()
