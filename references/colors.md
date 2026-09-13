# Thermal and HUD colors

These controls work with every thermal look, still images, and videos. They change
color only; segmentation, glyph selection, waveform data, and timecode values stay
the same. Omit them to keep the existing red/cyan HUD and original Yautja palette.

## Match the HUD to the selected palette

```bash
python scripts/yautja.py "clip.mov" "green.mp4" --palette green-phosphor --hud-theme palette --timecode
python scripts/yautja.py "photo.jpg" "ironbow.png" --palette ironbow --hud-theme palette
```

`--hud-theme palette` takes coordinated highlights and accents from the thermal
palette, with dimmer scale lines. Green Phosphor uses greens; Amber Phosphor uses
ambers; White Hot and Black Hot use gray/white HUD ink. It also works with custom
and random thermal palettes. `--hud-theme standard` retains the familiar red/cyan
HUD. Matching is optional, not a change to the default.

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

Full example, with an independent thermal palette and every HUD element assigned:

```bash
python scripts/yautja.py "clip.mov" "custom.mp4" --thermal cinematic --verbose --timecode --palette custom --palette-colors "#020518,#173d8f,#10b7ad,#fbad43,#fff1c7" --hud-theme custom --hud-colors "waveform=#ffb347,waveform-axis=#684323,waveform-ticks=#9c6535,waveform-glyphs=#ffd28a,readout=#7fe8ff,timecode=#d6f7ff,callouts=#77ffd0,leaders=#399e83,markers=#ffffff"
```

Custom HUD ink uses normal alpha compositing so black and dark colors work.
Standard, matched, and random HUD themes retain the existing luminous blending.
Glow and VHS/CRT effects can alter final pixel values; use `--glow 0` and omit
those effects when checking exact solid ink colors. Virtual Boy stays entirely
red-only with standard/matched HUD themes. Explicit custom/random HUD themes
allow other HUD colors with its red thermal palette.

## Random colors

```bash
python scripts/yautja.py "clip.mov" "random.mp4" --random-colors --seed 137
python scripts/yautja.py "clip.mov" "random-thermal.mp4" --palette random --hud-theme palette --seed 137
python scripts/yautja.py "photo.jpg" "random-hud.png" --palette green-phosphor --hud-theme random --seed 137
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
