# Runnable examples

Use an activated environment with Yautja installed. Replace `photo.jpg` and `clip.mov` with your own files. Videos need FFmpeg/ffprobe. Recipes marked **Segmented** also need `yautja[semantic]` and the one-time [model setup](#models-setup). Output names are distinct; existing files are protected unless `--overwrite` is explicit.

Each block is a complete command. The verifier runs the same blocks with generated media and checks the reports; `--models` adds cached-model recipes. Setup downloads remain explicit manual operations. Parameters, aliases and defaults are in the [option reference](options.md).

## Inspect the runtime

<a id="inspect"></a>

Run these in the environment where Yautja is installed. Image diagnosis needs no FFmpeg.

<!-- example: {"id": "inspect", "tier": "classic", "checks": {}} -->
```bash
yautja --help
yautja --version
yautja --doctor --media image
```

## Download the segmented models

<a id="models-setup"></a>

After `python -m pip install "yautja[semantic]"`, download once. This setup operation uses the network; ordinary conversions only read cached models.

<!-- example: {"id": "models-setup", "tier": "setup", "checks": {}} -->
```bash
yautja --download-models
```

## A lightweight still

<a id="lightweight"></a>

Use your own JPEG or PNG. This runs without segmentation or FFmpeg.

<!-- example: {"id": "lightweight", "tier": "classic", "checks": {"media_type": "image"}} -->
```bash
yautja "photo.jpg" "classic.png" --thermal classic --palette costa-rica --max-size 960 --seed 42 --glow 0.4
```

## The Yautja hero look

<a id="hero"></a>

**Segmented.** Complete presets require the segmented setup. Use a short video first; omit the duration for the full clip.

<!-- example: {"id": "hero", "tier": "models", "checks": {"look_preset": "yautja"}} -->
```bash
yautja "clip.mov" "hero.mp4" --stylepreset yautja --verbose --timecode --duration 4
```

## Palette substitution

<a id="palette-only"></a>

Change only the palette while keeping the thermal mode and other settings. The first example selects a built-in ramp; the second authors a custom ramp.

<!-- example: {"id": "palette-only", "tier": "classic", "checks": {}} -->
```bash
yautja "photo.jpg" "palette.png" --thermal classic --palette green-phosphor --hud-theme palette
yautja "photo.jpg" "custom-palette.png" --palette custom --palette-colors "#000000,#0033ff,#ff2200,#fff0c0"
```

## Thermal field grading

<a id="thermal-grade"></a>

Levels enable grading. White point must exceed black point by at least 0.01. Band softness changes transitions; thermal softness smooths the heat field.

<!-- example: {"id": "thermal-grade", "tier": "classic", "checks": {}} -->
```bash
yautja "photo.jpg" "graded.png" --thermal-levels 12 --thermal-band-softness 0.6 --thermal-black-point 0.1 --thermal-white-point 0.9 --thermal-gamma 1.1 --thermal-softness 1.5
```

## Grain and display pixels

<a id="sensor"></a>

Explicit grain, pixelation and line switches override the sensor-texture defaults. Detection resolution is a different control.

<!-- example: {"id": "sensor", "tier": "classic", "checks": {}} -->
```bash
yautja "photo.jpg" "sensor.png" --sensor-texture --sensor-resolution 256 --grain 0.025 --pixelation 96 --no-crt-lines
```

## Analog texture and heat bloom

<a id="crt"></a>

These are independent whole-picture effects. Motion blur needs successive video frames; heat glow colors synthetic hot areas.

<!-- example: {"id": "crt", "tier": "classic", "checks": {}} -->
```bash
yautja "clip.mov" "crt.mp4" --duration 1 --crt-lines --crt-vertical-lines --crt-grid --crt-crosshatch --crt-strength 0.15 --crt-bleed 0.2 --vhs --motion-blur 0.25 --heat-glow 0.6 --heat-glow-speed 1.2
```

## A clean export without HUD

<a id="clean"></a>

No HUD hides every overlay, including targets, code and device backplates. The selected palette, picture effects and soundtrack remain independent.

<!-- example: {"id": "clean", "tier": "classic", "checks": {}} -->
```bash
yautja "clip.mov" "clean.mp4" --duration 1 --no-hud --no-crt-lines --no-crt-grid --no-crt-crosshatch --no-crt-vertical-lines --no-vhs --grain 0 --pixelation 0
```

## A vivid red vocoder

<a id="vocoder"></a>

Style selects shape, display selects the device, HUD color supplies ink, and neon lights active cells. Burgundy-to-black idle cells do not emit light.

<!-- example: {"id": "vocoder", "tier": "classic", "checks": {"wave_display": "led"}} -->
```bash
yautja "clip.mov" "vocoder.mp4" --duration 1 --wave-style digital-circuit --wave-display led --wave-backlight 0.2 --wave-width 0.15 --wave-height 0.96 --wave-detail 0.7 --waveform audio --wave-window 0.6 --wave-gain 1.5 --hud-theme custom --hud-colors "waveform=#ff302b" --neon
```

## LED on an inkblot waveform

<a id="led-inkblot"></a>

The same device works with all seven shapes. Trace retains its plain axis, ticks and glyph readouts.

<!-- example: {"id": "led-inkblot", "tier": "classic", "checks": {"wave_display": "led"}} -->
```bash
yautja "photo.jpg" "led-inkblot.png" --wave-style rorschach --wave-display led --wave-backlight 0.3
```

## Style HUD elements independently

<a id="hud-ink"></a>

A supplied element map replaces the inherited map. Unlisted keys use the corresponding global setting; explicit zero remains zero. See [the role table](hud-elements.md).

<!-- example: {"id": "hud-ink", "tier": "classic", "checks": {}} -->
```bash
yautja "photo.jpg" "hud-ink.png" --hud --timecode --timecode-start 90 --hud-theme custom --hud-colors "waveform=#ff302b,timecode=#ffffff" --hud-blur 1 --hud-blur-elements "waveform=3,timecode=0" --hud-opacity 0.8 --hud-opacity-elements "waveform=0.5,timecode=1"
yautja "photo.jpg" "random.png" --random-colors --seed 137
```

## Neon light and precise per-element tuning

<a id="neon"></a>

Neon replaces standard HUD bloom. Zero per-element neon disables its glow treatment, while opacity controls the actual artwork and halo together.

<!-- example: {"id": "neon", "tier": "classic", "checks": {}} -->
```bash
yautja "photo.jpg" "neon.png" --neon --neon-intensity 0.9 --neon-spread 0.8 --neon-core-whiten 0.2 --neon-flicker 0.1 --neon-elements "waveform=1.2,timecode=0" --timecode
```

## Persistent Focus targeting

<a id="focus"></a>

**Segmented.** One target glides between subjects. Hold is dwell time, response is motion smoothing, and fill is independent of shape. No catalog is needed.

<!-- example: {"id": "focus", "tier": "models", "checks": {"target_fill": "stroked"}} -->
```bash
yautja "clip.mov" "focus.mp4" --stylepreset focus --duration 4 --target-mode cycle --target-motion persistent --target-hold 2 --target-response 0.5 --target-shape hexagon --target-fill stroked
```

## A rotating geodesic sphere

<a id="grid"></a>

Grid rotation has its own clock. Speed zero freezes light pulses while rotation can continue; a still freezes both.

<!-- example: {"id": "grid", "tier": "classic", "checks": {}} -->
```bash
yautja "photo.jpg" "grid.png" --geo-grid --geo-grid-projection sphere --geo-grid-scale 160 --geo-grid-jitter 0.65 --geo-grid-speed 1 --geo-grid-rotation 0.6 --geo-grid-center-fade 0.96 --geo-grid-width 2.2 --geo-grid-breaks 0.7 --geo-grid-details
```

## Partial holographic outlines

<a id="hologram"></a>

**Segmented.** All visible subjects receive subject outlines. Optional yellow patches are decorative, selected-mask graphics; they do not assess actual weak points.

<!-- example: {"id": "hologram", "tier": "models", "checks": {"outline_shine": 0.75}} -->
```bash
yautja "photo.jpg" "hologram.png" --thermal low-detail --subject-outline --outline-style holographic --outline-width 6.4 --outline-coverage 0.35 --outline-arcs 5 --outline-speed 1.35 --outline-shine 0.75 --target-mode cycle --target-weak-spots
```

## Relic ornaments and code behind figures

<a id="relic"></a>

**Segmented.** Broken triangles spawn on the selected figure, rise, then collapse and spin away. Code retains its glyph size and stream count inside the figure-wide column.

<!-- example: {"id": "relic", "tier": "models", "checks": {"look_preset": "relic"}} -->
```bash
yautja "clip.mov" "relic.mp4" --stylepreset relic --duration 4 --target-motif triangles --target-motif-count 7 --target-motif-scale 1 --target-motif-speed 1 --target-motif-breaks 0.7 --code-layer behind
```

## Murphy with a thinking caption

<a id="murphy"></a>

**Segmented.** Automatic targeting works without a figure catalog. Scale affects the box; caption scale affects only the text. The underscore cursor blinks in video.

<!-- example: {"id": "murphy", "tier": "models", "checks": {"target_label": "SEARCHING"}} -->
```bash
yautja "clip.mov" "murphy.mp4" --stylepreset murphy --duration 4 --target-mode auto --target-outline --target-label "SEARCHING" --target-label-scale 2.2 --target-cursor --hud-font orbitron-medium --target-scale 1.25
```

## Fremont vehicle analysis

<a id="fremont"></a>

**Segmented.** Detected categories drive abbreviated text; numeric telemetry is decorative. The analysis disk is independent of geometric reticles and never zooms.

<!-- example: {"id": "fremont", "tier": "models", "checks": {"analysis_target": true}} -->
```bash
yautja "clip.mov" "fremont.mp4" --stylepreset fremont --duration 4 --warm-objects "person,car,motorcycle,bicycle,bus,truck" --analysis --analysis-speed 1.5 --analysis-blink-rate 2 --analysis-margin 0.05 --analysis-outline-width 5 --analysis-target --analysis-target-size 0.4 --analysis-target-response 0.6
```

## Netrunner glyphs, code and label spacing

<a id="netrunner"></a>

**Segmented.** Yautja, Cyber and Tech are independent glyph choices. Tech uses the selected readable font; the timecode always stays numeric.

<!-- example: {"id": "netrunner", "tier": "models", "checks": {"hud_glyphs": "cyber"}} -->
```bash
yautja "clip.mov" "netrunner.mp4" --stylepreset netrunner --duration 4 --HUDglyphs cyber --subject-code --subject-labels --subject-head-gap 30 --subject-title-gap 20 --subject-caret-scale 1.35 --code-size 22 --code-speed 1.2 --code-density 0.95
```

## Retain source detail under a tint

<a id="source-grade"></a>

Source mode preserves the original scene. Exposure is a brightness multiplier, and highlight retention restores pale highlights in the tinted portion.

<!-- example: {"id": "source-grade", "tier": "classic", "checks": {}} -->
```bash
yautja "photo.jpg" "source-grade.png" --scene-mode source --scene-tint "#8395E6" --scene-tint-strength 0.28 --scene-exposure 0.82 --scene-highlights 0.15
```

## Detection and mask stability

<a id="tracking"></a>

**Segmented.** Semantic runtime settings are not saved in visual presets. Start with automatic device choice and FP32. BF16 is an optional CUDA experiment, explained in the [runtime guide](runtime.md).

<!-- example: {"id": "tracking", "tier": "models", "checks": {}} -->
```bash
yautja "photo.jpg" "tracked.png" --thermal low-detail --subject-outline --device auto --precision fp32 --warm-objects "person,dog" --hot-objects "fire" --confidence 0.3 --detect-interval 0.5 --mask-stability 0.18 --mask-min-region 0.02
```

## Scan a figure catalog

<a id="catalog-scan"></a>

**Segmented.** Run this on your own clip, then open figures.html and replace the sample ID in the next recipe with an ID from that scan. A catalog belongs to that exact source file.

<!-- example: {"id": "catalog-scan", "tier": "models", "checks": {}} -->
```bash
yautja "clip.mov" "figures.json" --list-figures --duration 1 --fps 12
```

## Target a catalog figure

<a id="catalog-target"></a>

After [scanning](#catalog-scan), substitute a real ID shown in figures.html for S001-F001. Explicit targets can be rendered in Classic without loading segmentation. The verification fixture supplies a matching one-figure catalog.

<!-- example: {"id": "catalog-target", "tier": "classic", "checks": {}} -->
```bash
yautja "clip.mov" "target.mp4" --duration 1 --figures "figures.json" --target S001-F001 --target-shape triangle-dots --target-colors "#ff302b,#ffffff" --target-acquire 0.8 --target-flash --target-flash-rate 1.5 --target-scale 1 --target-stroke 2 --target-stroke-colors "#660b12,#687a8d"
```

## Save a portable visual snapshot

<a id="save"></a>

Saving needs no media or models. It captures resolved visual settings, including defaults, with an optional display name. Existing files require explicit overwrite.

<!-- example: {"id": "save", "tier": "classic", "checks": {}} -->
```bash
yautja --list-presets
yautja --stylepreset yautja --thermal classic --hud-theme palette --neon --heat-glow 0.6 --save-preset "my-style.json" --preset-name "My Style"
```

## Load and override saved settings

<a id="reuse"></a>

Run the [save recipe](#save) first. Reusing a file leaves its contents intact; explicit flags override the saved snapshot.

<!-- example: {"id": "reuse", "tier": "classic", "checks": {}} -->
```bash
yautja "photo.jpg" "reused.png" --preset-file "my-style.json" --heat-glow 0.2
```

## Resolution, compression and audio

<a id="quality"></a>

CRF controls quality versus file size; lower is higher quality. Encoder preset controls encoding effort. It is unrelated to a style preset. Start/duration are seconds on the source timeline.

<!-- example: {"id": "quality", "tier": "classic", "checks": {"audio_preserved": false}} -->
```bash
yautja "clip.mov" "quality.mp4" --start 0 --duration 1 --max-size 640 --fps 24 --crf 18 --preset slow --audio-stream 0 --mute --waveform audio --overwrite
```

## Use a local licensed font

<a id="font-file"></a>

Supply your own printable-ASCII TTF or OTF as my-font.ttf. The path is machine-specific and is never saved. The verification fixture uses the existing bundled OFL font, not the rejected font pack.

<!-- example: {"id": "font-file", "tier": "classic", "checks": {}} -->
```bash
yautja "photo.jpg" "font.png" --HUDglyphs tech --hud-font-file "my-font.ttf"
```
