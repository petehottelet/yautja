"""Render a compact filled/stroked catalog using the production target artwork."""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from yautja.target import TARGET_SHAPES, TargetOverlay


LABELS = {'triangle': 'Triangle', 'crosshair': 'Circular crosshair', 'hollow-cross': 'Hollow Cross',
          'square': 'Square brackets', 'square-cross': 'Square + cross', 'square-mil': 'Square + graduated cross',
          'square-x': 'Square + diagonal marks', 'hexagon': 'Hexagon', 'frame-box': 'Frame box'}


def build_sheet(destination):
    shapes = [shape for shape in TARGET_SHAPES if shape not in ('triangle-dots', 'round-dot')]
    columns, cell_w, cell_h, gap, margin, header, ss = 3, 320, 228, 12, 18, 56, 2
    rows = (len(shapes) + columns - 1) // columns
    width = margin * 2 + columns * cell_w + (columns-1) * gap
    height = header + rows * cell_h + (rows-1) * gap + margin
    canvas = Image.new('RGB', (width * ss, height * ss), '#0b1117')
    draw = ImageDraw.Draw(canvas)
    font_path = Path(__file__).resolve().parents[1] / 'src/yautja/assets/fonts/Orbitron-Medium.ttf'
    fonts = {size: ImageFont.truetype(str(font_path), size * ss) for size in (10, 12, 14, 19)}

    def text(x, y, value, size, color, anchor=None):
        draw.text((x*ss, y*ss), value, font=fonts[size], fill=color, anchor=anchor)

    text(margin, 12, 'TARGET SHAPES', 19, '#f0f3f7')
    text(width-margin, 22, 'FILLED / STROKED', 10, '#94a3b4', 'ra')
    for index, shape in enumerate(shapes):
        x = margin + index % columns * (cell_w+gap)
        y = header + index // columns * (cell_h+gap)
        draw.rectangle((x*ss,y*ss,(x+cell_w)*ss,(y+cell_h)*ss), fill='#101923', outline='#2c3947', width=ss)
        text(x+14,y+12,LABELS[shape],14,'#f0f3f7')
        text(x+14,y+35,shape,10,'#94a3b4')
        for side, fill in enumerate(('filled','stroked')):
            tile_size = (148, 142)
            background = Image.new('RGB',tile_size,'#101923')
            target = {'id':'sample','bbox':(.1,.1,.9,.9),'persistent':True,'center':(.5,.5)}
            tile = TargetOverlay(shape=shape,fill=fill,scale=2.3,flash_rate=0).draw(
                background,0,[target],((255,64,56),)*2,static=True)
            left = x+8+side*156
            canvas.paste(tile.resize((tile.width*ss,tile.height*ss),Image.Resampling.LANCZOS),
                         (left*ss,(y+57)*ss))
            text(left+74,y+205,fill.upper(),10,'#94a3b4','ma')
    destination = Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    canvas.resize((width,height),Image.Resampling.LANCZOS).save(destination)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('assets/examples/target-shapes.png'))
    args = parser.parse_args()
    print(build_sheet(args.output))


if __name__ == '__main__':
    main()
