"""Synthetic surface behavior and optional sensor texture, without models."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from render import Renderer
from semantic import Subject, SurfacePart, SemanticTracker
from thermal import SurfaceHeatField


def mask(x, y, w, h):
    result = np.zeros((240, 320), dtype=np.float32)
    result[y:y+h, x:x+w] = 1
    return result


def person():
    return Subject(mask(80, 20, 140, 200), 'person', .95, track_id=1, parts=[
        SurfacePart(mask(110, 25, 55, 45), 'face', .9),
        SurfacePart(mask(80, 70, 140, 100), 'jacket', .9),
        SurfacePart(mask(130, 95, 45, 45), 'camera', .9),
    ])


class SurfaceTests(unittest.TestCase):
    def test_skin_garment_and_gear_have_separate_warmth_and_stay_in_owner(self):
        field = SurfaceHeatField(320, 240, resolution=320)
        frame, owner = Image.new('RGB', (320, 240), 'white'), person()
        heat = field.build(frame, [owner])
        self.assertGreater(int(heat[45, 135]) - int(heat[90, 100]), 45)
        self.assertGreater(int(heat[90, 100]) - int(heat[115, 150]), 60)
        self.assertLess(heat[100, 270], 105)
        # Even a bad overlarge part cannot color outside its owning silhouette.
        owner.parts.append(SurfacePart(np.ones((240, 320), np.float32), 'hand', .99))
        outside = field.build(frame, [owner])
        np.testing.assert_array_equal(heat[:, 245:], outside[:, 245:])

    def test_cool_foreground_gear_occludes_overlapping_warm_person(self):
        frame, owner = Image.new('RGB', (320, 240)), person()
        behind = Subject(mask(120, 80, 70, 90), 'person', .99, hot=True, track_id=2)
        field = SurfaceHeatField(320, 240, resolution=320)
        result = field.build(frame, [owner, behind])
        np.testing.assert_array_equal(result, field.build(frame, [behind, owner]))
        self.assertLess(result[115, 150], 110)
        owner.opacity = 0
        np.testing.assert_array_equal(field.build(frame, [owner, behind]), field.build(frame, [behind]))

    def test_no_source_face_detail_and_uncertain_parts_fall_back(self):
        frame, owner = Image.new('RGB', (320, 240)), person()
        field = SurfaceHeatField(320, 240, resolution=320)
        reference = field.build(frame, [owner])
        pixels = np.asarray(frame).copy()
        pixels[25:70:2, 110:165:2] = 255
        changed = field.build(Image.fromarray(pixels), [owner])
        np.testing.assert_array_equal(reference[35:60, 120:155], changed[35:60, 120:155])
        owner.parts = []
        fallback = field.build(frame, [owner])
        owner.parts = [SurfacePart(mask(80, 20, 140, 200), 'camera', .2),
                       SurfacePart(mask(80, 20, 140, 200), 'face', float('nan')),
                       SurfacePart(mask(80, 20, 140, 200), 'unknown', .99)]
        np.testing.assert_array_equal(fallback, field.build(frame, [owner]))

    def test_clothing_shading_is_normalized_not_absolute_brightness(self):
        owner, field = person(), SurfaceHeatField(320, 240, resolution=320)
        pixels = np.zeros((240, 320, 3), dtype=np.uint8)
        pixels[70:170, 80:220] = np.linspace(30, 130, 140, dtype=np.uint8)[None, :, None]
        brighter = pixels.copy()
        brighter[70:170, 80:220] += 60
        a = field.build(Image.fromarray(pixels), [owner]).astype(float)
        b = field.build(Image.fromarray(brighter), [owner]).astype(float)
        self.assertLess(np.abs(a[80:155, 90:120] - b[80:155, 90:120]).mean(), 1.5)
        flat = field.build(Image.new('RGB', (320, 240), (80, 80, 80)), [owner])
        self.assertGreater(np.abs(a[80:155, 90:120] - flat[80:155, 90:120]).mean(), 1)


class SensorTextureTests(unittest.TestCase):
    def test_texture_is_opt_in_for_every_mode(self):
        frame = Image.new('RGB', (320, 240), (100, 100, 100))
        for mode in ('classic', 'silhouette', 'cinematic', 'detailed'):
            with self.subTest(mode=mode):
                plain = Renderer(320, 240, thermal=mode).render(frame, 0, subjects=[person()])
                explicit = Renderer(320, 240, thermal=mode, sensor_texture=False, grain=0, pixelation=0, scanlines=False).render(frame, 0, subjects=[person()])
                textured = Renderer(320, 240, thermal=mode, sensor_texture=True).render(frame, 0, subjects=[person()])
                np.testing.assert_array_equal(np.asarray(plain), np.asarray(explicit))
                self.assertFalse(np.array_equal(np.asarray(plain), np.asarray(textured)))

    def test_texture_is_seeded_and_time_varying_but_hud_is_unchanged(self):
        frame = Image.new('RGB', (640, 360), (100, 100, 100))
        renderer = Renderer(640, 360, sensor_texture=True)
        # Capture HUD layers before compositing onto a different background.
        layers = []
        with patch.object(renderer, 'composite', side_effect=lambda image, overlay, x, y: layers.append(np.array(overlay))):
            a = np.array(renderer.render(frame, 0))
        b = np.array(Renderer(640, 360, sensor_texture=True).render(frame, 0))
        c = np.array(renderer.render(frame, .5))
        np.testing.assert_array_equal(a[100:280, 200:440], b[100:280, 200:440])
        self.assertFalse(np.array_equal(a[100:280, 200:440], c[100:280, 200:440]))
        other_seed = np.array(Renderer(640, 360, sensor_texture=True, seed=43).render(frame, 0))
        self.assertFalse(np.array_equal(a[100:280, 200:440], other_seed[100:280, 200:440]))
        clean_layers = []
        clean = Renderer(640, 360)
        with patch.object(clean, 'composite', side_effect=lambda image, overlay, x, y: clean_layers.append(np.array(overlay))):
            clean.render(frame, 0)
        self.assertEqual(len(layers), len(clean_layers))
        for actual, expected in zip(layers, clean_layers):
            np.testing.assert_array_equal(actual, expected)

    def test_zero_grain_retains_sensor_grid_and_scanlines(self):
        frame = Image.new('RGB', (640, 360), (100, 100, 100))
        textured = np.array(Renderer(640, 360, sensor_texture=True, grain=0).render(frame, 0))
        # Scanlines are visible even with no noise; quiet interiors stay uniform.
        self.assertTrue(np.all(textured[150, 250] <= textured[151, 250]))
        self.assertTrue(np.any(textured[150, 250] < textured[151, 250]))
        np.testing.assert_array_equal(textured[151, 200:400], np.tile(textured[151, 250], (200, 1)))

    def test_palette_is_independent_of_texture(self):
        self.assertEqual(Renderer(320, 240, thermal='realistic').palette_name, 'yautja')
        self.assertEqual(Renderer(320, 240, thermal='semantic').palette_name, 'yautja')
        for palette in ('yautja', 'ironbow'):
            a = Renderer(320, 240, thermal='realistic', palette=palette)
            b = Renderer(320, 240, thermal='realistic', palette=palette, sensor_texture=True)
            np.testing.assert_array_equal(a.palette, b.palette)


@unittest.skipUnless(importlib.util.find_spec('cv2'), 'optional OpenCV not installed')
class SurfaceTrackingTests(unittest.TestCase):
    def test_parts_follow_flow_and_missing_parts_are_removed_on_refresh(self):
        one, two = person(), person()
        two.parts = []
        batches = iter([[one], [two]])
        detector = SimpleNamespace(detect=lambda frame: next(batches), device='cpu')
        tracker = SemanticTracker(detector, interval=.5)
        pixels = np.random.default_rng(3).integers(20, 160, (240, 320), dtype=np.uint8)
        frame = Image.fromarray(pixels).convert('RGB')
        initial = tracker.update(frame, 0)[0]
        before = np.nonzero(initial.parts[0].mask > .5)[1].mean()
        moved_frame = Image.fromarray(np.roll(pixels, 4, axis=1)).convert('RGB')
        moved = tracker.update(moved_frame, .1)[0]
        after = np.nonzero(moved.parts[0].mask > .5)[1].mean()
        self.assertAlmostEqual(after - before, 4, delta=.5)
        refreshed = tracker.update(moved_frame, .5)[0]
        self.assertEqual(initial.track_id, refreshed.track_id)
        self.assertEqual(refreshed.parts, [])


if __name__ == '__main__':
    unittest.main()
