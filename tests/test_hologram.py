"""Holographic details stay seeded, current-mask bound and independently styled."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from yautja.cli import main, parser, extra_report
from yautja.geometry import GeometryStyle
from yautja.hologram import weak_spot_ink
from yautja.presets import load_preset, validate_settings
from yautja.render import Renderer
from yautja.semantic import Subject
from yautja.signal import SignalStyle


class HologramTests(unittest.TestCase):
    size = (640, 360)

    def subjects(self):
        mask = np.zeros((360, 640), np.float32)
        mask[45:320, 70:210] = 1
        mask[145:170, 120:150] = 0
        return [Subject(mask, 'object', .95, track_id=1),
                Subject(np.roll(mask, 320, axis=1), 'object', .95, track_id=2)]

    def test_grid_satellites_move_out_and_back_with_seven_sided_node_rings(self):
        style = GeometryStyle(geo_grid_projection='sphere', geo_grid_details=True)
        first = list(style.grid_accents(self.size, 42, 0))
        self.assertTrue(any(len(item['ring']) == 7 for item in first))
        self.assertTrue(any(not item['ring'] for item in first))
        node = next(item for item in first if item['dots'])['node']
        _, _, _, phase, period, _ = next(item for item in style.accents if item[0] == node)
        times = ((-phase) / (2*np.pi)*period, (np.pi-phase)/(2*np.pi)*period,
                 (2*np.pi-phase)/(2*np.pi)*period)
        dots = [next(item for item in style.grid_accents(self.size, 42, time) if item['node'] == node)['dots']
                for time in times]
        center = style.lattice(self.size, 42)[0][node]
        self.assertGreater(np.linalg.norm(np.array(dots[1][2])-center), np.linalg.norm(np.array(dots[0][2])-center)*2)
        np.testing.assert_allclose(dots[0], dots[2], atol=1e-8)
        frozen = list(style.grid_accents(self.size, 42, 8, static=True))
        np.testing.assert_allclose(first[0]['dots'], frozen[0]['dots'])
        style.geo_grid_speed = 0
        np.testing.assert_allclose(first[0]['dots'], list(style.grid_accents(self.size, 42, 8))[0]['dots'])

    def test_grid_details_are_repeatable_and_obey_center_fade_in_all_aspects(self):
        for size in ((480,270),(270,480),(320,320)):
            images=[]
            for details in (False,True,True):
                r=Renderer(*size,geo_grid=True,geo_grid_details=details,geo_grid_projection='sphere',
                           geo_grid_center_fade=1,glow=0)
                image=Image.new('RGB',size)
                r.geometry.draw_grid(r,image,1.3)
                images.append(np.asarray(image))
            np.testing.assert_array_equal(images[1],images[2])
            self.assertGreater(np.count_nonzero(images[0]!=images[1]),100)
            cx,cy=size[0]//2,size[1]//2
            self.assertEqual(images[1][cy-4:cy+4,cx-4:cx+4].max(),0)

    def test_holographic_edges_are_thicker_partial_and_use_current_silhouette(self):
        size=(960,540)
        mask=Image.new('L',size)
        ImageDraw.Draw(mask).ellipse((300,50,640,490),fill=255)
        subjects=[Subject(np.asarray(mask,np.float32)/255,'object',.95,track_id=1)]
        counts=[]
        for width in (3,8):
            r=Renderer(*size,subject_outline=True,outline_style='holographic',outline_width=width,
                       hud_colors='subject-outline=#A6B4FF',hud_theme='custom',glow=0)
            image=Image.new('RGB',size)
            r.signal.draw(r,image,subjects,1,1)
            pixels=np.asarray(image)
            counts.append(np.count_nonzero(pixels.max(axis=2)>60))
        self.assertGreater(counts[1],counts[0]*1.8)
        visible=pixels.max(axis=2)>0
        self.assertFalse(np.any(visible & (np.asarray(mask)==0)))
        full=np.asarray(ImageChops.subtract(mask,mask.filter(ImageFilter.MinFilter(9))))>0
        self.assertLess(visible.sum(),full.sum()*.75)
        bright=pixels[pixels.max(axis=2)>180]
        self.assertTrue(np.all(bright[:,2]>=bright[:,0]))
        self.assertGreater(np.ptp(bright[:,0].astype(float)/bright[:,2]),.05)
        moved=np.roll(subjects[0].mask,120,axis=1)
        image=Image.new('RGB',size)
        r.signal.draw(r,image,[Subject(moved,'object',.95,track_id=1)],1.04,1)
        self.assertFalse(np.any((np.asarray(image).max(axis=2)>0)&(moved==0)))

    def test_weak_patches_are_seeded_textured_animated_and_clipped_to_arbitrary_mask(self):
        mask=Image.new('L',(180,300))
        d=ImageDraw.Draw(mask)
        d.polygon([(20,0),(160,0),(160,280),(90,299),(0,230),(30,160)],fill=255)
        d.ellipse((60,70,120,220),fill=0)
        a=weak_spot_ink(mask,(255,211,77),0,42)
        self.assertEqual(a.tobytes(),weak_spot_ink(mask,(255,211,77),0,42).tobytes())
        self.assertNotEqual(a.tobytes(),weak_spot_ink(mask,(255,211,77),1,42).tobytes())
        self.assertNotEqual(a.tobytes(),weak_spot_ink(mask,(255,211,77),0,43).tobytes())
        alpha=np.asarray(a)[...,3]
        self.assertFalse(np.any(alpha[np.asarray(mask)==0]))
        self.assertGreater(np.count_nonzero(alpha),200)
        self.assertLess(np.count_nonzero(alpha),np.count_nonzero(mask)*.4)
        self.assertGreater(len(np.unique(alpha[alpha>0])),50)

    def test_weak_patches_follow_one_selected_subject_and_clear_without_stale_ink(self):
        subjects=self.subjects()
        r=Renderer(*self.size,target_mode='cycle',target_weak_spots=True,glow=0)
        for time,expected in ((0,1),(3.2,2)):
            r.geometry.prepare_targets(subjects,None,time,1,self.size)
            image=Image.new('RGB',self.size)
            r.geometry.draw_weak_spots(r,image,subjects,time,1)
            selected=next(s for s in subjects if s.track_id==expected)
            self.assertGreater(np.asarray(image).max(),100)
            self.assertFalse(np.any(np.asarray(image)[selected.mask==0]))
        for targets in ([],[{'id':'catalog','bbox':(.11,.125,.328,.89)}]):
            r.geometry.prepare_targets(subjects,targets,4,2,self.size,True)
            image=Image.new('RGB',self.size)
            r.geometry.draw_weak_spots(r,image,subjects,4,2,True)
            self.assertEqual(bool(image.getbbox()),bool(targets))
            self.assertFalse(np.any(np.asarray(image)[subjects[0].mask==0]))
        r.geometry.prepare_targets([],None,5,3,self.size)
        image=Image.new('RGB',self.size)
        r.geometry.draw_weak_spots(r,image,subjects,5,3)
        self.assertIsNone(image.getbbox())

    def test_weak_spot_visibility_and_static_controls_include_glow(self):
        frame=Image.new('RGB',self.size,(40,50,60))
        subjects=self.subjects()
        for options in ({'neon':True},{'glow':0},{'hud_blur_elements':'target-weak-spots=8'}):
            plain=Renderer(*self.size,scene_mode='source',hud=False).render_source(frame,0,None,subjects)
            for hidden in ({'hud':False},{'hud_opacity':0}):
                r=Renderer(*self.size,scene_mode='source',target_mode='cycle',target_weak_spots=True,**options,**hidden)
                image=r.render_source(frame,0,None,subjects)
                self.assertEqual(plain.tobytes(),image.tobytes())
        r=Renderer(*self.size,target_weak_spots=True,glow=0)
        images=[]
        for time in (0,8):
            r.geometry.prepare_targets(subjects,[{'track_id':1,'bbox':(.11,.125,.328,.89),'id':'one'}],time,1,self.size,True)
            image=Image.new('RGB',self.size)
            r.geometry.draw_weak_spots(r,image,subjects,time,1,True)
            images.append(image.tobytes())
        self.assertEqual(*images)
        off=Renderer(*self.size,look_preset='focus',hud=False)
        self.assertFalse(extra_report(off,None)['target_weak_spots'])

    def test_new_controls_round_trip_and_reject_incompatible_rendering(self):
        for tokens in (['--stylepreset','focus','--no-geo-grid-details','--no-target-weak-spots','--outline-width','6'],
                       ['--no-geo-grid-details','--no-target-weak-spots','--outline-width','6','--stylepreset','focus']):
            args=parser().parse_args(tokens)
            self.assertEqual((args.geo_grid_details,args.target_weak_spots,args.outline_width),(False,False,6))
            self.assertFalse(args.subject_code)
        for options in ({'outline_width':0},{'outline_width':float('nan')},{'outline_width':21}):
            with self.assertRaises(ValueError):
                SignalStyle(**options)
        with tempfile.TemporaryDirectory() as directory:
            for style in ('focus','relic','yautja'):
                path=Path(directory)/(style+'.json')
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(['--stylepreset',style,'--save-preset',str(path)]),0)
                settings=validate_settings(load_preset(path)['settings'],parser())
                self.assertIn('outline_width',settings)
                self.assertIn('target_weak_spots',settings)
            with contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit):
                main(['missing.png','out.png','--target-weak-spots'])
            self.assertIn('weak-spot',err.getvalue())


if __name__=='__main__':
    unittest.main()
