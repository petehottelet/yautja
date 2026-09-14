<p align="center">
  <img src="https://raw.githubusercontent.com/petehottelet/yautja/main/assets/wordmark.svg" alt="Yautja" width="520">
</p>

<p align="center">
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

Yautja is a **sci-fi-styled image segmentation, re-skinning, and annotation skill** for creating thermal-imaging-style output.

**For entertainment purposes only.** Colors assigned during re-skinning are purely algorithmically generated, with some randomness. They do not represent measured temperatures.

Re-skin local images and video frames with cold blues, warm silhouettes, and alien HUD glyphs. Videos add an audio-reactive waveform. A small **agent skill for Claude and OpenAI Codex**, backed by an installable Python CLI and FFmpeg for video. [yautja.ai](https://yautja.ai).

[![Cinematic thermal look in the original Yautja palette, with broad warm regions, shaded cyan glyph callouts, and compact LCD timecode](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/hero.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/style-cinematic.gif)

A three-second loop from generated jungle-explorer footage, using **Cinematic** detail and the **original Yautja palette**, with texture off. The waveform follows the source audio; GIFs are silent. [View a still frame](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/poster.png). The gallery reflects the 2.x source, including the centered waveform. The older [1.0 demo with sound](https://github.com/petehottelet/yautja/releases/download/v1.0.0/yautja-demo.mp4) uses the previous renderer.

## Install the agent skill

```bash
npx skills add petehottelet/yautja --skill yautja --agent claude-code codex --global
```

Then ask: **“Use Yautja’s Cinematic look with the original palette, glyph callouts, timecode, and the original sound. Keep the image clean.”** The skill checks Python and FFmpeg before converting. Subject segmentation needs the separate semantic setup below.

The installer copies only `skills/yautja/`; it does not copy the GIF gallery or converter source. The skill installs the runtime separately. New builds produce `yautja-skill.zip`, with the matching application wheel for offline setup; the existing 1.0 release predates this layout.

Silent videos use the smoothly generated waveform from the original effect.

## When to use Yautja

- Create a sci-fi thermal-imaging look or false-color treatment for MP4, MOV, MKV, or WebM footage.
- Restyle JPEG/PNG images and export a PNG with the same anatomy-guided colors and glyph callouts.
- Segment people and selected animals, then re-skin them as warm silhouettes against cool surroundings.
- Annotate subjects with alien glyphs and add sound-driven waveform animation and optional elapsed timecode.
- Export a short preview or a complete local H.264/AAC MP4 while preserving aspect ratio and sound.

The effect uses image segmentation and synthetic color fields, with seeded variation and optional sensor grain. It does not analyze infrared sensor data or provide identity/anonymity guarantees. Model files download explicitly; ordinary conversions process footage locally.

## Quick start

Python 3.10+ is required. For videos, also install [FFmpeg](https://ffmpeg.org/download.html) with ffprobe on PATH. Images do not need FFmpeg.

Install a published release from [PyPI](https://pypi.org/project/yautja/) in an isolated environment:

```bash
python -m venv .venv-yautja
# macOS/Linux
.venv-yautja/bin/python -m pip install "yautja>=2.2,<3"
.venv-yautja/bin/python -m yautja --doctor
.venv-yautja/bin/python -m yautja "clip.mov" "clip-yautja.mp4" --timecode
```

```powershell
# Windows, after creating the venv
.venv-yautja\Scripts\python.exe -m pip install "yautja>=2.2,<3"
.venv-yautja\Scripts\python.exe -m yautja --doctor
.venv-yautja\Scripts\python.exe -m yautja "clip.mov" "clip-yautja.mp4" --timecode
```

For the segmented looks, add `[semantic]` after `yautja` in the install specification. For a local clone use `python -m pip install ".[semantic]"` in its environment; for a built wheel use its exact path. The lightweight install supports Classic mode only.

Alternatively, use `pipx install "yautja>=2.2,<3"` or `pipx install "yautja[semantic]>=2.2,<3"` for segmentation. An activated venv can instead use `python -m pip install` with those same specifications. Then run `yautja --version`, `yautja --doctor`, and `yautja "clip.mov" "clip-yautja.mp4"`. Use the same environment's Python for `python -m yautja` if the command is not on PATH. [Environment and offline setup](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/runtime.md).

Leave off `--timecode` for the alien readout alone. Sound is retained unless `--mute` is used. Existing files are protected unless you explicitly pass `--overwrite`.

### Still images

JPEG and PNG inputs save directly to PNG. With Yautja installed in the selected Python environment:

```bash
python -m yautja --doctor --media image
python -m yautja "photo.jpg" "outputs/photo-yautja.png"
# After the semantic setup below, use anatomy coloring and glyph callouts:
python -m yautja "photo.jpg" "outputs/photo-semantic.png" --thermal semantic --verbose
```

Use your virtual environment's Python. PNG output selects still-image mode automatically; FFmpeg is not needed. The same renderer supplies the chosen look, palette, optional grain/pixelation, shaded glyphs, and a static procedural waveform. All four segmented looks work with still images. `--timecode` optionally displays a static clock at `--timecode-start` (zero by default).

Images retain their aspect ratio and EXIF orientation, with a longest edge of at most 1920 pixels and no upscaling. `--max-size` changes that limit. Transparent areas are flattened onto black before coloring; output is an RGB PNG without source metadata. Animated PNG and video-only timing/audio controls are rejected. Existing output and source files are protected.

## Four thermal looks

Choose the level of detail separately from the color palette. All four examples use the **original Yautja colors**, with grain, pixelation, and scanlines off. **Click any preview for its large, 960×540 animated GIF.**

| Low Detail | Cinematic |
| --- | --- |
| [![Low Detail: broad, soft heat blobs with subdued anatomy](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/style-low-detail.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/style-low-detail.gif) | [![Cinematic: broad skin and gear patches with softened boundaries](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/style-cinematic.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/style-cinematic.gif) |
| Broad, soft silhouettes with reduced anatomical variation and an abstract background. | Broad heat patches, some skin/gear separation, and softer edges. |
| `--thermal low-detail` | `--thermal cinematic` |

| Detailed | Very Detailed |
| --- | --- |
| [![Detailed: distinct skin, clothing, and equipment regions](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/style-detailed.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/style-detailed.gif) | [![Very Detailed: visible facial features and fabric texture retained from the source](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/style-very-detailed.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/style-very-detailed.gif) |
| Distinct skin, clothing, hair, and equipment, with restrained garment shading. | Preserves visible eyes, nose, mouth, hair, and clothing texture through local source contrast. |
| `--thermal detailed` | `--thermal very-detailed` |

All four use anatomy-guided fallback when estimates are uncertain. Cinematic, Detailed, and Very Detailed reuse the same models for extra surface segmentation; they take longer as the number of people increases. Very Detailed preserves features that are visible in the input; small, blurred, or obscured faces cannot gain missing detail. Small objects, distant hands, eyewear, and overlaps can still be missed or misclassified. These are generated visual effects, not measured temperatures or material properties.

Existing commands still work: `--thermal silhouette` and `--thermal semantic` now select Low Detail, and `--thermal realistic` remains an alias for Detailed. The lightweight `--thermal classic` luminance filter remains the no-flag CLI default; it does not segment subjects.

### Presets - HotTropic

This preset uses eleven colors from black and deep blue through cyan, green, yellow, orange, red, pink, and pale pink-white. It applies **12 thermal levels with soft transitions**, dark scenery, and no HUD or sensor texture.

| HotTropic · complete preset | Thermal Spectrum · palette only |
| --- | --- |
| [![HotTropic: dark scenery, soft color bands, pink and pale highlights](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/look-thermal-spectrum-reference-v1.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/look-thermal-spectrum-reference-v1.gif) | [![Thermal Spectrum palette with ordinary Cinematic grading and HUD](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-thermal-spectrum.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-thermal-spectrum.gif) |
| `--look-preset hottropic` | `--palette thermal-spectrum` |

Use `--thermal-levels 6` or `--thermal-levels 20` for fewer or more bands, `--thermal-levels 0` for continuous color, and `--thermal-band-softness 0` for hard bands. Soft transitions and optional glow add intermediate visible colors; twelve representative levels does not limit a GIF to twelve RGB colors. Explicit options override the recipe regardless of argument order. For example, add `--hud --thermal very-detailed` to use its colors and levels with more source detail and overlays. [Exact recipe and grading controls](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/colors.md#thermal-levels-and-reference-preset).

### Create your own presets

A **preset** saves a combination of colors, thermal detail, levels, HUD styling, and effects. A **palette** is the color ramp inside it. Every existing palette now has a Cinematic starter preset, and HotTropic is a complete look. The old `thermal-spectrum-reference-v1` name still works.

List the built-ins, customize one, and save your version:

```bash
yautja --list-presets
yautja --look-preset hottropic --hud --hud-theme palette --heat-glow 0.6 --timecode --verbose --save-preset "tropic-glow.json" --preset-name "Tropic Glow"
yautja "clip.mov" "glowing.mp4" --preset-file "tropic-glow.json"
```

Saving needs no source or models. Share the JSON file with another person or agent, then override individual choices when using it, such as `--heat-glow 0.2`. Existing saves require `--overwrite`. Presets remember visual settings; choose input/output files, target figures, and encoding per conversion.

| Tropic Glow · a custom HotTropic preset |
| --- |
| [![Tropic Glow: HotTropic with coordinated HUD colors and animated heat glow](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/preset-tropic-glow.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/preset-tropic-glow.gif) |
| [Editable JSON preset](skills/yautja/assets/presets/tropic-glow.json) · [Creation, schema, and sharing guide](skills/yautja/references/presets.md) |

### Palette presets

**Yautja remains the default palette.** Each starter below selects Cinematic plus its named colors; optional timecode and subject callouts are enabled in these previews. All use identical segmentation and no added texture. Use `--palette NAME` to change only the colors within any preset. The existing encoder `--preset` option remains separate.

| Redline · red, blue, and black | Virtual Boy · red only |
| --- | --- |
| [![Redline palette: near-black shadows, vivid blue cooler regions, and dominant red warmth with restrained pink highlights](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-redline.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-redline.gif) | [![Virtual Boy palette: the scene and HUD rendered entirely in shades of red and black](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-virtualboy.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-virtualboy.gif) |
| `--look-preset redline` | `--look-preset virtualboy` |

Redline gives the movie-style red/blue/black treatment, with broad red warmth and small pink highlights. Virtual Boy uses only red and black, including the glyphs, waveform, and timecode, unless you explicitly choose custom or random HUD colors.

| Yautja · original/default | Ironbow | Green Phosphor |
| --- | --- | --- |
| [![Original Yautja palette: cool blue and cyan through yellow and red](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/style-cinematic.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/style-cinematic.gif) | [![Ironbow palette: purple, orange, and yellow-white](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-ironbow.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-ironbow.gif) | [![Green Phosphor palette: a monochrome green night-vision style](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-green-phosphor.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-green-phosphor.gif) |
| `--look-preset yautja` | `--look-preset ironbow` | `--look-preset green-phosphor` |

| Amber Phosphor | White Hot | Black Hot |
| --- | --- | --- |
| [![Amber Phosphor palette: warm amber display colors](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-amber-phosphor.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-amber-phosphor.gif) | [![White Hot palette: lighter warm regions with a white waveform and HUD](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-white-hot.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-white-hot.gif) | [![Black Hot palette: simulated warm regions appear darker](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-black-hot.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-black-hot.gif) |
| `--look-preset amber-phosphor` | `--look-preset white-hot` | `--look-preset black-hot` |

`--palette auto` also selects the original Yautja palette. Changing the level of detail never changes the palette automatically. Phosphor palettes are display styles, not a low-light recovery feature.

### Abyss and animated heat glow

**Abyss** uses deep blue-black scenery, amber-to-white-hot regions, and a subdued cyan HUD. Glow is a separate option and is off by default, including with Abyss.

| Abyss · clean | Abyss · heat glow |
| --- | --- |
| [![Abyss palette with muted cyan HUD and no glow](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/palette-abyss.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/palette-abyss.gif) | [![Abyss palette with moving glow on the hot regions](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/glow-abyss.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/glow-abyss.gif) |
| `--look-preset abyss` | `--look-preset abyss --heat-glow 0.75` |

`--hud-theme muted-cyan` makes the same subdued HUD available with any palette. Selecting `--hud-theme palette` instead matches its colors to that palette's ramp.

### Turn the HUD off

Use **`--no-hud`** for the thermal image alone. It removes the waveform, scale, glyphs, timecode, callouts, connector lines, and target markers—even when `--timecode` or `--verbose` is also supplied. Thermal style, palette, textures, and the video soundtrack stay active. HUD is on by default; `--hud` turns it back on.

| HUD on · default | HUD off |
| --- | --- |
| [![Cinematic thermal output with the full HUD and annotations](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/style-cinematic.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/style-cinematic.gif) | [![Cinematic thermal output with every HUD overlay hidden](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/hud-off.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/hud-off.gif) |
| Default HUD, with `--verbose --timecode` for annotations and clock | `--no-hud` |

```bash
python -m yautja "clip.mov" "thermal-only.mp4" --thermal cinematic --no-hud
python -m yautja "photo.jpg" "thermal-only.png" --palette green-phosphor --no-hud
```

### HUD colors, custom palettes, and random colors

White Hot uses a **white waveform and HUD** by default, Black Hot uses black, Abyss uses muted cyan, and other palettes retain the standard red/cyan HUD. Use **`--hud-theme palette`** to match the waveform, glyphs, clock, callouts, and scale to the selected palette; White Hot keeps white ink and Black Hot keeps black ink in this mode too. Custom and random HUD themes remain available. These controls work with images and videos and every thermal look.

| Green Phosphor · matched HUD | Ironbow · matched HUD |
| --- | --- |
| [![Green Phosphor with matching green waveform, readout, timecode, and callouts](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/colors-matched-green.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/colors-matched-green.gif) | [![Ironbow with coordinated orange and purple HUD colors](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/colors-matched-ironbow.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/colors-matched-ironbow.gif) |
| `--palette green-phosphor --hud-theme palette` | `--palette ironbow --hud-theme palette` |

| Custom thermal + HUD colors | Random thermal + HUD colors |
| --- | --- |
| [![Custom navy, teal, and gold thermal colors with independently colored HUD elements](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/colors-custom.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/colors-custom.gif) | [![A seeded random thermal palette and independently randomized HUD colors, stable across frames](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/colors-random.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/colors-random.gif) |
| [Exact custom settings](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/colors.md#custom-hud-elements) | `--random-colors --seed 137` |

**Custom thermal colors:** use `--palette custom --palette-colors "#000000,#0033ff,#ff2200,#fff0c0"`. Supply 2–16 hex colors, cold to hot, separated by commas or spaces. Stops are evenly spaced. Three- and six-digit RGB hex values work; quote the string.

**Custom HUD colors:** use `--hud-theme custom --hud-colors "waveform=#44ff88,timecode=#ddffee,callouts=#88ccff"`. Set any of these independently: `waveform`, `waveform-axis`, `waveform-ticks`, `waveform-glyphs`, `readout`, `timecode`, `callouts`, `leaders`, and `markers`. Omitted elements keep their standard colors. Custom ink supports black and dark colors as well as bright ones.

**Random colors:** `--random-colors` randomizes both the thermal palette and every HUD element. Use `--palette random` or `--hud-theme random` for just one. A different `--seed` produces a new set; the same seed repeats it. Colors stay fixed throughout the clip. The JSON report includes the resolved hex values so a set can be reused.

See the [color controls guide](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/colors.md) for full commands, element descriptions, and how custom ink interacts with glow and analog effects.

### Grain and chunky pixels

Every effect is **optional and off by default**. Add grain, chunky pixels, CRT lines, or VHS styling independently, or combine them. The heat field, glyph selection, and audio behavior stay the same.

| Clean · default | Grain only | Chunky pixels only |
| --- | --- | --- |
| [![Clean Cinematic output without added texture](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/style-cinematic.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/style-cinematic.gif) | [![Fine animated grain without pixelation or scanlines](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-grain.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-grain.gif) | [![Chunky pixelation without added grain or scanlines](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-pixelation.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-pixelation.gif) |
| No texture flags | `--grain 0.06` | `--pixelation 80` |

| CRT Lines only | Sensor texture · combined preset |
| --- | --- |
| [![Horizontal CRT lines across the picture and HUD](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-crt-lines.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-crt-lines.gif) | [![Combined sensor texture with grain, sensor pixels, and CRT lines](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-sensor-texture.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-sensor-texture.gif) |
| `--crt-lines` | `--sensor-texture` |

| VHS only | VHS + CRT Lines |
| --- | --- |
| [![VHS styling with softened color, chroma bleed, horizontal wobble, tape noise, and occasional tracking defects](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-vhs.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-vhs.gif) | [![Combined VHS analog defects and horizontal CRT lines](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-vhs-crt.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-vhs-crt.gif) |
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

All comparison GIFs use the same three-second slice at 12 fps, with the original audio driving the waveform. Embedded previews are 480×270; click one to open its **960×540 large version**, rendered with HUD and textures at that size. The hero uses 640×360. They compare styling choices, not model accuracy. The source footage stays local.

### Heat glow, vertical CRT lines, and adjustable trails

**Heat glow works with every palette.** Set `--heat-glow` from **0–1** (default 0), and `--heat-glow-speed` from **0–5** (default 1). A speed of 0 freezes the glow pattern. It brightens and diffuses hot regions before the HUD is added; inverted Black Hot uses dark diffusion. The existing `--glow` setting still controls HUD bloom independently.

| Original palette · heat glow | Green Phosphor · heat glow |
| --- | --- |
| [![Original Yautja palette with moving heat glow](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-heat-glow.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-heat-glow.gif) | [![Green Phosphor with palette-matched HUD and heat glow](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/glow-green.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/glow-green.gif) |
| `--heat-glow 0.75` | `--palette green-phosphor --hud-theme palette --heat-glow 0.75` |

**Vertical CRT lines** can be enabled independently or together with horizontal lines. `--crt-strength` sets their darkness from **0–1** (default 0.12); 0 hides them. These stripes affect the complete picture, including the HUD.

[![Vertical CRT lines at strength 0.25](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-crt-vertical.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-crt-vertical.gif)

`--crt-vertical-lines --crt-strength 0.25` · add `--crt-lines` for both directions.

**Motion blur** adds temporal frame persistence: higher values leave longer trails on moving subjects and HUD details. It resets at detected cuts and needs consecutive video frames; stills have no motion trail. **CRT bleed** adds horizontal phosphor smear to both images and videos. Both strengths range from **0–1**, default to 0, and leave the soundtrack unchanged.

| Softer motion trails | Stronger motion trails |
| --- | --- |
| [![Softer temporal motion trails](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-motion-soft.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-motion-soft.gif) | [![Stronger temporal motion trails](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-motion-strong.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-motion-strong.gif) |
| `--motion-blur 0.35` | `--motion-blur 0.85` |

| Softer CRT bleed | Stronger CRT bleed |
| --- | --- |
| [![Softer horizontal CRT phosphor bleed](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-bleed-soft.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-bleed-soft.gif) | [![Stronger horizontal CRT phosphor bleed](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/texture-bleed-strong.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/texture-bleed-strong.gif) |
| `--crt-bleed 0.3` | `--crt-bleed 0.85` |

All of these controls are independent of VHS, grain, pixelation, and the sensor-texture preset. Click each preview for the large animated GIF.

### Rorschach waveforms

For a thick, full-height, mirrored inkblot display, choose one of three waveform transformations. These examples use **Redline**, with `--wave-width 0.14 --wave-height 1 --wave-gain 4` (extra audio gain for this quiet clip). The occupied width follows the soundtrack; GIFs are silent.

| Filled · broad connected lobes | Split · separated inkblots | Hollow · dark interior pockets |
| --- | --- | --- |
| [![Filled mirrored Rorschach waveform spanning the image height](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/waveform-rorschach.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/waveform-rorschach.gif) | [![Separated mirrored inkblots responding to the soundtrack](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/waveform-rorschach-split.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/waveform-rorschach-split.gif) | [![Hollow mirrored waveform lobes with dark pockets](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/waveform-rorschach-hollow.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/waveform-rorschach-hollow.gif) |
| `--wave-style rorschach` | `--wave-style rorschach-split` | `--wave-style rorschach-hollow` |

`--wave-width` sets maximum width as a fraction of the frame (0.02–0.3, default 0.12); `--wave-height` sets height (0.1–1, default 0.96). `--wave-detail` goes from broad and smooth at 0 to sharper edge spikes and more intricate lobes at 1 (default 0.6). The shapes keep a thick mirrored core, with pointed, irregular edges driven by short peaks and troughs in the waveform. Quiet ambience is amplified for visibility, and louder audio fills more of the column. Silent pauses within audible tracks stay empty; the existing fallback for an absent or entirely silent soundtrack remains procedural.

The original `--wave-style trace` stays the default. Rorschach replaces the left trace, scale, and flanking glyph rows. It uses the existing waveform color, works with all HUD themes, and leaves timecode, callouts, and selected targets intact. Combine `--crt-bleed 0.3` for softer edges or `--motion-blur 0.4` for video trails. Each preview links to its large animated GIF.

### Target shapes

Choose `--target-shape` independently of colors, lock timing, flash, outline, blur, and transparency. The original `triangle` remains the default. Triangle dots, the square center dot, and Vector Lock’s center diamond appear on lock and reset when the target is lost. Vector Lock replaces the old iron-sights design; `iron-sights` remains an alias for existing commands and saved presets.

| Triangle + three lock dots | Circular crosshair |
| --- | --- |
| [![Triangle + three lock dots animated target](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-shape-triangle-dots.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-shape-triangle-dots.gif) | [![Circular crosshair animated target](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-shape-crosshair.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-shape-crosshair.gif) |
| `--target-shape triangle-dots` | `--target-shape crosshair` |

| Vector Lock | Square brackets |
| --- | --- |
| [![Vector Lock: angular guards, inward chevrons, and a center lock diamond](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-shape-iron-sights.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-shape-iron-sights.gif) | [![Square brackets animated target](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-shape-square.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-shape-square.gif) |
| `--target-shape vector-lock` | `--target-shape square` |

| Square + lock dot | Square + cross |
| --- | --- |
| [![Square + lock dot animated target](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-shape-square-dot.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-shape-square-dot.gif) | [![Square + cross animated target](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-shape-square-cross.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-shape-square-cross.gif) |
| `--target-shape square-dot` | `--target-shape square-cross` |

| Square + graduated cross | Square + diagonal marks |
| --- | --- |
| [![Square + graduated cross animated target](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-shape-square-mil.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-shape-square-mil.gif) | [![Square + diagonal marks animated target](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-shape-square-x.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-shape-square-x.gif) |
| `--target-shape square-mil` | `--target-shape square-x` |

Click any preview for its large animated GIF. [Selection, target colors, and effects](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/targets.md#target-animation-and-color).

### Choose a figure and add a target

Scan a clip or still to get a **shot-by-shot figure list**, thumbnails, and reusable IDs. Scanning needs the semantic setup below. Open the generated contact sheet, choose an ID, then render:

```bash
yautja "clip.mov" "figures.json" --list-figures
# Open figures.html; select an ID from that scan.
yautja "clip.mov" "targeted.mp4" --thermal cinematic --figures "figures.json" --target S001-F003
```

The saved catalog belongs to the exact source file. Reuse it for different palettes, resolutions, frame rates, or trims; select additional shot IDs explicitly when a figure reappears after a cut. IDs are detected tracks, and detection can miss or swap figures during occlusion. Inspect the contact sheet and output. `targets_seen` and `targets_unseen` in the report confirm which selections appeared.

| Assemble and flash · red/white | Abyss · steady target + vertical CRT | Custom target colors |
| --- | --- | --- |
| [![Three blades assemble around a selected explorer and flash red and white](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-lock.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-lock.gif) | [![Abyss with steady red target, vertical CRT lines, and heat glow](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-abyss-steady.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-abyss-steady.gif) | [![Green palette with a custom teal and pale mint target](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-custom.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-custom.gif) |
| Default target animation | `--palette abyss --no-target-flash --crt-vertical-lines --crt-strength 0.25 --heat-glow 0.65` | `--palette green-phosphor --hud-theme palette --target-colors "#31d7bb,#d6fff3" --target-acquire 0.45 --crt-bleed 0.4` |

These target examples show seconds 0–3.25 of the source, selecting the foreground explorer separately in the first two shots. The triangle contracts into a compact marker at the figure's center, with solid-color sides and narrow, clear gaps at all three corners. It assembles in **0.8 seconds**, lands red, then flashes red/white at **1.5 cycles per second**. Set `--target-acquire`, `--target-scale`, and `--target-flash-rate` to change timing and size; scale 1 uses the compact reticle. `--no-target-flash` keeps the assembly and holds the primary color; equal primary/flash colors work too. White Hot uses white and Black Hot uses black for both target states unless colors are overridden. Stills display the assembled triangle immediately.

Set `--target-colors "#ff302b,#ffffff"` for independent primary/flash colors, or use the `target` and `target-flash` keys with custom HUD colors. Palette-matched and random HUD themes also color targets. `--no-hud` hides them along with every other overlay. [All target controls, bounds, scan details, and effect options](skills/yautja/references/targets.md).

### Reticle stroke and HUD blur

Add an optional outline with `--target-stroke 5`. Choose one outline color or a landing/flash pair with `--target-stroke-colors "#660b12,#687a8d"`; omit the colors to use darker shades of the current target colors. The outline is drawn inward, keeping the corner gaps open. It is off by default (`--target-stroke 0`); the bare flag uses width 2 and the range is 0–12.

`--hud-blur 3` softens all HUD artwork. Use `--hud-blur-elements "waveform=6,target=4,timecode=0"` for independent overrides: omitted elements inherit the shared amount, and explicit 0 keeps an element sharp. Every radius is 0–20, with 0 as the default. Blur and stroke widths are pixels at a **1080px short edge**, scaled with output size. HUD blur affects the artwork before it is placed on the scene, leaving the underlying thermal image sharp.

| Reticle outline · separate flash colors | Target blur only |
| --- | --- |
| [![Reticle with an optional colored outline](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-outline.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-outline.gif) | [![Soft target with crisp waveform, callouts, and readout](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-blur.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-blur.gif) |
| `--target-stroke 5 --target-stroke-colors "#660b12,#687a8d"` | `--hud-blur-elements "target=8"` |

| Matched red · waveform + reticle blur | Shared HUD blur · sharp timecode |
| --- | --- |
| [![Blurred red Rorschach waveform and reticle with a crisp matching timecode](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-wave-blur.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-wave-blur.gif) | [![HUD softened by element while its timecode remains sharp](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-hud-blur.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-hud-blur.gif) |
| `--wave-style rorschach --wave-width 0.14 --wave-height 1 --hud-blur-elements "waveform=6,target=6"` | `--hud-blur 3 --hud-blur-elements "waveform=6,target=5,timecode=0"` |

Click any preview for the large GIF. These comparisons use the same 0–3.25-second clip and target selections as the examples above. Blur keys are `waveform`, `waveform-axis`, `waveform-ticks`, `waveform-glyphs`, `readout`, `timecode`, `callouts`, `leaders`, `markers`, and `target`. Target blur applies to both flash states. These controls work for images and videos, alongside HUD bloom, heat glow, and CRT/VHS effects. `--no-hud` hides them all. [Full controls and examples](skills/yautja/references/targets.md#reticle-stroke-and-independent-hud-blur).

The matched-red Rorschach example additionally uses `--hud-theme custom --hud-colors "waveform=#ff302b,timecode=#ff302b" --target-colors "#ff302b,#ff302b"`. Both reticle states use the same red. Custom HUD colors use alpha compositing, avoiding the pink shift that screen blending can introduce over a blue scene.

### HUD transparency

Set `--hud-opacity 0.5` for half-strength HUD artwork, or `--hud-opacity-elements "waveform=0.3,target=0.7,timecode=0.9"` for separate values. **0 is invisible; 1 keeps full existing visibility** (the default). Omitted elements inherit the shared opacity; explicit values override it. Blur and opacity are independent, and both work for stills and videos.

| Entire HUD · opacity 0.5 | Independent opacity · waveform / target / timecode |
| --- | --- |
| [![All HUD artwork at half opacity](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-opacity.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-opacity.gif) | [![Red waveform at 0.3 opacity, target at 0.7, and timecode at 0.9](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/target-opacity-elements.gif)](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/large/target-opacity-elements.gif) |
| `--hud-opacity 0.5` | `--hud-opacity-elements "waveform=0.3,target=0.7,timecode=0.9"` with the matched red Rorschach colors and shape above |

Opacity keys cover all HUD elements: `waveform`, `waveform-axis`, `waveform-ticks`, `waveform-glyphs`, `readout`, `timecode`, `callouts`, `leaders`, `markers`, `target`, and `target-flash`. A `target` override controls both states unless `target-flash` is explicitly set. Reticle outlines and glow follow their element's opacity. `--no-hud` still hides everything. Click either GIF for the large version. [Detailed transparency controls](skills/yautja/references/targets.md#hud-transparency).

### Segmentation setup

Install the `semantic` extra in the same environment, then explicitly download the pinned models once:

```bash
python -m pip install "yautja[semantic]>=2.2,<3"
python -m yautja --download-models
python -m yautja --doctor --thermal cinematic --device cuda
python -m yautja "clip.mov" "outputs/clip-cinematic.mp4" --thermal cinematic --verbose --timecode
```

Use your environment's Python. Grounding DINO, SAM 2.1, and ViTPose are shared by all four looks, and conversions use cached weights only. `--device auto` chooses available CUDA or CPU; CPU is slower. Start with a short `--duration 5` sample. See [setup, controls, and limitations](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/semantic.md) and the [isolated GPU setup](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/semantic.md#isolated-cuda-environment-on-windows).

`--sensor-resolution 160` increases heat-field abstraction, `--warm-objects "person,dog,bird"` selects warm categories, and `--hot-objects "fire"` explicitly adds an artistic hot category. Reports include the actual device, precision, timings, model revisions, and resolved effects. Full precision is the default; `--precision bf16` is experimental. [Earlier CPU/CUDA validation](https://github.com/petehottelet/yautja/blob/main/docs/performance-validation.md).

Yautja's code is MIT; the separately installed models retain their Apache-2.0 licenses. Model weights, runtime binaries, and gallery GIFs are excluded from the portable skill archive. [Dependency licensing details](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/dependencies.md).

## Local skill bundles and updates

From a developer checkout, build the wheel first, then build or install the small skill:

```bash
python -m tools.prepare_release
python -m tools.build_skill_bundle --zip dist/yautja-skill.zip
python -m tools.build_skill_bundle --install both
```

Choose `--install claude`, `--install codex`, or `--install both`. Codex respects `CODEX_HOME`; Claude uses `~/.claude/skills/yautja`. Existing installs require `--replace`, which updates known skill files and removes obsolete bundled runtime files/wheels while keeping personal files and environments. New bundles contain instructions, references, the MIT license and one application wheel. Dependencies, FFmpeg, models and gallery media are separate. See the [complete offline wheelhouse procedure](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/runtime.md#offline-install).

Use the original skill installer to update instructions. Upgrade the runtime in its original environment: `pipx runpip yautja install --upgrade "yautja>=2.2,<3"`, or that venv's `python -m pip install --upgrade "yautja>=2.2,<3"` (retain the semantic extra when used). Verify the compatible version and rerun doctor before converting; restart the agent session after updating the skill. Conversion never updates either component automatically. See the [changelog](https://github.com/petehottelet/yautja/blob/main/CHANGELOG.md) and [release instructions](https://github.com/petehottelet/yautja/blob/main/docs/PUBLISHING.md).

## Useful controls

| Option | Behavior |
| --- | --- |
| `--timecode` / `--no-timecode` | LCD-style elapsed `HH:MM:SS.mmm`, on/off; default off |
| `--timecode-start 90` | Begin the displayed clock at 00:01:30.000 |
| `--waveform auto` | Use audio, or procedural motion for absent/silent audio |
| `--waveform procedural` | Force generated motion, keeping the soundtrack |
| `--waveform audio` | Require an audio track; silent samples produce a flat trace |
| `--wave-gain 1.5` | Increase audio waveform amplitude |
| `--wave-window 0.6` | Seconds represented along the vertical trace |
| `--audio-stream 1` | Use the second audio track for analysis and playback |
| `--mute` | Remove sound without disabling audio analysis |
| `--start 10 --duration 5` | Convert a five-second trim starting at ten seconds |
| `--max-size 1280 --fps 30` | Limit resolution and set output frame rate |
| `--grain 0.02` | Add fine grain independently; 0 disables |
| `--pixelation 80` | Add chunky pixels independently; smaller grids make larger blocks |
| `--crt-lines` / `--no-crt-lines` | Toggle horizontal CRT lines, including across the HUD |
| `--vhs` / `--no-vhs` | Toggle analog tape styling and defects |
| `--sensor-texture` / `--no-sensor-texture` | Toggle the combined preset; individual effects override its defaults |
| `--palette green-phosphor` | Choose a palette independently of thermal detail |
| `--no-hud` / `--hud` | Hide or restore the entire HUD; keep thermal effects and sound |
| `--hud-theme palette` | Match every HUD element to the thermal palette |
| `--palette custom --palette-colors "#000,#03f,#f20"` | Define an evenly spaced cold-to-hot hex ramp |
| `--hud-theme custom --hud-colors "waveform=#0f8,timecode=#fff"` | Assign colors to individual HUD elements |
| `--random-colors` | Randomize both the thermal palette and HUD colors |
| `--glow 0.4` | Restrain HUD bloom independently of sensor texture |
| `--seed 123` | Reproducible colors, generated waveform, grain, and callout glyph combinations |

Video output is H.264/AAC MP4, CRF 18, source aspect ratio and orientation, at most 1920 pixels on the longest edge, and source-average constant frame rate capped at 60 fps. Image output is RGB PNG. It handles local JPEG/PNG stills and FFmpeg-decodable videos; protected, corrupt, or unsupported media cannot be guaranteed. Colors are simulated and do not measure temperature.

## Development

```bash
python -m pip install -e ".[dev,tracking]"
python -m tools.prepare_release
python -m unittest discover -s tests -v
python -m tools.verify_install
```

Tests include JPEG/PNG conversion without FFmpeg, EXIF orientation, transparency, deterministic stills, output protection, and real FFmpeg conversions with audio timing, timecode, and aspect handling.

Semantic heat and tracking tests use deterministic masks and optional OpenCV, without downloading models. They check cool backgrounds, texture suppression, tracking and fading, scene cuts, and CLI validation. A real model render should also be checked when changing segmentation dependencies.

CI runs the full test suite and fresh installed-wheel/extracted-skill image and video conversions on Windows, macOS, and Linux, with Python 3.10/3.11 coverage. Offline install checks disable package-index access and pip caches after preparing a complete dependency wheelhouse. Builds compare repeated wheel/bundle bytes and rebuild the wheel from the sdist. Build before running tests that inspect the release bundle.

Release versions live in `pyproject.toml`. The release workflow prepares and validates every artifact before its gated PyPI publish step. [Publishing and maintainer setup](https://github.com/petehottelet/yautja/blob/main/docs/PUBLISHING.md), [limited Python API](https://github.com/petehottelet/yautja/blob/main/docs/API.md), and [future improvements](https://github.com/petehottelet/yautja/blob/main/docs/ROADMAP.md).

For repeatable local performance comparisons, run these sequentially with each environment's Python. Use the same input and settings; the runner creates a new output directory for every invocation, records a source hash and exact commands, and verifies decoded frames and audio timing. It requires cached models and never downloads them.

```bash
python -m tools.benchmark "clip.mov" --device cpu --runs 2
python -m tools.benchmark "clip.mov" --device cuda --runs 2
python -m tools.benchmark "clip.mov" --device cuda --precision bf16 --runs 2
python -m tools.compare_precision "clip.mov" --times 0 2 4 6 8
```

Every benchmark run starts a fresh process and reloads models. Operating-system file caches are uncontrolled, so a first run is not necessarily cold. `compare_precision.py` compares sampled mask agreement; it does not establish detection accuracy. These developer tools stay in the repository, outside the portable skill manifest.

<details>
<summary>Regenerate the labelled README GIF gallery</summary>

The generated demo source is kept locally in the ignored `00_project_files/` folder and is not included in a clone. With the semantic environment and cached models ready:

```bash
yautja "00_project_files/create_a_video_of_explorers_wa.mp4" "outputs/figures.json" --list-figures --fps 12 --max-size 640 --device cuda
# Inspect outputs/figures.html and use the IDs from your scan.
python -m tools.build_gallery "00_project_files/create_a_video_of_explorers_wa.mp4" --device cuda --figures outputs/figures.json --target S001-F003,S002-F002,S003-F002 --overwrite
python -m tools.build_gallery "00_project_files/create_a_video_of_explorers_wa.mp4" --device cuda --figures outputs/figures.json --target S001-F003,S002-F002 --start 0 --duration 3.25 --only target-lock target-abyss-steady target-custom --overwrite
python -m tools.build_gallery "00_project_files/create_a_video_of_explorers_wa.mp4" --device cuda --wave-gain 4 --only waveform-rorschach waveform-rorschach-split waveform-rorschach-hollow --overwrite
```

The first gallery command processes seconds 0.5–3.5 once, shares tracked masks and heat fields across matched variants, and exports all labelled examples into `assets/examples/`, with larger versions in `assets/examples/large/`. Add `--only colors-matched-green texture-crt-lines` to regenerate selected previews and their large versions. The second gallery command gives target acquisition and flashing a longer first shot (seconds 0–3.25); the third raises audio gain for the Rorschach comparisons. It applies texture at the final display size so GIF downsampling does not erase grain or scanlines. It verifies animation timing before replacing the GIFs. The source and temporary decoded frames are never included in the skill archive. The helper is for short SDR gallery clips; use the main converter for normal images and videos.

</details>
