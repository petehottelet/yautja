"""Original five-by-seven display alphabet, with solid or CRT raster cells."""
from functools import lru_cache
import io

from PIL import Image, ImageDraw


# Each hexadecimal value describes one row of five pixels, left to right.
ROWS = {
    'A': (14,17,17,31,17,17,17), 'B': (30,17,17,30,17,17,30),
    'C': (14,17,16,16,16,17,14), 'D': (30,17,17,17,17,17,30),
    'E': (31,16,16,30,16,16,31), 'F': (31,16,16,30,16,16,16),
    'G': (14,17,16,23,17,17,15), 'H': (17,17,17,31,17,17,17),
    'I': (31,4,4,4,4,4,31), 'J': (7,2,2,2,18,18,12),
    'K': (17,18,20,24,20,18,17), 'L': (16,16,16,16,16,16,31),
    'M': (17,27,21,21,17,17,17), 'N': (17,25,21,19,17,17,17),
    'O': (14,17,17,17,17,17,14), 'P': (30,17,17,30,16,16,16),
    'Q': (14,17,17,17,21,18,13), 'R': (30,17,17,30,20,18,17),
    'S': (15,16,16,14,1,1,30), 'T': (31,4,4,4,4,4,4),
    'U': (17,17,17,17,17,17,14), 'V': (17,17,17,17,17,10,4),
    'W': (17,17,17,21,21,21,10), 'X': (17,17,10,4,10,17,17),
    'Y': (17,17,10,4,4,4,4), 'Z': (31,1,2,4,8,16,31),
    '0': (14,17,19,21,25,17,14), '1': (4,12,4,4,4,4,14),
    '2': (14,17,1,2,4,8,31), '3': (30,1,1,14,1,1,30),
    '4': (2,6,10,18,31,2,2), '5': (31,16,16,30,1,1,30),
    '6': (14,16,16,30,17,17,14), '7': (31,1,2,4,8,8,8),
    '8': (14,17,17,14,17,17,14), '9': (14,17,17,15,1,1,14),
    ' ': (0,)*7, '.': (0,0,0,0,0,12,12), ':': (0,12,12,0,12,12,0),
    '-': (0,0,0,31,0,0,0), '+': (0,4,4,31,4,4,0),
    '/': (1,1,2,4,8,16,16), '%': (25,25,2,4,8,19,19),
    '[': (14,8,8,8,8,8,14), ']': (14,2,2,2,2,2,14),
    '(': (2,4,8,8,8,4,2), ')': (8,4,2,2,2,4,8),
    '=': (0,0,31,0,31,0,0), '_': (0,0,0,0,0,0,31),
    ',': (0,0,0,0,0,4,8), '!': (4,4,4,4,4,0,4),
    '?': (14,17,1,2,4,0,4), '#': (10,31,10,10,31,10,0),
    '<': (2,4,8,16,8,4,2), '>': (8,4,2,1,2,4,8),
    '*': (0,21,14,31,14,21,0), '|': (4,)*7,
}


@lru_cache(maxsize=512)
def pixel_mask(text, height, tracking=0., crt=False):
    """Monospaced uppercase instrument text; CRT adds fine raster gaps."""
    height = max(1, round(height))
    step = 6 + max(0, round(tracking * 7))
    mask = Image.new('L', (max(1, len(text) * step - 1) * 3, 21))
    draw = ImageDraw.Draw(mask)
    for i, char in enumerate(text.upper()):
        for y, row in enumerate(ROWS.get(char, ROWS['?'])):
            for x in range(5):
                if row & (1 << (4 - x)):
                    left, top = (i * step + x) * 3, y * 3
                    draw.rectangle((left, top, left + 2, top + 2), fill=255)
    mask = mask.resize((max(1, round(mask.width * height / 21)), height), Image.Resampling.NEAREST)
    if crt:
        # Subtle scan rows retain strokes even at small delivery sizes.
        draw = ImageDraw.Draw(mask)
        for y in range(2, height, 3):
            row = mask.crop((0, y, mask.width, y + 1)).point(lambda v: round(v * .55))
            mask.paste(row, (0, y))
    return mask


@lru_cache(maxsize=2)
def font_data(crt=False):
    """Compile the same cells for Pillow consumers that require a font object."""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    glyphs = {'.notdef': TTGlyphPen(None).glyph()}
    cmap = {}
    for code in range(32, 127):
        char = chr(code)
        name = f'uni{code:04X}'
        pen = TTGlyphPen(None)
        for y, row in enumerate(ROWS.get(char.upper(), ROWS['?'])):
            for x in range(5):
                if row & (1 << (4-x)):
                    left, bottom = x*100, (6-y)*100
                    top = bottom + (72 if crt else 100)
                    pen.moveTo((left, bottom))
                    pen.lineTo((left, top))
                    pen.lineTo((left+100, top))
                    pen.lineTo((left+100, bottom))
                    pen.closePath()
        glyphs[name] = pen.glyph()
        cmap[code] = name
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(list(glyphs))
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics({name:(600,0) for name in glyphs})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    family = 'Yautja CRT' if crt else 'Yautja Pixel'
    builder.setupNameTable({'familyName':family, 'styleName':'Regular', 'uniqueFontIdentifier':family+'V1'})
    builder.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    builder.setupPost()
    buffer = io.BytesIO()
    builder.save(buffer)
    return buffer.getvalue()
