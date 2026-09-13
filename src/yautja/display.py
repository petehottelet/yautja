"""Optional horizontal phosphor bleed and time-based frame persistence."""
import math

import numpy as np
from PIL import Image, ImageFilter


def highlight_glow(image, field, strength, time, speed=1., seed=42, *, dark=False):
    """Animate broad luminous patches from synthetic heat, never source texture."""
    if not strength:
        return image
    height, width = field.shape
    y, x = np.mgrid[:height, :width].astype(np.float32)
    phase = time * speed + (seed % 997) / 997 * math.tau
    moving = .65 + .22 * np.sin(x / max(1, width) * 11 + phase * 2.1) + .13 * np.sin(y / max(1, height) * 14 - phase * 1.6)
    hot = np.clip((field.astype(np.float32) / 255 - .55) / .30, 0, 1) * moving
    pixels = np.asarray(image, np.float32)
    emission = Image.fromarray(np.uint8((255 - pixels if dark else pixels) * hot[..., None]))
    radius = max(.6, width / 160 * strength)
    halo = np.asarray(emission.filter(ImageFilter.GaussianBlur(radius)), np.float32)
    wide = np.asarray(emission.filter(ImageFilter.GaussianBlur(radius * 2.5)), np.float32)
    bloom = strength * (halo * .55 + wide * .4)
    return Image.fromarray(np.uint8(np.clip(pixels - bloom if dark else pixels + bloom, 0, 255)))


class DisplayEffects:
    def __init__(self, motion_blur=0., crt_bleed=0.):
        for name, value in (('motion-blur', motion_blur), ('crt-bleed', crt_bleed)):
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f'--{name} must be between 0 and 1')
        self.motion_blur, self.crt_bleed = motion_blur, crt_bleed
        self.previous = None
        self.time = None
        self.shot = None

    def reset(self):
        self.previous = self.time = None

    def apply(self, image, time, shot=None):
        if not (self.motion_blur or self.crt_bleed):
            return image
        pixels = np.asarray(image, dtype=np.float32)
        if self.crt_bleed:
            radius = max(1, round(self.crt_bleed * image.width / 64))
            padded = np.pad(pixels, ((0, 0), (radius, radius), (0, 0)), mode='edge')
            summed = np.concatenate((np.zeros((image.height, 1, 3), np.float32), np.cumsum(padded, axis=1)), axis=1)
            blurred = (summed[:, 2 * radius + 1:] - summed[:, :-2 * radius - 1]) / (2 * radius + 1)
            # Horizontal-only mixing and a soft bright-side halo, with no wrap.
            strength = self.crt_bleed
            pixels = pixels * (1 - .35 * strength) + blurred * .35 * strength
            pixels += np.maximum(blurred - pixels, 0) * .55 * strength
        if self.motion_blur:
            delta = None if self.time is None else time - self.time
            if self.previous is not None and self.previous.shape == pixels.shape and self.shot == shot and 0 < delta <= .5:
                retention = self.motion_blur * math.exp(-delta / (.015 + .22 * self.motion_blur))
                pixels = pixels * (1 - retention) + self.previous * retention
            self.previous = pixels.copy()
            self.time, self.shot = time, shot
        return Image.fromarray(np.uint8(np.clip(pixels, 0, 255)))
