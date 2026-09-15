"""Source-scene grading and silhouette-bound Cyber code streams."""
from functools import lru_cache
import hashlib
from importlib.resources import files
import io
import json
import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from .colors import parse_hex
from .hologram import holographic_ink

SIGNAL_OPTIONS = ('scene_mode', 'scene_tint', 'scene_tint_strength', 'scene_exposure', 'scene_highlights',
                  'subject_outline', 'subject_code', 'subject_labels',
                  'code_size', 'code_speed', 'code_density', 'subject_head_gap', 'subject_title_gap', 'subject_caret_scale',
                  'outline_style', 'outline_coverage', 'outline_arcs', 'outline_speed', 'outline_width', 'code_layer')
SUBJECT_ELEMENTS = ('subject-outline', 'subject-code', 'subject-labels', 'subject-carets')


@lru_cache(maxsize=1)
def glyph_font():
    """Compile the 192 original contours, including holes and detached marks."""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.svgLib.path import parse_path
    data = json.loads(files('yautja').joinpath('assets/cyber-glyphs.json').read_text(encoding='utf-8'))
    glyphs = {'.notdef': TTGlyphPen(None).glyph()}
    for item in data['glyphs']:
        pen = TTGlyphPen(None)
        transformed = TransformPen(Cu2QuPen(pen, 1.), (10, 0, 0, -10, 0, 1000))
        for path in item['paths']:
            parse_path(path, transformed)
        glyphs[item['id']] = pen.glyph()
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(list(glyphs))
    builder.setupCharacterMap({0xe000 + i: item['id'] for i, item in enumerate(data['glyphs'])})
    builder.setupGlyf(glyphs)
    metrics = {}
    for name, glyph in glyphs.items():
        glyph.recalcBounds(None)
        metrics[name] = (1000, getattr(glyph, 'xMin', 0))
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=1000, descent=0)
    builder.setupNameTable({'familyName': 'Cyber Code', 'styleName': 'Regular', 'uniqueFontIdentifier': 'CyberCodeV2'})
    builder.setupOS2(sTypoAscender=1000, sTypoDescender=0, usWinAscent=1000, usWinDescent=0)
    builder.setupPost()
    buffer = io.BytesIO()
    builder.save(buffer)
    return buffer.getvalue()


@lru_cache(maxsize=16)
def sized_font(size):
    return ImageFont.truetype(io.BytesIO(glyph_font()), size * 3)


@lru_cache(maxsize=768)
def code_glyph(index, size):
    tile = Image.new('L', (size * 3, size * 3))
    ImageDraw.Draw(tile).text((0, 0), chr(0xe000 + index % 192), font=sized_font(size), fill=255, anchor='la')
    return tile.resize((size, size), Image.Resampling.LANCZOS)


def stable_number(seed, *parts):
    value = ':'.join(str(p) for p in (seed, 'cyber-code', *parts))
    return int.from_bytes(hashlib.sha256(value.encode()).digest()[:8], 'little')


class SignalStyle:
    def __init__(self, *, scene_mode='thermal', scene_tint='#548568', scene_tint_strength=.8,
                 scene_exposure=.65, subject_outline=False, subject_code=False, subject_labels=False,
                 code_size=22., code_speed=1., code_density=.65, subject_head_gap=24.,
                 subject_title_gap=18., subject_caret_scale=1., scene_highlights=0.,
                 outline_style='solid', outline_coverage=.35, outline_arcs=5, outline_speed=1., code_layer='inside',
                 outline_width=None):
        if outline_style not in ('solid', 'shimmer', 'holographic'):
            raise ValueError('--outline-style must be solid, shimmer or holographic')
        if outline_width is not None and (not math.isfinite(outline_width) or not .5 <= outline_width <= 20):
            raise ValueError('--outline-width must be between 0.5 and 20')
        self.outline_width = outline_width
        if code_layer not in ('inside', 'behind'):
            raise ValueError('--code-layer must be inside or behind')
        if type(outline_arcs) is not int or not 1 <= outline_arcs <= 12:
            raise ValueError('--outline-arcs must be an integer between 1 and 12')
        self.outline_style, self.outline_coverage = outline_style, outline_coverage
        self.outline_arcs, self.outline_speed, self.code_layer = outline_arcs, outline_speed, code_layer
        if scene_mode not in ('thermal', 'source'):
            raise ValueError('--scene-mode must be thermal or source')
        self.tint = parse_hex(scene_tint)
        for key, value, low, high in (
            ('scene-tint-strength', scene_tint_strength, 0, 1), ('scene-exposure', scene_exposure, .1, 2),
            ('scene-highlights', scene_highlights, 0, 1),
            ('outline-coverage', outline_coverage, 0, 1), ('outline-speed', outline_speed, 0, 5),
            ('code-size', code_size, 8, 80), ('code-speed', code_speed, 0, 5), ('code-density', code_density, 0, 3),
            ('subject-head-gap', subject_head_gap, 0, 120), ('subject-title-gap', subject_title_gap, 0, 80),
            ('subject-caret-scale', subject_caret_scale, .25, 3)):
            if not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f'--{key} must be between {low} and {high}')
        self.scene_mode, self.scene_tint = scene_mode, scene_tint
        self.scene_tint_strength, self.scene_exposure = scene_tint_strength, scene_exposure
        self.scene_highlights = scene_highlights
        self.subject_outline, self.subject_code, self.subject_labels = subject_outline, subject_code, subject_labels
        self.code_size, self.code_speed, self.code_density = code_size, code_speed, code_density
        self.subject_head_gap, self.subject_title_gap = subject_head_gap, subject_title_gap
        self.subject_caret_scale = subject_caret_scale
        self.anchors = {}
        self.time = self.shot = None

    def report(self):
        return {key: getattr(self, key) for key in SIGNAL_OPTIONS}

    def grade(self, frame):
        rgb = np.asarray(frame.convert('RGB'), np.float32) / 255
        luma = rgb @ np.array([.2126, .7152, .0722], np.float32)
        tint = np.asarray(self.tint, np.float32) / max(1, max(self.tint))
        tinted = luma[..., None] * tint
        if self.scene_highlights:
            highlight = np.clip((luma - .68) / .32, 0, 1)
            highlight = (highlight * highlight * (3 - 2 * highlight)) * self.scene_highlights
            tinted = tinted * (1 - highlight[..., None]) + luma[..., None] * highlight[..., None]
        out = (rgb * (1 - self.scene_tint_strength) + tinted * self.scene_tint_strength) * self.scene_exposure
        return Image.fromarray(np.uint8(np.clip(out * 255, 0, 255)))

    def streams(self, size, bounds, anchor, time, seed, track_id, glyph=code_glyph):
        """Fixed glyph cells, upward bright cursors, fading tails and slow cycling."""
        width, height = size
        cell = max(5, round(self.code_size * min(size) / 1080))
        # Values above one pack additional streams into the same area while
        # retaining glyph size. Lower values preserve sparse-column behavior.
        pitch_x, pitch_y = cell * 1.15 / max(1., self.code_density), cell * 1.45
        x0, y0, x1, y1 = bounds
        # A screen-aligned lattice prevents body motion from dragging the code
        # sideways. Masks reveal the lattice; bright heads travel upward in it.
        cx, cy = 0., 0.
        mask = Image.new('L', size)
        if not self.code_density:
            return mask
        for col in range(math.floor((x0 - cx) / pitch_x), math.ceil((x1 - cx) / pitch_x) + 1):
            number = stable_number(seed, track_id, col)
            if (number % 10000) / 10000 >= self.code_density:
                continue
            period = 22 + number % 17
            length = period * (.48 + (number % 31) / 100)
            speed = self.code_speed * (5 + (number % 997) / 997 * 6)
            head = (number % 101) / 101 * period - time * speed
            start, end = math.floor(y0 / pitch_y) - 1, math.ceil(y1 / pitch_y)
            for row in range(start, end + 1):
                trail = (row - head) % period
                # Fade the cursor's arrival across one cell. The longer tail is
                # below the cursor, so both brightness and direction read upward.
                alpha = round(255 * min(1., trail * 4) * max(0., 1 - trail / length) ** .85)
                if not alpha:
                    continue
                identity = stable_number(seed, track_id, col, row)
                age = math.floor(time * self.code_speed * (.5 + identity % 19 / 25) + identity % 101 / 101)
                tile = glyph(stable_number(seed, track_id, col, row, age) % 192, cell)
                tile = tile.point(lambda v: round(v * alpha / 255))
                x, y = round(col * pitch_x), round(row * pitch_y)
                mask.paste(255, (x, y, x+tile.width, y+tile.height), tile)
        return mask

    def shimmer(self, edge, center, time, seed, track_id):
        from .geometry import noise
        yy, xx = np.nonzero(np.asarray(edge))
        ink = np.zeros((edge.height, edge.width), np.uint8)
        if not len(xx) or not self.outline_coverage:
            return Image.fromarray(ink)
        phase = np.arctan2(yy - center[1], xx - center[0]) / math.tau % 1
        brightness = np.zeros(len(xx))
        for j in range(self.outline_arcs):
            rng = np.random.default_rng(stable_number(seed, 'shimmer', track_id, j))
            start, width, speed, gain = rng.random(4)
            half = self.outline_coverage / self.outline_arcs * (.55 + .9 * width)
            position = start + time * self.outline_speed * (.04 + .10 * speed) * (1 if j % 2 else -1)
            distance = np.abs((phase - position + .5) % 1 - .5)
            blend = np.clip((half - distance) / max(.0001, half * .35), 0, 1)
            brightness += blend * blend * (3 - 2 * blend) * (.75 + .25 * gain) * (
                .7 + .3 * noise(stable_number(seed, 'shimmer-twinkle', track_id, j), time * 5 * self.outline_speed))
        ink[yy, xx] = np.uint8(np.clip(brightness, 0, 1) * 255)
        return Image.fromarray(ink)

    def draw(self, renderer, image, subjects, time, shot_id, static=False):
        if not (self.subject_outline or self.subject_code or self.subject_labels):
            return
        dt = None if self.time is None else time - self.time
        if shot_id != self.shot or dt is None or dt <= 0 or dt > .5:
            self.anchors.clear()
            dt = None
        self.time, self.shot = time, shot_id
        active = {}
        panel = renderer.hud_panel(image.size, *SUBJECT_ELEMENTS)
        behind = renderer.hud_panel(image.size, 'subject-code') if self.subject_code and self.code_layer == 'behind' else None
        union = Image.new('L', image.size) if behind else None
        scale = min(image.size) / 1080
        for subject in sorted(subjects, key=lambda s: s.track_id):
            if subject.opacity <= 0:
                continue
            mask = Image.fromarray(np.uint8(np.clip(subject.mask, 0, 1) * 255)).resize(image.size, Image.Resampling.BILINEAR)
            binary = mask.point(lambda v: 255 if v >= 128 else 0)
            if behind:
                union = ImageChops.lighter(union, binary)
            bounds = binary.getbbox()
            if bounds is None:
                continue
            x0, y0, x1, y1 = bounds
            yy, xx = np.nonzero(np.asarray(binary))
            # Headward anchor uses the highest portion of the actual mask, also
            # working on quadrupeds without assuming a human pose model.
            top = yy <= y0 + max(1, (y1 - y0) * .04)
            current = np.array([xx.mean(), yy.mean(), xx[top].mean(), y0], float)
            previous = self.anchors.get(subject.track_id)
            if previous is not None and dt is not None and np.linalg.norm(current[:2] - previous[:2]) < min(image.size) * .15:
                current = previous + (current - previous) * (1 - math.exp(-dt / .09))
            active[subject.track_id] = current
            opacity = min(1., max(0., subject.opacity))

            def paste(element, ink):
                layer = Image.new('RGBA', image.size, (*renderer.hud_colors[element], 0))
                layer.putalpha(ink.point(lambda v: round(v * opacity)))
                (behind if behind and element == 'subject-code' else panel).layer(element).alpha_composite(layer)

            if self.subject_code:
                if behind:
                    bw, bh = x1 - x0, y1 - y0
                    expanded = (max(0, x0 - bw * .12), max(0, y0 - bh * .35), min(image.width, x1 + bw * .12), y1)
                    code = self.streams(image.size, expanded, current[:2], 0 if static else time, renderer.seed, subject.track_id, renderer.code_mask)
                    x = np.arange(image.width)
                    y = np.arange(image.height)
                    fx = np.clip(np.minimum(x - expanded[0], expanded[2] - x) / max(1, bw * .08), 0, 1)
                    fy = np.clip((y - expanded[1]) / max(1, y0 - expanded[1]), 0, 1) * (y < y1)
                    feather = Image.fromarray(np.uint8(fy[:, None] * fx[None, :] * 255))
                    paste('subject-code', ImageChops.multiply(code, feather))
                else:
                    code = self.streams(image.size, bounds, current[:2], time, renderer.seed, subject.track_id, renderer.code_mask)
                    paste('subject-code', ImageChops.multiply(code, mask))
            if self.subject_outline:
                # Outline the visible silhouette, without tracing segmentation
                # pinholes in clothing and equipment as extra interior contours.
                # Partial highlights process only occupied bounds: the padded empty
                # border preserves connectivity without walking the whole frame.
                partial = self.outline_style in ('shimmer', 'holographic')
                region = binary.crop(bounds) if partial else binary
                exterior = Image.new('L', (region.width + 2, region.height + 2))
                exterior.paste(region, (1, 1))
                ImageDraw.floodfill(exterior, (0, 0), 255)
                holes = ImageChops.invert(exterior.crop((1, 1, region.width + 1, region.height + 1)))
                if partial:
                    local_holes = holes
                    holes = Image.new('L', image.size)
                    holes.paste(local_holes, bounds[:2])
                silhouette = ImageChops.lighter(binary, holes)
                default_width = {'solid': 2, 'shimmer': 3, 'holographic': 8}[self.outline_style]
                radius = max(1, round((self.outline_width if self.outline_width is not None else default_width) * scale))
                # Keep the luminous core on the inner contour of the current
                # silhouette, rather than smoothing or displacing its boundary.
                edge = ImageChops.subtract(silhouette, silhouette.filter(ImageFilter.MinFilter(radius * 2 + 1)))
                if partial:
                    edge = self.shimmer(edge, current[:2], 0 if static else time, renderer.seed, subject.track_id)
                if self.outline_style == 'holographic':
                    layer = holographic_ink(edge.crop(bounds), renderer.hud_colors['subject-outline'],
                                             0 if static else time * self.outline_speed,
                                             stable_number(renderer.seed, 'holographic-edge', subject.track_id))
                    layer.putalpha(layer.getchannel('A').point(lambda v: round(v * opacity)))
                    panel.layer('subject-outline').alpha_composite(layer, bounds[:2])
                else:
                    paste('subject-outline', edge)
            if self.subject_labels:
                cell = max(8, round(30 * scale))
                label_w = cell * 5
                hx, hy = current[2], y0
                span = max(3, round(10 * scale)) * self.subject_caret_scale
                stroke = max(2, round(6 * scale * self.subject_caret_scale))
                caret_y = round(hy - self.subject_head_gap * scale - stroke / 2)
                title_tile = Image.new('L', (label_w, cell))
                for i in range(5):
                    tile = renderer.code_mask(stable_number(renderer.seed, subject.track_id, 'title', i) % 192, cell)
                    title_tile.paste(tile, (i * cell, 0))
                ink_bounds = title_tile.getbbox()
                if ink_bounds is None:
                    continue
                title_tile = title_tile.crop(ink_bounds)
                label_x = round(hx - (title_tile.width - 1) / 2)
                label_y = round(caret_y - span * .55 - stroke / 2 - self.subject_title_gap * scale - title_tile.height)
                # Keep the same head/caret/title distances at frame edges.
                # Pillow crops offscreen ink independently; an offscreen title
                # must not hide its still-visible caret or shift the stack.
                title = Image.new('L', image.size)
                title.paste(title_tile, (label_x, label_y))
                paste('subject-labels', title)
                caret = Image.new('L', image.size)
                ImageDraw.Draw(caret).line([(hx - span, caret_y - span * .55), (hx, caret_y),
                                           (hx + span, caret_y - span * .55)], fill=255,
                                          width=stroke, joint='curve')
                paste('subject-carets', caret)
        self.anchors = active
        if behind:
            # Clip the final emission, including both regular bloom and neon.
            # Union occlusion protects other subjects as well as this stream's owner.
            before = image.copy()
            renderer.composite_panel(image, behind, 0, 0)
            image.paste(before, (0, 0), union)
        # Layers stay separate so opacity, blur, colors, and neon remain per element.
        if panel.layers:
            renderer.composite_panel(image, panel, 0, 0)
