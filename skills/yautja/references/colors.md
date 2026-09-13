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
ambers; White Hot uses gray/white ink. Black Hot uses black for the waveform and
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
