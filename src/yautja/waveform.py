"""Mirrored inkblot transformations of audio or procedural waveform energy."""
import math

import numpy as np
from PIL import Image

WAVE_STYLES = ('trace', 'rorschach', 'rorschach-split', 'rorschach-hollow')


def inkblot_mask(width, height, signal, time, *, style='rorschach', detail=.6, seed=42):
    """Return a symmetrical shaded L mask; zero input always produces zero ink."""
    if style not in WAVE_STYLES[1:]:
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
