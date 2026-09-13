"""Decorative, animated three-blade targeting overlay; no inference here."""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .colors import parse_hex


def target_colors(value):
    if value is None:
        return None
    parts = value.split(',')
    if len(parts) != 2:
        raise ValueError('--target-colors needs two comma-separated RGB hex colors: landing,flash')
    return tuple(parse_hex(part) for part in parts)


class TargetOverlay:
    """Keep a bounded animation state for only the currently visible selections."""
    def __init__(self, acquire=.8, flash_rate=1.5, scale=1.):
        for value, low, high, flag in ((acquire, .1, 5, 'target-acquire'),
                                       (flash_rate, 0, 3, 'target-flash-rate'),
                                       (scale, .25, 3, 'target-scale')):
            if not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f'--{flag} must be between {low} and {high}')
        self.acquire, self.flash_rate, self.scale = acquire, flash_rate, scale
        self.active = {}
        self.last_time = None
        self.shot = None
        self.seen = set()
        self.frames = 0

    def draw(self, image, time, targets, colors, *, shot=None, static=False):
        if self.shot != shot or (self.last_time is not None and (time <= self.last_time or time - self.last_time > .5)):
            self.active.clear()
        self.shot, self.last_time = shot, time
        visible = {item['id'] for item in targets}
        self.active = {key: value for key, value in self.active.items() if key in visible}
        if not targets:
            return image
        self.seen.update(visible)
        self.frames += 1
        width, height = image.size
        # Draw at twice output resolution for crisp bevels without jagged edges.
        overlay = Image.new('RGBA', (width * 2, height * 2))
        draw = ImageDraw.Draw(overlay)
        for item in targets:
            start = self.active.setdefault(item['id'], time)
            age = self.acquire if static else time - start
            progress = min(1., max(0., age / self.acquire))
            ease = 1 - (1 - progress) ** 3
            x0, y0, x1, y1 = item['bbox']
            cx, cy = (x0 + x1) * width / 2, (y0 + y1) * height / 2
            radius = max((x1 - x0) * width * .8, (y1 - y0) * height * .62, 12) * self.scale
            # Lock onto the figure's center with a compact reticle, rather than
            # enclosing its full silhouette. Keep the broad acquisition sweep.
            radius = min(radius, max(width, height) * .65) * .30
            radius += (max(width, height) * .75 - radius) * (1 - ease)
            angle = -.17 * (1 - ease)
            points = np.array([(math.cos(a + angle), math.sin(a + angle))
                               for a in (-math.pi / 2, math.pi / 6, 5 * math.pi / 6)]) * radius
            thickness = min(radius * .30, max(1.5, min(width, height) / 150) + radius * .24
                            + (1 - ease) * min(width, height) * .08)
            elapsed = max(0., age - self.acquire - .18)
            flash = progress == 1 and elapsed > 0 and self.flash_rate > 0 and int(elapsed * self.flash_rate * 2) % 2 == 1
            color = colors[int(flash)]
            opacity = round(255 * float(item.get('opacity', 1.)))
            for index in range(3):
                a, b = points[index], points[(index + 1) % 3]
                direction = (b - a) / max(1., np.linalg.norm(b - a))
                inward = np.array([-direction[1], direction[0]])
                if np.dot(inward, -(a + b) / 2) < 0:
                    inward = -inward
                offset = -inward * (1 - ease) * max(width, height) * .25
                # Terminate each blade well before the vertex: three clearly
                # open corners, including the white flash and its soft glow.
                gap = min(radius * .30, max(.8, radius * .24))
                # Parallel cuts at the 60-degree corners keep the gap open
                # through the entire stroke, rather than pinching shut inside.
                cutback = gap + thickness * math.sqrt(3)
                vertices = np.array([a + direction * gap, b - direction * gap,
                                     b - direction * cutback + inward * thickness,
                                     a + direction * cutback + inward * thickness])
                vertices += np.array([cx, cy]) + offset
                draw.polygon([tuple(point * 2) for point in vertices], fill=(*color, opacity))
                # A subtle darker inner bevel follows the selected ink color.
                bevel = tuple(round(c * .62) for c in color)
                draw.line([tuple(vertices[2] * 2), tuple(vertices[3] * 2)], fill=(*bevel, opacity), width=max(1, round(thickness * .28)))
        overlay = overlay.resize(image.size, Image.Resampling.LANCZOS)
        glow = overlay.filter(ImageFilter.GaussianBlur(max(.5, width / 640)))
        glow.putalpha(glow.getchannel('A').point(lambda a: round(a * .22)))
        base = Image.alpha_composite(image.convert('RGBA'), glow)
        return Image.alpha_composite(base, overlay).convert('RGB')
