"""Render a compact filled/stroked catalog using the production target artwork."""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from yautja.target import TARGET_SHAPES, TargetOverlay
from yautja.render import Renderer


LABELS = {'triangle': 'Triangle', 'triangle-dots': 'Triangle + three lock dots',
          'round-dot': 'Circle + three lock dots', 'crosshair': 'Circular crosshair', 'hollow-cross': 'Hollow Cross',
          'square': 'Square brackets', 'square-cross': 'Square + cross', 'square-mil': 'Square + graduated cross',
          'square-x': 'Square + diagonal marks', 'hexagon': 'Hexagon', 'frame-box': 'Frame box',
          'fremont-analysis': 'Fremont scan disk'}


def fremont_tile(size, filled):
    # Red is catalog artwork only; the preset keeps its native translucent ink.
    background = Image.new('RGB', size, '#101923')
    options = {'target_fill': 'filled' if filled else 'stroked'}
    options['hud_colors'] = ('analysis-target-fill=#FF4038' if filled
                             else 'analysis-target=#FF4038')
    renderer = Renderer(*size, look_preset='fremont', analysis_target_size=.72, glow=0, **options)
    target = renderer.analysis.target
    target.advance((.5, .5), 0, 0, size, static=True)
    target.draw(renderer, background)
    return background


def build_sheet(destination):
    first = ('triangle', 'triangle-dots', 'round-dot')
    shapes = [*first, *(shape for shape in TARGET_SHAPES if shape not in first), 'fremont-analysis']
    columns, cell_w, cell_h, gap, margin, header, ss = 3, 320, 228, 12, 18, 56, 2
    rows = (len(shapes) + columns - 1) // columns
    width = margin * 2 + columns * cell_w + (columns-1) * gap
    footer = header + rows * cell_h + (rows-1) * gap
    height = footer + 62
    canvas = Image.new('RGB', (width * ss, height * ss), '#0b1117')
    draw = ImageDraw.Draw(canvas)
    font_path = Path(__file__).resolve().parents[1] / 'src/yautja/assets/fonts/Orbitron-Medium.ttf'
    fonts = {size: ImageFont.truetype(str(font_path), size * ss) for size in (10, 12, 14, 19)}

    def text(x, y, value, size, color, anchor=None):
        draw.text((x*ss, y*ss), value, font=fonts[size], fill=color, anchor=anchor)

    text(margin, 12, 'TARGET SHAPES', 19, '#f0f3f7')
    text(width-margin, 22, f'{len(TARGET_SHAPES)} GEOMETRIC + FREMONT', 10, '#94a3b4', 'ra')
    for index, shape in enumerate(shapes):
        x = margin + index % columns * (cell_w+gap)
        y = header + index // columns * (cell_h+gap)
        draw.rectangle((x*ss,y*ss,(x+cell_w)*ss,(y+cell_h)*ss), fill='#101923', outline='#2c3947', width=ss)
        text(x+14,y+12,LABELS[shape],14,'#f0f3f7')
        text(x+14,y+35,'--analysis-target' if shape == 'fremont-analysis' else shape,10,'#94a3b4')
        for side, fill in enumerate(('filled','stroked')):
            tile_size = (148, 142)
            if shape == 'fremont-analysis':
                tile = fremont_tile(tile_size, fill == 'filled')
            else:
                background = Image.new('RGB',tile_size,'#101923')
                target = {'id':'sample','bbox':(.1,.1,.9,.9),'persistent':True,'center':(.5,.5)}
                tile = TargetOverlay(shape=shape,fill=fill,scale=2.3,flash_rate=0).draw(
                    background,0,[target],((255,64,56),)*2,static=True)
            left = x+8+side*156
            canvas.paste(tile.resize((tile.width*ss,tile.height*ss),Image.Resampling.LANCZOS),
                         (left*ss,(y+57)*ss))
            label = fill.upper()
            text(left+74,y+205,label,10,'#94a3b4','ma')
    text(margin,footer+14,'All reticles: --target-fill filled / stroked. Lock-dot shapes shown after acquisition.',10,'#94a3b4')
    text(margin,footer+34,'Fremont is shown in red for this sheet; its preset keeps its original colors.',10,'#94a3b4')
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
