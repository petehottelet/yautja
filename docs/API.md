# Integration contract

The supported 2.x interface is the `yautja` CLI, equivalently the chosen environment's `python -m yautja`, its exit codes (0 success, 1 conversion/runtime failure, 2 invalid arguments, 130 cancellation), and the versioned JSON conversion report. Existing flags retain their meanings within the major version; new flags can require a newer minor version. Inspect `--help` and the installed `__version__` before using newly added controls.

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

## 2.6 source scenes, subject code, and Cyber glyphs

`--stylepreset ghost-signal` combines source-scene grading, automatic silhouette outlines, upward code, overhead glyph titles and carets, and warm-red neon styling. `--HUDglyphs cyber|yautja` selects the glyph set for all alien HUD text, code, and titles; timecode is unaffected. The JSON/experimental Python keyword is `hud_glyphs`. See [the full controls and recipe](../skills/yautja/references/cyber.md).

New visual keys are `scene_mode`, `scene_tint`, `scene_tint_strength`, `scene_exposure`, `subject_outline`, `subject_code`, `subject_labels`, `subject_head_gap`, `subject_title_gap`, `subject_caret_scale`, `code_size`, `code_speed`, `code_density`, `hud_glyphs`, and `neon_core_whiten`. They participate in preset save/load, explicit override precedence, and conversion reports. The per-element styling maps add `subject-outline`, `subject-code`, `subject-labels`, and `subject-carets`. Their opacity, blur, color, and neon intensity are independently configurable; `--no-hud` hides all four.

Subject outlines enable current-frame SAM contour refinement between detections. The semantic report adds `mask_refresh` (`frame` or `flow`) and `mask_refinement_frames`. The `wave_style` enum additionally accepts `digital-blocks`, `digital-shards`, and `digital-circuit`; they share non-trace waveform dimensions and styling controls.

In `scene_mode='source'`, call `Renderer.render` with an RGB source frame at the renderer's dimensions. `render_field` rejects source mode because a scalar heat field cannot reconstruct source colors. Source mode uses tint/exposure rather than the thermal palette/transfer; display texture remains available. Experimental Python callers supply subject masks to activate overlays. The CLI enforces segmented-mode setup for subject overlays and reuses its tracked masks without requiring a figure catalog. `Renderer` preset configuration translates the CLI preset's `timecode` setting to its Python `show_timecode` keyword.

## 2.2 looks, levels, and reticle shapes

`--thermal low-detail` replaces the simpler Silhouette presentation; `silhouette` and `semantic` remain aliases. `--thermal very-detailed` preserves resolved source facial and fabric features. All four segmented modes use the same model setup.

`--stylepreset hottropic` applies the frozen HotTropic recipe. Explicit choices override it in either argument order. `--thermal-levels` opts into unified grading (0 continuous, 2–64 banded); band softness, black/white points, gamma, and scalar softness are separately configurable. Reports include the resolved look and transfer parameters. The experimental `Renderer` supports the same grading keywords and preset precedence; explicit grading also accepts finite floating-point fields in the 0–255 range. Legacy `render_field` retains its uint8 contract. See [the grading reference](../skills/yautja/references/colors.md#thermal-levels-and-reference-preset).

`--target-shape` selects `triangle`, `triangle-dots`, `crosshair`, `hollow-cross`, `square`, `round-dot`, `square-cross`, `square-mil`, or `square-x`. `round-dot` provides a circular outline with four evenly spaced gaps (2.5.6+) and three center dots arranged in a triangle, appearing on lock (2.5.8+). In 2.4.2+, Hollow Cross replaces Vector Lock with four thick L-shaped bands and an open center and arm ends. `vector-lock` and `iron-sights` remain input aliases and reports resolve them to `hollow-cross`. Reports include the chosen shape. All inherit existing target styling/timing controls; lock dots appear only after acquisition completes. In 2.5.7+, `crosshair`, `hollow-cross`, `round-dot`, `square`, `square-cross`, `square-mil`, and `square-x` lock at 85% of their previous size. Their acquisition still starts at the same size and contracts to the smaller final shape; `--target-scale` multiplies this final size. The default triangle geometry is unchanged.

## 2.3 presets

`--stylepreset hottropic` selects HotTropic. All existing palette IDs also select Cinematic starter presets. `--palette` still changes only the ramp, and encoder `--preset` retains its meaning. The CLI selector is `--stylepreset` in 2.5.2+. The Python keyword and JSON report key remain `look_preset`, for example `Renderer(width, height, look_preset="hottropic")`.

`--list-presets` returns a JSON catalog without media or inference. `--save-preset PATH --preset-name NAME` exports current visual settings without conversion; `--preset-file PATH` loads schema-1 JSON presets for images or videos. File settings override an optional built-in base; explicit CLI choices override file settings. The schema permits visual options only, with strict JSON types and no source paths, selected figure IDs, actions, or machine settings. Reports add `preset_name`, `preset_kind`, and `preset_file`. [Preset schema, examples, and precedence](../skills/yautja/references/presets.md).

## Neon illumination

Yautja 2.5 adds renderer keywords `neon=False`, `neon_intensity=1.0`, `neon_spread=0.6`, `neon_flicker=0.0`, and `neon_elements=None`. The last value is a comma-separated `element=intensity` string. Intensity and spread accept finite 0–2 values; flicker accepts 0–1. Per-element intensity zero disables its entire neon treatment; target applies to both flash states. Invalid tuning fails even while neon is off. Geometry and default output are unchanged when neon is disabled.

Requested values are preserved in conversion `settings`. Top-level reports contain effective `neon`, `neon_intensity`, `neon_spread`, `neon_flicker`, and the resolved per-element map as both `neon_elements` and `neon_intensities`. Effective values are false/zero when neon or HUD is disabled. `neon_flicker_seed_stream` is `sha256(seed:neon-flicker)` when enabled, otherwise null. Stills evaluate time zero; all HUD layers share one deterministic flicker gain per frame. No new runtime dependencies are required.

All five options are portable visual preset keys. [Controls, interactions, and examples](../skills/yautja/references/targets.md#neon-hud).

## Figure catalog schema

`--list-figures` writes a versioned catalog and adjacent HTML contact sheet. Pass its path with `--figures` and repeat or comma-separate `--target` IDs on subsequent conversions. See [the selection and effects reference](../skills/yautja/references/targets.md) for flags, bounds, defaults, and examples.

Catalog schema 1 includes `source.name`, `source.sha256`, `start`, `end`, `fps`, and `shots`. Each shot has `id`, `start`, `end`, and `figures`; each figure has `id`, `category`, `confidence`, `first_seen`, `last_seen`, `thumbnail_jpeg`, and `samples`. A sample is `[source_seconds, x0, y0, x1, y1, opacity]`, with normalized coordinates and opacity in 0–1. Times are relative to the first video frame, including `--start`. Interpolation is bounded to consecutive samples within the same shot. IDs represent detected tracks and do not establish real-world identity.

Conversion reports add `targets`, `targets_seen`, `targets_unseen`, `target_frames`, target colors/timing/size, `motion_blur`, `crt_bleed`, `crt_vertical_lines`, `crt_grid`, `crt_crosshatch`, `crt_strength`, `heat_glow`, and `heat_glow_speed`. Requested values also remain in `settings`. `target_flash` is false for still images and when no target is enabled. HUD colors now include `target` and `target-flash`; integrations should accept additional named roles. Invalid IDs, malformed catalogs, or source hashes that differ fail before rendering.

The experimental renderer accepts `targets`, `shot_id`, and `target_static` keyword arguments on `render` and `render_field`. Targets are dictionaries with `id`, normalized `bbox`, and optional `opacity`. Supply consecutive times and shot IDs to animate acquisition and frame persistence; reset the renderer for an unrelated clip. These low-level calls do not validate the external catalog or source file.

Rorschach waveform controls add `wave_style`, `wave_width`, `wave_height`, and `wave_detail` to reports and renderer construction. The default style is `trace`; the other styles are `rorschach`, `rorschach-split`, and `rorschach-hollow`. Effective geometry/detail are null for the trace or HUD off. The existing `waveform` field still describes the signal source (audio, procedural, or off), independently of its visual style.

CRT grid and crosshatch are available in 2.4+. `crt_grid` combines horizontal and vertical lines without duplicating separately enabled directions; `crt_crosshatch` adds two diagonal directions at 45 degrees. Both default to false, apply after HUD composition, use `crt_strength`, and are supported by stills, videos, and saved presets. Existing `scanlines`/`crt_lines` and `crt_vertical_lines` report their individual controls; `crt_grid` reports the combined-grid control.
