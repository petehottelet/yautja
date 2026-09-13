"""Color validation, independent HUD ink, stable random schemes, and CLI exports."""
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

from yautja.colors import HUD_DEFAULTS, resolve_colors
from yautja.render import PALETTES, Renderer
from yautja.semantic import Subject
from yautja.cli import main


class ColorTests(unittest.TestCase):
    def test_custom_ramp_preserves_order_endpoints_and_interpolation(self):
        scheme = resolve_colors(PALETTES, palette='custom', palette_colors=' #123, ABCDEF, #f00 ')
        self.assertEqual(scheme.stops, [(0., (17, 34, 51)), (.5, (171, 205, 239)), (1., (255, 0, 0))])
        np.testing.assert_array_equal(scheme.palette[0], (17, 34, 51))
        np.testing.assert_array_equal(scheme.palette[-1], (255, 0, 0))
        white = resolve_colors(PALETTES, palette='custom', palette_colors='000 FFF')
        np.testing.assert_array_equal(white.palette[:, 0], np.arange(256))
        report = scheme.report()
        self.assertEqual(report['palette_stops'][1], {'position': .5, 'hex': '#abcdef'})

    def test_matched_hud_uses_palette_channels_for_every_element(self):
        for name in ('green-phosphor', 'amber-phosphor', 'white-hot', 'black-hot', 'virtualboy'):
            with self.subTest(palette=name):
                scheme = resolve_colors(PALETTES, palette=name, hud_theme='palette')
                for rgb in scheme.hud.values():
                    r, g, b = rgb
                    if name == 'green-phosphor':
                        self.assertGreater(g, max(r, b))
                    elif name == 'amber-phosphor':
                        self.assertGreater(r, g)
                        self.assertGreater(g, b)
                    elif name == 'virtualboy':
                        self.assertGreater(r, 0)
                        self.assertEqual((g, b), (0, 0))
                    else:
                        self.assertEqual((r, g), (g, b))
        frame = Image.new('RGB', (640, 360), (80, 80, 80))
        result = np.asarray(Renderer(640, 360, palette='green-phosphor', hud_theme='palette', show_timecode=True).render(frame, .5))
        self.assertTrue(np.all(result[..., 1] >= result[..., 0]))
        self.assertTrue(np.all(result[..., 1] >= result[..., 2]))

    def test_each_custom_hud_element_changes_its_own_visible_ink(self):
        mask = np.zeros((360, 640), np.float32)
        mask[100:300, 220:370] = 1
        subjects = [Subject(mask, 'person', .9, track_id=1)]
        field = np.full((360, 640), 100, np.uint8)
        all_green = ','.join(f'{key}=#00ff00' for key in HUD_DEFAULTS)
        options = dict(hud_theme='custom', hud_colors=all_green, glow=0, verbose=True, show_timecode=True)
        original = Renderer(640, 360, **options)
        baseline = np.asarray(original.render_field(field, .5, subjects=subjects))
        for key in HUD_DEFAULTS:
            with self.subTest(element=key):
                renderer = Renderer(640, 360, **{**options, 'hud_colors': all_green.replace(f'{key}=#00ff00', f'{key}=#0000ff')})
                result = np.asarray(renderer.render_field(field, .5, subjects=subjects))
                self.assertGreater(np.count_nonzero(result != baseline), 0)
                # Recoloring never alters the thermal ramp or the glyph sequence/layout.
                np.testing.assert_array_equal(renderer.palette, original.palette)
                self.assertEqual(renderer.annotation_positions, original.annotation_positions)
                self.assertEqual(renderer.callout_symbols(1), original.callout_symbols(1))
                self.assertEqual(sum(renderer.hud_colors[k] != original.hud_colors[k] for k in HUD_DEFAULTS), 1)
        partial = resolve_colors(PALETTES, hud_theme='custom', hud_colors='waveform=#000;timecode=fff')
        self.assertEqual(partial.hud['waveform'], (0, 0, 0))
        self.assertEqual(partial.hud['readout'], HUD_DEFAULTS['readout'])

    def test_black_custom_ink_is_drawn_and_virtualboy_allows_explicit_hud_colors(self):
        renderer = Renderer(640, 360, palette='custom', palette_colors='#fff,#fff',
                            hud_theme='custom', hud_colors='waveform=#000,timecode=#000',
                            show_timecode=True, glow=0)
        image = np.asarray(renderer.render(Image.new('RGB', (640, 360)), .5))
        self.assertTrue(np.any(np.all(image[70:300, :50] == 0, axis=2)))
        self.assertTrue(np.any(np.all(image[:60, 450:] == 0, axis=2)))
        blue = Renderer(640, 360, palette='virtualboy', hud_theme='custom', hud_colors='readout=#00f', glow=0)
        result = np.asarray(blue.render(Image.new('RGB', (640, 360)), .5))
        self.assertGreater(result[:40, 450:, 2].max(), 100)

    def test_random_schemes_are_seeded_stable_and_can_be_reused_as_custom(self):
        a = Renderer(320, 180, random_colors=True, seed=-137)
        b = Renderer(320, 180, palette='random', hud_theme='random', seed=-137)
        c = Renderer(320, 180, random_colors=True, seed=138)
        self.assertEqual(a.colors.report(), b.colors.report())
        self.assertFalse(np.array_equal(a.palette, c.palette))
        self.assertTrue(all(a.hud_colors[key] != c.hud_colors[key] for key in HUD_DEFAULTS))
        before = a.colors.report()
        for time in (0, .5, 100):
            a.render(Image.new('RGB', (320, 180)), time)
        self.assertEqual(before, a.colors.report())
        copy = Renderer(320, 180, palette='custom', palette_colors=','.join(item['hex'] for item in before['palette_stops']),
                        hud_theme='custom', hud_colors=','.join(f'{key}={value}' for key, value in before['hud_colors'].items()))
        np.testing.assert_array_equal(a.palette, copy.palette)
        self.assertEqual(a.hud_colors, copy.hud_colors)
        self.assertEqual(Renderer(320, 180, palette='random').hud_colors, HUD_DEFAULTS)
        np.testing.assert_array_equal(Renderer(320, 180, hud_theme='random').palette, Renderer(320, 180).palette)

    def test_invalid_choices_fail_before_model_setup_or_output_changes(self):
        bad = [
            ['--palette', 'custom'], ['--palette-colors', '#000,#fff'],
            ['--palette', 'custom', '--palette-colors', '#000'],
            ['--palette', 'custom', '--palette-colors', '#000,,#fff'],
            ['--palette', 'custom', '--palette-colors', '#ff000080,#fff'],
            ['--palette', 'custom', '--palette-colors', ','.join(['#fff'] * 17)],
            ['--hud-theme', 'custom'], ['--hud-colors', 'waveform=#fff'],
            ['--hud-theme', 'custom', '--hud-colors', 'unknown=#fff'],
            ['--hud-theme', 'custom', '--hud-colors', 'waveform=#fff,waveform=#000'],
            ['--hud-theme', 'custom', '--hud-colors', 'waveform=red'],
            ['--hud-theme', 'custom', '--hud-colors', 'waveform=#fff,'],
            ['--random-colors', '--palette', 'ironbow'],
        ]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'keep.png'
            output.write_bytes(b'keep this output')
            for options in bad:
                with self.subTest(options=options), patch('yautja.cli.semantic_tracker') as tracker, \
                        patch('sys.stderr', new_callable=io.StringIO) as error:
                    self.assertEqual(main(['missing.jpg', str(output), '--thermal', 'detailed', '--overwrite', *options]), 1)
                    tracker.assert_not_called()
                    self.assertIn('Yautja:', error.getvalue())
                    self.assertEqual(output.read_bytes(), b'keep this output')

    def test_image_cli_reports_resolved_colors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.png'
            Image.new('RGB', (320, 180), (100, 100, 100)).save(source)
            for options in (['--palette', 'green-phosphor', '--hud-theme', 'palette'],
                            ['--random-colors', '--seed', '137'],
                            ['--palette', 'custom', '--palette-colors', '#000,#a3f,#fff',
                             '--hud-theme', 'custom', '--hud-colors', 'waveform=#0f0,timecode=#fff']):
                with self.subTest(options=options), patch('sys.stdout', new_callable=io.StringIO) as report:
                    self.assertEqual(main([str(source), str(root / 'out.png'), '--overwrite', '--timecode', *options]), 0)
                    data = json.loads(report.getvalue())
                self.assertEqual(len(data['hud_colors']), 9)
                self.assertGreaterEqual(len(data['palette_stops']), 2)
                with Image.open(root / 'out.png') as image:
                    self.assertEqual(image.size, (320, 180))

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg unavailable')
    def test_video_cli_exports_matched_hud_and_reports_colors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / 'source.mp4', root / 'green.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=12',
                            '-t', '0.5', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(source)], check=True)
            with patch('sys.stdout', new_callable=io.StringIO) as report:
                self.assertEqual(main([str(source), str(output), '--palette', 'green-phosphor', '--hud-theme', 'palette', '--timecode']), 0)
                data = json.loads(report.getvalue())
            self.assertEqual(data['frames'], 6)
            self.assertEqual(data['hud_theme'], 'palette')
            self.assertEqual(data['settings']['hud_theme'], 'palette')
            decoded = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(output), '-frames:v', '1',
                                      '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
            image = np.frombuffer(decoded, np.uint8).reshape(180, 320, 3).astype(int)
            self.assertGreater((image[..., 1] - image[..., 0]).mean(), 20)


if __name__ == '__main__':
    unittest.main()
