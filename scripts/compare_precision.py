#!/usr/bin/env python3
"""Compare cached-model CUDA fp32/bf16 masks on sampled frames; no quality ground truth."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image

from benchmark import fingerprint
from runtime import validate_execution
from semantic import GroundedSegmenter, mask_iou
from yautja import binary


def compare(reference, candidate):
    pairs = sorted(((mask_iou(a.mask, b.mask), i, j)
                    for i, a in enumerate(reference) for j, b in enumerate(candidate) if a.label == b.label), reverse=True)
    used_a, used_b, overlaps = set(), set(), []
    for overlap, i, j in pairs:
        if overlap < .15 or i in used_a or j in used_b:
            continue
        used_a.add(i)
        used_b.add(j)
        overlaps.append(overlap)
    return {'reference_subjects': len(reference), 'candidate_subjects': len(candidate), 'matched_mask_ious': overlaps,
            'unmatched_reference': len(reference) - len(used_a), 'unmatched_candidate': len(candidate) - len(used_b)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--times', type=float, nargs='+', default=[0, 2, 4, 6, 8])
    args = parser.parse_args(argv)
    if not args.input.is_file() or any(not np.isfinite(t) or t < 0 for t in args.times):
        parser.error('provide an existing local video and nonnegative finite sample times')
    model = GroundedSegmenter(device='cuda', precision='fp32')
    validate_execution(model.torch, 'cuda', 'bf16')
    results = []
    for seconds in args.times:
        import io
        raw = subprocess.check_output([binary('ffmpeg'), '-v', 'error', '-ss', str(seconds), '-i', str(args.input),
                                       '-frames:v', '1', '-vf', 'scale=640:640:force_original_aspect_ratio=decrease',
                                       '-f', 'image2pipe', '-c:v', 'png', 'pipe:1'])
        frame = Image.open(io.BytesIO(raw)).convert('RGB')
        model.precision = 'fp32'
        reference = model.detect(frame)
        model.precision = 'bf16'
        candidate = model.detect(frame)
        results.append({'seconds': seconds, **compare(reference, candidate)})
        print(f'Compared masks at {seconds:g}s', file=sys.stderr, flush=True)
    print(json.dumps({'source_sha256': fingerprint(args.input), 'reference': 'cuda/fp32', 'candidate': 'cuda/bf16',
                      'note': 'Agreement between model outputs is not labeled accuracy or a temporal tracking evaluation.',
                      'samples': results}, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
