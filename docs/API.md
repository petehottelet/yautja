# Integration contract

`geo_grid_details` enables seeded satellite dots that travel outward and back along grid edges, plus seven-sided node rings. `outline_style="holographic"` gives partial contours raster texture and pale cores; `outline_width` is optional (0.5–20 reference pixels, or `None` for the style default). `target_weak_spots` enables fictional yellow scan patches only on selected current silhouettes. Its independent HUD role is `target-weak-spots`. These settings support schema-1 presets, reports and explicit overrides. Grid details share `geo_grid_speed`; holographic contours share `outline_speed`. Stills freeze their motion. Patches are decorative and make no physical assessment.

Grid center fade, width and irregular breaks (`geo_grid_center_fade`, `geo_grid_width`, `geo_grid_breaks`) and triangle animation speed/breaks (`target_motif_speed`, `target_motif_breaks`) are visual preset settings. `code_density` accepts 0–3: existing 0–1 values retain sparse-column behavior; higher values increase stream count at the same glyph size. These remain flat schema-1 settings; animation phase and cached paths are runtime state.

The supported interface is the `yautja` CLI, equivalently the chosen environment's `python -m yautja`, its exit codes (0 success, 1 conversion/runtime failure, 2 invalid arguments, 130 cancellation), and the versioned JSON conversion report. Inspect `--help` for available controls.

`import yautja` exposes `__version__` without loading image or ML libraries. `yautja.runtime` is also safe to import without those dependencies. Installation metadata comes from the installed distribution; contributors should use an editable install.

Python rendering APIs are **experimental**: `yautja.render.Renderer(...).render(PIL_image, seconds, wave=None, subjects=())` returns a new RGB Pillow image. `render_field(uint8_array, seconds, wave=None, subjects=())` accepts an already computed two-dimensional field matching the renderer's height and width. The defaults use Classic luminance mapping. Segmented rendering requires subject masks from a separately configured semantic pipeline.

```python
from PIL import Image
from yautja.render import Renderer

with Image.open('photo.jpg') as source:
    image = source.convert('RGB')
    result = Renderer(*image.size, palette='green-phosphor', hud=False).render(image, 0)
    result.save('restyled.png')
```

This low-level example does not perform the CLI's orientation, metadata, input/output protection or atomic-write checks. Prefer the CLI for end-user conversion. Other helpers, classes and module internals are not a promised stable API merely because tests or repository tools import them.

## persistent scan target

Fremont enables `analysis_target` independently of the readable `analysis` overlay. Both share the same subject selector and `analysis_speed`; no figure catalog is required. `analysis_target_size` is a fixed diameter of 0.1–0.8 times the short frame edge (default 0.36). `analysis_target_response` is 0–3 seconds to travel 95% toward a new stationary focus (default 0.6); zero follows immediately. These additive visual keys save in schema-1 presets and accept explicit overrides in either order.

The reticle persists through search and track loss, uses smooth damped position/velocity, never zooms or flashes, and resets on cuts/backward time. Stills acquire immediately. `analysis-target-fill` (40% native alpha) and `analysis-target` (90% native alpha) accept shared color/opacity/blur/neon maps. `--no-analysis` hides text/grid/outlines while leaving an enabled scan target; `--no-analysis-target` hides the reticle. `--no-hud` hides both. Legacy `target_*` controls and explicit catalog selections remain separate.

Reports add effective `analysis_target`, configured size/response, and `analysis_target_position` (normalized XY, or null when hidden/unrendered). Shared `analysis_phase`/`analysis_track` remain active when either analysis component is enabled. Low-level renderers use the same supplied subjects and `target_static=True` path. [Controls and recipe](../skills/yautja/references/analysis.md).

## geometry and typography

`--stylepreset focus`, `relic`, and `murphy` add shared grid, shimmer, code-layer, target ornament/caption, and readable-font controls. [Options and ranges](../skills/yautja/references/focus.md). The preset schema remains version 1 with additive flat visual keys; local `hud_font_file` paths are excluded. `hud_font` selects a portable bundled font and `hud_glyphs` now accepts `tech`.

The experimental renderer uses `targets=None` to permit automatic segmented targets when `target_mode="auto"`; supplying a list, including an empty list, overrides automatic selection. `target_mode="selected"` remains the default. Maps add `geo-grid`, `target-motif`, and `target-label`. Reports include geometry controls, font family/weight and the runtime custom path when used. Automatic track IDs in `targets_seen` use `auto-<track_id>`; `targets` remains the list of requested catalog IDs.

Fremont now selects `hud_font="orbitron-bold"` and `analysis_outline_width=5` (0.5–12 reference pixels, default 2.4). These are ordinary saved visual settings. Readable font selection also applies to analysis and captions when the glyph set remains Yautja or Cyber. `--no-target-label` clears an inherited caption.

## Fremont analysis

`--stylepreset fremont` combines a detailed red/burgundy source scene with white readable analysis text, a moving XY grid and blinking subject outlines. It requires segmented setup, automatically selects visible subjects, and needs no figure catalog. The JSON/experimental Python keys are `analysis` (bool), `analysis_speed` (0–5), `analysis_blink_rate` (0–4), `analysis_margin` (0.01–0.15), and `scene_highlights` (0–1). All are visual preset settings. The HUD maps add `analysis-grid`, `analysis-text`, and `analysis-outline`.

Descriptions use detector labels and stay in the frame; numeric telemetry is seeded and decorative. Current-frame mask refinement also applies when analysis is enabled. Reports include `analysis_phase`, `analysis_track`, and `analysis_numbers`; `analysis` is false when the HUD is hidden. Low-level Python callers provide `subjects` and use `target_static=True` for a still's held analysis. [Timing, selection, source grading, and controls](../skills/yautja/references/analysis.md).

## source scenes, subject code, and Cyber glyphs

`--stylepreset netrunner` combines source-scene grading, automatic silhouette outlines, upward code, overhead glyph titles and carets, and warm-red neon styling. `--HUDglyphs cyber|yautja` selects the glyph set for all alien HUD text, code, and titles; timecode is unaffected. The JSON/experimental Python keyword is `hud_glyphs`. See [the full controls and recipe](../skills/yautja/references/cyber.md).

Visual keys include `scene_mode`, `scene_tint`, `scene_tint_strength`, `scene_exposure`, `subject_outline`, `subject_code`, `subject_labels`, `subject_head_gap`, `subject_title_gap`, `subject_caret_scale`, `code_style`, `code_size`, `code_speed`, `code_density`, `hud_glyphs`, and `neon_core_whiten`. They participate in preset save/load, explicit override precedence, and conversion reports. `code_style` is `glyphs` by default; `light` draws continuous rising filaments centered on the body core using pose joints or a mask fallback. Relic selects `light`. The per-element styling maps add `subject-outline`, `subject-code`, `subject-labels`, and `subject-carets`. Their opacity, blur, color, and neon intensity are independently configurable; `--no-hud` hides all four.

Subject outlines enable current-frame SAM contour refinement between detections. The semantic report adds `mask_refresh` (`frame` or `flow`) and `mask_refinement_frames`. The `wave_style` enum additionally accepts `digital-blocks`, `digital-shards`, and `digital-circuit`; they share non-trace waveform dimensions and styling controls. In 2.7.0, `digital-circuit` draws one full-height stack of rounded horizontal vocoder bars containing vertical LED segments, with a pronounced active/idle contrast: bright active segments expand with audio, while dim inactive segments remain visible even during silence. The separate dark casing and inactive segments follow waveform opacity and blur without producing neon emission; the gallery uses `wave_width=0.09` and `wave_height=1`. Netrunner uses 30/20 reference pixels of head/title clearance (half the 2.6.1 gaps), 95% code density, thicker carets, and thinner outlines; annotations crop independently at frame edges.

In `scene_mode='source'`, call `Renderer.render` with an RGB source frame at the renderer's dimensions. `render_field` rejects source mode because a scalar heat field cannot reconstruct source colors. Source mode uses tint/exposure rather than the thermal palette/transfer; display texture remains available. Experimental Python callers supply subject masks to activate overlays. The CLI enforces segmented-mode setup for subject overlays and reuses its tracked masks without requiring a figure catalog. `Renderer` preset configuration translates the CLI preset's `timecode` setting to its Python `show_timecode` keyword.

## looks, levels, and reticle shapes

`--thermal low-detail` replaces the simpler Silhouette presentation; `silhouette` and `semantic` remain aliases. `--thermal very-detailed` preserves resolved source facial and fabric features. All four segmented modes use the same model setup.

`--stylepreset yautja` applies the frozen Yautja recipe. Explicit choices override it in either argument order. `--thermal-levels` opts into unified grading (0 continuous, 2–64 banded); band softness, black/white points, gamma, and scalar softness are separately configurable. Reports include the resolved look and transfer parameters. The experimental `Renderer` supports the same grading keywords and preset precedence; explicit grading also accepts finite floating-point fields in the 0–255 range. Legacy `render_field` retains its uint8 contract. See [the grading reference](../skills/yautja/references/colors.md#thermal-levels-and-reference-preset).

`--target-shape` selects `triangle`, `triangle-dots`, `crosshair`, `hollow-cross`, `square`, `round-dot`, `square-cross`, `square-mil`, `square-x`, `hexagon`, or `frame-box`. `round-dot` provides a circular outline with four evenly spaced gaps and three center dots arranged in a triangle, appearing on lock. Hollow Cross replaces Vector Lock with four thick L-shaped bands and an open center and arm ends. `vector-lock` and `iron-sights` remain input aliases and reports resolve them to `hollow-cross`. Reports include the chosen shape. All inherit existing target styling/timing controls; lock dots appear only after acquisition completes. `crosshair`, `hollow-cross`, `round-dot`, `square`, `square-cross`, `square-mil`, and `square-x` use compact locked geometry. Acquisition contracts toward the final shape; `--target-scale` multiplies this final size. The default triangle geometry is unchanged.

## presets

`--stylepreset yautja` selects Yautja. All existing palette IDs also select Cinematic starter presets. `--palette` still changes only the ramp, and encoder `--preset` retains its meaning. The CLI selector is `--stylepreset`. The Python keyword and JSON report key remain `look_preset`, for example `Renderer(width, height, look_preset="yautja")`.

`--list-presets` returns a JSON catalog without media or inference. `--save-preset PATH --preset-name NAME` exports current visual settings without conversion; `--preset-file PATH` loads schema-1 JSON presets for images or videos. File settings override an optional built-in base; explicit CLI choices override file settings. The schema permits visual options only, with strict JSON types and no source paths, selected figure IDs, actions, or machine settings. Reports add `preset_name`, `preset_kind`, and `preset_file`. [Preset schema, examples, and precedence](../skills/yautja/references/presets.md).

## Neon illumination

Renderer keywords include `neon=False`, `neon_intensity=1.0`, `neon_spread=0.6`, `neon_flicker=0.0`, and `neon_elements=None`. The last value is a comma-separated `element=intensity` string. Intensity and spread accept finite 0–2 values; flicker accepts 0–1. Per-element intensity zero disables its entire neon treatment; target applies to both flash states. Invalid tuning fails even while neon is off. Geometry and default output are unchanged when neon is disabled.

Requested values are preserved in conversion `settings`. Top-level reports contain effective `neon`, `neon_intensity`, `neon_spread`, `neon_flicker`, and the resolved per-element map as both `neon_elements` and `neon_intensities`. Effective values are false/zero when neon or HUD is disabled. `neon_flicker_seed_stream` is `sha256(seed:neon-flicker)` when enabled, otherwise null. Stills evaluate time zero; all HUD layers share one deterministic flicker gain per frame. No new runtime dependencies are required.

All five options are portable visual preset keys. [Controls, interactions, and examples](../skills/yautja/references/targets.md#neon-hud).

## Figure catalog schema

`--list-figures` writes a versioned catalog and adjacent HTML contact sheet. Pass its path with `--figures` and repeat or comma-separate `--target` IDs on subsequent conversions. See [the selection and effects reference](../skills/yautja/references/targets.md) for flags, bounds, defaults, and examples.

Catalog schema 1 includes `source.name`, `source.sha256`, `start`, `end`, `fps`, and `shots`. Each shot has `id`, `start`, `end`, and `figures`; each figure has `id`, `category`, `confidence`, `first_seen`, `last_seen`, `thumbnail_jpeg`, and `samples`. A sample is `[source_seconds, x0, y0, x1, y1, opacity]`, with normalized coordinates and opacity in 0–1. Times are relative to the first video frame, including `--start`. Interpolation is bounded to consecutive samples within the same shot. IDs represent detected tracks and do not establish real-world identity.

Conversion reports add `targets`, `targets_seen`, `targets_unseen`, `target_frames`, target colors/timing/size, `motion_blur`, `crt_bleed`, `crt_vertical_lines`, `crt_grid`, `crt_crosshatch`, `crt_strength`, `heat_glow`, and `heat_glow_speed`. Requested values also remain in `settings`. `target_flash` is false for still images and when no target is enabled. HUD colors now include `target` and `target-flash`; integrations should accept additional named roles. Invalid IDs, malformed catalogs, or source hashes that differ fail before rendering.

The experimental renderer accepts `targets`, `shot_id`, and `target_static` keyword arguments on `render` and `render_field`. Targets are dictionaries with `id`, normalized `bbox`, and optional `opacity`. Supply consecutive times and shot IDs to animate acquisition and frame persistence; reset the renderer for an unrelated clip. These low-level calls do not validate the external catalog or source file.

Rorschach waveform controls add `wave_style`, `wave_width`, `wave_height`, and `wave_detail` to reports and renderer construction. The default style is `trace`; the other styles are `rorschach`, `rorschach-split`, and `rorschach-hollow`. Effective geometry/detail are null for the trace or HUD off. The existing `waveform` field still describes the signal source (audio, procedural, or off), independently of its visual style.

CRT grid and crosshatch are available. `crt_grid` combines horizontal and vertical lines without duplicating separately enabled directions; `crt_crosshatch` adds two diagonal directions at 45 degrees. Both default to false, apply after HUD composition, use `crt_strength`, and are supported by stills, videos, and saved presets. Existing `scanlines`/`crt_lines` and `crt_vertical_lines` report their individual controls; `crt_grid` reports the combined-grid control.

## Preset naming and persistent targets

`yautja` is the complete Cinematic recipe with the former HotTropic colors, red HUD, cyan annotations, and CRT lines. `costa-rica` preserves the original ramp. `hottropic` and `hot-tropic` normalize to `yautja`. Plain CLI use remains Classic with the new Yautja palette and CRT lines; `--no-crt-lines` turns them off.

The renderer and schema-1 visual presets accept `geo_grid_projection` (`flat` or `sphere`), `target_mode` (`selected`, `auto`, or `cycle`), `target_motion` (`acquire` or `persistent`), `target_hold`, `target_response`, `target_fill` (`auto`, `filled`, or `stroked`), `target_outline`, `target_label_scale`, and `target_cursor`. Read the [defaults and ranges](../skills/yautja/references/focus.md). `target-outline` is an independent HUD color/opacity/blur/neon role. Every target shape supports filled and stroked treatment. Filled marks and dots are solid; enclosed reticles add translucent interiors. Stroked open paths outline their thick bands, retaining end caps and gaps, and stroked lock dots are rings. Triangle lock-dot radii are 0.0924 target-radius units (12% smaller), with unchanged centers.

Persistent movement keeps one constant-size reticle. Automatic empty scenes sweep in search; explicit empty target lists suppress targeting. Catalogs supply the candidate pool, while cycle mode and persistent motion choose one candidate. Selection and motion reset on cuts/backward seeks. Current masks drive outlines without spatial smoothing. Runtime selection and spring state are never exported as preset settings. The decorated `hexagon` and center-crossing `frame-box` use the same common target controls.

## Shared display and stabilization controls

`Renderer(..., wave_display=None, wave_backlight=.2)` resolves LED display for digital-circuit and plain for other wave styles. Explicit `"led"` works for all seven styles; `"plain"` removes the device. Idle housing/cells use waveform color, blur and opacity without emitting light. `outline_shine=.55` controls holographic band brightness, including optional weak-spot textures. `geo_grid_rotation=0.` is independent angular drift in degrees per second. These four options are portable visual settings and appear in conversion reports.

`SemanticTracker(..., mask_stability=.18, mask_min_region=.02)` stabilizes flow-aligned overlays. Each returned `Subject` retains a probability `mask` and may carry a `binary_mask` for overlays. Runtime controls never enter visual presets. Both zero restores the former refinement gate and raw contour behavior. Model weights are still loaded only through the optional semantic runtime.

[Canonical option reference](../skills/yautja/references/options.md) · [Runnable examples](../skills/yautja/references/examples.md).
