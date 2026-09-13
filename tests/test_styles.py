"""Style ordering, legacy aliases, independent palettes and texture controls."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from yautja.render import Renderer, PALETTES
from yautja.semantic import Subject, SurfacePart
from yautja.thermal import HeatField, CinematicHeatField, SurfaceHeatField
from yautja.cli import main, parser


def sample_person():
    mask = np.zeros((240, 320), np.float32)
    mask[15:225, 70:250] = 1
    parts = []
    for label, box in [('face', (125, 25, 180, 75)), ('jacket', (70, 75, 250, 175)), ('camera', (120, 95, 180, 140))]:
        region = np.zeros_like(mask)
        x0, y0, x1, y1 = box
        region[y0:y1, x0:x1] = 1
        parts.append(SurfacePart(region, label, .95))
    return Subject(mask, 'person', .95, track_id=1, parts=parts)


class StyleTests(unittest.TestCase):
    def test_cinematic_is_between_silhouette_and_detailed_and_softens_boundaries(self):
        frame, person = Image.new('RGB', (320, 240)), sample_person()
        fields = [field(320, 240, resolution=320).build(frame, [person]).astype(float)
                  for field in (HeatField, CinematicHeatField, SurfaceHeatField)]
        soft, middle, detailed = fields
        area = np.s_[25:210, 80:240]
        gap = np.abs(detailed[area] - soft[area]).mean()
        self.assertGreater(gap, 5)
        self.assertGreater(np.abs(middle[area] - soft[area]).mean(), 2)
        self.assertLess(np.abs(middle[area] - soft[area]).mean(), gap)
        self.assertLess(np.abs(middle[area] - detailed[area]).mean(), gap)
        self.assertGreater(middle[115, 150], detailed[115, 150])  # cooler gear becomes a broad patch
        self.assertLess(middle[115, 150], soft[115, 150])
        self.assertLess(np.abs(np.diff(middle[80:155, 90:220], axis=1)).max(),
                        np.abs(np.diff(detailed[80:155, 90:220], axis=1)).max())

    def test_cinematic_does_not_restore_rgb_face_or_garment_detail(self):
        person = sample_person()
        frame = Image.new('RGB', (320, 240))
        pixels = np.zeros((240, 320, 3), np.uint8)
        pixels[15:225:2, 70:250:2] = 255
        field = CinematicHeatField(320, 240, resolution=320)
        a, b = field.build(frame, [person]), field.build(Image.fromarray(pixels), [person])
        np.testing.assert_array_equal(a[30:205, 90:230], b[30:205, 90:230])
        np.testing.assert_array_equal(a, field.build(frame, [person]))
        person.opacity = 0
        np.testing.assert_array_equal(field.build(frame, [person]), field.build(frame, []))

    def test_old_mode_names_are_exact_aliases_with_the_original_default_palette(self):
        frame, person = Image.new('RGB', (320, 240)), sample_person()
        for old, new in [('semantic', 'silhouette'), ('realistic', 'detailed')]:
            before, after = Renderer(320, 240, thermal=old), Renderer(320, 240, thermal=new)
            np.testing.assert_array_equal(np.array(before.render(frame, 0, subjects=[person])),
                                          np.array(after.render(frame, 0, subjects=[person])))
            self.assertEqual(parser().parse_args(['--thermal', old]).thermal, new)
        original = Renderer(320, 240).palette
        for mode in ('classic', 'silhouette', 'cinematic', 'detailed'):
            for palette in ('auto', 'yautja'):
                np.testing.assert_array_equal(Renderer(320, 240, thermal=mode, palette=palette).palette, original)

    def test_phosphor_and_monochrome_ramps_have_the_right_direction_and_channel_balance(self):
        for name in ('green-phosphor', 'amber-phosphor', 'white-hot', 'black-hot'):
            ramp = Renderer(320, 240, palette=name).palette.astype(int)
            direction = -1 if name == 'black-hot' else 1
            self.assertTrue(np.all(np.diff(ramp, axis=0) * direction >= 0))
            if name in ('white-hot', 'black-hot'):
                np.testing.assert_array_equal(ramp[:, 0], ramp[:, 1])
                np.testing.assert_array_equal(ramp[:, 1], ramp[:, 2])
            if name == 'green-phosphor':
                self.assertTrue(np.all(ramp[:, 1] >= ramp[:, 0]))
                self.assertTrue(np.all(ramp[:, 1] >= ramp[:, 2]))
            if name == 'amber-phosphor':
                self.assertTrue(np.all(ramp[:, 0] >= ramp[:, 1]))
                self.assertTrue(np.all(ramp[:, 1] >= ramp[:, 2]))

    def test_redline_uses_black_shadows_blue_cool_regions_and_red_warmth(self):
        ramp = Renderer(320, 240, palette='redline').palette.astype(int)
        self.assertLess(ramp[45].max(), 16)
        self.assertGreater(ramp[105, 2], ramp[105, 0] * 3)
        self.assertGreater(ramp[105, 2], ramp[105, 1] * 2)
        self.assertGreater(ramp[185, 0], ramp[185, 1] * 4)
        self.assertGreater(ramp[185, 0], ramp[185, 2] * 4)
        self.assertGreater(ramp[255, 2], ramp[225, 2])


class IndependentEffectsTests(unittest.TestCase):
    def test_grain_alone_changes_over_time_without_a_pixel_grid_or_scanlines(self):
        renderer = Renderer(640, 360, grain=.06)
        self.assertEqual(renderer.pixelation, 0)
        self.assertFalse(renderer.scanlines)
        frame = Image.new('RGB', (640, 360), (110, 110, 110))
        a, b = np.array(renderer.render(frame, 0)), np.array(renderer.render(frame, .5))
        self.assertFalse(np.array_equal(a[90:270, 200:440], b[90:270, 200:440]))
        self.assertGreater(len(np.unique(a[150, 200:230], axis=0)), 4)

    def test_chunky_pixels_alone_are_blocky_and_time_invariant(self):
        renderer = Renderer(640, 360, pixelation=80)
        self.assertEqual(renderer.grain, 0)
        self.assertFalse(renderer.scanlines)
        pixels = np.random.default_rng(7).integers(0, 255, (360, 640, 3), dtype=np.uint8)
        a, b = [np.array(renderer.render(Image.fromarray(pixels), t)) for t in (0, .5)]
        np.testing.assert_array_equal(a[90:270, 200:440], b[90:270, 200:440])
        np.testing.assert_array_equal(a[152:160, 240:248], np.tile(a[152, 240], (8, 8, 1)))

    def test_preset_can_be_overridden_component_by_component(self):
        renderer = Renderer(640, 360, sensor_texture=True)
        self.assertEqual((renderer.grain, renderer.pixelation, renderer.scanlines), (.035, 256, True))
        disabled = Renderer(640, 360, sensor_texture=True, grain=0, pixelation=0, scanlines=False)
        self.assertEqual((disabled.grain, disabled.pixelation, disabled.scanlines), (0, 0, False))
        # Explicit controls also work with the combined preset off.
        explicit = Renderer(640, 360, sensor_texture=False, grain=.02, pixelation=64, scanlines=True)
        self.assertEqual((explicit.grain, explicit.pixelation, explicit.scanlines), (.02, 64, True))

    def test_display_options_do_not_change_heat_or_hud_layers(self):
        field = np.tile(np.arange(256, dtype=np.uint8), (180, 1))
        saved = field.copy()
        options = [{}, {'grain': .05}, {'pixelation': 64}, {'scanlines': True},
                   {'sensor_texture': True}, {'heat_glow': .8}, {'crt_vertical_lines': True}, {'crt_bleed': .7}]
        for palette in PALETTES:
            layers = []
            for settings in options:
                renderer = Renderer(256, 180, palette=palette, **settings)
                captured = []
                with patch.object(renderer, 'composite', side_effect=lambda image, overlay, x, y: captured.append(np.array(overlay))):
                    renderer.render_field(field, 0)
                for reference, actual in zip(layers, captured):
                    np.testing.assert_array_equal(reference, actual)
                layers = captured
                np.testing.assert_array_equal(field, saved)

    def test_cli_defaults_bare_flags_and_invalid_settings(self):
        defaults = parser().parse_args([])
        self.assertEqual(defaults.palette, 'yautja')
        self.assertIsNone(defaults.grain)
        self.assertIsNone(defaults.pixelation)
        self.assertFalse(defaults.sensor_texture)
        args = parser().parse_args(['--grain', '--pixelation', '--no-scanlines'])
        self.assertEqual((args.grain, args.pixelation, args.scanlines), (.035, 96, False))
        for options in [('--grain', 'nan'), ('--grain', '-.1'), ('--pixelation', '31'),
                        ('--pixelation', '-1'), ('--pixelation', '641'), ('--thermal', 'typo')]:
            with self.subTest(options=options), patch('yautja.cli.convert') as convert, patch('sys.stderr', new_callable=io.StringIO):
                with self.assertRaises(SystemExit) as result:
                    main(['input.mp4', 'output.mp4', *options])
                self.assertEqual(result.exception.code, 2)
                convert.assert_not_called()

    @unittest.skipUnless(importlib.util.find_spec('cv2'), 'optional OpenCV not installed')
    def test_image_cli_routes_each_style_and_reports_individual_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'input.png'
            Image.new('RGB', (320, 240)).save(source)
            for mode in ('silhouette', 'cinematic', 'detailed'):
                detector = SimpleNamespace(device='cpu', device_reason='test fixture', precision='fp32',
                    detect=lambda frame: [sample_person()], report=lambda: {})
                with patch('yautja.semantic.GroundedSegmenter', return_value=detector) as constructor, \
                     patch('sys.stdout', new_callable=io.StringIO) as output, patch('sys.stderr', new_callable=io.StringIO):
                    status = main([str(source), str(root / (mode + '.png')), '--thermal', mode,
                                   '--verbose', '--grain', '.02', '--pixelation', '80', '--palette', 'green-phosphor'])
                self.assertEqual(status, 0)
                report = json.loads(output.getvalue())
                self.assertEqual(report['thermal'], mode)
                self.assertEqual(report['palette'], 'green-phosphor')
                self.assertEqual((report['grain'], report['pixelation'], report['scanlines']), (.02, 80, False))
                self.assertFalse(report['sensor_texture'])
                self.assertEqual(constructor.call_args.kwargs['surfaces'], mode != 'silhouette')


if __name__ == '__main__':
    unittest.main()
