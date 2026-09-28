"""Block silhouettes, object boxes, and transparent technical instruments."""
import math
import re

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .colors import parse_hex
from .masks import subject_binary


OUTLINE_MODES = ('off', 'chunky', 'box')
PANEL_MODES = ('off', 'readout', 'city-map', 'elevation', 'telemetry')
READOUT_STYLES = ('ink', 'reversed', 'amber-black', 'amber-bars', 'amber-glow', 'amber-reversed')
CORNERS = ('top-left', 'top-right', 'bottom-left', 'bottom-right')
DAY_ELEMENTS = ('object-outline', *(f'corner-{corner}' for corner in CORNERS))
DAY_OPTIONS = ('object_outline', 'object_outline_width', 'object_outline_block', 'object_outline_padding', 'object_outline_fill', 'object_outline_glow',
               'hud_top_left', 'hud_top_right', 'hud_bottom_left', 'hud_bottom_right',
               'hud_panel_scale', 'hud_panel_margin', 'readout_style', 'readout_color',
               'readout_glow', 'readout_fill')


def outline_rules(text):
    """Parse source-specific styles; never evaluate file contents or expressions."""
    if text is None:
        return {}
    result = {}
    for entry in text.split(','):
        identifier, separator, mode = entry.strip().partition('=')
        identifier, mode = identifier.strip().upper(), mode.strip().lower()
        if not separator or not re.fullmatch(r'S\d{3,}-F\d{3,}', identifier) or mode not in OUTLINE_MODES:
            raise ValueError('--object-outlines needs one chunky, box or off assignment per figure, e.g. S001-F001=chunky')
        if identifier in result:
            raise ValueError('Duplicate object outline ID: ' + identifier)
        result[identifier] = mode
    if len(result) > 256:
        raise ValueError('Select at most 256 object outline overrides per render')
    return result


def block_silhouette(binary, block):
    """Quantize the silhouette on a fixed square grid, retaining thin parts."""
    w, h = binary.size
    bits = np.asarray(binary) > 0
    gh, gw = math.ceil(h / block), math.ceil(w / block)
    padded = np.pad(bits, ((0, gh * block - h), (0, gw * block - w)))
    cells = padded.reshape(gh, block, gw, block).any(axis=(1, 3))
    return Image.fromarray(np.uint8(np.repeat(np.repeat(cells, block, 0), block, 1)[:h, :w]) * 255)


def block_outline(binary, block, width):
    quantized = block_silhouette(binary, block)
    w, h = binary.size
    # Pad with zero so contours also close where a subject touches the frame.
    pad = width + 1
    padded_mask = Image.new('L', (w + pad * 2, h + pad * 2))
    padded_mask.paste(quantized, (pad, pad))
    outer = padded_mask.filter(ImageFilter.MaxFilter(width * 2 + 1))
    inner = padded_mask.filter(ImageFilter.MinFilter(width * 2 + 1))
    return ImageChops.subtract(outer, inner).crop((pad, pad, pad + w, pad + h))


def add_glow(backing, emission, color, strength, spread=1.):
    """Shared broad bloom and tight fringe for lettering and object edges."""
    if not strength:
        return backing
    for radius, gain in ((4.5,1.6),(1.2,2.0)):
        halo = Image.new('RGBA',backing.size,(*color,0))
        halo.putalpha(emission.filter(ImageFilter.GaussianBlur(radius*spread)).point(
            lambda v: min(255,round(v*strength*gain))))
        backing = Image.alpha_composite(backing,halo)
    return backing


def bright_core(color, strength):
    return tuple(round(c+(255-c)*strength*.7) for c in color)


class DayHUD:
    def __init__(self, *, object_outline='off', object_outline_width=8., object_outline_block=14.,
                 object_outline_padding=12., object_outline_fill=0., object_outline_glow=0., hud_top_left='off', hud_top_right='off',
                 hud_bottom_left='off', hud_bottom_right='off', hud_panel_scale=1., hud_panel_margin=.035,
                 readout_style='ink', readout_color='#ffbf47', readout_glow=.65, readout_fill=.24):
        values = locals().copy()
        for key, choices in (('object_outline', OUTLINE_MODES), ('readout_style', READOUT_STYLES),
                             *((f'hud_{corner.replace("-", "_")}', PANEL_MODES) for corner in CORNERS)):
            if values[key] not in choices:
                raise ValueError('--' + key.replace('_', '-') + ' must be one of ' + ', '.join(choices))
        for key, low, high in (('object_outline_width', 1, 32), ('object_outline_block', 2, 64),
                               ('object_outline_padding', 0, 80), ('object_outline_fill', 0, 1), ('object_outline_glow', 0, 1), ('hud_panel_scale', .5, 2),
                               ('hud_panel_margin', .01, .15), ('readout_glow', 0, 1), ('readout_fill', 0, .6)):
            if not math.isfinite(values[key]) or not low <= values[key] <= high:
                raise ValueError(f'--{key.replace("_", "-")} must be between {low} and {high}')
        self.amber = parse_hex(readout_color)
        for key in DAY_OPTIONS:
            setattr(self, key, values[key])
        self.styles = {}
        self.panel_bounds = {}

    @property
    def active(self):
        return self.object_outline != 'off' or any(self.panels.values())

    @property
    def panels(self):
        return {corner: getattr(self, 'hud_' + corner.replace('-', '_')) != 'off' for corner in CORNERS}

    def report(self, hud=True):
        return {**{key: getattr(self, key) for key in DAY_OPTIONS},
                'object_outlines_active': bool(hud and (self.object_outline != 'off' or self.styles)),
                'corner_hud_active': bool(hud and any(self.panels.values())),
                'corner_data': 'simulated; not source geolocation or measured terrain'}

    def draw_objects(self, renderer, image, subjects):
        if self.object_outline == 'off' and not self.styles:
            return
        scale = min(image.size) / 1080
        width = max(1, round(self.object_outline_width * scale))
        block = max(2, round(self.object_outline_block * scale))
        padding = round(self.object_outline_padding * scale)
        ink = Image.new('L', image.size)
        edges = Image.new('L',image.size)
        for subject in subjects:
            mode = self.styles.get(subject.track_id, self.object_outline)
            if mode == 'off' or subject.opacity <= 0:
                continue
            binary = subject_binary(subject, image.size)
            box = binary.getbbox()
            if box is None:
                continue
            outline = block_outline(binary, block, width) if mode == 'chunky' else Image.new('L', image.size)
            fill = block_silhouette(binary, block) if mode == 'chunky' and self.object_outline_fill else None
            if mode == 'box':
                x0, y0, x1, y1 = box
                bounds = (max(0, x0-padding), max(0, y0-padding),
                          min(image.width-1, x1-1+padding), min(image.height-1, y1-1+padding))
                ImageDraw.Draw(outline).rectangle(bounds, outline=255, width=width)
                if self.object_outline_fill:
                    fill = Image.new('L', image.size)
                    ImageDraw.Draw(fill).rectangle(bounds, fill=255)
            edge = outline
            if fill is not None:
                outline = ImageChops.lighter(outline, fill.point(lambda v: round(v*self.object_outline_fill)))
            if subject.opacity < 1:
                outline = outline.point(lambda v: round(v * max(0., subject.opacity)))
                edge = edge.point(lambda v: round(v * max(0., subject.opacity)))
            ink = ImageChops.lighter(ink, outline)
            edges = ImageChops.lighter(edges,edge)
        panel = renderer.hud_panel(image.size, 'object-outline')
        color = renderer.hud_colors['object-outline']
        artwork = Image.new('RGBA', image.size, (*color, 0))
        artwork.putalpha(ink)
        if self.object_outline_glow:
            bloom = add_glow(Image.new('RGBA',image.size),edges,color,self.object_outline_glow,max(.5,width*.4))
            artwork = Image.alpha_composite(bloom,artwork)
            core = Image.new('RGBA',image.size,(*bright_core(color,self.object_outline_glow),0))
            core.putalpha(edges)
            artwork = Image.alpha_composite(artwork,core)
        panel.replace('object-outline', artwork)
        renderer.neon_widths['object-outline'] = width
        renderer.composite_panel(image, panel, 0, 0)

    def panel_layout(self, size):
        w, h = size
        margin = max(1, round(min(size) * self.hud_panel_margin))
        scale = min(w / 1280, h / 720) * self.hud_panel_scale
        scale = min(scale, max(1, (w - 3 * margin) // 2) / 280,
                    max(1, (h - 3 * margin) // 2) / 168)
        pw, ph = max(1, round(280 * scale)), max(1, round(168 * scale))
        return {corner: (margin if corner.endswith('left') else w-margin-pw,
                         margin if corner.startswith('top') else h-margin-ph, pw, ph) for corner in CORNERS}

    def draw_panels(self, renderer, image, time, subjects, shot):
        self.panel_bounds = {}
        for corner, (x, y, width, height) in self.panel_layout(image.size).items():
            mode = getattr(self, 'hud_' + corner.replace('-', '_'))
            if mode == 'off':
                continue
            element = 'corner-' + corner
            layer = self.instrument(renderer.typography, mode, time, subjects, shot, renderer.seed,
                                    renderer.hud_colors[element])
            layer = layer.resize((width, height), Image.Resampling.LANCZOS)
            panel = renderer.hud_panel(layer.size, element)
            panel.replace(element, layer)
            renderer.neon_widths[element] = max(1., width / 280)
            renderer.composite_panel(image, panel, x, y)
            self.panel_bounds[corner] = (x, y, x + width, y + height)

    def instrument(self, typography, mode, time, subjects, shot, seed, color=(0, 0, 0)):
        """Draw at a fixed design size; alpha is the only panel background."""
        layer = Image.new('RGBA', (280, 168))
        draw = ImageDraw.Draw(layer)
        ink = (*color, 255)
        count = sum(subject.opacity > .05 for subject in subjects)
        lettering = Image.new('L', layer.size)
        backing = Image.new('RGBA', layer.size)
        readout_regions = []
        reversed_text = self.readout_style in ('reversed', 'amber-reversed')

        def text(value, x, y, height=10, fill=ink):
            mask = typography.mask(value, height)
            if mask.width > 260 - x:
                mask = mask.resize((max(1, 260-x), height), Image.Resampling.NEAREST)
            lettering.paste(mask, (x,y))
            if mode == 'readout':
                # Keep each line and its square marker on one fitted backing.
                glyph_bounds = mask.getbbox()
                readout_regions.append((16,y,x+(glyph_bounds[2] if glyph_bounds else 0),y+mask.height))
            bar_height = max(mask.height+2, round(mask.height*1.15))
            pad_top = (bar_height-mask.height)//2
            if mode == 'readout' and self.readout_style == 'amber-bars':
                ImageDraw.Draw(backing).rectangle((x-4,y-pad_top,x+mask.width+3,y-pad_top+bar_height-1),
                                                 fill=(0,0,0,255))
            if mode == 'readout' and reversed_text:
                # Opaque highlight, literal alpha holes for the lettering.
                alpha = Image.new('L', (mask.width+8, bar_height), 255)
                alpha.paste(ImageChops.invert(mask), (4,pad_top))
                glyphs = Image.new('RGBA', alpha.size, fill)
                glyphs.putalpha(alpha)
                layer.alpha_composite(glyphs, (x-4,y-pad_top))
            else:
                glyphs = Image.new('RGBA', mask.size, fill)
                glyphs.putalpha(mask)
                layer.alpha_composite(glyphs, (x, y))

        if mode == 'readout':
            amber = self.readout_style in ('amber-black', 'amber-bars', 'amber-glow', 'amber-reversed')
            if amber:
                ink = (*self.amber, 255)
            text('BRAND NEW DAY', 16, 13, 14, ink)
            draw.rectangle((16, 36, 259, 39), fill=ink)
            readout_regions.append((16,36,260,40))
            scene = str(shot if shot is not None else '001').upper().removeprefix('S')
            for row, value in enumerate((f'SCENE {scene:0>3} / TRACK {count:02d}',
                                         f'T+ {max(0., time):09.2f}', 'OPTICAL / LOCAL', 'STATUS  ACQUIRING' if not count else 'STATUS  TRACKING')):
                y = 51 + row * 22
                draw.rectangle((16, y, 23, y + 10), fill=ink)
                text(value, 33, y, 11, ink)
            draw.rectangle((16, 145, 72, 153), fill=ink)
            for left in range(80, 260, 12):
                draw.rectangle((left, 145, left + (6 if left % 24 else 9), 153), fill=ink)
            readout_regions.append((16,145,255,154))
            if amber:
                foreground = layer
                layer = backing
                draw = ImageDraw.Draw(layer)
                if self.readout_style == 'amber-black':
                    # Follow the rows' widths, including the divider and footer,
                    # so the source shows through to the right of shorter rows.
                    previous = None
                    for left,top,right,bottom in readout_regions:
                        bounds = (max(0,left-10),max(0,top-8),
                                  min(layer.width-1,right+9),min(layer.height-1,bottom+7))
                        if previous and bounds[1] > previous[3]+1:
                            # Join separated rows at their shared width to keep
                            # a continuous left edge without filling the recesses.
                            draw.rectangle((max(previous[0],bounds[0]),previous[3]+1,
                                            min(previous[2],bounds[2]),bounds[1]-1),fill=(0,0,0,255))
                        draw.rectangle(bounds,fill=(0,0,0,255))
                        previous = bounds
                elif self.readout_style == 'amber-glow':
                    draw.rectangle((6, 4, 273, 163), fill=(*self.amber, round(255 * self.readout_fill)))
                    ImageDraw.Draw(foreground).rectangle((6, 4, 273, 163), outline=(*self.amber, 235), width=2)
                # A broad amber bloom plus a tight bright fringe remains visible
                # after the corner instrument is reduced to delivery resolution.
                emission = foreground.getchannel('A')
                layer = add_glow(layer,emission,self.amber,self.readout_glow)
                layer = Image.alpha_composite(layer, foreground)
                if reversed_text:
                    # Bloom must never paint over the source inside cutout text.
                    layer.putalpha(ImageChops.multiply(layer.getchannel('A'), ImageChops.invert(lettering)))
                else:
                    core_color = bright_core(self.amber,self.readout_glow)
                    core = Image.new('RGBA', layer.size, (*core_color,0))
                    core.putalpha(lettering)
                    layer = Image.alpha_composite(layer,core)
            return layer

        if mode == 'city-map':
            text('SECTOR GRID / SIM', 12, 8)
            rng = np.random.default_rng(seed & 0xffffffff)
            # Original schematic street grid, stable throughout the clip.
            for row in range(4):
                for col in range(7):
                    if rng.random() < .18:
                        continue
                    x, y = 14 + col * 36, 29 + row * 22
                    draw.rectangle((x, y, x + 26, y + 13), outline=ink, width=1)
                    if rng.random() > .4:
                        draw.line((x + 3, y + 4, x + 22, y + 4), fill=ink)
            draw.line((8, 119, 84, 91, 134, 91, 205, 28, 264, 28), fill=ink, width=3)
            cx, cy = 142, 82
            draw.polygon(((cx, cy-7), (cx-5, cy+5), (cx, cy+2), (cx+5, cy+5)), fill=ink)
            text('N', 260, 47, 9)
            draw.line((264, 61, 264, 80), fill=ink)
            text(f'X+{1200 + int(time*3):05d} Y+{6400 + int(time):05d}', 12, 133, 10)
            text('SIMULATED COORDINATES', 12, 151, 8)
        elif mode == 'elevation':
            text('TERRAIN / SIM PROFILE', 12, 8)
            xs = np.linspace(14, 260, 90)
            for row in range(8):
                ys = 115-row*9 - (17+row*1.5)*np.exp(-((xs-160)/64)**2) + 6*np.sin(xs/28+row*.18)
                draw.line(list(zip(xs, ys)), fill=ink, width=1)
            draw.line((14, 34, 14, 128, 265, 128), fill=ink)
            for x in range(14, 265, 25):
                draw.line((x, 128, x, 132), fill=ink)
            text('0      250      500 M', 14, 144, 10)
        elif mode == 'telemetry':
            text('OPTICAL TELEMETRY', 12, 8)
            text(f'TRACKS {count:02d}   T+{max(0.,time):07.1f}', 12, 30, 10)
            xs = np.linspace(14, 260, 130)
            ys = 75 + np.sin(xs*.09+time)*8 + np.sin(xs*.23-time*2)*3
            draw.line(list(zip(xs, ys)), fill=ink, width=2)
            for x in range(14, 261, 14):
                level = 10 + int((math.sin(x*.2+time)+1)*13)
                draw.rectangle((x, 130-level, x+6, 130), fill=ink)
            text('SIGNAL / SIMULATION', 12, 145, 9)
        return layer
