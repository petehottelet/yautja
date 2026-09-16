import unittest

import numpy as np
from PIL import Image

from yautja.cli import parser
from yautja.geometry import GeometryStyle
from yautja.looks import normalize_preset
from yautja.render import Renderer, STOPS
from yautja.semantic import Subject
from yautja.target import TargetOverlay, detail_shapes, TARGET_SHAPES


class PresetRefreshTests(unittest.TestCase):
    size = (480, 270)

    def subjects(self):
        result = []
        for identity, x in enumerate((80, 320), 1):
            mask = np.zeros((270, 480), np.float32)
            mask[45:240, x:x+70] = 1
            result.append(Subject(mask, 'person', .95, track_id=identity))
        return result

    def test_focus_has_one_constant_size_target_during_handoff_and_search(self):
        renderer = Renderer(*self.size, look_preset='focus')
        positions, radii = [], []
        for i in range(81):
            renderer.draw_targets(Image.new('RGB', self.size), i/20, self.subjects(), None,
                                  ((180,90,255),)*2, shot=1)
            self.assertEqual(len(renderer.target_overlay.placements), 1)
            _, x, y, radius, opacity = renderer.target_overlay.placements[0]
            positions.append((x,y)); radii.append(radius)
            self.assertEqual(opacity, 1)
        self.assertLess(max(np.linalg.norm(np.diff(positions, axis=0), axis=1)), 40)
        self.assertGreater(positions[-1][0] - positions[0][0], 150)
        self.assertEqual(len(set(radii)), 1)
        renderer.draw_targets(Image.new('RGB', self.size), 4.1, [], None, ((180,90,255),)*2, shot=1)
        self.assertEqual(len(renderer.target_overlay.placements), 1)
        self.assertEqual(renderer.target_overlay.placements[0][0], 'search')
        renderer.draw_targets(Image.new('RGB', self.size), 4.2, self.subjects(), [], ((180,90,255),)*2, shot=1)
        self.assertFalse(renderer.target_overlay.placements)

    def test_motion_resets_on_cut_and_seek_but_not_same_frame(self):
        g = GeometryStyle(target_mode='cycle', target_motion='persistent')
        one, two = self.subjects()
        p = g.prepare_targets([one], None, 0, 1, self.size)[0]['center']
        a = g.prepare_targets([two], None, .05, 1, self.size)[0]['center']
        b = g.prepare_targets([two], None, .05, 1, self.size)[0]['center']
        self.assertEqual(a, b)
        c = g.prepare_targets([two], None, .1, 2, self.size)[0]['center']
        self.assertGreater(c[0]-a[0], .3)
        d = g.prepare_targets([one], None, 0, 2, self.size)[0]['center']
        self.assertEqual(d, p)

    def test_hexagon_inset_ring_ten_satellites_and_center_square(self):
        paths, dots = detail_shapes('hexagon', 100, True)
        self.assertEqual(len(paths), 13)
        self.assertFalse(dots)
        self.assertEqual([len(paths[i][0]) for i in (0,1,12)], [6,64,4])
        self.assertAlmostEqual(np.linalg.norm(paths[1][0][0]), .9*.74*np.cos(np.pi/6))
        centers = [np.mean(path, axis=0) for path, _ in paths[2:12]]
        self.assertEqual(sum(np.linalg.norm(c) > .74 for c in centers), 4)
        self.assertEqual(sum(np.linalg.norm(c) < .64 for c in centers), 6)

    def test_sphere_has_straight_facets_shared_vertices_and_stable_seed(self):
        a = GeometryStyle(geo_grid_projection='sphere')
        vertices, edges, _ = a.lattice(self.size, 42)
        curves = np.asarray(a.curves)
        self.assertTrue(np.isfinite(curves).all())
        self.assertEqual(curves.shape[1:], (2,2))
        np.testing.assert_array_equal(curves,vertices[np.asarray(edges)])
        # The straight sides still connect a 3D spherical mesh, not a flat grid.
        vectors = a.sphere_cache[1]
        np.testing.assert_allclose(np.linalg.norm(vectors,axis=1),1)
        self.assertGreater(np.ptp(vectors[:,2]),1.5)
        b = GeometryStyle(geo_grid_projection='sphere')
        b.lattice(self.size, 42)
        np.testing.assert_array_equal(curves, b.curves)
        wide = GeometryStyle(geo_grid_projection='sphere', geo_grid_scale=220)
        wide.lattice(self.size, 42)
        self.assertFalse(np.array_equal(curves, wide.curves))
        a.lattice((270,480), 42)
        self.assertFalse(np.array_equal(curves, a.curves))

    def test_murphy_defaults_and_live_mask_outline(self):
        renderer = Renderer(*self.size, look_preset='murphy')
        self.assertEqual(renderer.typography.report()['hud_font_family'], 'Michroma')
        self.assertEqual(renderer.typography.report()['hud_font_weight'], 'Medium (synthetic)')
        self.assertEqual(renderer.target_overlay.scale, 1.25)
        self.assertFalse(renderer.show_timecode)
        self.assertEqual(renderer.hud_opacities['readout'], 0)
        self.assertEqual(renderer.hud_colors['target'], renderer.hud_colors['target-outline'])
        self.assertTrue(renderer.neon)
        renderer = Renderer(*self.size, look_preset='murphy', neon=False, glow=0,
                            hud_opacity=0, hud_opacity_elements='target-outline=1')
        one, two = self.subjects()
        g = renderer.geometry
        g.prepare_targets([one,two], None, 0, 1, self.size, True)
        image = Image.new('RGB', self.size)
        g.draw_outline(renderer, image, [one,two])
        pixels = np.asarray(image).max(axis=2)
        self.assertGreater(pixels[:,80:150].sum(), 0)
        self.assertEqual(pixels[:,320:].sum(), 0)
        one.mask = np.roll(one.mask, 25, axis=1)
        image = Image.new('RGB', self.size)
        g.draw_outline(renderer, image, [one,two])
        self.assertEqual(np.asarray(image)[:,:105].sum(), 0)

    def test_standalone_outline_works_without_custom_colors_or_neon(self):
        renderer = Renderer(*self.size, target_mode='auto', target_outline=True, glow=0)
        image = renderer.draw_targets(Image.new('RGB',self.size), 0, self.subjects(), None,
                                      ((0,0,0),)*2, static=True)
        self.assertGreater(np.asarray(image).max(), 0)
        g = GeometryStyle(target_mode='auto')
        subject = self.subjects()[0]
        subject.opacity = .1
        self.assertEqual(g.prepare_targets([subject],None,0,1,self.size)[0]['opacity'], .1)

    def test_cursor_blinks_without_moving_or_resizing_caption(self):
        renderer = Renderer(*self.size, target_label='TARGETING', target_cursor=True, target_label_scale=1.8,
                            target_motion='persistent', hud_font='orbitron-medium')
        candidates = [{'id':'one','bbox':(.2,.2,.4,.8)}]
        frames, boxes = [], []
        for time in (.1,.6,1.1):
            frames.append(renderer.draw_targets(Image.new('RGB',self.size),time,[],candidates,((0,0,0),)*2,shot=1))
            boxes.append(renderer.geometry.label_box)
        self.assertEqual(boxes[0], boxes[1]); self.assertEqual(boxes[1], boxes[2])
        crop = [np.asarray(frame.crop(boxes[0])) for frame in frames]
        self.assertGreater(np.abs(crop[0].astype(int)-crop[1]).sum(), 0)
        np.testing.assert_array_equal(crop[0],crop[2])

    def test_shape_fill_and_stroke_options_produce_different_artwork(self):
        target = [{'id':'x','bbox':(.1,.1,.9,.9)}]
        for shape in TARGET_SHAPES:
            frames = [np.asarray(TargetOverlay(shape=shape, fill=fill).draw(
                Image.new('RGB',self.size),0,target,((255,50,30),)*2,static=True))
                for fill in ('filled','stroked')]
            self.assertTrue(np.isfinite(frames).all())
            self.assertFalse(np.array_equal(*frames), shape)

    def test_aliases_new_defaults_and_original_costa_rica_palette(self):
        self.assertEqual(normalize_preset('HotTropic'),'yautja')
        self.assertEqual(normalize_preset('hot-tropic'),'yautja')
        costa = Renderer(*self.size, look_preset='costa-rica')
        self.assertEqual(costa.palette_name,'costa-rica')
        self.assertFalse(costa.scanlines)
        self.assertEqual(costa.colors.stops, STOPS)
        default = Renderer(*self.size)
        self.assertEqual(default.thermal,'luminance')
        self.assertTrue(default.scanlines)
        for tokens in (['--stylepreset','focus','--target-motion','acquire','--target-fill','filled'],
                       ['--target-motion','acquire','--target-fill','filled','--stylepreset','focus']):
            args = parser().parse_args(tokens)
            self.assertEqual((args.target_motion,args.target_fill),('acquire','filled'))


if __name__ == '__main__':
    unittest.main()
