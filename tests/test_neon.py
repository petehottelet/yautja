"""Emission stays local, deterministic, color-aware, and independently adjustable."""
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw

from yautja.cli import extra_report, main, parser
from yautja.hud import BLUR_ELEMENTS
from yautja.neon import NeonStyle, NeonFlicker, glow_color
from yautja.render import Renderer
from yautja.semantic import Subject
from yautja.target import TARGET_SHAPES, TargetOverlay


class NeonTests(unittest.TestCase):
    def tube(self, *, color=(38, 112, 133), opacity=1., alpha=255, blur=0., intensity=.25):
        layer = Image.new('RGBA', (100, 100))
        ImageDraw.Draw(layer).line([(50, 20), (50, 80)], fill=(*color, alpha), width=6)
        base = Image.new('RGB', (240, 200), (100, 100, 100) if max(color) == 0 else (10, 10, 10))
        NeonStyle(intensity).apply(base, layer, 50, 40, color, element='target', width=6, opacity=opacity, blur=blur)
        return np.asarray(base).astype(int)

    def test_halo_extends_past_ink_and_panel_but_distant_scene_is_unchanged(self):
        frame = self.tube()
        self.assertGreater(frame[90, 110, 2], 10)
        self.assertGreater(frame[90, 45, 2], 10)
        np.testing.assert_array_equal(frame[0, 0], [10, 10, 10])
        self.assertEqual(glow_color((38, 112, 133)), (73, 215, 255))
        halo = frame[90, 110] - 10
        self.assertGreater(halo[2], halo[1])
        self.assertGreater(halo[1], halo[0] * 2)

    def test_opacity_scales_both_light_and_core_and_does_not_renormalize_fades(self):
        full, half, hidden = self.tube(), self.tube(opacity=.5), self.tube(opacity=0)
        self.assertLessEqual(np.abs((half - 10) * 2 - (full - 10)).max(), 1)
        np.testing.assert_array_equal(hidden, np.full(hidden.shape, 10))
        faded = self.tube(alpha=128)
        self.assertLessEqual(np.abs(faded - half).max(), 1)

    def test_black_ink_is_subtractive_and_white_ink_stays_neutral(self):
        black = self.tube(color=(0, 0, 0))
        self.assertLess(black[90, 110, 0], 100)
        self.assertLessEqual(black.max(), 100)
        np.testing.assert_array_equal(black[..., 0], black[..., 1])
        white = self.tube(color=(255, 255, 255))
        np.testing.assert_array_equal(white[..., 0], white[..., 2])

    def test_blur_softens_core_without_recomputing_halo_from_blurred_artwork(self):
        sharp, soft = self.tube(), self.tube(blur=3)
        self.assertFalse(np.array_equal(sharp, soft))
        np.testing.assert_array_equal(sharp[:, :80], soft[:, :80])
        self.assertLess(soft[90, 100].max(), sharp[90, 100].max())

    def test_zero_neon_keeps_original_ink_with_no_whitening_or_halo(self):
        frame = self.tube(intensity=0)
        np.testing.assert_array_equal(frame[90, 100], [38, 112, 133])
        np.testing.assert_array_equal(frame[90, 110], [10, 10, 10])

    def test_flicker_is_smooth_seeded_and_independent_of_call_order(self):
        a, b, c = NeonFlicker(42), NeonFlicker(42), NeonFlicker(43)
        times = np.arange(20) / 24
        values = [a.gain(t, .8) for t in times]
        self.assertEqual(values, [b.gain(t, .8) for t in times])
        self.assertNotEqual(values, [c.gain(t, .8) for t in times])
        self.assertTrue(all(a.gain(t, 0) == 1 for t in times))
        self.assertLess(abs(a.gain(.231, 1) - a.gain(.23101, 1)), .002)
        self.assertEqual(a.gain(.231, 1), b.gain(.231, 1))

    def test_flicker_changes_only_emission_with_fixed_artwork(self):
        style = NeonStyle(flicker=1)
        layer = Image.new('RGBA', (80, 80))
        ImageDraw.Draw(layer).line([(40, 20), (40, 60)], fill=(38, 112, 133, 255), width=3)
        frames = []
        for t in (0, .17, 0):
            base = Image.new('RGB', (160, 160))
            style.apply(base, layer, 40, 40, (38, 112, 133), element='readout', width=3, gain=style.noise.gain(t, 1))
            frames.append(np.asarray(base))
        np.testing.assert_array_equal(frames[0], frames[2])
        self.assertFalse(np.array_equal(frames[0], frames[1]))

    def test_every_hud_element_uses_shared_gain_and_has_independent_intensity(self):
        field = np.full((540, 960), 100, np.uint8)
        mask = np.zeros(field.shape, np.float32)
        mask[130:470, 400:580] = 1
        subjects = [Subject(mask, 'person', .95, track_id=1)]
        target = [{'id': 'one', 'bbox': [.4, .25, .6, .8]}]
        def render(key=None):
            renderer = Renderer(960, 540, neon=True, neon_flicker=.4, show_timecode=True, verbose=True,
                                analysis=True,
                                geo_grid=True, target_motif='triangles', target_label='TARGETING',
                                subject_outline=True, subject_code=True, subject_labels=True,
                                neon_elements=None if key is None else key + '=0')
            with patch.object(renderer.neon_style, 'apply', wraps=renderer.neon_style.apply) as apply:
                frame = renderer.render_field(field, .17, subjects=subjects, targets=target, target_static=True)
                self.assertEqual({call.kwargs['gain'] for call in apply.call_args_list}, {renderer.neon_gain})
                self.assertEqual({call.kwargs['element'] for call in apply.call_args_list}, set(BLUR_ELEMENTS))
            return np.asarray(frame)
        original = render()
        for key in BLUR_ELEMENTS:
            with self.subTest(key=key):
                self.assertGreater(np.count_nonzero(original != render(key)), 10)

    def test_off_is_unchanged_even_with_tuning_and_no_hud_or_zero_opacity_emit_nothing(self):
        field = np.full((180, 320), 100, np.uint8)
        for opts in ({}, {'palette': 'black-hot'}, {'wave_style': 'rorschach'}, {'hud_theme': 'custom', 'hud_colors': 'waveform=#080'}):
            with self.subTest(opts=opts):
                original = Renderer(320, 180, **opts).render_field(field, 0)
                with patch.object(NeonStyle, 'apply', side_effect=AssertionError('Neon disabled')):
                    off = Renderer(320, 180, **opts, neon_intensity=2, neon_flicker=1).render_field(field, 0)
                np.testing.assert_array_equal(original, off)
                plain = Renderer(320, 180, hud=False, **opts).render_field(field, 0)
                for options in ({'hud': False}, {'hud_opacity': 0}):
                    hidden = Renderer(320, 180, neon=True, **opts, **options).render_field(field, 0)
                    np.testing.assert_array_equal(plain, hidden)

    def test_old_bloom_does_not_stack_with_neon_and_virtualboy_stays_red(self):
        field = np.full((180, 320), 100, np.uint8)
        a = Renderer(320, 180, neon=True, glow=0).render_field(field, 0)
        b = Renderer(320, 180, neon=True, glow=1).render_field(field, 0)
        np.testing.assert_array_equal(a, b)
        red = Renderer(320, 180, neon=True, palette='virtualboy').render_field(field, 0)
        self.assertEqual(np.asarray(red)[..., 1:].max(), 0)

    def test_multiple_targets_keep_separate_widths_colors_fades_and_animation_state(self):
        base = Image.new('RGB', (480, 270), (10, 10, 10))
        targets = [{'id': 'one', 'bbox': [.1, .2, .3, .9], 'opacity': .35},
                   {'id': 'two', 'bbox': [.7, .2, .8, .5]}]
        colors = ((255, 0, 0), (0, 255, 255))
        for shape in TARGET_SHAPES:
            with self.subTest(shape=shape):
                combined = TargetOverlay(neon=NeonStyle(), shape=shape)
                singles = [TargetOverlay(neon=NeonStyle(), shape=shape) for _ in targets]
                for t in (0, .3, .6, .9, 1.2, 1.4):
                    present = targets if t >= .3 else targets[:1]
                    together = combined.draw(base, t, present, colors)
                    separate = base
                    for index, item in enumerate(present):
                        separate = singles[index].draw(separate, t, [item], colors)
                    np.testing.assert_array_equal(together, separate)
                np.testing.assert_array_equal(np.asarray(base), np.full((270, 480, 3), 10))

    def test_invalid_values_fail_before_media_open(self):
        for flags in (['--neon-intensity', 'nan'], ['--neon-spread', 'inf'], ['--neon-flicker', '1.1'],
                      ['--neon-intensity', '-1'], ['--neon-spread', '2.1'], ['--neon-elements', 'target=nan'],
                      ['--neon-elements', 'target=1,target=2'], ['--neon-elements', 'target-flash=1'],
                      ['--neon-elements', 'typo=1'], ['--neon-elements', ''], ['--neon-elements', 'target=3']):
            with self.subTest(flags=flags), patch('yautja.cli.load_image') as read, patch('sys.stderr', new_callable=io.StringIO):
                self.assertEqual(main(['missing.png', 'out.png', *flags]), 1)
                read.assert_not_called()

    def test_preset_roundtrip_cli_still_report_and_no_hud_effective_values(self):
        preset = Path(__file__).resolve().parents[1] / 'skills/yautja/assets/presets/abyss-neon.json'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new('RGB', (320, 180), (100, 100, 100)).save(root / 'in.png')
            def invoke(flags):
                with patch('sys.stdout', new_callable=io.StringIO) as out, patch('sys.stderr', new_callable=io.StringIO), \
                        patch('yautja.cli.binary', side_effect=AssertionError('Stills do not need FFmpeg')):
                    self.assertEqual(main([str(f) for f in flags]), 0)
                    return json.loads(out.getvalue())
            flags = ['--preset-file', preset, '--thermal', 'classic', '--neon-flicker', '.5', '--neon-elements', 'target=0,timecode=.4']
            saved = invoke([*flags, '--save-preset', root / 'saved.json'])
            self.assertTrue(saved['settings']['neon'])
            direct = invoke([root / 'in.png', root / 'direct.png', *flags])
            repeat = invoke([root / 'in.png', root / 'repeat.png', '--preset-file', root / 'saved.json'])
            self.assertEqual(direct['neon_flicker'], .5)
            self.assertEqual(direct['neon_intensities']['target-flash'], 0)
            self.assertEqual(direct['settings']['neon_elements'], 'target=0,timecode=.4')
            self.assertEqual(direct['neon_intensities'], repeat['neon_intensities'])
            with Image.open(root / 'direct.png') as a, Image.open(root / 'repeat.png') as b:
                np.testing.assert_array_equal(a, b)
        self.assertFalse(parser().parse_args(['--preset-file', str(preset), '--no-neon']).neon)
        report = extra_report(Renderer(320, 180, neon=True, hud=False), None)
        self.assertFalse(report['neon'])
        self.assertEqual(report['neon_intensity'], 0)
        self.assertFalse(any(report['neon_intensities'].values()))

    def test_notices_keep_json_stdout_clean(self):
        with tempfile.TemporaryDirectory() as folder:
            for index, flags in enumerate((['--neon-spread', '1'], ['--neon', '--glow', '.1'])):
                with patch('sys.stdout', new_callable=io.StringIO) as out, patch('sys.stderr', new_callable=io.StringIO) as err:
                    self.assertEqual(main(['--save-preset', str(Path(folder) / f'{index}.json'), *flags]), 0)
                self.assertEqual(json.loads(out.getvalue())['schema_version'], 1)
                self.assertEqual(len(err.getvalue().strip().splitlines()), 1)
                self.assertIn('--neon', err.getvalue())

    def test_faint_blurred_ink_can_have_no_visible_core(self):
        layer = Image.new('RGBA', (20, 20))
        layer.putpixel((10, 10), (38, 112, 133, 1))
        base = Image.new('RGB', (40, 40))
        NeonStyle().apply(base, layer, 10, 10, (38, 112, 133), element='callouts', width=1, blur=20)
        self.assertLessEqual(np.asarray(base).max(), 1)

    def test_crt_lines_darkening_runs_after_neon_and_rorschach_is_supported(self):
        field = np.full((180, 320), 100, np.uint8)
        for shape in ('rorschach', 'rorschach-split', 'rorschach-hollow'):
            with self.subTest(shape=shape):
                plain = np.asarray(Renderer(320, 180, neon=True, wave_style=shape).render_field(field, 0))
                striped = np.asarray(Renderer(320, 180, neon=True, wave_style=shape,
                                     crt_vertical_lines=True, crt_strength=1).render_field(field, 0))
                self.assertEqual(striped[:, ::2].max(), 0)
                np.testing.assert_array_equal(plain[:, 1::2], striped[:, 1::2])

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg not installed')
    def test_video_cli_renders_neon_on_cpu_and_preserves_audio(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, target = root / 'input.mp4', root / 'output.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=320x180:r=12:d=0.5',
                            '-f', 'lavfi', '-i', 'sine=frequency=440:duration=0.5', '-c:v', 'libx264', '-c:a', 'aac',
                            '-shortest', str(source)], check=True, capture_output=True)
            with patch('sys.stdout', new_callable=io.StringIO) as out, patch('sys.stderr', new_callable=io.StringIO), \
                    patch('yautja.semantic.GroundedSegmenter', side_effect=AssertionError('Classic needs no models')):
                self.assertEqual(main([str(source), str(target), '--neon', '--neon-flicker', '.5', '--timecode']), 0)
            report = json.loads(out.getvalue())
            self.assertTrue(report['neon'] and report['audio_preserved'])
            self.assertEqual(report['frames'], 6)
            self.assertEqual(report['neon_flicker'], .5)
            subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(target), '-f', 'null', '-'], check=True, capture_output=True)


if __name__ == '__main__':
    unittest.main()
