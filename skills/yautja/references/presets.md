# Visual presets

Available in Yautja 2.3+. A **preset** combines visual choices: a color palette, thermal detail and levels, HUD styling, waveform appearance, and optional effects. A **palette** is the color ramp inside that preset. Keep `--palette` when changing only colors; use `--look-preset` to start with a named look.

## Built-in presets

```bash
yautja --list-presets
yautja "clip.mov" "hottropic.mp4" --look-preset hottropic
yautja "clip.mov" "green.mp4" --look-preset green-phosphor
```

`--list-presets` prints JSON containing IDs, display names, kinds, settings, and aliases. It needs no media, FFmpeg, or segmentation models. Names are case-insensitive.

**HotTropic** uses eleven colors from black and deep blue through cyan, green, yellow, orange, red, pink, and pale pink-white. It applies **12 thermal levels with soft transitions**, dark scenery, and no HUD or sensor texture. Its exact recipe is unchanged from `thermal-spectrum-reference-v1`, which remains a supported alias. See [colors.md](colors.md#thermal-levels-and-reference-preset) for the fixed palette positions and grading values.

Every existing palette also has a starter preset: `yautja`, `ironbow`, `abyss`, `redline`, `virtualboy`, `green-phosphor`, `amber-phosphor`, `white-hot`, `black-hot`, and `thermal-spectrum`. Each selects that palette with Cinematic detail; other settings use the normal defaults. HUD colors follow the existing palette behavior, including white for White Hot, black for Black Hot, and muted cyan for Abyss. Add `--hud-theme palette` for coordinated HUD colors on other palettes.

Explicit options override a preset regardless of argument order:

```bash
yautja "clip.mov" "my-tropic.mp4" --look-preset hottropic --thermal very-detailed --hud --heat-glow 0.6
```

The encoder's existing `--preset fast` option remains separate and keeps its meaning.

## Save your own preset

Saving is a separate operation: omit input and output media paths. No inference or conversion runs.

```bash
yautja --look-preset hottropic --hud --hud-theme palette --heat-glow 0.6 --timecode --verbose --save-preset "tropic-glow.json" --preset-name "Tropic Glow"
yautja "clip.mov" "glowing.mp4" --preset-file "tropic-glow.json"
yautja "clip.mov" "less-glow.mp4" --preset-file "tropic-glow.json" --heat-glow 0.2
```

The saved file contains the complete resolved visual settings, including defaults, so it can be copied to another machine or given to another agent. `--preset-name` is optional and defaults to the filename stem. Existing files require explicit `--overwrite`. To edit a saved preset, load it, apply changes, and save to a new filename (or explicitly overwrite the existing file).

Preset files store thermal mode, palette/custom colors, levels and tonal controls, HUD colors/visibility/blur/opacity, target shape/colors/timing/outline, waveform settings, texture, glow, display effects, and seed. They exclude media paths, figure catalogs and selected IDs, trims, output resolution/frame rate/encoding, audio-track selection/muting, model configuration, and overwrite permission. Choose those separately per source. Nonvisual flags are rejected when saving, rather than silently dropped. A preset styles targets; select actual figures using `--figures` and `--target` when rendering.

Image and video conversions share the same preset loader. The existing media restrictions still apply: custom audio waveform settings such as `waveform: "audio"`, nondefault `wave_window`, or nondefault `wave_gain` require video input.

## Write or share a JSON preset

[Tropic Glow example](../assets/presets/tropic-glow.json) is a compact editable version of the example above. Files use UTF-8 JSON with schema version 1:

```json
{
  "schema_version": 1,
  "name": "Tropic Glow",
  "base": "hottropic",
  "settings": {
    "hud": true,
    "hud_theme": "palette",
    "heat_glow": 0.6,
    "timecode": true,
    "verbose": true
  }
}
```

`base` is optional and can name only a built-in preset. Omitted settings inherit that base, or ordinary CLI defaults when there is no base. Settings use CLI option names with underscores and without `--`; use `scanlines` for horizontal CRT lines. Values must use their actual JSON types: booleans, numbers, or strings. An optional `description` is display text, never instructions. Exported presets are flattened snapshots and do not depend on `base`.

For CRT patterns, use `"crt_grid": true` for horizontal/vertical lines or `"crt_crosshatch": true` for a grid at 45 degrees, with `"crt_strength": 0.25` to set their darkness. Both pattern keys require Yautja 2.4+ and can be explicitly disabled with `--no-crt-grid` or `--no-crt-crosshatch` when loading a preset.

Precedence is **CLI defaults → built-in base → file settings → explicit CLI options**. Choose either `--look-preset` or `--preset-file`; a file can declare its own built-in base. Explicit `--thermal-levels 0` clears inherited band softness. `--sensor-texture` enables the combined effect's normal defaults unless individual texture controls are also specified. Changing away from custom palette/HUD modes clears their inherited custom color strings; switching to `--wave-style trace` clears inherited Rorschach dimensions. Explicit conflicting options are still errors.

Files are data only, limited to 64 KiB. Unknown fields/settings, duplicate keys, unsupported schema versions, invalid types, and invalid settings fail without rendering. Presets cannot contain commands, external imports, media paths, or actions. Use the supported 2.x CLI to validate them; the lower-level Python helpers remain experimental.

Conversion reports retain `look_preset` and add `preset_name`, `preset_kind` (`look`, `palette`, or `custom`), and `preset_file`. These fields are null when unused. Existing reports continue to include resolved colors, levels, effects, and settings.
