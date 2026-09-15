import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image, ImageDraw

from yautja.cli import parser, main, extra_report
from yautja.colors import HUD_DEFAULTS
from yautja.geometry import GeometryStyle, GEO_OPTIONS, TARGET_OPTIONS
from yautja.looks import FOCUS_SETTINGS, LOOK_PRESETS
from yautja.presets import VISUAL_OPTIONS, load_preset, validate_settings
from yautja.render import Renderer
from yautja.semantic import Subject
from yautja.signal import SignalStyle
from yautja.target import TargetOverlay, detail_shapes
from yautja.typography import HUDTypography, FONT_FILES


class FocusTests(unittest.TestCase):
    def setUp(self):
        self.size = (320, 180)
        self.frame = Image.new('RGB', self.size, (43, 57, 68))
        mask = Image.new('L', self.size)
        d = ImageDraw.Draw(mask)
        d.ellipse((130, 40, 170, 80), fill=255)
        d.rectangle((125, 70, 180, 170), fill=255)
        d.rectangle((105, 95, 135, 120), fill=255)
        self.mask = np.asarray(mask, np.float32) / 255
        self.subject = Subject(self.mask, 'person', .95, track_id=1)

    def test_complete_recipes_and_explicit_options_in_both_orders(self):
        for name in ('focus', 'relic', 'murphy', 'fremont'):
            for tokens in (['--stylepreset', name, '--no-neon', '--hud-font', 'orbitron-medium'],
                           ['--no-neon', '--hud-font', 'orbitron-medium', '--stylepreset', name]):
                args = parser().parse_args(tokens)
                self.assertFalse(args.neon)
                self.assertEqual(args.hud_font, 'orbitron-medium')
        for key, value in FOCUS_SETTINGS.items():
            if key not in ('hud_colors', 'subject_code', 'target_motif', 'neon_elements'):
                self.assertEqual(LOOK_PRESETS['relic'][key], value)
        self.assertTrue(set((*GEO_OPTIONS, *TARGET_OPTIONS, 'hud_font', 'analysis_outline_width')) <= set(VISUAL_OPTIONS))
        self.assertNotIn('hud_font_file', VISUAL_OPTIONS)
        self.assertIsNone(parser().parse_args(['--stylepreset', 'murphy', '--no-target-label']).target_label)
        auto = Renderer(*self.size, target_mode='auto', target_flash=True)
        self.assertTrue(extra_report(auto, None)['target_flash'])

    def test_json_roundtrip_and_map_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'saved.json'
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['--stylepreset', 'relic', '--save-preset', str(path)]), 0)
            data = load_preset(path)
            settings = validate_settings(data['settings'], parser())
            renderer = Renderer(*self.size, **{k: v for k, v in settings.items() if k not in ('waveform', 'wave_window', 'wave_gain')})
            self.assertEqual(renderer.geometry.target_mode, 'auto')
            args = parser().parse_args(['--preset-file', str(path), '--neon-elements', 'geo-grid=0'])
            self.assertEqual(args.neon_elements, 'geo-grid=0')
            data['settings']['hud_font_file'] = 'private.ttf'
            path.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaises(ValueError):
                load_preset(path)

    def test_fonts_have_actual_weights_and_cached_glyphs(self):
        for face in FONT_FILES:
            typography = HUDTypography(face)
            for text in ('TARGETING', 'CRITERIA', '0123456789ABCDEF', '00:12:34.567'):
                mask = typography.mask(text, 18)
                self.assertIs(mask, typography.mask(text, 18))
                self.assertIsNotNone(mask.getbbox())
            self.assertEqual(typography.font(20).getname()[0].split()[0], 'Michroma' if face == 'michroma' else 'Orbitron')
        r = Renderer(*self.size, look_preset='fremont')
        self.assertIn('Bold', r.typography.font(20).getname()[1])
        self.assertEqual(r.analysis.analysis_outline_width, 5)

    def test_custom_fonts_validate_before_opening_media(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'broken.ttf'
            path.write_bytes(b'not a font')
            for value in (path, path.with_name('missing.ttf')):
                with self.assertRaises(ValueError):
                    HUDTypography(hud_font_file=value)
            with contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(main(['missing.png', 'out.png', '--hud-font-file', str(path)]), 1)
            self.assertIn('--hud-font-file', err.getvalue())
        path = Path(__file__).resolve().parents[1] / 'src/yautja/assets/fonts/Michroma-Regular.ttf'
        face = HUDTypography(hud_font_file=path)
        self.assertEqual(face.report()['hud_font_file'], str(path.resolve()))

    def test_tech_routes_every_text_consumer_through_readable_faces(self):
        r = Renderer(*self.size, hud_glyphs='tech', hud_font='orbitron-bold',
                     subject_code=True, subject_labels=True, verbose=True, show_timecode=True)
        self.assertEqual(r.code_mask(2, 14).tobytes(), r.typography.glyph(2, 14).tobytes())
        self.assertEqual(r.callout_glyph(3, 14).tobytes(), r.typography.glyph(3, 14).tobytes())
        a = r.render(self.frame, 0., subjects=[self.subject], target_static=True)
        b = Renderer(*self.size, hud_glyphs='cyber', subject_code=True, subject_labels=True,
                     verbose=True, show_timecode=True).render(self.frame, 0., subjects=[self.subject], target_static=True)
        self.assertNotEqual(a.tobytes(), b.tobytes())

    def test_grid_cached_seeded_animated_and_frozen(self):
        def draw(seed=42, speed=1, time=0, static=False):
            r = Renderer(*self.size, geo_grid=True, geo_grid_speed=speed, seed=seed)
            image = self.frame.copy()
            r.geometry.draw_grid(r, image, time, static)
            self.assertIs(r.geometry.lattice(self.size, seed)[0], r.geometry.lattice(self.size, seed)[0])
            return image.tobytes()
        self.assertEqual(draw(), draw())
        self.assertNotEqual(draw(), draw(seed=43))
        self.assertNotEqual(draw(), draw(time=1))
        self.assertEqual(draw(speed=0), draw(speed=0, time=8))
        self.assertEqual(draw(static=True), draw(static=True, time=8))

    def test_auto_targets_respect_explicit_empty_selection_and_hud_off(self):
        r = Renderer(*self.size, look_preset='focus')
        r.render(self.frame, 0, subjects=[self.subject], target_static=True)
        self.assertEqual(r.target_overlay.placements[0][0], 'auto-1')
        r.render(self.frame, .1, subjects=[self.subject], targets=[], target_static=True)
        self.assertFalse(r.target_overlay.placements)
        target = [{'id': 'chosen', 'bbox': [.4, .2, .6, .9]}]
        r.render(self.frame, .2, subjects=[self.subject], targets=target, target_static=True)
        self.assertEqual(r.target_overlay.placements[0][0], 'chosen')
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(['--target-mode', 'auto', '--save-preset', 'unused.json'])
        for name in ('focus', 'relic', 'murphy', 'fremont'):
            off = Renderer(*self.size, look_preset=name, hud=False)
            image = off.render(self.frame, .2, subjects=[self.subject], targets=target)
            self.assertFalse(off.target_overlay.placements)
            self.assertFalse(extra_report(off, None)['geo_grid'])
            self.assertEqual(image.size, self.size)

    def test_shimmer_is_partial_seeded_moves_and_follows_current_edge(self):
        def ink(speed=1, time=0, mask=None):
            style = SignalStyle(subject_outline=True, outline_style='shimmer', outline_speed=speed)
            r = Renderer(*self.size, glow=0, hud_theme='custom', hud_colors='subject-outline=#fff')
            image = Image.new('RGB', self.size)
            subject = self.subject if mask is None else Subject(mask, 'person', .95, track_id=1)
            style.draw(r, image, [subject], time, 1)
            return np.asarray(image).max(axis=2)
        a, b = ink(), ink(time=2)
        self.assertGreater(np.count_nonzero(a), 20)
        self.assertFalse(np.array_equal(a,b))
        np.testing.assert_array_equal(ink(speed=0), ink(speed=0,time=10))
        moved = np.roll(self.mask, 60, axis=1)
        result = ink(time=.1, mask=moved)
        self.assertEqual(np.count_nonzero(result[moved==0]), 0)
        self.assertLess(np.count_nonzero(result), np.count_nonzero(moved))

    def test_behind_code_occludes_final_neon_and_blur_for_all_subjects(self):
        other = Subject(np.roll(self.mask, 30, axis=1), 'person', .9, track_id=2)
        union = (self.mask >= .5) | (other.mask >= .5)
        for neon in (False, True):
            for blur in (0, 12):
                r = Renderer(*self.size, subject_code=True, code_layer='behind', code_density=1.,
                             code_size=40, neon=neon, neon_intensity=2, hud_blur_elements=f'subject-code={blur}')
                image = self.frame.copy()
                r.signal.draw(r, image, [self.subject, other], 1.2, 1)
                pixels = np.asarray(image)
                np.testing.assert_array_equal(pixels[union], np.asarray(self.frame)[union])
                self.assertGreater(np.count_nonzero(pixels[~union] != np.asarray(self.frame)[~union]), 0)

    def test_new_reticles_geometry_axes_state_and_captions(self):
        self.assertEqual(len(detail_shapes('hexagon', 100, True)[0][0][0]), 6)
        for shape in ('hexagon','frame-box'):
            r = Renderer(*self.size, target_shape=shape, target_motif='triangles', target_label='TARGETING', glow=0)
            target = [{'id':'one','bbox':[.35,.15,.65,.9]}]
            r.draw_targets(self.frame.copy(),0,[],target,((255,255,255),)*2,shot=1)
            r.draw_targets(self.frame.copy(),.4,[],target,((255,255,255),)*2,shot=1)
            self.assertGreater(r.target_overlay.placements[0][-1],0)
            r.draw_targets(self.frame.copy(),.5,[],target,((255,255,255),)*2,shot=2)
            self.assertEqual(r.target_overlay.placements[0][-1],0)
            r.draw_targets(self.frame.copy(),.2,[],target,((255,255,255),)*2,shot=2,static=True)
            self.assertEqual(r.target_overlay.placements[0][-1],1)
            self.assertIsNotNone(r.geometry.label_box)
            r.draw_targets(self.frame.copy(),.3,[],[],((255,255,255),)*2,shot=2)
            self.assertIsNone(r.geometry.label_box)
        overlay=TargetOverlay(shape='frame-box',flash_rate=0)
        result=np.asarray(overlay.draw(Image.new('RGB', self.size),0,target,((255,255,255),)*2,static=True))
        cx,cy=160,94
        self.assertLess(result[cy,cx].max(),10)
        self.assertGreater(result[cy,0].max(),100)
        self.assertGreater(result[0,cx].max(),100)

    def test_caption_safe_layout_in_all_aspects(self):
        for size in ((960,540),(540,960),(128,72),(72,128)):
            r=Renderer(*size,target_label='LONG TARGET LABEL 123456',hud_font='orbitron-bold')
            r.render(Image.new('RGB',size),0,targets=[{'id':'one','bbox':[.9,.01,1,.4]}],target_static=True)
            x0,y0,x1,y1=r.geometry.label_box
            self.assertTrue(0<=x0<x1<=size[0] and 0<=y0<y1<=size[1])

    def test_new_option_validation(self):
        for kw in ({'geo_grid_scale':39},{'geo_grid_speed':float('nan')},{'target_label':'\n'},
                   {'target_label':'x'*25},{'target_motif_count':2.5},{'target_motif_scale':4}):
            with self.assertRaises(ValueError): GeometryStyle(**kw)
        for kw in ({'outline_arcs':1.5},{'outline_coverage':2},{'outline_speed':float('inf')},{'code_layer':'front'}):
            with self.assertRaises(ValueError): SignalStyle(**kw)


if __name__ == '__main__':
    unittest.main()
