"""Versioned visual recipes and scalar thermal grading, independent of detection."""
import math

import numpy as np

from .colors import parse_hex, HUD_DEFAULTS

SPECTRUM = [(position, parse_hex(color)) for position, color in (
    (0., '#000000'), (.06, '#081328'), (.20, '#173B82'), (.33, '#176DAD'),
    (.45, '#26A5AC'), (.56, '#62B84E'), (.64, '#D9C742'), (.72, '#F26427'),
    (.80, '#FF303A'), (.91, '#FF65AB'), (1., '#E6D8DD'))]

LOOK_PRESETS = {'hottropic': {
    'thermal': 'cinematic', 'palette': 'thermal-spectrum', 'thermal_levels': 12,
    'thermal_band_softness': .65, 'thermal_black_point': .2, 'thermal_white_point': .9,
    'thermal_gamma': 1.1, 'thermal_softness': .8, 'sensor_resolution': 192,
    'hud': False, 'neon': False, 'grain': 0., 'pixelation': 0, 'sensor_texture': False, 'scanlines': False,
    'vhs': False, 'seed': 42, 'heat_glow': 0., 'motion_blur': 0., 'crt_bleed': 0.,
    'crt_vertical_lines': False, 'crt_grid': False, 'crt_crosshatch': False,
}, 'ghost-signal': {
    'thermal': 'low-detail', 'scene_mode': 'source', 'scene_tint': '#548568',
    'scene_tint_strength': .8, 'scene_exposure': .65, 'hud': True,
    'hud_glyphs': 'cyber', 'hud_theme': 'custom',
    'hud_colors': ','.join(f'{key}=' + ('#FFC442' if key == 'subject-carets' else '#41E8EF' if key == 'subject-labels' else '#FD5550')
                           for key in HUD_DEFAULTS),
    'subject_outline': True, 'subject_code': True, 'subject_labels': True,
    'subject_head_gap': 24., 'subject_title_gap': 18., 'subject_caret_scale': 1.35,
    'code_size': 22., 'code_speed': 1., 'code_density': .65,
    'neon': True, 'neon_intensity': .35, 'neon_spread': .3, 'neon_core_whiten': 0.,
    'neon_elements': 'subject-code=0.2,subject-outline=0.3,subject-labels=0.25,subject-carets=0.2',
    'hud_opacity_elements': 'subject-code=0.8,waveform-axis=0.35,waveform-ticks=0.4',
    'verbose': False, 'timecode': True, 'target_flash': False, 'grain': 0., 'pixelation': 0,
    'sensor_texture': False, 'scanlines': False, 'heat_glow': 0.,
}}
COMPLETE_PRESETS = {'hottropic', 'ghost-signal'}
PRESET_LABELS = {
    'hottropic': 'HotTropic', 'yautja': 'Yautja', 'ironbow': 'Ironbow', 'abyss': 'Abyss',
    'redline': 'Redline', 'virtualboy': 'Virtual Boy', 'green-phosphor': 'Green Phosphor',
    'amber-phosphor': 'Amber Phosphor', 'white-hot': 'White Hot', 'black-hot': 'Black Hot',
    'thermal-spectrum': 'Thermal Spectrum',
    'ghost-signal': 'Ghost Signal',
}
LOOK_PRESETS.update({name: {'thermal': 'cinematic', 'palette': name}
                     for name in PRESET_LABELS if name not in COMPLETE_PRESETS})
LEVEL_OPTIONS = ('thermal_levels', 'thermal_band_softness', 'thermal_black_point',
                 'thermal_white_point', 'thermal_gamma', 'thermal_softness')


def normalize_preset(name):
    name = name.strip().lower()
    if name not in LOOK_PRESETS:
        raise ValueError('Unknown look preset: ' + str(name))
    return name


def merge_look(base, overrides):
    result = dict(base)
    if 'palette' in overrides and overrides['palette'] != result.get('palette'):
        result.pop('palette_colors', None)
        result.pop('random_colors', None)
    if 'hud_theme' in overrides and overrides['hud_theme'] != result.get('hud_theme'):
        result.pop('hud_colors', None)
        result.pop('random_colors', None)
    if overrides.get('wave_style') == 'trace':
        result.pop('wave_width', None)
        result.pop('wave_height', None)
    if overrides.get('thermal_levels') == 0 and 'thermal_band_softness' not in overrides:
        result.pop('thermal_band_softness', None)
    if overrides.get('sensor_texture'):
        for key in ('grain', 'pixelation', 'scanlines'):
            result.pop(key, None)
    if overrides.get('random_colors'):
        for key in ('palette', 'palette_colors', 'hud_theme', 'hud_colors'):
            result.pop(key, None)
    result.update(overrides)
    return result


def resolve_look(name, overrides):
    if name is not None:
        name = normalize_preset(name)
    return merge_look(LOOK_PRESETS.get(name, {}), overrides)


def blur_scalar(values, radius):
    """Separable Gaussian in float, retaining sub-byte heat values."""
    if radius <= .01:
        return values
    extent = max(1, math.ceil(radius * 3))
    offsets = np.arange(-extent, extent + 1, dtype=np.float32)
    weights = np.exp(-.5 * (offsets / radius) ** 2)
    weights /= weights.sum()
    result = np.asarray(values, dtype=np.float32)
    for axis in (0, 1):
        padding = [(0, 0), (0, 0)]
        padding[axis] = (extent, extent)
        padded = np.pad(result, padding, mode='edge')
        result = np.zeros_like(result)
        for i, weight in enumerate(weights):
            section = [slice(None), slice(None)]
            section[axis] = slice(i, i + result.shape[axis])
            result += padded[tuple(section)] * weight
    return result


class ThermalTransfer:
    def __init__(self, thermal_levels=None, thermal_band_softness=None, thermal_black_point=0.,
                 thermal_white_point=1., thermal_gamma=1., thermal_softness=0.):
        n = thermal_levels
        if n is not None and (isinstance(n, bool) or not isinstance(n, (int, np.integer)) or n not in (0, *range(2, 65))):
            raise ValueError('--thermal-levels must be 0 (continuous) or an integer from 2 to 64')
        for value, lo, hi, flag in ((thermal_black_point, 0, .95, 'black-point'),
                                   (thermal_white_point, .05, 1, 'white-point'),
                                   (thermal_gamma, .25, 4, 'gamma'), (thermal_softness, 0, 8, 'softness')):
            if not math.isfinite(value) or not lo <= value <= hi:
                raise ValueError(f'--thermal-{flag} must be between {lo} and {hi}')
        if thermal_white_point - thermal_black_point < .01 - 1e-12:
            raise ValueError('Thermal white point must exceed black point by at least 0.01')
        if n is None and (thermal_band_softness is not None or thermal_black_point != 0 or
                          thermal_white_point != 1 or thermal_gamma != 1 or thermal_softness != 0):
            raise ValueError('Thermal grading requires --thermal-levels or --stylepreset')
        if thermal_band_softness is not None and (not math.isfinite(thermal_band_softness) or not 0 <= thermal_band_softness <= 1):
            raise ValueError('--thermal-band-softness must be between 0 and 1')
        if n == 0 and thermal_band_softness is not None:
            raise ValueError('--thermal-band-softness requires at least 2 thermal levels')
        self.levels = n
        self.band_softness = (.35 if thermal_band_softness is None else thermal_band_softness) if n else None
        self.black, self.white, self.gamma, self.softness = thermal_black_point, thermal_white_point, thermal_gamma, thermal_softness

    def normalize(self, field):
        u = blur_scalar(np.asarray(field, np.float32) / 255, self.softness * max(field.shape) / 1920)
        return np.clip((u - self.black) / (self.white - self.black), 0, 1) ** self.gamma

    def quantize(self, u):
        if not self.levels:
            return u
        scaled = u * (self.levels - 1)
        if self.band_softness == 0:
            return np.floor(scaled + .5) / (self.levels - 1)
        lower = np.minimum(np.floor(scaled), self.levels - 2)
        t = np.clip((scaled - lower - .5) / self.band_softness + .5, 0, 1)
        return (lower + t * t * (3 - 2 * t)) / (self.levels - 1)

    def report(self):
        return {'thermal_levels': self.levels, 'thermal_band_softness': self.band_softness,
                'thermal_black_point': self.black, 'thermal_white_point': self.white,
                'thermal_gamma': self.gamma, 'thermal_softness': self.softness,
                'thermal_transfer': 'legacy' if self.levels is None else 'continuous' if self.levels == 0 else 'banded',
                'thermal_softness_units': 'pixels at 1920px longest edge'}
