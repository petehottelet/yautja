"""Still-image conversion, orientation, output protection, and offline operation."""
import io
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
from yautja.cli import main


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'input image.png'
        pixels = np.zeros((181, 321, 3), dtype=np.uint8)
        pixels[:, :160] = (240, 200, 160)
        pixels[:, 160:] = (20, 40, 60)
        Image.fromarray(pixels).save(self.source)

    def call(self, source, output, *options):
        with patch('sys.stdout', new_callable=io.StringIO) as stdout, \
                patch('sys.stderr', new_callable=io.StringIO) as stderr, \
                patch('yautja.cli.binary', side_effect=AssertionError('Images must not require FFmpeg')):
            status = main([str(source), str(output), *options])
        return status, stdout.getvalue(), stderr.getvalue()

    def convert(self, source, name, *options):
        output = self.root / name
        status, stdout, stderr = self.call(source, output, *options)
        self.assertEqual(status, 0, stderr)
        with Image.open(output) as image:
            self.assertEqual(image.format, 'PNG')
            self.assertEqual(image.mode, 'RGB')
            self.assertEqual(image.n_frames, 1)
            pixels = np.array(image)
        return json.loads(stdout), pixels

    def test_png_is_deterministic_keeps_odd_dimensions_and_does_not_upscale(self):
        before = self.source.read_bytes()
        report, pixels = self.convert(self.source, 'result.png')
        _, repeat = self.convert(self.source, 'repeat.PNG')
        self.assertEqual((report['width'], report['height']), (321, 181))
        self.assertEqual(report['media_type'], 'image')
        self.assertEqual(report['waveform'], 'procedural-static')
        self.assertFalse(report['audio_preserved'])
        np.testing.assert_array_equal(pixels, repeat)
        with Image.open(self.source) as original:
            self.assertFalse(np.array_equal(pixels, np.array(original)))
        self.assertEqual(self.source.read_bytes(), before)
        resized, _ = self.convert(self.source, 'small.png', '--max-size', '160')
        self.assertEqual((resized['width'], resized['height']), (160, 90))

    def test_jpeg_orientation_matches_upright_image_and_metadata_is_removed(self):
        source = self.root / 'rotated.JPEG'
        exif = Image.Exif()
        exif[274] = 6
        exif[270] = 'source metadata should not be copied'
        with Image.open(self.source) as image:
            image.save(source, exif=exif)
        upright = self.root / 'upright.png'
        with Image.open(source) as image:
            expected = ImageOps.exif_transpose(image)
            expected.info.clear()
            expected.save(upright)
        report, result = self.convert(source, 'oriented.png')
        _, reference = self.convert(upright, 'reference.png')
        self.assertEqual((report['width'], report['height']), (181, 321))
        self.assertEqual(report['input_format'], 'JPEG')
        np.testing.assert_array_equal(result, reference)
        with Image.open(self.root / 'oriented.png') as image:
            self.assertFalse(image.getexif())
            self.assertNotIn('exif', image.info)

    def test_transparency_is_flattened_on_black_before_coloring(self):
        rgba = np.full((181, 321, 4), 255, dtype=np.uint8)
        rgba[:, :160, 3] = 0
        source, flat = self.root / 'transparent.png', self.root / 'flat.png'
        Image.fromarray(rgba).save(source)
        rgb = rgba[..., :3].copy()
        rgb[:, :160] = 0
        Image.fromarray(rgb).save(flat)
        report, pixels = self.convert(source, 'alpha-result.png')
        _, reference = self.convert(flat, 'flat-result.png')
        self.assertTrue(report['transparency_flattened'])
        np.testing.assert_array_equal(pixels, reference)

    def test_timecode_is_optional_static_and_respects_offset(self):
        large = self.root / 'large.png'
        Image.new('RGB', (640, 360), (100, 90, 80)).save(large)
        _, plain = self.convert(large, 'plain.png')
        report, clock = self.convert(large, 'clock.png', '--timecode', '--timecode-start', '90')
        _, zero = self.convert(large, 'zero.png', '--timecode')
        self.assertTrue(report['timecode'])
        self.assertEqual(report['settings']['timecode_start'], 90)
        self.assertTrue(np.any(clock[:80, 400:] != zero[:80, 400:]))
        self.assertTrue(np.any(clock[:80, 400:] != plain[:80, 400:]))
        np.testing.assert_array_equal(clock[80:], plain[80:])

    def test_existing_output_and_input_are_protected(self):
        destination = self.root / 'protected.png'
        destination.write_bytes(b'existing output')
        status, _, _ = self.call(self.source, destination)
        self.assertEqual(status, 1)
        self.assertEqual(destination.read_bytes(), b'existing output')
        original = self.source.read_bytes()
        status, _, _ = self.call(self.source, self.source, '--overwrite')
        self.assertEqual(status, 1)
        self.assertEqual(self.source.read_bytes(), original)
        status, _, error = self.call(self.source, destination, '--overwrite')
        self.assertEqual(status, 0, error)
        with Image.open(destination) as image:
            image.verify()

    def test_failed_save_or_cancellation_preserves_output_and_cleans_scratch(self):
        destination = self.root / 'protected.png'
        for error, code in [(OSError('disk full'), 1), (KeyboardInterrupt(), 130)]:
            destination.write_bytes(b'existing output')
            def fail_save(image, fp, *args, **kwargs):
                Path(fp).write_bytes(b'partial PNG')
                raise error
            with self.subTest(error=type(error).__name__), patch.object(Image.Image, 'save', fail_save):
                status, _, _ = self.call(self.source, destination, '--overwrite')
            self.assertEqual(status, code)
            self.assertEqual(destination.read_bytes(), b'existing output')
            self.assertEqual(list(self.root.glob('.yautja-*')), [])

    def test_corrupt_animated_and_unsupported_images_fail_without_output(self):
        corrupt = self.root / 'corrupt.jpg'
        corrupt.write_bytes(b'not a JPEG')
        animated = self.root / 'animated.png'
        Image.new('RGB', (200, 200), 'white').save(animated, save_all=True,
            append_images=[Image.new('RGB', (200, 200), 'black')], duration=100, loop=0)
        unsupported = self.root / 'input.gif'
        Image.new('RGB', (200, 200)).save(unsupported)
        for source in (corrupt, animated, unsupported):
            with self.subTest(source=source.name):
                output = self.root / 'absent.png'
                status, _, _ = self.call(source, output)
                self.assertEqual(status, 1)
                self.assertFalse(output.exists())

    def test_video_options_and_wrong_output_format_fail_clearly(self):
        for options in [('--duration', '1'), ('--start', '1'), ('--fps', '24'),
                        ('--waveform', 'audio'), ('--audio-stream', '1'), ('--mute',)]:
            with self.subTest(options=options):
                status, _, error = self.call(self.source, self.root / 'absent.png', *options)
                self.assertEqual(status, 1)
                self.assertIn(options[0], error)
                self.assertFalse((self.root / 'absent.png').exists())
        status, _, error = self.call(self.source, self.root / 'absent.mp4')
        self.assertEqual(status, 1)
        self.assertIn('.png', error)

    def test_cli_and_image_doctor_work_without_ffmpeg_on_path(self):
        env = {**os.environ, 'PATH': '', 'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1'}
        for options in [[str(self.source), str(self.root / 'subprocess.png')],
                        ['--doctor', '--media', 'image']]:
            result = subprocess.run([sys.executable, '-m', 'yautja', *options],
                                    capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['media_type'], 'image')

    @unittest.skipUnless(importlib.util.find_spec('cv2'), 'Optional tracking runtime is not installed')
    def test_realistic_cli_and_texture_toggle_reach_the_shared_renderer(self):
        from yautja.semantic import Subject, SurfacePart
        def detect(frame):
            mask = np.zeros((frame.height, frame.width), dtype=np.float32)
            mask[45:160, 100:155] = 1
            part = np.zeros_like(mask)
            part[50:75, 110:145] = 1
            return [Subject(mask, 'person', .99, parts=[SurfacePart(part, 'face', .9)])]
        detector = SimpleNamespace(device='cpu', device_reason='test fixture', precision='fp32',
                                   surfaces=True, detect=detect, report=lambda: {})
        with patch('yautja.semantic.GroundedSegmenter', return_value=detector) as constructor:
            clean, a = self.convert(self.source, 'realistic-clean.png', '--thermal', 'realistic', '--verbose')
            textured, b = self.convert(self.source, 'realistic-textured.png', '--thermal', 'realistic',
                                       '--verbose', '--sensor-texture')
            disabled, c = self.convert(self.source, 'realistic-off.png', '--thermal', 'realistic',
                                       '--verbose', '--sensor-texture', '--no-sensor-texture', '--grain', '0')
            override, _ = self.convert(self.source, 'realistic-palette.png', '--thermal', 'realistic',
                                       '--palette', 'ironbow')
        self.assertTrue(all(call.kwargs['surfaces'] for call in constructor.call_args_list))
        self.assertEqual(clean['palette'], 'yautja')
        self.assertEqual(override['palette'], 'ironbow')
        self.assertFalse(clean['sensor_texture'])
        self.assertTrue(textured['sensor_texture'])
        self.assertFalse(disabled['sensor_texture'])
        self.assertEqual(clean['semantic']['detection_frames'], 1)
        self.assertIn('skin', clean['semantic']['heat_model'])
        np.testing.assert_array_equal(a, c)
        self.assertFalse(np.array_equal(a, b))

    @unittest.skipUnless(importlib.util.find_spec('cv2'), 'Optional tracking runtime is not installed')
    def test_semantic_image_detects_once_and_preserves_cool_background(self):
        from yautja.semantic import Subject
        calls = []
        def detect(frame):
            calls.append(frame.size)
            mask = np.zeros((frame.height, frame.width), dtype=np.float32)
            mask[45:160, 100:155] = 1
            return [Subject(mask, 'person', .99)]
        detector = SimpleNamespace(device='cpu', device_reason='test fixture', precision='fp32',
                                   detect=detect, report=lambda: {})
        with patch('yautja.semantic.GroundedSegmenter', return_value=detector):
            report, pixels = self.convert(self.source, 'semantic.png', '--thermal', 'semantic',
                                          '--verbose', '--grain', '0')
        self.assertEqual(calls, [(321, 181)])
        self.assertEqual(report['semantic']['max_subjects'], 1)
        self.assertEqual(report['semantic']['detection_frames'], 1)
        self.assertEqual(report['semantic']['tracking'], 'none')
        self.assertEqual(report['semantic']['backend'], 'single-image')
        # A segmented subject is warmer than bright visible pixels beside it.
        self.assertGreater(int(pixels[100, 130, 0]), int(pixels[100, 80, 0]) + 100)
        cyan = (pixels[..., 1] > 170) & (pixels[..., 2] > 170) & (pixels[..., 0] < 120)
        self.assertGreater(np.count_nonzero(cyan), 10)


if __name__ == '__main__':
    unittest.main()
