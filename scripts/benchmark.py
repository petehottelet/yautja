#!/usr/bin/env python3
"""Run comparable, cached-model conversions in fresh processes; never download models."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from yautja import binary


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--python', default=sys.executable, help='Interpreter for the environment under test')
    parser.add_argument('--device', choices=['cpu', 'cuda'], required=True)
    parser.add_argument('--precision', choices=['fp32', 'bf16'], default='fp32')
    parser.add_argument('--output-dir', type=Path, default=Path('outputs/benchmarks'))
    parser.add_argument('--runs', type=int, default=2, help='Fresh-process runs; later runs may benefit from the OS file cache')
    parser.add_argument('--max-size', type=int, default=1280)
    parser.add_argument('--fps', type=float, default=24)
    parser.add_argument('--start', type=float, default=0)
    parser.add_argument('--duration', type=float)
    args = parser.parse_args(argv)
    if not args.input.is_file():
        parser.error('input must be an existing local video')
    if not 1 <= args.runs <= 20:
        parser.error('--runs must be between 1 and 20')
    ffmpeg, ffprobe = binary('ffmpeg'), binary('ffprobe')
    source = args.input.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix=f'{args.device}-{args.precision}-', dir=args.output_dir)).resolve()
    record = {'schema_version': 1, 'source_sha256': fingerprint(source), 'source_bytes': source.stat().st_size,
              'cache_policy': 'Pinned weights must already be cached. Every run loads models in a fresh process. '
                              'OS disk cache is uncontrolled; first run is not a guaranteed cold-cache measurement.',
              'runs': []}
    status = 0
    for index in range(1, args.runs + 1):
        output = directory / f'run-{index}.mp4'
        command = [str(args.python), str(Path(__file__).with_name('yautja.py')), str(source), str(output),
                   '--thermal', 'semantic', '--device', args.device, '--precision', args.precision,
                   '--max-size', str(args.max_size), '--fps', str(args.fps), '--start', str(args.start),
                   '--verbose', '--timecode']
        if args.duration is not None:
            command += ['--duration', str(args.duration)]
        print(f'Benchmark {index}/{args.runs}: {output}', file=sys.stderr, flush=True)
        started = time.perf_counter()
        entry = {'index': index, 'command': command}
        with (directory / f'run-{index}.log').open('w', encoding='utf-8') as log:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=log, text=True, encoding='utf-8')
        entry.update(wall_seconds=round(time.perf_counter() - started, 3), exit_code=result.returncode)
        (directory / f'run-{index}.stdout.json').write_text(result.stdout, encoding='utf-8')
        if result.returncode == 0:
            try:
                entry['report'] = json.loads(result.stdout)
                entry['probe'] = json.loads(subprocess.check_output(
                    [ffprobe, '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', str(output)]))
                subprocess.run([ffmpeg, '-v', 'error', '-xerror', '-i', str(output), '-f', 'null', '-'], check=True)
                video = next(s for s in entry['probe']['streams'] if s['codec_type'] == 'video')
                report = entry['report']
                audio = next((s for s in entry['probe']['streams'] if s['codec_type'] == 'audio'), None)
                entry['verified'] = (int(video['nb_read_frames']) == report['frames']
                                     and (video['width'], video['height']) == (report['width'], report['height'])
                                     and abs(float(video['duration']) - report['duration']) <= 1 / report['fps']
                                     and bool(audio) == report['audio_preserved']
                                     and (not audio or abs(float(audio['duration']) - report['duration']) < .1))
                if not entry['verified']:
                    raise ValueError('Decoded frame coverage, dimensions, or audio timing differs from the conversion report')
            except (ValueError, KeyError, StopIteration, subprocess.CalledProcessError) as exc:
                entry.update(verified=False, error=str(exc))
                status = 1
        else:
            status = 1
        record['runs'].append(entry)
        # Each finished run survives an interrupted subsequent run.
        pending = directory / 'benchmark.json.tmp'
        pending.write_text(json.dumps(record, indent=2), encoding='utf-8')
        pending.replace(directory / 'benchmark.json')
        if status:
            break
    print(directory / 'benchmark.json')
    return status


if __name__ == '__main__':
    sys.exit(main())
