"""Inkblot and block-grid transformations of waveform energy."""
import math

import numpy as np
from PIL import Image, ImageDraw

RORSCHACH_STYLES = ('rorschach', 'rorschach-split', 'rorschach-hollow')
DIGITAL_STYLES = ('digital-blocks', 'digital-shards', 'digital-circuit')
WAVE_STYLES = ('trace', *RORSCHACH_STYLES, *DIGITAL_STYLES)


def inkblot_mask(width, height, signal, time, *, style='rorschach', detail=.6, seed=42):
    """Return an inkblot or digital L mask; zero input produces zero ink."""
    if style in DIGITAL_STYLES:
        return digital_mask(width, height, signal, time, style=style, detail=detail, seed=seed)
    if style not in RORSCHACH_STYLES:
        raise ValueError('Choose a Rorschach waveform style.')
    # Supersample for antialiasing while retaining short, pointed audio peaks.
    rows, columns = height * 2, width * 2
    y = np.linspace(0, 1, rows)
    values = np.clip(np.abs(np.nan_to_num(np.asarray(signal, np.float32))), 0, 1)
    peaks = np.interp(y, np.linspace(0, 1, len(values)), values)
    radius = max(1, round(rows * (.018 - detail * .012)))
    kernel_x = np.arange(-radius * 3, radius * 3 + 1)
    kernel = np.exp(-.5 * (kernel_x / radius) ** 2)
    kernel /= kernel.sum()
    envelope = np.convolve(np.pad(peaks, len(kernel) // 2, mode='edge'), kernel, mode='valid')
    phase = (seed % 997) / 997 * math.tau
    frequency = 22 + detail * 55
    # Slowly drifting, incommensurate lobes avoid a repeated stack of identical cells.
    broad = np.sin(y * frequency + time * 1.1 + phase)
    fine = np.sin(y * frequency * 2.31 - time * .7 + phase * 1.3)
    profile = np.clip(.52 + .29 * broad + .16 * fine, .05, 1)
    # Compress dynamic range so quiet ambience still makes broad inkblots,
    # without normalizing each frame or turning actual silence into movement.
    drive = np.clip(envelope * 4, 0, 1) ** .25
    outer = drive * (.16 + .84 * profile)
    # Preserve local attacks and troughs instead of smoothing them into lobes.
    # Linear interpolation makes pointed teeth at the actual waveform bins;
    # their height follows the local peak/envelope contrast, not random noise.
    contrast = np.divide(peaks, envelope, out=np.ones_like(peaks), where=envelope > 1e-8)
    teeth = np.clip(contrast - 1, -1, 1.5)
    # Lift small audio attacks, just as the broad envelope lifts quiet ambience.
    teeth = np.sign(teeth) * np.sqrt(np.abs(teeth))
    outer = np.clip(outer * (1 + .8 * detail * teeth), 0, 1)
    if style == 'rorschach-split':
        outer *= np.clip((profile - .28) * 4, 0, 1)
    x = np.abs(np.linspace(-1, 1, columns))[None, :]
    ink = np.clip((outer[:, None] - x) * columns / 2, 0, 1)
    if style == 'rorschach-hollow':
        pockets = np.clip((profile - .35) * 4, 0, 1)
        inner = outer * (.30 + .28 * (fine + 1) / 2) * pockets
        ink *= 1 - np.clip((inner[:, None] - x) * columns / 2, 0, 1)
    shading = .70 + .30 * np.clip(1 - x / np.maximum(.01, outer[:, None]), 0, 1)
    mask = Image.fromarray(np.uint8(np.clip(ink * shading * 255, 0, 255)))
    return mask.resize((width, height), Image.Resampling.LANCZOS)


def digital_mask(width, height, signal, time, *, style, detail=.6, seed=42):
    """Audio controls block width or the height of three segmented LED columns."""
    if style not in DIGITAL_STYLES:
        raise ValueError('Choose a digital waveform style.')
    if style == 'digital-circuit':
        return vocoder_mask(width, height, signal, detail=detail)
    pixel = max(2, round(width / (14 + detail * 18)))
    columns = max(5, math.ceil(width / pixel))
    rows = max(2, math.ceil(height / pixel))
    canvas = Image.new('L', (columns, rows))
    values = np.clip(np.abs(np.nan_to_num(np.asarray(signal, np.float32))), 0, 1)
    if not len(values) or not values.max():
        return Image.new('L', (width, height))
    bins = np.linspace(0, len(values), rows + 1)
    energy = np.array([values[int(lo):max(int(lo) + 1, math.ceil(hi))].max() for lo, hi in zip(bins, bins[1:])])
    drive = np.clip(energy * 4, 0, 1) ** .35
    center, half = columns // 2, (columns - 1) // 2
    rng = np.random.default_rng((seed + int(time * 5) * 104729) & 0xffffffff)
    draw = ImageDraw.Draw(canvas)
    for row in range(0, rows, 3):
        strength = float(drive[row:row + 3].max())
        if strength <= 0:
            continue
        radius = max(1, round(half * strength))
        if style == 'digital-blocks':
            # Broad bit-crushed slabs, alternating widths, with square cutouts.
            width_cells = max(1, radius - (row // 3 % 3))
            draw.rectangle((center - width_cells, row, center + width_cells, row + 2), fill=235)
            if row % 12 == 0 and width_cells > 3:
                draw.rectangle((center - 1, row, center + 1, row), fill=0)
            if row % 9 == 0:
                draw.rectangle((center - width_cells, row + 2, center + width_cells, row + 2), fill=0)
        elif style == 'digital-shards':
            # Separated, unequal data packets displaced across the waveform axis.
            for sign in (-1, 1):
                span = max(1, round(radius * rng.uniform(.25, .65)))
                offset = max(1, radius - span + 1)
                left = center + offset if sign == 1 else center - offset - span + 1
                draw.rectangle((left, row, left + span - 1, row + int(rng.integers(0, 2))),
                               fill=int(rng.integers(175, 256)))
            if row % 12 == 3:
                draw.rectangle((center - 1, row, center, row + 1), fill=255)
    # Exact square raster cells; no bilinear smoothing or diagonal stair blur.
    return canvas.resize((columns * pixel, rows * pixel), Image.Resampling.NEAREST).crop((0, 0, width, height))


def vocoder_mask(width, height, signal, *, detail=.6):
    """Three LED stacks light outward from the middle, led by the center stack."""
    mask = Image.new('L', (width, height))
    values = np.clip(np.abs(np.nan_to_num(np.asarray(signal, np.float32))), 0, 1)
    if not len(values) or not values.max():
        return mask
    # Different trailing windows give the flanking columns their own audio
    # response. No random animation is added to a constant or silent signal.
    levels = []
    for fraction in (.55, .3, .8):
        window = values[-max(1, round(len(values) * fraction)):]
        energy = .65 * float(np.sqrt(np.mean(window ** 2))) + .35 * float(window.max())
        levels.append(float(np.clip(energy * 6, 0, 1) ** .3))
    levels = (levels[0] * .68, max(levels), levels[2] * .72)
    segments = 2 * round(10 + detail * 6)
    pitch = height / segments
    bar_height = max(1, round(pitch * .65))
    bar_width = max(1, round(width * .23))
    gap = max(2, round(width * .1))
    left = (width - (3 * bar_width + 2 * gap)) // 2
    draw = ImageDraw.Draw(mask)
    for col, level in enumerate(levels):
        x = left + col * (bar_width + gap)
        for row in range(segments):
            distance = (abs(row - (segments - 1) / 2) + .5) / (segments / 2)
            activation = float(np.clip((level - distance) * segments / 2 + 1, 0, 1))
            if not activation:
                continue
            brightness = .65 + .35 * max(0., 1 - distance / max(level, 1e-8))
            y = round((row + .5) * pitch - bar_height / 2)
            draw.rectangle((x, y, x + bar_width - 1, y + bar_height - 1),
                           fill=round(255 * activation * brightness))
    return mask
