# Fremont and readable analysis

Requires Yautja 2.7.0+ and the segmented runtime. Run:

```bash
yautja "clip.mov" "fremont.mp4" --stylepreset fremont
```

Fremont preserves photographic detail under a red/burgundy source grade, with pale highlights, white readable Michroma text, a moving XY grid, and a white silhouette outline. It hides the ordinary waveform, alien readout, and overhead glyph labels. Numbers are seeded decorative telemetry, not measurements. Descriptions use detected category names; the renderer does not identify a person's identity, physical measurements, or a vehicle's make/model.

No figure catalog is required. The scanner acquires the largest visible subject first, holds that track through analysis, then visits the next visible subject in size order. It searches for 0.9 seconds, acquires for 0.5, analyzes for 2.4, and holds for 2.2. It restarts on a shot cut or track loss. Stills display a held analysis immediately; with no subjects they display search mode.

People and animals use the standard detection classes. Include vehicles explicitly when appropriate:

```bash
yautja "street.mov" "street-fremont.mp4" --stylepreset fremont --warm-objects "person,car,motorcycle,bicycle,bus,truck,dog"
```

| Option | Default | Behavior |
| --- | --- | --- |
| `--analysis` / `--no-analysis` | Off; on in Fremont | Adds/removes the readable scan HUD; requires segmented mode when HUD is visible |
| `--analysis-speed` | `1` | 0–5; six-second cycle at 1; higher values shorten the sequence; 0 freezes search |
| `--analysis-blink-rate` | `2` | 0–4 blinks/second during analysis; 0 keeps the outline steady |
| `--analysis-margin` | `0.035` | 0.01–0.15 of the short frame edge; safe margin for descriptions and readouts |
| `--scene-highlights` | `0`; Fremont `0.95` | 0–1; restores neutral highlights above a source tint while retaining midtone color |

Fremont's source settings are `--scene-mode source --scene-tint "#E51A24" --scene-tint-strength 1 --scene-exposure 1.25 --scene-highlights 0.95`. Thermal palette/detail settings do not recolor the source image in this mode. Texture effects remain available.

All five visual options save/load in JSON presets and use the existing explicit-option precedence. The new element names are `analysis-grid`, `analysis-text`, and `analysis-outline`. Each accepts the ordinary HUD color, opacity, blur, and neon overrides. For example:

```bash
yautja "clip.mov" "quiet-analysis.mp4" --stylepreset fremont --analysis-blink-rate 0 --hud-opacity-elements "analysis-grid=0.4,analysis-text=1,analysis-outline=1,waveform=0,waveform-axis=0,waveform-ticks=0,waveform-glyphs=0,readout=0"
```

An explicit element-map option replaces the preset's map; specify any hidden elements you want to keep hidden. `--no-hud` hides every overlay, including scan outlines, while preserving the source grade. `--no-analysis` hides just the analysis HUD. Adding `--analysis` to another preset composes it with that preset's existing overlays.

Descriptions reposition and wrap to stay inside the safe area, scaling down on small frames. Numeric rows are revealed during analysis rather than randomized every frame. Outlines use current-frame mask refinement, with no spatial lag smoothing; detection and occlusion quality depend on the footage. The report includes the configured scan controls, effective `analysis` enablement, `analysis_phase`, `analysis_track`, and an `analysis_numbers` description.

The bundled Michroma font is unmodified and retains its [SIL Open Font License](https://github.com/google/fonts/blob/8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5/ofl/michroma/OFL.txt). It is included with its license in the application wheel and source distribution.
