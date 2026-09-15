#!/usr/bin/env python3
"""Build matched README GIFs from a short local SDR video using cached models."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from PIL import Image

from yautja.render import Renderer, PALETTES
from yautja.looks import resolve_look
from yautja.presets import load_preset
from yautja.figures import TargetSelection
from yautja.semantic import GroundedSegmenter, SemanticTracker
from yautja.cli import (AudioAnalysis, ConversionError, audio_filter, binary, dimensions,
                    number, probe, read_frame, run, stop_process)


def variants():
    result = {f'style-{style}': {'thermal': style} for style in ('low-detail', 'cinematic', 'detailed', 'very-detailed')}
    for palette in PALETTES:
        if palette != 'yautja':
            result[f'palette-{palette}'] = {'look_preset': palette}
    for name, options in {
        'grain': {'grain': .06}, 'pixelation': {'pixelation': 80},
        'crt-lines': {'scanlines': True}, 'sensor-texture': {'sensor_texture': True},
        'vhs': {'vhs': True}, 'vhs-crt': {'vhs': True, 'scanlines': True},
        'crt-vertical': {'crt_vertical_lines': True, 'crt_strength': .25},
        'crt-grid': {'crt_grid': True, 'crt_strength': .25},
        'crt-crosshatch': {'crt_crosshatch': True, 'crt_strength': .25},
        'motion-soft': {'motion_blur': .35}, 'motion-strong': {'motion_blur': .85},
        'bleed-soft': {'crt_bleed': .3}, 'bleed-strong': {'crt_bleed': .85},
        'heat-glow': {'heat_glow': .75},
        'neon': {'neon': True}, 'neon-flicker': {'neon': True, 'neon_flicker': .5},
    }.items():
        result[f'texture-{name}'] = {'thermal': 'cinematic', **options}
    result.update({
        'look-netrunner': {'look_preset': 'netrunner'},
        'look-fremont': {'look_preset': 'fremont'},
        'look-focus': {'look_preset': 'focus'},
        'look-relic': {'look_preset': 'relic'},
        'look-murphy': {'look_preset': 'murphy'},
        'look-thermal-spectrum-reference-v1': {'look_preset': 'hottropic'},
        **{f'target-shape-{shape}': {'thermal': 'cinematic', 'target_shape': shape}
           for shape in ('triangle-dots', 'crosshair', 'iron-sights', 'square', 'round-dot', 'square-cross', 'square-mil', 'square-x', 'hexagon', 'frame-box')},
        'hud-off': {'thermal': 'cinematic', 'hud': False},
        'colors-matched-green': {'thermal': 'cinematic', 'palette': 'green-phosphor', 'hud_theme': 'palette'},
        'colors-matched-ironbow': {'thermal': 'cinematic', 'palette': 'ironbow', 'hud_theme': 'palette'},
        'colors-custom': {'thermal': 'cinematic', 'palette': 'custom',
                          'palette_colors': '#020518,#173d8f,#10b7ad,#fbad43,#fff1c7',
                          'hud_theme': 'custom',
                          'hud_colors': 'waveform=#ffb347,waveform-axis=#684323,waveform-ticks=#9c6535,waveform-glyphs=#ffd28a,readout=#7fe8ff,timecode=#d6f7ff,callouts=#77ffd0,leaders=#399e83,markers=#ffffff'},
        'colors-random': {'thermal': 'cinematic', 'random_colors': True, 'seed': 137},
        'glow-abyss': {'thermal': 'cinematic', 'palette': 'abyss', 'heat_glow': .75},
        'glow-green': {'thermal': 'cinematic', 'palette': 'green-phosphor', 'hud_theme': 'palette', 'heat_glow': .75},
        'target-lock': {'thermal': 'cinematic'},
        'target-abyss-steady': {'thermal': 'cinematic', 'palette': 'abyss', 'target_flash': False,
                              'target_colors': '#267085,#267085', 'neon': True,
                              'crt_vertical_lines': True, 'crt_strength': .25, 'heat_glow': .65},
        'target-custom': {'thermal': 'cinematic', 'palette': 'green-phosphor', 'hud_theme': 'palette',
                          'target_colors': '#31d7bb,#d6fff3', 'target_acquire': .45, 'crt_bleed': .4},
        'target-outline': {'thermal': 'cinematic', 'target_stroke': 5, 'target_stroke_colors': '#660b12,#687a8d'},
        'target-blur': {'thermal': 'cinematic', 'hud_blur_elements': 'target=8'},
        'target-wave-blur': {'thermal': 'cinematic', 'wave_style': 'rorschach',
                             'wave_width': .14, 'wave_height': 1., 'hud_blur_elements': 'waveform=6,target=6',
                             'hud_theme': 'custom', 'hud_colors': 'waveform=#ff302b,timecode=#ff302b',
                             'target_colors': '#ff302b,#ff302b'},
        'target-hud-blur': {'thermal': 'cinematic', 'hud_blur': 3,
                            'hud_blur_elements': 'waveform=6,target=5,timecode=0'},
        'target-opacity': {'thermal': 'cinematic', 'hud_opacity': .5},
        'target-opacity-elements': {'thermal': 'cinematic', 'wave_style': 'rorschach',
                                    'wave_width': .14, 'wave_height': 1., 'hud_theme': 'custom',
                                    'hud_colors': 'waveform=#ff302b,timecode=#ff302b',
                                    'target_colors': '#ff302b,#ff302b',
                                    'hud_opacity_elements': 'waveform=0.3,target=0.7,timecode=0.9'},
        **{f'waveform-{style}': {'thermal': 'cinematic', 'palette': 'redline', 'wave_style': style,
                               'wave_width': .14, 'wave_height': 1.,
                               **({'wave_width': .09, 'hud_theme': 'custom', 'hud_colors': 'waveform=#FF302B',
                                   'neon': True, 'neon_intensity': 0., 'neon_elements': 'waveform=1.2',
                                   'neon_spread': .4, 'neon_core_whiten': 0.}
                                  if style == 'digital-circuit' else {})}
           for style in ('rorschach', 'rorschach-split', 'rorschach-hollow', 'digital-blocks', 'digital-shards', 'digital-circuit')},
    })
    # Preserve the published image URLs while replacing the old sight geometry.
    result['target-shape-iron-sights']['target_shape'] = 'hollow-cross'
    result['target-opacity-neon'] = {**result['target-opacity-elements'], 'neon': True}
    custom = load_preset(Path(__file__).resolve().parents[1] / 'skills/yautja/assets/presets/tropic-glow.json')
    options = resolve_look(custom.get('base'), custom['settings'])
    options['show_timecode'] = options.pop('timecode')
    result['preset-tropic-glow'] = options
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output-dir', type=Path, default=Path('assets/examples'))
    parser.add_argument('--device', choices=['auto', 'cpu', 'cuda'], default='auto')
    parser.add_argument('--start', type=float, default=.5)
    parser.add_argument('--duration', type=float, default=3.)
    parser.add_argument('--fps', type=int, default=12)
    parser.add_argument('--wave-gain', type=float, default=1., help='Audio waveform gain for these previews')
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--figures', type=Path, help='Saved figure catalog for the target examples')
    parser.add_argument('--target', action='append', default=[], help='Demo figure IDs, repeated or comma-separated')
    parser.add_argument('--only', nargs='+', choices=[*variants(), 'hero'], help='Regenerate selected previews and their large versions only')
    args = parser.parse_args()
    if not math.isfinite(args.wave_gain) or not .01 <= args.wave_gain <= 20:
        parser.error('Waveform gain must be between 0.01 and 20.')
    if not math.isfinite(args.start) or args.start < 0 or not math.isfinite(args.duration) or not .5 <= args.duration <= 10 or not 6 <= args.fps <= 24:
        parser.error('Use a nonnegative start, 0.5–10 seconds, and 6–24 fps.')
    source, destination = args.input.resolve(), args.output_dir.resolve()
    settings = {name: options for name, options in variants().items() if not args.only or name in args.only}
    selected = None
    if any(name.startswith('target-') or name == 'look-murphy' for name in settings):
        if not args.figures or not args.target:
            parser.error('Target examples require --figures and --target from a saved scan.')
        selected = TargetSelection(args.figures, source, args.target)
    include_hero = not args.only or 'hero' in args.only
    settings.update({f'large/{name}': options for name, options in list(settings.items())})
    if include_hero:
        settings['hero'] = {'thermal': 'cinematic'}
    names = [*(name + '.gif' for name in settings), *(['poster.png'] if include_hero else [])]
    if any(source == destination / name for name in names):
        parser.error('The gallery cannot replace its source.')
    if not args.overwrite and any((destination / name).exists() for name in names):
        parser.error('Gallery files exist; use --overwrite to regenerate them.')
    ffmpeg = binary('ffmpeg')
    data, video = probe(source, binary('ffprobe'))
    if video.get('color_transfer') in ('smpte2084', 'arib-std-b67'):
        parser.error('Normalize HDR to SDR with the main converter workflow before building the gallery.')
    width, height = dimensions(video, 640)
    gif_width, gif_height = dimensions(video, 480)
    large_width, large_height = dimensions(video, 960)
    container_start = number(data.get('format', {}).get('start_time'))
    video_start = number(video.get('start_time'), container_start)
    seek = max(0., args.start + video_start - container_start)
    destination.mkdir(parents=True, exist_ok=True)
    resolved_settings = [resolve_look(options.get('look_preset'), options) for options in settings.values()]
    tracker = SemanticTracker(GroundedSegmenter(device=args.device,
                              surfaces=any(o.get('scene_mode') != 'source' for o in resolved_settings)),
                              refine_masks=any((o.get('subject_outline') or o.get('analysis') or o.get('analysis_target') or o.get('subject_code') or o.get('target_mode') == 'auto') and o.get('hud', True) for o in resolved_settings))
    def gallery_options(options):
        resolved = resolve_look(options.get('look_preset'), options)
        if 'timecode' in resolved:
            resolved['show_timecode'] = resolved.pop('timecode')
        return {'verbose': True, 'show_timecode': True, **resolved}

    renderers = {name: Renderer(*( (large_width, large_height) if name.startswith('large/') else
                                  (width, height) if name == 'hero' else (gif_width, gif_height)),
                                **gallery_options(options))
                 for name, options in settings.items()}
    def field_key(renderer):
        return renderer.thermal, renderer.sensor_resolution, renderer.transfer.levels is None

    fields = {field_key(r): Renderer(width, height, thermal=r.thermal, sensor_resolution=r.sensor_resolution,
                                    thermal_levels=None if r.transfer.levels is None else 0).heat_field
              for r in renderers.values() if r.signal.scene_mode != 'source'}
    results = {}
    with tempfile.TemporaryDirectory(prefix='.yautja-gallery-', dir=destination) as directory:
        temp = Path(directory)
        analysis = decoder = None
        count = 0
        try:
            audios = [s for s in data['streams'] if s['codec_type'] == 'audio']
            if audios:
                audio = audios[0]
                pcm = temp / 'analysis.f32'
                run([ffmpeg, '-v', 'error', '-nostdin', '-i', str(source), '-map', f"0:{audio['index']}",
                     '-vn', '-af', audio_filter(AudioAnalysis.rate), '-ar', str(AudioAnalysis.rate),
                     '-c:a', 'pcm_f32le', '-f', 'f32le', str(pcm)])
                analysis = AudioAnalysis(pcm, int(audio.get('channels', 1)),
                                         number(audio.get('start_time'), container_start) - video_start)
            for name in renderers:
                (temp / name).mkdir(parents=True)
            filters = f'setpts=PTS-STARTPTS,fps={args.fps}:eof_action=pass,scale={width}:{height}:flags=lanczos,setsar=1,format=rgb24'
            with (temp / 'decode.log').open('w+b') as log:
                decoder = subprocess.Popen([ffmpeg, '-v', 'error', '-nostdin', '-ss', str(seek), '-i', str(source),
                    '-map', f"0:{video['index']}", '-t', str(args.duration), '-an', '-sn', '-dn',
                    '-vf', filters, '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'], stdout=subprocess.PIPE, stderr=log)
                try:
                    while True:
                        raw = read_frame(decoder.stdout, width * height * 3)
                        if raw is None:
                            break
                        time = count / args.fps
                        frame = Image.frombytes('RGB', (width, height), raw)
                        subjects = tracker.update(frame, time)
                        heat = {mode: field.build(frame, subjects) for mode, field in fields.items()}
                        scaled_heat = {(size, mode): np.asarray(Image.fromarray(value).resize(size, Image.Resampling.BILINEAR))
                                       for size in {(r.width, r.height) for r in renderers.values()}
                                       for mode, value in heat.items()}
                        wave = analysis.waveform(args.start + time, gain=args.wave_gain) if analysis and not analysis.silent else None
                        for name, renderer in renderers.items():
                            # Apply grain, pixels, and scanlines at final GIF size;
                            # downsampling them afterward could erase the effect.
                            targets, shot = selected.at(args.start + time) if selected and (name.removeprefix('large/').startswith('target-') or name.removeprefix('large/') == 'look-murphy') else (None, tracker.scene_cuts + 1)
                            if renderer.signal.scene_mode == 'source':
                                image = renderer.render(frame.resize((renderer.width, renderer.height), Image.Resampling.LANCZOS), time,
                                                        wave, subjects, targets=targets, shot_id=shot)
                            else:
                                image = renderer.render_field(scaled_heat[((renderer.width, renderer.height), field_key(renderer))], time, wave, subjects,
                                                              targets=targets, shot_id=shot)
                            image.save(temp / name / f'{count:04d}.png')
                            if name == 'hero' and count == 0:
                                image.save(temp / 'poster.png')
                        count += 1
                        if count % args.fps == 0:
                            print(f'Rendered {count / args.fps:g}s across {len(settings)} matched examples.', flush=True)
                    if decoder.wait():
                        log.seek(0)
                        raise ConversionError(log.read().decode('utf-8', 'replace')[-3000:])
                finally:
                    stop_process(decoder)
                    decoder.stdout.close()
            if count < 2:
                raise ConversionError('The selected clip has fewer than two frames.')
            for name in settings:
                frames = temp / name
                size = renderers[name].width
                palette = f'scale={size}:-1:flags=lanczos,split[frames][colors];[colors]palettegen=max_colors=128:stats_mode=diff[palette];[frames][palette]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle'
                gif = temp / (name + '.gif')
                run([ffmpeg, '-v', 'error', '-nostdin', '-framerate', str(args.fps), '-i', str(frames / '%04d.png'),
                     '-filter_complex', palette, '-an', '-loop', '0', str(gif)])
                with Image.open(gif) as check:
                    duration = 0
                    for index in range(check.n_frames):
                        check.seek(index)
                        duration += check.info['duration']
                    if check.n_frames < 2 or abs(duration / 1000 - count / args.fps) > .03:
                        raise ConversionError('GIF timing check failed: ' + name)
                    results[name] = {'frames': check.n_frames, 'seconds': duration / 1000,
                                     'size': list(check.size), 'bytes': gif.stat().st_size,
                                     'settings': settings[name], 'colors': renderers[name].colors.report(),
                                     'thermal_transfer': renderers[name].transfer.report()}
                    results[name]['scene'] = renderers[name].signal.report()
                    results[name]['analysis'] = renderers[name].analysis.report(renderers[name].hud)
                    results[name]['geometry'] = renderers[name].geometry.report(renderers[name].hud)
                    results[name]['hud_glyphs'] = renderers[name].hud_glyphs
                    if name.removeprefix('large/').startswith('target-'):
                        if not renderers[name].target_overlay.seen:
                            raise ConversionError('No selected targets appeared in the gallery range: ' + name)
                        results[name]['targets_seen'] = sorted(renderers[name].target_overlay.seen)
            for name in names:
                if not args.overwrite and (destination / name).exists():
                    raise ConversionError('A gallery output appeared during rendering: ' + name)
                (destination / name).parent.mkdir(parents=True, exist_ok=True)
                os.replace(temp / name, destination / name)
        finally:
            if analysis:
                analysis.close()
    print(json.dumps({'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                      'source_start': args.start, 'frames': count, 'fps': args.fps, 'wave_gain': args.wave_gain,
                      'tracking': tracker.report(), 'examples': results}, indent=2))


if __name__ == '__main__':
    main()
