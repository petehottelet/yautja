"""Shot-local figure catalogs, thumbnails, and deterministic target selection."""
import base64
from bisect import bisect_right
import hashlib
import html
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

MAX_SAMPLES = 500_000


def fingerprint(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def subject_box(subject):
    yy, xx = np.where(subject.mask > .5)
    if not len(xx):
        return None
    height, width = subject.mask.shape
    return [float(xx.min() / width), float(yy.min() / height),
            float((xx.max() + 1) / width), float((yy.max() + 1) / height)]


class FigureCatalog:
    def __init__(self, source, start=0., fps=24.):
        self.data = {'schema_version': 1, 'source': {'name': Path(source).name, 'sha256': fingerprint(source)},
                     'start': start, 'end': start, 'fps': fps, 'shots': []}
        self.lookup = {}
        self.samples = 0

    def add(self, frame, time, subjects, shot_id):
        shots = self.data['shots']
        key = f'S{shot_id:03d}'
        if not shots or shots[-1]['id'] != key:
            if shots:
                shots[-1]['end'] = time
            shots.append({'id': key, 'start': time, 'end': time, 'figures': []})
        shot = shots[-1]
        end = time + 1 / self.data['fps']
        shot['end'] = self.data['end'] = end
        for subject in sorted(subjects, key=lambda s: (subject_box(s) or [2])[0]):
            box = subject_box(subject)
            if box is None or subject.opacity <= .05:
                continue
            track = (key, subject.track_id)
            if track not in self.lookup:
                identifier = f"{key}-F{len(shot['figures']) + 1:03d}"
                figure = {'id': identifier, 'category': subject.label, 'confidence': float(subject.score),
                          'first_seen': time, 'last_seen': time, 'samples': []}
                x0, y0, x1, y1 = box
                crop = frame.crop((max(0, int(x0 * frame.width) - 12), max(0, int(y0 * frame.height) - 12),
                                   min(frame.width, math.ceil(x1 * frame.width) + 12), min(frame.height, math.ceil(y1 * frame.height) + 12)))
                crop.thumbnail((240, 200))
                buffer = io.BytesIO()
                crop.save(buffer, format='JPEG', quality=80)
                figure['thumbnail_jpeg'] = base64.b64encode(buffer.getvalue()).decode('ascii')
                self.lookup[track] = figure
                shot['figures'].append(figure)
            figure = self.lookup[track]
            figure['last_seen'] = time
            figure['samples'].append([round(time, 6), *[round(v, 6) for v in box], round(float(subject.opacity), 4)])
            self.samples += 1
            if self.samples > MAX_SAMPLES:
                raise ValueError('Figure catalog is too large; scan shorter sections with --start/--duration.')

    def summary(self):
        return {'source': self.data['source'], 'start': self.data['start'], 'end': self.data['end'],
                'shots': [{**shot, 'figures': [{k: v for k, v in figure.items() if k not in ('samples', 'thumbnail_jpeg')}
                                             for figure in shot['figures']]} for shot in self.data['shots']]}

    def contact_sheet(self):
        sections = []
        for shot in self.data['shots']:
            cards = ''.join(f'<article><img src="data:image/jpeg;base64,{f["thumbnail_jpeg"]}" alt="{html.escape(f["id"])}">'
                            f'<h3>{html.escape(f["id"])}</h3><p>{html.escape(f["category"])} · {f["first_seen"]:.2f}–{f["last_seen"]:.2f}s</p></article>'
                            for f in shot['figures'])
            sections.append(f'<section><h2>{shot["id"]} · {shot["start"]:.2f}–{shot["end"]:.2f}s</h2><div>{cards or "No figures detected."}</div></section>')
        return ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
                '<title>Yautja figure selection</title><style>body{background:#0e1118;color:#edf2ff;font:16px system-ui;margin:32px;max-width:1200px}'
                'h1{color:#ff4349}section{margin:36px 0}section>div{display:flex;gap:16px;flex-wrap:wrap}article{background:#1a202c;padding:16px;border-radius:8px}'
                'img{width:240px;height:200px;object-fit:contain}h3{margin-bottom:4px}p{color:#bac4d4}</style>'
                '<h1>Choose a figure</h1><p>Use a figure ID with <code>--target</code>. IDs are local to each detected shot; a reappearing figure can receive a new ID.</p>'
                + ''.join(sections) + '</html>')


class TargetSelection:
    def __init__(self, path, source, identifiers):
        path = Path(path)
        if path.stat().st_size > 128 * 1024 * 1024:
            raise ValueError('Figure catalog exceeds the 128 MB limit.')
        self.data = json.loads(path.read_text(encoding='utf-8'))
        try:
            self._validate()
        except (KeyError, TypeError, IndexError, AttributeError, ValueError) as exc:
            raise ValueError('Invalid figure catalog; create a new one with --list-figures.') from exc
        if self.data['source']['sha256'] != fingerprint(source):
            raise ValueError('Figure catalog belongs to a different source file; scan this input first.')
        self.selected = set(part.strip().upper() for value in identifiers for part in value.split(','))
        unknown = self.selected - set(self.figures)
        if not self.selected or unknown:
            raise ValueError('Unknown target IDs: ' + ', '.join(sorted(unknown)) + '. Choose IDs from the figure catalog.')
        if len(self.selected) > 16:
            raise ValueError('Select at most 16 targets per render.')

    def _validate(self):
        def require(condition):
            if not condition:
                raise ValueError('Invalid figure catalog')

        d = self.data
        require(d['schema_version'] == 1 and re.fullmatch('[0-9a-f]{64}', d['source']['sha256']))
        require(all(isinstance(d[k], (int, float)) and math.isfinite(d[k]) for k in ('start', 'end', 'fps')))
        require(0 <= d['start'] < d['end'] and 1 <= d['fps'] <= 120)
        require(isinstance(d['shots'], list))
        self.figures, self.times = {}, {}
        last_end, count = d['start'], 0
        seen = set()
        for shot in d['shots']:
            require(re.fullmatch(r'S\d{3,}', shot['id']) and shot['id'] not in seen)
            seen.add(shot['id'])
            require(all(isinstance(shot[k], (int, float)) and math.isfinite(shot[k]) for k in ('start', 'end')))
            require(last_end <= shot['start'] < shot['end'] <= d['end'] + 1e-6)
            require(isinstance(shot['figures'], list))
            last_end = shot['end']
            for figure in shot['figures']:
                identifier = figure['id']
                require(re.fullmatch(re.escape(shot['id']) + r'-F\d{3,}', identifier) and identifier not in self.figures)
                previous = -math.inf
                require(isinstance(figure['samples'], list) and figure['samples'])
                for sample in figure['samples']:
                    require(len(sample) == 6 and all(isinstance(v, (int, float)) and math.isfinite(v) for v in sample))
                    t, x0, y0, x1, y1, alpha = sample
                    require(shot['start'] - 1e-6 <= t < shot['end'] and t > previous)
                    require(0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1 and 0 <= alpha <= 1)
                    previous = t
                    count += 1
                    require(count <= MAX_SAMPLES)
                self.figures[identifier] = figure
                self.times[identifier] = [s[0] for s in figure['samples']]

    def at(self, time):
        shot = next((s for s in self.data['shots'] if s['start'] <= time < s['end']), None)
        if shot is None:
            return [], None
        result = []
        interval = 1 / self.data['fps']
        for identifier in sorted(self.selected):
            if not identifier.startswith(shot['id'] + '-'):
                continue
            figure, times = self.figures[identifier], self.times[identifier]
            index = bisect_right(times, time + 1e-6) - 1
            if index < 0:
                continue
            a = figure['samples'][index]
            if time - a[0] > interval + 1e-5:
                continue
            box, alpha = a[1:5], a[5]
            if index + 1 < len(times):
                b = figure['samples'][index + 1]
                if b[0] - a[0] <= interval * 1.5:
                    fraction = min(1., max(0., (time - a[0]) / (b[0] - a[0])))
                    box = [x + (y - x) * fraction for x, y in zip(box, b[1:5])]
                    alpha += (b[5] - alpha) * fraction
            result.append({'id': identifier, 'bbox': box, 'opacity': alpha})
        return result, shot['id']


def scan(args):
    from .cli import (binary, dimensions, media_kind, number, output_paths, probe,
                      read_frame, semantic_tracker, stop_process, load_image)
    from fractions import Fraction
    if args.output is None:
        args.output = args.input.with_name(args.input.stem + '-figures.json')
    source, output = output_paths(args, '.json')
    sheet = output.with_suffix('.html')
    if sheet.resolve() == source:
        raise ValueError('Contact sheet cannot replace the input file.')
    if sheet.exists() and not args.overwrite:
        raise ValueError('Contact sheet already exists; choose another output name or use --overwrite.')
    image_mode = media_kind(args) == 'image'
    if image_mode and (args.start or args.duration is not None or args.fps is not None):
        raise ValueError('Still-image scans do not use --start, --duration or --fps.')
    fps = 1. if image_mode else (args.fps or 24.)
    catalog = FigureCatalog(source, args.start, fps)
    tracker = semantic_tracker(args)
    decoder = None
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.yautja-scan-', dir=output.parent) as folder:
        temp = Path(folder)
        if image_mode:
            frame, _, _ = load_image(source, args.max_size)
            catalog.add(frame, 0., tracker.update(frame, 0.), 1)
        else:
            ffmpeg, ffprobe = binary('ffmpeg'), binary('ffprobe')
            data, video = probe(source, ffprobe)
            width, height = dimensions(video, args.max_size)
            container_start = number(data.get('format', {}).get('start_time'))
            video_start = number(video.get('start_time'), container_start)
            seek = max(0., args.start + video_start - container_start)
            filters = ['setpts=PTS-STARTPTS', f'fps={Fraction(fps).limit_denominator(1001000)}:eof_action=pass']
            if video.get('color_transfer') in ('smpte2084', 'arib-std-b67'):
                filters += ['zscale=t=linear:npl=100', 'format=gbrpf32le', 'tonemap=hable:desat=0', 'zscale=p=bt709:t=bt709:m=bt709:r=tv']
            filters += [f'scale={width}:{height}:flags=lanczos', 'setsar=1', 'format=rgb24']
            command = [ffmpeg, '-v', 'error', '-nostdin', '-ss', str(seek), '-i', str(source), '-map', f"0:{video['index']}"]
            if args.duration:
                command += ['-t', str(args.duration)]
            command += ['-an', '-sn', '-dn', '-vf', ','.join(filters), '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1']
            with (temp / 'decode.log').open('w+b') as log:
                try:
                    decoder = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=log)
                    count = 0
                    while True:
                        raw = read_frame(decoder.stdout, width * height * 3)
                        if raw is None:
                            break
                        frame = Image.frombytes('RGB', (width, height), raw)
                        time = count / fps
                        subjects = tracker.update(frame, time)
                        catalog.add(frame, args.start + time, subjects, tracker.scene_cuts + 1)
                        count += 1
                        if count % max(1, round(fps * 2)) == 0:
                            print(f'Listed figures through {args.start + time:.1f}s', file=sys.stderr, flush=True)
                    if decoder.wait() or not count:
                        log.seek(0)
                        raise ValueError('Figure scan could not decode the selected range. ' + log.read().decode('utf-8', 'replace')[-2000:])
                finally:
                    if decoder:
                        stop_process(decoder)
                        decoder.stdout.close()
        (temp / 'catalog.json').write_text(json.dumps(catalog.data, separators=(',', ':')), encoding='utf-8')
        (temp / 'contact.html').write_text(catalog.contact_sheet(), encoding='utf-8')
        if not args.overwrite and (output.exists() or sheet.exists()):
            raise ValueError('A scan output appeared during processing; refusing to overwrite it.')
        os.replace(temp / 'contact.html', sheet)
        os.replace(temp / 'catalog.json', output)
    report = {'catalog': str(output), 'contact_sheet': str(sheet), **catalog.summary()}
    print(json.dumps(report, indent=2))
    return report
