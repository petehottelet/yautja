# Thermal and HUD colors

These controls work with every thermal look, still images, and videos. They change
color only; segmentation, glyph selection, waveform data, and timecode values stay
the same. Omit them to keep the existing red/cyan HUD and original Yautja palette.

`--no-hud` hides every overlay, regardless of the chosen HUD colors, timecode, or
annotation settings. Thermal colors, textures, and video sound remain active.
Use `--hud` to restore overlays. Reports distinguish effective `hud`, `timecode`,
`verbose`, and `waveform` values from the requested settings.

## Match the HUD to the selected palette

```bash
python -m yautja "clip.mov" "green.mp4" --palette green-phosphor --hud-theme palette --timecode
python -m yautja "photo.jpg" "ironbow.png" --palette ironbow --hud-theme palette
```

`--hud-theme palette` takes coordinated highlights and accents from the thermal
palette, with dimmer scale lines. Green Phosphor uses greens; Amber Phosphor uses
ambers. White Hot uses white and Black Hot uses black for the waveform and
all HUD elements in both `standard` and `palette` modes, including both target
states. Black ink is alpha-composited so it remains visible against light regions.
Matching also works with custom and random thermal palettes. `--hud-theme standard`
uses red/cyan for other palettes, with a muted cyan default for Abyss. `--hud-theme muted-cyan`
selects that subdued theme with any palette. Abyss maps blue-black scenery through
amber and white-hot regions. Matching remains optional; the original Yautja palette
and HUD defaults are unchanged. Heat glow is independent: add `--heat-glow 0.6`
to any palette, and adjust movement with `--heat-glow-speed` (0 freezes it).

## Custom thermal palette

Use `--palette custom --palette-colors "#000000,#0636a8,#e52230,#fff2ba"`.
Supply **2–16 hex colors**, separated by commas or spaces and ordered from cold
to hot. Stops are evenly spaced and interpolated in RGB; the supplied endpoints
are preserved without the original palette's shadow dimming. `#RGB` and `#RRGGBB`
are accepted, with or without `#`; alpha values and named colors are not accepted.
Quote the entire string so a shell does not interpret `#` as a comment.

## Custom HUD elements

Use `--hud-theme custom --hud-colors "waveform=#55ff88,timecode=#caffda"`.
Assignments are separated by commas or semicolons. Unspecified elements keep
their **standard** colors. Each element takes one hex color; its existing shading,
antialiasing, opacity, and glow still apply.

| Element key | Changes |
| --- | --- |
| `waveform` | Moving audio/procedural trace |
| `waveform-axis` | Vertical center line behind the trace |
| `waveform-ticks` | Scale ticks beside the trace |
| `waveform-glyphs` | Glyph rows above and below the waveform |
| `readout` | Upper-right alien readout |
| `timecode` | Optional LCD digits and separators |
| `callouts` | Glyph labels attached to segmented subjects |
| `leaders` | Lines from labels to subjects |
| `markers` | Small circles at the target endpoints |
| `target` | Selected three-blade triangle's primary/landing color |
| `target-flash` | Selected triangle's alternate flash color |

Example with an independent thermal palette and the usual HUD elements assigned:

```bash
python -m yautja "clip.mov" "custom.mp4" --thermal cinematic --verbose --timecode --palette custom --palette-colors "#020518,#173d8f,#10b7ad,#fbad43,#fff1c7" --hud-theme custom --hud-colors "waveform=#ffb347,waveform-axis=#684323,waveform-ticks=#9c6535,waveform-glyphs=#ffd28a,readout=#7fe8ff,timecode=#d6f7ff,callouts=#77ffd0,leaders=#399e83,markers=#ffffff"
```

Custom HUD ink uses normal alpha compositing so black and dark colors work.
Standard, matched, and random HUD themes retain the existing luminous blending.
Glow and VHS/CRT effects can alter final pixel values; use `--glow 0` and omit
those effects when checking exact solid ink colors. Virtual Boy stays entirely
red-only with standard/matched HUD themes. Explicit custom/random HUD themes
or `--target-colors` allow other HUD colors with its red thermal palette.

Selected triangles use `target` and `target-flash`, including in matched and random
themes. `--target-colors "#ff302b,#ffffff"` overrides both keys directly.
Use `--no-target-flash` or equal colors to keep the primary color after assembly.
Custom, random, or muted-cyan HUD themes and explicit target color pairs take
precedence over Black Hot's black default.
See [targets.md](targets.md) for scanning, selecting figures, animation, and display effects.

## Random colors

```bash
python -m yautja "clip.mov" "random.mp4" --random-colors --seed 137
python -m yautja "clip.mov" "random-thermal.mp4" --palette random --hud-theme palette --seed 137
python -m yautja "photo.jpg" "random-hud.png" --palette green-phosphor --hud-theme random --seed 137
```

`--random-colors` selects a random thermal palette **and** independent random
colors for every HUD element. Use `--palette random` or `--hud-theme random` to
randomize just one. Choose a different `--seed` for a new set; the default is 42.
Colors are chosen once per conversion and stay fixed throughout the video,
including scene cuts. The same seed and options reproduce the same colors.
Changing the seed also changes the existing seeded grain, waveform, and glyphs.

The JSON report records resolved `palette_stops` (positions and hex values),
`hud_colors`, `hud_theme`, and `color_seed`, alongside the requested settings.
Random palette stops are evenly spaced, so their reported hex values can be
reused directly as a custom palette. Invalid hex, unknown or duplicate HUD keys,
missing custom values, and conflicting color options fail before media processing
or model setup.
## Thermal levels and reference preset

In Yautja 2.3+, `--look-preset hottropic` applies **HotTropic**. Its recipe is unchanged from Yautja 2.2’s `thermal-spectrum-reference-v1`, which remains a supported alias. It selects Cinematic, the eleven positioned colors below, 12 representative levels, band softness 0.65, black point 0.2, white point 0.9, gamma 1.1, scalar softness 0.8, sensor resolution 192, and seed 42. HUD, grain, pixelation, sensor texture, horizontal/vertical CRT lines, VHS, heat glow, motion blur, and CRT bleed are off.

| Position | RGB |
| --- | --- |
| 0 | `#000000` |
| 0.06 | `#081328` |
| 0.20 | `#173B82` |
| 0.33 | `#176DAD` |
| 0.45 | `#26A5AC` |
| 0.56 | `#62B84E` |
| 0.64 | `#D9C742` |
| 0.72 | `#F26427` |
| 0.80 | `#FF303A` |
| 0.91 | `#FF65AB` |
| 1 | `#E6D8DD` |

`--palette thermal-spectrum` selects only these colors and does not change the thermal mode, levels, or HUD. The preset is a reproducible treatment of the supplied visual reference; its 12-level setting is not a measurement of that compressed image.

| Control | Range / behavior |
| --- | --- |
| `--thermal-levels N` | 2–64 representative values including both endpoints; 0 continuous; omitted preserves legacy grading |
| `--thermal-band-softness S` | 0–1 transition width; 0 hard bands, default 0.35 when levels are set; requires N ≥ 2 |
| `--thermal-black-point B` | 0–0.95; normalized synthetic warmth mapped to the cold end |
| `--thermal-white-point W` | 0.05–1; at least 0.01 above B |
| `--thermal-gamma G` | 0.25–4; 1 neutral, above 1 darkens intermediate values |
| `--thermal-softness R` | 0–8 Gaussian pixels at a 1920px longest edge, scaled to output resolution |

Grading controls require explicit levels (including 0) or a look preset. Spatial softness, band softness, heat glow, and HUD blur are independent. The transfer spatially softens the float field, normalizes between black and white points, applies gamma, applies requested pixelation/grain, then quantizes and maps colors. Explicit levels bypass Cinematic's old mild bands and sensor texture's fixed quantizer. HUD readouts receive the underlying field, before grading; changing level count does not change detection or the model setup. With level controls and the look preset omitted, the existing grading path remains unchanged. Soft bands, glow, and later display effects introduce intermediate RGB values; N counts representative thermal values, not all colors in the final image.

Explicit options override a preset regardless of order. `--thermal-levels 0` clears inherited band softness; explicitly combining continuous mode with band softness is an error. `--sensor-texture` enables its usual grain/pixels/horizontal-line defaults over the clean preset; explicit individual texture flags win. `--hud` enables overlays. Encoder `--preset` remains separate.

```bash
yautja "clip.mov" "reference.mp4" --look-preset hottropic
yautja "photo.jpg" "six-levels.png" --look-preset hottropic --thermal-levels 6 --thermal-band-softness 0
yautja "clip.mov" "features.mp4" --look-preset hottropic --thermal very-detailed --thermal-levels 0 --hud
```

JSON reports include `look_preset`, `thermal_transfer` (`legacy`, `continuous`, or `banded`), all six grading values, scalar softness units, and resolved positioned palette colors. Built-in recipe values remain fixed; save a customized version as a separate JSON preset. See [presets.md](presets.md) for creation, sharing, and file validation.
