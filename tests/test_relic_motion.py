import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from yautja.cli import main, parser
from yautja.geometry import GeometryStyle, broken_path
from yautja.looks import LOOK_PRESETS
from yautja.presets import load_preset, validate_settings
from yautja.render import Renderer
from yautja.semantic import Subject
from yautja.signal import SignalStyle


class RelicMotionTests(unittest.TestCase):
    def test_grid_center_fades_in_all_aspects_without_dimming_outer_edges(self):
        for size in ((480,270),(270,480),(640,180)):
            images = []
            for fade in (0, 1):
                r = Renderer(*size, look_preset='focus', geo_grid_center_fade=fade,
                             neon=False, glow=0, hud_opacity=1, hud_opacity_elements=None)
                frame = Image.new('RGB', size)
                r.geometry.draw_grid(r, frame, .5)
                images.append(np.asarray(frame).max(axis=2).astype(float))
            y,x = np.mgrid[:size[1],:size[0]]
            radius = np.hypot((x-size[0]/2)/(size[0]/2), (y-size[1]/2)/(size[1]/2))
            inner, outer = radius < .25, radius > 1.1
            self.assertGreater(images[0][inner].sum(), 0)
            self.assertLess(images[1][inner].sum(), images[0][inner].sum()*.09)
            np.testing.assert_array_equal(images[0][outer], images[1][outer])

    def test_broken_grid_is_repeatable_and_thicker_strokes_remain_visible(self):
        size = (480,270)
        def render(width, gaps, seed=42):
            r = Renderer(*size, geo_grid=True, geo_grid_width=width, geo_grid_breaks=gaps,
                         hud_theme='custom', hud_colors='geo-grid=#fff', glow=0, seed=seed)
            frame = Image.new('RGB',size)
            r.geometry.draw_grid(r,frame,0)
            return np.asarray(frame).max(axis=2)
        thin, thick, broken = render(1.3,0), render(2.2,0), render(2.2,.7)
        self.assertGreater(thick.sum(),thin.sum()*1.3)
        self.assertLess(broken.sum(),thick.sum()*.97)
        np.testing.assert_array_equal(broken,render(2.2,.7))
        self.assertFalse(np.array_equal(broken,render(2.2,.7,43)))
        path = [(0,0),(40,0),(80,15),(120,20)]
        pieces = broken_path(path,42,.7)
        self.assertGreater(len(pieces),1)
        self.assertTrue(all(np.isfinite(piece).all() for piece in pieces))
        self.assertTrue(any(np.linalg.norm(a[-1]-b[0])>1 for a,b in zip(pieces,pieces[1:])))

    def test_triangles_rise_contract_spin_fade_and_freeze(self):
        style = GeometryStyle(target_motif='triangles', target_motif_count=1, target_motif_breaks=.7)
        initial = next(style.motif_particles(42,'one',0))
        period, offset = initial['lifetime'], initial['phase']
        def at(phase):
            return next(style.motif_particles(42,'one',(phase-offset+1)*period))
        self.assertAlmostEqual(at(0)['x'],0)
        self.assertAlmostEqual(at(0)['y'],0)
        early, middle, late, gone = [at(p) for p in (.2,.5,.9,.99999)]
        self.assertLess(middle['y'], early['y'])
        self.assertAlmostEqual(early['radius'],middle['radius'])
        self.assertLess(late['radius'],middle['radius']*.5)
        self.assertGreater(abs(late['rotation']-middle['rotation']),2)
        self.assertLess(gone['radius'],1e-6)
        self.assertLess(gone['alpha'],1e-6)
        self.assertEqual(list(style.motif_particles(42,'one',0)),list(style.motif_particles(42,'one',0)))
        self.assertEqual(list(style.motif_particles(42,'one',0,True)),list(style.motif_particles(42,'one',15,True)))
        frozen = GeometryStyle(target_motif_speed=0)
        self.assertEqual(list(frozen.motif_particles(42,'one',0)),list(frozen.motif_particles(42,'one',15)))

    def test_attached_triangles_emerge_at_mass_center_then_rise(self):
        size = (480, 360)
        mask = np.zeros((360, 480), np.float32)
        mask[55:320, 200:270] = 1
        mask[130:145, 100:200] = 1  # Extended arm makes the bounding-box center wrong.
        subject = Subject(mask, 'person', .95, track_id=1)
        yy, xx = np.nonzero(mask)
        cx, cy = xx.mean(), yy.mean()
        height = yy.max() - yy.min() + 1
        renderer = Renderer(*size, look_preset='relic', target_motif_count=1,
                            target_motif_breaks=0, neon=False, glow=0)
        initial = next(renderer.geometry.motif_particles(renderer.seed, 'subject-1', 0))
        centers = []
        for phase in (.08, .55):
            time = (phase - initial['phase'] + 1) * initial['lifetime']
            frame = renderer.draw_targets(Image.new('RGB', size), time, [subject],
                                          None, ((0, 0, 0),) * 2, shot=1)
            ink = np.asarray(frame).max(axis=2)
            iy, ix = np.nonzero(ink > 8)
            self.assertGreater(len(ix), 10)
            centers.append((ix.mean(), iy.mean()))
        self.assertLess(abs(centers[0][0] - cx), 5)
        self.assertLess(abs(centers[0][1] - cy), height * .07)
        self.assertGreater(centers[0][1] - centers[1][1], height * .16)

    def test_relic_has_three_times_the_streams_at_the_same_glyph_size(self):
        size, counts, glyph_sizes = (1920,1080), [], []
        for density in (.55,1.65):
            calls = []
            def glyph(index, size):
                calls.append(size)
                return Image.new('L',(size,size),255)
            style = SignalStyle(code_size=26,code_speed=.8,code_density=density)
            for seed in range(42,48):
                for time in (0,1):
                    style.streams(size,(0,0,*size),(0,0),time,seed,1,glyph)
            counts.append(len(calls)); glyph_sizes.append(set(calls))
        self.assertTrue(2.8 < counts[1]/counts[0] < 3.2, counts)
        self.assertEqual(glyph_sizes[0],glyph_sizes[1])
        self.assertEqual(LOOK_PRESETS['relic']['code_density'],1.65)
        self.assertFalse(LOOK_PRESETS['focus']['subject_code'])
        self.assertEqual(LOOK_PRESETS['netrunner']['code_density'],.95)

    def test_dense_code_remains_occluded_after_neon_and_blur(self):
        size = (320,180)
        mask = np.zeros((180,320),np.float32)
        mask[45:170,135:190] = 1
        other = np.roll(mask,40,axis=1)
        subjects = [Subject(mask,'person',.95,track_id=1),Subject(other,'person',.95,track_id=2)]
        r = Renderer(*size,look_preset='relic',subject_outline=False,hud_blur_elements='subject-code=8')
        frame = Image.new('RGB',size,(30,40,50))
        before = np.asarray(frame).copy()
        r.signal.draw(r,frame,subjects,1,1)
        union = (mask+other)>0
        np.testing.assert_array_equal(np.asarray(frame)[union],before[union])
        self.assertGreater(np.count_nonzero(np.asarray(frame)[~union]!=before[~union]),0)

    def test_controls_round_trip_and_override_presets(self):
        flags = ['--geo-grid-center-fade','.8','--geo-grid-width','2.5','--geo-grid-breaks','.4',
                 '--target-motif-speed','1.5','--target-motif-breaks','.8','--code-density','2']
        for tokens in (['--stylepreset','relic',*flags],[*flags,'--stylepreset','relic']):
            args = parser().parse_args(tokens)
            self.assertEqual((args.geo_grid_center_fade,args.code_density,args.target_motif_speed),(.8,2,1.5))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'relic.json'
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['--stylepreset','relic',*flags,'--save-preset',str(path)]),0)
            data = load_preset(path)
            settings = validate_settings(data['settings'],parser())
            r = Renderer(320,180,**{k:v for k,v in settings.items() if k not in ('waveform','wave_window','wave_gain')})
            self.assertEqual(r.geometry.geo_grid_width,2.5)
            self.assertEqual(r.signal.code_density,2)
        for options in ({'geo_grid_center_fade':1.1},{'geo_grid_width':0},{'geo_grid_breaks':float('nan')},
                        {'target_motif_speed':-1},{'target_motif_breaks':1.1}):
            with self.assertRaises(ValueError):
                GeometryStyle(**options)


if __name__ == '__main__':
    unittest.main()
