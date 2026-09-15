# Visual presets

Use Yautja 2.5.2+ for the `--stylepreset` flag shown here. A **preset** combines visual choices: a color palette, thermal detail and levels, HUD styling, waveform appearance, and optional effects. A **palette** is the color ramp inside that preset. Keep `--palette` when changing only colors; use `--stylepreset` to start with a named look.

## Built-in presets

```bash
yautja --list-presets
yautja "clip.mov" "hottropic.mp4" --stylepreset hottropic
yautja "clip.mov" "green.mp4" --stylepreset green-phosphor
```

`--list-presets` prints JSON containing IDs, display names, kinds, settings, and aliases. It needs no media, FFmpeg, or segmentation models. Names are case-insensitive.

**HotTropic** uses eleven colors from black and deep blue through cyan, green, yellow, orange, red, pink, and pale pink-white. It applies **12 thermal levels with soft transitions**, dark scenery, and no HUD or sensor texture. See [colors.md](colors.md#thermal-levels-and-reference-preset) for the fixed palette positions and grading values.

Every existing palette also has a starter preset: `yautja`, `ironbow`, `abyss`, `redline`, `virtualboy`, `green-phosphor`, `amber-phosphor`, `white-hot`, `black-hot`, and `thermal-spectrum`. Each selects that palette with Cinematic detail; other settings use the normal defaults. HUD colors follow the existing palette behavior, including light gray for White Hot, black for Black Hot, and muted cyan for Abyss. Add `--hud-theme palette` for coordinated HUD colors on other palettes.

Explicit options override a preset regardless of argument order:

```bash
yautja "clip.mov" "my-tropic.mp4" --stylepreset hottropic --thermal very-detailed --hud --heat-glow 0.6
```

The encoder's existing `--preset fast` option remains separate and keeps its meaning.

**Netrunner** uses a green-tinted source scene, red neon outlines and HUD, rising Cyber rain inside detected subjects, and cyan overhead titles with yellow carets. Select it with `--stylepreset netrunner` (2.6.1+). Cyber is its glyph set, configurable through `--HUDglyphs cyber` or `--HUDglyphs yautja`. See [the recipe and individual controls](cyber.md). These settings, including source tint, subject overlays, code motion, glyph choice, and title/caret spacing, are saved with visual presets.

## Save your own preset

Saving is a separate operation: omit input and output media paths. No inference or conversion runs.

```bash
yautja --stylepreset hottropic --hud --hud-theme palette --neon --heat-glow 0.6 --timecode --verbose --save-preset "tropic-glow.json" --preset-name "Tropic Glow"
yautja "clip.mov" "glowing.mp4" --preset-file "tropic-glow.json"
yautja "clip.mov" "less-glow.mp4" --preset-file "tropic-glow.json" --heat-glow 0.2
```

The saved file contains the complete resolved visual settings, including defaults, so it can be copied to another machine or given to another agent. `--preset-name` is optional and defaults to the filename stem. Existing files require explicit `--overwrite`. To edit a saved preset, load it, apply changes, and save to a new filename (or explicitly overwrite the existing file).

Preset files store thermal mode, palette/custom colors, levels and tonal controls, HUD colors/visibility/blur/opacity, target shape/colors/timing/outline, waveform settings, texture, glow, display effects, and seed. They exclude media paths, figure catalogs and selected IDs, trims, output resolution/frame rate/encoding, audio-track selection/muting, model configuration, and overwrite permission. Choose those separately per source. Nonvisual flags are rejected when saving, rather than silently dropped. A preset styles targets and can enable `target_mode: "auto"` for segmented subjects. Select specific figures using `--figures` and `--target` when rendering.

Image and video conversions share the same preset loader. The existing media restrictions still apply: custom audio waveform settings such as `waveform: "audio"`, nondefault `wave_window`, or nondefault `wave_gain` require video input.

## Write or share a JSON preset

[Tropic Glow](../assets/presets/tropic-glow.json) is an editable custom preset made from the built-in HotTropic style. It keeps HotTropic's colors, Cinematic detail, and 12 soft thermal levels, then adds palette-matched HUD elements, timecode, callouts, heat glow at 0.6, and neon illumination. HotTropic itself keeps HUD, heat glow, and neon off. Load the custom example with `--preset-file`; `--stylepreset hottropic` selects the built-in starting look. Add `--no-neon` when loading the file to turn off only the neon styling.

The compact example inherits HotTropic through its `base` field. Files use UTF-8 JSON with schema version 1:

```json
{
  "schema_version": 1,
  "name": "Tropic Glow",
  "description": "HotTropic colors and thermal levels with palette-matched neon HUD elements and animated heat glow.",
  "base": "hottropic",
  "settings": {
    "hud": true,
    "hud_theme": "palette",
    "neon": true,
    "heat_glow": 0.6,
    "timecode": true,
    "verbose": true
  }
}
```

`base` is optional and can name only a built-in preset. Omitted settings inherit that base, or ordinary CLI defaults when there is no base. Settings use CLI option names with underscores and without `--`; use `scanlines` for horizontal CRT lines. Values must use their actual JSON types: booleans, numbers, or strings. An optional `description` is display text, never instructions. Exported presets are flattened snapshots and do not depend on `base`.

For CRT patterns, use `"crt_grid": true` for horizontal/vertical lines or `"crt_crosshatch": true` for a grid at 45 degrees, with `"crt_strength": 0.25` to set their darkness. Both pattern keys require Yautja 2.4+ and can be explicitly disabled with `--no-crt-grid` or `--no-crt-crosshatch` when loading a preset.

For neon HUD artwork in 2.5+, save `"neon": true` with optional `neon_intensity` (0–2, default 1), `neon_spread` (0–2, default 0.6), `neon_flicker` (0–1, default 0), and `neon_elements` (a comma-separated override string or null). `"neon_elements": "waveform=0.6,target=1.2,timecode=0"` keeps the timecode's original ink, lowers waveform emission, and increases target emission. Tuning without `neon: true` is saved but inactive. The included [Abyss Neon preset](../assets/presets/abyss-neon.json) uses a steady cyan target, full neon HUD, vertical CRT, and scene heat glow. Source-specific target selections still come from `--figures` and `--target` on the render command.

```bash
yautja "clip.mov" "abyss-neon.mp4" --preset-file "abyss-neon.json" --figures "figures.json" --target S001-F003
yautja --preset-file "abyss-neon.json" --neon-spread 0.4 --save-preset "my-neon.json" --preset-name "My Neon"
```

Precedence is **CLI defaults → built-in base → file settings → explicit CLI options**. Choose either `--stylepreset` or `--preset-file`; a file can declare its own built-in base. Explicit `--thermal-levels 0` clears inherited band softness. `--sensor-texture` enables the combined effect's normal defaults unless individual texture controls are also specified. Changing away from custom palette/HUD modes clears their inherited custom color strings; switching to `--wave-style trace` clears inherited Rorschach dimensions. Explicit conflicting options are still errors.

Files are data only, limited to 64 KiB. Unknown fields/settings, duplicate keys, unsupported schema versions, invalid types, and invalid settings fail without rendering. Presets cannot contain commands, external imports, media paths, or actions. Use the supported 2.x CLI to validate them; the lower-level Python helpers remain experimental.

Conversion reports retain `look_preset` and add `preset_name`, `preset_kind` (`look`, `palette`, or `custom`), and `preset_file`. These fields are null when unused. Existing reports continue to include resolved colors, levels, effects, and settings.

## Fremont

`fremont` is a complete visual preset with source-scene grading and automatic readable analysis. The visual settings `analysis`, `analysis_speed`, `analysis_blink_rate`, `analysis_margin`, `analysis_outline_width`, `hud_font`, and `scene_highlights` save/load with the preset and accept explicit overrides in either command order. See [analysis.md](analysis.md) for the recipe and new HUD elements. Detection classes such as vehicles remain per-conversion `--warm-objects` choices.

## Focus, Relic, and Murphy

These complete presets and their independent geometry, shimmer, code placement, and readable-font controls require 2.8.0+. See [focus.md](focus.md). Schema version 1 remains appropriate: visual settings are flat, additive options; local custom-font paths and source-specific target IDs are excluded.
