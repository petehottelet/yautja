"""Digital waveform shapes are distinct, block-aligned and audio driven."""
import unittest
import numpy as np
from PIL import Image

from yautja.cli import parser
from yautja.render import Renderer
from yautja.waveform import DIGITAL_STYLES, inkblot_mask


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
            if style == 'digital-circuit':
                self.assertGreater(np.ptp(np.nonzero(b)[0]), np.ptp(np.nonzero(a)[0]))
                masks.append(b)
                continue
            self.assertGreater(np.ptp(np.nonzero(b)[1]), np.ptp(np.nonzero(a)[1]))
            # All visible transitions fall on the chosen square cell lattice.
            edges = np.nonzero(np.diff(b.astype(int), axis=1))[1] + 1
            pixel = max(2, round(84 / (14 + .6 * 18)))
            self.assertTrue(np.all(edges % pixel == 0))
            masks.append(b)
        for i in range(3):
            for j in range(i + 1, 3):
                self.assertGreater(np.count_nonzero(masks[i] != masks[j]), 1000)

    def test_vocoder_has_three_separated_columns_and_a_taller_center(self):
        mask = np.asarray(inkblot_mask(120, 540, np.full(256, .15), 0, style='digital-circuit'))
        lit_columns = np.flatnonzero(mask.max(axis=0))
        groups = np.split(lit_columns, np.flatnonzero(np.diff(lit_columns) > 1) + 1)
        self.assertEqual(len(groups), 3)
        heights = []
        for group in groups:
            lit_rows = np.flatnonzero(mask[:, group].max(axis=1))
            heights.append(np.ptp(lit_rows))
            self.assertGreater(np.count_nonzero(np.diff(lit_rows) > 1), 5)
            self.assertAlmostEqual((lit_rows.min() + lit_rows.max()) / 2, 270, delta=1)
        self.assertGreater(heights[1], max(heights[0], heights[2]))
        np.testing.assert_array_equal(mask, inkblot_mask(120, 540, np.full(256, .15), 5, style='digital-circuit'))

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
