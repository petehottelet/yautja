"""Portable, cached readable HUD faces; custom font paths are runtime only."""
from functools import lru_cache
from importlib.resources import files
import io
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_FILES = {'michroma': 'Michroma-Regular.ttf', 'orbitron': 'Orbitron-Light.ttf',
              'orbitron-medium': 'Orbitron-Medium.ttf', 'orbitron-bold': 'Orbitron-Bold.ttf'}
TECH_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


@lru_cache(maxsize=128)
def bundled_font(name, size):
    return ImageFont.truetype(io.BytesIO(files('yautja').joinpath('assets/fonts/' + FONT_FILES[name]).read_bytes()), size)


class HUDTypography:
    def __init__(self, hud_font='michroma', hud_font_file=None):
        if hud_font not in FONT_FILES:
            raise ValueError('Unknown --hud-font: ' + str(hud_font))
        self.hud_font = hud_font
        self.path = Path(hud_font_file).expanduser().resolve() if hud_font_file else None
        self.data = None
        self.fonts, self.tiles = {}, {}
        if self.path:
            try:
                if self.path.suffix.lower() not in ('.ttf', '.otf'):
                    raise ValueError('expected a .ttf or .otf file')
                self.data = self.path.read_bytes()
                from fontTools.ttLib import TTFont
                with TTFont(io.BytesIO(self.data)) as font:
                    cmap = font.getBestCmap() or {}
                    missing = [chr(i) for i in range(32, 127) if i not in cmap]
                    if missing:
                        raise ValueError('font must cover printable ASCII; missing ' + repr(''.join(missing)))
                self.font(24)
            except Exception as exc:
                raise ValueError(f'Cannot load --hud-font-file {self.path}: {exc}') from exc

    def font(self, size):
        size = max(1, int(size))
        if self.data is None:
            return bundled_font(self.hud_font, size)
        if size not in self.fonts:
            if len(self.fonts) >= 128:
                self.fonts.clear()
            self.fonts[size] = ImageFont.truetype(io.BytesIO(self.data), size)
        return self.fonts[size]

    def mask(self, text, height, tracking=0.):
        height = max(1, round(height))
        key = (text, height, tracking)
        if key in self.tiles:
            return self.tiles[key]
        ss = 3
        font = self.font(height * ss * 2)
        bounds = font.getbbox(text)
        spacing = tracking * font.size
        advance = sum(font.getlength(char) for char in text) if tracking else font.getlength(text)
        width = max(1, math.ceil(max(advance, bounds[2] - min(0, bounds[0])) + spacing * max(0, len(text) - 1)) + 4)
        ink = Image.new('L', (width, max(1, bounds[3] - bounds[1]) + 4))
        draw = ImageDraw.Draw(ink)
        x = 2 - min(0, bounds[0])
        if tracking:
            for char in text:
                draw.text((x, 2 - bounds[1]), char, font=font, fill=255)
                x += font.getlength(char) + spacing
        else:
            draw.text((x, 2 - bounds[1]), text, font=font, fill=255)
        box = ink.getbbox()
        if box:
            ink = ink.crop(box)
        ink = ink.resize((max(1, round(ink.width * height / ink.height)), height), Image.Resampling.LANCZOS)
        if len(self.tiles) >= 512:
            self.tiles.clear()
        self.tiles[key] = ink
        return ink

    def glyph(self, index, height, alphabet=TECH_ALPHABET):
        ink = self.mask(alphabet[index % len(alphabet)], height)
        width = max(1, round(height * .85))
        if ink.width > width:
            ink = ink.resize((width, height), Image.Resampling.LANCZOS)
        tile = Image.new('L', (width, height))
        tile.paste(ink, ((width - ink.width) // 2, 0))
        return tile

    def report(self):
        return {'hud_font': self.hud_font, 'hud_font_file': str(self.path) if self.path else None,
                'hud_font_family': self.font(24).getname()[0], 'hud_font_weight': self.font(24).getname()[1]}
