import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw

from yautja.hud import HudPanel, grid_clearance
from yautja.render import Renderer
from yautja.semantic import Subject


class GridClearanceTests(unittest.TestCase):
    def test_clearance_feathers_and_ignores_hidden_or_decorative_layers(self):
        panel = HudPanel('RGBA', (120, 160), {'waveform': 0}, ('waveform',), {'waveform': 1})
        ImageDraw.Draw(panel.layer('waveform')).rectangle((20, 20, 60, 140), fill='white')
        mask = np.asarray(grid_clearance((400, 200), [(panel, 0, 0)], 1))
        self.assertGreater(mask[80, 40], 210)
        self.assertGreater(mask[80, 70], mask[80, 85])
        self.assertGreater(mask[80, 85], 0)
        self.assertEqual(mask[:, 120:].max(), 0)
        panel.opacities['waveform'] = 0
        self.assertIsNone(grid_clearance((400, 200), [(panel, 0, 0)], 1).getbbox())
        decoration = HudPanel('RGBA', (400, 200), {'subject-code': 0}, ('subject-code',), {'subject-code': 1})
        ImageDraw.Draw(decoration.layer('subject-code')).rectangle((0, 0, 399, 199), fill='white')
        self.assertIsNone(grid_clearance((400, 200), [(decoration, 0, 0)], 1).getbbox())

    def test_grid_is_dimmer_near_hud_but_identical_away_from_it(self):
        size = (480, 270)
        for neon in (False, True):
            renderer = Renderer(*size, look_preset='focus', neon=neon, glow=0)
            panels = []
            original = grid_clearance
            def capture(size, layers, scale):
                mask = original(size, layers, scale)
                panels.append(mask)
                return mask
            with patch('yautja.render.grid_clearance', side_effect=capture):
                renderer.render(Image.new('RGB', size, '#203040'), .5)
            mask = panels[0]
            before, after = Image.new('RGB', size), Image.new('RGB', size)
            renderer.geometry.draw_grid(renderer, before, .5)
            renderer.geometry.draw_grid(renderer, after, .5, clearance=mask)
            a, b = np.asarray(before).astype(float), np.asarray(after).astype(float)
            near = np.asarray(mask) > 180
            self.assertGreater(a[near].sum(), 0)
            self.assertLess(b[near].sum(), a[near].sum() * .4)
            np.testing.assert_array_equal(a[110:230, 180:350], b[110:230, 180:350])

    def test_layout_pass_preserves_led_backing_and_subject_composition(self):
        size = (320, 180)
        frame = Image.new('RGB', size, '#203040')
        mask = np.zeros((180, 320), np.float32)
        mask[40:170, 120:170] = 1
        subjects = [Subject(mask, 'person', .95, track_id=1)]
        # An invisible grid still takes the layout path. It must leave all other
        # artwork unchanged, including non-emissive LED material and neon.
        for neon in (False, True):
            for wave_style in ('trace', 'rorschach'):
                settings = dict(look_preset='relic', neon=neon, wave_style=wave_style,
                                wave_display='led', verbose=True, show_timecode=True,
                                hud_opacity_elements='geo-grid=0')
                on = Renderer(*size, **settings)
                off = Renderer(*size, **settings, geo_grid=False)
                for time in (.5, .6):
                    np.testing.assert_array_equal(on.render(frame, time, subjects=subjects),
                                                  off.render(frame, time, subjects=subjects))


if __name__ == '__main__':
    unittest.main()
