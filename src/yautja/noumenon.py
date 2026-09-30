"""Deterministic, locally sampled Noumenon Classic material.

Rain equations and symbol cadence adapted from Rezmason's MIT renderer through
Noumenon; see assets/noumenon-source.json for the pin and complete notices.
This CPU port uses float64 state equations and filtered contour rasters, not
WebGL half-float state/MSDFs. It is a behavioral port, not pixel parity.
"""
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
import colorsys
import io
import json
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .signal import code_glyph

MATERIAL_OPTIONS = ('material_source', 'material_face', 'material_mix', 'material_mapping',
                    'material_structure', 'material_foreground', 'material_background', 'material_glow',
                    'material_subject_density', 'material_subject_trail', 'material_edge_glow', 'material_edge_shade')
SOURCE_REVISION = '97739c649e5e0dce60c4f1ad780359c5524f4b37'
TICK_RATE = 60
WARMUP_TICKS = 180
FIELD_SIZE = 256


class MaterialStyle:
    def __init__(self, material_source='noumenon', material_face='mixed', material_mix=.1,
                 material_mapping=1., material_structure=.65, material_foreground=2.1,
                 material_background=.385, material_glow=.18, material_subject_density=2.,
                 material_subject_trail=1.2, material_edge_glow=0., material_edge_shade=.4):
        if material_source != 'noumenon':
            raise ValueError('--material-source must be noumenon')
        if material_face not in ('mixed', 'cyber', 'classic'):
            raise ValueError('--material-face must be mixed, cyber, or classic')
        values = locals()
        for key in MATERIAL_OPTIONS:
            value = values[key]
            if key not in ('material_source', 'material_face'):
                high = 3 if key in ('material_foreground', 'material_background', 'material_subject_density') else 1
                low = 0
                if key == 'material_subject_trail':
                    low, high = 1, 2
                if isinstance(value, bool) or not math.isfinite(value) or not low <= value <= high:
                    raise ValueError(f'--{key.replace("_", "-")} must be between {low} and {high}')
            setattr(self, key, value)

    def report(self):
        return {key: getattr(self, key) for key in MATERIAL_OPTIONS}


def random_float(x, y):
    """The reference shader's hash, evaluated in float64 on this backend."""
    value = np.sin(np.mod(x * 12.9898 + y * 78.233, math.pi)) * 43758.5453
    return value - np.floor(value)


def rain_brightness(x, y, time):
    column_time = random_float(x, 0) * 1000 + time * .3 * (random_float(x + .1, 0) * .5 + .5)
    phase = (y * .01 + column_time) / .75
    phase += .3 * np.sin(math.sqrt(2) * phase) + .2 * np.sin(math.sqrt(5) * phase)
    return 1 - np.mod(phase, 1)


@lru_cache(maxsize=1)
def classic_font():
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.svgLib.path import parse_path
    try:
        data = json.loads(files('yautja').joinpath('assets/noumenon-classic.json').read_text(encoding='utf-8'))
        if data['count'] != 56 or len(data['glyphs']) != 56:
            raise ValueError('invalid classic catalog')
        glyphs = {'.notdef': TTGlyphPen(None).glyph()}
        mapping = {}
        for item in data['glyphs']:
            pen = TTGlyphPen(None)
            transformed = TransformPen(Cu2QuPen(pen, 1.), (10, 0, 0, -10, 0, 1000))
            for path in item['paths']:
                parse_path(path, transformed)
            name = item['glyph_id']
            glyphs[name] = pen.glyph()
            mapping[0xe000 + item['source_sequence_index']] = name
        # Slot four is intentionally blank in the pinned 57-slot reference.
        mapping[0xe004] = '.notdef'
        builder = FontBuilder(1000, isTTF=True)
        builder.setupGlyphOrder(list(glyphs))
        builder.setupCharacterMap(mapping)
        builder.setupGlyf(glyphs)
        for glyph in glyphs.values():
            glyph.recalcBounds(None)
        builder.setupHorizontalMetrics({name: (1000, getattr(g, 'xMin', 0)) for name, g in glyphs.items()})
        builder.setupHorizontalHeader(ascent=1000, descent=0)
        builder.setupNameTable({'familyName': 'Noumenon Classic', 'styleName': 'Regular', 'uniqueFontIdentifier': 'NoumenonClassic'})
        builder.setupOS2(sTypoAscender=1000, sTypoDescender=0, usWinAscent=1000, usWinDescent=0)
        builder.setupPost()
        buffer = io.BytesIO()
        builder.save(buffer)
        return buffer.getvalue()
    except (OSError, KeyError, ValueError) as exc:
        raise ValueError('Noumenon material assets are missing or invalid; reinstall the complete yautja package.') from exc


@lru_cache(maxsize=1)
def glyph_mips():
    """One shared 249-glyph atlas and area-filtered mip chain, bounded at ~6 MB."""
    try:
        font = ImageFont.truetype(io.BytesIO(classic_font()), 192)
        tiles = []
        for index in range(57):
            tile = Image.new('L', (192, 192))
            ImageDraw.Draw(tile).text((0, 0), chr(0xe000 + index), font=font, fill=255, anchor='la')
            tiles.append(tile.resize((64, 64), Image.Resampling.LANCZOS))
        tiles += [code_glyph(index, 64) for index in range(192)]
        return tuple(np.stack([np.asarray(tile.resize((size, size), Image.Resampling.BOX), np.float32) / 255
                               for tile in tiles]) for size in (64, 32, 16, 8, 4, 2, 1))
    except (OSError, KeyError) as exc:
        raise ValueError('Noumenon requires the packaged Classic and Cyber glyph catalogs; reinstall yautja.') from exc


@dataclass
class MaterialSample:
    coverage: np.ndarray
    body: np.ndarray
    head: np.ndarray


class NoumenonMaterial:
    """Random access Classic state at fixed ticks; O(1) seeking, no growing history.

    Classic has skipIntro=true, brightnessDecay=1, cycleFrameSkip=1 and
    cycleSpeed=.03. Rain is therefore analytic. Symbol age has a closed form;
    reconstruct the last replacement tick instead of replaying prior frames.
    All output rates sample the same settled, output-relative 60 Hz clock.
    """
    def __init__(self, seed=42, face='mixed', mix=.1, speed=1., density=1., trail_length=1.):
        if isinstance(trail_length, bool) or not math.isfinite(trail_length) or not 1 <= trail_length <= 2:
            raise ValueError('Material trail length must be between 1 and 2')
        self.seed, self.face, self.mix = seed, face, mix
        self.speed, self.density = speed, density
        self.trail_length = trail_length
        self.mips = glyph_mips()
        y, x = np.mgrid[:FIELD_SIZE, :FIELD_SIZE].astype(np.float64)
        # Fixed seeded translations; no global RNG and no per-region simulation.
        rng = np.random.default_rng(seed & 0xffffffffffffffff)
        offset = rng.uniform(0, 100, 2)
        self.x, self.y = x + .5 + offset[0], -y + .5 + offset[1]
        self.sx, self.sy = self.x / FIELD_SIZE, self.y / FIELD_SIZE
        self.initial_age = random_float(self.sx + .5, self.sy + .5)
        self.enabled = random_float(self.x, 0) < min(1., self.density)
        self.last_tick = None
        self.state = None

    def field(self, time):
        if not math.isfinite(time) or time < 0:
            raise ValueError('Material time must be finite and nonnegative')
        tick = math.floor(time * TICK_RATE + 1e-8) + WARMUP_TICKS
        if tick == self.last_tick:
            return self.state
        delta = self.speed * .03
        cycles = np.floor(self.initial_age + tick * delta + 1e-12)
        changed = cycles > 0
        last = np.ceil((cycles - self.initial_age - 1e-12) / max(delta, 1e-30))
        symbol_time = np.where(changed, last / TICK_RATE * self.speed, 0)
        sx, sy = self.sx + symbol_time, self.sy + symbol_time
        mix = self.mix if self.face == 'mixed' else float(self.face == 'cyber')
        generated = random_float(sx + 17, sy + 41) < mix
        symbol = np.floor(random_float(sx, sy) * np.where(generated, 192, 57)).astype(np.int32)
        symbol += generated * 57
        t = tick / TICK_RATE * self.speed
        rain = rain_brightness(self.x, self.y, t)
        cursor = rain > rain_brightness(self.x, self.y - 1, t)
        brightness = np.maximum(0, rain * 1.1 - .5).astype(np.float32)
        brightness *= self.enabled
        body = brightness
        if self.trail_length != 1:
            # Extend the fading tail behind the same head. Its phase, speed,
            # peak brightness and glyph grid stay unchanged; no temporal smear.
            body = np.maximum(0, .6 - (1 - rain) * 1.1 / self.trail_length).astype(np.float32)
            body *= self.enabled
        self.state = (symbol, body * ~cursor, brightness * cursor)
        self.last_tick = tick
        return self.state

    def sample(self, u, v, time, footprint=None):
        """Sample cell coordinates with trilinear mip filtering at minification."""
        result = self._sample_column(u, v, time, footprint, 0)
        # Dense rain adds overlapping columns without narrowing the glyphs.
        # Choose the strongest local stroke instead of adding their brightness.
        for offset in range(1, math.ceil(max(1., self.density))):
            other = self._sample_column(u, v, time, footprint, offset)
            use = other.coverage * (.01 + other.body + other.head) > result.coverage * (.01 + result.body + result.head)
            for key in ('coverage', 'body', 'head'):
                target = getattr(result, key)
                target[use] = getattr(other, key)[use]
        return result

    def _sample_column(self, u, v, time, footprint, offset):
        symbols, bodies, heads = self.field(time)
        ix, iy = np.floor(u).astype(np.int32) - offset, np.floor(v).astype(np.int32)
        symbol = symbols[iy % FIELD_SIZE, ix % FIELD_SIZE]
        fu, fv = (u - ix) / max(1., self.density), v - iy
        if footprint is None:
            footprint = np.ones_like(u) / 16
        lod = np.clip(np.log2(np.maximum(np.asarray(footprint) * 64, 1)), 0, 6)
        coverage = np.zeros_like(u, dtype=np.float32)
        for level, atlas in enumerate(self.mips):
            weight = np.maximum(0, 1 - np.abs(lod - level))
            active = weight > 0
            if not np.any(active):
                continue
            size = atlas.shape[1]
            # Clamp within the cell so the glyph never bleeds into another slot.
            x = np.clip(fu[active] * size - .5, 0, size - 1)
            y = np.clip(fv[active] * size - .5, 0, size - 1)
            x0, y0 = x.astype(np.int32), y.astype(np.int32)
            x1, y1 = np.minimum(x0 + 1, size - 1), np.minimum(y0 + 1, size - 1)
            dx, dy, s = x - x0, y - y0, symbol[active]
            raster = ((atlas[s, y0, x0] * (1 - dx) + atlas[s, y0, x1] * dx) * (1 - dy)
                      + (atlas[s, y1, x0] * (1 - dx) + atlas[s, y1, x1] * dx) * dy)
            coverage[active] += raster * weight[active]
        coverage *= self.enabled[iy % FIELD_SIZE, ix % FIELD_SIZE] * (fu < 1)
        return MaterialSample(coverage, bodies[iy % FIELD_SIZE, ix % FIELD_SIZE], heads[iy % FIELD_SIZE, ix % FIELD_SIZE])


def srgb_to_linear(value):
    return np.where(value <= .04045, value / 12.92, ((value + .055) / 1.055) ** 2.4)


def linear_to_srgb(value):
    value = np.clip(value, 0, 1)
    return np.where(value <= .0031308, value * 12.92, 1.055 * value ** (1 / 2.4) - .055)


@lru_cache(maxsize=1)
def body_palette():
    # Noumenon's Matrix palette retains Classic's exposure stop positions.
    return srgb_to_linear(np.array([colorsys.hls_to_rgb(137 / 360, v, .8)
                                   for v in np.linspace(0, .8, 1024)], np.float32))


def shade(sample, gain):
    """Convert reference display colors to linear light before coverage/gain."""
    body = body_palette()[np.minimum(1023, (sample.body * 1023 / .8).astype(np.int32))]
    mint = srgb_to_linear(np.array([162, 255, 216], np.float32) / 255)
    emission = body + sample.head[..., None] * 2 * mint
    return emission * (sample.coverage * gain)[..., None]
