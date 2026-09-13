"""Shot selection, target animation, and configurable display-effect regressions."""
import copy
import io
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from yautja.cli import main
from yautja.colors import HUD_DEFAULTS, resolve_colors
from yautja.display import DisplayEffects, highlight_glow
from yautja.figures import FigureCatalog, TargetSelection
from yautja.render import PALETTES, Renderer
from yautja.semantic import Subject
from yautja.target import TargetOverlay


def person(left=40, track=1):
    mask = np.zeros((180, 320), np.float32)
    mask[30:150, left:left + 40] = 1
    return Subject(mask, 'person', .9, track_id=track)


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'photo.png'
        self.frame = Image.new('RGB', (320, 180), (80, 90, 100))
        self.frame.save(self.source)

    def catalog(self):
        catalog = FigureCatalog(self.source, fps=10)
        catalog.add(self.frame, 0, [person(200, 2), person(40, 1)], 1)
        catalog.add(self.frame, .1, [person(50, 1)], 1)
        catalog.add(self.frame, .2, [person(210, 2)], 2)
        path = self.root / 'figures.json'
        path.write_text(json.dumps(catalog.data), encoding='utf-8')
        return catalog, path

    def test_ids_are_shot_local_and_first_discovery_is_left_to_right(self):
        catalog, path = self.catalog()
        shots = catalog.summary()['shots']
        self.assertEqual([s['id'] for s in shots], ['S001', 'S002'])
        self.assertEqual(shots[0]['figures'][0]['id'], 'S001-F001')
        self.assertNotIn('samples', shots[0]['figures'][0])
        self.assertIn('data:image/jpeg;base64,', catalog.contact_sheet())
        selection = TargetSelection(path, self.source, ['S001-F001'])
        self.assertEqual(selection.at(.2)[0], [])
        self.assertEqual(selection.at(.2)[1], 'S002')

    def test_interpolation_uses_source_time_and_normalized_coordinates(self):
        _, path = self.catalog()
        selection = TargetSelection(path, self.source, ['s001-f001'])
        values, _ = selection.at(.05)
        self.assertAlmostEqual(values[0]['bbox'][0], 45 / 320)
        self.assertEqual(selection.at(-1)[0], [])
        self.assertEqual(selection.at(10)[0], [])

    def test_lost_figures_do_not_bridge_gaps_or_switch_to_another_id(self):
        catalog, path = self.catalog()
        selected = TargetSelection(path, self.source, ['S001-F002'])
        self.assertEqual(selected.at(.15)[0], [])
        self.assertEqual(selected.at(.2)[0], [])

    def test_changed_source_and_unknown_target_are_rejected(self):
        _, path = self.catalog()
        with self.assertRaisesRegex(ValueError, 'Unknown target'):
            TargetSelection(path, self.source, ['S005-F001'])
        self.source.write_bytes(b'changed source')
        with self.assertRaisesRegex(ValueError, 'different source'):
            TargetSelection(path, self.source, ['S001-F001'])

    def test_invalid_catalog_coordinates_times_and_schema_are_rejected(self):
        catalog, path = self.catalog()
        for index, bad in ((0, float('nan')), (1, -1), (3, 2), (5, 2)):
            data = copy.deepcopy(catalog.data)
            data['shots'][0]['figures'][0]['samples'][0][index] = bad
            path.write_text(json.dumps(data), encoding='utf-8')
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, 'Invalid figure catalog'):
                TargetSelection(path, self.source, ['S001-F001'])

    def test_still_scan_and_selected_render_need_no_ffmpeg(self):
        catalog = self.root / 'scan.json'
        tracker = SimpleNamespace(update=lambda f, t: [person()], scene_cuts=0)
        with patch('yautja.cli.semantic_tracker', return_value=tracker), patch('sys.stdout', new_callable=io.StringIO) as out:
            self.assertEqual(main([str(self.source), str(catalog), '--list-figures']), 0)
            self.assertEqual(json.loads(out.getvalue())['shots'][0]['figures'][0]['id'], 'S001-F001')
        output = self.root / 'result.png'
        with patch('yautja.cli.binary', side_effect=AssertionError('No FFmpeg for stills')), patch('sys.stdout', new_callable=io.StringIO) as out:
            self.assertEqual(main([str(self.source), str(output), '--figures', str(catalog), '--target', 'S001-F001',
                                   '--target-colors', '#0f0,#00f', '--no-target-flash']), 0)
            report = json.loads(out.getvalue())
        self.assertEqual(report['targets_seen'], ['S001-F001'])
        self.assertFalse(report['target_flash'])
        self.assertEqual(report['target_colors'], ['#00ff00', '#0000ff'])
        with Image.open(output) as picture:
            self.assertEqual(picture.size, self.frame.size)

    def test_scan_protects_existing_contact_sheet_and_catalog(self):
        catalog = self.root / 'scan.json'
        sheet = catalog.with_suffix('.html')
        sheet.write_bytes(b'keep this')
        with patch('yautja.cli.semantic_tracker') as tracker, patch('sys.stderr', new_callable=io.StringIO):
            self.assertEqual(main([str(self.source), str(catalog), '--list-figures']), 1)
            tracker.assert_not_called()
        self.assertEqual(sheet.read_bytes(), b'keep this')
        self.assertFalse(catalog.exists())

    def test_target_pairing_and_invalid_controls_fail_before_processing(self):
        for flags in (['--target', 'S001-F001'], ['--figures', 'missing.json'], ['--target-colors', '#f00'],
                      ['--heat-glow', 'nan'], ['--motion-blur', '1.01'], ['--crt-bleed', '-1'],
                      ['--target-flash-rate', '4'], ['--heat-glow-speed', '-1']):
            with self.subTest(flags=flags), patch('yautja.cli.convert') as convert, patch('sys.stderr', new_callable=io.StringIO):
                try:
                    status = main([str(self.source), str(self.root / 'bad.png'), *flags])
                except SystemExit as exc:
                    status = exc.code
                self.assertNotEqual(status, 0)
                convert.assert_not_called()

    def test_catalog_validation_still_runs_with_python_optimization(self):
        import sys
        catalog, path = self.catalog()
        catalog.data['shots'][0]['figures'][0]['samples'][0][1] = -2
        path.write_text(json.dumps(catalog.data), encoding='utf-8')
        run = subprocess.run([sys.executable, '-O', '-c',
            'from yautja.figures import TargetSelection; import sys; TargetSelection(sys.argv[1],sys.argv[2],["S001-F001"])',
            str(path), str(self.source)], capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('Invalid figure catalog', run.stderr)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg unavailable')
    def test_video_catalog_reuses_tracks_across_trim_size_and_fps_with_audio(self):
        source, catalog, output = [self.root / name for name in ('clip.mp4', 'scan.json', 'target.mp4')]
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=320x180:r=24:d=1',
                        '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1', '-c:v', 'libx264', '-c:a', 'aac',
                        '-shortest', str(source)], check=True, capture_output=True)
        tracker = SimpleNamespace(scene_cuts=0)
        def update(frame, time):
            tracker.scene_cuts = int(time >= .5)
            return [person(40 + round(time * 50))]
        tracker.update = update
        with patch('yautja.cli.semantic_tracker', return_value=tracker), patch('sys.stdout', new_callable=io.StringIO):
            self.assertEqual(main([str(source), str(catalog), '--list-figures', '--fps', '12', '--max-size', '320']), 0)
        with patch('sys.stdout', new_callable=io.StringIO) as out:
            self.assertEqual(main([str(source), str(output), '--figures', str(catalog), '--target', 'S001-F001,S002-F001',
                                   '--start', '.25', '--duration', '.5', '--fps', '24', '--max-size', '160',
                                   '--palette', 'abyss', '--motion-blur', '.8', '--crt-vertical-lines', '--heat-glow', '.7']), 0)
            report = json.loads(out.getvalue())
        self.assertEqual(report['targets_seen'], ['S001-F001', 'S002-F001'])
        self.assertEqual(report['targets_unseen'], [])
        self.assertEqual(report['target_frames'], 12)
        self.assertTrue(report['audio_preserved'])
        subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(output), '-f', 'null', '-'], check=True, capture_output=True)


class TargetAnimationTests(unittest.TestCase):
    targets = [{'id': 'S001-F001', 'bbox': [.4, .25, .6, .8]}]

    def animate(self, flash=True, colors=((255, 0, 0), (255, 255, 255))):
        overlay = TargetOverlay(flash_rate=1.5 if flash else 0)
        image = Image.new('RGB', (320, 180))
        frames = []
        for time in (0, .3, .6, .9, 1.2, 1.4):
            frames.append(np.asarray(overlay.draw(image, time, self.targets, colors, shot='S001')))
        return overlay, frames

    def test_three_blades_acquire_red_then_flash_white(self):
        overlay, frames = self.animate()
        self.assertFalse(np.array_equal(frames[0], frames[3]))
        self.assertGreater(frames[3][..., 0].max(), 200)
        self.assertEqual(frames[3][..., 1].max(), 0)
        self.assertGreater(frames[-1][..., 1].max(), 200)
        self.assertEqual(overlay.seen, {'S001-F001'})

    def test_landed_reticle_is_larger_with_an_independently_thinner_stroke(self):
        # The bottom side measures the radius independently of the corner gaps.
        # Stroke baselines come from the initial compact reticle at these sizes.
        for width, height, old_stroke in ((320, 180, 6), (480, 270, 9), (960, 540, 19)):
            with self.subTest(size=(width, height)):
                image = Image.new('RGB', (width, height))
                ink = np.asarray(TargetOverlay().draw(image, 0, self.targets,
                                    ((255, 255, 255),) * 2, static=True))[..., 0] > 64
                bottom = np.flatnonzero(ink[:, round(width * .5)]).max()
                compact_radius = max(.2 * width * .8, .55 * height * .62, 12) * .30
                self.assertAlmostEqual(bottom - height * .525, compact_radius * 1.30 / 2, delta=1)
                stroke = np.count_nonzero(ink[round(height * .525):, round(width * .5)])
                self.assertAlmostEqual(stroke, old_stroke * .75, delta=1)
                self.assertLess(stroke, old_stroke)

    def test_all_three_corner_channels_remain_open_during_white_flash(self):
        for width, height in ((320, 180), (480, 270), (960, 540)):
            overlay = TargetOverlay()
            image = Image.new('RGB', (width, height))
            for time in (0, .3, .6, .9, 1.2, 1.4):
                frame = np.asarray(overlay.draw(image, time, self.targets,
                                      ((255, 0, 0), (255, 255, 255)), shot='S001'))
                if time not in (.9, 1.4):
                    continue
                with self.subTest(size=(width, height), time=time):
                    self.assertGreater(frame[..., 0].max(), 200)
                    self.assertEqual(frame[..., 1].max() > 200, time == 1.4)
                    radius = max(.2 * width * .8, .55 * height * .62, 12) * .39
                    distances = np.linspace(radius * .25, radius * 1.05, 100)
                    for angle in (-math.pi / 2, math.pi / 6, 5 * math.pi / 6):
                        x = np.rint(width * .5 + np.cos(angle) * distances).astype(int)
                        y = np.rint(height * .525 + np.sin(angle) * distances).astype(int)
                        # Clear corridors through each corner, not tiny notches.
                        # At small sizes, glow and rounded sampling can approach
                        # an edge; the channel stays below 25% of blade intensity.
                        self.assertLess(frame[y, x].max(), 64)

    def test_no_flash_and_identical_colors_hold_after_landing(self):
        for flash, colors in ((False, ((255, 0, 0), (255, 255, 255))), (True, ((0, 200, 150), (0, 200, 150)))):
            _, frames = self.animate(flash, colors)
            np.testing.assert_array_equal(frames[3], frames[-1])

    def test_target_disappears_and_reacquires_after_loss_or_cut(self):
        overlay, _ = self.animate()
        blank = Image.new('RGB', (320, 180))
        gone = overlay.draw(blank, 1.5, [], ((255, 0, 0), (255, 255, 255)), shot='S001')
        self.assertEqual(np.asarray(gone).max(), 0)
        overlay.draw(blank, 1.6, self.targets, ((255, 0, 0), (255, 255, 255)), shot='S002')
        self.assertEqual(overlay.active['S001-F001'], 1.6)

    def test_hud_off_removes_targets_but_keeps_effects(self):
        field = np.full((180, 320), 140, np.uint8)
        a = Renderer(320, 180, hud=False, heat_glow=.5, crt_vertical_lines=True)
        b = Renderer(320, 180, hud=False, heat_glow=.5, crt_vertical_lines=True)
        np.testing.assert_array_equal(np.asarray(a.render_field(field, 1, targets=self.targets)),
                                      np.asarray(b.render_field(field, 1)))

    def test_black_target_and_explicit_virtualboy_target_colors_are_supported(self):
        frame = Image.new('RGB', (320, 180), 'white')
        picture = TargetOverlay().draw(frame, 0, self.targets, ((0, 0, 0), (0, 0, 0)), static=True)
        self.assertEqual(np.asarray(picture).min(), 0)
        renderer = Renderer(320, 180, palette='virtualboy', target_colors='#0f0,#0f0')
        picture = renderer.render(frame, 0, targets=self.targets, target_static=True)
        self.assertGreater(np.asarray(picture)[..., 1].max(), 200)


class DisplayTests(unittest.TestCase):
    def test_zero_effects_are_exact_passthrough(self):
        image = Image.fromarray(np.random.default_rng(4).integers(0, 256, (80, 120, 3), dtype=np.uint8))
        self.assertIs(DisplayEffects().apply(image, 0), image)
        self.assertIs(highlight_glow(image, np.zeros((80, 120), np.uint8), 0, 1), image)

    def test_motion_persistence_tracks_time_and_resets_at_cuts(self):
        effect = DisplayEffects(motion_blur=.8)
        before = Image.new('RGB', (120, 80))
        before.paste((255, 0, 0), (20, 20, 30, 30))
        effect.apply(before, 0, 'S001')
        blank = Image.new('RGB', before.size)
        trail = np.asarray(effect.apply(blank, .04, 'S001'))
        self.assertGreater(trail[25, 25, 0], 0)
        self.assertLess(trail[25, 25, 0], 255)
        reset = effect.apply(blank, .08, 'S002')
        self.assertEqual(np.asarray(reset).max(), 0)
        self.assertEqual(np.asarray(effect.apply(blank, .01, 'S002')).max(), 0)

    def test_bleed_is_horizontal_strength_controlled_and_does_not_wrap(self):
        image = Image.new('RGB', (320, 180))
        image.paste((255, 0, 0), (0, 60, 3, 90))
        low = np.asarray(DisplayEffects(crt_bleed=.2).apply(image, 0))
        high = np.asarray(DisplayEffects(crt_bleed=.9).apply(image, 0))
        self.assertGreater(high[70, 5, 0], low[70, 5, 0])
        self.assertEqual(high[:, -1].max(), 0)
        self.assertEqual(high[30].max(), 0)
        self.assertEqual(high[..., 1:].max(), 0)

    def test_vertical_and_horizontal_lines_are_independent_and_adjustable(self):
        field = np.full((180, 320), 180, np.uint8)
        base = np.asarray(Renderer(320, 180, hud=False).render_field(field, 0), np.float32)
        vertical = np.asarray(Renderer(320, 180, hud=False, crt_vertical_lines=True, crt_strength=.4).render_field(field, 0))
        expected = base.copy(); expected[:, ::2] *= .6
        np.testing.assert_array_equal(vertical, np.uint8(expected))
        both = np.asarray(Renderer(320, 180, hud=False, scanlines=True, crt_vertical_lines=True, crt_strength=.4).render_field(field, 0))
        expected = base.copy(); expected[::2] *= .6; expected[:, ::2] *= .6
        np.testing.assert_array_equal(both, np.uint8(expected))

    def test_heat_glow_moves_only_hot_emission_and_can_freeze(self):
        field = np.zeros((180, 320), np.uint8); field[60:100, 130:180] = 220
        image = Image.new('RGB', (320, 180)); image.paste((70, 130, 50), (130, 60, 180, 100))
        a = np.asarray(highlight_glow(image, field, .8, 0))
        b = np.asarray(highlight_glow(image, field, .8, .7))
        self.assertGreater(np.abs(a.astype(float) - b).sum(), 0)
        self.assertEqual(a[0].max(), 0)
        self.assertGreater(a[75, 128].max(), 0)
        np.testing.assert_array_equal(highlight_glow(image, field, .8, 0, speed=0),
                                      highlight_glow(image, field, .8, 9, speed=0))

    def test_abyss_has_dark_blue_cold_and_white_hot_with_muted_cyan_hud(self):
        colors = resolve_colors(PALETTES, palette='abyss')
        self.assertLess(colors.palette[50].max(), 60)
        self.assertGreater(colors.palette[80, 2], colors.palette[80, 0])
        self.assertTrue(np.all(colors.palette[-1] == 255))
        r, g, b = colors.hud['waveform']
        self.assertLess(r, g); self.assertLess(g, b); self.assertLess(b, 160)
        self.assertEqual(colors.hud['target'], HUD_DEFAULTS['target'])
        self.assertEqual(Renderer(320, 180, palette='abyss').heat_glow, 0)

    def test_heat_glow_works_across_all_palettes_including_inverted_heat(self):
        field = np.zeros((100, 160), np.uint8)
        field[35:65, 60:100] = 205
        for name in PALETTES:
            with self.subTest(palette=name):
                plain = np.asarray(Renderer(160, 100, palette=name, hud=False).render_field(field, 0))
                glowing = np.asarray(Renderer(160, 100, palette=name, hud=False, heat_glow=.8).render_field(field, 0))
                self.assertFalse(np.array_equal(plain, glowing))
                np.testing.assert_array_equal(plain[0], glowing[0])
                if name == 'black-hot':
                    self.assertLess(glowing.mean(), plain.mean())
                if name == 'virtualboy':
                    self.assertEqual(glowing[..., 1:].max(), 0)
