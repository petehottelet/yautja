# Focus, Relic, Murphy, and readable fonts

A style preset is a recipe of ordinary visual settings. All controls below save in schema-version-1 presets except the local `--hud-font-file` path. Explicit options override a preset in either argument order. A supplied element map replaces the preset's map; omitted keys inherit that control's global value.

## Complete styles

**Focus** uses a blue-violet source scene and neon-purple HUD. A curved, triangulated geodesic sphere wraps around the viewpoint; thicker broken lines fade toward the center. Satellite dots pulse outward and back along incident edges, and some vertices carry seven-sided rings. Thick partial subject contours glow bluish-lavender/white, with raster texture and moving light bands. Yellow holographic scan patches follow only the currently selected subject. A single persistent hexagon glides between subjects, without acquisition zoom. Its central circle is 90% of the inscribed radius, with six small circles inside, four outside, and a small central square. **Relic** adds pink broken-edge triangles that rise, contract, spin and fade away, plus dense rising code behind all silhouettes. Focus keeps code off. **Murphy** uses a blue cast, glowing green targeting and current-mask outlines, a 25% larger box with center-crossing XY axes, and large Orbitron Medium text with a blinking underscore. Its waveform and upper-right readout are hidden.

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
| `--outline-style solid\|shimmer\|holographic` | `solid` | Continuous edge, partial highlights, or textured partial projection with pale cores; requires `--subject-outline` |
| `--outline-width` | Automatic | Edge thickness at 1080p, 0.5–20; solid uses 2, shimmer 3, holographic 8 |
| `--outline-coverage` | `0.35` | Highlight coverage, 0–1; 0 hides partial highlights |
| `--outline-arcs` | `5` | Number of highlights, integer 1–12 |
| `--outline-speed` | `1` | Travel, twinkle and holographic texture speed, 0–5; 0 freezes all three |
| `--code-layer inside\|behind` | `inside` | Placement of `--subject-code`; behind-code extends above and beside subjects |
| `--code-density` | `0.65` | Stream density, 0–3; below 1 selects a fraction of columns, above 1 packs more streams into the same area without shrinking glyphs. Relic uses 1.65, three times its former 0.55 density |

The final behind-code glow and blur are occluded by the union of current visible subject masks, including overlapping subjects. Other HUD elements remain visible over figures. Current masks drive the outline position; shimmer brightness moves around edge regions, using an angular approximation rather than exact contour distance. Seed and track IDs keep the motion reproducible. Stills freeze shimmer and behind-code at time zero.

`subject-outline` and `subject-code` retain their existing HUD color, blur, opacity, and neon controls. These features need segmented subjects regardless of source or thermal grading. Tuning an inactive feature is permitted and saved.

## Grid, targets, and captions

| Option | Default | Behavior |
| --- | --- | --- |
| `--geo-grid` / `--no-geo-grid` | Off | Full-frame triangular lattice, drawn beneath other HUD artwork |
| `--geo-grid-scale` | `160` | Spacing, 40–480 reference pixels at a 1080px short edge |
| `--geo-grid-jitter` | `0.65` | Seeded vertex irregularity, 0–1 |
| `--geo-grid-speed` | `1` | Brightness and satellite movement, 0–5; 0 freezes both |
| `--geo-grid-center-fade` | `0` | Center attenuation, 0–1; 0 is uniform, 1 clears the center. Focus/Relic use 0.96; outer edges retain their brightness |
| `--geo-grid-width` | `1.3` | Line thickness, 0.5–6 reference pixels at a 1080px short edge; Focus/Relic use 2.2 |
| `--geo-grid-breaks` | `0` | Seeded irregular gaps, 0–1; 0 keeps continuous lines. Focus/Relic use 0.7 |
| `--geo-grid-details` / `--no-geo-grid-details` | Off | Pulsing satellite dots and seven-sided node rings; enabled by Focus/Relic and animated by `--geo-grid-speed` |
| `--geo-grid-projection flat\|sphere` | `flat` | Flat lattice or great-circle arcs on a subdivided icosahedron, projected from the sphere center |
| `--target-mode selected\|auto\|cycle` | `selected` | Catalog selections, all automatic subjects, or one cycling subject; catalogs supply the candidate pool |
| `--target-shape hexagon` | — | Hexagon, circle at 90% of its inscribed radius, ten small circles and center square |
| `--target-shape frame-box` | — | Box with center-crossing XY axes extending to frame edges; stays axis-aligned |
| `--target-motif none\|triangles` | `none` | Seeded hollow triangle ornaments around each visible target |
| `--target-motif-count` | `7` | Triangles per target, integer 0–24 |
| `--target-motif-scale` | `1` | Ornament size and spread, 0.25–3 |
| `--target-motif-speed` | `1` | Rise, contraction and spin speed, 0–5; 0 freezes the ornaments |
| `--target-motif-breaks` | `0` | Unequal, seeded gaps in triangle edges, 0–1; Relic uses 0.7 |
| `--target-label` | Unset | One readable lower-left caption, 1–24 printable ASCII characters; preserves case |
| `--no-target-label` | — | Clear a caption inherited from a style preset |
| `--target-motion acquire\|persistent` | `acquire` | Assembly animation or one constant-size reticle with smooth motion; persistent mode also sweeps empty automatic scenes |
| `--target-hold` | `3` | Seconds per subject before cycling, 0.5–30 |
| `--target-response` | `0.6` | Seconds to cover 95% of a stationary focus change, 0–3; 0 follows immediately |
| `--target-fill auto\|filled\|stroked` | `auto` | Original styling, solid marks/translucent enclosures, or hollow mark outlines; works with all target types |
| `--target-weak-spots` / `--no-target-weak-spots` | Off | Fictional holographic scan patches on the selected subject; enabled by Focus/Relic, requires segmentation |
| `--target-outline` / `--no-target-outline` | Off | Outline only selected subjects using their current masks; needs segmentation |
| `--target-label-scale` | `1` | Caption size multiplier, 0.5–4; Murphy uses 1.8 |
| `--target-cursor` / `--no-target-cursor` | Off | Blink an underscore after the caption; on for Murphy |


The HUD elements are `geo-grid`, `target-motif`, `target-label`, `target-outline`, and `target-weak-spots`. Each supports `--hud-colors`, `--hud-opacity-elements`, `--hud-blur-elements`, and `--neon-elements`. Motifs and captions follow target acquisition and tracking visibility, independently of target opacity or flashing. They disappear without a visible target. Captions scale to fit inside the frame, reserving cursor space throughout its blink cycle. Stills show a fully acquired target and visible cursor. Persistent motion resets on cuts and backward seeks, holds continuity at repeated timestamps, and never smooths subject masks. `--no-hud` hides all of them.

```bash
yautja "clip.mov" "custom.mp4" --stylepreset focus --geo-grid-scale 220 --target-motif triangles --target-label "LOCK"
yautja --stylepreset focus --geo-grid-scale 220 --save-preset "my-focus.json"
yautja "clip.mov" "broken-grid.mp4" --stylepreset focus --geo-grid-center-fade 1 --geo-grid-width 2.5 --geo-grid-breaks 0.8
yautja "clip.mov" "relic-motion.mp4" --stylepreset relic --target-motif-speed 1.2 --target-motif-breaks 0.7 --code-density 1.65
```

Triangle lifetimes and edge gaps are seeded independently. Each ornament fades in, drifts slightly upward, then shrinks and spins out before its next cycle. Stills freeze the ornaments and code at time zero. Grid gaps stay fixed while brightness shimmers, so they do not flicker randomly between frames. These controls work in both grid projections and save with the preset.

Holographic outlines use `subject-outline` as their base color, mixing in pale cores and animated raster detail. Focus/Relic use `#A6B4FF` for the bluish-lavender edge and `#FFD34D` for yellow patches; the remaining HUD stays purple. Both effects keep their sharp artwork within the current silhouette, while glow can extend past it. Patches use seeded decorative positions, not anatomical or physical weak-point detection. They clear when no subject is selected, and explicit catalog targets resolve to their matching silhouette. Stills freeze both textures.

```bash
yautja "clip.mov" "hologram.mp4" --stylepreset focus --outline-width 10 --outline-coverage 0.4
yautja "clip.mov" "subtle-patches.mp4" --stylepreset focus --hud-opacity-elements "target-weak-spots=0.45"
yautja "clip.mov" "simple-grid.mp4" --stylepreset focus --no-geo-grid-details --no-target-weak-spots
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
