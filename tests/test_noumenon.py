"""Material determinism, visible ownership, projection and public preset contracts."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw

from yautja.cli import extra_report, main, material_subject_ids, parser
from yautja.figures import FigureCatalog, MaterialSelection
from yautja.noumenon import (FIELD_SIZE, WARMUP_TICKS, MaterialStyle, NoumenonMaterial,
                            glyph_mips, random_float)
from yautja.presets import VISUAL_OPTIONS, load_preset
from yautja.render import Renderer
from yautja.scene_material import (SceneMaterial, SurfaceMapper, estimate_room, homography,
                                   project, visible_ownership)
from yautja.semantic import Subject, SurfacePart
from tools.preview_noumenon import fixture


class NoumenonTests(unittest.TestCase):
    size = (240, 136)

    def renderer(self, **options):
        return Renderer(*self.size, look_preset='noumenon', **options)

    def test_preset_overrides_saved_roundtrip_and_report(self):
        args = parser().parse_args(['--stylepreset', 'noumenon'])
        self.assertEqual((args.scene_mode, args.hud, args.thermal, args.code_size), ('code', False, 'low-detail', 24.))
        self.assertEqual(args.material_edge_glow, 0)
        for argv in (['--material-face', 'cyber', '--stylepreset', 'noumenon'],
                     ['--stylepreset', 'noumenon', '--material-face', 'cyber']):
            self.assertEqual(parser().parse_args(argv).material_face, 'cyber')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'material.json'
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['--stylepreset', 'noumenon', '--material-mapping', '.4',
                                       '--material-subject-density', '1.4', '--material-subject-trail', '1.3',
                                       '--material-edge-glow', '.09', '--material-edge-shade', '.3',
                                       '--save-preset', str(path)]), 0)
            saved = load_preset(path)
            self.assertEqual(saved['settings']['material_mapping'], .4)
            self.assertEqual(saved['settings']['material_subject_density'], 1.4)
            self.assertEqual(saved['settings']['material_subject_trail'], 1.3)
            self.assertEqual(saved['settings']['material_edge_glow'], .09)
            self.assertEqual(saved['settings']['material_edge_shade'], .3)
            resolved = parser().parse_args(['--preset-file', str(path), '--material-glow', '.3'])
            self.assertEqual((resolved.scene_mode, resolved.material_mapping, resolved.material_glow), ('code', .4, .3))
            self.assertEqual(resolved.material_subject_trail, 1.3)
            self.assertEqual((resolved.material_edge_glow, resolved.material_edge_shade), (.09, .3))
        r = self.renderer()
        r.render(Image.new('RGB', self.size), 0)
        report = extra_report(r, None)
        self.assertEqual(report['material_time_origin'], 'output-relative')
        self.assertEqual(report['material_tick_hz'], 60)
        self.assertEqual(report['material_source'], 'noumenon')
        self.assertIn('material_mapping_mode', report)

    def test_invalid_settings_fail_before_media_or_models(self):
        for key, value in (('material_glow', float('nan')), ('material_mapping', -1),
                           ('material_mix', 1.1), ('material_foreground', 4), ('material_face', 'missing'),
                           ('material_subject_density', 3.1), ('material_subject_density', float('nan')),
                           ('material_subject_trail', .9), ('material_subject_trail', 2.1),
                           ('material_subject_trail', float('nan')), ('material_edge_glow', -1),
                           ('material_edge_glow', float('nan')), ('material_edge_shade', 1.1)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                MaterialStyle(**{key: value})
        with patch('yautja.cli.convert') as convert, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['missing.png', 'output.png', '--stylepreset', 'noumenon', '--material-glow', 'nan']), 1)
        convert.assert_not_called()

    def test_source_assets_and_blank_reference_slot(self):
        from importlib.resources import files
        receipt = json.loads(files('yautja').joinpath('assets/noumenon-source.json').read_text())
        self.assertIn('Copyright (c) 2018 Rezmason', receipt['engine_license'])
        atlas = glyph_mips()[0]
        self.assertEqual(atlas.shape, (249, 64, 64))
        self.assertEqual(atlas[4].max(), 0)
        self.assertTrue(np.all(atlas[np.arange(249) != 4].max(axis=(1, 2)) > 0))

    def test_symbol_closed_form_matches_reference_tick_recurrence(self):
        material = NoumenonMaterial(seed=17, speed=.8)
        age = material.initial_age.copy()
        sx, sy = material.sx, material.sy
        catalog = random_float(sx + 17, sy + 41) < .1
        symbols = np.floor(random_float(sx, sy) * np.where(catalog, 192, 57)).astype(int) + catalog * 57
        for tick in range(1, WARMUP_TICKS + 181):
            age += .03 * .8
            changed = age >= 1 - 1e-12
            age[changed] -= 1
            t = tick / 60 * .8
            catalog = random_float(sx + t + 17, sy + t + 41) < .1
            chosen = np.floor(random_float(sx + t, sy + t) * np.where(catalog, 192, 57)).astype(int) + catalog * 57
            symbols[changed] = chosen[changed]
        np.testing.assert_array_equal(material.field(3)[0], symbols)

    def test_random_access_fps_and_symbol_freeze(self):
        a, b = NoumenonMaterial(), NoumenonMaterial()
        for t in np.arange(61) / 30:
            a.field(float(t))
        for actual, expected in zip(a.field(2), b.field(2)):
            np.testing.assert_array_equal(actual, expected)
        for t in (1.5, 0., 1000., 2.):
            for actual, expected in zip(a.field(t), NoumenonMaterial().field(t)):
                np.testing.assert_array_equal(actual, expected)
        frozen = NoumenonMaterial(speed=0)
        for actual, expected in zip(frozen.field(0), frozen.field(500)):
            np.testing.assert_array_equal(actual, expected)
        self.assertEqual(a.state[0].shape, (FIELD_SIZE, FIELD_SIZE))
        self.assertFalse(np.array_equal(a.field(0)[0], NoumenonMaterial(seed=43).field(0)[0]))

    def test_heads_descend_on_fixed_cells_and_mix_is_catalog_weighted(self):
        m = NoumenonMaterial()
        first = m.field(1)[2]
        second = m.field(1 + 1 / 60)[2]
        rows, cols = np.nonzero((first > 0) & (np.indices(first.shape)[0] < FIELD_SIZE - 2))
        # In one tick cursors either stay in place or move down one/two cells.
        moved_down = second[rows, cols] + second[rows + 1, cols] + second[rows + 2, cols]
        self.assertGreater(np.mean(moved_down > 0), .97)
        symbols = m.field(2)[0]
        self.assertAlmostEqual(float((symbols >= 57).mean()), .1, delta=.008)
        self.assertTrue(np.all(NoumenonMaterial(face='cyber').field(0)[0] >= 57))
        self.assertTrue(np.all(NoumenonMaterial(face='classic').field(0)[0] < 57))

    def test_longer_trails_preserve_heads_symbols_and_seeking(self):
        classic = NoumenonMaterial()
        extended = NoumenonMaterial(trail_length=1.2)
        for time in (0., 1., 10., .5):
            symbols, body, heads = classic.field(time)
            longer_symbols, longer_body, longer_heads = extended.field(time)
            np.testing.assert_array_equal(symbols, longer_symbols)
            np.testing.assert_array_equal(heads, longer_heads)
            self.assertTrue(np.all(longer_body >= body - 1e-6))
            ratio = np.count_nonzero(longer_body) / np.count_nonzero(body)
            self.assertAlmostEqual(ratio, 1.2, delta=.03)
            self.assertGreater(np.mean((longer_body + longer_heads) == 0), .25)
            for actual, expected in zip(extended.field(time), NoumenonMaterial(trail_length=1.2).field(time)):
                np.testing.assert_array_equal(actual, expected)

    def test_trail_extension_is_confined_to_silhouettes(self):
        source = Image.new('RGB', self.size, 'gray')
        mask = np.zeros(self.size[::-1], np.float32)
        mask[20:110, 60:170] = 1
        subject = Subject(mask, 'person', .9, track_id=1)
        short = self.renderer(material_glow=0, material_mapping=0, material_subject_trail=1)
        long = self.renderer(material_glow=0, material_mapping=0)
        a = np.asarray(short.render(source, .5, subjects=[subject]))
        b = np.asarray(long.render(source, .5, subjects=[subject]))
        np.testing.assert_array_equal(a[mask == 0], b[mask == 0])
        self.assertGreater(np.count_nonzero(b[mask == 1]), np.count_nonzero(a[mask == 1]))
        self.assertAlmostEqual(long.scene_material.style.material_background / .55, .7)
        self.assertEqual(long.scene_material.subject_density, 2)
        self.assertEqual(long.scene_material.material.trail_length, 1)
        self.assertEqual(long.scene_material.subject_material(subject).trail_length, 1.2)

    def test_soft_ownership_overlap_and_empty_scene(self):
        mask = np.zeros(self.size[::-1], np.float32)
        mask[20:110, 50:150] = .7
        near = Subject(mask, 'person', .2, track_id=2)
        far = Subject(mask * .8, 'person', .99, track_id=1)
        weights = list(visible_ownership([near, far], self.size))
        total = sum(weight for _, weight in weights)
        np.testing.assert_allclose(total, 1, atol=2e-6, rtol=0)
        self.assertTrue(all(np.all(weight >= 0) for _, weight in weights))
        a = list(visible_ownership([near, far], self.size))
        b = list(visible_ownership([far, near], self.size))
        for (_, w1), (_, w2) in zip(a, b):
            np.testing.assert_array_equal(w1, w2)
        self.assertEqual(len(list(visible_ownership([near, near], self.size))), 2)
        np.testing.assert_array_equal(list(visible_ownership([], self.size))[0][1], 1)

    def test_empty_room_animated_without_hud_or_rgb_underlay(self):
        source = Image.new('RGB', self.size, (255, 0, 255))
        r = self.renderer(material_structure=0, material_mapping=0, material_glow=0)
        a, b = np.asarray(r.render(source, 0)), np.asarray(r.render(source, .5))
        self.assertGreater(np.count_nonzero(a), 100)
        self.assertFalse(np.array_equal(a, b))
        # Different RGB with the same source luminance has identical shading.
        gray = source.convert('L').convert('RGB')
        np.testing.assert_array_equal(a, r.render(gray, 0))
        self.assertGreater(np.mean(np.all(a == 0, axis=2)), .2)
        np.testing.assert_array_equal(a, self.renderer(material_structure=0, material_mapping=0, material_glow=0,
                                                     hud_glyphs='tech', palette='redline').render(source, 0))
        self.assertEqual(np.asarray(self.renderer(code_density=0).render(source, 0)).max(), 0)

    def test_opaque_foreground_has_no_background_glyph_cores(self):
        source = Image.new('RGB', self.size, (130, 130, 130))
        mask = np.zeros(self.size[::-1], np.float32)
        mask[20:115, 70:150] = 1
        subject = Subject(mask, 'person', .9, track_id=4)
        a = np.asarray(self.renderer(material_background=0, material_glow=0).render(source, 1, subjects=[subject]))
        b = np.asarray(self.renderer(material_background=3, material_glow=0).render(source, 1, subjects=[subject]))
        np.testing.assert_array_equal(a[mask == 1], b[mask == 1])
        self.assertFalse(np.array_equal(a[mask == 0], b[mask == 0]))

    def test_only_selected_silhouette_glyphs_are_brightened(self):
        source, subjects = fixture(self.size)
        r = self.renderer(material_mapping=0, material_glow=0, code_size=64,
                          material_edge_glow=0, material_edge_shade=0)
        plain = np.asarray(r.render(source, 0, subjects=subjects, material_subjects=set()))
        chosen = np.asarray(r.render(source, 0, subjects=subjects, material_subjects={1, 3}))
        selected = (subjects[0].mask + subjects[2].mask) > .5
        np.testing.assert_array_equal(chosen[~selected], plain[~selected])
        self.assertGreater(chosen[selected].mean(), plain[selected].mean() * 2)
        # Glyph gaps stay dark; selection cannot turn a mask into a solid fill.
        self.assertGreater(np.all(chosen[selected] == 0, axis=1).mean(), .05)
        np.testing.assert_array_equal(plain, r.render(source, 0, subjects=subjects, material_subjects=set()))
        np.testing.assert_array_equal(r.render(source, 0, subjects=subjects),
                                      r.render(source, 0, subjects=subjects, material_subjects={1, 2, 3}))

    def test_unselected_luminance_and_selected_dark_clothing(self):
        mask = np.ones(self.size[::-1], np.float32)
        subject = Subject(mask, 'person', .9, track_id=1)
        for subjects in ([], [subject]):
            r = self.renderer(material_mapping=0, material_structure=0, material_glow=0)
            levels = [np.asarray(r.render(Image.new('RGB', self.size, (level,) * 3), 0,
                                          subjects=subjects, material_subjects=set())) for level in (0, 40, 180)]
            self.assertEqual(levels[0].max(), 0)
            self.assertTrue(np.all(levels[2] >= levels[1]))
            self.assertGreater(levels[2].mean(), levels[1].mean() * 1.7)
        dark = Image.new('RGB', self.size)
        self.assertGreater(np.asarray(r.render(dark, 0, subjects=[subject], material_subjects={1})).mean(), 20)
        # Unselected body parts also use ordinary source luminance.
        before = r.render(Image.new('RGB', self.size, 'gray'), 0, subjects=[subject], material_subjects=set())
        subject.parts = [SurfacePart(mask, 'face', .9)]
        np.testing.assert_array_equal(before, r.render(Image.new('RGB', self.size, 'gray'), 0,
                                                      subjects=[subject], material_subjects=set()))

    def test_unselected_occluder_hides_selected_emission_and_glow(self):
        mask = np.ones(self.size[::-1], np.float32)
        near, far = [Subject(mask, 'person', .9, track_id=track) for track in (1, 2)]
        r = self.renderer(material_mapping=0)
        source = Image.new('RGB', self.size, 'gray')
        np.testing.assert_array_equal(r.render(source, 0, subjects=[near, far], material_subjects={2}),
                                      r.render(source, 0, subjects=[near], material_subjects=set()))

    def test_silhouettes_clip_their_own_instance_without_resizing_or_refilling(self):
        source = Image.new('RGB', self.size, 'white')
        for density in (.4, 1.):
            options = dict(material_mapping=0, material_glow=0, code_size=24, code_density=density,
                           material_edge_glow=0, material_edge_shade=0)
            background = np.asarray(self.renderer(material_background=1, **options).render(source, .5))
            renderer = self.renderer(material_foreground=1, material_background=0, **options)
            instances = []
            for track, box in ((1, (20, 25, 70, 115)), (42, (65, 40, 220, 90))):
                full = Subject(np.ones(self.size[::-1], np.float32), 'person', .9, track_id=track)
                original = np.asarray(renderer.render(source, .5, subjects=[full]))
                instances.append(original)
                self.assertFalse(np.array_equal(original, background))
                self.assertGreater(np.all(original == 0, axis=2).mean(), .1)
                mask = np.zeros(self.size[::-1], np.float32)
                x0, y0, x1, y1 = box
                mask[y0:y1, x0:x1] = 1
                subject = Subject(mask, 'person', .9, track_id=track)
                clipped = np.asarray(renderer.render(source, .5, subjects=[subject]))
                np.testing.assert_array_equal(clipped[mask == 1], original[mask == 1])
                self.assertEqual(clipped[mask == 0].max(), 0)
            self.assertFalse(np.array_equal(*instances))

    def test_background_camera_roll_cannot_tilt_fallback_rain(self):
        mapper = SurfaceMapper(self.size)
        source = Image.new('RGB', self.size, 'gray')
        with patch('yautja.scene_material.estimate_room', return_value=None), patch.object(mapper, '_track_camera') as track:
            mapper.update(source, [], 0, 1)
            mapper.camera = np.array([[.87, -.5, 12], [.5, .87, 8], [0, 0, 1]])
            mapper.update(source, [], .1, 1)
            track.assert_not_called()
        y, x = np.mgrid[:self.size[1], :self.size[0]].astype(np.float32)
        np.testing.assert_array_equal(mapper.environment(x, y), (x, y))
        self.assertEqual(mapper.mode, 'stable-flat')

    def test_room_losing_evidence_or_tracking_returns_to_vertical_rain(self):
        mapper = SurfaceMapper(self.size)
        source = Image.new('RGB', self.size, 'gray')
        room = np.array([[.36, .36], [.64, .36], [.64, .64], [.36, .64]])
        with patch('yautja.scene_material.estimate_room', side_effect=[room, None]), patch.object(mapper, '_track_camera'):
            mapper.update(source, [], 0, 1)
            self.assertEqual(mapper.mode, 'room-planes')
            y, x = np.mgrid[:self.size[1], :self.size[0]].astype(np.float32)
            mapper.confidence = .3
            np.testing.assert_array_equal(mapper.environment(x, y), (x, y))
            mapper.confidence = 1.
            mapper.update(source, [], 1.1, 1)
            self.assertIsNone(mapper.room)
            np.testing.assert_array_equal(mapper.environment(x, y), (x, y))

    def test_front_instance_blocks_background_even_between_its_drops(self):
        scene = SceneMaterial(self.size, code_size=24, material_glow=0, material_edge_glow=0)
        source = Image.new('RGB', self.size, 'white')
        mask = np.zeros(self.size[::-1], np.float32)
        mask[20:120, 50:180] = 1
        subject = Subject(mask, 'person', .9, track_id=5)
        first = np.asarray(scene.render(source, .5, [subject], 1))
        scene.material = NoumenonMaterial(seed=999)
        changed = np.asarray(scene.render(source, .5, [subject], 1))
        np.testing.assert_array_equal(first[mask == 1], changed[mask == 1])
        self.assertFalse(np.array_equal(first[mask == 0], changed[mask == 0]))
        self.assertGreater(np.all(first[mask == 1] == 0, axis=1).mean(), .1)

    def test_inner_edge_glow_is_selected_clipped_and_hollow(self):
        source = Image.new('RGB', self.size)
        mask = np.zeros(self.size[::-1], np.float32)
        mask[25:110, 40:100] = 1
        other = np.zeros_like(mask)
        other[25:110, 145:195] = 1
        subjects = [Subject(mask, 'person', .9, track_id=1), Subject(other, 'person', .9, track_id=2)]
        # Disable rain to measure the edge contribution alone.
        options = dict(code_density=0, code_size=64, material_glow=0, material_mapping=0)
        default = self.renderer(**options)
        self.assertEqual(np.asarray(default.render(source, 0, subjects=subjects)).max(), 0)
        r = self.renderer(material_edge_glow=.12, **options)
        selected = np.asarray(r.render(source, 0, subjects=subjects, material_subjects={1}))
        self.assertGreater(selected[mask == 1].max(), 40)
        self.assertEqual(selected[mask == 0].max(), 0)
        self.assertEqual(selected[35:100, 50:90].max(), 0)
        self.assertEqual(np.asarray(r.render(source, 0, subjects=subjects, material_subjects=set())).max(), 0)
        subjects[0].opacity = .5
        faded = np.asarray(r.render(source, 0, subjects=subjects, material_subjects={1}))
        self.assertTrue(np.all(faded <= selected))
        self.assertLess(faded.max(), selected.max())
        subjects[0].opacity = 0
        self.assertEqual(np.asarray(r.render(source, 0, subjects=subjects, material_subjects={1})).max(), 0)

    def test_edge_shade_is_local_and_only_affects_residual_background(self):
        source = Image.new('RGB', self.size, 'white')
        mask = np.zeros(self.size[::-1], np.float32)
        mask[20:110, 50:115] = 1
        other = np.zeros_like(mask)
        other[70:125, 100:155] = 1
        chosen = Subject(mask, 'person', .9, track_id=2)
        occluder = Subject(other, 'person', .9, track_id=1)
        subjects = [chosen, occluder]
        options = dict(code_size=64, material_glow=0, material_mapping=0, material_edge_glow=0)
        plain, shaded = self.renderer(material_edge_shade=0, **options), self.renderer(**options)
        a = np.asarray(plain.render(source, .5, subjects=subjects, material_subjects={2}))
        b = np.asarray(shaded.render(source, .5, subjects=subjects, material_subjects={2}))
        occupied = (mask + other) > 0
        np.testing.assert_array_equal(a[occupied], b[occupied])
        self.assertTrue(np.all(b <= a))
        self.assertTrue(np.any(b[30:100, 40:50] < a[30:100, 40:50]))
        np.testing.assert_array_equal(a[:, :25], b[:, :25])
        np.testing.assert_array_equal(plain.render(source, .5, subjects=subjects, material_subjects=set()),
                                      shaded.render(source, .5, subjects=subjects, material_subjects=set()))
        # A fully hidden selected person must not shade around its occluder.
        occluder.mask = mask.copy()
        np.testing.assert_array_equal(plain.render(source, .5, subjects=subjects, material_subjects={2}),
                                      shaded.render(source, .5, subjects=subjects, material_subjects={2}))

    @unittest.skipUnless(importlib.util.find_spec('cv2'), 'OpenCV tracking extra is optional')
    def test_converging_branches_and_uprights_are_not_an_enclosed_room(self):
        image = Image.new('L', (480, 270), 60)
        draw = ImageDraw.Draw(image)
        corners = ((173, 97), (307, 97), (307, 173), (173, 173))
        for start, end in zip(((0, 0), (480, 0), (480, 270), (0, 270)), corners):
            draw.line([start, end], fill=190, width=2)
        draw.line([corners[0], corners[3]], fill=190, width=2)
        draw.line([corners[1], corners[2]], fill=190, width=2)
        # Upright trunks and converging branches are insufficient: no supported
        # header/floor junctions close the proposed far wall.
        self.assertIsNone(estimate_room(np.asarray(image)))

    def test_known_plane_corners_and_minification(self):
        corners = np.array([(20, 20), (80, 20), (100, 100), (0, 100)])
        target = np.array([(0, 0), (100, 0), (100, 100), (0, 100)])
        matrix = homography(corners, target)
        u, v = project(matrix, corners[:, 0], corners[:, 1])
        np.testing.assert_allclose(np.column_stack((u, v)), target, atol=1e-10)
        m = NoumenonMaterial()
        u = np.linspace(3.01, 3.99, 100, dtype=np.float32)
        v = np.full_like(u, 8.3)
        far = m.sample(u, v, 1, np.ones_like(u) * 2).coverage
        self.assertLess(float(far.max() - far.min()), 1e-6)

    @unittest.skipUnless(importlib.util.find_spec('cv2'), 'OpenCV tracking extra is optional')
    def test_qualified_room_and_plain_image_fallback(self):
        frame, subjects = fixture((480, 270))
        scene = SceneMaterial(frame.size)
        scene.render(frame, 0, subjects)
        self.assertEqual(scene.mapper.mode, 'room-planes')
        self.assertIsNotNone(scene.mapper.room)
        y, x = np.mgrid[:270, :480].astype(np.float32)
        u, v = scene.mapper.environment(x, y)
        self.assertFalse(np.allclose(u[200], x[200]))
        self.assertLess(np.median(np.diff(u[260])), np.median(np.diff(u[205])))
        self.assertIsNone(estimate_room(np.full((270, 480), 80, np.uint8)))

    def test_vertical_coordinates_ignore_subject_motion_and_camera_state(self):
        frame = Image.new('RGB', self.size, 'gray')
        mask = np.zeros(self.size[::-1], np.float32)
        mask[20:100, 70:150] = 1
        subject = Subject(mask, 'person', .9, track_id=5)
        mapper = SurfaceMapper(self.size)
        mapper.update(frame, [subject], 0, 1)
        x, y = np.array([85., 100.]), np.array([35., 60.])
        mapper.camera[0, 2] = 3.
        u0, v0 = mapper.flat(x, y)
        shifted = Subject(np.roll(mask, 7, axis=1), 'person', .9, track_id=5,
                          parts=[SurfacePart(mask, 'skin', .8)])
        mapper.update(frame, [shifted], .1, 1)
        u1, v1 = mapper.flat(x, y)
        np.testing.assert_allclose(u0, u1)
        np.testing.assert_allclose(v0, v1)
        shifted.label = 'human'
        mapper.update(frame, [shifted], .15, 1)
        np.testing.assert_allclose(mapper.flat(x, y), (u0, v0))
        checkpoint = mapper.checkpoint()
        restored = SurfaceMapper(self.size)
        restored.restore(checkpoint)
        np.testing.assert_allclose(restored.flat(x, y), mapper.flat(x, y))
        mapper.update(frame, [], .2, 2)
        np.testing.assert_allclose(mapper.flat(x, y), (x, y))
        self.assertIsNone(mapper.room)

    def test_classic_scale_has_eighty_cells_on_the_long_edge(self):
        for size in ((1280, 720), (720, 1280), (960, 960)):
            r = Renderer(*size, look_preset='noumenon')
            self.assertEqual(max(size) / r.scene_material.cell, 80)
            self.assertEqual(r.scene_material.report()['material_subject_mapping'], 'independent-screen-vertical-rain')
            self.assertEqual(r.scene_material.report()['material_subject_density_resolved'], 2.)

    def test_png_cli_and_material_settings_without_semantic_dependencies(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / 'source.png', Path(folder) / 'result.png'
            Image.new('RGB', self.size, 'gray').save(source)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main([str(source), str(target), '--stylepreset', 'noumenon', '--thermal', 'luminance']), 0)
            report = json.loads(output.getvalue())
            self.assertFalse(report['hud'])
            self.assertEqual(report['scene_mode'], 'code')
            self.assertEqual(report['settings']['material_face'], 'mixed')
            with Image.open(target) as image:
                self.assertEqual(image.size, self.size)
                self.assertGreater(np.asarray(image).max(), 0)

    def test_catalog_selection_matches_only_chosen_figures_across_shots(self):
        with tempfile.TemporaryDirectory() as folder:
            source, path = Path(folder) / 'source.png', Path(folder) / 'figures.json'
            frame, subjects = fixture(self.size)
            frame.save(source)
            catalog = FigureCatalog(source, fps=2)
            for time in (0., .5, 1., 1.5):
                catalog.add(frame, time, subjects, 1 + int(time >= 1))
            path.write_text(json.dumps(catalog.data), encoding='utf-8')
            selection = MaterialSelection(path, source, {'S001-F001', 'S001-F003', 'S002-F002'})
            self.assertEqual(selection.tracks_at(0., list(reversed(subjects))), {1, 3})
            # A trim/restarted tracker can use different live IDs than the scan.
            subjects[1].track_id = 99
            self.assertEqual(selection.tracks_at(1.25, subjects), {99})
            self.assertEqual(selection.shot, 'S002')
            self.assertEqual(selection.tracks_at(2.5, subjects), set())
            self.assertEqual(selection.tracks_at(.25, subjects), {1, 3})
            self.assertEqual(selection.seen, selection.selected)
            self.assertIn('--material-subjects', catalog.contact_sheet())
            with self.assertRaisesRegex(ValueError, 'Unknown target IDs'):
                MaterialSelection(path, source, {'S003-F001'})

    def test_cli_material_selection_with_hud_off_and_report(self):
        with tempfile.TemporaryDirectory() as folder:
            source, path, target = [Path(folder) / name for name in ('source.png', 'figures.json', 'chosen.png')]
            frame, subjects = fixture(self.size)
            frame.save(source)
            catalog = FigureCatalog(source, fps=1)
            catalog.add(frame, 0., subjects, 1)
            path.write_text(json.dumps(catalog.data), encoding='utf-8')
            tracker = SimpleNamespace(update=lambda f, t: subjects, report=lambda: {})
            with patch('yautja.cli.semantic_tracker', return_value=tracker), patch('sys.stdout', new_callable=io.StringIO) as out:
                self.assertEqual(main([str(source), str(target), '--stylepreset', 'noumenon', '--figures', str(path),
                                       '--material-subjects', 'S001-F001', '--material-subjects', 's001-f003']), 0)
            report = json.loads(out.getvalue())
            self.assertFalse(report['hud'])
            self.assertEqual(report['material_subjects'], ['S001-F001', 'S001-F003'])
            self.assertEqual(report['material_subjects_seen'], report['material_subjects'])
            self.assertEqual(report['material_subjects_unseen'], [])
            self.assertEqual(report['settings']['material_subjects'], report['material_subjects'])
            with Image.open(target) as result:
                np.testing.assert_array_equal(result, self.renderer().render(frame, 0, subjects=subjects,
                                                                            material_subjects={1, 3}, shot_id='S001'))
            # Catalog validation happens before model setup or writing output.
            missing = Path(folder) / 'missing.png'
            with patch('yautja.cli.semantic_tracker') as setup, patch('sys.stderr', new_callable=io.StringIO):
                self.assertEqual(main([str(source), str(missing), '--stylepreset', 'noumenon', '--figures', str(path),
                                       '--material-subjects', 'S099-F001']), 1)
            setup.assert_not_called()
            self.assertFalse(missing.exists())

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg unavailable')
    def test_trimmed_video_selects_source_shot_while_animation_starts_at_zero(self):
        with tempfile.TemporaryDirectory() as folder:
            source, path, target = [Path(folder) / name for name in ('clip.mp4', 'figures.json', 'chosen.mp4')]
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=240x136:r=4:d=2',
                            '-c:v', 'libx264', str(source)], check=True, capture_output=True)
            frame, subjects = fixture(self.size)
            catalog = FigureCatalog(source, fps=4)
            for time in np.arange(8) / 4:
                catalog.add(frame, float(time), subjects, 1 + int(time >= 1))
            path.write_text(json.dumps(catalog.data), encoding='utf-8')
            subjects[1].track_id = 99
            tracker = SimpleNamespace(update=lambda f, t: subjects, report=lambda: {}, scene_cuts=0, max_subjects=3)
            calls, render = [], Renderer.render
            def capture(renderer, frame, time, *args, **kwargs):
                calls.append((time, kwargs['shot_id'], kwargs['material_subjects']))
                return render(renderer, frame, time, *args, **kwargs)
            with patch('yautja.cli.semantic_tracker', return_value=tracker), patch.object(Renderer, 'render', capture), \
                    patch('sys.stdout', new_callable=io.StringIO) as out, patch('sys.stderr', new_callable=io.StringIO):
                self.assertEqual(main([str(source), str(target), '--stylepreset', 'noumenon', '--figures', str(path),
                                       '--material-subjects', 'S001-F001,S002-F002', '--start', '1', '--duration', '.5']), 0)
            self.assertEqual(calls, [(0., 'S002', {99}), (.25, 'S002', {99})])
            report = json.loads(out.getvalue())
            self.assertEqual(report['material_subjects_seen'], ['S002-F002'])
            self.assertEqual(report['material_subjects_unseen'], ['S001-F001'])
            subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(target), '-f', 'null', '-'],
                           check=True, capture_output=True)

    def test_material_selection_modes_and_invalid_runtime_combinations(self):
        self.assertIsNone(material_subject_ids([]))
        self.assertIsNone(material_subject_ids(['all']))
        self.assertEqual(material_subject_ids(['none']), set())
        self.assertEqual(material_subject_ids(['s001-f001,S001-F002', 'S001-F001']), {'S001-F001', 'S001-F002'})
        self.assertNotIn('material_subjects', VISUAL_OPTIONS)
        cases = [(['--material-subjects', value], True) for value in ('all,none', 'all,S001-F001', '', 'S001-F001')]
        cases += [(['--material-subjects', 'none'], False),
                  (['--material-subjects', 'S001-F001', '--figures', 'scan.json', '--thermal', 'luminance'], True),
                  (['--material-subjects', 'none', '--list-figures'], True)]
        for flags, preset in cases:
            with self.subTest(flags=flags), patch('sys.stderr', new_callable=io.StringIO), patch('yautja.cli.convert') as convert:
                try:
                    status = main(['missing.png', 'output.png', *(['--stylepreset', 'noumenon'] if preset else []), *flags])
                except SystemExit as exc:
                    status = exc.code
                self.assertNotEqual(status, 0)
                convert.assert_not_called()

    def test_chunk_checkpoint_preserves_composed_scene(self):
        size = (320, 180)
        scene = SceneMaterial(size)
        for index in range(3):
            frame, subjects = fixture(size, index / 24)
            scene.render(frame, index / 24, subjects, 1)
        checkpoint = scene.checkpoint()
        resumed = SceneMaterial(size)
        resumed.restore(checkpoint)
        frame, subjects = fixture(size, 3 / 24)
        np.testing.assert_array_equal(scene.render(frame, 3 / 24, subjects, 1),
                                      resumed.render(frame, 3 / 24, subjects, 1))
        with self.assertRaisesRegex(ValueError, 'configuration'):
            SceneMaterial(size, seed=9).restore(checkpoint)

    def test_shared_mapping_and_diagnostics_have_bounded_storage(self):
        mapper = SurfaceMapper(self.size, strength=0)
        source = Image.new('RGB', self.size)
        mask = np.ones(self.size[::-1], np.float32)
        subjects = [Subject(mask, 'person', .9, track_id=index) for index in range(100)]
        fields = set(mapper.__dict__)
        mapper.update(source, subjects, 0, 1)
        self.assertEqual(set(mapper.__dict__), fields)
        self.assertEqual(mapper.previous.shape, self.size[::-1])
        mapper.update(source, [], 3, 1)
        self.assertEqual(set(mapper.__dict__), fields)
        self.assertEqual(mapper.previous_foreground.max(), 0)
        scene = SceneMaterial(self.size)
        scene.frame_seconds.extend(range(1000))
        self.assertEqual(scene.report()['material_frame_sample_count'], 512)

    def test_instance_identity_survives_label_changes_eviction_and_seeking(self):
        scene = SceneMaterial(self.size)
        mask = np.ones(self.size[::-1], np.float32)
        subject = Subject(mask, 'person', .9, track_id=5)
        original = scene.subject_material(subject)
        expected = [field.copy() for field in original.field(.5)]
        subject.label = 'human'
        self.assertIs(original, scene.subject_material(subject))
        for track in range(100, 166):
            scene.subject_material(Subject(mask, 'person', .9, track_id=track))
        self.assertEqual(len(scene.subject_materials), 64)
        restored = scene.subject_material(subject)
        for actual, wanted in zip(restored.field(.5), expected):
            np.testing.assert_array_equal(actual, wanted)
        restored.field(2.)
        for actual, wanted in zip(restored.field(.5), expected):
            np.testing.assert_array_equal(actual, wanted)
        scene.mapper.shot = 2
        self.assertNotEqual(restored.seed, scene.subject_material(subject).seed)
        self.assertEqual(len(scene.subject_materials), 1)

    def test_missing_classic_catalog_fails_precisely(self):
        from yautja.noumenon import classic_font
        classic_font.cache_clear()
        with patch('yautja.noumenon.files', side_effect=FileNotFoundError), self.assertRaisesRegex(ValueError, 'assets are missing'):
            classic_font()

    def test_extra_density_preserves_glyph_width(self):
        materials = [NoumenonMaterial(density=density) for density in (1., 1.25, 2.)]
        for material in materials:
            material.field(0)
            material.state[0][:] = 17
            material.enabled[:] = False
            material.enabled[:, 0] = True
        u = np.linspace(0, .999, 256, dtype=np.float32)
        v = np.full_like(u, .42)
        original = materials[0].sample(u, v, 0).coverage
        for material in materials[1:]:
            np.testing.assert_allclose(original, material.sample(u * material.density, v, 0).coverage, atol=1e-6)


if __name__ == '__main__':
    unittest.main()
