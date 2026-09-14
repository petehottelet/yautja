"""Decorative animated reticles; no inference here."""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .colors import parse_hex
from .hud import blur_layer

TARGET_SHAPES = ('triangle', 'triangle-dots', 'crosshair', 'hollow-cross',
                 'square', 'round-dot', 'square-cross', 'square-mil', 'square-x')


def resolve_target_shape(shape):
    shape = {'iron-sights': 'hollow-cross', 'vector-lock': 'hollow-cross'}.get(shape, shape)
    if shape not in TARGET_SHAPES:
        raise ValueError('Unknown target shape: ' + str(shape))
    return shape


def detail_shapes(shape, radius, locked):
    """Local paths and circles in radius units; hollow-cross contours are filled."""
    paths, circles = [], []
    if shape.startswith('square'):
        for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            paths.append(([(x * .40, y * .72), (x * .72, y * .72), (x * .72, y * .40)], False))
    if shape == 'triangle-dots' and locked:
        circles = [(0, -.23, .105), (-.25, .16, .105), (.25, .16, .105)]
    elif shape in ('crosshair', 'square-cross', 'square-mil'):
        outer = .9 if shape == 'crosshair' else .46
        for axis in (0, 1):
            for sign in (-1, 1):
                points = [(sign * .12, 0), (sign * outer, 0)]
                if axis:
                    points = [(y, x) for x, y in points]
                paths.append((points, False))
        if shape == 'crosshair':
            for quadrant in range(4):
                angles = np.linspace(quadrant * math.pi / 2 + .20, (quadrant + 1) * math.pi / 2 - .20, 14)
                paths.append(([(.59 * math.cos(a), .59 * math.sin(a)) for a in angles], False))
        if shape == 'square-mil':
            for axis in (0, 1):
                for position in (-.38, -.25, .25, .38):
                    points = [(position, -.055), (position, .055)]
                    paths.append(([(y, x) for x, y in points] if axis else points, False))
    elif shape == 'hollow-cross':
        # Four solid, square-cornered L bands outline a plus. The center and
        # the ends of all four arms stay open, as in the reference artwork.
        quadrant = [(.21, .98), (.39, .98), (.39, .39),
                    (.98, .39), (.98, .21), (.21, .21)]
        for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            paths.append(([(x * px, y * py) for px, py in quadrant], True))
    elif shape == 'round-dot':
        # Open arcs leave equal gaps at the top, right, bottom, and left.
        segments = max(16, min(128, math.ceil(math.tau * radius * .72 / 16)))
        for quadrant in range(4):
            angles = np.linspace(quadrant * math.pi / 2 + .18,
                                 (quadrant + 1) * math.pi / 2 - .18, segments)
            paths.append(([(.72 * math.cos(a), .72 * math.sin(a)) for a in angles], False))
        if locked:
            circles = [(0, -.23, .10), (-.25, .16, .10), (.25, .16, .10)]
    elif shape == 'square-x':
        for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            paths.append(([(x * .10, y * .10), (x * .39, y * .39)], False))
    return paths, circles


def target_colors(value):
    if value is None:
        return None
    parts = value.split(',')
    if len(parts) != 2:
        raise ValueError('--target-colors needs two comma-separated RGB hex colors: landing,flash')
    return tuple(parse_hex(part) for part in parts)


def parse_stroke_colors(value):
    if value is None or value.strip().lower() == 'auto':
        return None
    parts = value.split(',')
    if len(parts) not in (1, 2):
        raise ValueError('--target-stroke-colors needs one RGB hex color or a landing,flash pair')
    colors = tuple(parse_hex(part) for part in parts)
    return colors * 2 if len(colors) == 1 else colors


class TargetOverlay:
    """Keep a bounded animation state for only the currently visible selections."""
    def __init__(self, acquire=.8, flash_rate=1.5, scale=1., *, stroke=0., stroke_colors=None, blur=0.,
                 opacity=1., flash_opacity=None, shape='triangle', neon=None):
        self.neon = neon
        self.shape = resolve_target_shape(shape)
        flash_opacity = opacity if flash_opacity is None else flash_opacity
        for value, low, high, flag in ((acquire, .1, 5, 'target-acquire'),
                                       (flash_rate, 0, 3, 'target-flash-rate'),
                                       (scale, .25, 3, 'target-scale'), (stroke, 0, 12, 'target-stroke'),
                                       (blur, 0, 20, 'target blur'), (opacity, 0, 1, 'target opacity'),
                                       (flash_opacity, 0, 1, 'target flash opacity')):
            if not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f'--{flag} must be between {low} and {high}')
        self.acquire, self.flash_rate, self.scale = acquire, flash_rate, scale
        self.stroke, self.blur = stroke, blur
        self.opacity, self.flash_opacity = opacity, flash_opacity
        self.stroke_colors = parse_stroke_colors(stroke_colors)
        self.active = {}
        self.last_time = None
        self.shot = None
        self.seen = set()
        self.frames = 0

    def draw(self, image, time, targets, colors, *, shot=None, static=False, neon_gain=1.):
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
        if self.neon:
            image = image.copy()
        # Draw at twice output resolution for crisp edges without jagged pixels.
        overlay = Image.new('RGBA', (width * 2, height * 2))
        draw = ImageDraw.Draw(overlay)
        for item in targets:
            if self.neon:
                overlay = Image.new('RGBA', (width * 2, height * 2))
                draw = ImageDraw.Draw(overlay)
            start = self.active.setdefault(item['id'], time)
            age = self.acquire if static else time - start
            progress = min(1., max(0., age / self.acquire))
            ease = 1 - (1 - progress) ** 3
            x0, y0, x1, y1 = item['bbox']
            cx, cy = (x0 + x1) * width / 2, (y0 + y1) * height / 2
            radius = max((x1 - x0) * width * .8, (y1 - y0) * height * .62, 12) * self.scale
            # Lock onto the figure's center with a compact reticle, rather than
            # enclosing its full silhouette. Keep the broad acquisition sweep.
            lock_radius = min(radius, max(width, height) * .65) * .30
            if self.shape not in ('triangle', 'triangle-dots'):
                lock_radius *= .85
            stroke_radius = lock_radius + (max(width, height) * .75 - lock_radius) * (1 - ease)
            radius = stroke_radius + lock_radius * .30 * ease
            angle = -.17 * (1 - ease)
            points = np.array([(math.cos(a + angle), math.sin(a + angle))
                               for a in (-math.pi / 2, math.pi / 6, 5 * math.pi / 6)]) * radius
            # Reduce the existing stroke independently of the 30% size increase.
            thickness = .75 * min(stroke_radius * .30, max(1.5, min(width, height) / 150) + stroke_radius * .24
                                  + (1 - ease) * min(width, height) * .08)
            elapsed = max(0., age - self.acquire - .18)
            flash = progress == 1 and elapsed > 0 and self.flash_rate > 0 and int(elapsed * self.flash_rate * 2) % 2 == 1
            color = colors[int(flash)]
            opacity = round(255 * float(item.get('opacity', 1.)) * (self.flash_opacity if flash else self.opacity))
            neon_opacity = opacity / 255
            if self.neon:
                opacity = 255
            for index in range(3) if self.shape in ('triangle', 'triangle-dots') else ():
                a, b = points[index], points[(index + 1) % 3]
                direction = (b - a) / max(1., np.linalg.norm(b - a))
                inward = np.array([-direction[1], direction[0]])
                if np.dot(inward, -(a + b) / 2) < 0:
                    inward = -inward
                offset = -inward * (1 - ease) * max(width, height) * .25
                # Terminate each blade well before the vertex: three clearly
                # open corners, including the white flash and its soft glow.
                gap = .595 * min(radius * .30, max(.8, radius * .24))
                # Parallel cuts at the 60-degree corners keep the gap open
                # through the entire stroke, rather than pinching shut inside.
                cutback = gap + thickness * math.sqrt(3)
                vertices = np.array([a + direction * gap, b - direction * gap,
                                     b - direction * cutback + inward * thickness,
                                     a + direction * cutback + inward * thickness])
                vertices += np.array([cx, cy]) + offset
                polygon = [tuple(point * 2) for point in vertices]
                draw.polygon(polygon, fill=(*color, opacity))
                # Draw inward so an outline never expands the blades into the gaps.
                stroke_width = round(self.stroke * min(width, height) / 1080 * 2)
                if stroke_width:
                    outline = self.stroke_colors[int(flash)] if self.stroke_colors else tuple(round(c * .62) for c in color)
                    draw.polygon(polygon, outline=(*outline, opacity), width=stroke_width)
            # All alternative shapes share acquisition, flash, tracking fade,
            # inward outlines, blur, and transparency with the original triangle.
            paths, circles = detail_shapes(self.shape, radius, progress == 1)
            line_width = max(2, round(radius * .085 * 2))
            outline_width = round(self.stroke * min(width, height) / 1080 * 2)
            outline = self.stroke_colors[int(flash)] if self.stroke_colors else tuple(round(c * .62) for c in color)
            cosine, sine = math.cos(angle), math.sin(angle)

            def point(x, y):
                return ((cx + radius * (x * cosine - y * sine)) * 2,
                        (cy + radius * (x * sine + y * cosine)) * 2)

            for path, closed in paths:
                vertices = [point(x, y) for x, y in path]
                if self.shape == 'hollow-cross':
                    draw.polygon(vertices, fill=(*color, opacity))
                    if outline_width:
                        draw.polygon(vertices, outline=(*outline, opacity), width=outline_width)
                    continue
                if closed:
                    vertices.append(vertices[0])
                draw.line(vertices, fill=(*(outline if outline_width else color), opacity), width=line_width, joint='curve')
                if outline_width and line_width > outline_width * 2:
                    draw.line(vertices, fill=(*color, opacity), width=line_width - outline_width * 2, joint='curve')
            for x, y, dot_radius in circles:
                px, py = point(x, y)
                r = radius * dot_radius * 2
                box = (px - r, py - r, px + r, py + r)
                draw.ellipse(box, fill=(*color, opacity))
                if outline_width:
                    draw.ellipse(box, outline=(*outline, opacity), width=min(outline_width, max(1, round(r))))
            if self.neon:
                tube_width = thickness if self.shape.startswith('triangle') else radius * .18 if self.shape == 'hollow-cross' else line_width / 2
                bounds = overlay.getbbox()
                if bounds and neon_opacity:
                    # Resize only occupied artwork. Align to the 2x raster and
                    # retain the Lanczos kernel margin so subpixel edges match.
                    box = (max(0, bounds[0] // 2 * 2 - 8), max(0, bounds[1] // 2 * 2 - 8),
                           min(width * 2, (bounds[2] + 1) // 2 * 2 + 8),
                           min(height * 2, (bounds[3] + 1) // 2 * 2 + 8))
                    tile = overlay.crop(box).resize(((box[2] - box[0]) // 2, (box[3] - box[1]) // 2), Image.Resampling.LANCZOS)
                    self.neon.apply(image, tile, box[0] // 2, box[1] // 2, color,
                                    element='target-flash' if flash else 'target', width=tube_width,
                                    gain=neon_gain, opacity=neon_opacity, blur=self.blur * min(width, height) / 1080)
        if self.neon:
            return image
        overlay = overlay.resize(image.size, Image.Resampling.LANCZOS)
        overlay = blur_layer(overlay, self.blur * min(width, height) / 1080)
        glow = overlay.filter(ImageFilter.GaussianBlur(max(.5, width / 640)))
        glow.putalpha(glow.getchannel('A').point(lambda a: round(a * .22)))
        base = Image.alpha_composite(image.convert('RGBA'), glow)
        return Image.alpha_composite(base, overlay).convert('RGB')
