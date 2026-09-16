"""Preset discovery, portable saves, layering, and real conversion round trips."""
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from yautja.cli import main, parser
from yautja.looks import LOOK_PRESETS, COMPLETE_PRESETS
from yautja.presets import VISUAL_OPTIONS, load_preset
from yautja.render import PALETTES, Renderer


class PresetTests(unittest.TestCase):
    def invoke(self, flags):
        with patch('sys.stdout', new_callable=io.StringIO) as stdout:
            self.assertEqual(main([str(flag) for flag in flags]), 0)
        return json.loads(stdout.getvalue())

    def test_catalog_covers_every_palette_and_hottropic(self):
        with patch('yautja.cli.semantic_tracker') as models, patch('yautja.cli.convert') as convert:
            report = self.invoke(['--list-presets'])
            models.assert_not_called()
            convert.assert_not_called()
        presets = {entry['id']: entry for entry in report['presets']}
        self.assertEqual(report['presets'][-1]['id'], 'fremont')
        self.assertEqual(presets['netrunner']['name'], 'Netrunner')
        self.assertEqual(presets['netrunner']['aliases'], ['ghost-signal'])
        self.assertEqual(set(presets) - { 'netrunner', 'fremont', 'focus', 'relic', 'murphy'}, set(PALETTES))
        for name in PALETTES:
            args = parser().parse_args(['--stylepreset', name])
            self.assertEqual((args.thermal, args.palette, args.preset_kind), ('cinematic', name, 'look' if name in COMPLETE_PRESETS else 'palette'))
        self.assertEqual(presets['yautja']['name'], 'Yautja')
        self.assertEqual(parser().parse_args(['--stylepreset', 'HotTropic']).look_preset, 'yautja')
        self.assertEqual(presets['yautja']['aliases'], ['hottropic', 'hot-tropic'])

    def test_ripley_colors_round_trip_and_explicit_overrides(self):
        args = parser().parse_args(['--stylepreset', 'Ripley'])
        self.assertEqual((args.look_preset, args.preset_name, args.preset_kind), ('ripley', 'Ripley', 'look'))
        renderer = Renderer(320, 180, look_preset='ripley')
        self.assertEqual(tuple(renderer.palette[0]), (13, 14, 9))
        self.assertEqual(tuple(renderer.palette[-1]), (238, 176, 61))
        self.assertEqual(renderer.hud_colors['waveform'], (238, 176, 61))
        self.assertEqual(renderer.hud_colors['readout'], (211, 93, 12))
        self.assertTrue(all(r >= g >= b for r, g, b in renderer.hud_colors.values()))
        self.assertNotEqual(renderer.hud_colors['waveform'], renderer.hud_colors['readout'])
        for flags in (['--palette', 'white-hot', '--hud-theme', 'palette'], ['--no-hud', '--glow', '0']):
            a = parser().parse_args(['--stylepreset', 'ripley', *flags])
            b = parser().parse_args([*flags, '--stylepreset', 'ripley'])
            self.assertEqual(vars(a), vars(b))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, preset = root / 'source.png', root / 'ripley.json'
            Image.fromarray(np.tile(np.arange(256, dtype=np.uint8), (180, 1))).convert('RGB').save(source)
            self.invoke(['--stylepreset', 'ripley', '--save-preset', preset])
            saved = load_preset(preset)['settings']
            self.assertEqual((saved['palette'], saved['hud_colors']), ('ripley', args.hud_colors))
            self.invoke([source, root / 'direct.png', '--stylepreset', 'ripley', '--thermal', 'classic'])
            self.invoke([source, root / 'loaded.png', '--preset-file', preset, '--thermal', 'classic'])
            with Image.open(root / 'direct.png') as direct, Image.open(root / 'loaded.png') as loaded:
                np.testing.assert_array_equal(direct, loaded)

    def test_removed_reference_name_is_rejected_by_cli_api_and_preset_base(self):
        removed = 'thermal-spectrum-reference-v1'
        with patch('sys.stderr', new_callable=io.StringIO), self.assertRaises(SystemExit) as result:
            parser().parse_args(['--stylepreset', removed])
        self.assertEqual(result.exception.code, 2)
        with self.assertRaisesRegex(ValueError, 'Unknown look preset'):
            Renderer(320, 180, look_preset=removed)
        with tempfile.TemporaryDirectory() as folder:
            preset = Path(folder) / 'old.json'
            preset.write_text(json.dumps({'schema_version': 1, 'name': 'Old base', 'base': removed, 'settings': {}}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Unknown look preset'):
                load_preset(preset)

    def test_stylepreset_replaces_old_flag_and_keeps_source_exclusivity(self):
        args = parser().parse_args(['--stylepreset=white-hot'])
        self.assertEqual((args.look_preset, args.palette, args.preset_name), ('white-hot', 'white-hot', 'White Hot'))
        for flags in (['--look-preset', 'white-hot'],
                      ['--stylepreset', 'white-hot', '--preset-file', 'custom.json']):
            with self.subTest(flags=flags), patch('sys.stderr', new_callable=io.StringIO), \
                    patch('yautja.cli.convert') as convert, self.assertRaises(SystemExit) as result:
                main(['input.png', 'output.png', *flags])
            self.assertEqual(result.exception.code, 2)
            convert.assert_not_called()

    def test_save_load_matches_images_including_custom_colors_and_effects(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, preset = root / 'source.png', root / 'mine.json'
            Image.fromarray(np.tile(np.arange(256, dtype=np.uint8), (180, 1))).convert('RGB').save(source)
            flags = ['--thermal', 'classic', '--palette', 'custom', '--palette-colors', '#000,#137,#fa6',
                     '--hud-theme', 'custom', '--hud-colors', 'waveform=#0f0,timecode=#fff',
                     '--timecode', '--thermal-levels', '8', '--thermal-band-softness', '.6',
                     '--sensor-texture', '--grain', '.02', '--hud-blur', '2', '--hud-opacity', '.7',
                     '--crt-grid', '--crt-crosshatch', '--crt-strength', '.3',
                     '--wave-style', 'rorschach', '--wave-height', '1', '--target-shape', 'round-dot', '--seed', '78']
            with patch('yautja.cli.semantic_tracker') as models, patch('yautja.cli.convert') as convert:
                saved = self.invoke([*flags, '--save-preset', preset, '--preset-name', 'My Glow'])
                models.assert_not_called()
                convert.assert_not_called()
            self.assertEqual(saved['name'], 'My Glow')
            self.assertEqual(set(saved['settings']), set(VISUAL_OPTIONS))
            self.assertFalse({'input', 'output', 'target', 'figures', 'device', 'preset', 'overwrite'} & set(saved['settings']))
            self.invoke([source, root / 'direct.png', *flags])
            report = self.invoke([source, root / 'saved.png', '--preset-file', preset])
            self.assertEqual((report['preset_name'], report['preset_kind']), ('My Glow', 'custom'))
            self.assertEqual(report['target_shape'], 'round-dot')
            self.assertTrue(report['crt_grid'] and report['crt_crosshatch'])
            args = parser().parse_args(['--preset-file', str(preset), '--no-crt-grid', '--no-crt-crosshatch'])
            self.assertFalse(args.crt_grid or args.crt_crosshatch)
            with Image.open(root / 'direct.png') as a, Image.open(root / 'saved.png') as b:
                np.testing.assert_array_equal(a, b)
            original = preset.read_bytes()
            with patch('sys.stderr', new_callable=io.StringIO):
                self.assertEqual(main(['--save-preset', str(preset)]), 1)
            self.assertEqual(preset.read_bytes(), original)
            self.invoke(['--save-preset', preset, '--overwrite', '--palette', 'white-hot'])
            self.assertEqual(load_preset(preset)['settings']['palette'], 'white-hot')

    def test_inheritance_and_explicit_overrides_are_order_independent(self):
        with tempfile.TemporaryDirectory() as folder:
            preset = Path(folder) / 'custom.json'
            preset.write_text(json.dumps({'schema_version': 1, 'name': 'Derived', 'base': 'hottropic',
                                         'settings': {'hud': True, 'heat_glow': .6}}))
            for flags in (['--thermal-levels', '0'], ['--sensor-texture'], ['--random-colors'],
                          ['--no-hud', '--heat-glow', '0']):
                a, b = [parser().parse_args(tokens) for tokens in (
                    ['--preset-file', str(preset), *flags], [*flags, '--preset-file', str(preset)])]
                self.assertEqual(vars(a), vars(b))
            args = parser().parse_args(['--preset-file', str(preset), '--thermal-levels', '0'])
            self.assertEqual((args.thermal_levels, args.thermal_band_softness, args.hud, args.heat_glow), (0, None, True, .6))
            args = parser().parse_args(['--preset-file', str(preset), '--sensor-texture'])
            self.assertEqual((args.grain, args.pixelation, args.scanlines), (None, None, None))
            self.assertEqual(LOOK_PRESETS['yautja']['thermal_levels'], 12)

    def test_changing_modes_clears_inherited_dependent_values(self):
        base = {'palette': 'custom', 'palette_colors': '#000,#fff', 'hud_theme': 'custom',
                'hud_colors': 'waveform=#f00', 'wave_style': 'rorschach', 'wave_width': .2}
        with tempfile.TemporaryDirectory() as folder:
            preset = Path(folder) / 'mine.json'
            preset.write_text(json.dumps({'schema_version': 1, 'name': 'Custom', 'settings': base}))
            args = parser().parse_args(['--preset-file', str(preset), '--palette', 'green-phosphor',
                                        '--hud-theme', 'palette', '--wave-style', 'trace'])
            self.assertIsNone(args.palette_colors)
            self.assertIsNone(args.hud_colors)
            self.assertIsNone(args.wave_width)
            args = parser().parse_args(['--preset-file', str(preset), '--random-colors'])
            self.assertEqual((args.palette, args.hud_theme, args.palette_colors, args.hud_colors), ('yautja', 'standard', None, None))

    def test_bad_files_cannot_change_media_or_trigger_actions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output, preset = root / 'keep.png', root / 'bad.json'
            output.write_bytes(b'keep')
            base = {'schema_version': 1, 'name': 'Bad', 'settings': {}}
            cases = [[], {**base, 'schema_version': True}, {**base, 'schema_version': 2},
                     {**base, 'base': '../other.json'}, {**base, 'command': 'anything'},
                     {**base, 'settings': {'input': 'private.mov'}}, {**base, 'settings': {'overwrite': True}},
                     {**base, 'settings': {'download_models': True}}, {**base, 'settings': {'target': ['S001-F001']}},
                     {**base, 'settings': {'hud': 'false'}}, {**base, 'settings': {'seed': True}},
                     {**base, 'settings': {'thermal_levels': 4.5}}, {**base, 'settings': {'thermal_levels': 1}},
                     {**base, 'settings': {'palette': 'missing'}}, {**base, 'settings': {'grain': float('nan')}},
                     {**base, 'settings': {'thermal_gamma': 1e309}}, {**base, 'settings': {'seed': 10**1000}},
                     {**base, 'settings': {'thermal': None}}]
            for data in cases:
                preset.write_text(json.dumps(data))
                with self.subTest(data=data), patch('yautja.cli.convert') as convert, \
                        patch('sys.stderr', new_callable=io.StringIO):
                    with self.assertRaises(SystemExit) as error:
                        main(['missing.png', str(output), '--overwrite', '--preset-file', str(preset)])
                    self.assertEqual(error.exception.code, 2)
                    convert.assert_not_called()
                    self.assertEqual(output.read_bytes(), b'keep')
            for text in ('{"schema_version":1,"schema_version":1}', '{broken', ' ' * 65537):
                preset.write_text(text)
                with self.assertRaises(ValueError):
                    load_preset(preset)

    def test_save_rejects_operational_flags_and_invalid_looks_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            preset = Path(folder) / 'mine.json'
            for flags in (['--fps', '24'], ['--mute'], ['--thermal-levels', '1'],
                          ['--wave-style', 'trace', '--wave-width', '.2'], ['--grain', '1'],
                          ['in.png', 'out.png'], ['--doctor'], ['--list-figures']):
                with self.subTest(flags=flags), patch('sys.stderr', new_callable=io.StringIO):
                    with self.assertRaises(SystemExit):
                        main(['--save-preset', str(preset), *flags])
                    self.assertFalse(preset.exists())

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg unavailable')
    def test_video_uses_saved_preset_with_audio_without_inheriting_target_selections(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'clip.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=12:duration=0.5',
                            '-f', 'lavfi', '-i', 'sine=frequency=330:duration=0.5', '-c:v', 'libx264',
                            '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', str(source)], check=True)
            preset = root / 'video.json'
            self.invoke(['--save-preset', preset, '--stylepreset', 'white-hot', '--thermal', 'classic',
                         '--target-shape', 'crosshair', '--motion-blur', '.3', '--crt-lines', '--timecode'])
            report = self.invoke([source, root / 'out.mp4', '--preset-file', preset])
            self.assertEqual((report['frames'], report['audio_preserved'], report['target_shape']), (6, True, 'crosshair'))
            self.assertEqual(set(report['hud_colors'].values()), {'#d0d0d0'})
            self.assertEqual(report['targets'], [])


if __name__ == '__main__':
    unittest.main()
