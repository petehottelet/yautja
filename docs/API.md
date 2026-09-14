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

## 2.2 looks, levels, and reticle shapes

`--thermal low-detail` replaces the simpler Silhouette presentation; `silhouette` and `semantic` remain aliases. `--thermal very-detailed` preserves resolved source facial and fabric features. All four segmented modes use the same model setup.

`--look-preset thermal-spectrum-reference-v1` applies the frozen Reference 12 recipe. Explicit choices override it in either argument order. `--thermal-levels` opts into unified grading (0 continuous, 2–64 banded); band softness, black/white points, gamma, and scalar softness are separately configurable. Reports include the resolved look and transfer parameters. The experimental `Renderer` supports the same underscored keywords and preset precedence; explicit grading also accepts finite floating-point fields in the 0–255 range. Legacy `render_field` retains its uint8 contract. See [the grading reference](../skills/yautja/references/colors.md#thermal-levels-and-reference-preset).

`--target-shape` selects `triangle`, `triangle-dots`, `crosshair`, `vector-lock`, `square`, `square-dot`, `square-cross`, `square-mil`, or `square-x`. In 2.3.1+, Vector Lock replaces the old iron-sights geometry; `iron-sights` remains an input alias and reports resolve it to `vector-lock`. Reports include the chosen shape. All inherit existing target styling/timing controls; lock dots appear only after acquisition completes. The default triangle geometry is unchanged.

## 2.3 presets

`--look-preset hottropic` names the unchanged reference look; `thermal-spectrum-reference-v1` remains an alias. All existing palette IDs also select Cinematic starter presets. `--palette` still changes only the ramp, and encoder `--preset` retains its meaning.

`--list-presets` returns a JSON catalog without media or inference. `--save-preset PATH --preset-name NAME` exports current visual settings without conversion; `--preset-file PATH` loads schema-1 JSON presets for images or videos. File settings override an optional built-in base; explicit CLI choices override file settings. The schema permits visual options only, with strict JSON types and no source paths, selected figure IDs, actions, or machine settings. Reports add `preset_name`, `preset_kind`, and `preset_file`. [Preset schema, examples, and precedence](../skills/yautja/references/presets.md).

## Figure catalog schema

`--list-figures` writes a versioned catalog and adjacent HTML contact sheet. Pass its path with `--figures` and repeat or comma-separate `--target` IDs on subsequent conversions. See [the selection and effects reference](../skills/yautja/references/targets.md) for flags, bounds, defaults, and examples.

Catalog schema 1 includes `source.name`, `source.sha256`, `start`, `end`, `fps`, and `shots`. Each shot has `id`, `start`, `end`, and `figures`; each figure has `id`, `category`, `confidence`, `first_seen`, `last_seen`, `thumbnail_jpeg`, and `samples`. A sample is `[source_seconds, x0, y0, x1, y1, opacity]`, with normalized coordinates and opacity in 0–1. Times are relative to the first video frame, including `--start`. Interpolation is bounded to consecutive samples within the same shot. IDs represent detected tracks and do not establish real-world identity.

Conversion reports add `targets`, `targets_seen`, `targets_unseen`, `target_frames`, target colors/timing/size, `motion_blur`, `crt_bleed`, `crt_vertical_lines`, `crt_grid`, `crt_crosshatch`, `crt_strength`, `heat_glow`, and `heat_glow_speed`. Requested values also remain in `settings`. `target_flash` is false for still images and when no target is enabled. HUD colors now include `target` and `target-flash`; integrations should accept additional named roles. Invalid IDs, malformed catalogs, or source hashes that differ fail before rendering.

The experimental renderer accepts `targets`, `shot_id`, and `target_static` keyword arguments on `render` and `render_field`. Targets are dictionaries with `id`, normalized `bbox`, and optional `opacity`. Supply consecutive times and shot IDs to animate acquisition and frame persistence; reset the renderer for an unrelated clip. These low-level calls do not validate the external catalog or source file.

Rorschach waveform controls add `wave_style`, `wave_width`, `wave_height`, and `wave_detail` to reports and renderer construction. The default style is `trace`; the other styles are `rorschach`, `rorschach-split`, and `rorschach-hollow`. Effective geometry/detail are null for the trace or HUD off. The existing `waveform` field still describes the signal source (audio, procedural, or off), independently of its visual style.

CRT grid and crosshatch are available in 2.4+. `crt_grid` combines horizontal and vertical lines without duplicating separately enabled directions; `crt_crosshatch` adds two diagonal directions at 45 degrees. Both default to false, apply after HUD composition, use `crt_strength`, and are supported by stills, videos, and saved presets. Existing `scanlines`/`crt_lines` and `crt_vertical_lines` report their individual controls; `crt_grid` reports the combined-grid control.
