"""Frozen recipe, independent scalar levels, and source feature preservation."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw

from yautja.cli import main, parser
from yautja.looks import LOOK_PRESETS, SPECTRUM, ThermalTransfer
from yautja.render import Renderer
from yautja.semantic import Subject, SurfacePart
from yautja.thermal import HeatField, LowDetailHeatField, SurfaceHeatField, VeryDetailedHeatField

NAME = 'hottropic'


class LevelTests(unittest.TestCase):
    def test_exact_hard_levels_endpoints_and_monotonic_soft_transitions(self):
        u = np.linspace(0, 1, 10001, dtype=np.float32)
        for count in (2, 6, 12, 20, 64):
            hard = ThermalTransfer(count, 0).quantize(u)
            np.testing.assert_allclose(np.unique(hard), np.linspace(0, 1, count), atol=1e-7)
            for softness in (.35, .65, 1):
                soft = ThermalTransfer(count, softness).quantize(u)
                self.assertEqual((soft[0], soft[-1]), (0, 1))
                self.assertTrue((np.diff(soft) >= -1e-7).all())
                self.assertGreater(len(np.unique(soft)), count)
        np.testing.assert_array_equal(ThermalTransfer(0).quantize(u), u)

    def test_hard_levels_reach_final_pixels_without_an_extra_sensor_quantizer(self):
        field = np.tile(np.linspace(0, 255, 1001, dtype=np.float32), (24, 1))
        for texture in (False, True):
            r = Renderer(1001, 24, palette='white-hot', hud=False, thermal_levels=12,
                         thermal_band_softness=0, sensor_texture=texture, grain=0, pixelation=0, scanlines=False)
            image = np.asarray(r.render_field(field, 0))
            self.assertEqual(len(np.unique(image[..., 0])), 12)
            self.assertEqual((image.min(), image.max()), (0, 255))

    def test_grade_does_not_change_hud_source_or_mutate_field(self):
        field = np.tile(np.arange(256, dtype=np.uint8), (180, 1))
        saved = field.copy()
        for count in (0, 2, 12, 64):
            r = Renderer(256, 180, thermal_levels=count, thermal_gamma=2)
            with patch.object(r, 'draw_hud') as hud:
                r.render_field(field, 0)
                np.testing.assert_array_equal(hud.call_args.args[1], saved)
            np.testing.assert_array_equal(field, saved)

    def test_invalid_levels_and_grades_rejected_before_decoding(self):
        for flags in (['--thermal-levels', '1'], ['--thermal-levels', '65'],
                      ['--thermal-levels', '0', '--thermal-band-softness', '.2'],
                      ['--thermal-gamma', '2'], ['--thermal-levels', '6', '--thermal-gamma', 'nan'],
                      ['--thermal-levels', '6', '--thermal-black-point', '.9', '--thermal-white-point', '.8']):
            with self.subTest(flags=flags), patch('yautja.cli.convert') as convert, patch('sys.stderr', new_callable=io.StringIO):
                with self.assertRaises(SystemExit) as result:
                    main(['in.mov', 'out.mp4', *flags])
                self.assertEqual(result.exception.code, 2)
                convert.assert_not_called()


class PresetTests(unittest.TestCase):
    def test_reference_recipe_and_positioned_colors_are_frozen(self):
        r = Renderer(320, 180, look_preset=NAME)
        self.assertEqual((r.thermal, r.palette_name, r.sensor_resolution, r.hud), ('cinematic', 'thermal-spectrum', 192, False))
        self.assertEqual((r.transfer.levels, r.transfer.band_softness, r.transfer.black, r.transfer.white,
                          r.transfer.gamma, r.transfer.softness), (12, .65, .2, .9, 1.1, .8))
        self.assertEqual([hexval['hex'] for hexval in r.colors.report()['palette_stops']],
                         ['#000000', '#081328', '#173b82', '#176dad', '#26a5ac', '#62b84e', '#d9c742',
                          '#f26427', '#ff303a', '#ff65ab', '#e6d8dd'])
        self.assertEqual([x[0] for x in SPECTRUM], [0, .06, .2, .33, .45, .56, .64, .72, .8, .91, 1])
        self.assertFalse(any((r.grain, r.pixelation, r.sensor_texture, r.scanlines, r.vhs, r.heat_glow,
                              r.display.motion_blur, r.display.crt_bleed, r.crt_vertical_lines)))

    def test_overrides_are_order_independent_and_continuous_clears_softness(self):
        base = ['--look-preset', NAME]
        for flags in (['--thermal-levels', '6', '--hud', '--palette', 'ironbow'],
                      ['--thermal-levels', '0'], ['--sensor-texture'],
                      ['--sensor-texture', '--grain', '0'], ['--random-colors']):
            a, b = [parser().parse_args(tokens) for tokens in (base + flags, flags + base)]
            self.assertEqual(vars(a), vars(b))
        continuous = parser().parse_args(base + ['--thermal-levels', '0'])
        self.assertIsNone(continuous.thermal_band_softness)
        textured = Renderer(320, 180, look_preset=NAME, sensor_texture=True)
        self.assertEqual((textured.grain, textured.pixelation, textured.scanlines), (.035, 192, True))
        args = parser().parse_args(base + ['--sensor-texture'])
        self.assertIsNone(args.grain)
        self.assertIsNone(args.pixelation)
        self.assertIsNone(args.scanlines)
        self.assertEqual(parser().parse_args(base + ['--preset', 'fast']).preset, 'fast')
        self.assertEqual(LOOK_PRESETS[NAME]['thermal_levels'], 12)

    def test_cli_still_recipe_report_and_explicit_classic_override(self):
        with tempfile.TemporaryDirectory() as folder:
            source, output = Path(folder) / 'in.png', Path(folder) / 'out.png'
            Image.fromarray(np.tile(np.arange(256, dtype=np.uint8), (180, 1))).convert('RGB').save(source)
            with patch('sys.stdout', new_callable=io.StringIO) as stdout:
                self.assertEqual(main([str(source), str(output), '--look-preset', NAME, '--thermal', 'classic']), 0)
            report = json.loads(stdout.getvalue())
            self.assertEqual((report['look_preset'], report['thermal_levels'], report['hud']), (NAME, 12, False))
            self.assertEqual(report['thermal'], 'classic')
            with Image.open(output) as image:
                self.assertEqual(image.size, (256, 180))


class VeryDetailedTests(unittest.TestCase):
    def test_low_detail_suppresses_anatomical_variation_and_keeps_aliases(self):
        mask = np.zeros((240, 320), np.float32)
        mask[25:220, 100:220] = 1
        subject = Subject(mask, 'person', .95)
        hard = mask > .5
        before = HeatField(320, 240, resolution=320).surface(subject, hard)
        after = LowDetailHeatField(320, 240, resolution=320).surface(subject, hard)
        self.assertLess(np.std(after[hard]), np.std(before[hard]) * .3)
        for alias in ('semantic', 'silhouette', 'low-detail'):
            self.assertEqual(parser().parse_args(['--thermal', alias]).thermal, 'low-detail')

    def test_visible_face_features_survive_only_in_very_detailed_mode(self):
        flat = Image.new('RGB', (320, 240), (160, 160, 160))
        face = flat.copy()
        draw = ImageDraw.Draw(face)
        draw.ellipse((117, 65, 136, 77), fill=(25, 25, 25))
        draw.ellipse((176, 65, 195, 77), fill=(25, 25, 25))
        draw.line((156, 80, 148, 106, 161, 106), fill=(80, 80, 80), width=5)
        draw.arc((130, 108, 181, 137), 0, 180, fill=(30, 30, 30), width=5)
        mask = np.zeros((240, 320), np.float32)
        mask[30:220, 80:240] = 1
        region = np.zeros_like(mask)
        region[40:150, 100:215] = 1
        subject = Subject(mask, 'person', .95, parts=[SurfacePart(region, 'face', .95)])
        for field_class, preserves in ((SurfaceHeatField, False), (VeryDetailedHeatField, True)):
            field = field_class(320, 240)
            a, b = field.build(flat, [subject]), field.build(face, [subject])
            delta = np.abs(a[55:145, 110:205].astype(float) - b[55:145, 110:205])
            if preserves:
                self.assertGreater(delta.max(), 15)
                self.assertGreater(delta.mean(), 2)
                self.assertLess(b[71, 125], b[55, 125])
                np.testing.assert_array_equal(b, field.build(face, [subject]))
            else:
                self.assertEqual(delta.max(), 0)
        self.assertEqual(parser().parse_args(['--thermal', 'very-detailed']).thermal, 'very-detailed')
