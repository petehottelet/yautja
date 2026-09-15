"""Torso-aligned light streams, independent of arms, props and glyph artwork."""
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw

from yautja.cli import main, parser, extra_report
from yautja.masks import subject_binary
from yautja.presets import load_preset, validate_settings
from yautja.render import Renderer
from yautja.semantic import Subject
from yautja.signal import SignalStyle, body_core


class LightStreamTests(unittest.TestCase):
    size = (360, 420)

    def subject(self, props=False, pose=True):
        mask = Image.new('L', self.size)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((166, 30, 204, 82), fill=255)
        draw.rectangle((150, 80, 220, 400), fill=255)
        if props:
            draw.rectangle((50, 145, 165, 168), fill=255)
            draw.rectangle((10, 210, 110, 250), fill=255)
        joints = np.zeros((17, 3), np.float32)
        for index, xy in ((5,(156,85)), (6,(216,95)), (11,(165,240)), (12,(215,240)),
                          (9,(30,160)), (10,(95,235))):
            joints[index] = (*xy, .95)
        return Subject(np.asarray(mask, np.float32)/255, 'person', .95, track_id=1,
                       keypoints=joints if pose else None)

    def test_pose_core_ignores_extended_arm_and_map_and_scales_with_frame(self):
        bare, props = self.subject(), self.subject(True)
        core = body_core(bare, subject_binary(bare))
        np.testing.assert_allclose(core, body_core(props, subject_binary(props)))
        self.assertAlmostEqual(core[0], 188)
        self.assertLess(core[1], 75)
        small = subject_binary(props, (180,210))
        np.testing.assert_allclose(body_core(props, small), core/2)

    def test_mask_fallback_finds_body_instead_of_bbox_center(self):
        bare, props = self.subject(pose=False), self.subject(True, pose=False)
        first = body_core(bare, subject_binary(bare))
        second = body_core(props, subject_binary(props))
        self.assertLess(abs(first[0]-second[0]), 3)
        self.assertGreater(second[0], 175)
        self.assertLess(second[1], 85)
        props.keypoints = np.full((17,3), np.nan)
        np.testing.assert_array_equal(second, body_core(props, subject_binary(props)))

    def test_light_moves_up_continuously_without_glyph_cells(self):
        style = SignalStyle(code_style='light', code_density=.1)
        bounds = (110,0,210,540)
        a = np.asarray(style.light_streams((320,540), bounds, 0, 42, 1), float).sum(axis=1)
        b = np.asarray(style.light_streams((320,540), bounds, .2, 42, 1), float).sum(axis=1)
        shifts = range(-24,25)
        shift = min(shifts, key=lambda dy: np.mean((a[150:400]-b[150+dy:400+dy])**2))
        self.assertLess(shift, -2)
        np.testing.assert_array_equal(style.light_streams((320,540), bounds, .2, 42, 1),
                                      style.light_streams((320,540), bounds, .2, 42, 1))
        frozen = SignalStyle(code_style='light', code_speed=0)
        np.testing.assert_array_equal(frozen.light_streams((320,540), bounds, 0, 42, 1),
                                      frozen.light_streams((320,540), bounds, 10, 42, 1))
        self.assertIsNone(SignalStyle(code_style='light', code_density=0).light_streams((320,540), bounds, 0, 42, 1).getbbox())

    def test_light_uses_body_core_and_occludes_all_foreground_after_glow(self):
        subject = self.subject(True)
        other_mask = np.zeros(self.size[::-1], np.float32)
        other_mask[0:25,165:200] = 1
        other = Subject(other_mask,'person',.9,track_id=2)
        union = (subject.mask > .5) | (other.mask > .5)
        for neon in (False, True):
            renderer = Renderer(*self.size, subject_code=True, code_style='light', code_layer='behind',
                                neon=neon, neon_intensity=1.5, hud_blur_elements='subject-code=3')
            image = Image.new('RGB', self.size, (35,45,55))
            with patch.object(renderer, 'code_mask', side_effect=AssertionError('Light must not draw glyphs')):
                renderer.signal.draw(renderer, image, [subject,other], .5, 1)
            pixels = np.asarray(image)
            np.testing.assert_array_equal(pixels[union], np.tile([35,45,55], (union.sum(),1)))
            self.assertTrue(np.any(pixels[~union] != [35,45,55]))
            np.testing.assert_array_equal(pixels[:, :100], np.broadcast_to([35,45,55], pixels[:, :100].shape))

    def test_static_frames_and_anchor_lifecycle(self):
        subject = self.subject(True)
        renderer = Renderer(*self.size, subject_code=True, code_style='light', code_layer='behind', glow=0)
        def draw(time, subjects, shot=1, static=False):
            image = Image.new('RGB',self.size)
            renderer.signal.draw(renderer,image,subjects,time,shot,static)
            return image
        np.testing.assert_array_equal(draw(0,[subject],static=True),draw(7,[subject],static=True))
        self.assertIn(1,renderer.signal.light_anchors)
        self.assertIsNone(draw(7.1,[]).getbbox())
        self.assertEqual(renderer.signal.light_anchors,{})
        draw(8,[subject],2)
        np.testing.assert_allclose(renderer.signal.light_anchors[1],body_core(subject,subject_binary(subject)))

    def test_preset_cli_report_and_saved_override(self):
        self.assertEqual(extra_report(Renderer(320,180,look_preset='relic'),None)['code_style'],'light')
        self.assertEqual(Renderer(320,180,look_preset='netrunner').signal.code_style,'glyphs')
        self.assertFalse(Renderer(320,180,look_preset='focus').signal.subject_code)
        for flags in (['--stylepreset','relic','--code-style','glyphs'], ['--code-style','glyphs','--stylepreset','relic']):
            self.assertEqual(parser().parse_args(flags).code_style,'glyphs')
        with tempfile.TemporaryDirectory() as folder, patch('sys.stdout',new_callable=io.StringIO):
            path = Path(folder)/'light.json'
            self.assertEqual(main(['--stylepreset','relic','--save-preset',str(path)]),0)
            settings = validate_settings(load_preset(path)['settings'],parser())
            self.assertEqual(settings['code_style'],'light')
        with self.assertRaisesRegex(ValueError,'--code-style'):
            SignalStyle(code_style='invalid')


if __name__ == '__main__': unittest.main()
