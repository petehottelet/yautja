<p align="center">
  <img src="https://raw.githubusercontent.com/petehottelet/yautja/main/assets/wordmark.svg?v=2.10.0" alt="Yautja" width="520">
</p>

<p align="center">
  <a href="https://pypi.org/project/yautja/"><img alt="Install Yautja from PyPI" src="https://img.shields.io/pypi/v/yautja?color=3776ab&amp;label=PyPI"></a>
  <a href="https://github.com/petehottelet/yautja/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/petehottelet/yautja?display_name=tag&sort=semver&color=2da44e&label=release"></a>
  <a href="https://github.com/petehottelet/yautja/blob/main/LICENSE"><img alt="Code license: MIT" src="https://img.shields.io/badge/code%20license-MIT-green.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-blue.svg">
  <img alt="Claude + Codex" src="https://img.shields.io/badge/Claude%20%2B%20Codex-agent%20ready-555555.svg">
  <a href="https://github.com/petehottelet/yautja/blob/main/skills/yautja/SKILL.md"><img alt="Agent Skill (SKILL.md)" src="https://img.shields.io/badge/Agent%20Skill-SKILL.md-orange.svg"></a>
  <a href="#install-the-agent-skill"><img alt="Install with skills.sh" src="https://img.shields.io/badge/skills.sh-install-111111.svg"></a>
  <a href="https://github.com/petehottelet/yautja/actions/workflows/ci.yml?query=branch%3Amain"><img alt="CI on main" src="https://github.com/petehottelet/yautja/actions/workflows/ci.yml/badge.svg?branch=main&amp;event=push"></a>
  <a href="https://yautja.ai"><img alt="Website: yautja.ai" src="https://img.shields.io/badge/web-yautja.ai-ef4444.svg"></a>
</p>

# Yautja is sci-fi segmentation, re-skinning, and annotation for video and images. 

Yautja is a **local Python tool for sci-fi-styled image segmentation, re-skinning, and annotation** with thermal-imaging-style output.

**For entertainment purposes only.** Colors assigned during re-skinning are purely algorithmically generated, with some randomness. They do not represent measured temperatures. HUD elements are for entertainment/costume/cosplay purposes only. 

Re-skin local images and video frames with cold blues, warm silhouettes, and alien HUD glyphs. Videos add an audio-reactive waveform. Install the converter from PyPI and use it directly, or add the optional **agent skill for Claude and OpenAI Codex**. Videos use FFmpeg. [yautja.ai](https://yautja.ai).

[![Yautja: soft thermal bands, red HUD, cyan annotations and CRT lines](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/hero.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/look-yautja.gif?v=2.10.0)

| Fremont | Murphy |
| --- | --- |
| [![Fremont: burgundy scene and persistent scan target](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/look-fremont.gif?v=2.12.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/look-fremont.gif?v=2.12.0) | [![Murphy: green targeting and thinking cursor](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/look-murphy.gif?v=2.12.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/look-murphy.gif?v=2.12.0) |
| Netrunner | Focus |
| [![Netrunner: red outlines and upward Cyber code](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/look-netrunner.gif?v=2.12.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/look-netrunner.gif?v=2.12.0) | [![Focus: purple geodesic sphere and one moving hexagon](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/look-focus.gif?v=2.12.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/look-focus.gif?v=2.12.0) |

The large hero uses **`--stylepreset yautja`**: Cinematic detail, 12 soft thermal levels, red HUD, cyan annotations, and CRT lines. The smaller previews show four alternative styles. The waveform follows the original source audio. [View a still frame](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/poster.png?v=2.10.0).

<!-- media: {"file":"assets/examples/hero.gif","width":960,"height":540} -->
<!-- media: {"file":"assets/examples/look-focus.gif","width":480,"height":270,"duration_ms":4000} -->
The hero is 960×540. The four compact preset previews are 480×270, running at normal source speed, 24 fps for four seconds. Click a preview for the larger version.

**Start here:** [Install and convert](#quick-start) · [Choose a look](#choose-a-look) · [Customize](#customize) · [Save a style](#save-load-and-share) · [Export controls](#control-the-output) · [Troubleshooting](#troubleshooting) · [Agent skill](#install-the-agent-skill) · [Every option](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/options.md)

<a id="still-images"></a>
## Quick start

**Install Yautja from [PyPI](https://pypi.org/project/yautja/).** Requires Python 3.10+. Use an activated virtual environment; [Windows and macOS/Linux setup](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/runtime.md#virtual-environment-setup) shows how to create one.

**Classic — lightweight installation.** The base package provides the Classic effect. The segmented gallery looks use the extra setup immediately below. Try Classic on your own JPEG or PNG; images need no FFmpeg or model downloads.

<!-- quick-start-classic: exercised by tools.verify_install -->
```bash
pip install yautja
yautja --version
yautja --doctor --media image
yautja "photo.jpg" "photo-yautja.png"
```

<a id="segmentation-setup"></a>
### Segmented looks

**For the gallery's Low Detail, Cinematic, Detailed, and Very Detailed looks**, install the `semantic` extra and explicitly download the models once. You can install this extra directly without installing the base command first. Use the same environment's Python throughout:

```bash
python -m pip install "yautja[semantic]"
python -m yautja --download-models
python -m yautja --doctor --media image --thermal cinematic
python -m yautja "photo.jpg" "photo-cinematic.png" --thermal cinematic --verbose
```

The pinned models use roughly 1.2 GB and are reused from the local cache; ordinary conversions do not download them. A color palette works with Classic. Palette starter presets and Yautja select Cinematic; Netrunner, Focus, Relic, Murphy, and Fremont use segmented outlines and need the same setup. Thermal presets can also use `--thermal classic`; subject outlines, code, titles, and analysis require a segmented mode. [Segmentation and GPU setup](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/semantic.md).

### Video

Install [FFmpeg](https://ffmpeg.org/download.html) and ffprobe separately and put them on PATH. With the base package, convert a video using Classic:

```bash
yautja --doctor
yautja "input.mov" "output-yautja.mp4"
```

After segmented setup, try a five-second Cinematic preview:

```bash
python -m yautja --doctor --thermal cinematic
python -m yautja "clip.mov" "clip-preview.mp4" --thermal cinematic --verbose --timecode --duration 5
```

Remove `--duration 5` and choose a new output filename for the full video. Sound is retained unless `--mute` is used; `--timecode` adds elapsed time beneath the alien readout. Silent videos use a generated waveform. Existing files require explicit `--overwrite`.

**Other installation options:** `pipx install yautja` (or `pipx install "yautja[semantic]"`) provides an isolated CLI. Existing compatible pipx installations can be reused. Source checkouts and offline release wheels are covered in the [runtime guide](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/runtime.md). For upgrades, use the [original environment](#local-skill-bundles-and-updates).

JPEG and PNG inputs save directly to PNG, retaining aspect ratio and applying EXIF orientation. Stills freeze animated HUD features in a settled state. Videos export H.264/AAC MP4; the source remains untouched.

To reproduce the hero after segmented setup:

<!-- example: {"id": "readme-hero", "tier": "models", "checks": {"look_preset": "yautja"}} -->
```bash
yautja "clip.mov" "hero.mp4" --stylepreset yautja --verbose --timecode --duration 4
```

<a id="style-presets-and-individual-options"></a>
<a id="when-to-use-yautja"></a>
## Choose a look

Choose a **complete preset** for a coordinated scene and HUD; a **palette starter** for Cinematic with named colors; `--palette` to change only colors; or `--thermal` to choose the image treatment independently. The no-flag command is lightweight Classic with Yautja colors. `--stylepreset yautja` adds the complete Cinematic recipe.

| Complete preset | Scene | HUD and targeting |
| --- | --- | --- |
| `yautja` | Soft thermal bands and dark scenery | Red HUD, cyan callouts, CRT lines |
| `fremont` | Detailed red/burgundy source | Bold white analysis, persistent translucent scan disk |
| `murphy` | Source detail with a slight blue cast | Glowing green box and thinking caption |
| `focus` | Dark, cool source detail | Violet geodesic sphere, partial blue-white edges, one gliding hexagon |
| `relic` | Focus scene grade | Figure-bound violet triangles and rising light streams behind each body core |
| `netrunner` | Dark green source tint | Red edges, upward Cyber code, cyan titles, yellow carets |

All complete presets need [segmented setup](#segmented-looks). Palettes alone also work in Classic. Every preset consists of ordinary options; no effect is reserved for one preset.

<a id="four-thermal-detail-modes"></a>
### Five thermal modes

**Classic** is the lightweight luminance-based filter with no models. The other four modes segment subjects. Choose the level of detail separately from the color palette. Comparison base: `yautja "clip.mov" "detail.mp4" --palette costa-rica --verbose --timecode --grain 0 --pixelation 0 --no-crt-lines`. Add exactly one `--thermal` setting shown below. **Click any preview for its large, 960×540 animated GIF.**

| Low Detail | Cinematic |
| --- | --- |
| [![Low Detail: broad, soft heat blobs with subdued anatomy](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/style-low-detail.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/style-low-detail.gif?v=2.10.0) | [![Cinematic: broad skin and gear patches with softened boundaries](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/style-cinematic.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/style-cinematic.gif?v=2.10.0) |
| Broad, soft silhouettes with reduced anatomical variation and an abstract background. | Broad heat patches, some skin/gear separation, and softer edges. |
| `--thermal low-detail` | `--thermal cinematic` |

| Detailed | Very Detailed |
| --- | --- |
| [![Detailed: distinct skin, clothing, and equipment regions](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/style-detailed.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/style-detailed.gif?v=2.10.0) | [![Very Detailed: visible facial features and fabric texture retained from the source](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/style-very-detailed.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/style-very-detailed.gif?v=2.10.0) |
| Distinct skin, clothing, hair, and equipment, with restrained garment shading. | Preserves visible eyes, nose, mouth, hair, and clothing texture through local source contrast. |
| `--thermal detailed` | `--thermal very-detailed` |

All four use anatomy-guided fallback when estimates are uncertain. Cinematic, Detailed, and Very Detailed reuse the same models for extra surface segmentation; they take longer as the number of people increases. Very Detailed preserves features that are visible in the input; small, blurred, or obscured faces cannot gain missing detail. Small objects, distant hands, eyewear, and overlaps can still be missed or misclassified. These are generated visual effects, not measured temperatures or material properties.

Existing commands still work: `--thermal silhouette` and `--thermal semantic` now select Low Detail, and `--thermal realistic` remains an alias for Detailed. The lightweight `--thermal classic` luminance filter remains the no-flag CLI default; it does not segment subjects.

### Yautja style preset

This preset uses eleven colors from black and deep blue through cyan, green, yellow, orange, red, pink, and pale pink-white. It applies **12 thermal levels with soft transitions**, dark scenery, a red HUD, cyan annotations, and horizontal CRT lines. Grain and pixelation remain off.

| Yautja · complete preset | Thermal Spectrum · palette only |
| --- | --- |
| [![Yautja: dark scenery, soft color bands, pink and pale highlights](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/look-yautja.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/look-yautja.gif?v=2.10.0) | [![Thermal Spectrum palette with ordinary Cinematic grading and HUD](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-thermal-spectrum.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-thermal-spectrum.gif?v=2.10.0) |
| `--stylepreset yautja` | `--palette thermal-spectrum` |

Use `--thermal-levels 6` or `--thermal-levels 20` for fewer or more bands, `--thermal-levels 0` for continuous color, and `--thermal-band-softness 0` for hard bands. Soft transitions and optional glow add intermediate visible colors; twelve representative levels does not limit a GIF to twelve RGB colors. Explicit options override the recipe regardless of argument order. For example, add `--hud --thermal very-detailed` to use its colors and levels with more source detail and overlays. [Exact recipe and grading controls](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/colors.md#thermal-levels-and-reference-preset).

### Focus and Relic style presets

Focus uses a slowly rotating geodesic sphere, with bluish-violet broken lines fading toward the center. Satellite dots pulse away from vertices and return; some vertices carry seven-sided rings. Partial blue/lavender/white outlines shimmer along current subjects. One persistent hexagon glides between targets, containing the inset circle, six inner circles, four outer circles and a center square. The Focus preview is at the top of this page.

Relic adds violet triangles that spawn on the selected figure, rise, contract and spin away. Soft violet filaments stream upward behind each body's core, using shoulders and hips for alignment instead of extended arms or held props. When pose information is unavailable, the solid body region supplies the center. Foreground silhouettes hide the trails and their glow. [`--code-style light`](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/options.md#code-style) selects this treatment; `glyphs` selects readable code. Focus keeps this effect off. Decorative yellow scan patches remain available with `--target-weak-spots`; both presets leave them off.

| Relic |
| --- |
| [![Relic: violet figure-bound ornaments and soft rising light streams centered on each body core](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/look-relic.gif?v=2.12.1-light)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/look-relic.gif?v=2.12.1-light) |

<!-- example: {"id": "readme-focus", "tier": "models", "checks": {}} -->
```bash
yautja "clip.mov" "focus.mp4" --stylepreset focus --duration 4
```

<!-- example: {"id": "readme-relic", "tier": "models", "checks": {}} -->
```bash
yautja "clip.mov" "relic.mp4" --stylepreset relic --duration 4
```

Use `--outline-width`, `--outline-shine` and `--outline-speed` for the edge treatment. Grid brightness speed and `--geo-grid-rotation` are independent. Relic's `--target-motif-*` controls tune its ornaments. [Focus/Relic guide](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/focus.md) · [Every grid option](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/options.md#geo-grid).

### Murphy style preset

Murphy preserves source detail under a slight blue cast. Its bright green HUD uses a centered XY box, selected-subject outline and a medium-weight caption with a blinking underscore. The preview is at the top of the page. Automatic targeting needs no catalog:

<!-- example: {"id": "readme-murphy", "tier": "models", "checks": {}} -->
```bash
yautja "clip.mov" "murphy.mp4" --stylepreset murphy --duration 4
```

To customize it, add `--target-label "SEARCHING" --target-label-scale 2.2 --target-cursor --hud-font orbitron-medium --target-scale 1.25`. `--no-target-cursor` holds the caption without a blinking underscore. [Complete caption example](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/examples.md#murphy).

### Fremont style preset

**Fremont** preserves fine source detail under a **red/burgundy grade**, with **white Orbitron Bold text**, a **moving XY search grid**, and **thicker white subject outlines that blink during analysis**. A **persistent translucent gray circular target** glides between subjects, with a dark inner ring and crosshair. Its size stays constant throughout search, acquisition, and analysis. Descriptions stay inside the screen, including portrait frames. The numbers are decorative; labels describe detected categories such as person, dog, car, or motorcycle.

```bash
yautja "clip.mov" "fremont.mp4" --stylepreset fremont
```

This preset uses the segmented setup above; no figure catalog is needed. The four-second preview runs at normal source speed and 24 fps. Stills show the held analysis immediately. Empty scenes keep the target sweeping in search mode, and cuts or lost tracks restart scanning.

Use `--analysis-speed 2` for a faster sequence, `--analysis-blink-rate 0` for a steady outline, and `--analysis-margin 0.06` for more space at the edges. `--analysis-target-size 0.45` enlarges the disk; `--analysis-target-response 0.9` makes focus changes more gradual. `--no-analysis-target` hides just the disk and crosshair, `--no-analysis` hides the grid/text/outline, and `--no-hud` hides every overlay. The source highlights are adjustable with `--scene-highlights`. To scan vehicles, add `--warm-objects "person,car,motorcycle,bicycle,bus,truck"`. [Full analysis controls and styling](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/analysis.md).

Use `--hud-font orbitron-medium` for medium-weight text and `--analysis-outline-width 5` to set outline thickness in reference pixels at a 1080px short edge. These controls save with the style preset.

### Style presets based on palettes

**Yautja is the default look and palette; Costa Rica preserves the original colors.** Other palettes have a built-in style preset that selects Cinematic plus its named colors; other settings use the normal defaults. These are the same kind of visual bundle as Yautja, with fewer settings specified. Use `--stylepreset white-hot` to select the White Hot starter, or `--palette white-hot` to change the colors while keeping your thermal detail and other choices. HUD colors follow each palette's default theme unless customized. Optional timecode and subject callouts are enabled in these previews; all use identical segmentation and no added texture.

| Redline · red, blue, and black | Virtual Boy · red only |
| --- | --- |
| [![Redline palette: near-black shadows, vivid blue cooler regions, and dominant red warmth with restrained pink highlights](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-redline.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-redline.gif?v=2.10.0) | [![Virtual Boy palette: the scene and HUD rendered entirely in shades of red and black](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-virtualboy.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-virtualboy.gif?v=2.10.0) |
| `--stylepreset redline` | `--stylepreset virtualboy` |

Redline gives the movie-style red/blue/black treatment, with broad red warmth and small pink highlights. Virtual Boy uses only red and black, including the glyphs, waveform, and timecode, unless you explicitly choose custom or random HUD colors.

| Costa Rica · original look | Ironbow | Green Phosphor |
| --- | --- | --- |
| [![Costa Rica palette: cool blue and cyan through yellow and red](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-costa-rica.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-costa-rica.gif?v=2.10.0) | [![Ironbow palette: purple, orange, and yellow-white](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-ironbow.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-ironbow.gif?v=2.10.0) | [![Green Phosphor palette: a monochrome green night-vision style](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-green-phosphor.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-green-phosphor.gif?v=2.10.0) |
| `--stylepreset costa-rica` | `--stylepreset ironbow` | `--stylepreset green-phosphor` |

| Amber Phosphor | White Hot | Black Hot |
| --- | --- | --- |
| [![Amber Phosphor palette: warm amber display colors](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-amber-phosphor.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-amber-phosphor.gif?v=2.10.0) | [![White Hot palette: lighter warm regions with a light gray waveform and HUD](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-white-hot.gif?v=2.5.4)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-white-hot.gif?v=2.5.4) | [![Black Hot palette: simulated warm regions appear darker](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-black-hot.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-black-hot.gif?v=2.10.0) |
| `--stylepreset amber-phosphor` | `--stylepreset white-hot` | `--stylepreset black-hot` |

`--palette auto` selects the new Yautja palette. `--palette costa-rica` selects the original colors without changing detail. Changing the level of detail never changes the palette automatically. Phosphor palettes are display styles, not a low-light recovery feature.

### Abyss and animated heat glow

**Abyss** uses deep blue-black scenery, amber-to-white-hot regions, and a subdued cyan HUD. Glow is a separate option and is off by default, including with Abyss.

| Abyss · clean | Abyss · heat glow |
| --- | --- |
| [![Abyss palette with muted cyan HUD and no glow](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-abyss.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-abyss.gif?v=2.10.0) | [![Abyss palette with moving glow on the hot regions](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/glow-abyss.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/glow-abyss.gif?v=2.10.0) |
| `--stylepreset abyss` | `--stylepreset abyss --heat-glow 0.75` |

`--hud-theme muted-cyan` makes the same subdued HUD available with any palette. Selecting `--hud-theme palette` instead matches its colors to that palette's ramp.

### Netrunner style preset

**Netrunner** keeps the recognizable scene under a dark green tint, with **warm-red neon HUD and silhouette outlines**, **Cyber code raining upward inside detected people and animals**, and **cyan overhead titles with yellow downward carets**. It uses red `#FD5550`, cyan `#41E8EF`, and yellow `#FFC442`. Bold yellow carets keep fixed gaps of 30 reference pixels above the head and 20 below the cyan title, scaled to the frame size. Annotations crop naturally at the screen edge without squeezing these gaps or hiding a still-visible caret. The red silhouette outline is thinner, and upward code uses 95% of available columns. It requires the segmented setup above.

```bash
yautja "clip.mov" "netrunner.mp4" --stylepreset netrunner
```

Choose the glyph set independently with **`--HUDglyphs cyber`** or **`--HUDglyphs yautja`**, or readable **`--HUDglyphs tech`**. Cyber contains 192 generated vector glyphs and is the default for Netrunner. The choice applies to every alien HUD readout, waveform glyph, callout, subject title, and code stream; human-readable timecode stays numeric. It also works with other style presets.

```bash
yautja "clip.mov" "cyber-thermal.mp4" --stylepreset yautja --HUDglyphs cyber
yautja "clip.mov" "custom-signal.mp4" --stylepreset netrunner --code-speed 1.5 --code-density 0.8
```

Outlines use flow-aligned, stabilized current-frame masks, with periodic detection and per-frame refinement. This reduces boundary drift during movement, with additional processing time. Titles are decorative labels that stay with a track. A fixed glyph grid lights up in rising streams with bright heads, fading tails, and occasional character changes, clipped within each mask. Glow can extend past the edge. `--code-speed 0` freezes the rain. `--no-subject-code`, `--no-subject-outline`, and `--no-subject-labels` switch those parts off independently; `--no-hud` hides them all. Tracking and occlusion quality depend on the input footage. [Complete controls and preset customization](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/cyber.md).

## Customize

Options apply in this order: **defaults → optional built-in base → saved settings → explicit flags**. Choose one selector, `--stylepreset` or `--preset-file`; individual flags win regardless of their position. Supplying a per-element map replaces an inherited map, and omitted elements inherit the relevant global setting. Explicit zero is preserved.

| Rendering stage | Options and purpose | Reference |
| --- | --- | --- |
| Detect and track | Categories, detection interval, mask stability | [Runtime controls](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/options.md#mask-stability) |
| Build the scene | Thermal detail, palette/levels or source tint/exposure | [Scene/thermal recipe](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/examples.md#thermal-grade) |
| Add subject overlays | Outlines, code, titles, carets | [Netrunner](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/cyber.md) |
| Add targeting and grid | Selection, geometry, movement, fill, analysis | [Targets](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/targets.md) · [Analysis disk](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/analysis.md) |
| Draw the waveform | Source → shape → display device → ink | [Waveform options](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/options.md#waveform) |
| Style HUD artwork | Color, opacity, blur, bloom or neon | [Authoritative HUD role table](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/hud-elements.md) |
| Finish the picture | Grain, pixels, CRT, VHS, trails | [Display recipe](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/examples.md#crt) |

Five different edge controls have different scopes: `--subject-outline` outlines every detected subject, `--target-outline` outlines selected subjects, `--analysis-outline-width` sizes Fremont analysis contours, `--target-fill stroked` makes the reticle hollow, and `--target-stroke` adds a colored border to reticle marks. Thermal softness smooths the heat field; HUD blur softens artwork; heat glow lights hot picture regions; HUD bloom/neon lights overlays.

### HUD colors, custom palettes, and random colors

White Hot uses a **light gray (`#D0D0D0`) waveform and HUD** by default, Black Hot uses black, Abyss uses muted cyan, and other palettes retain the standard red/cyan HUD. Use **`--hud-theme palette`** to match the waveform, glyphs, clock, callouts, and scale to the selected palette; White Hot keeps light gray ink and Black Hot keeps black ink in this mode too. Custom and random HUD themes remain available. These controls work with images and videos and every thermal look.

| Green Phosphor · matched HUD | Ironbow · matched HUD |
| --- | --- |
| [![Green Phosphor with matching green waveform, readout, timecode, and callouts](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/colors-matched-green.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/colors-matched-green.gif?v=2.10.0) | [![Ironbow with coordinated orange and purple HUD colors](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/colors-matched-ironbow.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/colors-matched-ironbow.gif?v=2.10.0) |
| `--palette green-phosphor --hud-theme palette` | `--palette ironbow --hud-theme palette` |

| Custom thermal + HUD colors | Random thermal + HUD colors |
| --- | --- |
| [![Custom navy, teal, and gold thermal colors with independently colored HUD elements](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/colors-custom.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/colors-custom.gif?v=2.10.0) | [![A seeded random thermal palette and independently randomized HUD colors, stable across frames](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/colors-random.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/colors-random.gif?v=2.10.0) |
| [Exact custom settings](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/colors.md#custom-hud-elements) | `--random-colors --seed 137` |

**Custom thermal colors:** use `--palette custom --palette-colors "#000000,#0033ff,#ff2200,#fff0c0"`. Supply 2–16 hex colors, cold to hot, separated by commas or spaces. Stops are evenly spaced. Three- and six-digit RGB hex values work; quote the string.

**Custom HUD colors:** select a custom theme and assign the desired roles:

```bash
yautja "photo.jpg" "custom-hud.png" --hud-theme custom --hud-colors "waveform=#44ff88,timecode=#ddffee,callouts=#88ccff"
```

Use any key in the [HUD role table](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/hud-elements.md), including subject, targeting, grid and analysis layers. Omitted elements keep standard colors. Custom ink supports black and dark colors as well as bright ones.

**Random colors:** `--random-colors` randomizes both the thermal palette and every HUD element. Use `--palette random` or `--hud-theme random` for just one. A different `--seed` produces a new set; the same seed repeats it. Colors stay fixed throughout the clip. The JSON report includes the resolved hex values so a set can be reused.

See the [color controls guide](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/colors.md) for full commands, element descriptions, and how custom ink interacts with glow and analog effects.

### Grain and chunky pixels

Comparison base: `yautja "clip.mov" "comparison.mp4" --thermal cinematic --palette costa-rica --verbose --timecode --grain 0 --pixelation 0 --no-crt-lines`. Add the pictured option; target comparisons also use a [catalog selection](#choose-a-figure-and-add-a-target). The complete saved-look examples identify their own preset.

Every effect is optional. **Yautja enables CRT lines by default**; use `--no-crt-lines` to turn them off. The comparisons below use Costa Rica, with other effects off unless shown. Add grain, chunky pixels, CRT lines, or VHS styling independently, or combine them. The heat field, glyph selection, and audio behavior stay the same.

| Clean · default | Grain only | Chunky pixels only |
| --- | --- | --- |
| [![Clean Cinematic output without added texture](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/style-cinematic.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/style-cinematic.gif?v=2.10.0) | [![Fine animated grain without pixelation or scanlines](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-grain.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-grain.gif?v=2.10.0) | [![Chunky pixelation without added grain or scanlines](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-pixelation.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-pixelation.gif?v=2.10.0) |
| No texture flags | `--grain 0.06` | `--pixelation 80` |

| CRT Lines only | Sensor texture · combined preset |
| --- | --- |
| [![Horizontal CRT lines across the picture and HUD](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-crt-lines.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-crt-lines.gif?v=2.10.0) | [![Combined sensor texture with grain, sensor pixels, and CRT lines](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-sensor-texture.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-sensor-texture.gif?v=2.10.0) |
| `--crt-lines` | `--sensor-texture` |

| VHS only | VHS + CRT Lines |
| --- | --- |
| [![VHS styling with softened color, chroma bleed, horizontal wobble, tape noise, and occasional tracking defects](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-vhs.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-vhs.gif?v=2.10.0) | [![Combined VHS analog defects and horizontal CRT lines](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-vhs-crt.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-vhs-crt.gif?v=2.10.0) |
| `--vhs` | `--vhs --crt-lines` |

Bare `--grain` uses strength 0.035; the example above uses a stronger 0.06 so it is easy to see. `--grain 0` disables noise. Bare `--pixelation` uses a longest grid edge of 96; lower values make larger blocks (range 32–640), and `--pixelation 0` disables it. Pixelation changes the display, not the segmentation resolution. `--no-crt-lines` disables CRT lines; the older `--scanlines` / `--no-scanlines` flags are aliases.

VHS adds softer color detail, chroma bleed, slight horizontal wobble, tape noise, and occasional dropouts and tracking defects across the finished picture, including the HUD. It animates in video; still images receive a fixed frame of the effect. `--no-vhs` disables it. It does not alter the soundtrack or invent thermal detail. CRT lines can be used with or without VHS.

The combined sensor preset adds grain 0.035, a grid at `--sensor-resolution` (default 256), CRT lines, and light intensity quantization. It does not enable VHS. Individual settings override the corresponding preset components. `--no-sensor-texture` disables the preset while preserving explicitly enabled effects. For completely clean output, omit the effects or use `--no-sensor-texture --grain 0 --pixelation 0 --no-crt-lines --no-vhs`.

```bash
python -m yautja "clip.mov" "outputs/clip-cinematic.mp4" --thermal cinematic --verbose --timecode
python -m yautja "photo.jpg" "outputs/photo-detailed.png" --thermal detailed --palette ironbow --verbose
python -m yautja "clip.mov" "outputs/clip-phosphor.mp4" --thermal cinematic --palette green-phosphor --grain 0.03 --pixelation 96
python -m yautja "clip.mov" "outputs/clip-vhs.mp4" --thermal cinematic --palette redline --vhs --crt-lines
python -m yautja "clip.mov" "outputs/clip-virtualboy.mp4" --thermal silhouette --palette virtualboy
```

Comparison GIFs use the same source footage, with ranges chosen for each effect; Focus and Relic show four seconds at normal speed and 24 fps. Embedded previews are 480×270; click one to open its **960×540 large version**, rendered with HUD and textures at that size. The hero is also 960×540. They compare styling choices, not model accuracy. The source footage stays local.

### Heat glow, vertical CRT lines, and adjustable trails

Comparison base: `yautja "clip.mov" "comparison.mp4" --thermal cinematic --palette costa-rica --verbose --timecode --grain 0 --pixelation 0 --no-crt-lines`. Add the pictured option; target comparisons also use a [catalog selection](#choose-a-figure-and-add-a-target). The complete saved-look examples identify their own preset.

**Heat glow works with every palette.** Set `--heat-glow` from **0–1** (default 0), and `--heat-glow-speed` from **0–5** (default 1). A speed of 0 freezes the glow pattern. It brightens and diffuses hot regions before the HUD is added; inverted Black Hot uses dark diffusion. The existing `--glow` setting still controls HUD bloom independently.

| Original palette · heat glow | Green Phosphor · heat glow |
| --- | --- |
| [![Original Yautja palette with moving heat glow](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-heat-glow.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-heat-glow.gif?v=2.10.0) | [![Green Phosphor with palette-matched HUD and heat glow](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/glow-green.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/glow-green.gif?v=2.10.0) |
| `--heat-glow 0.75` | `--palette green-phosphor --hud-theme palette --heat-glow 0.75` |

**CRT patterns** include vertical lines, a horizontal/vertical **grid**, and **crosshatch** (a grid at 45 degrees). `--crt-strength` sets their darkness from **0–1** (default 0.12); 0 hides them. These patterns affect the complete picture, including the HUD, and work with every palette on images and videos.

| Vertical lines | Grid | Crosshatch · 45° |
| --- | --- | --- |
| [![Vertical CRT lines at strength 0.25](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-crt-vertical.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-crt-vertical.gif?v=2.10.0) | [![Horizontal and vertical CRT grid at strength 0.25](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-crt-grid.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-crt-grid.gif?v=2.10.0) | [![45-degree CRT crosshatch at strength 0.25](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-crt-crosshatch.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-crt-crosshatch.gif?v=2.10.0) |
| `--crt-vertical-lines --crt-strength 0.25` | `--crt-grid --crt-strength 0.25` | `--crt-crosshatch --crt-strength 0.25` |

Click any preview for its large animated GIF. Grid is equivalent to enabling `--crt-lines` and `--crt-vertical-lines` together; combining those flags with grid does not darken the same lines twice. Crosshatch adds two diagonal line directions and can be combined with grid or individual lines. Intersections are darker. Both new options default off; use `--no-crt-grid` or `--no-crt-crosshatch` to disable each independently. The sensor-texture preset continues to enable only its horizontal lines. Save these settings in [your own preset](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/presets.md).

**Motion blur** adds temporal frame persistence: higher values leave longer trails on moving subjects and HUD details. It resets at detected cuts and needs consecutive video frames; stills have no motion trail. **CRT bleed** adds horizontal phosphor smear to both images and videos. Both strengths range from **0–1**, default to 0, and leave the soundtrack unchanged.

| Softer motion trails | Stronger motion trails |
| --- | --- |
| [![Softer temporal motion trails](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-motion-soft.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-motion-soft.gif?v=2.10.0) | [![Stronger temporal motion trails](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-motion-strong.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-motion-strong.gif?v=2.10.0) |
| `--motion-blur 0.35` | `--motion-blur 0.85` |

| Softer CRT bleed | Stronger CRT bleed |
| --- | --- |
| [![Softer horizontal CRT phosphor bleed](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-bleed-soft.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-bleed-soft.gif?v=2.10.0) | [![Stronger horizontal CRT phosphor bleed](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-bleed-strong.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-bleed-strong.gif?v=2.10.0) |
| `--crt-bleed 0.3` | `--crt-bleed 0.85` |

All of these controls are independent of VHS, grain, pixelation, and the sensor-texture preset. Click each preview for the large animated GIF.

### Waveforms

Choose a Rorschach inkblot or one of three **digital distortion** waveforms. These examples use **Redline**, with `--wave-width 0.14 --wave-height 1 --wave-gain 4` (extra audio gain for this quiet clip); the narrower Vocoder Bars example uses `--wave-width 0.09`. The illuminated shape follows the soundtrack; GIFs are silent.

| Filled · broad connected lobes | Split · separated inkblots | Hollow · dark interior pockets |
| --- | --- | --- |
| [![Filled mirrored Rorschach waveform spanning the image height](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/waveform-rorschach.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/waveform-rorschach.gif?v=2.10.0) | [![Separated mirrored inkblots responding to the soundtrack](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/waveform-rorschach-split.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/waveform-rorschach-split.gif?v=2.10.0) | [![Hollow mirrored waveform lobes with dark pockets](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/waveform-rorschach-hollow.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/waveform-rorschach-hollow.gif?v=2.10.0) |
| `--wave-style rorschach` | `--wave-style rorschach-split` | `--wave-style rorschach-hollow` |

The digital styles use distinct geometries: stacked blocks with square cutouts, scattered data packets, or horizontal vocoder bars in one narrow vertical stack. The vocoder spans the frame height along the left edge; each rounded, dark bar contains small vertical LED segments, brightest at the center and fading toward the ends. Audio lights up vivid red segments across alternating shorter and longer rows, with an exaggerated response and a strong red halo. Inactive segments remain visible in dark burgundy fading to black, including during silence. Its red glow is inspired by KITT’s voice display.

| Bitcrush Blocks | Packet Shards | Vocoder Bars |
| --- | --- | --- |
| [![Chunky stacked waveform blocks with square notches](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/waveform-digital-blocks.gif?v=2.6.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/waveform-digital-blocks.gif?v=2.6.0) | [![Scattered unequal pixel packets responding to audio](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/waveform-digital-shards.gif?v=2.6.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/waveform-digital-shards.gif?v=2.6.0) | [![Bright glowing red active vocoder segments above dark burgundy-to-black inactive bars](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/waveform-digital-circuit.gif?v=2.7.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/waveform-digital-circuit.gif?v=2.7.0) |
| `--wave-style digital-blocks` | `--wave-style digital-shards` | `--wave-style digital-circuit` |

`--wave-width` sets maximum width as a fraction of the frame (0.02–0.3, default 0.12); `--wave-height` sets height (0.1–1, default 0.96). In Rorschach styles, `--wave-detail` goes from broad and smooth at 0 to sharper edge spikes and more intricate lobes at 1 (default 0.6). These shapes keep a thick mirrored core, with pointed, irregular edges driven by short peaks and troughs in the waveform. Quiet ambience is amplified for visibility, and louder audio fills more of the column. Silent pauses within audible tracks stay empty; the existing fallback for an absent or entirely silent soundtrack remains procedural.

In Blocks and Shards, `--wave-detail` controls pixel density: lower values make larger chunks, higher values make finer blocks. In Vocoder Bars it controls the number of horizontal rows. The casings and idle segments stay fixed while audio expands and brightens the active segments. Silence leaves the dim inactive bars visible. The vocoder preview uses `--hud-theme custom --hud-colors "waveform=#FF302B"` and `--neon --neon-intensity 0 --neon-elements "waveform=1.2" --neon-spread 0.4 --neon-core-whiten 0` for bright red active segments with a strong glow. Inactive segments use a dim version of the chosen waveform color and emit no light. The dark casing shares waveform opacity and blur, and emits no light; color and neon remain configurable. The original `--wave-style trace` stays the default. All six styled waveforms replace the left trace, scale, and flanking glyph rows. They use the existing waveform color, work with all HUD themes, blur, opacity, and neon, and leave timecode, callouts, and selected targets intact. Combine `--crt-bleed 0.3` for softer edges or `--motion-blur 0.4` for video trails. Each preview links to its large animated GIF.

**Shape and display are independent.** `--wave-style` chooses any of the seven shapes; `--wave-display plain|led` chooses direct ink or a segmented LED device. Digital Circuit defaults to LED, the others to plain. `--wave-backlight` controls non-emissive idle cells from 0–1. LED device materials follow waveform ink, opacity and blur; only active cells emit bloom/neon. Trace keeps its axis, ticks and glyphs plain.

<!-- example: {"id": "readme-led", "tier": "classic", "checks": {"wave_display": "led"}} -->
```bash
yautja "clip.mov" "led-rorschach.mp4" --wave-style rorschach --wave-display led --wave-backlight 0.2 --hud-theme custom --hud-colors "waveform=#ff302b" --neon --duration 1
```

The same Rorschach shape rendered as an LED display: glowing red active cells, dark burgundy idle cells, and a non-emissive black backing. This preview plays four seconds of source footage in four seconds. [Exact preview recipe](https://github.com/petehottelet/yautja/blob/main/docs/GALLERY.md#led-waveform).

[![Rorschach waveform rendered with bright red LED cells and a dark inactive display](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/waveform-led-rorschach.gif?v=2.12.1)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/waveform-led-rorschach.gif?v=2.12.1)

### Target shapes

Comparison base: `yautja "clip.mov" "comparison.mp4" --thermal cinematic --palette costa-rica --verbose --timecode --grain 0 --pixelation 0 --no-crt-lines`. Add the pictured option; target comparisons also use a [catalog selection](#choose-a-figure-and-add-a-target). The complete saved-look examples identify their own preset.

All 11 target types support **`--target-fill filled`** and **`--target-fill stroked`**. Filled mode uses solid marks and dots, with translucent interiors for enclosed reticles. Stroked mode traces their edges, including hollow dots, curved bands, crosshairs, and square brackets. The default `auto` keeps each design's original treatment. Color, acquisition timing, flash, glow, blur, and opacity remain independent; `--target-stroke` adds an optional colored border.

| Triangle + three lock dots | Circle + three lock dots |
| --- | --- |
| [![Triangle target with three lock dots that appear on acquisition](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-shape-triangle-dots.gif?v=2.12.1-tight-dots)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-shape-triangle-dots.gif?v=2.12.1-tight-dots) | [![Circular target with four ring gaps and three lock dots](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-shape-round-dot.gif?v=2.11.0-targets)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-shape-round-dot.gif?v=2.11.0-targets) |
| `--target-shape triangle-dots` | `--target-shape round-dot` |

Both previews play at normal source speed and 24 fps. The three dots appear only on lock and reset when the target is lost. The triangle's dots retain their 12% smaller diameter and now have 15% less spacing between their centers. The circle's dots retain their size and spacing. Click either GIF for the larger version.

The complete contact sheet includes all **11 geometric shapes**, including both lock-dot designs, plus **Fremont's scan disk**. Geometric shapes are **filled on the left and stroked on the right**; their labels give the corresponding `--target-shape` value. Fremont uses `--analysis-target` and is shown with its default translucent fill and with the fill off (`--hud-opacity-elements "analysis-target-fill=0"`). Its controls are explained in the [analysis guide](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/analysis.md).

[![Complete target contact sheet: all 11 geometric shapes including triangle and circle with three lock dots, plus Fremont's translucent scan disk](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-shapes.png?v=2.12.1-tight-dots)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-shapes.png?v=2.12.1-tight-dots)

```bash
yautja "clip.mov" "filled.mp4" --stylepreset yautja --figures "figures.json" --target S001-F002 --target-shape triangle-dots --target-fill filled
yautja "clip.mov" "stroked.mp4" --stylepreset yautja --figures "figures.json" --target S001-F002 --target-shape square-cross --target-fill stroked
```

The original `triangle` is the default; `--target-scale` changes the reticle size. Hollow Cross has four L-shaped bands and an open center; `vector-lock` and `iron-sights` resolve to this design. `--target-mode auto` uses segmented subjects automatically, while the default `selected` mode uses a catalog. Explicit catalog selections take precedence, including frames where a selected figure is absent. `--target-motif triangles` and `--target-label "TARGETING"` add ornaments and a caption. [Full selection, color, and effect controls](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/targets.md).

### Choose a figure and add a target

Scan a clip or still to get a **shot-by-shot figure list**, thumbnails, and reusable IDs. Scanning needs the semantic setup below. Open the generated contact sheet, choose an ID, then render:

```bash
yautja "clip.mov" "figures.json" --list-figures
# Open figures.html; select an ID from that scan.
yautja "clip.mov" "targeted.mp4" --thermal cinematic --figures "figures.json" --target S001-F003
```

The saved catalog belongs to the exact source file. Reuse it for different palettes, resolutions, frame rates, or trims; select additional shot IDs explicitly when a figure reappears after a cut. IDs are detected tracks, and detection can miss or swap figures during occlusion. Inspect the contact sheet and output. `targets_seen` and `targets_unseen` in the report confirm which selections appeared.

| Assemble and flash · red/white | Abyss · glowing cyan target + vertical CRT | Custom target colors |
| --- | --- | --- |
| [![Three blades assemble around a selected explorer and flash red and white](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-lock.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-lock.gif?v=2.10.0) | [![Abyss with a glowing cyan target and neon HUD, vertical CRT lines, and heat glow](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-abyss-steady.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-abyss-steady.gif?v=2.10.0) | [![Green palette with a custom teal and pale mint target](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-custom.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-custom.gif?v=2.10.0) |
| Default target animation | `--palette abyss --target-colors "#267085,#267085" --no-target-flash --neon --crt-vertical-lines --crt-strength 0.25 --heat-glow 0.65` | `--palette green-phosphor --hud-theme palette --target-colors "#31d7bb,#d6fff3" --target-acquire 0.45 --crt-bleed 0.4` |

These target examples show seconds 0–3.25 of the source, selecting the foreground explorer separately in the first two shots. The triangle contracts into a compact marker at the figure's center, with solid-color sides and narrow, clear gaps at all three corners. It assembles in **0.8 seconds**, lands red, then flashes red/white at **1.5 cycles per second**. Set `--target-acquire`, `--target-scale`, and `--target-flash-rate` to change timing and size; scale 1 uses the compact reticle. `--no-target-flash` keeps the assembly and holds the primary color; equal primary/flash colors work too. White Hot uses light gray and Black Hot uses black for both target states unless colors are overridden. Stills display the assembled triangle immediately.

Set `--target-colors "#ff302b,#ffffff"` for independent primary/flash colors, or use the `target` and `target-flash` keys with custom HUD colors. Palette-matched and random HUD themes also color targets. `--no-hud` hides them along with every other overlay. [All target controls, bounds, scan details, and effect options](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/targets.md).

### Neon HUD

Add **`--neon`** to illuminate waveform artwork, glyphs, timecode, callouts, leaders, markers, and selected targets. A bright core and two soft halos follow each element's color. Neon is off by default and works with every palette, for images and video.

| Steady neon | Neon hum |
| --- | --- |
| [![Neon waveform, glyphs, callouts and LCD timecode](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-neon.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-neon.gif?v=2.10.0) | [![The same neon HUD with gentle synchronized flicker](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-neon-flicker.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-neon-flicker.gif?v=2.10.0) |
| `--neon` | `--neon --neon-flicker 0.5` |

These matched examples show seconds 0–3.25 with verbose callouts and timecode enabled. Click a preview for the large GIF. The Abyss target example above also uses neon: its muted `#267085` ink emits a brighter cyan halo.

| Control | Meaning |
| --- | --- |
| `--neon` / `--no-neon` | Enable or disable the entire treatment; default off |
| `--neon-intensity 1` | Brightness from 0–2; default 1. Zero keeps the original ink with no neon |
| `--neon-spread 0.6` | Halo spread from 0–2; default 0.6. Lower values give a tighter rim |
| `--neon-flicker 0.5` | Synchronized seeded hum from 0–1; default 0 is steady |
| `--neon-elements "waveform=0.6,target=1.2,timecode=0"` | Independent intensity overrides; omitted elements inherit the shared value |

Element names are the same as HUD blur below; `target` covers both flash states. Existing colors, outlines, blur and opacity still apply. Blur softens the core; opacity fades both core and halo. White Hot glows white, Black Hot diffuses black, and Virtual Boy retains its red-only display. `--heat-glow` remains independent. Neon replaces standard `--glow` bloom while enabled, and CRT/VHS effects run afterward. `--no-hud` hides all of it.

Load or customize the bundled [Abyss Neon preset](https://github.com/petehottelet/yautja/blob/main/skills/yautja/assets/presets/abyss-neon.json) with `--preset-file`. All six neon controls can be saved with `--save-preset`. [Full controls](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/targets.md#neon-hud).

### Reticle stroke and HUD blur

Comparison base: `yautja "clip.mov" "comparison.mp4" --thermal cinematic --palette costa-rica --verbose --timecode --grain 0 --pixelation 0 --no-crt-lines`. Add the pictured option; target comparisons also use a [catalog selection](#choose-a-figure-and-add-a-target). The complete saved-look examples identify their own preset.

Add an optional outline with `--target-stroke 5`. Choose one outline color or a landing/flash pair with `--target-stroke-colors "#660b12,#687a8d"`; omit the colors to use darker shades of the current target colors. The outline is drawn inward, keeping the corner gaps open. It is off by default (`--target-stroke 0`); the bare flag uses width 2 and the range is 0–12.

`--hud-blur 3` softens all HUD artwork. Use `--hud-blur-elements "waveform=6,target=4,timecode=0"` for independent overrides: omitted elements inherit the shared amount, and explicit 0 keeps an element sharp. Every radius is 0–20, with 0 as the default. Blur and stroke widths are pixels at a **1080px short edge**, scaled with output size. HUD blur affects the artwork before it is placed on the scene, leaving the underlying thermal image sharp.

| Reticle outline · separate flash colors | Target blur only |
| --- | --- |
| [![Reticle with an optional colored outline](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-outline.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-outline.gif?v=2.10.0) | [![Soft target with crisp waveform, callouts, and readout](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-blur.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-blur.gif?v=2.10.0) |
| `--target-stroke 5 --target-stroke-colors "#660b12,#687a8d"` | `--hud-blur-elements "target=8"` |

| Matched red · waveform + reticle blur | Shared HUD blur · sharp timecode |
| --- | --- |
| [![Blurred red Rorschach waveform and reticle with a crisp matching timecode](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-wave-blur.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-wave-blur.gif?v=2.10.0) | [![HUD softened by element while its timecode remains sharp](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-hud-blur.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-hud-blur.gif?v=2.10.0) |
| `--wave-style rorschach --wave-width 0.14 --wave-height 1 --hud-blur-elements "waveform=6,target=6"` | `--hud-blur 3 --hud-blur-elements "waveform=6,target=5,timecode=0"` |

Click any preview for the large GIF. These comparisons use the same 0–3.25-second clip and target selections as the examples above. Blur keys are `waveform`, `waveform-axis`, `waveform-ticks`, `waveform-glyphs`, `readout`, `timecode`, `callouts`, `leaders`, `markers`, and `target`. Target blur applies to both flash states. These controls work for images and videos, alongside HUD bloom, heat glow, and CRT/VHS effects. `--no-hud` hides them all. [Full controls and examples](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/targets.md#reticle-stroke-and-independent-hud-blur).

The matched-red Rorschach example additionally uses `--hud-theme custom --hud-colors "waveform=#ff302b,timecode=#ff302b" --target-colors "#ff302b,#ff302b"`. Both reticle states use the same red. Custom HUD colors use alpha compositing, avoiding the pink shift that screen blending can introduce over a blue scene.

### HUD transparency

Comparison base: `yautja "clip.mov" "comparison.mp4" --thermal cinematic --palette costa-rica --verbose --timecode --grain 0 --pixelation 0 --no-crt-lines`. Add the pictured option; target comparisons also use a [catalog selection](#choose-a-figure-and-add-a-target). The complete saved-look examples identify their own preset.

Set `--hud-opacity 0.5` for half-strength HUD artwork, or `--hud-opacity-elements "waveform=0.3,target=0.7,timecode=0.9"` for separate values. **0 is invisible; 1 keeps full existing visibility** (the default). Omitted elements inherit the shared opacity; explicit values override it. Blur and opacity are independent, and both work for stills and videos.

| Entire HUD · opacity 0.5 | Independent opacity · waveform / target / timecode |
| --- | --- |
| [![All HUD artwork at half opacity](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-opacity.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-opacity.gif?v=2.10.0) | [![Red waveform at 0.3 opacity, target at 0.7, and timecode at 0.9](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-opacity-elements.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-opacity-elements.gif?v=2.10.0) |
| `--hud-opacity 0.5` | `--hud-opacity-elements "waveform=0.3,target=0.7,timecode=0.9"` with the matched red Rorschach colors and shape above |

| Independent opacity · neon on |
| --- |
| [![Neon red waveform, target, and timecode with cyan callouts and independent opacity](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-opacity-neon.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-opacity-neon.gif?v=2.10.0) |
| Add `--neon` to the independent-opacity example above |

This keeps the Costa Rica thermal colors, red waveform/target/timecode, cyan callouts, and the same opacity values: waveform 0.3, target 0.7, and timecode 0.9. Neon adds bright cores and soft halos to the HUD; both target states stay red. Click the preview for the large animated GIF.

Opacity keys cover all HUD elements: `waveform`, `waveform-axis`, `waveform-ticks`, `waveform-glyphs`, `readout`, `timecode`, `callouts`, `leaders`, `markers`, `target`, and `target-flash`. A `target` override controls both states unless `target-flash` is explicitly set. Reticle outlines and glow follow their element's opacity. `--no-hud` still hides everything. Click either GIF for the large version. [Detailed transparency controls](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/targets.md#hud-transparency).

### Turn the HUD off

Use **`--no-hud`** for the thermal image alone. It removes the waveform, scale, glyphs, timecode, callouts, connector lines, and target markers—even when `--timecode` or `--verbose` is also supplied. Thermal style, palette, textures, and the video soundtrack stay active. HUD is on by default; `--hud` turns it back on.

| HUD on · default | HUD off |
| --- | --- |
| [![Cinematic thermal output with the full HUD and annotations](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/style-cinematic.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/style-cinematic.gif?v=2.10.0) | [![Cinematic thermal output with every HUD overlay hidden](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/hud-off.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/hud-off.gif?v=2.10.0) |
| Default HUD, with `--verbose --timecode` for annotations and clock | `--no-hud` |

With `--verbose`, callout lines aim at a smoothed center of each visible silhouette—an image-based approximation of center of mass. Labels keep their position relative to the figure while that space remains clear, reducing jumps between moving arms and shoulders. If the center falls outside a concave or partly hidden silhouette, the marker uses the nearest visible point. This is automatic; no extra flag is needed.

```bash
python -m yautja "clip.mov" "thermal-only.mp4" --thermal cinematic --no-hud
python -m yautja "photo.jpg" "thermal-only.png" --palette green-phosphor --no-hud
```

<a id="create-your-own-style-presets"></a>
## Save, load and share

Save a full portable snapshot of visual settings. Bundled font names are saved; custom font paths, media paths, catalog IDs, timing, encoding, audio selection and model/device/mask-runtime settings are chosen per conversion. Saving needs no media or models.

<!-- example: {"id": "readme-save", "tier": "classic", "checks": {}} -->
```bash
yautja --stylepreset yautja --thermal classic --hud-theme palette --neon --save-preset "readme-style.json" --preset-name "My Style"
```

<!-- example: {"id": "readme-reuse", "tier": "classic", "checks": {}} -->
```bash
yautja "photo.jpg" "readme-reused.png" --preset-file "readme-style.json" --heat-glow 0.2
```

Share the JSON and load it with `--preset-file`. Exported snapshots include resolved defaults; hand-authored JSON can instead name a `base` and list only its changes. Existing files require explicit `--overwrite`. [Schema and full round trip](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/presets.md) · [List built-ins](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/options.md#list-presets).

| Tropic Glow · Yautja with neon HUD and heat glow |
| --- |
| [![Tropic Glow: Yautja with palette-matched neon HUD and animated heat glow](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/preset-tropic-glow.gif?v=2.10.0)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/preset-tropic-glow.gif?v=2.10.0) |
| [Editable JSON preset](https://github.com/petehottelet/yautja/blob/main/skills/yautja/assets/presets/tropic-glow.json) · [Creation, schema, and sharing guide](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/presets.md) |

[Tropic Glow editable JSON](https://github.com/petehottelet/yautja/blob/main/skills/yautja/assets/presets/tropic-glow.json) combines Yautja with palette-matched neon and heat glow. [Detailed comparison](https://github.com/petehottelet/yautja/blob/main/docs/GALLERY.md#custom-preset).

<a id="useful-controls"></a>
## Control the output

Keep aspect ratio with `--max-size`; set a frame rate with `--fps`, or omit it to retain the source rate. Trim with `--start` and `--duration`. Lower `--crf` means higher quality and larger files; encoder `--preset slow` spends more time compressing. It is unrelated to visual `--stylepreset`.

<!-- example: {"id": "readme-quality", "tier": "classic", "checks": {}} -->
```bash
yautja "clip.mov" "quality.mp4" --start 0 --duration 1 --max-size 1280 --fps 24 --crf 18 --preset slow --audio-stream 0
```

For a quick check, use `--max-size 640 --fps 12 --crf 24 --preset fast --duration 1`, then remove the preview limits for the final export.

Sound is retained by default. `--audio-stream 1` selects the second audio track for both playback and waveform analysis. `--mute` removes playback but keeps analysis. Auto waveforms use procedural motion when audio is absent or silent; `--waveform audio` requires an audio track and preserves silent samples. LED idle cells remain visible during silence. Stills always use procedural waveform sampling; timing/encoding/audio options intended for video are inactive or rejected where inappropriate. [Output and audio examples](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/examples.md#quality).

## Troubleshooting

| Symptom | Cause and next step |
| --- | --- |
| Models are missing | Install `yautja[semantic]`, then run `yautja --download-models` once. Ordinary conversion does not download. |
| Video fails before conversion | Run `yautja --doctor`; put both FFmpeg and ffprobe on PATH. Image diagnosis uses `--media image`. |
| A preset fails in Classic | Its subject overlays require segmentation. Install the semantic extra, or use only its palette with `--thermal classic --palette …`. |
| Target is missing | Automatic targeting needs segmented subjects; explicit targets need a catalog from the exact input file. Check `targets_seen` and `targets_unseen` in the report. |
| Outline flickers around small accessories | Defaults stabilize masks. Tune `--mask-stability` and `--mask-min-region`; both zero restores the previous contour behavior. |
| A label reaches the frame edge | Fremont descriptions and target captions fit safe margins. Overhead Netrunner glyph titles intentionally crop while preserving head/caret spacing. |
| Styling appears unchanged | Check its enabling flag, `--no-hud`, element opacity and preset precedence. Nonzero neon settings require `--neon`. |
| Output already exists | Choose another output path or explicitly add `--overwrite`. Replacement happens after successful conversion. |
| CLI uses the wrong environment | Run `python -m yautja --doctor` with the same Python used for installation; inspect its installation report. |

The same seed repeats procedural artwork for the same inputs and settings. Model/device/precision differences, codec conversion and source changes can still alter output; this is not a cross-platform pixel guarantee. [Runtime and codecs](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/runtime.md) · [Segmentation details](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/semantic.md).

## Install the agent skill

**Optional:** add instructions for Claude Code or Codex to operate Yautja. The converter can be used directly without an agent or this installer.

```bash
npx skills add petehottelet/yautja --skill yautja --agent claude-code codex --global
```

Then ask: **“Use Yautja’s Cinematic look with the original palette, glyph callouts, timecode, and the original sound. Keep the image clean.”** The skill reuses a compatible installed runtime, checks prerequisites, and guides segmentation setup when needed.

The installer copies only `skills/yautja/`; it does not copy the converter or gallery. If the runtime is missing, the skill installs it separately from PyPI in a suitable environment. Release bundles include `yautja-skill.zip` with the matching application wheel; [offline setup](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/runtime.md#offline-install) also requires dependency wheels and, for segmentation, model caches.

### Local skill bundles and updates

Use `python -m pip install --upgrade yautja` in the original virtual environment, or retain the extra with `python -m pip install --upgrade "yautja[semantic]"`. For pipx, use `pipx upgrade yautja`. Run `yautja --version` and `yautja --doctor` afterward. Update agent instructions through their original installer and restart the agent session. Neither conversion nor a skill update silently upgrades the other component.

Release bundles include a matching wheel; offline use also requires a compatible dependency wheelhouse and separate model caches/FFmpeg. [Offline instructions](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/runtime.md#offline-install) · [Local skill builds](https://github.com/petehottelet/yautja/blob/main/docs/DEVELOPMENT.md#local-skill-bundles-and-updates).

<a id="development"></a>
## Reference, licensing and contributing

- [Every CLI option, default, alias and example](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/options.md)
- [Runnable examples](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/examples.md) and [HUD element roles](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/hud-elements.md)
- [Additional gallery detail](https://github.com/petehottelet/yautja/blob/main/docs/GALLERY.md), [Python API](https://github.com/petehottelet/yautja/blob/main/docs/API.md), [changelog](https://github.com/petehottelet/yautja/blob/main/CHANGELOG.md) and [roadmap](https://github.com/petehottelet/yautja/blob/main/docs/ROADMAP.md)
- [Development, tests and gallery regeneration](https://github.com/petehottelet/yautja/blob/main/docs/DEVELOPMENT.md) and [publishing](https://github.com/petehottelet/yautja/blob/main/docs/PUBLISHING.md)

Code and original glyph artwork are [MIT licensed](https://github.com/petehottelet/yautja/blob/main/LICENSE). Bundled Michroma and Orbitron fonts retain their [OFL licenses](https://github.com/petehottelet/yautja/blob/main/src/yautja/assets/fonts/README.md). Downloaded model weights carry their own licenses, described in the [dependency guide](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/dependencies.md). The int10h font pack is not bundled. Bring only fonts you are licensed to use through `--hud-font-file`.

Contributions are welcome through [issues](https://github.com/petehottelet/yautja/issues) and pull requests. Include a small reproducible example and verification for a changed visual behavior. Private plans and source demo footage are excluded from releases.
