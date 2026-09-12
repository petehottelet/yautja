"""Behavior tests for simulated heat and tracking; no model downloads."""
import importlib.util
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from thermal import HeatField
from semantic import Subject, SemanticTracker
from render import Renderer
from yautja import main


def subject(x=60, y=30, width=70, height=120, shape=(180, 320), label='person', hot=False):
    mask = np.zeros(shape, dtype=np.float32)
    mask[y:y+height, x:x+width] = 1
    return Subject(mask, label, .9, hot=hot)


class HeatTests(unittest.TestCase):
    def test_dark_subject_is_hotter_than_white_background(self):
        frame = np.full((180, 320, 3), 255, dtype=np.uint8)
        frame[30:150, 60:130] = 0
        heat = HeatField(320, 180).build(Image.fromarray(frame), [subject()])
        self.assertGreater(heat[65:130, 80:110].min(), 175)
        self.assertLess(heat[:, 170:].max(), 100)

    def test_no_detection_does_not_invent_hot_objects(self):
        heat = HeatField(320, 180).build(Image.new('RGB', (320, 180), 'white'), [])
        self.assertLess(heat.max(), 100)

    def test_fabric_and_facial_texture_do_not_control_subject_heat(self):
        black = Image.new('RGB', (320, 180))
        textured = np.zeros((180, 320, 3), dtype=np.uint8)
        textured[30:150:2, 60:130:2] = 255
        field = HeatField(320, 180)
        a = field.build(black, [subject()])
        b = field.build(Image.fromarray(textured), [subject()])
        np.testing.assert_array_equal(a[55:130, 80:110], b[55:130, 80:110])
        self.assertGreater(int(a[60:130, 80:110].max()) - int(a[60:130, 80:110].min()), 10)

    def test_hot_override_overlap_order_and_fade(self):
        frame = Image.new('RGB', (320, 180))
        warm, hot = subject(), subject(x=90, hot=True)
        field = HeatField(320, 180)
        a = field.build(frame, [warm, hot])
        np.testing.assert_array_equal(a, field.build(frame, [hot, warm]))
        self.assertGreater(a[80, 135], field.build(frame, [subject(x=90)])[80, 135])
        hot.opacity = 0
        np.testing.assert_array_equal(field.build(frame, [hot]), field.build(frame, []))

    def test_portrait_and_tiny_sensor_outputs_match_frame(self):
        for size in [(180, 320), (2, 2), (640, 360)]:
            result = HeatField(*size, resolution=160).build(Image.new('RGB', size), [])
            self.assertEqual(result.shape, size[::-1])
            self.assertEqual(result.dtype, np.uint8)

    def test_annotations_are_deterministic_and_out_of_main_hud(self):
        frame = Image.new('RGB', (640, 360))
        one = subject(shape=(360, 640), x=300, y=130)
        one.track_id = 4
        renderer = Renderer(640, 360, thermal='semantic', verbose=True, grain=0)
        a = np.array(renderer.render(frame, 0, subjects=[one]))
        np.testing.assert_array_equal(a, np.array(renderer.render(frame, 0, subjects=[one])))
        plain = np.array(Renderer(640, 360, thermal='semantic', grain=0).render(frame, 0, subjects=[one]))
        self.assertTrue(np.any(a != plain))
        np.testing.assert_array_equal(a[:, :50], plain[:, :50])
        np.testing.assert_array_equal(a[:45], plain[:45])

    def test_large_callouts_stay_near_boundaries_without_covering_subjects(self):
        people = [subject(x=210, y=100, width=80, height=150, shape=(360, 640)),
                  subject(x=450, y=120, width=90, height=170, shape=(360, 640))]
        for track_id, person in enumerate(people, 1):
            person.track_id = track_id
        renderer = Renderer(640, 360, thermal='semantic', verbose=True)
        layout = renderer.annotation_layout(people)
        self.assertEqual(len(layout), 2)
        for item in layout:
            self.assertGreaterEqual(item['size'], 15)
            self.assertLessEqual(np.linalg.norm(np.subtract(item['anchor'], item['target'])), 52)
            x0, y0, x1, y1 = item['rect']
            self.assertGreaterEqual(x0, 65)
            self.assertGreaterEqual(y0, 50)
            self.assertLessEqual(x1, 640)
            self.assertLessEqual(y1, 360)
            for person in people:
                self.assertFalse(np.any(person.mask[y0:y1, x0:x1] > .5))
        a, b = [item['rect'] for item in layout]
        self.assertFalse(a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1])

    def test_callout_rows_use_distinct_artwork_across_nearby_tracks(self):
        renderer = Renderer(640, 360, verbose=True)
        artwork = []
        for track_id in range(1, 9):
            row = renderer.callout_symbols(track_id)
            self.assertEqual(len(row), 6)
            artwork.extend(renderer.callout_glyph(pattern, 48).tobytes() for pattern in row)
        self.assertEqual(len(set(artwork)), 48)

    def test_callout_identity_is_stable_independent_of_order_and_seeded(self):
        renderer = Renderer(640, 360, verbose=True, seed=42)
        ids = (1, 2, 7, 12, 10001)
        first = {track_id: renderer.callout_symbols(track_id) for track_id in ids}
        other = Renderer(640, 360, verbose=True, seed=42)
        for track_id in reversed(ids):
            self.assertEqual(first[track_id], other.callout_symbols(track_id))
        changed = Renderer(640, 360, verbose=True, seed=43)
        self.assertTrue(all(first[track_id] != changed.callout_symbols(track_id) for track_id in ids))
        self.assertNotEqual(first[1], first[10001])

    def test_callout_shading_preserves_dim_outlines_and_bright_segments(self):
        renderer = Renderer(640, 360, verbose=True)
        for height in (15, 30):
            outlines = renderer.callout_glyph(0, height)
            shaded = renderer.callout_glyph(renderer.callout_symbols(1)[0], height)
            off, on = np.asarray(outlines), np.asarray(shaded)
            self.assertGreaterEqual(np.count_nonzero((off > 10) & (on > 10)),
                                    .95 * np.count_nonzero(off > 10))
            self.assertGreater(np.count_nonzero(off > 10), 20)
            self.assertGreater(int(on.max()), int(off.max()) * 2)
            self.assertGreater(np.count_nonzero((on > 90) & (on < 200)), 10)

    def test_callout_follows_motion_and_drops_expired_layout_history(self):
        renderer = Renderer(640, 360, thermal='semantic', verbose=True)
        one = subject(x=250, y=110, width=80, height=140, shape=(360, 640))
        one.track_id = 7
        first = renderer.annotation_layout([one])[0]
        one.mask = np.roll(one.mask, 8, axis=1)
        moved = renderer.annotation_layout([one])[0]
        self.assertAlmostEqual(moved['rect'][0] - first['rect'][0], 8, delta=1)
        self.assertAlmostEqual(moved['rect'][1], first['rect'][1], delta=1)
        self.assertEqual(renderer.annotation_layout([]), [])
        self.assertEqual(renderer.annotation_positions, {})

    def test_crowded_or_small_frames_never_force_labels_over_the_hud(self):
        for width, height in ((160, 90), (180, 320), (640, 360)):
            person = subject(x=0, y=0, width=width, height=height, shape=(height, width))
            renderer = Renderer(width, height, thermal='semantic', verbose=True)
            self.assertEqual(renderer.annotation_layout([person]), [])


class FakeDetector:
    device = 'cpu'

    def __init__(self, batches):
        self.batches = iter(batches)

    def detect(self, frame):
        return next(self.batches, [])


@unittest.skipUnless(importlib.util.find_spec('cv2'), 'optional OpenCV not installed')
class TrackingTests(unittest.TestCase):
    def test_match_preserves_ids_then_missing_track_fades_and_expires(self):
        frame = Image.new('RGB', (320, 180), (50, 50, 50))
        tracker = SemanticTracker(FakeDetector([[subject()], [subject(x=63)]]), interval=.5)
        first = tracker.update(frame, 0)[0].track_id
        self.assertEqual(tracker.update(frame, .5)[0].track_id, first)
        self.assertLess(tracker.update(frame, 1.25)[0].opacity, 1)
        self.assertEqual(tracker.update(frame, 1.6), [])

    def test_scene_cut_clears_heat_and_ids_immediately(self):
        tracker = SemanticTracker(FakeDetector([[subject()], [subject()]]), interval=1.)
        first = tracker.update(Image.new('RGB', (320, 180)), 0)[0].track_id
        second = tracker.update(Image.new('RGB', (320, 180), 'white'), .1)[0].track_id
        self.assertNotEqual(first, second)
        self.assertEqual(len(tracker.tracks), 1)
        self.assertEqual(tracker.scene_cuts, 1)

    def test_optical_flow_moves_the_mask_in_the_correct_direction(self):
        rng = np.random.default_rng(3)
        pixels = rng.integers(20, 160, (180, 320), dtype=np.uint8)
        tracker = SemanticTracker(FakeDetector([[subject()]]), interval=1.)
        tracker.update(Image.fromarray(pixels).convert('RGB'), 0)
        moved = np.roll(pixels, 4, axis=1)
        tracks = tracker.update(Image.fromarray(moved).convert('RGB'), .1)
        cols = np.nonzero(tracks[0].mask > .5)[1]
        self.assertAlmostEqual(float(cols.mean()), 98.5, delta=1.)
        self.assertEqual(tracker.detection_frames, 1)

    def test_category_change_cannot_inherit_person_identity(self):
        frame = Image.new('RGB', (320, 180))
        tracker = SemanticTracker(FakeDetector([[subject()], [subject(label='dog')]]))
        first = tracker.update(frame, 0)[0].track_id
        dog = next(t for t in tracker.update(frame, .5) if t.label == 'dog')
        self.assertNotEqual(first, dog.track_id)


class ArgumentTests(unittest.TestCase):
    def test_invalid_semantic_options_fail_before_conversion(self):
        for options in [('--verbose',), ('--sensor-resolution', '0'), ('--detect-interval', 'nan'), ('--confidence', '2')]:
            with self.subTest(options=options), patch('yautja.convert') as convert, patch('sys.stderr', new_callable=io.StringIO):
                with self.assertRaises(SystemExit) as caught:
                    main(['input.mp4', 'output.mp4', *options])
                self.assertEqual(caught.exception.code, 2)
                convert.assert_not_called()


if __name__ == '__main__':
    unittest.main()
