"""Render one local Brand New Day GIF using cached segmentation when available."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from PIL import Image

from yautja.cli import binary, dimensions, probe, read_frame, run, stop_process
from yautja.figures import FigureCatalog, fingerprint
from yautja.render import Renderer
from yautja.semantic import GroundedSegmenter, SemanticTracker, Subject
from yautja.typography import FONT_FILES


def capture(args, cache):
    _, video = probe(args.input, binary('ffprobe'))
    width, height = dimensions(video, args.max_size)
    tracker = SemanticTracker(GroundedSegmenter(device=args.device), .5, refine_masks=True)
    catalog = FigureCatalog(args.input, start=args.start, fps=args.fps)
    command = [binary('ffmpeg'), '-v', 'error', '-nostdin', '-ss', str(args.start), '-i', str(args.input),
               '-t', str(args.duration), '-an', '-vf', f'fps={args.fps},scale={width}:{height}',
               '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1']
    metadata = []
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile() as log, subprocess.Popen(command, stdout=subprocess.PIPE, stderr=log) as decoder:
        try:
            while True:
                raw = read_frame(decoder.stdout, width*height*3)
                if raw is None:
                    break
                i = len(metadata)
                time = i / args.fps
                frame = Image.frombytes('RGB', (width,height), raw)
                subjects = tracker.update(frame, time)
                shot = tracker.scene_cuts + 1
                catalog.add(frame, args.start+time, subjects, shot)
                frame.save(cache/f'{i:04d}.png')
                np.savez_compressed(cache/f'{i:04d}.npz', **{f'mask{j}': subject.mask for j, subject in enumerate(subjects)},
                                    **{f'binary{j}': subject.binary_mask for j, subject in enumerate(subjects) if subject.binary_mask is not None})
                metadata.append({'time':time, 'shot':shot, 'subjects':[
                    {'label':subject.label, 'score':float(subject.score), 'track_id':subject.track_id,
                     'opacity':float(subject.opacity)} for subject in subjects]})
                if i % args.fps == 0:
                    print(f'Segmented {time:.1f}s; scene {shot}; {len(subjects)} objects', flush=True)
            if decoder.wait():
                raise ValueError('Preview decoder failed')
        finally:
            stop_process(decoder)
    if len(metadata) < 2:
        raise ValueError('Preview needs at least two frames')
    (cache/'frames.json').write_text(json.dumps(metadata), encoding='utf-8')
    (cache/'figures.json').write_text(json.dumps(catalog.data), encoding='utf-8')
    (cache/'figures.html').write_text(catalog.contact_sheet(), encoding='utf-8')
    return metadata, (width,height)


def gif(frames, destination, fps):
    palette = 'split[f][c];[c]palettegen=max_colors=256:stats_mode=diff[p];[f][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle'
    run([binary('ffmpeg'), '-v', 'error', '-nostdin', '-framerate', str(fps), '-i', str(frames/'%04d.png'),
         '-filter_complex', palette, '-an', '-loop', '0', str(destination)])
    with Image.open(destination) as image:
        duration = 0
        for i in range(image.n_frames):
            image.seek(i)
            duration += image.info.get('duration', 0)
        return {'frames':image.n_frames, 'duration':duration/1000, 'size':image.size}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--start', type=float, default=0.)
    p.add_argument('--duration', type=float, default=6.)
    p.add_argument('--fps', type=int, default=12)
    p.add_argument('--max-size', type=int, default=960)
    p.add_argument('--device', choices=('auto','cpu','cuda'), default='auto')
    p.add_argument('--cache', type=Path, help='Reuse this matching segmentation cache if present')
    p.add_argument('--hud-font', choices=FONT_FILES, help='Override the preset lettering')
    args = p.parse_args()
    if args.output.exists():
        p.error('Choose a new output directory to preserve earlier previews')
    if not 1 <= args.fps <= 30 or not 0 < args.duration <= 15 or args.start < 0 or not 320 <= args.max_size <= 1920:
        p.error('Use 1-30 fps, up to 15 seconds, nonnegative start and a 320-1920 longest edge')
    args.output.mkdir(parents=True)
    cache = args.cache or args.output/'cache'
    signature = {'sha256':fingerprint(args.input), 'start':args.start, 'duration':args.duration,
                 'fps':args.fps, 'max_size':args.max_size}
    if (cache/'signature.json').exists():
        if json.loads((cache/'signature.json').read_text()) != signature:
            p.error('Cache does not match this source and preview timing')
        metadata = json.loads((cache/'frames.json').read_text())
        with Image.open(cache/'0000.png') as image:
            size = image.size
    else:
        metadata, size = capture(args,cache)
        (cache/'signature.json').write_text(json.dumps(signature),encoding='utf-8')
    overrides = {'hud_font':args.hud_font} if args.hud_font else {}
    renderer = Renderer(*size,look_preset='brand-new-day',**overrides)
    with tempfile.TemporaryDirectory(prefix='.preview-',dir=args.output) as folder:
        folder = Path(folder)
        for i,record in enumerate(metadata):
            with Image.open(cache/f'{i:04d}.png') as original:
                source = original.convert('RGB')
            with np.load(cache/f'{i:04d}.npz',allow_pickle=False) as masks:
                subjects = [Subject(masks[f'mask{j}'],**data,
                                    binary_mask=masks[f'binary{j}'] if f'binary{j}' in masks else None)
                            for j,data in enumerate(record['subjects'])]
            frame = renderer.render(source,record['time'],subjects=subjects,shot_id=record['shot'])
            frame.save(folder/f'{i:04d}.png')
            if i == min(12,len(metadata)-1):
                frame.save(args.output/'brand-new-day.png')
            if i % args.fps == 0:
                print(f'Rendered {record["time"]:.1f}s',flush=True)
        result = gif(folder,args.output/'brand-new-day.gif',args.fps)
        if result['frames'] != len(metadata) or abs(result['duration']-len(metadata)/args.fps) > .04:
            raise ValueError('Preview GIF timing or frame count mismatch')
    settings = {**renderer.day.report(),**renderer.typography.report(),
                'scanlines':renderer.scanlines,'crt_strength':renderer.crt_strength,'crt_bleed':renderer.display.crt_bleed,
                'object_outline_color':renderer.hud_colors['object-outline'], 'gif':result}
    (args.output/'settings.json').write_text(json.dumps(settings,indent=2),encoding='utf-8')
    (args.output/'index.html').write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        '<title>Brand New Day preview</title><style>body{background:#e9e6df;color:#171713;font:16px system-ui;'
        'margin:32px auto;max-width:1100px;padding:0 24px}h1{font-size:38px}img{display:block;width:100%;height:auto}a{color:inherit}</style>'
        '<h1>Brand New Day</h1><p>Glowing chunky amber contours, 35% amber fill, and stepped black backing fitted to each readout row and graphic. CRT scanlines and phosphor bleed cover the entire scene.</p>'
        '<a href="brand-new-day.gif"><img src="brand-new-day.gif" alt="Chunky amber silhouettes and glowing CRT readout"></a>'
        f'<p>Contour blocks: {renderer.day.object_outline_block:g} reference pixels; line width: {renderer.day.object_outline_width:g}. One outline style per object. Map and terrain are simulated.</p></html>',
        encoding='utf-8')
    print(f'Verified one GIF: {result["frames"]} frames, {result["duration"]:.2f}s',flush=True)


if __name__ == '__main__':
    main()
