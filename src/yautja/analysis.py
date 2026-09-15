"""Readable search/analysis HUD with deterministic, decorative telemetry."""
from functools import lru_cache
from importlib.resources import files
import io
import math
import re

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from .signal import stable_number

ANALYSIS_OPTIONS = ('analysis', 'analysis_speed', 'analysis_blink_rate', 'analysis_margin', 'analysis_outline_width')
ANALYSIS_ELEMENTS = ('analysis-grid', 'analysis-text', 'analysis-outline')


@lru_cache(maxsize=32)
def analysis_font(size):
    return ImageFont.truetype(io.BytesIO(files('yautja').joinpath(
        'assets/fonts/Michroma-Regular.ttf').read_bytes()), size)


def category(label):
    """Use only detector labels, with no guessed identities or specifications."""
    text = re.sub(r'[^A-Z0-9 /-]', '', label.upper()).strip()
    return text[:32] or 'OBJECT'


class AnalysisHUD:
    def __init__(self, *, analysis=False, analysis_speed=1., analysis_blink_rate=2., analysis_margin=.035,
                 analysis_outline_width=2.4):
        for name, value, low, high in (
            ('analysis-speed', analysis_speed, 0, 5),
            ('analysis-blink-rate', analysis_blink_rate, 0, 4),
            ('analysis-margin', analysis_margin, .01, .15), ('analysis-outline-width', analysis_outline_width, .5, 12)):
            if not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f'--{name} must be between {low} and {high}')
        self.analysis = bool(analysis)
        self.analysis_speed, self.analysis_blink_rate = analysis_speed, analysis_blink_rate
        self.analysis_margin = analysis_margin
        self.analysis_outline_width = analysis_outline_width
        self.font = analysis_font
        self.shot, self.origin, self.last_time = None, None, None
        self.selected, self.previous, self.cycle = None, None, None
        self.phase = 'SEARCH'
        self.text_boxes = []

    def report(self, hud=True):
        return {**{key: getattr(self, key) for key in ANALYSIS_OPTIONS},
                'analysis': bool(hud and self.analysis),
                'analysis_phase': self.phase if hud and self.analysis else 'OFF',
                'analysis_track': self.selected if hud and self.analysis else None,
                'analysis_numbers': 'seeded decorative telemetry, not measurements'}

    def state(self, subjects, time, shot, static=False):
        visible = {s.track_id: s for s in subjects if s.opacity > .25 and np.any(s.mask >= .5)}
        if self.origin is None or shot != self.shot or (self.last_time is not None and time < self.last_time):
            self.origin, self.selected, self.previous, self.cycle = time, None, None, None
        self.shot, self.last_time = shot, time
        elapsed = max(0., time - self.origin) * self.analysis_speed
        cycle, phase = int(elapsed // 6.), elapsed % 6.
        if self.selected is not None and self.selected not in visible:
            self.origin, self.selected, self.cycle = time, None, None
            cycle, phase = 0, 0.
        if cycle != self.cycle:
            self.previous, self.selected, self.cycle = self.selected, None, cycle
        self.phase = 'SEARCH' if phase < .9 else 'ACQUIRE' if phase < 1.4 else 'ANALYSIS' if phase < 3.8 else 'HOLD'
        if static:
            self.phase, phase = 'HOLD', 5.
        if self.phase != 'SEARCH' and self.selected is None and visible:
            choices = sorted(visible, key=lambda key: (-np.count_nonzero(visible[key].mask >= .5), key))
            index = (choices.index(self.previous) + 1) % len(choices) if self.previous in choices else 0
            self.selected = choices[index]
        subject = visible.get(self.selected)
        if subject is None:
            self.phase = 'SEARCH'
        return subject, phase, elapsed

    def text_block(self, layer, lines, box, size, ink):
        """Fit complete text inside its reserved box, including portrait outputs."""
        x, y, width, height = map(int, box)
        if not lines or width < 3 or height < 3:
            return None
        # Supersampling retains readable strokes at README preview sizes.
        ss = 3
        for pixels in range(max(6, round(size * ss)), 2, -1):
            font = self.font(pixels)
            wrapped = []
            for line in lines:
                current = ''
                for word in line.split():
                    candidate = (current + ' ' + word).strip()
                    if current and font.getlength(candidate) > width * ss:
                        wrapped.append(current)
                        current = word
                    else:
                        current = candidate
                wrapped.append(current)
            bounds = font.getbbox('Ag')
            line_height = max(1, round((bounds[3] - bounds[1]) * 1.45))
            if max(font.getlength(line) for line in wrapped) <= width * ss and line_height * len(wrapped) <= height * ss:
                break
        else:
            return None
        tile = Image.new('L', (width * ss, line_height * len(wrapped)))
        draw = ImageDraw.Draw(tile)
        for row, line in enumerate(wrapped):
            draw.text((0, row * line_height - bounds[1]), line, font=font, fill=255,
                      stroke_width=max(0, pixels // 40))
        tile = tile.resize((width, max(1, math.ceil(tile.height / ss))), Image.Resampling.LANCZOS)
        bounds = tile.getbbox()
        if bounds:
            rgba = Image.new('RGBA', tile.size, (*ink[:3], 0))
            rgba.putalpha(tile)
            layer.paste(rgba, (x, y))
            placed = (x + bounds[0], y + bounds[1], x + bounds[2], y + bounds[3])
            self.text_boxes.append(placed)
            return placed
        return None

    def draw(self, renderer, image, subjects, time, shot, static=False):
        if not self.analysis:
            return
        self.font = renderer.typography.font
        subject, phase, elapsed = self.state(subjects, time, shot, static)
        width, height = image.size
        margin = max(2, round(min(width, height) * self.analysis_margin))
        self.text_boxes = []
        panel = renderer.hud_panel(image.size, *ANALYSIS_ELEMENTS)
        grid, text = panel.layer('analysis-grid'), panel.layer('analysis-text')
        grid_ink, text_ink = renderer.hud_ink('analysis-grid'), renderer.hud_ink('analysis-text')
        # Side columns leave the central scene and faces readable. Portrait
        # layouts put the same compact blocks at the top and bottom corners.
        column = min(round(width * .28), max(1, (width - 3 * margin) // 2))
        grid_size = min(column, round(height * .31))
        gx, gy = width - margin - grid_size, round(height * .12)
        stroke = max(1, round(min(width, height) / 540))
        d = ImageDraw.Draw(grid)
        dim = renderer.hud_ink('analysis-grid', .38)
        for i in range(11):
            px, py = gx + round(grid_size * i / 10), gy + round(grid_size * i / 10)
            d.line((px, gy, px, gy + grid_size), fill=dim, width=stroke)
            d.line((gx, py, gx + grid_size, py), fill=dim, width=stroke)
        if self.phase == 'SEARCH':
            # Independent smooth XY sweeps, avoiding per-frame random jumps.
            px = .5 + .46 * math.sin(elapsed * 2.3 + .3)
            py = .5 + .46 * math.sin(elapsed * 1.7 + 1.8)
        else:
            yy, xx = np.nonzero(subject.mask >= .5)
            px, py = xx.mean() / subject.mask.shape[1], yy.mean() / subject.mask.shape[0]
        cx, cy = gx + round(grid_size * px), gy + round(grid_size * py)
        d.line((cx, gy, cx, gy + grid_size), fill=grid_ink, width=stroke)
        d.line((gx, cy, gx + grid_size, cy), fill=grid_ink, width=stroke)
        radius = max(2, stroke * 3)
        d.rectangle((cx - radius, cy - radius, cx + radius, cy + radius), outline=grid_ink, width=stroke)
        identity = subject.track_id if subject else 0
        counter = lambda key: f'{stable_number(renderer.seed, shot, identity, key) % 100000:05d}'
        font_size = max(8, min(width, height) * .027)
        left = ['CRITERIA', '--------------', f'CLAS {category(subject.label) if subject else "SEARCH"}',
                f'SIZE {counter("size")}', f'MOVE {counter("move")}', f'CODE {counter("code")}',
                f'RNGE {counter("range")}', f'SCAN {counter("scan")}']
        count = 8 if self.phase == 'HOLD' else max(3, min(8, 3 + int(max(0, phase - 1.4) * 3)))
        self.text_block(text, left[:count], (margin, height * .24, column, height * .36), font_size, text_ink)
        right_y = gy + grid_size + margin
        right = [f'SCAN MODE {counter("mode")}', self.phase,
                 f'PRTY {counter("priority")}', f'X {counter("x")} Y {counter("y")}']
        if self.phase in ('ANALYSIS', 'HOLD'):
            right += ['ANALYSIS', f'OBJC {counter("object")}', f'STAT {counter("status")}']
        self.text_block(text, right, (width - margin - column, right_y, column,
                                     min(height * .38, height - margin - right_y)), font_size, text_ink)
        if subject is not None:
            binary = Image.fromarray(np.uint8(subject.mask >= .5) * 255).resize(image.size, Image.Resampling.NEAREST)
            bounds = binary.getbbox()
            # Never smooth the contour position: draw the current tracked mask.
            blink = static or self.phase != 'ANALYSIS' or not self.analysis_blink_rate or (
                (phase - 1.4) / max(self.analysis_speed, .001) * self.analysis_blink_rate) % 1 < .55
            if blink:
                ss = 2
                fine = Image.fromarray(np.uint8(np.clip(subject.mask, 0, 1) * 255)).resize(
                    (width * ss, height * ss), Image.Resampling.BILINEAR).point(lambda v: 255 if v >= 128 else 0)
                outline_width = max(1, round(self.analysis_outline_width * min(width, height) / 1080 * ss))
                edge = ImageChops.subtract(fine, fine.filter(ImageFilter.MinFilter(2 * outline_width + 1)))
                edge = edge.resize(image.size, Image.Resampling.LANCZOS)
                edge = edge.point(lambda v: round(v * min(1., subject.opacity)))
                ink = renderer.hud_ink('analysis-outline')
                layer = Image.new('RGBA', image.size, (*ink[:3], 0))
                layer.putalpha(edge)
                panel.replace('analysis-outline', layer)
            # A description travels beside its subject when space allows. The
            # lower safe band is a fallback, never clipping off a frame edge.
            x0, y0, x1, y1 = bounds
            desc_width = min(width - 2 * margin, round(width * .36))
            desc_height = min(height * .14, height - 2 * margin)
            candidates = [(x1 + margin, (y0 + y1) / 2),
                          (x0 - margin - desc_width, (y0 + y1) / 2),
                          ((x0 + x1 - desc_width) / 2, height - margin - desc_height)]
            def placed(pos):
                return (int(np.clip(pos[0], margin, width - margin - desc_width)),
                        int(np.clip(pos[1], margin, height - margin - desc_height)))
            def overlap(pos):
                x, y = placed(pos)
                return sum(max(0, min(x + desc_width, b[2]) - max(x, b[0])) *
                           max(0, min(y + desc_height, b[3]) - max(y, b[1]))
                           for b in [*self.text_boxes, (gx, gy, gx + grid_size, gy + grid_size)])
            dx, dy = placed(min(candidates, key=overlap))
            self.text_block(text, ['VISUAL: ' + category(subject.label), f'TRACK {identity:03d}'],
                            (dx, dy, desc_width, desc_height), font_size * 1.05, text_ink)
        renderer.composite_panel(image, panel, 0, 0)
