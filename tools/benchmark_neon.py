"""Compare warmed CPU frame rendering with fixed 1080p heat fields and moving HUD."""
import argparse
import json
import platform
import statistics
import time

import numpy as np
from yautja.render import Renderer
from yautja.semantic import Subject


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames', type=int, default=24)
    parser.add_argument('--runs', type=int, default=3)
    args = parser.parse_args()
    if min(args.frames, args.runs) < 1:
        parser.error('frames and runs must be positive')
    field = np.tile(np.linspace(30, 220, 1920, dtype=np.uint8), (1080, 1))
    mask = np.zeros(field.shape, np.float32)
    mask[250:950, 780:1150] = 1
    subject = Subject(mask, 'person', .95, track_id=1)
    samples = {False: [], True: []}
    for run in range(args.runs):
        for enabled in (False, True) if run % 2 == 0 else (True, False):
            renderer = Renderer(1920, 1080, neon=enabled, show_timecode=True, verbose=True, palette='abyss')
            for index in range(args.frames + 5):
                t = index / 24
                shift = .01 * np.sin(t)
                target = [{'id': 'one', 'bbox': [.4 + shift, .23, .6 + shift, .88]}]
                start = time.perf_counter()
                renderer.render_field(field, t, subjects=[subject], targets=target, target_static=True)
                elapsed = time.perf_counter() - start
                if index >= 5:
                    samples[enabled].append(elapsed * 1000)
    off, on = [statistics.median(samples[enabled]) for enabled in (False, True)]
    print(json.dumps({'platform': platform.platform(), 'python': platform.python_version(),
                      'size': [1920, 1080], 'frames_per_mode': len(samples[False]),
                      'scope': 'render_field: Classic fixed heat field, moving locked target, waveform, timecode and one callout; no inference, decoding or encoding',
                      'off_median_ms': off, 'neon_median_ms': on, 'overhead_percent': (on / off - 1) * 100}, indent=2))


if __name__ == '__main__':
    main()
