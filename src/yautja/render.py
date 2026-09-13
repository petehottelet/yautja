"""Deterministic thermal color and Yautja HUD. No browser or network needed."""
from __future__ import annotations

import hashlib
import io
import json
import math
from importlib.resources import files

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from .thermal import resolve_thermal
from .colors import resolve_colors
from .display import DisplayEffects, highlight_glow
from .target import TargetOverlay, target_colors as parse_target_colors
from .waveform import WAVE_STYLES, inkblot_mask
from .hud import HudPanel, hud_blurs, hud_opacities
from .looks import SPECTRUM, ThermalTransfer, resolve_look

STOPS = [(0, (2, 3, 23)), (.12, (16, 9, 94)), (.28, (37, 25, 202)),
         (.43, (0, 132, 239)), (.56, (0, 222, 170)), (.68, (201, 240, 37)),
         (.79, (255, 157, 12)), (.9, (255, 48, 25)), (1, (255, 249, 209))]

IRONBOW = [(0, (2, 0, 10)), (.18, (12, 15, 70)), (.30, (55, 18, 140)),
           (.45, (145, 20, 135)), (.60, (225, 45, 65)), (.73, (252, 132, 25)),
           (.86, (255, 220, 48)), (.96, (255, 250, 171)), (1, (255, 255, 240))]

PALETTES = {
    'thermal-spectrum': SPECTRUM,
    'yautja': STOPS,
    'ironbow': IRONBOW,
    'abyss': [(0, (5, 12, 15)), (.16, (5, 17, 25)), (.32, (4, 34, 61)),
              (.43, (8, 62, 85)), (.51, (25, 106, 93)), (.56, (134, 115, 19)),
              (.60, (158, 41, 3)), (.69, (244, 114, 6)), (.78, (255, 197, 56)),
              (.86, (255, 243, 159)), (.94, (255, 255, 232)), (1, (255, 255, 255))],
    'redline': [(0, (8, 9, 11)), (.20, (8, 9, 11)), (.27, (12, 16, 30)),
                (.32, (13, 50, 137)), (.43, (25, 92, 235)), (.52, (36, 110, 248)),
                (.555, (15, 19, 28)), (.60, (85, 17, 12)), (.68, (175, 24, 16)),
                (.78, (225, 35, 29)), (.89, (236, 48, 64)), (1, (242, 75, 119))],
    'green-phosphor': [(0, (0, 2, 0)), (.25, (0, 35, 9)), (.5, (16, 100, 30)),
                       (.75, (81, 194, 75)), (1, (210, 255, 184))],
    'amber-phosphor': [(0, (3, 1, 0)), (.25, (48, 17, 0)), (.5, (130, 61, 5)),
                       (.75, (222, 145, 35)), (1, (255, 239, 170))],
    'white-hot': [(0, (0, 0, 0)), (1, (255, 255, 255))],
    'black-hot': [(0, (255, 255, 255)), (1, (0, 0, 0))],
    'virtualboy': [(0, (0, 0, 0)), (.2, (20, 0, 0)), (.45, (80, 0, 0)),
                    (.7, (170, 0, 0)), (1, (255, 0, 0))],
}


def vhs_frame(image, time, seed):
    """Seeded tape-style bandwidth loss, chroma bleed, wobble, and dropouts."""
    rgb = np.asarray(image, dtype=np.float32)
    height, width = rgb.shape[:2]
    scale = width / 640
    rng = np.random.default_rng((seed * 1009 + round(time * 24) + 0x564853) & 0xffffffff)
    y = .299 * rgb[..., 0] + .587 * rgb[..., 1] + .114 * rgb[..., 2]
    u, v = .492 * (rgb[..., 2] - y), .877 * (rgb[..., 0] - y)

    def bandwidth(channel, columns):
        return np.asarray(Image.fromarray(channel).resize((max(1, min(width, columns)), height), Image.Resampling.BOX)
                          .resize((width, height), Image.Resampling.BILINEAR))

    y = .55 * y + .45 * bandwidth(y, 260)
    u, v = bandwidth(u, max(1, width // 8)), bandwidth(v, max(1, width // 8))
    # Chroma trails right without wrapping the opposite edge into the frame.
    delay = max(1, round(scale * 2))
    u = u[:, np.clip(np.arange(width) - delay, 0, width - 1)]
    v = v[:, np.clip(np.arange(width) - delay * 2, 0, width - 1)]
    y = y * (1 + .012 * np.sin(time * 5.3)) + rng.normal(0, .8, y.shape)
    rgb = np.stack((y + v / .877, y - .39465 * u - .5806 * v, y + u / .492), axis=2)
    rows = np.arange(height)
    knots = np.linspace(0, max(1, height - 1), min(height, 24))
    drift = np.interp(rows, knots, rng.normal(0, .55, len(knots)))
    shifts = scale * (drift + .6 * np.sin(rows / max(1, height) * 20 + time * 4.1))
    band = max(1, round(height * .018))
    band_y = min(height - band, round(height * (.95 + .015 * np.sin(time * 2.7))))
    shifts[band_y:band_y + band] += scale * (4 + 2 * np.sin(time * 13))
    sample_x = np.clip(np.arange(width)[None, :] - shifts[:, None], 0, width - 1)
    left = sample_x.astype(np.int32)
    fraction = (sample_x - left)[..., None]
    rgb = (rgb[rows[:, None], left] * (1 - fraction) +
           rgb[rows[:, None], np.minimum(left + 1, width - 1)] * fraction)
    rgb[band_y:band_y + band] += rng.normal(0, 9, (band, width, 1))
    # Short, occasional signal dropouts rather than a permanent overlay scratch.
    if rng.random() < .45:
        length = max(1, round(width * rng.uniform(.08, .24)))
        x = int(rng.integers(0, max(1, width - length + 1)))
        row = int(rng.integers(0, height))
        patch = rgb[row:row + max(1, round(height / 360)), x:x + length]
        patch[:] = patch * .65 + 225 * .35
    return Image.fromarray(np.uint8(np.clip(rgb, 0, 255)))


def noise_sample(indices, seed):
    # Same integer hash as the original web renderer (modulo 2**32).
    v = np.asarray(indices).astype(np.uint32) ^ np.uint32(seed & 0xffffffff)
    v = v * np.uint32(0x45d9f3b)
    v = (v ^ (v >> 16)) * np.uint32(0x45d9f3b)
    return (v ^ (v >> 16)).astype(np.float64) / 0xffffffff * 2 - 1


def wave_noise(position, seed):
    index = np.floor(position)
    fraction = position - index
    blend = fraction * fraction * (3 - 2 * fraction)
    a, b = noise_sample(index, seed), noise_sample(index + 1, seed)
    return a + (b - a) * blend


def procedural_wave(time, seed=42, count=256):
    i = np.arange(count)
    p = i + time * 42
    envelope = ((wave_noise(p * .035, seed) + 1) * .5) ** 1.25
    carrier = np.sin(p * 1.85 + wave_noise(p * .11, seed ^ 0x93ab) * 2) * .72
    carrier += wave_noise(p * .83, seed ^ 0x5f21) * .28
    taper = np.minimum(1, np.minimum(i / 10, (count - 1 - i) / 10))
    return carrier * (.12 + envelope * .88) * taper


def timecode(seconds):
    """Elapsed output time, milliseconds (not SMPTE/drop-frame)."""
    ms = max(0, round(seconds * 1000))
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    sec, ms = divmod(ms, 1000)
    return f'{hours:02}:{minutes:02}:{sec:02}.{ms:03}'


def lcd_timecode(text, height, color=(255, 118, 98)):
    """Draw a seven-segment clock from polygons, without a font asset."""
    segments = ('abcdef', 'bc', 'abdeg', 'abcdg', 'bcfg',
                'acdfg', 'acdefg', 'abc', 'abcdefg', 'abcdfg')
    polygons = {}
    for name, y in (('a', 1), ('g', 10), ('d', 19)):
        polygons[name] = [(2, y), (3, y-1), (9, y-1), (10, y), (9, y+1), (3, y+1)]
    for name, x, y0, y1 in (('f', 1, 2.3, 8.7), ('b', 11, 2.3, 8.7),
                             ('e', 1, 11.3, 17.7), ('c', 11, 11.3, 17.7)):
        polygons[name] = [(x, y0), (x+1, y0+1), (x+1, y1-1),
                          (x, y1), (x-1, y1-1), (x-1, y0+1)]
    ss = 3
    height = max(6, round(height))
    scale = height * ss / 20
    width = max(1, round((sum(7 if c in ':.' else 15 for c in text) - 3) * height / 20))
    tile = Image.new('RGBA' if len(color) == 4 else 'RGB', (width * ss, height * ss))
    draw = ImageDraw.Draw(tile)
    x = 0
    for char in text:
        if char in ':.':
            # Snap tiny dots to pixels so colons retain a gap at preview sizes.
            dot_size = max(1, round(height / 10))
            dot_x = round((x + 2) * height / 20 - dot_size / 2)
            tops = (round(height * .3), round(height * .65)) if char == ':' else (height - dot_size,)
            for y in tops:
                draw.rectangle((dot_x * ss, y * ss, (dot_x + dot_size) * ss - 1,
                                (y + dot_size) * ss - 1), fill=color)
            x += 7
        else:
            for name in segments[int(char)]:
                draw.polygon([((x+px)*scale, py*scale) for px, py in polygons[name]], fill=color)
            x += 15
    tile = tile.resize((width, height), Image.Resampling.LANCZOS)
    bounds = tile.getbbox()
    # Trim side bearings only: dots keep their vertical clock alignment.
    return tile.crop((bounds[0], 0, bounds[2], height)) if bounds else tile


def load_glyph_font():
    """Compile the bundled polygon shapes in memory for antialiased rendering."""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    selected = {}
    shapes = json.loads(files('yautja').joinpath('assets/glyphs.json').read_text(encoding='utf-8'))
    for item in shapes:
        char = item['character']
        pen = TTGlyphPen(None)
        for contour in item['contours']:
            pen.moveTo(tuple(contour[0]))
            for point in contour[1:]:
                pen.lineTo(tuple(point))
            pen.closePath()
        selected[char] = pen.glyph()
    if not selected:
        raise ValueError('Bundled character shapes are missing')
    builder = FontBuilder(1000, isTTF=True)
    order = ['.notdef', *selected]
    builder.setupGlyphOrder(order)
    builder.setupCharacterMap({ord(char): char for char in selected})
    builder.setupGlyf({'.notdef': TTGlyphPen(None).glyph(), **selected})
    builder.setupHorizontalMetrics({name: (1000, 0) for name in order})
    builder.setupHorizontalHeader(ascent=850, descent=-200)
    builder.setupNameTable({'familyName': 'Yautja HUD', 'styleName': 'Regular', 'uniqueFontIdentifier': 'YautjaHUD'})
    builder.setupOS2(sTypoAscender=850, sTypoDescender=-200, usWinAscent=1000, usWinDescent=250)
    builder.setupPost()
    buffer = io.BytesIO()
    builder.save(buffer)
    return buffer.getvalue(), sorted(selected)


class Renderer:
    def __init__(self, width, height, *, look_preset=None, **options):
        self.look_preset = look_preset
        self._configure(width, height, **resolve_look(look_preset, options))

    def _configure(self, width, height, *, seed=42, grain=None, glow=.65,
                 show_timecode=False, timecode_start=0., thermal='classic', sensor_resolution=256, verbose=False,
                 sensor_texture=False, palette='auto', pixelation=None, scanlines=None, vhs=False,
                 palette_colors=None, hud_theme='standard', hud_colors=None, random_colors=False, hud=True,
                 target_colors=None, target_acquire=.8, target_flash=True, target_flash_rate=1.5, target_scale=1.,
                 motion_blur=0., crt_bleed=0., crt_vertical_lines=False, crt_strength=.12,
                 heat_glow=0., heat_glow_speed=1., wave_style='trace', wave_width=None, wave_height=None, wave_detail=.6,
                 target_stroke=0., target_stroke_colors=None, hud_blur=0., hud_blur_elements=None,
                 hud_opacity=1., hud_opacity_elements=None, target_shape='triangle',
                 thermal_levels=None, thermal_band_softness=None, thermal_black_point=0.,
                 thermal_white_point=1., thermal_gamma=1., thermal_softness=0.):
        self.width, self.height = width, height
        self.transfer = ThermalTransfer(thermal_levels, thermal_band_softness, thermal_black_point,
                                        thermal_white_point, thermal_gamma, thermal_softness)
        self.seed, self.glow = seed, glow
        self.grain = (.035 if sensor_texture else 0.) if grain is None else grain
        self.pixelation = (sensor_resolution if sensor_texture else 0) if pixelation is None else pixelation
        self.scanlines = sensor_texture if scanlines is None else scanlines
        self.vhs = vhs
        self.hud = bool(hud)
        self.show_timecode, self.timecode_start = bool(hud and show_timecode), timecode_start
        self.thermal, self.verbose = resolve_thermal(thermal), bool(hud and verbose)
        self.sensor_texture, self.sensor_resolution = sensor_texture, sensor_resolution
        self.colors = resolve_colors(PALETTES, palette=palette, palette_colors=palette_colors,
                                     hud_theme=hud_theme, hud_colors=hud_colors,
                                     random_colors=random_colors, seed=seed)
        self.palette_name, self.palette = self.colors.palette_name, self.colors.palette
        self.hud_theme, self.hud_colors = self.colors.hud_theme, self.colors.hud
        self.target_color_override = parse_target_colors(target_colors)
        if self.target_color_override:
            self.hud_colors['target'], self.hud_colors['target-flash'] = self.target_color_override
        self.hud_blur = hud_blur
        self.hud_blurs = hud_blurs(hud_blur, hud_blur_elements)
        self.hud_opacity = hud_opacity
        self.hud_opacities = hud_opacities(hud_opacity, hud_opacity_elements)
        self.hud_blur_pixels = {key: value * min(width, height) / 1080 for key, value in self.hud_blurs.items()}
        self.target_overlay = TargetOverlay(target_acquire, target_flash_rate if target_flash else 0, target_scale,
                                            stroke=target_stroke, stroke_colors=target_stroke_colors,
                                            blur=self.hud_blurs['target'], opacity=self.hud_opacities['target'],
                                            flash_opacity=self.hud_opacities['target-flash'], shape=target_shape)
        self.target_flash = target_flash
        self.display = DisplayEffects(motion_blur, crt_bleed)
        self.previous_source = None
        self.crt_vertical_lines, self.crt_strength = crt_vertical_lines, crt_strength
        self.heat_glow, self.heat_glow_speed = heat_glow, heat_glow_speed
        if wave_style not in WAVE_STYLES:
            raise ValueError('Unknown waveform style: ' + wave_style)
        self.wave_style = wave_style
        self.wave_width = .12 if wave_width is None else wave_width
        self.wave_height = .96 if wave_height is None else wave_height
        self.wave_detail = wave_detail
        for value, lo, hi, flag in ((self.wave_width, .02, .3, 'wave-width'), (self.wave_height, .1, 1, 'wave-height'),
                                   (wave_detail, 0, 1, 'wave-detail')):
            if not math.isfinite(value) or not lo <= value <= hi:
                raise ValueError(f'--{flag} must be between {lo} and {hi}')
        for value, high, flag in ((crt_strength, 1, 'crt-strength'), (heat_glow, 1, 'heat-glow'), (heat_glow_speed, 5, 'heat-glow-speed')):
            if not math.isfinite(value) or not 0 <= value <= high:
                raise ValueError(f'--{flag} must be between 0 and {high}')
        # Alpha draws black ink over the image; screen blending would erase it.
        self.overlay_mode = 'RGBA' if self.hud_theme == 'custom' or self.hud_colors['waveform'] == (0, 0, 0) else 'RGB'
        self.annotation_positions = {}
        if self.thermal != 'classic':
            from .thermal import LowDetailHeatField, CinematicHeatField, SurfaceHeatField, VeryDetailedHeatField
            field = {'low-detail': LowDetailHeatField, 'cinematic': CinematicHeatField, 'detailed': SurfaceHeatField,
                     'very-detailed': VeryDetailedHeatField}[self.thermal]
            self.heat_field = field(width, height, sensor_resolution, seed=seed,
                                    legacy_bands=thermal_levels is None)
        self.scale = min(1.5, max(.5, width / 1100, min(width, height) / 900))
        self.color = self.hud_colors['waveform']
        self.font_data, self.font_chars = load_glyph_font() if self.hud else (None, [])
        self.fonts, self.tiles = {}, {}
        self.annotation_pool = None
        self.callout_segments = None

    def hud_ink(self, element, opacity=1.):
        color = self.hud_colors[element]
        if self.overlay_mode == 'RGBA':
            return (*color, round(255 * opacity))
        return tuple(round(v * opacity) for v in color)

    def glyph(self, value, height, numeral=False, element='waveform-glyphs'):
        height = max(8, round(height))
        color = self.hud_ink(element)
        key = (value, height, numeral, color)
        if key in self.tiles:
            return self.tiles[key]
        ss = 3
        tile = Image.new(self.overlay_mode, (round(height * .85) * ss, height * ss))
        choices = [c for c in self.font_chars if c.isdigit() == numeral]
        if choices:
            if height not in self.fonts:
                self.fonts[height] = ImageFont.truetype(io.BytesIO(self.font_data), height * ss)
            font = self.fonts[height]
            char = choices[value % len(choices)]
            box = font.getbbox(char)
            mask = Image.new(self.overlay_mode, (max(1, box[2] - box[0]), max(1, box[3] - box[1])))
            ImageDraw.Draw(mask).text((-box[0], -box[1]), char, font=font, fill=color)
            ratio = min(tile.width / mask.width, tile.height / mask.height)
            mask = mask.resize((max(1, round(mask.width * ratio)), max(1, round(mask.height * ratio))), Image.Resampling.LANCZOS)
            tile.paste(mask, ((tile.width - mask.width) // 2, (tile.height - mask.height) // 2))
        else:
            raise ValueError('Bundled alphabet is incomplete')
        tile = tile.resize((tile.width // ss, height), Image.Resampling.LANCZOS)
        self.tiles[key] = tile
        return tile

    def composite(self, image, overlay, x, y):
        if overlay.mode == 'RGBA':
            base = image.crop((x, y, x + overlay.width, y + overlay.height)).convert('RGBA')
            if self.glow:
                bloom = overlay.filter(ImageFilter.GaussianBlur(max(.5, self.scale * 2)))
                bloom.putalpha(bloom.getchannel('A').point(lambda v: round(v * self.glow)))
                base = Image.alpha_composite(base, bloom)
            image.paste(Image.alpha_composite(base, overlay).convert('RGB'), (x, y))
            return
        if self.glow:
            bloom = overlay.filter(ImageFilter.GaussianBlur(max(.5, self.scale * 2)))
            bloom = bloom.point(lambda v: round(v * self.glow))
            overlay = ImageChops.add(overlay, bloom)
        image.paste(ImageChops.screen(image.crop((x, y, x + overlay.width, y + overlay.height)), overlay), (x, y))

    def hud_panel(self, size, *elements):
        return HudPanel(self.overlay_mode, size, self.hud_blur_pixels, elements, self.hud_opacities)

    def composite_panel(self, image, panel, x, y):
        artwork, pad = panel.finish()
        self.composite(image, artwork, x - pad, y - pad)

    def callout_geometry(self):
        if self.callout_segments is None:
            shapes = json.loads(files('yautja').joinpath('assets/glyphs.json').read_text(encoding='utf-8'))
            # Reuse the broad, nine-segment geometry already bundled in the HUD.
            self.callout_segments = next(item['contours'] for item in shapes if item['character'] == '9')
        return self.callout_segments

    def callout_glyph(self, pattern, height):
        """Dim full outlines behind shaded, illuminated segments."""
        height = max(8, round(height))
        key = (pattern, height, 'callout')
        if key in self.tiles:
            return self.tiles[key]
        ss = 3
        width = round(height * .85)
        segments = self.callout_geometry()
        points = np.concatenate(segments)
        left, bottom = points.min(axis=0)
        right, top = points.max(axis=0)
        ratio = min((width - 2) * ss / (right - left), (height - 2) * ss / (top - bottom))
        ox, oy = (width * ss - (right - left) * ratio) / 2, (height * ss - (top - bottom) * ratio) / 2
        mask = Image.new('L', (width * ss, height * ss))
        outlines = Image.new('L', mask.size)
        fill, edges = ImageDraw.Draw(mask), ImageDraw.Draw(outlines)
        for i, segment in enumerate(segments):
            polygon = [((x - left) * ratio + ox, (top - y) * ratio + oy) for x, y in segment]
            edges.line(polygon + [polygon[0]], fill=58, width=max(1, round(.6 * ss)), joint='curve')
            if pattern & (1 << i):
                fill.polygon(polygon, fill=255)
        gradient = np.linspace(255, 145, mask.height, dtype=np.uint8)[:, None]
        shading = Image.fromarray(np.broadcast_to(gradient, (mask.height, mask.width)).copy())
        tile = ImageChops.lighter(outlines, ImageChops.multiply(mask, shading))
        tile = tile.resize((width, height), Image.Resampling.LANCZOS)
        self.tiles[key] = tile
        return tile

    def callout_symbols(self, track_id):
        """Give each track a stable, varied row of six decorative shapes."""
        if self.annotation_pool is None:
            count = len(self.callout_geometry())
            self.annotation_pool = tuple(pattern for pattern in range(1 << count)
                                         if 2 <= pattern.bit_count() <= 6)
        # Deal disjoint rows to consecutive tracks, then reshuffle the next batch.
        # No frame time or detection order enters the label, so it cannot flicker.
        batch, row = divmod(max(0, track_id - 1), len(self.annotation_pool) // 6)
        salt = f'{self.seed}:callouts:{batch}:'.encode('ascii')
        deck = sorted(self.annotation_pool, key=lambda symbol: hashlib.sha256(salt + str(symbol).encode('ascii')).digest())
        return tuple(deck[row * 6:row * 6 + 6])

    def annotation_layout(self, subjects):
        """Place readable labels beside silhouettes with short boundary leaders."""
        s = self.scale
        left, top = round(116 * s), round(100 * s)
        right, bottom = self.width - round(18 * s), self.height - round(18 * s)
        spacing, gap = max(2, round(3 * s)), max(6, round(14 * s))
        glyph_size = round(round(44 * .82 * .9 * s) * .83)
        size = min(max(10, round(glyph_size * .95)), int((right - left - 5 * spacing) / 5.1))
        step = round(size * .85) + spacing
        label_w = step * 6 - spacing
        previous = self.annotation_positions
        self.annotation_positions = {}
        if size < 10 or label_w > right - left or size > bottom - top:
            return []

        # A small occupancy map keeps labels off every subject, including nearby
        # tracks. Layout history is bounded by the visible labels in this frame.
        grid_w = min(320, self.width)
        grid_h = max(1, round(self.height * grid_w / self.width))
        occupied = np.zeros((grid_h, grid_w), dtype=bool)
        prepared = []
        for subject in sorted(subjects, key=lambda sub: sub.track_id):
            mask = subject.mask > .5
            rows, cols = np.nonzero(mask)
            if not len(rows) or subject.opacity <= 0:
                continue
            occupied |= np.asarray(Image.fromarray(mask).resize((grid_w, grid_h), Image.Resampling.NEAREST))
            sx, sy = self.width / mask.shape[1], self.height / mask.shape[0]
            bounds = (cols.min() * sx, rows.min() * sy, (cols.max() + 1) * sx, (rows.max() + 1) * sy)
            center = (float(cols.mean()) * sx, float(rows.mean()) * sy)
            edge = mask.copy()
            edge[1:-1, 1:-1] &= ~(mask[:-2, 1:-1] & mask[2:, 1:-1] & mask[1:-1, :-2] & mask[1:-1, 2:])
            ey, ex = np.nonzero(edge)
            stride = max(1, len(ex) // 512)
            points = np.column_stack(((ex[::stride] + .5) * sx, (ey[::stride] + .5) * sy))
            prepared.append((subject, bounds, center, points))
        integral = np.pad(occupied.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)

        placed = []
        for subject, (x0, y0, x1, y1), (cx, cy), points in prepared:
            preferred_y = y0 + (y1 - y0) * .3
            candidates = [(x, y0 + (y1 - y0) * fraction - size / 2)
                          for fraction in (.2, .5, .8) for x in (x1 + gap, x0 - gap - label_w)]
            candidates += [(x, y) for y in (y0 - gap - size, y1 + gap)
                           for x in (cx - label_w / 2, x0, x1 - label_w)]
            predicted = None
            if subject.track_id in previous:
                px, py, old_cx, old_cy = previous[subject.track_id]
                predicted = (px + cx - old_cx, py + cy - old_cy)
                candidates.insert(0, predicted)
            best = None
            for x, y in candidates:
                x, y = round(np.clip(x, left, right - label_w)), round(np.clip(y, top, bottom - size))
                rect = (x, y, x + label_w, y + size)
                if any(x < other['rect'][2] + gap / 2 and x + label_w > other['rect'][0] - gap / 2
                       and y < other['rect'][3] + gap / 2 and y + size > other['rect'][1] - gap / 2 for other in placed):
                    continue
                gx0, gy0 = int(x * grid_w / self.width), int(y * grid_h / self.height)
                gx1 = min(grid_w, int(np.ceil((x + label_w) * grid_w / self.width)))
                gy1 = min(grid_h, int(np.ceil((y + size) * grid_h / self.height)))
                covered = integral[gy1, gx1] - integral[gy0, gx1] - integral[gy1, gx0] + integral[gy0, gx0]
                if covered > .02 * max(1, (gx1 - gx0) * (gy1 - gy0)):
                    continue
                anchors = np.clip(points, (x, y), (x + label_w, y + size))
                distances = ((anchors - points) ** 2).sum(axis=1)
                nearest = int(distances.argmin())
                length_sq = float(distances[nearest])
                if length_sq > min(72 * s, self.width * .08) ** 2:
                    continue
                score = length_sq + .15 * (y + size / 2 - preferred_y) ** 2
                if predicted is not None:
                    score += .3 * ((x - predicted[0]) ** 2 + (y - predicted[1]) ** 2)
                if best is None or score < best[0]:
                    best = (score, rect, tuple(points[nearest]), tuple(anchors[nearest]))
            if best is None:
                continue
            _, rect, target, anchor = best
            self.annotation_positions[subject.track_id] = (*rect[:2], cx, cy)
            placed.append(dict(subject=subject, rect=rect, target=target, anchor=anchor, size=size, step=step))
            if len(placed) == 8:
                break
        return placed

    def annotate(self, image, subjects):
        s = self.scale
        panel = self.hud_panel(image.size, 'leaders', 'markers', 'callouts')
        leaders = ImageDraw.Draw(panel.layer('leaders'))
        markers = ImageDraw.Draw(panel.layer('markers'))
        layer = panel.layer('callouts')
        for item in self.annotation_layout(subjects):
            subject, size, step = item['subject'], item['size'], item['step']
            x, y = item['rect'][:2]
            cx, cy = item['target']
            color = self.hud_ink('callouts', subject.opacity)
            leaders.line([item['target'], item['anchor']], fill=self.hud_ink('leaders', subject.opacity), width=max(1, round(1.5 * s)))
            radius = max(1, round(2 * s))
            markers.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), outline=self.hud_ink('markers', subject.opacity))
            for i, pattern in enumerate(self.callout_symbols(subject.track_id)):
                ink = self.callout_glyph(pattern, size)
                if self.overlay_mode == 'RGBA':
                    tile = Image.new('RGBA', ink.size, color)
                    tile.putalpha(ink.point(lambda v: round(v * subject.opacity)))
                else:
                    tile = ImageChops.multiply(Image.merge('RGB', (ink,) * 3), Image.new('RGB', ink.size, color))
                layer.paste(tile, (x + i * step, y))
        self.composite_panel(image, panel, 0, 0)

    def render(self, frame, time, wave=None, subjects=(), *, targets=(), shot_id=None, target_static=False):
        if self.display.motion_blur:
            coarse = np.asarray(frame.convert('L').resize((32, 18)), np.float32)
            if self.previous_source is not None and np.abs(coarse - self.previous_source).mean() > 38:
                self.display.reset()
            self.previous_source = coarse
        # All modes are artistic effects, not actual heat measurement.
        if self.thermal != 'classic':
            luma = self.heat_field.build(frame, subjects)
        else:
            rgb = np.asarray(frame, dtype=np.uint8)
            luma = (rgb[..., 0].astype(np.float32) * .2126 + rgb[..., 1] * .7152 + rgb[..., 2] * .0722)
            luma = np.clip((luma - 127.5) * 1.10 + 127.5, 0, 255)
            if self.transfer.levels is None:
                luma = luma.astype(np.uint8)
        return self.render_field(luma, time, wave=wave, subjects=subjects, targets=targets, shot_id=shot_id, target_static=target_static)

    def render_field(self, luma, time, wave=None, subjects=(), *, targets=(), shot_id=None, target_static=False):
        """Color an existing scalar heat field; useful for matched style galleries."""
        if (luma.shape != (self.height, self.width) or
            (luma.dtype != np.uint8 and (self.transfer.levels is None or luma.dtype.kind != 'f')) or
            not np.isfinite(luma).all() or luma.min() < 0 or luma.max() > 255):
            raise ValueError('Heat field must match the renderer dimensions and contain finite 0–255 values; legacy mode requires uint8')
        # Texture is a display treatment; it must not change the HUD readouts.
        readout_luma = luma
        if self.transfer.levels is not None:
            return self.render_graded(luma, time, wave, subjects, targets, shot_id, target_static)
        if self.pixelation or self.grain or self.sensor_texture:
            from .thermal import sensor_size
            size = sensor_size(self.width, self.height, self.pixelation) if self.pixelation else (self.width, self.height)
            samples = np.asarray(Image.fromarray(luma).resize(size, Image.Resampling.BOX), dtype=np.float32)
            if self.grain:
                fixed = np.random.default_rng(self.seed & 0xffffffff).standard_normal(samples.shape, dtype=np.float32)
                rng = np.random.default_rng((self.seed + round(time * 1000)) & 0xffffffff)
                noise = fixed * .30 + rng.standard_normal(samples.shape, dtype=np.float32) * .70
                samples += noise * self.grain * 255
            if self.sensor_texture:
                samples = np.rint(samples / 2) * 2
            samples = np.clip(samples, 0, 255).astype(np.uint8)
            luma = np.asarray(Image.fromarray(samples).resize((self.width, self.height), Image.Resampling.NEAREST))
        mapped = self.palette[luma].astype(np.float32)
        image = Image.fromarray(np.uint8(np.clip(mapped, 0, 255)))
        image = highlight_glow(image, readout_luma, self.heat_glow, time, self.heat_glow_speed, self.seed,
                               dark=self.colors.palette[-1].mean() < self.colors.palette[0].mean())
        if self.hud:
            self.draw_hud(image, readout_luma, time, wave, subjects)
            colors = (self.hud_colors['target'], self.hud_colors['target-flash'])
            image = self.target_overlay.draw(image, time, targets, colors, shot=shot_id, static=target_static)
        return self.display_effects(image, time, shot_id)

    def render_graded(self, luma, time, wave, subjects, targets, shot_id, target_static):
        u = self.transfer.normalize(luma)
        if self.pixelation:
            from .thermal import sensor_size
            size = sensor_size(self.width, self.height, self.pixelation)
            u = np.asarray(Image.fromarray(u).resize(size, Image.Resampling.BOX)).copy()
        if self.grain:
            fixed = np.random.default_rng(self.seed & 0xffffffff).standard_normal(u.shape, dtype=np.float32)
            rng = np.random.default_rng((self.seed + round(time * 1000)) & 0xffffffff)
            u = np.clip(u + (fixed * .3 + rng.standard_normal(u.shape, dtype=np.float32) * .7) * self.grain, 0, 1)
        if self.pixelation:
            u = np.asarray(Image.fromarray(u).resize((self.width, self.height), Image.Resampling.NEAREST))
        graded = self.transfer.quantize(u)
        positions = [s[0] for s in self.colors.stops]
        rgb = np.stack([np.interp(graded, positions, [s[1][c] for s in self.colors.stops]) for c in range(3)], axis=-1)
        if self.palette_name in ('yautja', 'ironbow'):
            rgb *= 1 - (1 - graded[..., None]) ** 4 * .7
        image = Image.fromarray(np.uint8(np.floor(np.clip(rgb, 0, 255) + .5)))
        image = highlight_glow(image, u * 255, self.heat_glow, time, self.heat_glow_speed, self.seed,
                               dark=self.palette[-1].mean() < self.palette[0].mean())
        if self.hud:
            self.draw_hud(image, luma, time, wave, subjects)
            image = self.target_overlay.draw(image, time, targets,
                        (self.hud_colors['target'], self.hud_colors['target-flash']), shot=shot_id, static=target_static)
        return self.display_effects(image, time, shot_id)

    def draw_waveform(self, image, readout_luma, time, wave):
        s = self.scale
        if self.wave_style != 'trace':
            width = max(2, round(self.width * self.wave_width))
            height = max(2, round(self.height * self.wave_height))
            signal = np.abs(procedural_wave(time, self.seed)) if wave is None else np.maximum(np.abs(wave[0]), np.abs(wave[1]))
            mask = inkblot_mask(width, height, signal, time, style=self.wave_style, detail=self.wave_detail, seed=self.seed)
            color = self.hud_colors['waveform']
            if self.overlay_mode == 'RGBA':
                panel = Image.new('RGBA', mask.size, (*color, 0))
                panel.putalpha(mask)
            else:
                panel = ImageChops.multiply(Image.merge('RGB', (mask,) * 3), Image.new('RGB', mask.size, color))
            group = self.hud_panel(panel.size, 'waveform')
            group.replace('waveform', panel)
            self.composite_panel(image, group, max(1, round(self.width * .012)), (self.height - height) // 2)
            stats = [float(readout_luma.mean() / 255), float(readout_luma.max() / 255), float(np.abs(np.diff(readout_luma.astype(np.float32), axis=1)).mean() / 255)]
            return max(10, round(25 * s)), stats
        panel_w = min(self.width, round(110 * s))
        panel = self.hud_panel((panel_w, self.height), 'waveform-glyphs', 'waveform-axis', 'waveform-ticks', 'waveform')
        glyphs = panel.layer('waveform-glyphs')
        size = max(10, round(25 * s))
        gy = max(round(24 * s), round(self.height * .12))
        top, bottom = gy + size + round(6 * s), round(self.height * .84)
        # Glyph positions are tile origins. Put the signal through the middle
        # tile's center, rather than through its left edge.
        tile_width = round(max(8, size) * .85)
        center, amp = round(round(42 * s) + (tile_width - 1) / 2), 31 * s
        means = readout_luma.mean(axis=1) / 255
        stats = [float(readout_luma.mean() / 255), float(readout_luma.max() / 255), float(np.abs(np.diff(readout_luma.astype(np.float32), axis=1)).mean() / 255)]
        for i, metric in enumerate(stats):
            row = min(len(means) - 1, round(len(means) * (i + 1) / 4))
            anchor = center + round((i - 1) * 26 * s)
            for value, y in ((round(metric * 71), gy),
                             (round(means[row] * 97), bottom + round(12 * s))):
                tile = self.glyph(value, size)
                bounds = tile.getbbox()
                # Exclude side bearings so narrow and asymmetric symbols share
                # a fixed visible center; the audio axis never jitters with them.
                if bounds:
                    left, _, right, _ = bounds
                    tile = tile.crop((left, 0, right, tile.height))
                glyphs.paste(tile, (round(anchor - (tile.width - 1) / 2), y))
        d = ImageDraw.Draw(panel.layer('waveform-axis'))
        d.line((center, top, center, bottom), fill=self.hud_ink('waveform-axis'), width=max(1, round(s)))
        d = ImageDraw.Draw(panel.layer('waveform-ticks'))
        for i in range(17):
            y = top + (bottom - top) * i / 16
            d.line((10 * s, y, (19 if i % 4 == 0 else 14) * s, y), fill=self.hud_ink('waveform-ticks'))
        if wave is None:
            values = procedural_wave(time, self.seed)
            points = [(center + amp * v, top + (bottom - top) * i / (len(values) - 1)) for i, v in enumerate(values)]
        else:
            low, high = wave
            # Each horizontal excursion is the real minimum/maximum of its audio bin.
            points = []
            for i, (lo, hi) in enumerate(zip(low, high)):
                y = top + (bottom - top) * i / max(1, len(low) - 1)
                points.extend([(center + amp * lo, y), (center + amp * hi, y)])
        ImageDraw.Draw(panel.layer('waveform')).line(points, fill=self.hud_ink('waveform'), width=max(1, round(1.25 * s)))
        self.composite_panel(image, panel, 0, 0)
        return size, stats

    def draw_hud(self, image, readout_luma, time, wave=None, subjects=()):
        s = self.scale
        size, stats = self.draw_waveform(image, readout_luma, time, wave)
        # Top-right readout. Optional human timecode goes below the alien string.
        step, pad = round(25 * s), round(16 * s)
        rw = max(step * 8, round(180 * s))
        rh = size + (round(27 * s) if self.show_timecode else 0) + round(12 * s)
        panel = self.hud_panel((rw, rh), *(['readout', 'timecode'] if self.show_timecode else ['readout']))
        right = panel.layer('readout')
        reading = round(stats[0] * 9999)
        for i in range(8):
            value = round(stats[i % 3] * 71) if i < 4 else reading // 10 ** (7 - i) % 10
            right.paste(self.glyph(value, size, i >= 4, element='readout'), (i * step, 0))
        if self.show_timecode:
            # Align visible glyph artwork and the clock to one right edge,
            # excluding the glyph tiles' trailing side bearings.
            bounds = right.getbbox()
            if bounds:
                glyphs = right.crop(bounds)
                right = Image.new(self.overlay_mode, (rw, rh))
                right.paste(glyphs, (rw - glyphs.width, bounds[1]))
                panel.replace('readout', right)
            clock_height = max(6, round(max(9, round(19 * .8 * s)) * .69))
            clock = lcd_timecode(timecode(time + self.timecode_start), clock_height, self.hud_ink('timecode'))
            if clock.width > rw:
                clock = clock.resize((rw, max(1, round(clock.height * rw / clock.width))), Image.Resampling.LANCZOS)
            panel.layer('timecode').paste(clock, (rw - clock.width, size + round(7 * s)))
        self.composite_panel(image, panel, max(0, self.width - rw - pad), pad)
        if self.verbose:
            self.annotate(image, subjects)

    def display_effects(self, image, time, shot_id=None):
        # Tape/CRT treatments affect the final display, including the HUD.
        image = self.display.apply(image, time, shot_id)
        if self.vhs:
            image = vhs_frame(image, time, self.seed)
        if self.scanlines or self.crt_vertical_lines:
            pixels = np.asarray(image, dtype=np.float32).copy()
            if self.scanlines:
                pixels[::2] *= 1 - self.crt_strength
            if self.crt_vertical_lines:
                pixels[:, ::2] *= 1 - self.crt_strength
            image = Image.fromarray(np.uint8(pixels))
        if self.palette_name == 'virtualboy' and (not self.hud or (self.hud_theme in ('standard', 'palette')
                and not self.target_color_override and not (self.target_overlay.stroke and self.target_overlay.stroke_colors))):
            # This palette is strictly red-only, including glyphs and defects.
            pixels = np.asarray(image).copy()
            pixels[..., 0] = pixels.max(axis=2)
            pixels[..., 1:] = 0
            image = Image.fromarray(pixels)
        return image
