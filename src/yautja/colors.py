"""Validated, reproducible thermal and per-element HUD color choices."""
from __future__ import annotations

import colorsys
from dataclasses import dataclass
import hashlib
import re

import numpy as np

HUD_DEFAULTS = {
    'waveform': (255, 48, 43),
    'waveform-axis': (95, 17, 15),
    'waveform-ticks': (110, 22, 19),
    'waveform-glyphs': (255, 48, 43),
    'readout': (255, 48, 43),
    'timecode': (255, 118, 98),
    'callouts': (65, 232, 239),
    'leaders': (65, 232, 239),
    'markers': (65, 232, 239),
    'target': (255, 48, 43),
    'target-flash': (255, 255, 255),
}
HUD_THEMES = ('standard', 'palette', 'muted-cyan', 'custom', 'random')


def parse_hex(value):
    value = value.strip().removeprefix('#')
    if not re.fullmatch(r'(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})', value):
        raise ValueError('Colors must be RGB hex values such as #0f8 or #00ff88 (no alpha).')
    if len(value) == 3:
        value = ''.join(c * 2 for c in value)
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def hex_color(rgb):
    return '#' + ''.join(f'{int(c):02x}' for c in rgb)


def palette_hexes(value):
    # Accept commas or whitespace, but reject missing entries rather than guessing.
    if not value or any(not part.strip() for part in value.split(',')):
        raise ValueError('--palette-colors needs 2–16 hex colors, ordered cold to hot.')
    colors = [parse_hex(item) for item in re.split(r'[,\s]+', value.strip())]
    if not 2 <= len(colors) <= 16:
        raise ValueError('--palette-colors needs 2–16 hex colors, ordered cold to hot.')
    return [(i / (len(colors) - 1), color) for i, color in enumerate(colors)]


def hud_hexes(value):
    if not value or any(not part.strip() for part in re.split('[,;]', value)):
        raise ValueError('--hud-colors needs element=#RRGGBB assignments.')
    colors = {}
    for entry in re.split('[,;]', value):
        key, separator, color = entry.partition('=')
        key = key.strip()
        if not separator or key not in HUD_DEFAULTS:
            raise ValueError('Unknown HUD element; choose ' + ', '.join(HUD_DEFAULTS) + '.')
        if key in colors:
            raise ValueError('Duplicate HUD color: ' + key)
        colors[key] = parse_hex(color)
    return colors


def color_rng(seed, element):
    # Independent streams keep color choices separate from noise and glyph selection.
    digest = hashlib.sha256(f'{seed}:colors:{element}'.encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], 'little'))


def random_rgb(rng, value):
    return tuple(round(c * 255) for c in colorsys.hsv_to_rgb(float(rng.random()),
                 float(rng.uniform(.55, 1)), value))


@dataclass
class ColorScheme:
    palette_name: str
    stops: list
    palette: np.ndarray
    hud_theme: str
    hud: dict
    seed: int

    def report(self):
        return {'palette': self.palette_name, 'hud_theme': self.hud_theme,
                'color_seed': self.seed,
                'palette_stops': [{'position': float(position), 'hex': hex_color(rgb)}
                                  for position, rgb in self.stops],
                'hud_colors': {key: hex_color(rgb) for key, rgb in self.hud.items()}}


def resolve_colors(palettes, *, palette='auto', palette_colors=None, hud_theme='standard',
                   hud_colors=None, random_colors=False, seed=42):
    name = 'yautja' if palette == 'auto' else palette
    if random_colors:
        if name not in ('yautja', 'random') or hud_theme not in ('standard', 'random') or palette_colors is not None or hud_colors is not None:
            raise ValueError('--random-colors replaces both schemes; use --palette random or --hud-theme random to randomize just one.')
        name, hud_theme = 'random', 'random'
    if hud_theme not in HUD_THEMES:
        raise ValueError('Unknown HUD theme: ' + hud_theme)
    if palette_colors is not None and name != 'custom':
        raise ValueError('--palette-colors requires --palette custom.')
    if hud_colors is not None and hud_theme != 'custom':
        raise ValueError('--hud-colors requires --hud-theme custom.')
    if name == 'custom':
        stops = palette_hexes(palette_colors)
    elif name == 'random':
        rng = color_rng(seed, 'thermal')
        stops = [(i / 5, random_rgb(rng, value))
                 for i, value in enumerate((.025, .13, .34, .56, .79, 1.))]
    elif name in palettes:
        stops = palettes[name]
    else:
        raise ValueError('Unknown thermal palette: ' + name)
    pos = np.arange(256) / 255
    table = np.stack([np.interp(pos, [s[0] for s in stops], [s[1][c] for s in stops])
                      for c in range(3)], axis=1)
    if name in ('yautja', 'ironbow'):
        table *= 1 - (1 - pos[:, None]) ** 4 * .7
    table = np.uint8(np.clip(table, 0, 255))
    hud = HUD_DEFAULTS.copy()
    if hud_theme == 'muted-cyan' or (hud_theme == 'standard' and name == 'abyss'):
        hud.update({key: (38, 112, 133) for key in hud if key not in ('target', 'target-flash')})
        hud.update(timecode=(80, 157, 171), callouts=(54, 133, 149))
        hud['waveform-axis'] = (13, 55, 77)
        hud['waveform-ticks'] = (22, 73, 95)
    if hud_theme == 'palette':
        def sample(position):
            rgb = table[round(position * 255)].astype(float)
            if rgb.max() < 1:
                rgb = table[np.argmax(table.max(axis=1))].astype(float)
            return tuple(int(c) for c in np.rint(rgb * 240 / max(1, rgb.max())))

        primary, accent, light = sample(.82), sample(.48), sample(.96)
        hud.update(waveform=primary, readout=primary, timecode=light,
                   callouts=accent, leaders=accent, markers=accent)
        hud['waveform-glyphs'] = primary
        hud['waveform-axis'] = tuple(round(c * .36) for c in primary)
        hud['waveform-ticks'] = tuple(round(c * .43) for c in primary)
        hud['target'], hud['target-flash'] = primary, light
    elif hud_theme == 'custom':
        hud.update(hud_hexes(hud_colors))
    elif hud_theme == 'random':
        hud = {key: random_rgb(color_rng(seed, key), .43 if key in ('waveform-axis', 'waveform-ticks') else .95)
               for key in HUD_DEFAULTS}
    if name in ('white-hot', 'black-hot') and hud_theme in ('standard', 'palette'):
        ink = (255, 255, 255) if name == 'white-hot' else (0, 0, 0)
        hud = {key: ink for key in HUD_DEFAULTS}
    return ColorScheme(name, stops, table, hud_theme, hud, seed)
