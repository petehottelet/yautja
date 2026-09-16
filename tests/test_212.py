"""Shared 2.12 controls: flow-aligned silhouettes, display devices and geometry."""
import io
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from yautja.cli import main, parser, extra_report
from yautja.geometry import GeometryStyle
from yautja.hologram import holographic_ink
from yautja.masks import stabilize_binary, subject_binary
from yautja.presets import VISUAL_OPTIONS, NULLABLE, save_preset, load_preset, validate_settings
from yautja.render import Renderer
from yautja.semantic import SemanticTracker, Subject
from yautja.waveform import WAVE_STYLES, waveform_masks, vocoder_masks


class Release212Tests(unittest.TestCase):
    def subject(self, x=80):
        mask = np.zeros((180,320),np.float32)
        mask[30:165,x:x+65] = 1
        return Subject(mask,'person',.95,track_id=1)

    @unittest.skipUnless(importlib.util.find_spec('cv2'), 'Optional tracking runtime')
    def test_hysteresis_closing_islands_and_disable(self):
        mask = self.subject().mask
        mask[40:43,220:223] = 1  # <1% satellite
        mask[60:100,110] = 0  # narrow seam
        cleaned = stabilize_binary(mask,None,.18,.02)
        self.assertFalse(cleaned[41,221])
        self.assertTrue(cleaned[80,110])
        np.testing.assert_array_equal(stabilize_binary(mask,None,0,0), mask>=.5)
        previous = np.array([[True,False,True,False]])
        current = np.array([[.42,.579,.419,.58]])
        np.testing.assert_array_equal(stabilize_binary(current,previous,.18,0), [[True,False,False,True]])

    @unittest.skipUnless(importlib.util.find_spec('cv2'), 'Optional tracking runtime')
    def test_tracker_refinement_flicker_cuts_and_legacy(self):
        class Detector:
            device='cpu'
            def __init__(self): self.index=0
            def detect(inner,frame):
                mask=np.zeros((frame.height,frame.width),np.float32); mask[20:150,50:130]=1
                return [Subject(mask,'person',.95)]
            def refine(inner,frame,tracks):
                inner.index += 1
                for track in tracks:
                    mask=np.zeros_like(track.mask); mask[20:150,50:130]=1
                    mask[60:70,130:139]=inner.index%2
                    track.mask=mask
        frame=Image.new('RGB',(320,180),30)
        for stability in (.18,0):
            detector=Detector(); tracker=SemanticTracker(detector,interval=1,refine_masks=True,mask_stability=stability,mask_min_region=0)
            states=[]
            for i in range(12):
                subject=tracker.update(frame,i/24)[0]
                states.append(bool(np.asarray(subject_binary(subject))[64,134]))
            self.assertEqual(detector.refine_iou,.3 if stability else .1)
            self.assertEqual(len(set(states)),1 if stability else 2)
            old_id=subject.track_id
            fresh=tracker.update(Image.new('RGB',frame.size,220),.5)[0]
            self.assertNotEqual(fresh.track_id,old_id)
            self.assertFalse(np.asarray(subject_binary(fresh))[64,134])
            self.assertEqual(tracker.scene_cuts,1)
        for kw in ({'mask_stability':float('nan')},{'mask_min_region':.21}):
            with self.assertRaises(ValueError): SemanticTracker(Detector(),**kw)

    def test_led_all_styles_default_compatibility_and_idle_controls(self):
        signal=np.linspace(0,1,256)
        for actual, expected in zip(waveform_masks(60,180,signal,.4,style='digital-circuit'),vocoder_masks(60,180,signal)):
            np.testing.assert_array_equal(actual,expected)
        plain=waveform_masks(60,180,signal,.4,style='digital-circuit',display='plain')
        self.assertIsNone(plain[1])
        field=np.full((180,320),100,np.uint8)
        for style in WAVE_STYLES:
            base=dict(wave_style=style,glow=0,grain=0,scanlines=False)
            r=Renderer(320,180,**base,wave_display='led')
            led=r.render_field(field,0,wave=(-signal,signal))
            direct=Renderer(320,180,**base,wave_display='plain').render_field(field,0,wave=(-signal,signal))
            self.assertFalse(np.array_equal(led,direct),style)
            if style=='trace':
                # The device doesn't change the other readouts' ink/compositing.
                np.testing.assert_array_equal(np.asarray(led)[:,80:],np.asarray(direct)[:,80:])
            # Backlight remains present in silence; zero element opacity hides it too.
            images=[Renderer(320,180,**base,wave_display='led',wave_backlight=b).render_field(field,0,wave=(signal*0,signal*0)) for b in (0,.5)]
            self.assertFalse(np.array_equal(*images),style)
            images=[Renderer(320,180,**base,wave_display='led',wave_backlight=b,hud_opacity_elements='waveform=0').render_field(field,0,wave=(-signal,signal)) for b in (0,.5)]
            np.testing.assert_array_equal(*images)

    def test_rotation_independent_clocks_stills_determinism_and_topology(self):
        size=(320,180)
        for projection in ('flat','sphere'):
            options=dict(geo_grid=True,geo_grid_projection=projection,geo_grid_details=True,geo_grid_breaks=.7,geo_grid_speed=0,glow=0)
            fixed=Renderer(*size,**options)
            moving=Renderer(*size,**options,geo_grid_rotation=.6)
            def draw(r,t,static=False):
                image=Image.new('RGB',size); r.geometry.draw_grid(r,image,t,static); return np.asarray(image)
            np.testing.assert_array_equal(draw(fixed,1),draw(moving,1,True))
            a=draw(moving,1); edges=len(moving.geometry.geometry[2]); b=draw(moving,2)
            self.assertFalse(np.array_equal(a,b))
            self.assertEqual(edges,len(moving.geometry.geometry[2]))
            np.testing.assert_array_equal(a,draw(moving,1))
            for t in (0,75,150,300,600):
                image=draw(moving,t)
                self.assertGreater(np.count_nonzero(image),100)
                if projection=='flat':
                    for tile in (image[:30,:30],image[:30,-30:],image[-30:,:30],image[-30:,-30:]):
                        self.assertTrue(tile.any())

    def test_shine_default_and_band_contrast(self):
        mask=Image.new('L',(64,180),255)
        base=holographic_ink(mask,(110,140,255),.4,42)
        np.testing.assert_array_equal(base,holographic_ink(mask,(110,140,255),.4,42,shine=.55))
        contrast=[]
        for shine in (0,.3,.6,1):
            rgb=np.asarray(holographic_ink(mask,(110,140,255),.4,42,shine=shine))[:,:,:3]
            contrast.append(rgb[:,:,0].std())
        self.assertEqual(contrast,sorted(contrast))

    def test_presets_reports_and_runtime_exclusion(self):
        for name in ('focus','relic'):
            r=Renderer(320,180,look_preset=name)
            report=extra_report(r,None)
            self.assertFalse(report['target_weak_spots'])
            self.assertEqual(report['outline_width'],4.8)
            self.assertEqual(report['outline_shine'],.65)
            self.assertEqual(report['geo_grid_rotation'],1.8)
            for role in ('target','readout','waveform-glyphs','callouts','subject-labels','target-label'):
                self.assertEqual(r.hud_colors[role],(136,51,255))
            for role in ('geo-grid','waveform'):
                self.assertEqual(r.hud_colors[role],(80,124,255))
            self.assertEqual(r.hud_colors['subject-outline'],(96,153,255))
            for role in ('subject-code','target-motif'):
                self.assertEqual(r.hud_colors[role],(247,69,255) if name=='relic' else (136,51,255))
            self.assertEqual(r.signal.subject_code,name=='relic')
            if name=='relic':
                self.assertEqual(r.signal.code_style,'light')
        self.assertNotIn('mask_stability',VISUAL_OPTIONS)
        self.assertNotIn('mask_min_region',VISUAL_OPTIONS)
        self.assertIn('wave_display',NULLABLE)
        settings={'wave_display':None,'wave_backlight':.5,'outline_shine':.7,'geo_grid_rotation':-.6}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'preset.json'; save_preset(path,'test',settings)
            self.assertEqual(validate_settings(load_preset(path)['settings'],parser()),settings)
        for flag,value in (('--mask-stability','1.1'),('--mask-min-region','-.1'),('--wave-backlight','nan')):
            with patch('sys.stderr',new_callable=io.StringIO), patch('yautja.cli.convert') as convert, self.assertRaises(SystemExit):
                main(['in.png','out.png',flag,value])
            convert.assert_not_called()
        for flag,value in (('--outline-shine','2'),('--geo-grid-rotation','11')):
            with patch('sys.stderr',new_callable=io.StringIO), patch('yautja.cli.convert') as convert:
                self.assertEqual(main(['in.png','out.png',flag,value]),1)
            convert.assert_not_called()

    def test_behind_code_keeps_streams_inside_figure_width(self):
        size = (480, 360)
        r = Renderer(*size, subject_code=True, code_layer='behind', code_density=1.65,
                     glow=0, neon=False)
        mask = np.zeros((360, 480), np.float32)
        mask[140:320, 100:220] = 1
        subject = Subject(mask, 'person', .95, track_id=1)
        frame = Image.new('RGB', size)
        r.signal.draw(r, frame, [subject], 1.2, 1)
        ink = np.asarray(frame).max(axis=2)
        self.assertTrue(ink[:140, 100:220].any())
        self.assertFalse(ink[:, :100].any())
        self.assertFalse(ink[:, 220:].any())
        self.assertFalse(ink[140:320, 100:220].any())  # final subject occlusion

        # Packing the former wider span into the figure preserves its glyph
        # identities and count, so narrowing does not thin the waterfall.
        calls = []
        def glyph(identity, cell):
            calls.append((identity, cell))
            return Image.new('L', (cell, cell), 255)
        r.signal.streams(size, (85.6, 77, 234.4, 320), (160, 230), 1.2, 42, 1, glyph)
        original = calls[:]
        calls.clear()
        r.signal.streams(size, (100, 77, 220, 320), (160, 230), 1.2, 42, 1, glyph, fit_columns=True)
        self.assertGreater(len(calls), 50)
        self.assertEqual(calls, original)

    def test_attached_motifs_follow_selection_and_search(self):
        r=Renderer(320,180,look_preset='relic',glow=0,neon=False)
        def draw(subjects,t):
            image=Image.new('RGB',(320,180))
            image=r.draw_targets(image,t,subjects,None,((0,0,0),)*2,shot=1)
            return np.asarray(image)
        left=draw([self.subject(55)],0)
        right=draw([self.subject(205)],.1)
        lx=np.nonzero(left.max(axis=2))[1].mean(); rx=np.nonzero(right.max(axis=2))[1].mean()
        self.assertGreater(rx-lx,100)  # ornaments follow the subject, not gliding aim
        self.assertFalse(draw([], .2).any())
        explicit=Renderer(320,180,target_motif='triangles',target_motion='persistent',glow=0)
        image=explicit.draw_targets(Image.new('RGB',(320,180)),0,[],[{'id':'one','bbox':(.3,.2,.6,.8)}],((0,0,0),)*2,static=True)
        self.assertTrue(np.asarray(image).any())


if __name__ == '__main__': unittest.main()
