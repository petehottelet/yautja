"""Mask-bound decorative projection textures; no physical assessment is made."""
import math

import numpy as np
from PIL import Image


def holographic_ink(mask, color, time, seed, *, vertical=False, shine=.55):
    """Tinted emission with pale cores, fine raster texture and moving light bands."""
    alpha = np.asarray(mask, np.float32) / 255
    h, w = alpha.shape
    y, x = np.ogrid[:h, :w]
    phase = (seed % 65536) / 65536 * math.tau
    axis = x if vertical else y
    scan = .5 + .5 * np.sin(axis * 1.7 + time * 5 + phase)
    band = (.5 + .5 * np.sin(axis / max(8, (w if vertical else h) * .17) - time * 2 + phase)) ** 8
    white = np.broadcast_to(.15 + shine * band + .18 * scan, alpha.shape)
    base = np.array(color, np.float32)
    rgb = base + white[..., None] * (255-base) if max(color) else np.zeros((*alpha.shape, 3))
    texture = (.76 + .24 * scan) * (.90 + .10 * np.cos(x * 2.1 + phase) ** 2)
    pixels = np.empty((h, w, 4), np.uint8)
    pixels[..., :3] = np.uint8(np.clip(rgb, 0, 255))
    pixels[..., 3] = np.uint8(np.clip(alpha * texture * 255, 0, 255))
    return Image.fromarray(pixels)


def weak_spot_ink(mask, color, time, seed, *, shine=.55):
    """Two fictional scan patches, anchored in normalized current-mask space."""
    visible = np.asarray(mask) >= 128
    h, w = visible.shape
    yy, xx = np.nonzero(visible)
    if not len(xx):
        return Image.new('RGBA', mask.size)
    rng = np.random.default_rng(seed)
    y, x = np.ogrid[:h, :w]
    ink = np.zeros((h, w), np.float32)
    for index in range(2):
        # Snap a seeded, non-anatomical position onto actual foreground. This
        # works for vehicles, tools, wildlife and people without inventing parts.
        u, v = rng.uniform(.22, .78), (.32 if index == 0 else .68) + rng.uniform(-.07, .07)
        nearest = np.argmin(((xx / max(1, w-1) - u) ** 2 + (yy / max(1, h-1) - v) ** 2))
        cx, cy = xx[nearest], yy[nearest]
        rx, ry = max(2, w * rng.uniform(.14, .22)), max(2, h * rng.uniform(.06, .09))
        phase = rng.uniform(0, math.tau)
        dx, dy = (x-cx)/rx, (y-cy)/ry
        angle = np.arctan2(dy, dx)
        radius = np.hypot(dx, dy) * (1 + .12 * np.sin(angle*5 + phase) + .06 * np.cos(angle*9-phase))
        inside = np.clip((1-radius) * 10, 0, 1)
        rim = np.clip(1 - np.abs(radius-.88)/.12, 0, 1)
        bars = (.5 + .5 * np.sin((x-cx)/max(1, w*.015) + phase + time*.8)) ** 12
        raster = (.5 + .5 * np.sin((y-cy)*1.8 - time*4)) ** 3
        pulse = .82 + .18 * math.sin(time*2 + phase)
        patch = inside * (.25 + .36*bars + .15*raster) + rim*.65
        # Faint upward projection streaks remain inside the same silhouette.
        rays = bars * np.clip(1-np.abs(dx), 0, 1) * np.clip((dy+2.8)/1.8, 0, 1) * (dy < -.7) * .20
        ink = np.maximum(ink, np.clip((patch+rays)*pulse, 0, 1))
    return holographic_ink(Image.fromarray(np.uint8(ink * visible * 255)), color, time, seed, vertical=True, shine=shine)
