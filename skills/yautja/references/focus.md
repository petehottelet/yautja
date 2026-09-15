# Focus, Relic, Murphy, and readable fonts

Requires Yautja 2.8.0+. A style preset is a recipe of ordinary visual settings. All controls below save in schema-version-1 presets except the local `--hud-font-file` path. Explicit options override a preset in either argument order. A supplied element map replaces the preset's map; omitted keys inherit that control's global value.

## Complete styles

**Focus** preserves the source scene under a pale blue-violet tint, with a shimmering triangular grid, moving partial silhouette highlights, and thin hexagon reticles. **Relic** uses the same settings with pink hollow-triangle ornaments and rising pink code behind subjects. Both require the segmented setup. They select detected subjects automatically; a catalog is optional.

```bash
yautja "clip.mov" "focus.mp4" --stylepreset focus
yautja "clip.mov" "relic.mp4" --stylepreset relic
yautja "clip.mov" "selected-relic.mp4" --stylepreset relic --figures "figures.json" --target S001-F002
```

**Murphy** retains source detail, adds heavy CRT scanlines, green readable Tech text, and an axis-aligned frame-box target with a steady TARGETING caption. Its waveform is hidden. Conversion runs with the lightweight install. To display its target and caption, provide a previously generated figure catalog; creating that catalog needs the segmented setup.

```bash
yautja "clip.mov" "murphy.mp4" --stylepreset murphy --figures "figures.json" --target S001-F002
yautja "clip.mov" "murphy-bold.mp4" --stylepreset murphy --hud-font orbitron-bold --figures "figures.json" --target S001-F002
```

Without a catalog, Murphy still applies its source grade, CRT texture, and readable readout. To use automatic targets instead, add `--thermal low-detail --target-mode auto` and install the segmented runtime.

## Subject edges and code

| Option | Default | Behavior |
| --- | --- | --- |
| `--outline-style solid\|shimmer` | `solid` | Continuous edge or moving partial highlights; requires `--subject-outline` to draw |
| `--outline-coverage` | `0.35` | Highlight coverage, 0–1; 0 hides shimmer |
| `--outline-arcs` | `5` | Number of highlights, integer 1–12 |
| `--outline-speed` | `1` | Travel and twinkle speed, 0–5; 0 freezes both |
| `--code-layer inside\|behind` | `inside` | Placement of `--subject-code`; behind-code extends above and beside subjects |

The final behind-code glow and blur are occluded by the union of current visible subject masks, including overlapping subjects. Other HUD elements remain visible over figures. Current masks drive the outline position; shimmer brightness moves around edge regions, using an angular approximation rather than exact contour distance. Seed and track IDs keep the motion reproducible. Stills freeze shimmer and behind-code at time zero.

`subject-outline` and `subject-code` retain their existing HUD color, blur, opacity, and neon controls. These features need segmented subjects regardless of source or thermal grading. Tuning an inactive feature is permitted and saved.

## Grid, targets, and captions

| Option | Default | Behavior |
| --- | --- | --- |
| `--geo-grid` / `--no-geo-grid` | Off | Full-frame triangular lattice, drawn beneath other HUD artwork |
| `--geo-grid-scale` | `160` | Spacing, 40–480 reference pixels at a 1080px short edge |
| `--geo-grid-jitter` | `0.65` | Seeded vertex irregularity, 0–1 |
| `--geo-grid-speed` | `1` | Brightness animation, 0–5; 0 freezes it |
| `--target-mode selected\|auto` | `selected` | Catalog selections or all visible segmented subjects; explicit catalog selections always win |
| `--target-shape hexagon` | — | Thin closed hexagon using ordinary acquisition, flash, and target controls |
| `--target-shape frame-box` | — | Open-interior box with horizontal and vertical axes extending to frame edges; stays axis-aligned |
| `--target-motif none\|triangles` | `none` | Seeded hollow triangle ornaments around each visible target |
| `--target-motif-count` | `7` | Triangles per target, integer 0–24 |
| `--target-motif-scale` | `1` | Ornament size and spread, 0.25–3 |
| `--target-label` | Unset | One readable lower-left caption, 1–24 printable ASCII characters; preserves case |
| `--no-target-label` | — | Clear a caption inherited from a style preset |

The new HUD elements are `geo-grid`, `target-motif`, and `target-label`. Each supports `--hud-colors`, `--hud-opacity-elements`, `--hud-blur-elements`, and `--neon-elements`. Motifs and captions follow target acquisition and tracking visibility, independently of target opacity or flashing. They disappear without a visible target. Captions scale to fit inside the frame; stills show them fully acquired. `--no-hud` hides all of them.

```bash
yautja "clip.mov" "custom.mp4" --stylepreset focus --geo-grid-scale 220 --target-motif triangles --target-label "LOCK"
yautja --stylepreset focus --geo-grid-scale 220 --save-preset "my-focus.json"
```

An editable [Wide Focus example](../assets/presets/focus.json) demonstrates a compact preset based on Focus.

## Readable typography

`--HUDglyphs tech` selects Latin letters and numbers everywhere the other glyph sets are used: readouts, waveform decorations, callouts, subject titles, and code. Tech timecode uses the chosen readable font. The other choices remain `yautja` and `cyber`.

| `--hud-font` | Bundled face |
| --- | --- |
| `michroma` | Michroma Regular; default |
| `orbitron` | Orbitron Light |
| `orbitron-medium` | Orbitron Medium |
| `orbitron-bold` | Orbitron Bold; Fremont default |

The font also controls readable analysis and target captions, even when the glyph set is Yautja or Cyber. `--hud-font-file "C:\Fonts\MyFont.otf"` overrides the bundled choice for that conversion. TTF/OTF files must cover printable ASCII and load successfully before media opens. The machine-specific path cannot be saved in a portable preset or loaded from JSON. Reports identify the font family, weight, and resolved custom path when used.

Michroma and Orbitron retain their SIL Open Font Licenses, bundled beside their unmodified font files. [Pinned sources and checksums](https://github.com/petehottelet/yautja/blob/main/src/yautja/assets/fonts/README.md).
