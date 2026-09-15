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

SIGNAL_OPTIONS = ('scene_mode', 'scene_tint', 'scene_tint_strength', 'scene_exposure', 'scene_highlights',
                  'subject_outline', 'subject_code', 'subject_labels',
                  'code_size', 'code_speed', 'code_density', 'subject_head_gap', 'subject_title_gap', 'subject_caret_scale')
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
                 subject_title_gap=18., subject_caret_scale=1., scene_highlights=0.):
        if scene_mode not in ('thermal', 'source'):
            raise ValueError('--scene-mode must be thermal or source')
        self.tint = parse_hex(scene_tint)
        for key, value, low, high in (
            ('scene-tint-strength', scene_tint_strength, 0, 1), ('scene-exposure', scene_exposure, .1, 2),
            ('scene-highlights', scene_highlights, 0, 1),
            ('code-size', code_size, 8, 80), ('code-speed', code_speed, 0, 5), ('code-density', code_density, 0, 1),
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
        pitch_x, pitch_y = cell * 1.15, cell * 1.45
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
                mask.paste(tile, (round(col * pitch_x), round(row * pitch_y)))
        return mask

    def draw(self, renderer, image, subjects, time, shot_id):
        if not (self.subject_outline or self.subject_code or self.subject_labels):
            return
        dt = None if self.time is None else time - self.time
        if shot_id != self.shot or dt is None or dt <= 0 or dt > .5:
            self.anchors.clear()
            dt = None
        self.time, self.shot = time, shot_id
        active = {}
        panel = renderer.hud_panel(image.size, *SUBJECT_ELEMENTS)
        scale = min(image.size) / 1080
        for subject in sorted(subjects, key=lambda s: s.track_id):
            if subject.opacity <= 0:
                continue
            mask = Image.fromarray(np.uint8(np.clip(subject.mask, 0, 1) * 255)).resize(image.size, Image.Resampling.BILINEAR)
            binary = mask.point(lambda v: 255 if v >= 128 else 0)
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
                panel.layer(element).alpha_composite(layer)

            if self.subject_code:
                code = self.streams(image.size, bounds, current[:2], time, renderer.seed, subject.track_id, renderer.code_mask)
                paste('subject-code', ImageChops.multiply(code, mask))
            if self.subject_outline:
                # Outline the visible silhouette, without tracing segmentation
                # pinholes in clothing and equipment as extra interior contours.
                exterior = Image.new('L', (image.width + 2, image.height + 2))
                exterior.paste(binary, (1, 1))
                ImageDraw.floodfill(exterior, (0, 0), 255)
                holes = ImageChops.invert(exterior.crop((1, 1, image.width + 1, image.height + 1)))
                silhouette = ImageChops.lighter(binary, holes)
                radius = max(1, round(2 * scale))
                # A single inner edge is half the width of the previous
                # two-sided gradient and stays inside the current silhouette.
                edge = ImageChops.subtract(silhouette, silhouette.filter(ImageFilter.MinFilter(radius * 2 + 1)))
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
        # Layers stay separate so opacity, blur, colors, and neon remain per element.
        if panel.layers:
            renderer.composite_panel(image, panel, 0, 0)
