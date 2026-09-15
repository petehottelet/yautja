# Focus, Relic, Murphy, and readable fonts

A style preset is a recipe of ordinary visual settings. All controls below save in schema-version-1 presets except the local `--hud-font-file` path. Explicit options override a preset in either argument order. A supplied element map replaces the preset's map; omitted keys inherit that control's global value.

## Complete styles

**Focus** uses a blue-violet source scene and neon-purple HUD. A curved, triangulated geodesic sphere wraps around the viewpoint. A single persistent hexagon glides between subjects, without acquisition zoom. Its central circle is inscribed in the hexagon, with six small circles inside, four outside, and a small central square. **Relic** adds pink triangle ornaments and rising code behind all silhouettes. **Murphy** uses a blue cast, glowing green targeting and current-mask outlines, a 25% larger box with center-crossing XY axes, and large Orbitron Medium text with a blinking underscore. Its waveform and upper-right readout are hidden.

All three use the segmented runtime and automatically cycle through subjects. A catalog is optional and limits the candidate pool. Focus and Relic use persistent motion; Murphy retains acquisition animation. For Murphy's source grade alone without models, use `--thermal classic --target-mode selected --no-target-outline`.

```bash
yautja "clip.mov" "focus.mp4" --stylepreset focus
yautja "clip.mov" "relic.mp4" --stylepreset relic
yautja "clip.mov" "murphy.mp4" --stylepreset murphy
yautja "clip.mov" "selected.mp4" --stylepreset focus --figures "figures.json" --target S001-F002
```

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
| `--target-mode selected\|auto\|cycle` | `selected` | Catalog selections, all automatic subjects, or one cycling subject; catalogs supply the candidate pool |
| `--target-shape hexagon` | — | Hexagon, inscribed circle, ten small circles and center square |
| `--target-shape frame-box` | — | Box with center-crossing XY axes extending to frame edges; stays axis-aligned |
| `--target-motif none\|triangles` | `none` | Seeded hollow triangle ornaments around each visible target |
| `--target-motif-count` | `7` | Triangles per target, integer 0–24 |
| `--target-motif-scale` | `1` | Ornament size and spread, 0.25–3 |
| `--target-label` | Unset | One readable lower-left caption, 1–24 printable ASCII characters; preserves case |
| `--no-target-label` | — | Clear a caption inherited from a style preset |
| `--geo-grid-projection flat\|sphere` | `flat` | Flat lattice or great-circle arcs on a subdivided icosahedron, projected from the sphere center |
| `--target-motion acquire\|persistent` | `acquire` | Assembly animation or one constant-size reticle with smooth motion; persistent mode also sweeps empty automatic scenes |
| `--target-hold` | `3` | Seconds per subject before cycling, 0.5–30 |
| `--target-response` | `0.6` | Seconds to cover 95% of a stationary focus change, 0–3; 0 follows immediately |
| `--target-fill auto\|filled\|stroked` | `auto` | Original styling, translucent filled interiors, or stroked contours; open paths remain lines |
| `--target-outline` / `--no-target-outline` | Off | Outline only selected subjects using their current masks; needs segmentation |
| `--target-label-scale` | `1` | Caption size multiplier, 0.5–4; Murphy uses 1.8 |
| `--target-cursor` / `--no-target-cursor` | Off | Blink an underscore after the caption; on for Murphy |


The new HUD elements are `geo-grid`, `target-motif`, `target-label`, and `target-outline`. Each supports `--hud-colors`, `--hud-opacity-elements`, `--hud-blur-elements`, and `--neon-elements`. Motifs and captions follow target acquisition and tracking visibility, independently of target opacity or flashing. They disappear without a visible target. Captions scale to fit inside the frame, reserving cursor space throughout its blink cycle. Stills show a fully acquired target and visible cursor. Persistent motion resets on cuts and backward seeks, holds continuity at repeated timestamps, and never smooths subject masks. `--no-hud` hides all of them.

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
| `orbitron-medium` | Orbitron Medium; Murphy default |
| `orbitron-bold` | Orbitron Bold; Fremont default |

The font also controls readable analysis and target captions, even when the glyph set is Yautja or Cyber. `--hud-font-file "C:\Fonts\MyFont.otf"` overrides the bundled choice for that conversion. TTF/OTF files must cover printable ASCII and load successfully before media opens. The machine-specific path cannot be saved in a portable preset or loaded from JSON. Reports identify the font family, weight, and resolved custom path when used.

Michroma and Orbitron retain their SIL Open Font Licenses, bundled beside their unmodified font files. [Pinned sources and checksums](https://github.com/petehottelet/yautja/blob/main/src/yautja/assets/fonts/README.md).
