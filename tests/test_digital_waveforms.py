"""Digital waveform shapes are distinct, block-aligned and audio driven."""
import unittest
import numpy as np
from PIL import Image

from yautja.cli import parser
from yautja.render import Renderer
from yautja.waveform import DIGITAL_STYLES, inkblot_mask, vocoder_masks


class DigitalWaveformsTests(unittest.TestCase):
    def test_silence_and_determinism_for_every_digital_style(self):
        for style in DIGITAL_STYLES:
            with self.subTest(style=style):
                self.assertIsNone(inkblot_mask(84, 360, np.zeros(256), 1, style=style).getbbox())
                a = inkblot_mask(84, 360, np.ones(256) * .2, 1, style=style)
                b = inkblot_mask(84, 360, np.ones(256) * .2, 1, style=style)
                np.testing.assert_array_equal(a, b)
                self.assertIsNotNone(a.getbbox())
                self.assertEqual(parser().parse_args(['--wave-style', style]).wave_style, style)

    def test_pixel_geometries_are_distinct_and_stronger_audio_lights_more_area(self):
        masks = []
        for style in DIGITAL_STYLES:
            a = np.asarray(inkblot_mask(84, 360, np.ones(256) * .002, 1, style=style))
            b = np.asarray(inkblot_mask(84, 360, np.ones(256) * .2, 1, style=style))
            self.assertGreater(np.ptp(np.nonzero(b)[1]), np.ptp(np.nonzero(a)[1]))
            if style == 'digital-circuit':
                self.assertEqual(np.ptp(np.nonzero(b)[0]), np.ptp(np.nonzero(a)[0]))
                masks.append(b)
                continue
            # All visible transitions fall on the chosen square cell lattice.
            edges = np.nonzero(np.diff(b.astype(int), axis=1))[1] + 1
            pixel = max(2, round(84 / (14 + .6 * 18)))
            self.assertTrue(np.all(edges % pixel == 0))
            masks.append(b)
        for i in range(3):
            for j in range(i + 1, 3):
                self.assertGreater(np.count_nonzero(masks[i] != masks[j]), 1000)

    def test_vocoder_has_one_full_height_stack_of_horizontal_bars(self):
        mask = np.asarray(inkblot_mask(67, 540, np.full(256, .15), 0, style='digital-circuit'))
        lit_rows = np.flatnonzero(mask.max(axis=1))
        groups = np.split(lit_rows, np.flatnonzero(np.diff(lit_rows) > 1) + 1)
        self.assertGreater(len(groups), 30)
        self.assertLess(lit_rows.min(), 10)
        self.assertGreater(lit_rows.max(), 530)
        for group in groups:
            lit_columns = np.flatnonzero(mask[group].max(axis=0))
            self.assertGreater(np.count_nonzero(np.diff(lit_columns) > 1), 3)
            self.assertGreater(len(lit_columns), len(group) * 4)
            self.assertAlmostEqual((lit_columns.min() + lit_columns.max()) / 2, 33, delta=.5)
        np.testing.assert_array_equal(mask, inkblot_mask(67, 540, np.full(256, .15), 5, style='digital-circuit'))

    def test_vocoder_leds_fade_to_rounded_dark_ends(self):
        light, casing = (np.asarray(layer) for layer in vocoder_masks(67, 540, np.ones(256)))
        self.assertTrue(np.all(light <= casing))
        rows = np.flatnonzero(casing.max(axis=1))
        first = np.split(rows, np.flatnonzero(np.diff(rows) > 1) + 1)[0]
        middle = first[len(first) // 2]
        self.assertLess(np.count_nonzero(casing[first[0]]), np.count_nonzero(casing[middle]))
        self.assertGreater(light[middle, 33], light[middle, 15] * 2)
        self.assertGreater(np.count_nonzero((casing[middle] > 200) & (light[middle] == 0)), 5)

    def test_vocoder_housing_obeys_silence_opacity_and_neutral_ink(self):
        field = np.full((180, 320), 100, np.uint8)
        quiet = (np.zeros(256), np.zeros(256))
        baseline = np.asarray(Renderer(320, 180, hud=False).render_field(field, 1))
        for neon in (False, True):
            for blur in (0, 4):
                renderer = Renderer(320, 180, wave_style='digital-circuit', neon=neon,
                                    hud_opacity=0, hud_blur=blur)
                np.testing.assert_array_equal(renderer.render_field(field, 1), baseline)
                renderer = Renderer(320, 180, wave_style='digital-circuit', neon=neon,
                                    hud_opacity=0, hud_opacity_elements='waveform=1', hud_blur=blur)
                np.testing.assert_array_equal(renderer.render_field(field, 1, wave=quiet), baseline)
        black = np.asarray(Renderer(320, 180, palette='black-hot', wave_style='digital-circuit').render_field(field, 1))
        neutral = np.asarray(Renderer(320, 180, palette='black-hot', hud=False).render_field(field, 1))
        self.assertTrue(np.all(black <= neutral))
        np.testing.assert_array_equal(black[..., 0], black[..., 1])
        np.testing.assert_array_equal(black[..., 1], black[..., 2])

    def test_vocoder_rows_follow_local_audio_and_detail_changes_row_count(self):
        signal = np.repeat([.2, 0, .002], 100)
        mask = np.asarray(inkblot_mask(67, 540, signal, 0, style='digital-circuit'))
        self.assertFalse(mask[200:340].any())
        self.assertGreater(np.count_nonzero(mask[:160].max(axis=0)),
                           np.count_nonzero(mask[380:].max(axis=0)))
        coarse = np.asarray(inkblot_mask(67, 540, np.ones(256), 0, style='digital-circuit', detail=0))
        fine = np.asarray(inkblot_mask(67, 540, np.ones(256), 0, style='digital-circuit', detail=1))
        self.assertGreater(np.count_nonzero(np.diff(fine.max(axis=1).astype(bool))),
                           np.count_nonzero(np.diff(coarse.max(axis=1).astype(bool))))

    def test_new_styles_keep_other_hud_pixels_and_work_with_opacity_neon(self):
        field = np.full((270, 480), 100, np.uint8)
        reference = None
        for style in DIGITAL_STYLES:
            renderer = Renderer(480, 270, wave_style=style, wave_width=.14, wave_height=1,
                                hud_glyphs='cyber', neon=True, hud_opacity_elements='waveform=0.5')
            image = np.asarray(renderer.render_field(field, 1))
            if reference is not None:
                np.testing.assert_array_equal(image[:, 160:], reference[:, 160:])
            reference = image
            hidden = Renderer(480, 270, wave_style=style, hud=False).render_field(field, 1)
            np.testing.assert_array_equal(hidden, Image.new('RGB', (480, 270), tuple(renderer.palette[100])))


if __name__ == '__main__':
    unittest.main()
