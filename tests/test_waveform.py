"""Rorschach waveform geometry, audio response, and independent HUD controls."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from yautja.cli import main, parser
from yautja.render import Renderer, procedural_wave
from yautja.waveform import RORSCHACH_STYLES, inkblot_mask


class InkblotTests(unittest.TestCase):
    def test_mirrored_full_height_wide_lobes_and_three_distinct_forms(self):
        masks = []
        for style in RORSCHACH_STYLES:
            mask = np.asarray(inkblot_mask(100, 360, np.ones(256), .7, style=style))
            np.testing.assert_array_equal(mask, mask[:, ::-1])
            self.assertGreater(np.count_nonzero(mask.max(axis=1) > 5), 260)
            self.assertGreater(np.count_nonzero(mask.max(axis=0) > 5), 65)
            masks.append(mask)
        self.assertGreater(np.count_nonzero(masks[0]), np.count_nonzero(masks[1]))
        self.assertGreater(np.count_nonzero(masks[0]), np.count_nonzero(masks[2]))
        self.assertGreater(np.count_nonzero(masks[0][:, 50]), np.count_nonzero(masks[2][:, 50]))

    def test_audio_silence_stays_empty_and_louder_audio_grows(self):
        for style in RORSCHACH_STYLES:
            with self.subTest(style=style):
                zero = inkblot_mask(100, 360, np.zeros(256), .7, style=style)
                self.assertIsNone(zero.getbbox())
                quiet = np.asarray(inkblot_mask(100, 360, np.full(256, .008), .7, style=style))
                loud = np.asarray(inkblot_mask(100, 360, np.full(256, .8), .7, style=style))
                self.assertGreater(loud.sum(), quiet.sum() * 1.5)

    def test_short_audio_attacks_survive_as_localized_edge_spikes(self):
        steady = np.full(256, .02)
        attacks = steady.copy()
        positions = (63, 112, 177)
        attacks[list(positions)] = .12
        # Include the small README size: antialiasing must not erase the teeth.
        for width, height in ((100, 540), (67, 270)):
            for style in ('rorschach', 'rorschach-hollow'):
                with self.subTest(size=(width, height), style=style):
                    baseline = np.asarray(inkblot_mask(width, height, steady, .7, style=style))
                    spiky = np.asarray(inkblot_mask(width, height, attacks, .7, style=style))
                    np.testing.assert_array_equal(spiky, spiky[:, ::-1])
                    np.testing.assert_array_equal(spiky[:35], baseline[:35])
                    x = np.abs(np.arange(width) - (width - 1) / 2)
                    edge = np.max(np.where(spiky > 32, x, 0), axis=1)
                    old_edge = np.max(np.where(baseline > 32, x, 0), axis=1)
                    for index in positions:
                        row = round(index / 255 * (height - 1))
                        tip = edge[row - 1:row + 2].max()
                        self.assertGreater(tip - old_edge[row], 5)
                        self.assertGreater(tip - edge[[row - 4, row + 4]].mean(), 5)

    def test_inkblots_drift_deterministically_and_detail_changes_lobes(self):
        signal = np.abs(procedural_wave(1))
        a = np.asarray(inkblot_mask(100, 360, signal, 1))
        np.testing.assert_array_equal(a, inkblot_mask(100, 360, signal, 1))
        self.assertFalse(np.array_equal(a, inkblot_mask(100, 360, signal, 1.5)))
        smooth = np.asarray(inkblot_mask(100, 360, np.ones(256), 1, detail=0))
        intricate = np.asarray(inkblot_mask(100, 360, np.ones(256), 1, detail=1))
        def lobes(mask):
            slope = np.diff(np.count_nonzero(mask > 5, axis=1))
            return np.count_nonzero(np.diff(np.sign(slope[slope != 0])) != 0)
        self.assertGreater(lobes(intricate), lobes(smooth))

    def test_layout_controls_preserve_other_hud_and_support_custom_black(self):
        field = np.full((360, 640), 120, np.uint8)
        wave = (-np.ones(256), np.ones(256))
        narrow = Renderer(640, 360, wave_style='rorschach', wave_width=.08, wave_height=.5, show_timecode=True, glow=0)
        wide = Renderer(640, 360, wave_style='rorschach', wave_width=.2, wave_height=1, show_timecode=True, glow=0)
        a, b = [np.asarray(r.render_field(field, 0, wave=wave)) for r in (narrow, wide)]
        np.testing.assert_array_equal(a[:, 180:], b[:, 180:])
        self.assertFalse(np.array_equal(a[:, :160], b[:, :160]))
        black = Renderer(640, 360, wave_style='rorschach', hud_theme='custom', hud_colors='waveform=#000', glow=0)
        ink = np.asarray(black.render_field(field, 0, wave=wave))
        self.assertLess(ink[180, 46].max(), a[180, 46].max())

    def test_hud_off_suppresses_inkblots_and_still_report_records_options(self):
        with tempfile.TemporaryDirectory() as folder:
            source, output = [Path(folder) / name for name in ('in.png', 'out.png')]
            Image.new('RGB', (320, 180), (120, 80, 50)).save(source)
            options = ['--wave-style', 'rorschach-hollow', '--wave-width', '.14', '--wave-height', '1']
            with patch('sys.stdout', new_callable=io.StringIO) as out:
                self.assertEqual(main([str(source), str(output), *options]), 0)
                report = json.loads(out.getvalue())
            self.assertEqual((report['wave_style'], report['wave_width'], report['wave_height']), ('rorschach-hollow', .14, 1))
            original = Renderer(320, 180, hud=False).render(Image.open(source).convert('RGB'), 0)
            with patch('sys.stdout', new_callable=io.StringIO) as out:
                self.assertEqual(main([str(source), str(output), *options, '--no-hud', '--overwrite']), 0)
                self.assertEqual(json.loads(out.getvalue())['wave_style'], 'off')
            with Image.open(output) as image:
                np.testing.assert_array_equal(image, original)

    def test_trace_default_and_invalid_dimensions(self):
        self.assertEqual(parser().parse_args([]).wave_style, 'trace')
        for options in (['--wave-style', 'rorschach', '--wave-width', 'nan'],
                        ['--wave-style', 'rorschach', '--wave-height', '1.1'],
                        ['--wave-width', '.2'], ['--wave-detail', '-1']):
            with patch('sys.stderr', new_callable=io.StringIO), self.assertRaises(SystemExit), patch('yautja.cli.convert') as convert:
                main(['in.png', 'out.png', *options])
            convert.assert_not_called()
