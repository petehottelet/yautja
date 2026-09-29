"""Object-specific styles, transparent instruments and portable display treatments."""
import io
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw

from yautja.brand_new_day import DayHUD, READOUT_STYLES, outline_rules
from yautja.cli import main, parser
from yautja.figures import FigureCatalog, OutlineSelection
from yautja.presets import catalog, load_preset
from yautja.render import Renderer
from yautja.semantic import Subject
from yautja.typography import HUDTypography


class BrandNewDayTests(unittest.TestCase):
    size = (640, 360)

    def subjects(self):
        result = []
        for i, x in enumerate((190, 390), 1):
            mask = Image.new('L', self.size)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((x+15, 85, x+45, 120), fill=255)
            draw.polygon(((x+15,115),(x+45,115),(x+60,220),(x+42,275),
                          (x+30,220),(x+15,275),(x,220)), fill=255)
            result.append(Subject(np.asarray(mask, np.float32)/255, 'person' if i == 1 else 'robot', .95, track_id=i))
        return result

    def renderer(self, **options):
        return Renderer(*self.size, look_preset='brand-new-day',
                        **{**dict(object_outline_fill=0.,object_outline_block=14.,object_outline_glow=0.,scanlines=False,crt_bleed=0.,
                                  hud_colors='object-outline=#000000',hud_top_left='off',hud_top_right='off',
                                  hud_bottom_left='off',hud_bottom_right='off'),**options})

    def test_discovery_and_explicit_override_precedence(self):
        preset = next(p for p in catalog()['presets'] if p['id'] == 'brand-new-day')
        self.assertEqual((preset['name'], preset['kind']), ('Brand New Day', 'look'))
        a = parser().parse_args(['--stylepreset', 'Brand New Day', '--object-outline', 'box', '--hud-font', 'pixel'])
        b = parser().parse_args(['--hud-font', 'pixel', '--object-outline', 'box', '--stylepreset', 'brand-new-day'])
        self.assertEqual(vars(a), vars(b))
        self.assertEqual((a.object_outline, a.hud_font), ('box', 'pixel'))

    def test_all_outline_modes_and_per_object_override(self):
        source = Image.new('RGB', self.size, (190, 205, 220))
        subjects = self.subjects()
        frames = {}
        for mode in ('off', 'chunky', 'box'):
            frames[mode] = np.asarray(self.renderer(object_outline=mode).render(source, 0, subjects=subjects))
        np.testing.assert_array_equal(frames['off'], source)
        changes = {key: (frame != frames['off']).any(axis=2) for key, frame in frames.items()}
        self.assertFalse(np.array_equal(changes['chunky'], changes['box']))
        self.assertGreater(changes['chunky'][:, 380:470].sum(), 0)  # Non-human object too.
        rendered = self.renderer().render(source, 0, subjects=subjects, object_styles={1:'off', 2:'box'})
        np.testing.assert_array_equal(np.asarray(rendered)[:, :320], np.asarray(source)[:, :320])
        np.testing.assert_array_equal(np.asarray(rendered)[:, 320:], frames['box'][:, 320:])
        # Transparent interiors and a complete, object-sized rectangle.
        self.assertEqual(tuple(frames['box'][160,210]), (190,205,220))
        self.assertTrue(changes['box'][81,186:255].all())

    def test_outline_modes_are_mutually_exclusive_everywhere(self):
        with self.assertRaises(ValueError):
            DayHUD(object_outline='both')
        with self.assertRaises(ValueError):
            outline_rules('S001-F001=both')
        with self.assertRaises(ValueError):
            outline_rules('S001-F001=chunky,S001-F001=box')
        with self.assertRaises(ValueError):
            self.renderer().render(Image.new('RGB',self.size),0,object_styles={1:'both'})
        with patch('sys.stderr',new_callable=io.StringIO), self.assertRaises(SystemExit):
            parser().parse_args(['--object-outline','both'])

    def test_coarse_amber_contours_translucent_fill_and_no_stacked_rectangle(self):
        source = Image.new('RGB',self.size,(90,130,170))
        subjects = self.subjects()[:1]
        renderer = Renderer(*self.size,look_preset='brand-new-day',hud_top_left='off',hud_top_right='off',
                            hud_bottom_left='off',hud_bottom_right='off',object_outline_glow=0.,scanlines=False,crt_bleed=0.)
        self.assertEqual((renderer.day.object_outline,renderer.day.object_outline_block,renderer.day.object_outline_width,
                          renderer.day.object_outline_fill), ('chunky',33.6,5.6,.35))
        result = np.asarray(renderer.render(source,0,subjects=subjects))
        # Deep inside the silhouette, mix the source with amber at 35% alpha.
        expected = np.round(np.array((255,191,71))*89/255 + np.array((90,130,170))*166/255).astype('uint8')
        np.testing.assert_array_equal(result[175,220],expected)
        # A bounding-box corner outside the chunky shape remains source footage.
        np.testing.assert_array_equal(result[81,186],(90,130,170))
        contour = np.all(result == (255,191,71),axis=2)
        self.assertGreater(contour.sum(),0)
        self.assertEqual(renderer.day.report()['object_outline_fill'],.35)
        # Overlapping detections must not accumulate more than the chosen fill.
        duplicate = self.subjects()[0]
        duplicate.track_id = 3
        np.testing.assert_array_equal(renderer.render(source,0,subjects=[subjects[0],duplicate]),result)

    def test_empty_masks_fading_and_disabled_hud(self):
        source = Image.new('RGB', self.size, 'white')
        subjects = self.subjects()
        for subject in subjects:
            subject.opacity = .5
        full = np.asarray(self.renderer().render(source, 0, subjects=subjects))
        self.assertGreaterEqual(full.min(), 127)
        empty = Subject(np.zeros((360,640), np.float32), 'person', .9)
        np.testing.assert_array_equal(self.renderer().render(source, 0, subjects=[empty]), source)
        for style in READOUT_STYLES:
            r = Renderer(*self.size, look_preset='brand-new-day', hud=False, readout_style=style,scanlines=False,crt_bleed=0.)
            np.testing.assert_array_equal(r.render(source, 0, subjects=subjects), source)
        r = Renderer(*self.size, look_preset='brand-new-day', hud_opacity=0, readout_style='amber-glow',scanlines=False,crt_bleed=0.)
        np.testing.assert_array_equal(r.render(source, 0, subjects=subjects), source)

    def test_object_glow_emits_from_edges_without_brightening_the_whole_fill(self):
        source = Image.new('RGB',self.size,(30,40,50))
        mask = np.zeros((360,640),np.float32)
        mask[100:260,200:400] = 1
        subjects = [Subject(mask,'person',.95,track_id=1)]
        options = dict(object_outline='chunky',object_outline_fill=.5,object_outline_block=42.,hud_colors='object-outline=#ffbf47')
        unlit = np.asarray(self.renderer(**options).render(source,0,subjects=subjects))
        renderer = self.renderer(**options,object_outline_glow=.65)
        lit = np.asarray(renderer.render(source,0,subjects=subjects))
        self.assertGreater(int(lit[170,188,0]),int(unlit[170,188,0]))
        self.assertGreater(int(lit[170,195,1]),int(unlit[170,195,1]))
        np.testing.assert_array_equal(lit[170,300],unlit[170,300])
        np.testing.assert_array_equal(lit[40,80],source.getpixel((80,40)))
        for controls in ({'hud':False},{'hud_opacity':0}):
            np.testing.assert_array_equal(self.renderer(**options,object_outline_glow=.65,**controls).render(source,0,subjects=subjects),source)

    def test_crt_treatment_covers_scene_objects_and_readout(self):
        source = Image.new('RGB',self.size,(180,180,180))
        subjects = self.subjects()
        default = Renderer(*self.size,look_preset='brand-new-day')
        self.assertEqual((default.scanlines,default.crt_strength,default.display.crt_bleed),(True,.18,.2))
        self.assertEqual(default.day.object_outline_glow,.65)
        plain = Renderer(*self.size,look_preset='brand-new-day',scanlines=False,crt_bleed=0.)
        lined = Renderer(*self.size,look_preset='brand-new-day',crt_bleed=0.)
        clean = np.asarray(plain.render(source,0,subjects=subjects))
        actual = np.asarray(lined.render(source,0,subjects=subjects))
        expected = clean.astype(np.float32)
        expected[::2] *= .82
        np.testing.assert_array_equal(actual,np.uint8(expected))
        # Background, subject fill and upper-left amber readout all receive lines.
        for region in ((slice(180,220),slice(50,100)),(slice(160,220),slice(205,225)),
                       (slice(12,70),slice(12,130))):
            self.assertTrue(np.any(actual[region] != clean[region]))
        self.assertFalse(np.array_equal(default.render(source,0,subjects=subjects),actual))

    def test_transparent_black_instruments_and_amber_treatments(self):
        font = HUDTypography('crt')
        for mode in ('readout', 'city-map', 'elevation', 'telemetry'):
            layer = DayHUD().instrument(font, mode, 1., [], 1, 42)
            pixels = np.asarray(layer)
            self.assertEqual(pixels[..., :3].max(), 0)
            self.assertGreater((pixels[...,3] == 0).mean(), .5)
            self.assertGreater(pixels[...,3].max(), 0)
        black = DayHUD(readout_style='amber-black').instrument(font, 'readout', 0, [], 1, 42)
        glass = DayHUD(readout_style='amber-glow').instrument(font, 'readout', 0, [], 1, 42)
        self.assertEqual(black.getpixel((120,134))[3], 255)
        self.assertEqual(black.getpixel((269,100)), (0,0,0,0))
        self.assertGreater(glass.getpixel((120,134))[3], 0)
        self.assertLess(glass.getpixel((120,134))[3], 255)
        self.assertGreater(np.asarray(black)[...,0].max(), 240)
        no_glow = DayHUD(readout_style='amber-glow', readout_glow=0).instrument(font, 'readout', 0, [], 1, 42)
        self.assertFalse(np.array_equal(glass, no_glow))

    def test_instruments_animate_deterministically_and_fit_portrait(self):
        r = Renderer(240, 640, look_preset='brand-new-day', hud_panel_scale=2)
        source = Image.new('RGB', (240,640), (180,180,180))
        first = np.asarray(r.render(source, 0))
        np.testing.assert_array_equal(first, r.render(source, 0))
        self.assertFalse(np.array_equal(first, r.render(source, 1)))
        boxes = list(r.day.panel_bounds.values())
        self.assertEqual(len(boxes), 4)
        for i, a in enumerate(boxes):
            self.assertTrue(0 <= a[0] < a[2] <= 240 and 0 <= a[1] < a[3] <= 640)
            self.assertAlmostEqual((a[2]-a[0])/(a[3]-a[1]), 280/168, delta=.03)
            for b in boxes[i+1:]:
                self.assertTrue(a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])

    def test_corner_lineart_has_bold_strokes_and_unchanged_lettering(self):
        typography = HUDTypography('crt')
        panels = {mode: np.asarray(DayHUD().instrument(typography,mode,0,[],1,42))
                  for mode in ('city-map','elevation','telemetry')}
        city, terrain, telemetry = (panels[mode][...,3] for mode in panels)
        # Measure isolated cross-sections of the map compass, street and block,
        # terrain axis and contour, and the telemetry trace in rendered pixels.
        for section, expected in ((city[65,260:270], [4,5]), (city[22:36,225], [4,5,6,7,8,9]),
                                  (city[35,10:20], [4,5]), (terrain[40,10:20], [4,5]),
                                  (terrain[20:37,160], [8,9]), (telemetry[55:90,160], [24,25,26,27])):
            self.assertEqual(np.flatnonzero(section).tolist(),expected)
        for mode, title in (('city-map','SECTOR GRID / SIM'),('elevation','TERRAIN / SIM PROFILE'),
                            ('telemetry','OPTICAL TELEMETRY')):
            mask = typography.mask(title,10)
            np.testing.assert_array_equal(panels[mode][8:18,12:12+mask.width,3],mask)
            self.assertEqual(panels[mode][...,:3].max(),0)
            self.assertEqual(panels[mode][0,0,3],0)

    def test_pixel_and_crt_fonts_are_portable_and_distinct(self):
        from yautja.crt_font import CLEAN, SERIF, WIDE, font_data
        from fontTools.ttLib import TTFont

        faces = ('pixel', 'crt', 'crt-clean', 'crt-wide')
        masks = [HUDTypography(font).mask('BRAND NEW DAY', 28) for font in faces]
        # Freeze the approved Pixel sample independently of the new CRT engine.
        self.assertEqual(hashlib.sha256(masks[0].tobytes()).hexdigest(),
                         'cbe51e920f483c0b242f8ed6f0d2c60754c5d39f8d7febbe38848972ea008b77')
        self.assertEqual(masks[0].size, (308,28))
        self.assertEqual(len({(m.size,m.tobytes()) for m in masks}), 4)
        self.assertGreater(masks[3].width, masks[1].width)
        self.assertEqual(set(np.unique(masks[0])), {0,255})
        self.assertEqual(HUDTypography('crt').report()['hud_font_family'], 'Yautja CRT')
        # The serifed E and straight-sided E retain distinct reference shapes.
        self.assertEqual(SERIF['E'][:3], (254,102,98))
        self.assertEqual(CLEAN['E'][:3], (254,192,192))
        self.assertEqual(WIDE['A'][:4], (56,108,198,198))
        self.assertEqual(WIDE['E'][:4], (254,98,104,120))
        self.assertEqual(set(np.unique(masks[3])), {0,255})
        for face in faces[1:]:
            with TTFont(io.BytesIO(font_data(face))) as font:
                self.assertTrue(set(range(32,127)).issubset(font.getBestCmap()))
                for char in 'Aa0123!:;':
                    self.assertGreater(font['glyf'][font.getBestCmap()[ord(char)]].numberOfContours,0)
            typography = HUDTypography(face)
            self.assertNotEqual(typography.mask('abc',21).tobytes(), typography.mask('ABC',21).tobytes())
            self.assertEqual(typography.font(24).getname()[0], typography.report()['hud_font_family'])

    def test_reversed_highlights_have_actual_transparent_letter_cutouts(self):
        for font in ('pixel', 'crt', 'crt-clean', 'crt-wide'):
            for style in ('reversed', 'amber-reversed'):
                typography = HUDTypography(font)
                layer = DayHUD(readout_style=style).instrument(typography, 'readout', 0, [], 1, 42)
                text = np.asarray(typography.mask('BRAND NEW DAY', 14))
                alpha = np.asarray(layer.getchannel('A'))[13:27, 16:16+text.shape[1]]
                np.testing.assert_array_equal(alpha, 255-text)
                self.assertEqual(layer.getpixel((12,12))[3], 255)
                source = Image.new('RGBA', layer.size, (85,133,197,255))
                composite = np.asarray(Image.alpha_composite(source,layer))[13:27,16:16+text.shape[1],:3]
                self.assertTrue((composite[text==255] == (85,133,197)).all())
                no_glow = DayHUD(readout_style=style, readout_glow=0).instrument(typography, 'readout', 0, [], 1, 42)
                # Solid bars are 115% of the title height, rounded to pixels.
                column = np.flatnonzero(np.asarray(no_glow.getchannel('A'))[:36,12])
                self.assertEqual((column.min(),column.max(),len(column)), (12,27,round(14*1.15)))
                if style == 'amber-reversed':
                    self.assertEqual(no_glow.getpixel((12,12)), (255,191,71,255))
                    self.assertGreater(np.asarray(layer.getchannel('A'))[10,12],0)
                    self.assertFalse(np.array_equal(layer,no_glow))

    def test_amber_text_has_bright_core_and_glow_outside_the_letters(self):
        typography = HUDTypography('crt')
        ink = np.asarray(typography.mask('BRAND NEW DAY',14))
        for style in ('amber-black', 'amber-bars', 'amber-glow'):
            def panel(glow):
                layer = DayHUD(readout_style=style,readout_glow=glow).instrument(typography,'readout',0,[],1,42)
                return np.asarray(Image.alpha_composite(Image.new('RGBA',layer.size,(0,0,0,255)),layer))
            lit, unlit = panel(.65), panel(0)
            title = lit[13:27,16:16+ink.shape[1],:3]
            self.assertTrue((title[ink==255,1] >= 220).all())
            # Actual colored light above the title, beyond every glyph's bounds.
            self.assertGreater(lit[11,20,0],unlit[11,20,0])
            self.assertGreater(lit[11,20,1],unlit[11,20,1])

    def test_amber_bars_keep_black_highlights_and_clear_gaps(self):
        font = HUDTypography('crt')
        unlit = DayHUD(readout_style='amber-bars',readout_glow=0).instrument(font,'readout',0,[],1,42)
        lit = DayHUD(readout_style='amber-bars').instrument(font,'readout',0,[],1,42)
        self.assertEqual(unlit.getpixel((12,12)),(0,0,0,255))
        self.assertEqual(unlit.getpixel((270,100))[3],0)
        self.assertEqual(unlit.getpixel((120,44))[3],0)
        self.assertEqual(lit.getpixel((270,100))[3],0)
        text = np.asarray(font.mask('BRAND NEW DAY',14))
        color = np.asarray(lit)[13:27,16:16+text.shape[1]]
        self.assertTrue((color[text==255,3] == 255).all())
        self.assertTrue((color[text==255,1] >= 220).all())
        self.assertGreater(np.asarray(lit)[11,20,3],0)

    def test_default_readout_backing_follows_rows_and_covers_all_graphics(self):
        from PIL import ImageFilter

        renderer = Renderer(*self.size,look_preset='brand-new-day')
        self.assertEqual(renderer.day.readout_style,'amber-black')
        for face in ('pixel','crt','crt-clean','crt-wide'):
            for time,subjects in ((0,[]),(12.34,self.subjects())):
                font = HUDTypography(face)
                source_ink = DayHUD(readout_style='ink').instrument(font,'readout',time,subjects,2,42)
                plain = DayHUD(readout_style='amber-black',readout_glow=0).instrument(font,'readout',time,subjects,2,42)
                glowing = DayHUD(readout_style='amber-black').instrument(font,'readout',time,subjects,2,42)
                # Every solid element has opaque backing extending at least
                # eight pixels in all directions, not just around text masks.
                padded = np.asarray(source_ink.getchannel('A').filter(ImageFilter.MaxFilter(17))) > 0
                self.assertTrue((np.asarray(plain)[padded,3] == 255).all())
                self.assertTrue((np.asarray(glowing)[padded,3] == 255).all())
                for point in ((10,9),(10,37),(28,56),(12,141),(76,149),(120,44),(120,134)):
                    self.assertEqual(plain.getpixel(point),(0,0,0,255))
                # Short title/time rows leave the scene exposed on the right;
                # the long divider and bottom strip still have black backing.
                for point in ((267,19),(267,78),(267,122)):
                    self.assertEqual(plain.getpixel(point)[3],0)
                for point in ((267,37),(263,149)):
                    self.assertEqual(plain.getpixel(point),(0,0,0,255))
                # Each row's outer edge follows the current font and content,
                # including its square marker, instead of a full panel width.
                for y in (19,56,78,100,122):
                    occupied = np.flatnonzero(np.asarray(source_ink.getchannel('A'))[y-5:y+6].any(axis=0))
                    right = occupied[-1]
                    self.assertEqual(plain.getpixel((right+10,y)),(0,0,0,255))
                    self.assertEqual(plain.getpixel((right+11,y))[3],0)
                self.assertTrue((np.asarray(plain)[5:162,10,3] == 255).all())
                self.assertEqual(plain.getpixel((0,0))[3],0)
                self.assertEqual(plain.getpixel((279,167))[3],0)
                self.assertFalse(np.array_equal(plain,glowing))

    def test_optional_neon_uses_amber_for_readouts_and_corner_ink_elsewhere(self):
        for style in ('amber-glow', 'amber-bars', 'amber-reversed'):
            r = Renderer(*self.size, look_preset='brand-new-day', readout_style=style, neon=True)
            with patch.object(r.neon_style, 'apply', wraps=r.neon_style.apply) as apply:
                r.render(Image.new('RGB', self.size, (120,120,120)), 0)
            colors = {call.kwargs['element']:call.args[4] for call in apply.call_args_list}
            self.assertEqual(colors['corner-top-left'], (255,191,71))
            self.assertEqual(colors['corner-top-right'], (0,0,0))

    def test_catalog_styles_are_shot_local_match_classes_and_reset(self):
        with tempfile.TemporaryDirectory() as folder:
            source, path = Path(folder)/'source.png', Path(folder)/'figures.json'
            frame = Image.new('RGB', self.size, 'white')
            frame.save(source)
            catalog = FigureCatalog(source, fps=2)
            subjects = self.subjects()
            catalog.add(frame, 0., subjects, 1)
            catalog.add(frame, .5, subjects, 1)
            catalog.add(frame, 1., subjects, 2)
            catalog.add(frame, 1.5, subjects, 2)
            path.write_text(json.dumps(catalog.data), encoding='utf-8')
            selection = OutlineSelection(path, source, {'S001-F001':'chunky', 'S001-F002':'off', 'S002-F001':'box'})
            self.assertEqual(selection.styles_at(0., subjects), {1:'chunky',2:'off'})
            # The same live track ID receives the other shot's choice.
            self.assertEqual(selection.styles_at(1.25, subjects), {1:'box'})
            self.assertEqual(selection.styles_at(2.5, subjects), {})
            self.assertEqual(selection.styles_at(.25, list(reversed(subjects))), {1:'chunky',2:'off'})
            subjects[0].label = 'chair'
            self.assertEqual(selection.styles_at(.3, subjects), {2:'off'})
            with self.assertRaisesRegex(ValueError, 'Unknown target IDs'):
                OutlineSelection(path, source, {'S003-F001':'box'})

    def test_save_load_real_conversion_and_runtime_rules_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, saved = root/'source.png', root/'preset.json'
            Image.new('RGB', self.size, (183,193,210)).save(source)
            flags = ['--stylepreset','brand-new-day','--object-outline','off','--thermal','luminance',
                     '--readout-style','amber-black','--hud-font','crt-clean','--object-outline-fill','.5','--object-outline-glow','.65']
            with patch('sys.stdout', new_callable=io.StringIO):
                self.assertEqual(main([*flags,'--save-preset',str(saved)]), 0)
                self.assertEqual(main([str(source),str(root/'a.png'),*flags]), 0)
                self.assertEqual(main([str(source),str(root/'b.png'),'--preset-file',str(saved)]), 0)
            with Image.open(root/'a.png') as a, Image.open(root/'b.png') as b:
                np.testing.assert_array_equal(a,b)
            self.assertEqual(load_preset(saved)['settings']['readout_style'], 'amber-black')
            self.assertEqual(load_preset(saved)['settings']['object_outline_fill'],.5)
            self.assertEqual(load_preset(saved)['settings']['object_outline_glow'],.65)
            self.assertEqual(load_preset(saved)['settings']['hud_font'], 'crt-clean')
            self.assertNotIn('object_outlines', load_preset(saved)['settings'])
        for flags in (['--object-outlines','S001-F001=box'], ['--object-outline','box'],
                      ['--object-outline-block','nan'], ['--object-outline-fill','nan'], ['--object-outline-fill','1.1'],
                      ['--object-outline-glow','nan'], ['--object-outline-glow','1.1'],
                      ['--readout-fill','2'], ['--hud-top-left','missing']):
            with self.subTest(flags=flags), patch('sys.stderr', new_callable=io.StringIO), patch('yautja.cli.convert') as convert:
                try:
                    status = main(['input.png','output.png',*flags])
                except SystemExit as exc:
                    status = exc.code
                self.assertNotEqual(status, 0)
                convert.assert_not_called()
        for value in ('', 'S1-F1=box', 'S001-F001=bad', 'S001-F001=box,S001-F001=off'):
            with self.assertRaises(ValueError):
                outline_rules(value)


if __name__ == '__main__':
    unittest.main()
