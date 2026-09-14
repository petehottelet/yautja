"""Portable visual preset files: data only, with no media or machine settings."""
import argparse
import json
import math
import os
from pathlib import Path
import tempfile

from .looks import LOOK_PRESETS, PRESET_LABELS, LEVEL_OPTIONS, COMPLETE_PRESETS, normalize_preset
from .signal import SIGNAL_OPTIONS

VISUAL_OPTIONS = (
    'thermal', 'palette', 'palette_colors', 'hud_theme', 'hud_colors', 'hud_glyphs', 'random_colors', *SIGNAL_OPTIONS,
    'hud', 'hud_blur', 'hud_blur_elements', 'hud_opacity', 'hud_opacity_elements',
    'neon', 'neon_intensity', 'neon_spread', 'neon_flicker', 'neon_elements', 'neon_core_whiten',
    'seed', 'grain', 'glow', 'sensor_texture', 'sensor_resolution', 'pixelation',
    'scanlines', 'crt_vertical_lines', 'crt_grid', 'crt_crosshatch', 'crt_strength', 'crt_bleed', 'vhs', 'motion_blur',
    'heat_glow', 'heat_glow_speed', 'verbose', 'timecode', 'timecode_start',
    'waveform', 'wave_style', 'wave_width', 'wave_height', 'wave_detail', 'wave_window', 'wave_gain',
    'target_colors', 'target_shape', 'target_acquire', 'target_flash', 'target_flash_rate',
    'target_scale', 'target_stroke', 'target_stroke_colors', *LEVEL_OPTIONS,
)
NULLABLE = {'palette_colors', 'hud_colors', 'hud_blur_elements', 'hud_opacity_elements', 'neon_elements',
            'grain', 'pixelation', 'scanlines', 'wave_width', 'wave_height', 'target_colors',
            'target_stroke_colors', 'thermal_levels', 'thermal_band_softness'}
MAX_BYTES = 65536


def catalog():
    return {'schema_version': 1, 'presets': [
        {'id': name, 'name': label, 'kind': 'look' if name in COMPLETE_PRESETS else 'palette',
         'description': ('Eleven colors, 12 soft thermal levels, dark scenery, no HUD or sensor texture.'
                         if name == 'hottropic' else 'Green source scene, warm-red neon outlines, rising Cyber code and overhead glyph titles with yellow carets.'
                         if name == 'netrunner' else f'{label} colors with Cinematic detail; HUD and effects remain adjustable.'),
         'aliases': ['ghost-signal'] if name == 'netrunner' else [],
         'settings': dict(LOOK_PRESETS[name])} for name, label in PRESET_LABELS.items()]}


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate preset key: ' + key)
        result[key] = value
    return result


def preset_name(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 80 or any(ord(c) < 32 for c in value):
        raise ValueError('Preset name must be 1–80 characters, without control characters')
    return value.strip()


def reject_constant(value):
    raise ValueError('Non-finite preset number: ' + value)


def load_preset(path):
    path = Path(path)
    with path.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('Preset files must be at most 64 KiB')
    try:
        data = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_pairs,
                          parse_constant=reject_constant)
    except (UnicodeError, RecursionError) as exc:
        raise ValueError('Preset must be a UTF-8 JSON object') from exc
    if not isinstance(data, dict) or set(data) - {'schema_version', 'name', 'description', 'base', 'settings'}:
        raise ValueError('Preset needs schema_version, name, settings, and optional description/base')
    if type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        raise ValueError('Unsupported preset schema_version; expected 1')
    data['name'] = preset_name(data.get('name'))
    if 'description' in data and (not isinstance(data['description'], str) or len(data['description']) > 1000):
        raise ValueError('Preset description must be text of at most 1000 characters')
    if 'base' in data:
        if not isinstance(data['base'], str):
            raise ValueError('Preset base must name a built-in preset')
        data['base'] = normalize_preset(data['base'])
    settings = data.get('settings')
    if not isinstance(settings, dict):
        raise ValueError('Preset settings must be an object')
    unknown = set(settings) - set(VISUAL_OPTIONS)
    if unknown:
        raise ValueError('Unknown or nonvisual preset settings: ' + ', '.join(sorted(unknown)))
    return data


def validate_settings(settings, parser):
    """Use CLI types/choices, without coercing JSON strings into flags or numbers."""
    actions = {action.dest: action for action in parser._actions}
    result = {}
    for key, value in settings.items():
        action = actions[key]
        if value is None:
            if key not in NULLABLE:
                raise ValueError('Preset setting cannot be null: ' + key)
        elif isinstance(action, (argparse.BooleanOptionalAction, argparse._StoreTrueAction)):
            if type(value) is not bool:
                raise ValueError('Preset setting requires a JSON boolean: ' + key)
        elif action.type in (int, float):
            expected = (int,) if action.type is int else (int, float)
            try:
                valid = type(value) in expected and math.isfinite(value)
            except OverflowError:
                valid = False
            if not valid:
                raise ValueError('Preset setting requires a finite ' + action.type.__name__ + ': ' + key)
            value = action.type(value)
        else:
            if not isinstance(value, str):
                raise ValueError('Preset setting requires text: ' + key)
            if action.type:
                value = action.type(value)
        if value is not None and action.choices is not None and value not in action.choices:
            raise ValueError('Invalid preset setting ' + key + ': ' + str(value))
        result[key] = value
    return result


def save_preset(path, name, settings, *, overwrite=False):
    path = Path(path)
    if path.suffix.lower() != '.json':
        raise ValueError('--save-preset requires a .json filename')
    data = {'schema_version': 1, 'name': preset_name(name), 'settings': settings}
    payload = json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    if len(payload.encode('utf-8')) > MAX_BYTES:
        raise ValueError('Preset exceeds the 64 KiB size limit')
    path.parent.mkdir(parents=True, exist_ok=True)
    if overwrite:
        with tempfile.TemporaryDirectory(prefix='.yautja-preset-', dir=path.parent) as folder:
            temporary = Path(folder) / 'preset.json'
            temporary.write_text(payload, encoding='utf-8', newline='\n')
            os.replace(temporary, path)
    else:
        # Exclusive creation protects an existing preset, including during concurrent saves.
        with path.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(payload)
    return {'schema_version': 1, 'preset_saved': str(path.resolve()), **data}
