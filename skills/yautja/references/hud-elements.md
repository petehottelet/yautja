# HUD element reference

Color and opacity apply to every role. Blur and neon use the same registry; `target-flash` shares the target's blur and neon. `--hud-colors` requires `--hud-theme custom`. Omitted color keys use standard colors; omitted intensity, blur and opacity keys inherit their corresponding global controls. Supplying a map replaces a map inherited from a preset. Zero is an explicit value.

The target's optional colored stroke follows its opacity. Filled/stroked geometry (`--target-fill`) is separate from that extra border (`--target-stroke`). Every overlay is hidden by `--no-hud`.

| Element | Blur | Opacity | Neon | Artwork |
| --- | --- | --- | --- | --- |
| `waveform` | yes | yes | yes | Active waveform signal and non-emissive LED housing/idle cells |
| `waveform-axis` | yes | yes | yes | Trace center axis |
| `waveform-ticks` | yes | yes | yes | Trace scale ticks |
| `waveform-glyphs` | yes | yes | yes | Trace endpoint readouts |
| `readout` | yes | yes | yes | Upper-right glyph readout |
| `timecode` | yes | yes | yes | Numeric elapsed clock |
| `callouts` | yes | yes | yes | Subject glyph callout text |
| `leaders` | yes | yes | yes | Callout connector lines |
| `markers` | yes | yes | yes | Callout anchor points |
| `target` | yes | yes | yes | Geometric reticle primary state |
| `target-flash` | shared target | yes | no | Geometric reticle flash state |
| `subject-outline` | yes | yes | yes | All-subject silhouette edges |
| `subject-code` | yes | yes | yes | Rising glyph streams or body-centered light trails |
| `subject-labels` | yes | yes | yes | Overhead glyph titles |
| `subject-carets` | yes | yes | yes | Headward title pointers |
| `analysis-grid` | yes | yes | yes | Search grid and moving XY locator |
| `analysis-text` | yes | yes | yes | Readable scan criteria and descriptions |
| `analysis-outline` | yes | yes | yes | Blinking selected-subject analysis contour |
| `geo-grid` | yes | yes | yes | Spherical/flat grid, rings and pulsing dots |
| `target-motif` | yes | yes | yes | Broken triangle ornaments |
| `target-label` | yes | yes | yes | Readable target caption and cursor |
| `target-outline` | yes | yes | yes | Selected-subject contour |
| `target-weak-spots` | yes | yes | yes | Optional decorative holographic scan patches |
| `analysis-target-fill` | yes | yes | yes | Translucent persistent analysis disk; inactive with `--target-fill stroked` |
| `analysis-target` | yes | yes | yes | Analysis disk ring and XY marks |

The `target-flash` neon entry is not separately accepted: configure `target`. LED backplates and idle cells use waveform opacity/blur/color but never emit light. [Color, blur and opacity example](examples.md#hud-ink) · [Neon example](examples.md#neon).
