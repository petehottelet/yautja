# Noumenon

`--stylepreset noumenon` replaces the whole scene with animated green code. Selected silhouettes carry brighter, glowing glyph strokes, including over dark clothing. Every other area, including unselected silhouettes, uses source luminance for glyph lightness and darkness. No photographic RGB is composited. The HUD, outlines, labels, sensor texture and CRT effects default off. `--hud` enables the existing overlays independently.

```bash
yautja "input.mp4" "output-noumenon.mp4" --stylepreset noumenon
yautja "photo.jpg" "output-noumenon.png" --stylepreset noumenon
```

The preset uses the existing segmented setup and cached models. It adds no learned geometry model, network request, browser or live glyph generator. `--thermal luminance` runs without semantic models, with full environment coverage and image-based room mapping when the optional tracking extra is installed. It cannot emphasize undetected subjects.

## Choose brighter silhouettes

Scan the source and open the generated `figures.html` list. Choose the IDs of the silhouettes that should glow brighter; substitute your actual IDs below.

```bash
yautja "input.mp4" "figures.json" --list-figures
yautja "input.mp4" "selected-noumenon.mp4" --stylepreset noumenon --figures "figures.json" --material-subjects S001-F001,S001-F003
```

`--material-subjects all` is the default and brightens every detected silhouette. `--material-subjects none` uses luminance shading everywhere. Repeat the flag or comma-separate IDs to select multiple figures. ID selection requires segmentation and the catalog from the same source; it works with the HUD off. IDs are shot-local, so choose the figure's ID again after a cut. Trims use source-relative catalog timestamps, while the code animation starts at zero. Reports list selected, matched and unmatched IDs under `material_subjects`, `material_subjects_seen` and `material_subjects_unseen`.

Each silhouette clips its own independently seeded rain instance at its edges, in front of the background rain. Glyphs keep the background's size, with twice as many columns and 20% longer fading trails by default. Background emission defaults to 0.385 for stronger figure contrast. The instance stays stable as its tracked person moves; its texture does not resize with the body. Selection raises the gain of its trails and heads; dormant cells and glyph gaps block the rain behind them. Nearby background rain is softly darkened, while inner-edge glow defaults off. The interior stays hollow between drops. Unselected figures use the environment's luminance rule. Soft edges blend the layers, and glow can spill just outside a selected silhouette.

| Control | Meaning |
| --- | --- |
| `--scene-mode code` | Select the material path without selecting a preset |
| `--material-source noumenon` | Pinned Classic CPU renderer |
| `--material-face mixed` | Classic's 57 selection slots (one blank) mixed with 192 Cyber originals |
| `--material-face cyber` / `classic` | Use only that catalog |
| `--material-mix 0.1` | Probability of selecting the Cyber catalog in the mixed face; independent of HUD glyphs |
| `--code-size 24` | Scene cell size at a 1920-pixel long edge; Classic's 80 cells across the long dimension, or 16-pixel cells at 1280×720. Minimum rendered cell is 2 pixels |
| `--code-speed 1` | Speed multiplier; 0 freezes both rain and symbol changes |
| `--code-density 1` | Below 1 selects a fraction of columns; above 1 packs columns horizontally |
| `--material-subject-density 2` | Multiplies code density inside silhouettes, 0–3; resolved density is capped at 3, without shrinking glyphs |
| `--material-subject-trail 1.2` | Silhouette tail-length multiplier, 1–2; extends the fade behind existing heads without changing glyph size or speed |
| `--material-mapping 1` | Mapping strength, 0–1; 0 makes a flat-grid comparison |
| `--material-structure 0.65` | Local contrast strength, 0–1; 0 retains plain source-luminance shading |
| `--material-foreground 2.1` | Selected-silhouette emission gain in linear light, 0–3 |
| `--material-background 0.385` | Environment and unselected-silhouette emission gain in linear light, 0–3 |
| `--material-edge-glow 0` | Optional selected-figure inner-edge glow, 0–1; off by default. Scales with foreground gain |
| `--material-edge-shade 0.4` | Soft local background dimming around selected figures, 0–1; 0 disables. Other figures retain their shading |
| `--material-glow 0.18` | One glow pass after ownership/occlusion, 0–1 |

When enabled, the inner rim uses a blur radius of 0.12 glyph cells (minimum 0.6 pixels); the exterior shading falls off over a radius of 0.45 cells (minimum 1 pixel). At 720p with default glyph size, these are 1.92 and 7.2 pixels. Edge effects follow `--material-subjects`; `none` disables both. Visible ownership clips the rim and prevents fully hidden figures from creating a halo. The ordinary optical glow can still spill softly past edges.

The table's settings save and load with ordinary visual presets. Source-specific `--material-subjects` choices stay on the conversion command. Explicit flags override built-in or saved values. The scene palette is Matrix green with mint `#A2FFD8` heads; thermal palettes, source tint, `--HUDglyphs`, `--code-style` and `--code-layer` retain their separate meanings.

## Mapping and limits

Room mapping requires converging edges and long, aligned segments that support all four sides of a closed far-wall boundary. Uprights and diagonal branches alone do not qualify. Supported rooms receive separate back-wall, floor, ceiling and opposing-wall mappings in the residual environment. Floors flow along a depth axis; upright surfaces descend. Feature correspondences stabilize those confirmed room planes during small camera movements. Without supported geometry or reliable correspondence, background rain falls straight down in a fixed screen grid. Room evidence is rechecked during the shot. Reports expose `material_mapping_mode`, `material_mapping_modes`, `material_mapping_fallback` and plane confidence; a low-confidence guess is not a reconstructed room.

Silhouette rain always falls vertically in screen coordinates. Its seed depends on the shot and track identity, independently of the background and other people. Subject movement changes the mask, not the glyph grid. Soft masks use front-over ownership with a residual background; lower image contact points approximate visibility and track IDs break ties. Complex depth ordering still depends on mask quality. Alpha weights sum to one within 2e-6. Source-resolution glyphs use mip filtering at distance. Reports include `material_cell_pixels`, `material_subject_mapping` (`independent-screen-vertical-rain`) and `material_subject_density_resolved` so scale, mapping and density can be checked.

## Time and reproducibility

The CPU port samples a fixed 60 Hz clock, with 180 settled-state ticks before output time zero. Trims use **output-relative time**: a trimmed conversion starts a new animation at zero. A PNG samples zero. Speed does not depend on output FPS. Classic's full brightness replacement and constant symbol-age increment permit a closed-form state, so a material seek to T agrees exactly with sequential sampling on the same NumPy backend. There is no clip-length history or per-object material simulation.

Tracking remains sequential. Advanced Python callers can use `renderer.scene_material.checkpoint()` and `restore()` to carry surface state into an adjacent chunk. Checkpoints are in-memory Python data, including NumPy arrays; they are not portable visual preset files. Independent chunks without tracking history agree in material time but may establish different room coordinates. Shot changes clear the surface state; the material clock continues. Geometry retains the previous reduced frame and foreground mask. Up to 64 silhouette instances are cached; evicted instances reconstruct exactly from their seed and media time. Persistent, nonzero track IDs preserve each person's instance across label changes; untracked subjects instead depend on their list order.

## Source and validation

The material follows [Noumenon revision 97739c6](https://github.com/petehottelet/noumenon/tree/97739c649e5e0dce60c4f1ad780359c5524f4b37): Classic, Matrix green, mixed face, 10% original glyphs. It preserves stationary cells, descending illumination, wobbling columns, head/trail separation, the 60 Hz symbol cadence and Classic exposure constants. The packaged source receipt records hashes and complete MIT notices, including Rezmason's renderer and reference artwork. All 192 Cyber contour hashes match that revision.

This is a **CPU behavioral port**, not verified WebGL pixel parity. It replaces half-float feedback and MSDF sampling with float64 closed-form state and contour raster mipmaps, then shades and glows the composed scene in linear light. Different rasterizers can produce different edge pixels. Material determinism tests require exact equality within one backend; projective fixtures use numerical tolerances. The geometric fixture demonstrates mapping, not semantic detection or a reproduced film shot.

For a reproducible eight-second source/flat/surface comparison, use `python -m tools.preview_noumenon outputs/noumenon-check`. It writes actual rendered video, a still and measured timings to a new directory. The gallery builder includes a `look-noumenon` recipe for authorized source footage. No real-time throughput is promised. Conversion reports separate material state generation from mapping/compositing, alongside semantic and export timings.

Add `--selection-comparison` to compare luminance-only shading with the first and third fixture silhouettes highlighted. The middle silhouette keeps luminance shading in both rendered panels.

[Full option reference](options.md#material-source) · [Executable example](examples.md#noumenon-material)
