"""Alternative reticles keep acquisition, flash, opacity and outline semantics."""
import unittest

import numpy as np
from PIL import Image

from yautja.target import TARGET_SHAPES, TargetOverlay, detail_shapes
from yautja.render import Renderer


class TargetShapeTests(unittest.TestCase):
    targets = [{'id': 'S001-F001', 'bbox': [.3, .1, .7, .9]}]
    colors = ((255, 0, 0), (255, 255, 255))

    def test_each_shape_is_distinct_and_honors_hiding_blur_and_flash(self):
        background = Image.new('RGB', (480, 270))
        signatures = []
        for shape in TARGET_SHAPES:
            with self.subTest(shape=shape):
                overlay = TargetOverlay(shape=shape)
                for time in (0, .3, .6, .9, 1.2, 1.4):
                    frame = np.asarray(overlay.draw(background, time, self.targets, self.colors, shot='S001'))
                    if time == .9:
                        signatures.append(frame.tobytes())
                        self.assertEqual(frame[..., 1].max(), 0)
                self.assertGreater(frame[..., 1].max(), 200)
                hidden = TargetOverlay(shape=shape, opacity=0, stroke=4, blur=5).draw(background, 0, self.targets, self.colors, static=True)
                self.assertEqual(np.asarray(hidden).max(), 0)
                steady = TargetOverlay(shape=shape, flash_rate=0, stroke=3, blur=4)
                soft = np.asarray(steady.draw(background, 0, self.targets, self.colors, static=True))
                self.assertGreater(soft.max(), 0)
                self.assertNotEqual(soft.tobytes(), signatures[-1])
        self.assertEqual(len(set(signatures)), len(TARGET_SHAPES))

    def test_triangle_dots_appear_only_at_lock_and_reset_after_loss(self):
        base, dots = TargetOverlay(), TargetOverlay(shape='triangle-dots')
        background = Image.new('RGB', (480, 270))
        for time in (0, .3, .6, .79):
            a = base.draw(background, time, self.targets, self.colors)
            b = dots.draw(background, time, self.targets, self.colors)
            np.testing.assert_array_equal(np.asarray(a), np.asarray(b))
        a = np.asarray(base.draw(background, .81, self.targets, self.colors))
        b = np.asarray(dots.draw(background, .81, self.targets, self.colors))
        added = b[..., 0].astype(np.int16) - a[..., 0].astype(np.int16)
        self.assertGreater(np.count_nonzero(added > 10), 30)
        base.draw(background, 1., [], self.colors)
        dots.draw(background, 1., [], self.colors)
        np.testing.assert_array_equal(np.asarray(base.draw(background, 1.1, self.targets, self.colors)),
                                      np.asarray(dots.draw(background, 1.1, self.targets, self.colors)))

    def test_triangle_dot_diameters_shrink_twelve_percent_without_moving_centers(self):
        _, dots = detail_shapes('triangle-dots', 100, True)
        self.assertEqual([(x,y) for x,y,_ in dots], [(0,-.23),(-.25,.16),(.25,.16)])
        for _, _, radius in dots:
            self.assertAlmostEqual(radius / .105, .88)
        self.assertEqual(detail_shapes('triangle-dots', 100, False)[1], [])
        self.assertEqual([r for _,_,r in detail_shapes('round-dot', 100, True)[1]], [.1]*3)

    def test_stroked_bands_and_dots_keep_hollow_interiors(self):
        size = (960,540)
        probes = {'crosshair':(.3,0), 'square':(.72,.55), 'square-cross':(.72,.55),
                  'square-mil':(.72,.55), 'square-x':(.72,.55), 'hollow-cross':(.3,.65),
                  'round-dot':(0,-.23), 'triangle-dots':(0,-.23)}
        for shape, (x,y) in probes.items():
            frames=[]
            for fill in ('filled','stroked'):
                target=TargetOverlay(shape=shape,fill=fill,flash_rate=0)
                image=target.draw(Image.new('RGB',size),0,self.targets,self.colors,static=True)
                _,cx,cy,lock_radius,_=target.placements[0]
                frames.append(np.asarray(image)[round(cy+y*lock_radius*1.3),round(cx+x*lock_radius*1.3),0])
            self.assertGreater(frames[0],200,shape)
            self.assertLess(frames[1],60,shape)

    def test_every_fill_mode_keeps_flash_opacity_and_still_behavior(self):
        size=(480,270)
        background=Image.new('RGB',size)
        for shape in TARGET_SHAPES:
            for fill in ('filled','stroked'):
                target=TargetOverlay(shape=shape,fill=fill)
                for time in (0,.3,.6,.9,1.2,1.4):
                    frame=np.asarray(target.draw(background,time,self.targets,self.colors))
                self.assertGreater(frame[...,1].max(),100,(shape,fill))
                hidden=TargetOverlay(shape=shape,fill=fill,opacity=0,stroke=4,blur=3)
                self.assertIsNone(hidden.draw(background,0,self.targets,self.colors,static=True).getbbox())

    def test_all_shapes_respect_no_hud_and_invalid_shapes_fail(self):
        image = Image.new('RGB', (320, 180), (80, 80, 80))
        for shape in TARGET_SHAPES:
            renderer = Renderer(320, 180, target_shape=shape, hud=False)
            np.testing.assert_array_equal(np.asarray(renderer.render(image, 0, targets=self.targets)),
                                          np.asarray(renderer.render(image, 0)))
        for shape in ('typo', 'square-dot'):
            with self.subTest(shape=shape), self.assertRaises(ValueError):
                TargetOverlay(shape=shape)

    def test_round_dot_has_four_gaps_and_three_center_dots_only_on_lock(self):
        background = Image.new('RGB', (480, 270))
        overlay = TargetOverlay(shape='round-dot', flash_rate=0)

        def assert_three_dots(frame):
            # Count separate rendered dots, excluding the outer ring.
            pixels = set(map(tuple, np.argwhere(frame[112:158, 217:263, 0] > 128)))
            components = []
            while pixels:
                pending, count = [pixels.pop()], 0
                while pending:
                    y, x = pending.pop()
                    count += 1
                    for neighbor in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                        if neighbor in pixels:
                            pixels.remove(neighbor)
                            pending.append(neighbor)
                components.append(count)
            self.assertEqual(len(components), 3)
            self.assertGreater(min(components), 40)
            self.assertEqual(frame[135, 240, 0], 0, 'The dots must stay separate')

        for time in (0, .3, .6, .79):
            frame = np.asarray(overlay.draw(background, time, self.targets, self.colors))
            self.assertEqual(frame[112:158, 217:263].max(), 0)
        frame = np.asarray(overlay.draw(background, .81, self.targets, self.colors))
        assert_three_dots(frame)
        y, x = np.nonzero(frame[..., 0] > 128)
        radii = np.hypot(x - 239.5, y - 134.5)
        ring = radii[radii > 25]
        self.assertGreater(ring.size, 500)
        # A ring keeps its distance from the center at every angle; square
        # brackets would put the diagonal corners much farther out.
        self.assertLess(ring.max() / ring.min(), 1.2)
        dx, dy = x[radii > 25] - 239.5, y[radii > 25] - 134.5
        self.assertGreater(np.minimum(np.abs(dx), np.abs(dy)).min(), 4,
                           'The outline must leave clear gaps at all four cardinal directions')
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            self.assertGreater(np.count_nonzero((dx * sx > 0) & (dy * sy > 0)), 100,
                               'Each quadrant must retain a visible circular arc')
        empty = overlay.draw(background, 1., [], self.colors)
        np.testing.assert_array_equal(np.asarray(empty), np.asarray(background))
        frame = np.asarray(overlay.draw(background, 1.1, self.targets, self.colors))
        self.assertEqual(frame[112:158, 217:263].max(), 0)
        still = np.asarray(overlay.draw(background, 0, self.targets, self.colors, static=True))
        assert_three_dots(still)
