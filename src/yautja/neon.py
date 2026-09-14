"""CPU neon tubes inspired by Saber's two-radius glow and smooth value noise."""
from collections import OrderedDict
import hashlib
import math

import numpy as np
from PIL import Image, ImageChops, ImageFilter

from .hud import BLUR_ELEMENTS, blur_layer, element_values, opacity_layer


def neon_intensities(amount=1., elements=None):
    try:
        values = element_values(amount, elements, BLUR_ELEMENTS, 'neon', 2)[0]
    except ValueError as exc:
        raise ValueError('--neon-intensity / --neon-elements: ' + str(exc)) from None
    values['target-flash'] = values['target']
    return values


def glow_color(rgb):
    peak = max(rgb)
    return tuple(round(c * 255 / peak) for c in rgb) if peak else (255, 255, 255)


class NeonFlicker:
    def __init__(self, seed):
        digest = hashlib.sha256(f'{seed}:neon-flicker'.encode()).digest()
        self.values = np.random.default_rng(int.from_bytes(digest[:8], 'big')).uniform(-1, 1, 4096)

    def gain(self, time, amount):
        if not amount:
            return 1.
        total = weight = 0.
        amplitude, frequency = 1., 14.
        for _ in range(3):
            position = (time * frequency) % len(self.values)
            index = int(position)
            fraction = position - index
            fraction *= fraction * (3 - 2 * fraction)
            total += amplitude * (self.values[index] * (1 - fraction) + self.values[(index + 1) % 4096] * fraction)
            weight += amplitude
            amplitude *= .5
            frequency *= 2.1
        return max(.05, 1 + amount * .6 * total / weight)


def normalized_blur(mask, radius):
    # Pillow's GaussianBlur does not support float-mode images. Downsample in
    # float first, then normalize before the 8-bit blur to retain thin strokes.
    factor = 4 if radius > 14 else 2 if radius > 6 else 1
    small = mask.resize((max(1, mask.width // factor), max(1, mask.height // factor)), Image.Resampling.BOX)
    values = np.asarray(small, np.float32)
    peak = float(values.max())
    if peak == 0:
        return np.zeros((mask.height, mask.width), np.float32)
    image = Image.fromarray(np.uint8(np.clip(values * (255 / peak), 0, 255)))
    image = image.filter(ImageFilter.GaussianBlur(radius / factor))
    if factor > 1:
        image = image.resize(mask.size, Image.Resampling.BILINEAR)
    values = np.asarray(image, np.float32)
    return values / max(1., float(values.max()))


class NeonStyle:
    """One frame gain, bounded mask cache, and local additive/subtractive light."""
    def __init__(self, intensity=1., spread=.6, flicker=0., elements=None, seed=42):
        self.intensities = neon_intensities(intensity, elements)
        for name, value, upper in (('spread', spread, 2), ('flicker', flicker, 1)):
            if not math.isfinite(value) or not 0 <= value <= upper:
                raise ValueError(f'--neon-{name} must be finite and between 0 and {upper}')
        self.intensity, self.spread, self.flicker = intensity, spread, flicker
        self.noise = NeonFlicker(seed)
        self.cache = OrderedDict()
        self.cache_pixels = 0

    def apply(self, base, layer, x, y, color, *, element, width, gain=1., opacity=1., blur=0.):
        if opacity <= 0:
            return
        bounds = layer.getbbox()
        if bounds is None:
            return
        intensity = self.intensities[element]
        outer = max(.5, width) * (2 + 12 * self.spread)
        pad = math.ceil(3 * max(outer if intensity else 0, blur, .5))
        # Clip only at the final frame, never at an internal panel boundary.
        crop = (max(bounds[0] - pad, -x), max(bounds[1] - pad, -y),
                min(bounds[2] + pad, base.width - x), min(bounds[3] + pad, base.height - y))
        if crop[2] <= crop[0] or crop[3] <= crop[1]:
            return
        artwork = layer.crop(crop)
        x, y = x + crop[0], y + crop[1]
        # Coverage remains independent of ink brightness, including black ink.
        alpha = artwork.getchannel('A')
        sharp = np.asarray(alpha, np.float32) / 255
        peak = float(sharp.max())
        if not peak:
            return
        core = blur_layer(artwork, blur)
        region = (x, y, x + artwork.width, y + artwork.height)
        emission = None
        if intensity:
            digest = hashlib.blake2b(alpha.tobytes(), digest_size=16).digest()
            key = (alpha.size, digest, float(width), float(blur))
            cached = self.cache.get(key)
            if cached is None:
                mask = Image.fromarray(sharp / peak)
                inner = normalized_blur(mask, max(.5, width) * (.8 + 2.5 * self.spread))
                halo = inner * .55 + normalized_blur(mask, outer) * .45
                center = np.asarray(alpha.filter(ImageFilter.GaussianBlur(max(.5, width * .18))), np.float32) / (255 * peak)
                center = np.clip((center - .6) / .4, 0, 1)
                if blur:
                    center = np.asarray(Image.fromarray(np.uint8(center * 255)).filter(ImageFilter.GaussianBlur(blur)), np.float32) / 255
                cached = (halo, center)
                while self.cache and (len(self.cache) >= 24 or self.cache_pixels + halo.size > 1_000_000):
                    _, previous = self.cache.popitem(last=False)
                    self.cache_pixels -= previous[0].size
                if halo.size <= 1_000_000:
                    self.cache[key] = cached
                    self.cache_pixels += halo.size
            else:
                self.cache.move_to_end(key)
            halo, center = cached
            # Calibrated for stacked HUD layers: normalized halos must not wash
            # out the subject when a leader, marker and target overlap.
            emission = (halo * peak * .45 + sharp * .20) * (intensity * gain * opacity)
            core_box = core.getbbox()
            if max(color) and core_box:
                # Whiten only the occupied core; the padded halo can be much
                # larger. Avoid full-frame float RGB buffers for sparse ink.
                pixels = np.asarray(core.crop(core_box), np.float32).copy()
                left, top, right, bottom = core_box
                heat = center[top:bottom, left:right, None] * (.85 * min(1., intensity) * gain)
                pixels[..., :3] += heat * (255 - pixels[..., :3])
                core.paste(Image.fromarray(np.uint8(np.clip(pixels, 0, 255))), core_box[:2])
        background = base.crop(region).convert('RGBA')
        out = Image.alpha_composite(background, opacity_layer(core, opacity)).convert('RGB')
        if emission is not None:
            # Pillow adds channels in C. Keep emission in float until each
            # channel is quantized, so bright low-channel hues do not get capped
            # by the brightest channel's saturation.
            light = Image.merge('RGB', tuple(Image.fromarray(np.uint8(np.clip(emission * value, 0, 255)))
                                            for value in glow_color(color)))
            out = ImageChops.subtract(out, light) if max(color) == 0 else ImageChops.add(out, light)
        base.paste(out, (x, y))
