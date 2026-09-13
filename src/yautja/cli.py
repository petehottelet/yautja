#!/usr/bin/env python3
"""Local image/video-to-Yautja converter. Run with --help for options."""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from fractions import Fraction
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

from . import __version__
from .render import Renderer, PALETTES
from .colors import HUD_THEMES, resolve_colors, hex_color
from .hud import BLUR_ELEMENTS, OPACITY_ELEMENTS, hud_blurs, hud_opacities
from .thermal import THERMAL_MODES, resolve_thermal
from .waveform import WAVE_STYLES

EFFECT_OPTIONS = ('target_colors', 'target_acquire', 'target_flash', 'target_flash_rate', 'target_scale',
                  'motion_blur', 'crt_bleed', 'crt_vertical_lines', 'crt_strength', 'heat_glow', 'heat_glow_speed',
                  'wave_style', 'wave_width', 'wave_height', 'wave_detail',
                  'target_stroke', 'target_stroke_colors', 'hud_blur', 'hud_blur_elements',
                  'hud_opacity', 'hud_opacity_elements')


def target_selection(args, source):
    if not args.hud or not args.target:
        return None
    from .figures import TargetSelection
    return TargetSelection(args.figures, source, args.target)


def extra_report(renderer, selection, *, static=False):
    selected = selection.selected if selection and renderer.hud else set()
    unseen = sorted(selected - renderer.target_overlay.seen)
    if unseen:
        print('Selected targets not visible in this range: ' + ', '.join(unseen), file=sys.stderr)
    outline = renderer.target_overlay.stroke_colors or tuple(tuple(round(c * .62) for c in renderer.hud_colors[key])
                                                            for key in ('target', 'target-flash'))
    return {'targets': sorted(selected), 'targets_seen': sorted(renderer.target_overlay.seen),
            'targets_unseen': unseen, 'target_frames': renderer.target_overlay.frames,
            'target_colors': [renderer.colors.report()['hud_colors'][k] for k in ('target', 'target-flash')],
            'target_acquire': renderer.target_overlay.acquire,
            'target_flash': bool(selected and renderer.target_overlay.flash_rate and not static), 'target_flash_rate': renderer.target_overlay.flash_rate,
            'target_scale': renderer.target_overlay.scale, 'motion_blur': renderer.display.motion_blur,
            'target_stroke': renderer.target_overlay.stroke if renderer.hud else 0.,
            'target_stroke_colors': [hex_color(color) for color in outline],
            'hud_blur': renderer.hud_blur if renderer.hud else 0.,
            'hud_blur_elements': {key: value if renderer.hud else 0. for key, value in renderer.hud_blurs.items()},
            'hud_opacity': renderer.hud_opacity if renderer.hud else 0.,
            'hud_opacity_elements': {key: value if renderer.hud else 0. for key, value in renderer.hud_opacities.items()},
            'hud_effect_units': 'stroke widths and blur radii: pixels at 1080px short edge, scaled with output size',
            'crt_bleed': renderer.display.crt_bleed, 'crt_vertical_lines': renderer.crt_vertical_lines,
            'crt_strength': renderer.crt_strength, 'heat_glow': renderer.heat_glow, 'heat_glow_speed': renderer.heat_glow_speed,
            'wave_style': renderer.wave_style if renderer.hud else 'off',
            'wave_width': renderer.wave_width if renderer.hud and renderer.wave_style != 'trace' else None,
            'wave_height': renderer.wave_height if renderer.hud and renderer.wave_style != 'trace' else None,
            'wave_detail': renderer.wave_detail if renderer.hud and renderer.wave_style != 'trace' else None}


class ConversionError(RuntimeError):
    pass


def stop_process(process):
    if process.poll() is None:
        if os.name == 'nt':
            # Windows package managers can expose launcher shims. Killing only
            # the launcher leaves its FFmpeg child holding pipes and log files.
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        if process.poll() is None:
            process.kill()
    process.wait()


def run(command):
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        try:
            stdout, stderr = process.communicate()
        finally:
            stop_process(process)
        if process.returncode:
            raise ConversionError(stderr.decode('utf-8', 'replace')[-6000:])
        return stdout


def binary(name):
    found = shutil.which(name)
    if not found:
        raise ConversionError(f'{name} is missing. Install FFmpeg (including ffprobe), then put both on PATH.')
    return found


def number(value, default=0.):
    try:
        result = float(Fraction(str(value)))
        return result if math.isfinite(result) else default
    except (ValueError, ZeroDivisionError):
        return default


def probe(path, ffprobe):
    data = json.loads(run([ffprobe, '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)]))
    videos = [s for s in data['streams'] if s['codec_type'] == 'video' and not s.get('disposition', {}).get('attached_pic')]
    if not videos:
        raise ConversionError('Input has no decodable video stream.')
    return data, videos[0]


def dimensions(stream, max_size):
    width, height = stream['width'], stream['height']
    sar = number(stream.get('sample_aspect_ratio', '1').replace(':', '/'), 1.) or 1.
    width *= sar
    rotation = number(stream.get('tags', {}).get('rotate', 0))
    for side in stream.get('side_data_list', []):
        if 'rotation' in side:
            rotation = number(side['rotation'])
    if round(rotation / 90) % 2:
        width, height = height, width
    ratio = min(1., max_size / max(width, height))
    return max(2, round(width * ratio / 2) * 2), max(2, round(height * ratio / 2) * 2)


class AudioAnalysis:
    rate = 8000

    def __init__(self, path, channels, offset=0., threshold=1e-5):
        self.channels, self.offset = channels, offset
        self.samples = None
        size = path.stat().st_size // 4
        if size and size % channels == 0:
            self.samples = np.memmap(path, dtype='<f4', mode='r', shape=(size // channels, channels))
        self.peak = 0.
        if self.samples is not None:
            for start in range(0, len(self.samples), self.rate * 60):
                part = np.nan_to_num(np.asarray(self.samples[start:start + self.rate * 60]), copy=True)
                self.peak = max(self.peak, float(np.max(np.abs(part), initial=0)))
        self.silent = self.peak < threshold

    def close(self):
        if self.samples is not None:
            self.samples._mmap.close()
            self.samples = None

    def waveform(self, seconds, window=.6, gain=1., bins=256):
        count = max(bins, round(window * self.rate))
        end = round((seconds - self.offset) * self.rate)
        start = end - count
        part = np.zeros((count, self.channels), dtype=np.float32)
        if self.samples is not None:
            lo, hi = max(0, start), min(len(self.samples), end)
            if hi > lo:
                part[lo-start:hi-start] = self.samples[lo:hi]
        np.nan_to_num(part, copy=False)
        # Pool extrema across channels; opposite-phase stereo cannot cancel.
        edges = np.linspace(0, count, bins + 1).astype(int)
        low = np.array([part[edges[i]:edges[i+1]].min(initial=0) for i in range(bins)])
        high = np.array([part[edges[i]:edges[i+1]].max(initial=0) for i in range(bins)])
        normalization = min(8., .9 / max(self.peak, .001)) * gain
        return np.clip(low * normalization, -1, 1), np.clip(high * normalization, -1, 1)


def read_frame(pipe, size):
    parts, remaining = [], size
    while remaining:
        part = pipe.read(remaining)
        if not part:
            if parts:
                raise ConversionError('Video decoder returned a truncated frame.')
            return None
        parts.append(part)
        remaining -= len(part)
    return b''.join(parts)


def audio_filter(rate):
    # Preserve gaps on the track's relative timeline; the stream-start offset is
    # handled separately for waveform lookup and final soundtrack placement.
    return f'asetpts=PTS-STARTPTS,aresample={rate}:async=1:first_pts=0'


def media_kind(args):
    if args.media != 'auto':
        return args.media
    if ((args.input and args.input.suffix.lower() in ('.jpg', '.jpeg', '.png')) or
            (args.output and args.output.suffix.lower() == '.png')):
        return 'image'
    return 'video'


def output_paths(args, suffix):
    source, output = args.input.expanduser().resolve(), args.output.expanduser().resolve()
    if not source.is_file():
        raise ConversionError(f'Input does not exist: {source}')
    if source == output:
        raise ConversionError('Input and output must be different files.')
    if output.suffix.lower() != suffix:
        raise ConversionError(f'Output must end in {suffix} for this media type.')
    if output.exists() and not args.overwrite:
        raise ConversionError('Output already exists. Choose another name or use --overwrite.')
    return source, output


def semantic_tracker(args):
    if args.thermal == 'classic' and not args.list_figures:
        return None
    from .semantic import GroundedSegmenter, SemanticTracker
    print('Loading cached local segmentation and pose models...', file=sys.stderr, flush=True)
    tracker = SemanticTracker(GroundedSegmenter(warm=args.warm_objects, hot=args.hot_objects,
                              device=args.device, confidence=args.confidence, precision=args.precision,
                              surfaces=not args.list_figures and resolve_thermal(args.thermal) in ('cinematic', 'detailed')), args.detect_interval)
    print(f'Semantic device: {tracker.detector.device} ({tracker.detector.device_reason}); '
          f'precision: {tracker.detector.precision}', file=sys.stderr, flush=True)
    return tracker


def load_image(source, max_size):
    try:
        with Image.open(source, formats=['JPEG', 'PNG']) as original:
            if getattr(original, 'n_frames', 1) != 1:
                raise ConversionError('Animated PNG is not a still image. Use video mode or provide a single frame.')
            input_format = original.format
            oriented = ImageOps.exif_transpose(original)
            transparency = 'A' in oriented.getbands() or 'transparency' in oriented.info
            if transparency:
                rgba = oriented.convert('RGBA')
                frame = Image.alpha_composite(Image.new('RGBA', rgba.size, (0, 0, 0, 255)), rgba).convert('RGB')
            else:
                frame = oriented.convert('RGB')
            frame.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            frame.info.clear()
    except (OSError, Image.DecompressionBombError) as exc:
        raise ConversionError(f'Cannot read a still JPEG or PNG image: {exc}') from exc
    if min(frame.size) < 2:
        raise ConversionError('Image width and height must each be at least 2 pixels.')
    return frame, input_format, transparency


def convert_image(args):
    started = time.monotonic()
    source, output = output_paths(args, '.png')
    selection = target_selection(args, source)
    video_options = {'start': 0., 'duration': None, 'fps': None, 'audio_stream': 0,
                     'mute': False, 'wave_window': .6, 'wave_gain': 1.,
                     'crf': 18, 'preset': 'medium', 'detect_interval': .5}
    invalid = ['--' + key.replace('_', '-') for key, default in video_options.items()
               if getattr(args, key) != default]
    if args.hud and args.waveform == 'audio':
        invalid.append('--waveform audio')
    if invalid:
        raise ConversionError('Still images do not use video timing or audio options: ' + ', '.join(invalid))
    frame, input_format, transparency = load_image(source, args.max_size)
    timings = {'image_decode_seconds': time.monotonic() - started}
    setup_started = time.monotonic()
    tracker = semantic_tracker(args)
    timings['model_setup_seconds'] = time.monotonic() - setup_started
    processing_started = time.monotonic()
    width, height = frame.size
    subjects = tracker.update(frame, 0.) if tracker else ()
    renderer = Renderer(width, height, seed=args.seed, grain=args.grain, glow=args.glow,
                        show_timecode=args.timecode, timecode_start=args.timecode_start,
                        thermal=args.thermal, sensor_resolution=args.sensor_resolution, verbose=args.verbose,
                        sensor_texture=args.sensor_texture, palette=args.palette,
                        pixelation=args.pixelation, scanlines=args.scanlines, vhs=args.vhs,
                        palette_colors=args.palette_colors, hud_theme=args.hud_theme,
                        hud_colors=args.hud_colors, random_colors=args.random_colors, hud=args.hud,
                        **{key: getattr(args, key) for key in EFFECT_OPTIONS})
    targets, shot = selection.at(0.) if selection else ([], None)
    rendered = renderer.render(frame, 0., subjects=subjects, targets=targets, shot_id=shot, target_static=True)
    rendered.info.clear()
    timings['processing_seconds'] = time.monotonic() - processing_started
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.yautja-', dir=output.parent) as temp_dir:
        temporary = Path(temp_dir) / 'result.png'
        rendered.save(temporary, format='PNG')
        with Image.open(temporary) as check:
            check.verify()
        if output.exists() and not args.overwrite:
            raise ConversionError('Output appeared during conversion; refusing to overwrite it.')
        os.replace(temporary, output)
    from .runtime import environment_info
    report = {'report_version': 1, 'media_type': 'image', 'input_format': input_format,
              'output': str(output), 'output_format': 'PNG', 'width': width, 'height': height,
              'frames': 1, 'waveform': 'procedural-static' if args.hud else 'off', 'audio_preserved': False,
              'hud': renderer.hud, 'timecode': renderer.show_timecode, 'thermal': args.thermal, 'verbose': renderer.verbose,
              'sensor_texture': args.sensor_texture, 'palette': renderer.palette_name,
              'grain': renderer.grain, 'pixelation': renderer.pixelation, 'scanlines': renderer.scanlines,
              'crt_lines': renderer.scanlines, 'vhs': renderer.vhs,
              'transparency_flattened': transparency,
              'elapsed_seconds': round(time.monotonic() - started, 2),
              'environment': environment_info(),
              'timings': {key: round(value, 3) for key, value in timings.items()},
              'settings': {key: getattr(args, key) for key in (
                  'max_size', 'seed', 'grain', 'glow', 'device', 'precision', 'warm_objects',
                  'hot_objects', 'confidence', 'sensor_resolution', 'timecode_start', 'sensor_texture', 'palette',
                  'pixelation', 'scanlines', 'vhs', 'palette_colors', 'hud_theme', 'hud_colors', 'random_colors', 'hud', 'timecode', 'verbose')}}
    report.update(renderer.colors.report())
    report.update(extra_report(renderer, selection, static=True))
    report['settings'].update({key: getattr(args, key) for key in EFFECT_OPTIONS})
    report['settings']['target'] = args.target
    if tracker:
        report['semantic'] = {**tracker.report(), 'backend': 'single-image', 'tracking': 'none'}
        if not subjects:
            print('No requested subjects detected; semantic output contains only the cool environment.', file=sys.stderr)
    print(json.dumps(report, indent=2))
    return report


def convert(args):
    if media_kind(args) == 'image':
        return convert_image(args)
    return convert_video(args)


def convert_video(args):
    started = time.monotonic()
    timings = {}
    source, output = output_paths(args, '.mp4')
    selection = target_selection(args, source)
    ffmpeg, ffprobe = binary('ffmpeg'), binary('ffprobe')
    data, video = probe(source, ffprobe)
    audios = [s for s in data['streams'] if s['codec_type'] == 'audio']
    if args.audio_stream >= len(audios) and args.audio_stream != 0:
        raise ConversionError('Requested audio stream does not exist.')
    audio = audios[args.audio_stream] if audios else None
    width, height = dimensions(video, args.max_size)
    fps = args.fps or min(60., max(1., number(video.get('avg_frame_rate'), number(video.get('r_frame_rate'), 30.)) or 30.))
    fps_text = str(Fraction(fps).limit_denominator(1001000))
    duration = number(video.get('duration'), number(data.get('format', {}).get('duration')))
    if duration and args.start >= duration:
        raise ConversionError('--start is at or beyond the end of the video.')
    container_start = number(data.get('format', {}).get('start_time'))
    video_start = number(video.get('start_time'), container_start)
    seek = max(0., args.start + video_start - container_start)
    time_options = ['-ss', str(seek)] if seek else []
    length_options = ['-t', str(args.duration)] if args.duration else []
    # Resample timestamps before scaling: some FFmpeg scale builds discard
    # the last frame's duration metadata, which would truncate fps output.
    filters = ['setpts=PTS-STARTPTS', f'fps={fps_text}:eof_action=pass']
    hdr = video.get('color_transfer') in ('smpte2084', 'arib-std-b67')
    if hdr:
        filters += ['zscale=t=linear:npl=100', 'format=gbrpf32le', 'tonemap=hable:desat=0', 'zscale=p=bt709:t=bt709:m=bt709:r=tv']
    filters += [f'scale={width}:{height}:flags=lanczos', 'setsar=1', 'format=rgb24']
    output.parent.mkdir(parents=True, exist_ok=True)
    frames = 0
    analysis = None
    mode = 'procedural' if args.hud else 'off'
    setup_started = time.monotonic()
    tracker = semantic_tracker(args)
    timings['model_setup_seconds'] = time.monotonic() - setup_started
    with tempfile.TemporaryDirectory(prefix='.yautja-', dir=output.parent) as temp_dir:
        temp = Path(temp_dir)
        try:
            audio_started = time.monotonic()
            if args.hud and audio and args.waveform != 'procedural':
                print('Analyzing audio locally...', file=sys.stderr, flush=True)
                pcm = temp / 'analysis.f32'
                # Decode the selected track without downmixing; analysis is disk-backed.
                run([ffmpeg, '-v', 'error', '-nostdin', '-y', '-i', str(source), '-map', f"0:{audio['index']}",
                     '-vn', '-af', audio_filter(AudioAnalysis.rate), '-ar', str(AudioAnalysis.rate), '-c:a', 'pcm_f32le', '-f', 'f32le', str(pcm)])
                analysis = AudioAnalysis(pcm, int(audio.get('channels', 1)), number(audio.get('start_time'), container_start) - video_start)
                if args.waveform == 'audio' or not analysis.silent:
                    mode = 'audio'
            if args.hud and args.waveform == 'audio' and audio is None:
                raise ConversionError('--waveform audio requires an audio stream. Use auto for silent-video fallback.')
            timings['audio_analysis_seconds'] = time.monotonic() - audio_started
            print(f'{width}x{height} at {fps_text} fps; waveform: {mode}; timecode: {args.hud and args.timecode}', file=sys.stderr, flush=True)
            processing_started = time.monotonic()
            renderer = Renderer(width, height, seed=args.seed, grain=args.grain, glow=args.glow,
                                show_timecode=args.timecode, timecode_start=args.timecode_start,
                                thermal=args.thermal, sensor_resolution=args.sensor_resolution, verbose=args.verbose,
                                sensor_texture=args.sensor_texture, palette=args.palette,
                                pixelation=args.pixelation, scanlines=args.scanlines, vhs=args.vhs,
                                palette_colors=args.palette_colors, hud_theme=args.hud_theme,
                                hud_colors=args.hud_colors, random_colors=args.random_colors, hud=args.hud,
                                **{key: getattr(args, key) for key in EFFECT_OPTIONS})
            intermediate = temp / 'picture.mp4'
            decode_cmd = [ffmpeg, '-v', 'error', '-nostdin', *time_options, '-i', str(source), '-map', f"0:{video['index']}",
                          *length_options, '-an', '-sn', '-dn', '-vf', ','.join(filters), '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1']
            encode_cmd = [ffmpeg, '-v', 'error', '-nostdin', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{width}x{height}', '-r', fps_text, '-i', 'pipe:0', '-an', '-c:v', 'libx264',
                          '-preset', args.preset, '-crf', str(args.crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(intermediate)]
            decoder = encoder = None
            with (temp / 'decode.log').open('w+b') as dec_log, (temp / 'encode.log').open('w+b') as enc_log:
                try:
                    decoder = subprocess.Popen(decode_cmd, stdout=subprocess.PIPE, stderr=dec_log)
                    encoder = subprocess.Popen(encode_cmd, stdin=subprocess.PIPE, stderr=enc_log)
                    while True:
                        raw = read_frame(decoder.stdout, width * height * 3)
                        if raw is None:
                            break
                        t = frames / fps
                        wave = analysis.waveform(args.start + t, args.wave_window, args.wave_gain) if mode == 'audio' else None
                        frame = Image.frombytes('RGB', (width, height), raw)
                        subjects = tracker.update(frame, t) if tracker else ()
                        targets, shot = selection.at(args.start + t) if selection else ([], getattr(tracker, 'scene_cuts', None))
                        encoded = renderer.render(frame, t, wave, subjects, targets=targets, shot_id=shot)
                        encoder.stdin.write(encoded.tobytes())
                        frames += 1
                        if frames % max(1, round(fps * 2)) == 0:
                            print(f'Converted {frames / fps:.1f}s ({frames} frames)', file=sys.stderr, flush=True)
                    encoder.stdin.close()
                    decode_status, encode_status = decoder.wait(), encoder.wait()
                    if decode_status or encode_status:
                        dec_log.seek(0); enc_log.seek(0)
                        raise ConversionError((dec_log.read() + enc_log.read()).decode('utf-8', 'replace')[-6000:])
                except BrokenPipeError as exc:
                    enc_log.seek(0)
                    raise ConversionError('Encoder stopped: ' + enc_log.read().decode('utf-8', 'replace')[-3000:]) from exc
                finally:
                    for process in (decoder, encoder):
                        if process is not None:
                            stop_process(process)
                            for pipe in (process.stdin, process.stdout):
                                if pipe:
                                    try:
                                        pipe.close()
                                    except BrokenPipeError:
                                        pass
            if not frames:
                raise ConversionError('No frames decoded. The source may be unsupported, corrupt, or outside the requested range.')
            timings['processing_seconds'] = time.monotonic() - processing_started
            mux_started = time.monotonic()
            final = intermediate
            if audio and not args.mute:
                final = temp / 'result.mp4'
                # Fill timestamp gaps BEFORE trimming; seeking into a gap and
                # resetting the next packet's PTS would pull resumed sound early.
                offset = number(audio.get('start_time'), container_start) - video_start
                delay = max(0, round((offset - args.start) * 1000))
                audio_trim = max(0., args.start - offset)
                run([ffmpeg, '-v', 'error', '-nostdin', '-y', '-i', str(intermediate), '-i', str(source),
                     '-map', '0:v:0', '-map', f"1:{audio['index']}", '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                     '-af', f'{audio_filter(48000)},atrim=start={audio_trim},asetpts=PTS-STARTPTS,adelay={delay}:all=1,apad', '-t', str(frames / fps),
                     '-map_metadata', '-1', '-movflags', '+faststart', str(final)])
            timings['audio_mux_seconds'] = time.monotonic() - mux_started
            # Commit output only after both encoding and audio mux succeed.
            if output.exists() and not args.overwrite:
                raise ConversionError('Output appeared during conversion; refusing to overwrite it.')
            os.replace(final, output)
            report = {'media_type': 'video', 'output': str(output), 'width': width, 'height': height, 'fps': fps, 'frames': frames,
                      'duration': frames / fps, 'waveform': mode, 'audio_preserved': bool(audio and not args.mute),
                      'hud': renderer.hud, 'timecode': renderer.show_timecode, 'hdr_tonemapped': hdr, 'elapsed_seconds': round(time.monotonic() - started, 2)}
            report.update(thermal=args.thermal, verbose=renderer.verbose,
                          sensor_texture=args.sensor_texture, palette=renderer.palette_name,
                          grain=renderer.grain, pixelation=renderer.pixelation, scanlines=renderer.scanlines,
                          crt_lines=renderer.scanlines, vhs=renderer.vhs)
            from .runtime import environment_info
            report.update(report_version=1, environment=environment_info(),
                          timings={key: round(value, 3) for key, value in timings.items()},
                          processing_fps=round(frames / max(timings['processing_seconds'], .001), 3),
                          settings={key: getattr(args, key) for key in (
                              'start', 'duration', 'max_size', 'fps', 'crf', 'preset', 'seed', 'grain', 'glow',
                              'device', 'precision', 'warm_objects', 'hot_objects', 'confidence', 'detect_interval',
                              'sensor_resolution', 'waveform', 'wave_window', 'wave_gain', 'audio_stream', 'mute',
                              'timecode_start', 'sensor_texture', 'palette', 'pixelation', 'scanlines', 'vhs',
                              'palette_colors', 'hud_theme', 'hud_colors', 'random_colors', 'hud', 'timecode', 'verbose')})
            report.update(renderer.colors.report())
            report.update(extra_report(renderer, selection))
            report['settings'].update({key: getattr(args, key) for key in EFFECT_OPTIONS})
            report['settings']['target'] = args.target
            if tracker:
                report['semantic'] = tracker.report()
                if not tracker.max_subjects:
                    print('No requested subjects detected; semantic output contains only the cool environment.', file=sys.stderr)
            print(json.dumps(report, indent=2))
            return report
        finally:
            if analysis:
                analysis.close()


def parser():
    p = argparse.ArgumentParser(description='Re-skin a local image or video with a sci-fi thermal-imaging look and HUD. Optional segmentation, anatomy-guided coloring, and glyph annotations. For entertainment only; colors are algorithmically generated with some randomness, not measured temperatures.')
    version = __version__
    p.add_argument('--version', action='version', version=f'Yautja {version}')
    p.add_argument('input', nargs='?', type=Path, help='Local JPEG/PNG image or video')
    p.add_argument('output', nargs='?', type=Path, help='PNG for a still image; MP4 for a video')
    p.add_argument('--media', choices=['auto', 'image', 'video'], default='auto', help='Auto selects images for JPEG/PNG input or PNG output; use image with --doctor to skip FFmpeg checks')
    p.add_argument('--doctor', action='store_true', help='Check the local runtime, tools, and bundled shapes')
    p.add_argument('--thermal', type=resolve_thermal, choices=THERMAL_MODES, default='classic', help='Three segmented looks: silhouette (soft), cinematic (broad surface patches), detailed (skin/clothing/gear). Classic is the lightweight luminance filter; old semantic/realistic names remain aliases')
    p.add_argument('--palette', choices=['auto', *PALETTES, 'custom', 'random'], default='yautja', help='Thermal colors, independent of thermal style. Original Yautja by default; custom uses --palette-colors; random uses --seed')
    p.add_argument('--palette-colors', help='With --palette custom: quoted string of 2–16 comma/space-separated hex colors, cold to hot, evenly spaced; e.g. "#000000,#0033ff,#ff2200"')
    p.add_argument('--hud-theme', choices=HUD_THEMES, default='standard', help='HUD colors: standard red/cyan (black for Black Hot, muted cyan for Abyss), palette-matched, muted-cyan, custom, or seeded random')
    p.add_argument('--hud', action=argparse.BooleanOptionalAction, default=True, help='Show the HUD (default); --no-hud hides all waveform, scale, glyph, timecode, callout, leader, and marker overlays while retaining thermal coloring, textures, and sound')
    p.add_argument('--hud-colors', help='With --hud-theme custom: quoted comma-separated element=#RRGGBB assignments. Elements: waveform, waveform-axis, waveform-ticks, waveform-glyphs, readout, timecode, callouts, leaders, markers, target, target-flash. Unspecified elements keep standard colors')
    p.add_argument('--hud-blur', type=float, default=0., help='Gaussian softness for all HUD artwork only, 0-20 reference pixels at a 1080px short edge; default 0 (sharp)')
    p.add_argument('--hud-blur-elements', help='Override blur independently with quoted comma-separated element=radius values, 0-20; explicit 0 keeps an element sharp. Elements: ' + ', '.join(BLUR_ELEMENTS) + '. Target applies to both flash states')
    p.add_argument('--hud-opacity', type=float, default=1., help='Shared HUD visibility, 0-1: 0 is transparent, 1 keeps full existing visibility (default); includes outlines and glow')
    p.add_argument('--hud-opacity-elements', help='Independent transparency via quoted comma-separated element=opacity values, 0-1; omitted elements inherit --hud-opacity. Elements: ' + ', '.join(OPACITY_ELEMENTS) + '. Target-flash inherits target unless explicitly set')
    p.add_argument('--random-colors', action='store_true', help='Randomize both the thermal palette and every HUD element once using --seed; colors stay fixed throughout the clip')
    p.add_argument('--sensor-texture', action=argparse.BooleanOptionalAction, default=False, help='Preset combining sensor pixels, grain, and scanlines (default: off); individual controls override the preset')
    p.add_argument('--pixelation', nargs='?', type=int, const=96, help='Chunky pixels: longest grid edge, 32-640 (bare flag: 96); 0 disables. Independent of grain and segmentation')
    p.add_argument('--crt-lines', '--scanlines', dest='scanlines', action=argparse.BooleanOptionalAction, default=None, help='Horizontal CRT lines across the final image and HUD; default off unless sensor texture is enabled')
    p.add_argument('--vhs', action=argparse.BooleanOptionalAction, default=False, help='VHS-style color bleed, horizontal wobble, tape noise, and tracking defects; default off')
    p.add_argument('--list-figures', action='store_true', help='Scan shots into a JSON figure catalog and HTML contact sheet; optional output defaults beside the input. Requires the semantic runtime')
    p.add_argument('--figures', type=Path, help='Saved figure catalog from the same source, used with --target')
    p.add_argument('--target', action='append', default=[], help='Figure ID from the catalog, e.g. S001-F002; repeat or comma-separate for multiple figures/shots')
    p.add_argument('--target-colors', help='Two comma-separated RGB hex colors for landing and flash, overriding HUD target colors; default red,white')
    p.add_argument('--target-acquire', type=float, default=.8, help='Seconds for the three target blades to assemble, 0.1-5')
    p.add_argument('--target-flash', action=argparse.BooleanOptionalAction, default=True, help='Alternate target colors after landing; --no-target-flash keeps the landing color')
    p.add_argument('--target-flash-rate', type=float, default=1.5, help='Target flash cycles per second, 0-3; 0 holds the landing color')
    p.add_argument('--target-scale', type=float, default=1., help='Size multiplier for the compact reticle centered on the selected figure, 0.25-3; default 1')
    p.add_argument('--target-stroke', nargs='?', type=float, const=2., default=0., help='Optional inward outline on each target blade, 0-12 reference pixels at a 1080px short edge; bare flag 2, default 0 (off)')
    p.add_argument('--target-stroke-colors', help='Outline color: one RGB hex color or a landing,flash pair. Omit or use auto for darker shades of the current target colors; requires nonzero --target-stroke to be visible')
    p.add_argument('--motion-blur', type=float, default=0., help='Temporal motion trails/persistence strength, 0-1; 0 disables. Video only; stills have no preceding frames')
    p.add_argument('--crt-bleed', type=float, default=0., help='Horizontal phosphor color spread, 0-1; independent of VHS and CRT lines')
    p.add_argument('--crt-vertical-lines', '--vertical-crt-lines', dest='crt_vertical_lines', action=argparse.BooleanOptionalAction, default=False, help='Vertical CRT columns across image and HUD; combine with horizontal --crt-lines')
    p.add_argument('--crt-strength', type=float, default=.12, help='Darkening strength of enabled horizontal/vertical CRT lines, 0-1')
    p.add_argument('--heat-glow', type=float, default=0., help='Animated bloom from synthetic hot regions in any palette, 0-1; independent of HUD --glow')
    p.add_argument('--heat-glow-speed', type=float, default=1., help='Heat-glow movement speed, 0-5; 0 freezes it. Stills show time zero')
    p.add_argument('--download-models', action='store_true', help='Download pinned Apache-2.0 semantic models once, then exit (no input needed)')
    p.add_argument('--device', choices=['auto', 'cpu', 'cuda'], default='auto', help='Semantic inference device; auto prefers available CUDA')
    p.add_argument('--precision', choices=['fp32', 'bf16'], default='fp32', help='Semantic model precision; bf16 is experimental and requires compatible CUDA')
    p.add_argument('--warm-objects', default='person,bird,cat,dog,horse,sheep,cow,elephant,bear,zebra,giraffe', help='Comma-separated object categories to simulate as warm')
    p.add_argument('--hot-objects', default='', help='Explicit comma-separated hot categories, e.g. fire; these are artistic overrides')
    p.add_argument('--confidence', type=float, default=.30, help='Object detection threshold, 0.05-0.95')
    p.add_argument('--detect-interval', type=float, default=.5, help='Seconds between model detections; masks follow optical flow between them')
    p.add_argument('--sensor-resolution', type=int, default=256, help='Heat-field and optional texture grid longest edge, 64-640; smaller is more abstract')
    p.add_argument('--verbose', action='store_true', help='Attach stable glyph callouts to subjects (requires silhouette, cinematic, or detailed mode)')
    p.add_argument('--timecode', action=argparse.BooleanOptionalAction, default=False, help='Human-readable elapsed HH:MM:SS.mmm at upper right (default: off)')
    p.add_argument('--timecode-start', type=float, default=0., help='Offset the displayed elapsed time, in seconds')
    p.add_argument('--waveform', choices=['auto', 'audio', 'procedural'], default='auto')
    p.add_argument('--wave-style', choices=WAVE_STYLES, default='trace', help='Standard trace or thick mirrored Rorschach column: filled, split lobes, or hollow pockets')
    p.add_argument('--wave-width', type=float, help='Rorschach column maximum width as a fraction of the frame, 0.02-0.3; default 0.12')
    p.add_argument('--wave-height', type=float, help='Rorschach column height as a fraction of the frame, 0.1-1; default 0.96')
    p.add_argument('--wave-detail', type=float, default=.6, help='Rorschach detail, 0-1; 0 is broad/smooth, higher values add sharper audio-driven edge spikes and more intricate lobes')
    p.add_argument('--wave-window', type=float, default=.6, help='Trailing audio window in seconds')
    p.add_argument('--wave-gain', type=float, default=1., help='Audio waveform gain')
    p.add_argument('--audio-stream', type=int, default=0, help='Zero-based audio track used for waveform and output')
    p.add_argument('--mute', action='store_true', help='Omit output audio; waveform can still follow source audio')
    p.add_argument('--start', type=float, default=0., help='Trim start in seconds, relative to first video frame')
    p.add_argument('--duration', type=float, help='Limit conversion to this many seconds')
    p.add_argument('--fps', type=float, help='Output constant frame rate (default: source average, capped at 60)')
    p.add_argument('--max-size', type=int, default=1920, help='Longest output edge; preserves aspect and never upscales')
    p.add_argument('--crf', type=int, default=18, help='H.264 quality; lower is higher quality (0-51)')
    p.add_argument('--preset', choices=['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow'], default='medium')
    p.add_argument('--grain', nargs='?', type=float, const=.035, help='Optional grain strength, 0-0.25 (bare flag: 0.035); 0 disables. Default off unless sensor texture is enabled')
    p.add_argument('--glow', type=float, default=.65, help='HUD bloom strength, 0-1')
    p.add_argument('--seed', type=int, default=42, help='Reproducible colors, glyphs, procedural waveform, and grain seed (default: 42)')
    p.add_argument('--overwrite', action='store_true', help='Replace an existing output after successful conversion')
    return p


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    try:
        # Reject invalid color settings before opening media or loading models.
        resolve_colors(PALETTES, palette=args.palette, palette_colors=args.palette_colors,
                       hud_theme=args.hud_theme, hud_colors=args.hud_colors,
                       random_colors=args.random_colors, seed=args.seed)
        from .target import target_colors, parse_stroke_colors
        target_colors(args.target_colors)
        parse_stroke_colors(args.target_stroke_colors)
        hud_blurs(args.hud_blur, args.hud_blur_elements)
        hud_opacities(args.hud_opacity, args.hud_opacity_elements)
        if args.list_figures and (args.figures or args.target):
            p.error('--list-figures scans a new catalog; use --figures/--target on a later render')
        if args.hud and bool(args.target) != bool(args.figures):
            p.error('--target and --figures must be used together')
        if args.doctor:
            from .runtime import environment_info, installation_info, semantic_diagnostics
            from .render import load_glyph_font
            _, chars = load_glyph_font()
            media = media_kind(args)
            tools = {}
            if media == 'video':
                tools = {name: run([binary(name), '-version']).decode('utf-8', 'replace').splitlines()[0] for name in ['ffmpeg', 'ffprobe']}
                encoders = run([binary('ffmpeg'), '-v', 'error', '-encoders']).decode('utf-8', 'replace')
                if 'libx264' not in encoders or ' aac ' not in encoders:
                    raise ConversionError('FFmpeg needs the libx264 and AAC encoders.')
            semantic = semantic_diagnostics(args.device, args.precision)
            ready = (args.thermal == 'classic' and not args.list_figures) or semantic['ready']
            print(json.dumps({'python': sys.version.split()[0], 'characters': len(chars), 'media_type': media, **tools,
                              'environment': environment_info(), 'installation': installation_info(), 'thermal': args.thermal,
                              'ready': ready, 'semantic': semantic}, indent=2))
            return 0 if ready else 1
        if args.download_models:
            from .semantic import GroundedSegmenter, MODELS
            model = GroundedSegmenter(warm=args.warm_objects, hot=args.hot_objects, device=args.device,
                                      precision=args.precision, download=True)
            print(json.dumps({'downloaded': MODELS, 'device': model.device, 'license': 'Apache-2.0'}, indent=2))
            return 0
        if not args.input or (not args.output and not args.list_figures):
            p.error('input and output are required (or use --doctor)')
        if args.hud and args.verbose and args.thermal == 'classic':
            p.error('--verbose requires --thermal silhouette, cinematic, or detailed')
        if args.wave_style == 'trace' and (args.wave_width is not None or args.wave_height is not None):
            p.error('--wave-width and --wave-height require a Rorschach --wave-style')
        if args.precision != 'fp32' and args.thermal == 'classic' and not args.list_figures:
            p.error('--precision bf16 requires --thermal silhouette, cinematic, or detailed')
        checks = [(args.start, 0, math.inf, '--start'), (args.timecode_start, 0, math.inf, '--timecode-start'),
                  (args.wave_window, .05, 5, '--wave-window'), (args.wave_gain, .01, 20, '--wave-gain'),
                  (args.max_size, 160, 8192, '--max-size'), (args.crf, 0, 51, '--crf'),
                  (args.glow, 0, 1, '--glow'), (args.audio_stream, 0, 100, '--audio-stream')]
        checks += [(getattr(args, key), 0, 1, '--' + key.replace('_', '-')) for key in ('motion_blur', 'crt_bleed', 'crt_strength', 'heat_glow')]
        checks += [(args.heat_glow_speed, 0, 5, '--heat-glow-speed'), (args.target_acquire, .1, 5, '--target-acquire'),
                   (args.target_flash_rate, 0, 3, '--target-flash-rate'), (args.target_scale, .25, 3, '--target-scale'),
                   (args.wave_detail, 0, 1, '--wave-detail'), (args.target_stroke, 0, 12, '--target-stroke')]
        if args.wave_width is not None:
            checks.append((args.wave_width, .02, .3, '--wave-width'))
        if args.wave_height is not None:
            checks.append((args.wave_height, .1, 1, '--wave-height'))
        if args.grain is not None:
            checks.append((args.grain, 0, .25, '--grain'))
        if args.pixelation is not None and args.pixelation != 0:
            checks.append((args.pixelation, 32, 640, '--pixelation'))
        checks += [(args.sensor_resolution, 64, 640, '--sensor-resolution'),
                   (args.detect_interval, .05, 2, '--detect-interval'), (args.confidence, .05, .95, '--confidence')]
        if args.fps is not None:
            checks.append((args.fps, 1, 120, '--fps'))
        if args.duration is not None:
            checks.append((args.duration, .001, math.inf, '--duration'))
        for value, lo, hi, name in checks:
            if not math.isfinite(value) or not lo <= value <= hi:
                p.error(f'{name} must be finite and between {lo} and {hi}')
        if args.list_figures:
            from .figures import scan
            scan(args)
        else:
            convert(args)
        return 0
    except (ConversionError, ValueError, OSError) as exc:
        print(f'Yautja: {exc}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('Yautja: cancelled; temporary output removed.', file=sys.stderr)
        return 130


if __name__ == '__main__':
    sys.exit(main())
