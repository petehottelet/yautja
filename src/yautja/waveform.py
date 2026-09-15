"""Inkblot and block-grid transformations of waveform energy."""
import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw

RORSCHACH_STYLES = ('rorschach', 'rorschach-split', 'rorschach-hollow')
DIGITAL_STYLES = ('digital-blocks', 'digital-shards', 'digital-circuit')
WAVE_STYLES = ('trace', *RORSCHACH_STYLES, *DIGITAL_STYLES)


def resolve_display(style, display):
    if display is not None and display not in ('plain', 'led'):
        raise ValueError('--wave-display must be plain or led')
    return display or ('led' if style == 'digital-circuit' else 'plain')


def led_device(lit_mask, *, detail=.6):
    """Max-pool any waveform into lit cells, a rounded plate and idle cells."""
    width, height = lit_mask.size
    ss = 3
    layers = [Image.new('L', (width*ss, height*ss)) for _ in range(3)]
    lit, plate, idle = map(ImageDraw.Draw, layers)
    pitch = max(2, round(width / (14 + detail * 18)))
    pixels = np.asarray(lit_mask)
    plate.rounded_rectangle((0, 0, width*ss-1, height*ss-1), radius=max(2, width*.12*ss), fill=255)
    for y in range(0, height, pitch):
        for x in range(0, width, pitch):
            box = (x*ss+1, y*ss+1, min(width*ss-1,(x+pitch)*ss-2), min(height*ss-1,(y+pitch)*ss-2))
            if box[2] < box[0] or box[3] < box[1]:
                continue
            idle.rectangle(box, fill=180)
            lit.rectangle(box, fill=int(pixels[y:y+pitch, x:x+pitch].max()))
    return tuple(ImageChops.multiply(layer, layers[1]).resize((width,height), Image.Resampling.BOX) for layer in layers)


def waveform_masks(width, height, signal, time, *, style, detail=.6, seed=42, display=None):
    """Shape providers share the same display contract; trace supplies its own ink."""
    display = resolve_display(style, display)
    if style == 'digital-circuit' and display == 'led':
        return vocoder_masks(width, height, signal, detail=detail)
    lit = inkblot_mask(width, height, signal, time, style=style, detail=detail, seed=seed)
    return led_device(lit, detail=detail) if display == 'led' else (lit, None, None)


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
    """Audio controls the width of pixel blocks or horizontal LED bars."""
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
    """Light mask for segmented, rounded horizontal vocoder bars."""
    return vocoder_masks(width, height, signal, detail=detail)[0]


def vocoder_masks(width, height, signal, *, detail=.6):
    """Separate active light, rounded housings, and unlit LED segments."""
    ss = 3
    mask = Image.new('L', (width * ss, height * ss))
    housing = Image.new('L', mask.size)
    inactive = Image.new('L', mask.size)
    values = np.clip(np.abs(np.nan_to_num(np.asarray(signal, np.float32))), 0, 1)
    if not len(values):
        values = np.zeros(1, np.float32)
    # Lay the trailing audio window down the entire stack. Each row responds
    # independently; constant audio stays steady and silence shows idle bars.
    segments = min(max(1, height // 3), 2 * round(12 + detail * 10))
    bins = np.linspace(0, len(values), segments + 1)
    pitch = height / segments
    bar_height = max(1, round(pitch * .56))
    draw = ImageDraw.Draw(mask)
    casing = ImageDraw.Draw(housing)
    idle = ImageDraw.Draw(inactive)
    # The LED grid is anchored to the column center, so changing row widths
    # reveals or hides end segments without shifting the interior dividers.
    cell_pitch = max(2, width / 15)
    cell_width = cell_pitch * .74
    half_cells = math.ceil(width / cell_pitch / 2)
    for row, (lo, hi) in enumerate(zip(bins, bins[1:])):
        window = values[int(lo):max(int(lo) + 1, math.ceil(hi))]
        energy = .65 * float(np.sqrt(np.mean(window ** 2))) + .35 * float(window.max())
        # A steep response makes attacks visibly switch LEDs on. The fixed
        # casing and idle segments remain visible below the activation floor.
        strength = float(np.clip((energy - .055) / .08, 0, 1) ** .5)
        lit_span = .3 + .7 * strength if strength else 0.
        bar_width = max(1, round(width * .94 * (.76 if row % 2 == 0 else 1)))
        x = (width - bar_width) / 2
        y = round((row + .5) * pitch - bar_height / 2)
        box = (round(x * ss), y * ss, round((x + bar_width) * ss) - 1, (y + bar_height) * ss - 1)
        casing.rounded_rectangle(box, radius=bar_height * ss / 2, fill=255)
        inset = min(bar_height * .18, max(.5, height / 540))
        for cell in range(-half_cells, half_cells + 1):
            cx = width / 2 + cell * cell_pitch
            distance = abs(cx - width / 2) / max(.5, bar_width / 2)
            if distance >= 1:
                continue
            led = (round((cx - cell_width / 2) * ss), round((y + inset) * ss),
                   round((cx + cell_width / 2) * ss) - 1, round((y + bar_height - inset) * ss) - 1)
            idle.rectangle(led, fill=round(255 * (.15 + .85 * math.cos(distance * math.pi / 2) ** 2)))
            if distance < lit_span:
                edge = float(np.clip((lit_span - distance) * 8, 0, 1))
                brightness = (.55 + .45 * math.cos(distance / lit_span * math.pi / 2) ** 2) * (.75 + .25 * strength)
                draw.rectangle(led, fill=round(255 * edge * brightness))
    mask = ImageChops.multiply(mask, housing)
    inactive = ImageChops.multiply(inactive, housing)
    # Box downsampling keeps the tiny dividers dark at gallery resolution.
    return tuple(layer.resize((width, height), Image.Resampling.BOX) for layer in (mask, housing, inactive))
