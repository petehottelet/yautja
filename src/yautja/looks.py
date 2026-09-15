"""Versioned visual recipes and scalar thermal grading, independent of detection."""
import math

import numpy as np

from .colors import parse_hex, HUD_DEFAULTS

SPECTRUM = [(position, parse_hex(color)) for position, color in (
    (0., '#000000'), (.06, '#081328'), (.20, '#173B82'), (.33, '#176DAD'),
    (.45, '#26A5AC'), (.56, '#62B84E'), (.64, '#D9C742'), (.72, '#F26427'),
    (.80, '#FF303A'), (.91, '#FF65AB'), (1., '#E6D8DD'))]

LOOK_PRESETS = {'yautja': {
    'thermal': 'cinematic', 'palette': 'yautja', 'thermal_levels': 12,
    'thermal_band_softness': .65, 'thermal_black_point': .2, 'thermal_white_point': .9,
    'thermal_gamma': 1.1, 'thermal_softness': .8, 'sensor_resolution': 192,
    'hud': True, 'hud_theme': 'standard', 'verbose': True,
    'neon': False, 'grain': 0., 'pixelation': 0, 'sensor_texture': False, 'scanlines': True,
    'vhs': False, 'seed': 42, 'heat_glow': 0., 'motion_blur': 0., 'crt_bleed': 0.,
    'crt_vertical_lines': False, 'crt_grid': False, 'crt_crosshatch': False,
}, 'netrunner': {
    'thermal': 'low-detail', 'scene_mode': 'source', 'scene_tint': '#548568',
    'scene_tint_strength': .8, 'scene_exposure': .65, 'hud': True,
    'hud_glyphs': 'cyber', 'hud_theme': 'custom',
    'hud_colors': ','.join(f'{key}=' + ('#FFC442' if key == 'subject-carets' else '#41E8EF' if key == 'subject-labels' else '#FD5550')
                           for key in HUD_DEFAULTS),
    'subject_outline': True, 'subject_code': True, 'subject_labels': True,
    'subject_head_gap': 30., 'subject_title_gap': 20., 'subject_caret_scale': 1.35,
    'code_size': 22., 'code_speed': 1., 'code_density': .95,
    'neon': True, 'neon_intensity': .35, 'neon_spread': .3, 'neon_core_whiten': 0.,
    'neon_elements': 'subject-code=0.2,subject-outline=0.3,subject-labels=0.25,subject-carets=0.2',
    'hud_opacity_elements': 'subject-code=0.8,waveform-axis=0.35,waveform-ticks=0.4',
    'verbose': False, 'timecode': True, 'target_flash': False, 'grain': 0., 'pixelation': 0,
    'sensor_texture': False, 'scanlines': False, 'heat_glow': 0.,
}, 'fremont': {
    'thermal': 'low-detail', 'scene_mode': 'source', 'scene_tint': '#E51A24',
    'scene_tint_strength': 1., 'scene_exposure': 1.25, 'scene_highlights': .95,
    'hud': True, 'hud_theme': 'custom',
    'hud_colors': ','.join(f'{key}={value}' for key, value in {
        **dict.fromkeys(HUD_DEFAULTS, '#F2F6FA'), 'analysis-target-fill': '#8FA1B0', 'analysis-target': '#11161E'}.items()),
    'analysis': True, 'analysis_speed': 1., 'analysis_blink_rate': 2., 'analysis_margin': .035,
    'hud_font': 'orbitron-bold', 'analysis_outline_width': 5.,
    'analysis_target': True, 'analysis_target_size': .36, 'analysis_target_response': .6,
    'hud_opacity_elements': ','.join(f'{key}=0' for key in HUD_DEFAULTS if not key.startswith('analysis-')),
    'subject_outline': False, 'subject_code': False, 'subject_labels': False,
    'neon': False, 'glow': .25, 'verbose': False, 'timecode': False,
    'grain': 0., 'pixelation': 0, 'sensor_texture': False, 'scanlines': False,
    'vhs': False, 'heat_glow': 0., 'motion_blur': 0., 'crt_bleed': 0.,
}}
FOCUS_COLORS = {**dict.fromkeys(HUD_DEFAULTS, '#8833FF'),
                'geo-grid': '#507CFF', 'waveform': '#507CFF',
                'waveform-axis': '#293F82', 'waveform-ticks': '#344FA3',
                'subject-outline': '#6099FF'}
FOCUS_SETTINGS = {
    'thermal': 'low-detail', 'scene_mode': 'source', 'scene_tint': '#8395E6',
    'scene_tint_strength': .28, 'scene_exposure': .82,
    'hud': True, 'hud_glyphs': 'cyber', 'hud_theme': 'custom',
    'hud_colors': ','.join(f'{key}={value}' for key, value in FOCUS_COLORS.items()),
    'subject_outline': True, 'outline_style': 'holographic', 'outline_coverage': .35, 'outline_width': 4.8, 'outline_shine': .65,
    'outline_arcs': 5, 'outline_speed': 1.35, 'subject_code': False, 'subject_labels': False,
    'geo_grid': True, 'geo_grid_scale': 160., 'geo_grid_jitter': .65, 'geo_grid_speed': 1.,
    'geo_grid_projection': 'sphere', 'target_mode': 'cycle', 'target_motion': 'persistent',
    'geo_grid_center_fade': .96, 'geo_grid_width': 2.2, 'geo_grid_breaks': .7,
    'geo_grid_details': True, 'geo_grid_rotation': .6, 'target_weak_spots': False,
    'target_shape': 'hexagon', 'target_flash': False, 'target_fill': 'stroked',
    'target_motif': 'none', 'target_label': None,
    'neon': True, 'neon_intensity': 1.15, 'neon_spread': 1.05, 'neon_core_whiten': 0.,
    'neon_elements': 'geo-grid=0.8,subject-outline=0.55,target=1.2',
    'hud_opacity_elements': 'waveform=0.55,waveform-axis=0.3,waveform-ticks=0.35,geo-grid=0.8',
    'verbose': False, 'timecode': False, 'grain': 0., 'pixelation': 0,
    'sensor_texture': False, 'scanlines': False, 'vhs': False, 'heat_glow': 0.,
}
LOOK_PRESETS['focus'] = FOCUS_SETTINGS
LOOK_PRESETS['relic'] = {
    **FOCUS_SETTINGS,
    'hud_colors': ','.join(f'{key}={value}' for key, value in {
        **FOCUS_COLORS, 'subject-code': '#F745FF', 'target-motif': '#F745FF'}.items()),
    'subject_code': True, 'code_style': 'light', 'code_layer': 'behind', 'code_size': 26., 'code_speed': .8, 'code_density': 1.65,
    'target_motif': 'triangles', 'target_motif_count': 7, 'target_motif_scale': 1.,
    'target_motif_speed': 1., 'target_motif_breaks': .7,
    'neon_elements': FOCUS_SETTINGS['neon_elements'] + ',subject-code=1,target-motif=1.1',
}
LOOK_PRESETS['murphy'] = {
    'thermal': 'low-detail', 'scene_mode': 'source', 'scene_tint': '#719DD2',
    'scene_tint_strength': .4, 'scene_exposure': .95, 'hud': True, 'hud_glyphs': 'tech',
    'hud_font': 'orbitron-medium', 'hud_theme': 'custom',
    'hud_colors': ','.join(f'{key}={value}' for key, value in {
        **{key: '#38D988' for key in HUD_DEFAULTS}, 'waveform-axis': '#24523E',
        'waveform-ticks': '#2E6B50', 'timecode': '#9DEFC6', 'leaders': '#5FC498',
        'markers': '#5FC498', 'target-flash': '#D9FFEC', 'geo-grid': '#2E6B50'}.items()),
    'subject_outline': False, 'subject_code': False, 'subject_labels': False, 'geo_grid': False,
    'target_mode': 'cycle', 'target_outline': True, 'target_scale': 1.25,
    'target_shape': 'frame-box', 'target_flash': False, 'target_acquire': 1., 'target_label': 'TARGETING',
    'target_label_scale': 1.8, 'target_cursor': True,
    'neon': True, 'neon_intensity': .65, 'neon_spread': 1.2, 'neon_core_whiten': 0.,
    'glow': .5, 'timecode': False, 'verbose': False,
    'grain': .05, 'scanlines': True, 'crt_strength': .5, 'crt_bleed': .08,
    'pixelation': 0, 'sensor_texture': False, 'vhs': False, 'motion_blur': 0., 'heat_glow': 0.,
    'hud_opacity_elements': 'waveform=0,waveform-axis=0,waveform-ticks=0,waveform-glyphs=0,readout=0,timecode=0',
}
COMPLETE_PRESETS = {'yautja', 'netrunner', 'fremont', 'focus', 'relic', 'murphy'}
PRESET_DESCRIPTIONS = {
    'yautja': 'Eleven colors, 12 soft thermal levels, red HUD, cyan annotations and CRT lines.',
    'netrunner': 'Green source scene, warm-red neon outlines, rising Cyber code and overhead glyph titles with yellow carets.',
    'fremont': 'Detailed red/burgundy scene, bold white analysis and blinking outlines, with a persistent translucent target gliding between subjects.',
    'focus': 'Neon-purple HUD and gliding hexagon, blue spherical grid and waveform, and thin blue holographic outlines.',
    'relic': 'Focus with hot-pink triangle ornaments and soft rising light streams centered behind each body core.',
    'murphy': 'Blue-tinted scene, glowing green box and subject outline, CRT scanlines and a medium-weight TARGETING caption with blinking cursor.',
}
PRESET_LABELS = {
    'yautja': 'Yautja', 'costa-rica': 'Costa Rica', 'ironbow': 'Ironbow', 'abyss': 'Abyss',
    'redline': 'Redline', 'virtualboy': 'Virtual Boy', 'green-phosphor': 'Green Phosphor',
    'amber-phosphor': 'Amber Phosphor', 'white-hot': 'White Hot', 'black-hot': 'Black Hot',
    'thermal-spectrum': 'Thermal Spectrum',
    'netrunner': 'Netrunner',
    'focus': 'Focus', 'relic': 'Relic', 'murphy': 'Murphy',
    'fremont': 'Fremont',
}
LOOK_PRESETS.update({name: {'thermal': 'cinematic', 'palette': name}
                     for name in PRESET_LABELS if name not in COMPLETE_PRESETS})
LEVEL_OPTIONS = ('thermal_levels', 'thermal_band_softness', 'thermal_black_point',
                 'thermal_white_point', 'thermal_gamma', 'thermal_softness')


def normalize_preset(name):
    name = name.strip().lower()
    if name == 'ghost-signal':
        name = 'netrunner'
    if name in ('hottropic', 'hot-tropic'):
        name = 'yautja'
    if name not in LOOK_PRESETS:
        raise ValueError('Unknown look preset: ' + str(name))
    return name


def merge_look(base, overrides):
    result = dict(base)
    if overrides.get('thermal') == 'classic' and 'verbose' not in overrides:
        result.pop('verbose', None)
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
