# Visual presets

A **preset** combines visual choices: a color palette, thermal detail and levels, HUD styling, waveform appearance, and optional effects. A **palette** is the color ramp inside that preset. Keep `--palette` when changing only colors; use `--stylepreset` to start with a named look.

## Built-in presets

```bash
yautja --list-presets
yautja "clip.mov" "yautja.mp4" --stylepreset yautja
yautja "clip.mov" "green.mp4" --stylepreset green-phosphor
```

`--list-presets` prints JSON containing IDs, display names, kinds, settings, and aliases. It needs no media, FFmpeg, or segmentation models. Names are case-insensitive.

**Yautja** uses eleven colors from black and deep blue through cyan, green, yellow, orange, red, pink, and pale pink-white. It applies **12 thermal levels with soft transitions**, dark scenery, red HUD, cyan callouts, and CRT lines. See [colors.md](colors.md#thermal-levels-and-reference-preset) for the fixed palette positions and grading values.

Palette starter presets are `costa-rica`, `ironbow`, `abyss`, `redline`, `virtualboy`, `green-phosphor`, `amber-phosphor`, `white-hot`, `black-hot`, and `thermal-spectrum`. Each selects that palette with Cinematic detail; other settings use the normal defaults. HUD colors follow the existing palette behavior, including light gray for White Hot, black for Black Hot, and muted cyan for Abyss. Add `--hud-theme palette` for coordinated HUD colors on other palettes.

Explicit options override a preset regardless of argument order:

```bash
yautja "clip.mov" "my-tropic.mp4" --stylepreset yautja --thermal very-detailed --hud --heat-glow 0.6
```

The encoder's existing `--preset fast` option remains separate and keeps its meaning.

**Netrunner** uses a green-tinted source scene, red neon outlines and HUD, rising Cyber rain inside detected subjects, and cyan overhead titles with yellow carets. Select it with `--stylepreset netrunner`. Cyber is its glyph set, configurable through `--HUDglyphs cyber` or `--HUDglyphs yautja`. See [the recipe and individual controls](cyber.md). These settings, including source tint, subject overlays, code motion, glyph choice, and title/caret spacing, are saved with visual presets.

## Ripley

`--stylepreset ripley` combines Cinematic detail with near-black, burnt-orange and amber thermal colors. Its HUD uses burnt orange (`#D35D0C`) for glyphs and callouts, brighter amber (`#EEB03D`) for the waveform and targets, and dim brown scale lines. Highlights remain amber. Timecode and callouts are enabled, with a restrained glow.

Use `--palette ripley` to select only the thermal ramp. The complete preset, per-element colors and explicit overrides save as ordinary schema-1 settings. [Runnable example](examples.md#ripley).

## Parker

`--stylepreset parker` (also `--stylepreset "Parker"`) preserves the original scene colors and draws glowing amber contours around detected objects with 35% amber fill. The default contour grid is 33.6 reference pixels with a line width of 5.6 reference pixels. Horizontal CRT lines (strength 0.18) and phosphor bleed (0.2) affect the entire frame, including the footage and every overlay. The default uses glowing amber CRT lettering, markers and decorative rules on padded black backing that follows the widths of the rows and graphics at top left, a schematic city map with simulated coordinates at top right, an elevation profile at bottom left and telemetry at bottom right. The map, terrain and signal graphics are decorative simulations, not measurements or source geolocation.

- `--object-outline off|chunky|box` selects the default for all recognized objects. Chunky contours and rectangular boxes are mutually exclusive for each object. `--object-outline-width`, `--object-outline-block` and `--object-outline-padding` control thickness, square grid size and box clearance independently. `--object-outline-fill` sets interior opacity from 0 to 1, using the outline color; 0.5 gives a 50% fill. Overlapping objects do not stack fill opacity. `--object-outline-glow` sets edge bloom and core brightness independently of fill, using the same glow treatment as the readout. Contours follow stabilized masks; boxes enclose the full object, including non-human classes requested through `--warm-objects` or `--hot-objects`.
- Scan with `--list-figures`, inspect its HTML contact sheet, then use `--figures figures.json --object-outlines "S001-F001=chunky,S001-F002=box,S002-F001=chunky"`. `off` hides an individual outline; unspecified figures retain the default. Set `--object-outline off` to outline only the assigned figures. IDs are local to a scene. Live masks are matched to the source-verified catalog by class and overlapping boxes, with one-to-one assignments and continuity while a track remains visible. Unmatched IDs are reported, with no fabricated silhouette fallback. Use the same detection classes and scan resolution for reliable matching.
- `--hud-top-left`, `--hud-top-right`, `--hud-bottom-left` and `--hud-bottom-right` each select `off`, `readout`, `city-map`, `elevation` or `telemetry`. `--hud-panel-scale` and `--hud-panel-margin` adjust placement within the frame. All panels default to black ink on transparency.
- `--hud-font pixel` retains the solid five-by-seven uppercase alphabet. Three distinct terminal faces are available: `crt` has serifed letterforms, `crt-clean` has taller, cleaner stems, and `crt-wide` has chunky, solid eight-column letterforms. The CRT faces include lowercase letters and printable ASCII. All four are available to other presets; existing bundled fonts and local font overrides also work.
- `--readout-style ink` uses its corner's HUD color on transparency. `reversed` draws solid black highlights 15% taller than the lettering (rounded to pixels), with transparent letter cutouts so the source remains visible inside the text. `amber-reversed` uses glowing amber highlights with the same transparent lettering. `amber-bars` places bright, glowing amber text on separate black highlight bars while keeping the gaps transparent. `amber-black` fits padded opaque black backing to each text-and-marker row, divider and footer strip, creating a stepped contour with transparent space beside shorter rows, with a tight amber fringe and broad bloom; `amber-glow` adds a luminous border and dim amber fill. `--readout-color`, `--readout-glow` and `--readout-fill` (default 0.24) tune these treatments independently of global neon. The style applies wherever `readout` is placed; the other instruments keep their own colors.

The HUD roles `object-outline`, `corner-top-left`, `corner-top-right`, `corner-bottom-left` and `corner-bottom-right` accept independent colors, opacity, blur and neon. The amber styles take their text/border color from `--readout-color`. `--no-hud` hides every overlay. Parker suppresses the ordinary waveform, glyph readout and reticles through its opacity map; replacing that map also replaces those suppressions.

All visual options save/load with presets. `--object-outlines` and `--figures` remain source-specific runtime inputs. A model-free corner-HUD render is available with `--thermal luminance --object-outline off`; enabled object outlines require the segmented runtime. [Complete commands](examples.md#parker).

## Save your own preset

Saving is a separate operation: omit input and output media paths. No inference or conversion runs.

```bash
yautja --stylepreset yautja --hud --hud-theme palette --neon --heat-glow 0.6 --timecode --verbose --save-preset "tropic-glow.json" --preset-name "Tropic Glow"
yautja "clip.mov" "glowing.mp4" --preset-file "tropic-glow.json"
yautja "clip.mov" "less-glow.mp4" --preset-file "tropic-glow.json" --heat-glow 0.2
```

The saved file contains the complete resolved visual settings, including defaults, so it can be copied to another machine or given to another agent. `--preset-name` is optional and defaults to the filename stem. Existing files require explicit `--overwrite`. To edit a saved preset, load it, apply changes, and save to a new filename (or explicitly overwrite the existing file).

Preset files store thermal mode, palette/custom colors, levels and tonal controls, HUD colors/visibility/blur/opacity, target shape/colors/timing/outline, waveform settings, texture, glow, display effects, and seed. They exclude media paths, figure catalogs and selected IDs, trims, output resolution/frame rate/encoding, audio-track selection/muting, model configuration, and overwrite permission. Choose those separately per source. Nonvisual flags are rejected when saving, rather than silently dropped. A preset styles targets and can enable `target_mode: "auto"` for segmented subjects. Select specific figures using `--figures` and `--target` when rendering.

Image and video conversions share the same preset loader. The existing media restrictions still apply: custom audio waveform settings such as `waveform: "audio"`, nondefault `wave_window`, or nondefault `wave_gain` require video input.

## Write or share a JSON preset

[Tropic Glow](../assets/presets/tropic-glow.json) is an editable custom preset made from the built-in Yautja style. It keeps Yautja's colors, Cinematic detail, and 12 soft thermal levels, then adds palette-matched HUD elements, timecode, callouts, heat glow at 0.6, and neon illumination. Yautja itself uses red HUD, cyan callouts, and CRT lines; heat glow and neon are off. Load the custom example with `--preset-file`; `--stylepreset yautja` selects the built-in starting look. Add `--no-neon` when loading the file to turn off only the neon styling.

The compact example inherits Yautja through its `base` field. Files use UTF-8 JSON with schema version 1:

```json
{
  "schema_version": 1,
  "name": "Tropic Glow",
  "description": "Yautja colors and thermal levels with palette-matched neon HUD elements and animated heat glow.",
  "base": "yautja",
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

For CRT patterns, use `"crt_grid": true` for horizontal/vertical lines or `"crt_crosshatch": true` for a grid at 45 degrees, with `"crt_strength": 0.25` to set their darkness. Both pattern keys can be explicitly disabled with `--no-crt-grid` or `--no-crt-crosshatch` when loading a preset.

For neon HUD artwork, save `"neon": true` with optional `neon_intensity` (0–2, default 1), `neon_spread` (0–2, default 0.6), `neon_flicker` (0–1, default 0), and `neon_elements` (a comma-separated override string or null). `"neon_elements": "waveform=0.6,target=1.2,timecode=0"` keeps the timecode's original ink, lowers waveform emission, and increases target emission. Tuning without `neon: true` is saved but inactive. The included [Abyss Neon preset](../assets/presets/abyss-neon.json) uses a steady cyan target, full neon HUD, vertical CRT, and scene heat glow. Source-specific target selections still come from `--figures` and `--target` on the render command.

```bash
yautja "clip.mov" "abyss-neon.mp4" --preset-file "abyss-neon.json" --figures "figures.json" --target S001-F003
yautja --preset-file "abyss-neon.json" --neon-spread 0.4 --save-preset "my-neon.json" --preset-name "My Neon"
```

Precedence is **CLI defaults → built-in base → file settings → explicit CLI options**. Choose either `--stylepreset` or `--preset-file`; a file can declare its own built-in base. Explicit `--thermal-levels 0` clears inherited band softness. `--sensor-texture` enables the combined effect's normal defaults unless individual texture controls are also specified. Changing away from custom palette/HUD modes clears their inherited custom color strings; switching to `--wave-style trace` clears inherited Rorschach dimensions. Explicit conflicting options are still errors.

Files are data only, limited to 64 KiB. Unknown fields/settings, duplicate keys, unsupported schema versions, invalid types, and invalid settings fail without rendering. Presets cannot contain commands, external imports, media paths, or actions. Use the supported 2.x CLI to validate them; the lower-level Python helpers remain experimental.

Conversion reports retain `look_preset` and add `preset_name`, `preset_kind` (`look`, `palette`, or `custom`), and `preset_file`. These fields are null when unused. Existing reports continue to include resolved colors, levels, effects, and settings.

## Fremont

`fremont` is a complete visual preset with source-scene grading and automatic readable analysis. The visual settings `analysis`, `analysis_speed`, `analysis_blink_rate`, `analysis_margin`, `analysis_outline_width`, `analysis_target`, `analysis_target_size`, `analysis_target_response`, `hud_font`, and `scene_highlights` save/load with the preset and accept explicit overrides in either command order. See [analysis.md](analysis.md) for the recipe and new HUD elements. Detection classes such as vehicles remain per-conversion `--warm-objects` choices.

## Focus, Relic, and Murphy

These complete presets and their independent geometry, shimmer, code placement, and readable-font controls are independently configurable. See [focus.md](focus.md). Schema version 1 remains appropriate: visual settings are flat, additive options; local custom-font paths and source-specific target IDs are excluded.

The persistent Fremont scan target’s enablement is independent of readable analysis, while both share subject selection and cycle speed. Motion state and current track/position are report data, never saved settings. Schema version 1 remains unchanged.
