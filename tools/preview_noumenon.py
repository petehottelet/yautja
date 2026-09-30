"""Offline geometric fixture and real rendered Noumenon motion comparison.

No generated imagery or model inference: fixture silhouettes are explicit test
masks. This checks projection and compositing, not detection accuracy.
"""
import argparse
import json
from pathlib import Path
import platform
import subprocess
import time

import numpy as np
from PIL import Image, ImageDraw

from yautja.render import Renderer
from yautja.semantic import Subject


def peak_memory_bytes():
    if platform.system() == 'Windows':
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('faults', wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in ('peak', 'working', 'paged_peak', 'paged',
                                                    'nonpaged_peak', 'nonpaged', 'pagefile', 'pagefile_peak')]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        ok = ctypes.windll.psapi.GetProcessMemoryInfo(wintypes.HANDLE(-1), ctypes.byref(counters), counters.cb)
        return int(counters.peak) if ok else None
    import resource
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(peak * (1 if platform.system() == 'Darwin' else 1024))


def processor_name():
    if platform.system() == 'Windows':
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
            return winreg.QueryValueEx(key, 'ProcessorNameString')[0].strip()
    return platform.processor()


def fixture(size=(960, 540), time=0.):
    w, h = size
    frame = Image.new('RGB', size, (70, 85, 94))
    draw = ImageDraw.Draw(frame)
    scale = np.array(size)
    box = np.array([(.36, .36), (.64, .36), (.64, .64), (.36, .64)]) * scale
    tl, tr, br, bl = [tuple(p) for p in box]
    draw.polygon([(0, h), (w, h), br, bl], fill=(75, 76, 73))
    draw.polygon([(0, 0), (w, 0), tr, tl], fill=(35, 40, 47))
    draw.polygon([tl, tr, br, bl], fill=(82, 82, 78))
    for start, end in zip([(0, 0), (w, 0), (w, h), (0, h)], [tl, tr, br, bl]):
        draw.line([start, end], fill=(180, 180, 175), width=max(1, w // 300))
    draw.line([tl, tr, br, bl, tl], fill=(180, 180, 175), width=max(1, w // 300))
    for i in range(1, 12):
        y = round(h * (.64 + .36 * (i / 12) ** 2))
        draw.line([(0, y), (w, y)], fill=(95, 95, 90), width=max(1, w // 700))
    for x in np.linspace(-w, w * 2, 29):
        edge = .36 * w + (x / w) * .28 * w
        draw.line([(edge, .64 * h), (x, h)], fill=(95, 95, 90), width=max(1, w // 700))
    subjects = []
    for i, cx in enumerate((.425, .5, .575)):
        mask = Image.new('L', size)
        painter = ImageDraw.Draw(mask)
        sway = np.sin(time * .6 + i) * .006
        cx += sway
        def point(x, y):
            return (round((cx + x) * w), round(y * h))
        painter.ellipse([point(-.011, .40), point(.011, .45)], fill=255)
        painter.polygon([point(-.016, .454), point(.016, .454), point(.020, .596), point(-.018, .596)], fill=255)
        for sign in (-1, 1):
            painter.line([point(sign * .010, .585), point(sign * .015, .714)], fill=255, width=max(1, round(w * .012)))
            painter.line([point(sign * .017, .468), point(sign * .026, .595)], fill=255, width=max(1, round(w * .009)))
        frame.paste((183 - i * 16, 180 - i * 14, 170 - i * 10), mask=mask)
        subjects.append(Subject(np.asarray(mask, dtype=np.float32) / 255, 'person', .95, track_id=i + 1))
    return frame, subjects


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--width', type=int, default=960)
    parser.add_argument('--fps', type=int, default=24)
    parser.add_argument('--seconds', type=float, default=8.)
    parser.add_argument('--selection-comparison', action='store_true', help='Compare luminance-only shading with silhouettes 1 and 3 highlighted')
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    size = (args.width, round(args.width * 9 / 16 / 2) * 2)
    paths = [args.output / name for name in ('scene.png', 'comparison.png', 'comparison.mp4', 'benchmark.json')]
    if any(path.exists() for path in paths):
        parser.error('Use a new output directory; preview files already exist')
    started = time.perf_counter()
    options = ({}, {}) if args.selection_comparison else ({'material_mapping': 0.}, {})
    selections = (set(), {1, 3}) if args.selection_comparison else (None, None)
    captions = ['Luminance only', 'Silhouettes 1 and 3 brighter'] if args.selection_comparison else ['Flat mapping', 'Surface mapping']
    renderers = [Renderer(*size, look_preset='noumenon', **settings) for settings in options]
    warmup = time.perf_counter() - started
    times = []
    command = ['ffmpeg', '-v', 'error', '-nostdin', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
               '-s', f'{size[0] * 3}x{size[1]}', '-r', str(args.fps), '-i', 'pipe:0',
               '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '19', '-pix_fmt', 'yuv420p', str(paths[2])]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
        for index in range(round(args.seconds * args.fps)):
            t = index / args.fps
            source, subjects = fixture(size, t)
            begun = time.perf_counter()
            images = [r.render(source, t, subjects=subjects, shot_id=1, material_subjects=selected)
                      for r, selected in zip(renderers, selections)]
            times.append(time.perf_counter() - begun)
            comparison = Image.new('RGB', (size[0] * 3, size[1]))
            for col, (image, caption) in enumerate(zip([source, *images], ['Geometry fixture', *captions])):
                comparison.paste(image, (size[0] * col, 0))
                ImageDraw.Draw(comparison).text((size[0] * col + 12, 12), caption, fill='white', stroke_width=1, stroke_fill='black')
            if index == round(args.fps * min(2, args.seconds / 2)):
                images[-1].save(paths[0])
                comparison.save(paths[1])
            encoder.stdin.write(comparison.tobytes())
        encoder.stdin.close()
        if encoder.wait():
            raise RuntimeError('Preview encoding failed')
    report = {'fixture': 'three explicit silhouette masks; no learned segmentation', 'hardware': processor_name(),
              'comparison': captions,
              'size': size, 'fps': args.fps, 'frames': len(times), 'warmup_seconds': warmup,
              'peak_process_memory_bytes': peak_memory_bytes(), 'segmentation_seconds': 0.,
              'paired_frame_median_seconds': float(np.median(times)), 'paired_frame_p95_seconds': float(np.percentile(times, 95)),
              'elapsed_seconds': time.perf_counter() - started, 'renders': [r.scene_material.report() for r in renderers]}
    paths[3].write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
