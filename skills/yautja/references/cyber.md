# Cyber glyphs and Netrunner

Requires Yautja 2.6.2+. **Netrunner** is a complete style preset. **Cyber** is a selectable glyph set within that preset. The controls also work independently with other presets.

```bash
yautja "clip.mov" "signal.mp4" --stylepreset netrunner
yautja "photo.jpg" "signal.png" --stylepreset netrunner
yautja "clip.mov" "thermal-cyber.mp4" --stylepreset yautja --HUDglyphs cyber
```

Netrunner uses the normal [segmented runtime and cached models](semantic.md). The default detection categories include people and common animals. No figure catalog is needed for automatic outlines, code, or titles. A selected target reticle still uses the separate figure-selection workflow.

## Glyph sets

`--HUDglyphs cyber` selects 192 generated vector glyphs. `--HUDglyphs yautja` selects the existing Yautja glyphs. The spelling of the flag is case-sensitive. The selected set is used throughout alien HUD readouts, waveform decorations, side callouts, overhead subject titles, and silhouette code. Human-readable timecode remains numeric.

Titles are decorative glyph sequences derived from the seed and track ID. They do not identify people, translate language, or report personal information. Titles retain their sequence while the track exists. Rain illuminates a fixed glyph grid: bright heads travel upward at varied speeds, leaving fading tails below them. Characters change occasionally on independent, seeded cycles. Animation uses absolute time rather than accumulated frame brightness.

## Complete preset recipe

Netrunner uses source scene mode with tint `#548568`, tint strength `0.8`, exposure `0.65`, Low Detail segmentation, and Cyber glyphs. HUD ink is warm red `#FD5550`, subject titles are cyan `#41E8EF`, and carets are yellow `#FFC442`. All three subject overlays and timecode are on; side callouts and sensor textures are off. Code size is `22`, speed `1`, and density `0.95`. Caret size is `1.35` (35% larger); head clearance is `30` and title clearance is `20` reference pixels, half the 2.6.1 gaps. Titles are centered by their visible artwork above the caret, maintaining the same vertical spacing. The caret stroke is twice as thick as in 2.6.0, while the red silhouette contour is half as thick. Clearance is measured from the visible strokes. Titles and carets crop independently at screen edges; they are never shifted inward or hidden as a group to fit the frame.

Neon intensity is `0.35`, spread `0.3`, and core whitening `0`, which preserves the red ink. Element intensity overrides are `subject-code=0.2,subject-outline=0.3,subject-labels=0.25,subject-carets=0.2`. Opacity overrides are `subject-code=0.8,waveform-axis=0.35,waveform-ticks=0.4`. Other controls use their standard defaults. `yautja --list-presets` returns the machine-readable recipe.

## Individual controls

| Option | Values | Purpose |
| --- | --- | --- |
| `--scene-mode` | `thermal` (default), `source` | Choose thermal recoloring or a graded source scene |
| `--scene-tint` | RGB hex; default `#548568` | Source-scene tint color |
| `--scene-tint-strength` | 0–1; default 0.8 | Blend between original colors and tinted luminance |
| `--scene-exposure` | 0.1–2; default 0.65 | Source-scene brightness multiplier |
| `--subject-outline` / `--no-subject-outline` | On/off | Outline outer silhouette contours, omitting enclosed interior holes |
| `--subject-code` / `--no-subject-code` | On/off | Clip rising code to detected masks |
| `--subject-labels` / `--no-subject-labels` | On/off | Overhead glyph titles and downward carets |
| `--subject-head-gap` | 0–120; default 24, Netrunner 60 | Head-to-caret clearance in reference pixels |
| `--subject-title-gap` | 0–80; default 18, Netrunner 40 | Caret-to-title clearance in reference pixels |
| `--subject-caret-scale` | 0.25–3; default 1 | Caret size; Netrunner uses 1.35 |
| `--code-size` | 8–80; default 22 | Glyph size in reference pixels at a 1080px short edge |
| `--code-speed` | 0–5; default 1 | Upward speed; 0 freezes the code |
| `--code-density` | 0–1; default 0.65, Netrunner 0.95 | Fraction of active columns; 0 hides code |
| `--neon-core-whiten` | 0–1; default 1 | 0 keeps colored cores; 1 uses the standard pale core |

Outside Netrunner, the three subject overlays default off. Each requires a segmented thermal mode in the CLI. `--scene-mode source` changes the scene renderer: palettes, thermal detail/levels, and heat glow do not recolor that source scene. Grain, pixelation, CRT, VHS, and motion blur remain usable. Switch back with `--scene-mode thermal` to use thermal colors again.

`--scene-mode source --scene-tint-strength 0 --scene-exposure 1 --no-hud` preserves source RGB values before any separately enabled display effects. Stills render the code at time zero; frozen code remains clipped to the current tracked mask in video.

## Independent HUD styling

Four additional element names work with existing color, blur, opacity, and neon controls: `subject-outline`, `subject-code`, `subject-labels`, and `subject-carets`. The last two share the subject-labels visibility flag, but have independent styling. `--no-hud` suppresses all of them.

```bash
yautja "clip.mov" "soft-signal.mp4" --stylepreset netrunner --hud-blur-elements "subject-outline=2,subject-code=1" --hud-opacity-elements "subject-code=0.5,subject-labels=0.9"
yautja --stylepreset netrunner --code-speed 1.5 --save-preset "my-signal.json" --preset-name "My Signal"
yautja "clip.mov" "my-signal.mp4" --preset-file "my-signal.json"
```

Overrides are applied in either argument order and are saved in the usual visual preset format. The JSON glyph setting is `"hud_glyphs": "cyber"` or `"yautja"`.

## Tracking and rendering limits

When subject outlines are enabled, SAM refreshes contours on each frame between full detections, using optical flow to predict prompt positions. This reduces accumulated mask drift at the cost of additional inference. Masks that are empty or jump away from the tracked subject are rejected. Reports expose `semantic.mask_refresh` and `semantic.mask_refinement_frames`. Regular thermal renders retain the earlier flow-based behavior when subject outlines are off.

Masks, titles, and carets follow the same detected people/animal tracks. Smoothed anchors reduce label jitter; shot changes and missing tracks clear prior positions. People or animals missed by detection receive no invented outline. Overlapping subjects, small subjects, carried objects, and partial occlusion can still produce imperfect boundaries or new track IDs. Glyph ink is clipped to the mask, while blur and neon halos can extend beyond it.

The vector catalog is bundled with the package, including its MIT notice. No font download, browser, or extra glyph-rendering dependency is needed. The existing base dependencies rasterize its paths with preserved gaps, closed counters, and detached marks.
