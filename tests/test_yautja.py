import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from render import Renderer, lcd_timecode, load_glyph_font, procedural_wave, timecode
from yautja import AudioAnalysis, audio_filter, dimensions, read_frame


class SignalTests(unittest.TestCase):
    def test_wave_is_deterministic_and_matches_original_range(self):
        a = procedural_wave(2, 42)
        np.testing.assert_array_equal(a, procedural_wave(2, 42))
        self.assertFalse(np.array_equal(a, procedural_wave(2.1, 42)))
        self.assertGreater(np.max(a), .25)
        self.assertLess(np.min(a), -.25)
        self.assertEqual(a[0], 0)
        self.assertEqual(abs(a[-1]), 0)
        self.assertGreater(np.count_nonzero(np.diff(np.sign(a))), 80)

    def test_actual_audio_timing_volume_and_opposite_phase_stereo(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'sound.f32'
            t = np.arange(16000) / 8000
            signal = np.sin(2 * np.pi * 220 * t).astype(np.float32)
            signal[:4000] = 0
            signal[4000:8000] *= .1
            np.stack([signal, -signal], axis=1).astype('<f4').tofile(path)
            audio = AudioAnalysis(path, 2, offset=.2)
            try:
                quiet = audio.waveform(.5)
                low = audio.waveform(1.1, .3)
                loud = audio.waveform(1.7, .3)
                self.assertEqual(float(np.max(quiet[1])), 0)
                self.assertGreater(float(np.max(loud[1])), float(np.max(low[1])) * 5)
                self.assertLess(float(np.min(loud[0])), -.8)
                self.assertGreater(float(np.max(loud[1])), .8)
                self.assertFalse(audio.silent)
            finally:
                audio.close()

    def test_silent_track_and_silent_pause_are_different(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'silent.f32'
            np.zeros(8000, dtype='<f4').tofile(path)
            audio = AudioAnalysis(path, 1)
            self.assertTrue(audio.silent)
            audio.close()
            path.write_bytes(b'')
            audio = AudioAnalysis(path, 1)
            self.assertTrue(audio.silent)
            self.assertEqual(np.max(audio.waveform(1)[1]), 0)
            audio.close()

    def test_shapes_and_optional_timecode(self):
        _, characters = load_glyph_font()
        self.assertEqual(len(characters), 62)
        self.assertTrue(all(c.isascii() and c.isalnum() for c in characters))
        self.assertEqual(timecode(3661.234), '01:01:01.234')
        self.assertEqual(timecode(59.9999), '00:01:00.000')
        frame = Image.new('RGB', (640, 360), (120, 100, 80))
        plain = np.array(Renderer(640, 360, grain=0).render(frame, 1.5))
        clock = np.array(Renderer(640, 360, grain=0, show_timecode=True).render(frame, 1.5))
        diff = np.any(plain != clock, axis=2)
        self.assertTrue(np.any(diff[:80, 400:]))
        self.assertFalse(np.any(diff[80:]))
        self.assertFalse(np.any(diff[:, :400]))

    def test_lcd_digits_and_separators_remain_distinct_at_preview_size(self):
        for height in (6, 12):
            digits = [lcd_timecode(str(i), height) for i in range(10)]
            self.assertEqual(len({(tile.size, tile.tobytes()) for tile in digits}), 10)
            clocks = [lcd_timecode('00:00:09.95' + str(i), height) for i in range(10)]
            self.assertEqual(len({tile.size for tile in clocks}), 1)
            self.assertTrue(all(tile.getbbox()[2] == tile.width for tile in clocks))
            colon = np.asarray(lcd_timecode(':', height))[..., 0].max(axis=1) > 80
            dot = np.asarray(lcd_timecode('.', height))[..., 0].max(axis=1) > 80
            self.assertEqual(np.count_nonzero(np.diff(np.r_[False, colon].astype(int)) == 1), 2)
            self.assertEqual(np.count_nonzero(np.diff(np.r_[False, dot].astype(int)) == 1), 1)
            self.assertGreater(np.flatnonzero(dot)[0], height * .7)

    def test_lcd_clock_offset_matches_elapsed_readout(self):
        frame = Image.new('RGB', (640, 360), (120, 100, 80))
        offset = Renderer(640, 360, grain=0, show_timecode=True, timecode_start=90).render(frame, 1.125)
        elapsed = Renderer(640, 360, grain=0, show_timecode=True).render(frame, 91.125)
        np.testing.assert_array_equal(np.asarray(offset)[:80, 400:], np.asarray(elapsed)[:80, 400:])

    def test_sample_aspect_rotation_and_even_dimensions(self):
        self.assertEqual(dimensions({'width': 720, 'height': 480, 'sample_aspect_ratio': '4:3'}, 1920), (960, 480))
        self.assertEqual(dimensions({'width': 640, 'height': 360, 'side_data_list': [{'rotation': -90}]}, 1920), (360, 640))
        w, h = dimensions({'width': 1919, 'height': 1079}, 1280)
        self.assertEqual(w % 2, 0)
        self.assertEqual(h % 2, 0)
        self.assertAlmostEqual(w / h, 1919 / 1079, delta=.003)

    def test_partial_pipe_reads(self):
        import io
        class ShortPipe(io.BytesIO):
            def read(self, count):
                return super().read(min(3, count))
        self.assertEqual(read_frame(ShortPipe(b'abcdef'), 6), b'abcdef')
        self.assertIsNone(read_frame(ShortPipe(b''), 6))
        with self.assertRaisesRegex(RuntimeError, 'truncated'):
            read_frame(ShortPipe(b'ab'), 6)


class ConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.video = cls.root / 'source with spaces.mp4'
        cls.call(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=12:duration=2',
                  '-f', 'lavfi', '-i', 'sine=frequency=330:sample_rate=48000:duration=2',
                  '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', str(cls.video)])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @staticmethod
    def call(args):
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stderr)
        return result.stdout

    def convert(self, source, name, *options):
        output = self.root / name
        report = json.loads(self.call([sys.executable, str(ROOT / 'scripts' / 'yautja.py'), str(source), str(output),
                                      '--preset', 'ultrafast', '--grain', '0', *options]))
        info = json.loads(self.call(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-of', 'json', str(output)]))
        return report, info, output

    def test_audio_conversion_retains_sound_and_all_frames(self):
        report, info, output = self.convert(self.video, 'audio.mp4', '--timecode')
        self.assertEqual(report['report_version'], 1)
        self.assertEqual(report['environment']['executable'], sys.executable)
        self.assertGreater(report['timings']['processing_seconds'], 0)
        self.assertGreater(report['processing_fps'], 0)
        self.assertLessEqual(sum(report['timings'].values()), report['elapsed_seconds'] + .02)
        self.assertEqual(report['settings']['preset'], 'ultrafast')
        self.assertEqual(report['waveform'], 'audio')
        self.assertTrue(report['timecode'])
        video = next(s for s in info['streams'] if s['codec_type'] == 'video')
        audio = next(s for s in info['streams'] if s['codec_type'] == 'audio')
        self.assertEqual(int(video['nb_read_frames']), 24)
        self.assertAlmostEqual(float(audio['duration']), 2, delta=.05)
        decoded = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(output), '-map', '0:a:0', '-f', 'f32le', '-c:a', 'pcm_f32le', 'pipe:1'])
        self.assertGreater(np.max(np.abs(np.frombuffer(decoded, dtype='<f4'))), .05)

    def test_no_audio_and_fully_silent_audio_fallback(self):
        no_audio = self.root / 'no-audio.mp4'
        silent = self.root / 'silent.mp4'
        self.call(['ffmpeg', '-v', 'error', '-y', '-i', str(self.video), '-an', '-c:v', 'copy', str(no_audio)])
        self.call(['ffmpeg', '-v', 'error', '-y', '-i', str(self.video), '-af', 'volume=0', '-c:v', 'copy', str(silent)])
        for source, name, has_audio in [(no_audio, 'fallback.mp4', False), (silent, 'silent-result.mp4', True)]:
            report, info, _ = self.convert(source, name)
            self.assertEqual(report['waveform'], 'procedural')
            self.assertFalse(report['timecode'])
            self.assertEqual(any(s['codec_type'] == 'audio' for s in info['streams']), has_audio)

    def test_trim_and_mute_keep_audio_driven_wave(self):
        report, info, _ = self.convert(self.video, 'trim.mp4', '--start', '.5', '--duration', '1', '--mute')
        self.assertEqual(report['waveform'], 'audio')
        self.assertFalse(report['audio_preserved'])
        self.assertEqual(report['frames'], 12)
        self.assertTrue(all(s['codec_type'] == 'video' for s in info['streams']))

    def test_rotation_metadata(self):
        rotated = self.root / 'rotated.mov'
        self.call(['ffmpeg', '-v', 'error', '-y', '-display_rotation', '90', '-i', str(self.video), '-c', 'copy', str(rotated)])
        report, info, _ = self.convert(rotated, 'portrait.mp4', '--duration', '.5')
        self.assertEqual((report['width'], report['height']), (180, 320))
        self.assertEqual((info['streams'][0]['width'], info['streams'][0]['height']), (180, 320))

    def test_late_audio_stays_late(self):
        delayed = self.root / 'delayed.mkv'
        self.call(['ffmpeg', '-v', 'error', '-y', '-i', str(self.video), '-itsoffset', '1', '-i', str(self.video),
                   '-map', '0:v:0', '-map', '1:a:0', '-c', 'copy', str(delayed)])
        report, info, output = self.convert(delayed, 'delayed-result.mp4')
        decoded = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(output), '-map', '0:a:0', '-ar', '8000', '-ac', '1', '-f', 'f32le', 'pipe:1'])
        samples = np.frombuffer(decoded, dtype='<f4')
        self.assertLess(np.max(np.abs(samples[:6000])), .001)
        self.assertGreater(np.max(np.abs(samples[10000:])), .02)
        self.assertEqual(report['waveform'], 'audio')

    def test_audio_timestamp_gaps_stay_silent_in_analysis_and_soundtrack(self):
        source = self.root / 'audio-gap.mkv'
        self.call(['ffmpeg', '-v', 'error', '-y', '-i', str(self.video), '-c:v', 'copy',
                   '-af', "aselect='not(between(t,0.5,1.0))'", '-c:a', 'pcm_s16le', str(source)])
        pcm = self.root / 'gap-analysis.f32'
        self.call(['ffmpeg', '-v', 'error', '-y', '-i', str(source), '-map', '0:a:0',
                   '-af', audio_filter(8000), '-f', 'f32le', str(pcm)])
        audio = AudioAnalysis(pcm, 1)
        try:
            self.assertLess(float(np.max(audio.waveform(.85, .1)[1])), .001)
            self.assertGreater(float(np.max(audio.waveform(1.7, .1)[1])), .1)
        finally:
            audio.close()
        _, _, output = self.convert(source, 'gap-result.mp4')
        raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(output), '-map', '0:a:0',
                                       '-ar', '8000', '-ac', '1', '-f', 'f32le', 'pipe:1'])
        samples = np.frombuffer(raw, dtype='<f4')
        self.assertLess(float(np.max(np.abs(samples[5600:7200]))), .002)
        self.assertGreater(float(np.max(np.abs(samples[12800:14400]))), .03)
        _, _, trimmed = self.convert(source, 'gap-trimmed.mp4', '--start', '.75', '--duration', '1')
        raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(trimmed), '-map', '0:a:0',
                                       '-ar', '8000', '-ac', '1', '-f', 'f32le', 'pipe:1'])
        samples = np.frombuffer(raw, dtype='<f4')
        self.assertLess(float(np.max(np.abs(samples[:1200]))), .002)
        self.assertGreater(float(np.max(np.abs(samples[4000:5600]))), .03)

    def test_variable_frame_rate_and_anamorphic_input(self):
        source = self.root / 'variable.mkv'
        self.call(['ffmpeg', '-v', 'error', '-y', '-i', str(self.video), '-an',
                   '-vf', "setpts='if(lt(N,12),N/(12*TB),(1+(N-12)/6)/TB)',setsar=4/3",
                   '-fps_mode', 'vfr', '-c:v', 'libx264', str(source)])
        report, info, _ = self.convert(source, 'variable-result.mp4', '--fps', '24')
        self.assertEqual((report['width'], report['height']), (426, 180))
        self.assertEqual(info['streams'][0]['avg_frame_rate'], '24/1')
        self.assertAlmostEqual(report['duration'], 3., delta=.15)

    def test_hdr_input_tone_maps_to_sdr_output(self):
        source = self.root / 'hdr.mp4'
        self.call(['ffmpeg', '-v', 'error', '-y', '-i', str(self.video), '-t', '0.5', '-an',
                   '-vf', 'format=yuv420p10le,setparams=range=limited:color_primaries=bt2020:color_trc=smpte2084:colorspace=bt2020nc',
                   '-c:v', 'libx264', '-pix_fmt', 'yuv420p10le',
                   '-color_primaries', 'bt2020', '-color_trc', 'smpte2084', '-colorspace', 'bt2020nc', str(source)])
        fixture = json.loads(self.call(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(source)]))
        self.assertEqual(fixture['streams'][0]['color_transfer'], 'smpte2084')
        report, info, _ = self.convert(source, 'hdr-result.mp4')
        self.assertTrue(report['hdr_tonemapped'])
        self.assertEqual(info['streams'][0]['pix_fmt'], 'yuv420p')
        self.assertEqual(report['frames'], 6)

    def test_existing_output_and_corrupt_input_are_protected(self):
        output = self.root / 'protected.mp4'
        output.write_bytes(b'keep this')
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/yautja.py'), str(self.video), str(output)], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_bytes(), b'keep this')
        source = self.root / 'corrupt.mov'
        source.write_bytes(b'not a video')
        missing_output = self.root / 'must-not-exist.mp4'
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/yautja.py'), str(source), str(missing_output)], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(missing_output.exists())
        self.assertFalse(list(self.root.glob('.yautja-*')))

    def test_archive_only_contains_portable_manifest(self):
        import zipfile
        from package_skill import FILES
        archive = self.root / 'skill.zip'
        self.call([sys.executable, str(ROOT / 'scripts/package_skill.py'), '--zip', str(archive)])
        with zipfile.ZipFile(archive) as z:
            self.assertEqual(set(z.namelist()), {'yautja/' + name for name in FILES})
            self.assertTrue(all(not name.endswith(('.mp4', '.env')) for name in z.namelist()))
            z.extractall(self.root / 'portable')
        cli = self.root / 'portable/yautja/scripts/yautja.py'
        self.assertEqual(self.call([sys.executable, str(cli), '--version']).strip(),
                         'Yautja ' + (ROOT / 'VERSION').read_text().strip())
        self.assertTrue(json.loads(self.call([sys.executable, str(cli), '--doctor']))['ready'])
        result = json.loads(self.call([sys.executable, str(cli), str(self.video),
                                       str(self.root / 'portable.mp4'), '--duration', '.25', '--timecode']))
        self.assertEqual(result['frames'], 3)
        self.assertTrue(result['audio_preserved'])


if __name__ == '__main__':
    unittest.main()
