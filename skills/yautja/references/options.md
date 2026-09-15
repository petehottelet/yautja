# Option reference

Every public flag and alias is indexed here. These defaults describe a command without a preset; a preset may replace them. Precedence is defaults → optional built-in base → saved settings → explicit flags. Element maps replace inherited maps; unlisted entries use their global defaults.

Supply input and output positional paths for conversion: local JPEG/PNG → PNG, or video → MP4. Save/list/doctor/setup are separate operations. `--stylepreset` selects visual settings; encoder `--preset` controls compression effort.

The fixed fields below are checked against the parser and preset registries by `python -m tools.check_docs`. `nullable` means saved visual settings may use JSON null to retain automatic resolution; `runtime-only` settings are never included in portable visual presets. [Runnable recipes](examples.md) · [HUD roles](hud-elements.md) · [Core usage](https://github.com/petehottelet/yautja/blob/main/README.md).

## Index

[-h](#h) · [--version](#version) · [--media](#media) · [--doctor](#doctor) · [--thermal](#thermal) · [--palette](#palette) · [--palette-colors](#palette-colors) · [--stylepreset](#stylepreset) · [--preset-file](#preset-file) · [--list-presets](#list-presets) · [--save-preset](#save-preset) · [--preset-name](#preset-name) · [--thermal-levels](#thermal-levels) · [--thermal-band-softness](#thermal-band-softness) · [--thermal-black-point](#thermal-black-point) · [--thermal-white-point](#thermal-white-point) · [--thermal-gamma](#thermal-gamma) · [--thermal-softness](#thermal-softness) · [--hud-theme](#hud-theme) · [--HUDglyphs](#hudglyphs) · [--scene-mode](#scene-mode) · [--scene-tint](#scene-tint) · [--scene-tint-strength](#scene-tint-strength) · [--scene-exposure](#scene-exposure) · [--scene-highlights](#scene-highlights) · [--analysis](#analysis) · [--analysis-speed](#analysis-speed) · [--analysis-blink-rate](#analysis-blink-rate) · [--analysis-margin](#analysis-margin) · [--analysis-target](#analysis-target) · [--analysis-target-size](#analysis-target-size) · [--analysis-target-response](#analysis-target-response) · [--hud-font](#hud-font) · [--hud-font-file](#hud-font-file) · [--outline-style](#outline-style) · [--outline-shine](#outline-shine) · [--outline-width](#outline-width) · [--outline-coverage](#outline-coverage) · [--outline-arcs](#outline-arcs) · [--outline-speed](#outline-speed) · [--code-layer](#code-layer) · [--geo-grid](#geo-grid) · [--geo-grid-rotation](#geo-grid-rotation) · [--geo-grid-scale](#geo-grid-scale) · [--geo-grid-jitter](#geo-grid-jitter) · [--geo-grid-speed](#geo-grid-speed) · [--geo-grid-center-fade](#geo-grid-center-fade) · [--geo-grid-width](#geo-grid-width) · [--geo-grid-breaks](#geo-grid-breaks) · [--geo-grid-details](#geo-grid-details) · [--target-mode](#target-mode) · [--target-motion](#target-motion) · [--target-hold](#target-hold) · [--target-response](#target-response) · [--target-fill](#target-fill) · [--target-outline](#target-outline) · [--target-weak-spots](#target-weak-spots) · [--target-label-scale](#target-label-scale) · [--target-cursor](#target-cursor) · [--geo-grid-projection](#geo-grid-projection) · [--target-motif](#target-motif) · [--target-motif-count](#target-motif-count) · [--target-motif-scale](#target-motif-scale) · [--target-motif-speed](#target-motif-speed) · [--target-motif-breaks](#target-motif-breaks) · [--target-label](#target-label) · [--analysis-outline-width](#analysis-outline-width) · [--subject-outline](#subject-outline) · [--subject-code](#subject-code) · [--subject-labels](#subject-labels) · [--subject-head-gap](#subject-head-gap) · [--subject-title-gap](#subject-title-gap) · [--subject-caret-scale](#subject-caret-scale) · [--code-size](#code-size) · [--code-speed](#code-speed) · [--code-density](#code-density) · [--hud](#hud) · [--hud-colors](#hud-colors) · [--neon](#neon) · [--neon-intensity](#neon-intensity) · [--neon-spread](#neon-spread) · [--neon-core-whiten](#neon-core-whiten) · [--neon-flicker](#neon-flicker) · [--neon-elements](#neon-elements) · [--hud-blur](#hud-blur) · [--hud-blur-elements](#hud-blur-elements) · [--hud-opacity](#hud-opacity) · [--hud-opacity-elements](#hud-opacity-elements) · [--random-colors](#random-colors) · [--sensor-texture](#sensor-texture) · [--pixelation](#pixelation) · [--crt-lines](#crt-lines) · [--vhs](#vhs) · [--list-figures](#list-figures) · [--figures](#figures) · [--target](#target) · [--target-colors](#target-colors) · [--target-shape](#target-shape) · [--target-acquire](#target-acquire) · [--target-flash](#target-flash) · [--target-flash-rate](#target-flash-rate) · [--target-scale](#target-scale) · [--target-stroke](#target-stroke) · [--target-stroke-colors](#target-stroke-colors) · [--motion-blur](#motion-blur) · [--crt-bleed](#crt-bleed) · [--crt-vertical-lines](#crt-vertical-lines) · [--crt-grid](#crt-grid) · [--crt-crosshatch](#crt-crosshatch) · [--crt-strength](#crt-strength) · [--heat-glow](#heat-glow) · [--heat-glow-speed](#heat-glow-speed) · [--download-models](#download-models) · [--device](#device) · [--precision](#precision) · [--warm-objects](#warm-objects) · [--hot-objects](#hot-objects) · [--confidence](#confidence) · [--mask-stability](#mask-stability) · [--mask-min-region](#mask-min-region) · [--detect-interval](#detect-interval) · [--sensor-resolution](#sensor-resolution) · [--verbose](#verbose) · [--timecode](#timecode) · [--timecode-start](#timecode-start) · [--waveform](#waveform) · [--wave-display](#wave-display) · [--wave-backlight](#wave-backlight) · [--wave-style](#wave-style) · [--wave-width](#wave-width) · [--wave-height](#wave-height) · [--wave-detail](#wave-detail) · [--wave-window](#wave-window) · [--wave-gain](#wave-gain) · [--audio-stream](#audio-stream) · [--mute](#mute) · [--start](#start) · [--duration](#duration) · [--fps](#fps) · [--max-size](#max-size) · [--crf](#crf) · [--preset](#preset) · [--grain](#grain) · [--glow](#glow) · [--seed](#seed) · [--overwrite](#overwrite)

## Definitions

#### h

- Syntax: `-h`, `--help`
- Values: Switch; no value argument.
- Units: unitless
- Default: Print help and exit when requested.
- Applies: show this help message and exit
- Requires: No additional enabling flag.
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#inspect)

#### version

- Syntax: `--version`
- Values: Switch; no value argument.
- Units: unitless
- Default: Print the installed version and exit when requested.
- Applies: show program's version number and exit
- Requires: No additional enabling flag.
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#inspect)

#### media

- Syntax: `--media`
- Values: `auto`, `image`, `video`
- Units: not applicable
- Default: "auto"
- Applies: Auto selects images for JPEG/PNG input or PNG output; use image with --doctor to skip FFmpeg checks
- Requires: No additional enabling flag.
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#inspect)

#### doctor

- Syntax: `--doctor`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Check the local runtime, tools, and bundled shapes
- Requires: No additional enabling flag.
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#inspect)

#### thermal

- Syntax: `--thermal`
- Values: `classic`, `low-detail`, `cinematic`, `detailed`, `very-detailed`
- Units: not applicable
- Default: "classic"
- Applies: Four segmented looks: low-detail (soft blobs), cinematic (broad patches), detailed (surfaces), very-detailed (source facial/fabric features). Classic is the lightweight luminance filter; semantic/realistic aliases remain supported
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#lightweight)

#### palette

- Syntax: `--palette`
- Values: `auto`, `thermal-spectrum`, `costa-rica`, `yautja`, `ironbow`, `abyss`, `redline`, `green-phosphor`, `amber-phosphor`, `white-hot`, `black-hot`, `virtualboy`, `custom`, `random`
- Units: not applicable
- Default: "yautja"
- Applies: Thermal colors, independent of thermal style. Yautja by default; Costa Rica preserves the original palette; custom uses --palette-colors; random uses --seed
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#lightweight)

#### palette-colors

- Syntax: `--palette-colors`
- Values: 2–16 RGB hex colors, cold to hot
- Units: unitless
- Default: No custom ramp; use the named palette.
- Applies: With --palette custom: quoted string of 2–16 comma/space-separated hex colors, cold to hot, evenly spaced; e.g. "#000000,#0033ff,#ff2200"
- Requires: --palette custom
- Persistence: nullable
- Example: [Complete recipe](examples.md#palette-only)

#### stylepreset

- Syntax: `--stylepreset`
- Values: `yautja`, `netrunner`, `fremont`, `focus`, `relic`, `murphy`, `costa-rica`, `ironbow`, `abyss`, `redline`, `virtualboy`, `green-phosphor`, `amber-phosphor`, `white-hot`, `black-hot`, `thermal-spectrum`
- Units: not applicable
- Default: No recipe; Classic with Yautja colors.
- Applies: Built-in visual preset, including Yautja, Costa Rica, Netrunner, Focus, Relic, Murphy, Fremont, and a starter for every palette. Explicit options override it; encoder --preset stays separate
- Requires: Mutually exclusive with --preset-file
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#hero)

#### preset-file

- Syntax: `--preset-file`
- Values: Local filesystem path.
- Units: not applicable
- Default: No saved settings loaded.
- Applies: Load a local JSON visual preset; explicit options override its settings
- Requires: An existing schema-1 preset JSON; mutually exclusive with --stylepreset
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#reuse)

#### list-presets

- Syntax: `--list-presets`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: List built-in preset names and settings as JSON, then exit; no media or models needed
- Requires: No additional enabling flag.
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#save)

#### save-preset

- Syntax: `--save-preset`
- Values: Local filesystem path.
- Units: not applicable
- Default: No preset file written.
- Applies: Save the chosen visual settings to a .json preset, then exit; omit media paths
- Requires: No additional enabling flag.
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#save)

#### preset-name

- Syntax: `--preset-name`
- Values: 1–80 characters, no control characters
- Units: unitless
- Default: The output JSON filename stem.
- Applies: Display name for --save-preset (default: filename stem)
- Requires: --save-preset
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#save)

#### thermal-levels

- Syntax: `--thermal-levels`
- Values: 0 for continuous color, or integer 2–64
- Units: unitless
- Default: Legacy mode-specific quantization; specify --thermal-levels before using explicit grading controls.
- Applies: Representative thermal levels: 2–64, or 0 for continuous. Omitted retains legacy grading
- Requires: No additional enabling flag.
- Persistence: nullable
- Example: [Complete recipe](examples.md#thermal-grade)

#### thermal-band-softness

- Syntax: `--thermal-band-softness`
- Values: 0–1
- Units: unitless
- Default: 0.35 when explicit levels are enabled; inactive for continuous color.
- Applies: Transition width between levels, 0–1; 0 gives hard bands, default 0.35 with explicit levels
- Requires: --thermal-levels 2–64; cannot combine with levels 0
- Persistence: nullable
- Example: [Complete recipe](examples.md#thermal-grade)

#### thermal-black-point

- Syntax: `--thermal-black-point`
- Values: 0–0.95
- Units: unitless
- Default: 0.0
- Applies: Synthetic warmth mapped to black/cold end, 0–0.95; requires --thermal-levels or --stylepreset
- Requires: --thermal-levels or a preset that sets it; white minus black must be at least 0.01
- Persistence: saved
- Example: [Complete recipe](examples.md#thermal-grade)

#### thermal-white-point

- Syntax: `--thermal-white-point`
- Values: 0.05–1
- Units: unitless
- Default: 1.0
- Applies: Synthetic warmth mapped to hot end, 0.05–1; must exceed black point by 0.01
- Requires: --thermal-levels or a preset that sets it; white minus black must be at least 0.01
- Persistence: saved
- Example: [Complete recipe](examples.md#thermal-grade)

#### thermal-gamma

- Syntax: `--thermal-gamma`
- Values: 0.25–4
- Units: unitless
- Default: 1.0
- Applies: Thermal response exponent, 0.25–4; above 1 darkens intermediate warmth
- Requires: --thermal-levels or a preset that sets it
- Persistence: saved
- Example: [Complete recipe](examples.md#thermal-grade)

#### thermal-softness

- Syntax: `--thermal-softness`
- Values: 0–8
- Units: reference pixels at a 1920px longest edge
- Default: 0.0
- Applies: Scalar Gaussian softness, 0–8 pixels at a 1920px longest edge; separate from band transitions and glow
- Requires: --thermal-levels or a preset that sets it
- Persistence: saved
- Example: [Complete recipe](examples.md#thermal-grade)

#### hud-theme

- Syntax: `--hud-theme`
- Values: `standard`, `palette`, `muted-cyan`, `custom`, `random`
- Units: not applicable
- Default: "standard"
- Applies: HUD colors: standard red/cyan (white for White Hot, black for Black Hot, muted cyan for Abyss), palette-matched, muted-cyan, custom, or seeded random
- Requires: --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#palette-only)

#### HUDglyphs

- Syntax: `--HUDglyphs`
- Values: `yautja`, `cyber`, `tech`
- Units: not applicable
- Default: "yautja"
- Applies: HUD glyph set: Yautja, Cyber (192 generated glyphs), or readable Tech letters and numbers. Tech uses --hud-font; timecode stays numeric
- Requires: --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#netrunner)

#### scene-mode

- Syntax: `--scene-mode`
- Values: `thermal`, `source`
- Units: not applicable
- Default: "thermal"
- Applies: Color a thermal field (default) or retain the RGB source scene with configurable tint and exposure
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#source-grade)

#### scene-tint

- Syntax: `--scene-tint`
- Values: #RGB or #RRGGBB
- Units: unitless
- Default: "#548568"
- Applies: RGB hex tint for source scene mode; default muted green #548568
- Requires: --scene-mode source
- Persistence: saved
- Example: [Complete recipe](examples.md#source-grade)

#### scene-tint-strength

- Syntax: `--scene-tint-strength`
- Values: 0–1
- Units: unitless
- Default: 0.8
- Applies: Source tint blend, 0-1; 0 preserves source colors
- Requires: --scene-mode source
- Persistence: saved
- Example: [Complete recipe](examples.md#source-grade)

#### scene-exposure

- Syntax: `--scene-exposure`
- Values: 0.1–2
- Units: unitless
- Default: 0.65
- Applies: Source scene brightness multiplier, 0.1-2; default 0.65
- Requires: --scene-mode source
- Persistence: saved
- Example: [Complete recipe](examples.md#source-grade)

#### scene-highlights

- Syntax: `--scene-highlights`
- Values: 0–1
- Units: unitless
- Default: 0.0
- Applies: Restore neutral highlights above the source tint, 0-1; 0 retains the tint, 1 makes bright highlights white
- Requires: --scene-mode source
- Persistence: saved
- Example: [Complete recipe](examples.md#source-grade)

#### analysis

- Syntax: `--analysis`, `--no-analysis`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Readable scan HUD with a moving XY grid, automatic subject selection, descriptive text, and blinking analysis outlines; requires a segmented mode
- Requires: --hud and a segmented thermal mode
- Persistence: saved
- Example: [Complete recipe](examples.md#fremont)

#### analysis-speed

- Syntax: `--analysis-speed`
- Values: 0–5
- Units: unitless
- Default: 1.0
- Applies: Search/acquire/analysis/hold cycle speed, 0-5; 1 takes six seconds, 0 freezes the search
- Requires: --analysis and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#fremont)

#### analysis-blink-rate

- Syntax: `--analysis-blink-rate`
- Values: 0–4
- Units: cycles per second
- Default: 2.0
- Applies: Outline blinks per second during analysis, 0-4; 0 keeps it steady
- Requires: --analysis and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#fremont)

#### analysis-margin

- Syntax: `--analysis-margin`
- Values: 0.01–0.15
- Units: fraction of the relevant frame dimension; see applicability
- Default: 0.035
- Applies: Safe margin for readable analysis text as a fraction of the short frame edge, 0.01-0.15
- Requires: --analysis and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#fremont)

#### analysis-target

- Syntax: `--analysis-target`, `--no-analysis-target`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Persistent translucent scan target with smooth focus motion and no acquisition zoom; independent of --analysis, shares its subject selection and speed
- Requires: --hud and a segmented thermal mode; independent of --analysis
- Persistence: saved
- Example: [Complete recipe](examples.md#fremont)

#### analysis-target-size

- Syntax: `--analysis-target-size`
- Values: 0.1–0.8
- Units: fraction of the relevant frame dimension; see applicability
- Default: 0.36
- Applies: Constant scan target diameter as a fraction of the short frame edge, 0.1-0.8
- Requires: --analysis-target and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#fremont)

#### analysis-target-response

- Syntax: `--analysis-target-response`
- Values: 0–3
- Units: seconds
- Default: 0.6
- Applies: Seconds to cover 95 percent of a focus change, 0-3; 0 follows immediately
- Requires: --analysis-target and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#fremont)

#### hud-font

- Syntax: `--hud-font`
- Values: `michroma`, `orbitron`, `orbitron-medium`, `orbitron-bold`
- Units: not applicable
- Default: "michroma"
- Applies: Readable HUD font: Michroma Regular, Orbitron Light, Medium or Bold; applies to Tech, analysis and target captions
- Requires: --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#murphy)

#### hud-font-file

- Syntax: `--hud-font-file`
- Values: Local filesystem path.
- Units: not applicable
- Default: Use the bundled font selected by --hud-font.
- Applies: Local TTF/OTF overriding the bundled readable font; must cover printable ASCII. Machine-specific path is never saved in presets
- Requires: --hud
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#font-file)

#### outline-style

- Syntax: `--outline-style`
- Values: `solid`, `shimmer`, `holographic`
- Units: not applicable
- Default: "solid"
- Applies: Continuous edge, partial shimmer, or textured partial holographic glow; enable with --subject-outline
- Requires: --subject-outline and --hud; coverage/arcs/speed apply to partial styles
- Persistence: saved
- Example: [Complete recipe](examples.md#hologram)

#### outline-shine

- Syntax: `--outline-shine`
- Values: 0–1
- Units: unitless
- Default: 0.55
- Applies: Moving holographic band brightness, 0-1; affects holographic outlines and optional weak-spot textures
- Requires: --outline-style holographic with --subject-outline, or --target-weak-spots
- Persistence: saved
- Example: [Complete recipe](examples.md#hologram)

#### outline-width

- Syntax: `--outline-width`
- Values: 0.5–20
- Units: reference pixels at a 1080px short edge
- Default: Solid 2, shimmer 3, holographic 8 reference pixels.
- Applies: Subject edge thickness at 1080p, 0.5-20; automatic: solid 2, shimmer 3, holographic 8
- Requires: --subject-outline and --hud; coverage/arcs/speed apply to partial styles
- Persistence: nullable
- Example: [Complete recipe](examples.md#hologram)

#### outline-coverage

- Syntax: `--outline-coverage`
- Values: 0–1
- Units: unitless
- Default: 0.35
- Applies: Shimmer edge coverage, 0-1
- Requires: --subject-outline and --hud; coverage/arcs/speed apply to partial styles
- Persistence: saved
- Example: [Complete recipe](examples.md#hologram)

#### outline-arcs

- Syntax: `--outline-arcs`
- Values: integer 1–12
- Units: unitless
- Default: 5
- Applies: Shimmer highlight count, 1-12
- Requires: --subject-outline and --hud; coverage/arcs/speed apply to partial styles
- Persistence: saved
- Example: [Complete recipe](examples.md#hologram)

#### outline-speed

- Syntax: `--outline-speed`
- Values: 0–5
- Units: unitless
- Default: 1.0
- Applies: Shimmer speed, 0-5; 0 freezes travel and twinkle
- Requires: --subject-outline and --hud; coverage/arcs/speed apply to partial styles
- Persistence: saved
- Example: [Complete recipe](examples.md#hologram)

#### code-layer

- Syntax: `--code-layer`
- Values: `inside`, `behind`
- Units: not applicable
- Default: "inside"
- Applies: Place subject code inside silhouettes or behind all current subjects
- Requires: --subject-code, --hud and a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#relic)

#### code-style

- Syntax: `--code-style`
- Values: `glyphs`, `light`
- Units: not applicable
- Default: "glyphs"
- Applies: Choose readable glyph streams or soft rising light filaments centered on the body core; Relic uses light
- Requires: --subject-code, --hud and a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#relic)

#### geo-grid

- Syntax: `--geo-grid`, `--no-geo-grid`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Shimmering triangular grid over the frame
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#grid)

#### geo-grid-rotation

- Syntax: `--geo-grid-rotation`
- Values: −10–10
- Units: degrees per second
- Default: 0.0
- Applies: Grid rotation in degrees per second, -10 to 10; independent of brightness speed, 0 is stationary
- Requires: --geo-grid and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#grid)

#### geo-grid-scale

- Syntax: `--geo-grid-scale`
- Values: 40–480
- Units: reference pixels at a 1080px short edge
- Default: 160.0
- Applies: Grid spacing, 40-480 pixels at a 1080px short edge
- Requires: --geo-grid and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#grid)

#### geo-grid-jitter

- Syntax: `--geo-grid-jitter`
- Values: 0–1
- Units: unitless
- Default: 0.65
- Applies: Seeded grid irregularity, 0-1
- Requires: --geo-grid and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#grid)

#### geo-grid-speed

- Syntax: `--geo-grid-speed`
- Values: 0–5
- Units: unitless
- Default: 1.0
- Applies: Grid brightness animation speed, 0-5; 0 freezes it
- Requires: --geo-grid and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#grid)

#### geo-grid-center-fade

- Syntax: `--geo-grid-center-fade`
- Values: 0–1
- Units: unitless
- Default: 0.0
- Applies: Fade the grid toward the screen center, 0-1; 0 is uniform, 1 clears the center
- Requires: --geo-grid and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#grid)

#### geo-grid-width

- Syntax: `--geo-grid-width`
- Values: 0.5–6
- Units: reference pixels at a 1080px short edge
- Default: 1.3
- Applies: Grid line thickness, 0.5-6 pixels at a 1080px short edge
- Requires: --geo-grid and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#grid)

#### geo-grid-breaks

- Syntax: `--geo-grid-breaks`
- Values: 0–1
- Units: unitless
- Default: 0.0
- Applies: Seeded irregular gaps in grid edges, 0-1; 0 keeps continuous lines
- Requires: --geo-grid and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#grid)

#### geo-grid-details

- Syntax: `--geo-grid-details`, `--no-geo-grid-details`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Pulsing satellite dots along grid edges and seven-sided rings at selected vertices; motion follows --geo-grid-speed
- Requires: --geo-grid and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#grid)

#### target-mode

- Syntax: `--target-mode`
- Values: `selected`, `auto`, `cycle`
- Units: not applicable
- Default: "selected"
- Applies: Catalog selections, all automatic subjects, or one cycling subject; explicit --target selections supply the candidate pool
- Requires: --hud and catalog targets or automatic selection in a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#focus)

#### target-motion

- Syntax: `--target-motion`
- Values: `acquire`, `persistent`
- Units: not applicable
- Default: "acquire"
- Applies: Acquisition animation or one persistent reticle gliding between subjects without zoom
- Requires: --hud and catalog targets or automatic selection in a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#focus)

#### target-hold

- Syntax: `--target-hold`
- Values: 0.5–30
- Units: seconds
- Default: 3.0
- Applies: Seconds before cycling to another target, 0.5-30
- Requires: --target-mode cycle or --target-motion persistent
- Persistence: saved
- Example: [Complete recipe](examples.md#focus)

#### target-response

- Syntax: `--target-response`
- Values: 0–3
- Units: seconds
- Default: 0.6
- Applies: Persistent motion response in seconds, 0-3; 0 follows immediately
- Requires: --target-motion persistent
- Persistence: saved
- Example: [Complete recipe](examples.md#focus)

#### target-fill

- Syntax: `--target-fill`
- Values: `auto`, `filled`, `stroked`
- Units: not applicable
- Default: "auto"
- Applies: All shapes: original treatment, solid marks with translucent enclosures, or hollow mark outlines
- Requires: --hud and catalog targets or automatic selection in a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#focus)

#### target-outline

- Syntax: `--target-outline`, `--no-target-outline`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Outline only targeted subjects using their current segmentation masks
- Requires: --hud, a segmented mode and a selected target
- Persistence: saved
- Example: [Complete recipe](examples.md#murphy)

#### target-weak-spots

- Syntax: `--target-weak-spots`, `--no-target-weak-spots`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Decorative holographic scan patches on selected subjects, not physical weak-point detection; requires segmentation
- Requires: --hud, a segmented mode and a selected target
- Persistence: saved
- Example: [Complete recipe](examples.md#hologram)

#### target-label-scale

- Syntax: `--target-label-scale`
- Values: 0.5–4
- Units: unitless
- Default: 1.0
- Applies: Target caption size multiplier, 0.5-4
- Requires: --target-label and a visible target
- Persistence: saved
- Example: [Complete recipe](examples.md#murphy)

#### target-cursor

- Syntax: `--target-cursor`, `--no-target-cursor`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Blink an underscore after the target caption
- Requires: --target-label and a visible target
- Persistence: saved
- Example: [Complete recipe](examples.md#murphy)

#### geo-grid-projection

- Syntax: `--geo-grid-projection`
- Values: `flat`, `sphere`
- Units: not applicable
- Default: "flat"
- Applies: Flat triangular lattice or curved geodesic sphere viewed from its center
- Requires: --geo-grid and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#grid)

#### target-motif

- Syntax: `--target-motif`
- Values: `none`, `triangles`
- Units: not applicable
- Default: "none"
- Applies: Independent hollow-triangle target ornaments
- Requires: A visible selected target and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#relic)

#### target-motif-count

- Syntax: `--target-motif-count`
- Values: integer 0–24
- Units: unitless
- Default: 7
- Applies: Triangles per visible target, 0-24
- Requires: --target-motif triangles and a visible target
- Persistence: saved
- Example: [Complete recipe](examples.md#relic)

#### target-motif-scale

- Syntax: `--target-motif-scale`
- Values: 0.25–3
- Units: unitless
- Default: 1.0
- Applies: Triangle ornament scale, 0.25-3
- Requires: --target-motif triangles and a visible target
- Persistence: saved
- Example: [Complete recipe](examples.md#relic)

#### target-motif-speed

- Syntax: `--target-motif-speed`
- Values: 0–5
- Units: unitless
- Default: 1.0
- Applies: Triangle rise, contraction and spin speed, 0-5; 0 freezes the ornaments
- Requires: --target-motif triangles and a visible target
- Persistence: saved
- Example: [Complete recipe](examples.md#relic)

#### target-motif-breaks

- Syntax: `--target-motif-breaks`
- Values: 0–1
- Units: unitless
- Default: 0.0
- Applies: Seeded irregular gaps in triangle edges, 0-1; 0 keeps continuous edges
- Requires: --target-motif triangles and a visible target
- Persistence: saved
- Example: [Complete recipe](examples.md#relic)

#### target-label

- Syntax: `--target-label`, `--no-target-label`
- Values: 1–24 printable ASCII characters; --no-target-label clears it
- Units: unitless
- Default: No caption.
- Applies: Readable target caption, 1-24 printable ASCII characters; only shown with a visible target
- Requires: A visible target and --hud
- Persistence: nullable
- Example: [Complete recipe](examples.md#murphy)

#### analysis-outline-width

- Syntax: `--analysis-outline-width`
- Values: 0.5–12
- Units: reference pixels at a 1080px short edge
- Default: 2.4
- Applies: Analysis outline thickness, 0.5-12 pixels at a 1080px short edge; Fremont uses 5
- Requires: --analysis and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#fremont)

#### subject-outline

- Syntax: `--subject-outline`, `--no-subject-outline`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Outline detected subject silhouettes; requires a segmented mode
- Requires: --hud and a segmented thermal mode
- Persistence: saved
- Example: [Complete recipe](examples.md#hologram)

#### subject-code

- Syntax: `--subject-code`, `--no-subject-code`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Show rising glyphs or light streams on detected subjects; requires a segmented mode
- Requires: --hud and a segmented thermal mode
- Persistence: saved
- Example: [Complete recipe](examples.md#netrunner)

#### subject-labels

- Syntax: `--subject-labels`, `--no-subject-labels`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Stable overhead glyph titles and downward carets for detected subjects; requires a segmented mode
- Requires: --hud and a segmented thermal mode
- Persistence: saved
- Example: [Complete recipe](examples.md#netrunner)

#### subject-head-gap

- Syntax: `--subject-head-gap`
- Values: 0–120
- Units: reference pixels at a 1080px short edge
- Default: 24.0
- Applies: Head-to-caret clearance, 0-120 reference pixels at a 1080px short edge; default 24
- Requires: --subject-labels, --hud and a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#netrunner)

#### subject-title-gap

- Syntax: `--subject-title-gap`
- Values: 0–80
- Units: reference pixels at a 1080px short edge
- Default: 18.0
- Applies: Caret-to-title clearance, 0-80 reference pixels at a 1080px short edge; default 18
- Requires: --subject-labels, --hud and a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#netrunner)

#### subject-caret-scale

- Syntax: `--subject-caret-scale`
- Values: 0.25–3
- Units: unitless
- Default: 1.0
- Applies: Subject caret size multiplier, 0.25-3; Netrunner uses 1.35
- Requires: --subject-labels, --hud and a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#netrunner)

#### code-size

- Syntax: `--code-size`
- Values: 8–80
- Units: reference pixels at a 1080px short edge
- Default: 22.0
- Applies: Glyph size or light-stream spacing and width, 8-80 reference pixels at a 1080px short edge
- Requires: --subject-code, --hud and a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#netrunner)

#### code-speed

- Syntax: `--code-speed`
- Values: 0–5
- Units: unitless
- Default: 1.0
- Applies: Upward code speed multiplier, 0-5; 0 freezes code motion
- Requires: --subject-code, --hud and a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#netrunner)

#### code-density

- Syntax: `--code-density`
- Values: 0–3
- Units: unitless
- Default: 0.65
- Applies: Stream density, 0-3; 0 hides the effect. Glyph mode selects or adds columns without shrinking glyphs; light mode adjusts filament count
- Requires: --subject-code, --hud and a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#netrunner)

#### hud

- Syntax: `--hud`, `--no-hud`
- Values: Switch; no value argument.
- Units: not applicable
- Default: true
- Applies: Show the HUD (default); --no-hud hides all waveform, scale, glyph, timecode, callout, leader, and marker overlays while retaining thermal coloring, textures, and sound
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#clean)

#### hud-colors

- Syntax: `--hud-colors`
- Values: quoted element=#RGB or element=#RRGGBB assignments
- Units: unitless
- Default: Standard colors for unspecified elements.
- Applies: With --hud-theme custom: quoted comma-separated element=#RRGGBB assignments. Elements: waveform, waveform-axis, waveform-ticks, waveform-glyphs, readout, timecode, callouts, leaders, markers, target, target-flash, subject-outline, subject-code, subject-labels, subject-carets, analysis-grid, analysis-text, analysis-outline, geo-grid, target-motif, target-label, target-outline, target-weak-spots, analysis-target-fill, analysis-target. Unspecified elements keep standard colors
- Requires: --hud-theme custom and --hud
- Persistence: nullable
- Example: [Complete recipe](examples.md#vocoder)

#### neon

- Syntax: `--neon`, `--no-neon`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Light every HUD element with a bright neon core and colored halo; replaces standard HUD bloom. Default off
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#vocoder)

#### neon-intensity

- Syntax: `--neon-intensity`
- Values: 0–2
- Units: unitless
- Default: 1.0
- Applies: Neon brightness, 0-2; 0 disables neon treatment, 1 is normal, 2 is intense
- Requires: --neon and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#neon)

#### neon-spread

- Syntax: `--neon-spread`
- Values: 0–2
- Units: unitless
- Default: 0.6
- Applies: Halo radius relative to stroke width, 0-2; 0 is a tight rim, 2 is a wide wash
- Requires: --neon and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#neon)

#### neon-core-whiten

- Syntax: `--neon-core-whiten`
- Values: 0–1
- Units: unitless
- Default: 1.0
- Applies: Bright core whitening, 0-1; 0 retains the selected ink hue, 1 uses the standard pale neon core
- Requires: --neon and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#neon)

#### neon-flicker

- Syntax: `--neon-flicker`
- Values: 0–1
- Units: unitless
- Default: 0.0
- Applies: Seeded neon hum, 0-1; 0 is steady. Stills show time zero
- Requires: --neon and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#neon)

#### neon-elements

- Syntax: `--neon-elements`
- Values: quoted element=0–2 assignments
- Units: unitless
- Default: Every element inherits --neon-intensity.
- Applies: Comma-separated element=intensity overrides, 0-2; 0 disables neon for that element. Others inherit --neon-intensity. Elements: waveform, waveform-axis, waveform-ticks, waveform-glyphs, readout, timecode, callouts, leaders, markers, target, subject-outline, subject-code, subject-labels, subject-carets, analysis-grid, analysis-text, analysis-outline, geo-grid, target-motif, target-label, target-outline, target-weak-spots, analysis-target-fill, analysis-target. Target applies to both flash states
- Requires: --neon and --hud
- Persistence: nullable
- Example: [Complete recipe](examples.md#neon)

#### hud-blur

- Syntax: `--hud-blur`
- Values: 0–20
- Units: reference pixels at a 1080px short edge
- Default: 0.0
- Applies: Gaussian softness for all HUD artwork only, 0-20 reference pixels at a 1080px short edge; default 0 (sharp)
- Requires: --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#hud-ink)

#### hud-blur-elements

- Syntax: `--hud-blur-elements`
- Values: quoted element=0–20 assignments
- Units: unitless
- Default: Every element inherits --hud-blur.
- Applies: Override blur independently with quoted comma-separated element=radius values, 0-20; explicit 0 keeps an element sharp. Elements: waveform, waveform-axis, waveform-ticks, waveform-glyphs, readout, timecode, callouts, leaders, markers, target, subject-outline, subject-code, subject-labels, subject-carets, analysis-grid, analysis-text, analysis-outline, geo-grid, target-motif, target-label, target-outline, target-weak-spots, analysis-target-fill, analysis-target. Target applies to both flash states
- Requires: --hud
- Persistence: nullable
- Example: [Complete recipe](examples.md#hud-ink)

#### hud-opacity

- Syntax: `--hud-opacity`
- Values: 0–1
- Units: unitless
- Default: 1.0
- Applies: Shared HUD visibility, 0-1: 0 is transparent, 1 keeps full existing visibility (default); includes outlines and glow
- Requires: --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#hud-ink)

#### hud-opacity-elements

- Syntax: `--hud-opacity-elements`
- Values: quoted element=0–1 assignments
- Units: unitless
- Default: Every element inherits --hud-opacity.
- Applies: Independent transparency via quoted comma-separated element=opacity values, 0-1; omitted elements inherit --hud-opacity. Elements: waveform, waveform-axis, waveform-ticks, waveform-glyphs, readout, timecode, callouts, leaders, markers, target, target-flash, subject-outline, subject-code, subject-labels, subject-carets, analysis-grid, analysis-text, analysis-outline, geo-grid, target-motif, target-label, target-outline, target-weak-spots, analysis-target-fill, analysis-target. Target-flash inherits target unless explicitly set
- Requires: --hud
- Persistence: nullable
- Example: [Complete recipe](examples.md#hud-ink)

#### random-colors

- Syntax: `--random-colors`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Randomize both the thermal palette and every HUD element once using --seed; colors stay fixed throughout the clip
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#hud-ink)

#### sensor-texture

- Syntax: `--sensor-texture`, `--no-sensor-texture`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Preset combining sensor pixels, grain, and scanlines (default: off); individual controls override the preset
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#sensor)

#### pixelation

- Syntax: `--pixelation`
- Values: 0 (off), or integer 32–640; bare flag 96
- Units: pixels on the longest edge
- Default: Off; --sensor-texture uses --sensor-resolution unless explicitly overridden.
- Applies: Chunky pixels: longest grid edge, 32-640 (bare flag: 96); 0 disables. Independent of grain and segmentation
- Requires: No additional enabling flag.
- Persistence: nullable
- Example: [Complete recipe](examples.md#sensor)

#### crt-lines

- Syntax: `--crt-lines`, `--no-crt-lines`, `--scanlines`, `--no-scanlines`
- Values: Switch; no value argument.
- Units: not applicable
- Default: On for the default Yautja thermal palette or --sensor-texture; otherwise off.
- Applies: Horizontal CRT lines across scene and HUD; --scanlines is an alias for --crt-lines.
- Requires: No additional enabling flag.
- Persistence: nullable
- Example: [Complete recipe](examples.md#sensor)

#### vhs

- Syntax: `--vhs`, `--no-vhs`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: VHS-style color bleed, horizontal wobble, tape noise, and tracking defects; default off
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#crt)

#### list-figures

- Syntax: `--list-figures`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Scan shots into a JSON figure catalog and HTML contact sheet; optional output defaults beside the input. Requires the semantic runtime
- Requires: Cached semantic models; separate from conversion
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#catalog-scan)

#### figures

- Syntax: `--figures`
- Values: Local filesystem path.
- Units: not applicable
- Default: No figure catalog.
- Applies: Saved figure catalog from the same source, used with --target
- Requires: --target
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#catalog-target)

#### target

- Syntax: `--target`
- Values: Comma-separated shot-local IDs; repeat the flag to select more.
- Units: unitless
- Default: []
- Applies: Figure ID from the catalog, e.g. S001-F002; repeat or comma-separate for multiple figures/shots
- Requires: --figures from the exact input source and --hud
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#catalog-target)

#### target-colors

- Syntax: `--target-colors`
- Values: one or two RGB hex colors: primary,flash
- Units: unitless
- Default: Resolved target and flash HUD colors.
- Applies: Two comma-separated RGB hex colors for landing and flash, overriding HUD target colors; default red,white
- Requires: --hud and catalog targets or automatic selection in a segmented mode
- Persistence: nullable
- Example: [Complete recipe](examples.md#catalog-target)

#### target-shape

- Syntax: `--target-shape`
- Values: `triangle`, `triangle-dots`, `crosshair`, `hollow-cross`, `square`, `round-dot`, `square-cross`, `square-mil`, `square-x`, `hexagon`, `frame-box`
- Units: not applicable
- Default: "triangle"
- Applies: Animated reticle geometry; triangle by default. Round-dot is a circular outline with four gaps and three center dots arranged in a triangle, appearing on lock. Hollow-cross has four L-shaped bands with an open center and arm ends; vector-lock and iron-sights remain aliases
- Requires: --hud and catalog targets or automatic selection in a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#focus)

#### target-acquire

- Syntax: `--target-acquire`
- Values: 0.1–5
- Units: seconds
- Default: 0.8
- Applies: Seconds for the target reticle to assemble, 0.1-5
- Requires: --hud and catalog targets or automatic selection in a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#catalog-target)

#### target-flash

- Syntax: `--target-flash`, `--no-target-flash`
- Values: Switch; no value argument.
- Units: not applicable
- Default: true
- Applies: Alternate target colors after landing; --no-target-flash keeps the landing color
- Requires: --hud and catalog targets or automatic selection in a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#catalog-target)

#### target-flash-rate

- Syntax: `--target-flash-rate`
- Values: 0–3
- Units: cycles per second
- Default: 1.5
- Applies: Target flash cycles per second, 0-3; 0 holds the landing color
- Requires: --hud and catalog targets or automatic selection in a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#catalog-target)

#### target-scale

- Syntax: `--target-scale`
- Values: 0.25–3
- Units: unitless
- Default: 1.0
- Applies: Size multiplier for the compact reticle centered on the selected figure, 0.25-3; default 1
- Requires: --hud and catalog targets or automatic selection in a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#murphy)

#### target-stroke

- Syntax: `--target-stroke`
- Values: 0–12; bare flag 2
- Units: reference pixels at a 1080px short edge
- Default: 0.0
- Applies: Optional inward outline on each target blade, 0-12 reference pixels at a 1080px short edge; bare flag 2, default 0 (off)
- Requires: --hud and catalog targets or automatic selection in a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#catalog-target)

#### target-stroke-colors

- Syntax: `--target-stroke-colors`
- Values: auto, or one or two RGB hex colors
- Units: unitless
- Default: Darker shades of the resolved target colors.
- Applies: Outline color: one RGB hex color or a landing,flash pair. Omit or use auto for darker shades of the current target colors; requires nonzero --target-stroke to be visible
- Requires: Nonzero --target-stroke
- Persistence: nullable
- Example: [Complete recipe](examples.md#catalog-target)

#### motion-blur

- Syntax: `--motion-blur`
- Values: 0–1
- Units: unitless
- Default: 0.0
- Applies: Temporal motion trails/persistence strength, 0-1; 0 disables. Video only; stills have no preceding frames
- Requires: Video frames; inactive on stills
- Persistence: saved
- Example: [Complete recipe](examples.md#crt)

#### crt-bleed

- Syntax: `--crt-bleed`
- Values: 0–1
- Units: unitless
- Default: 0.0
- Applies: Horizontal phosphor color spread, 0-1; independent of VHS and CRT lines
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#crt)

#### crt-vertical-lines

- Syntax: `--crt-vertical-lines`, `--no-crt-vertical-lines`, `--vertical-crt-lines`, `--no-vertical-crt-lines`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Vertical CRT columns across image and HUD; combine with horizontal --crt-lines
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#crt)

#### crt-grid

- Syntax: `--crt-grid`, `--no-crt-grid`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Horizontal and vertical CRT grid across image and HUD; default off
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#crt)

#### crt-crosshatch

- Syntax: `--crt-crosshatch`, `--no-crt-crosshatch`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: CRT grid at 45 degrees across image and HUD; default off
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#crt)

#### crt-strength

- Syntax: `--crt-strength`
- Values: 0–1
- Units: unitless
- Default: 0.12
- Applies: Darkening strength of enabled CRT lines, grid, and crosshatch, 0-1
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#crt)

#### heat-glow

- Syntax: `--heat-glow`
- Values: 0–1
- Units: unitless
- Default: 0.0
- Applies: Animated bloom from synthetic hot regions in any palette, 0-1; independent of HUD --glow
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#crt)

#### heat-glow-speed

- Syntax: `--heat-glow-speed`
- Values: 0–5
- Units: unitless
- Default: 1.0
- Applies: Heat-glow movement speed, 0-5; 0 freezes it. Stills show time zero
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#crt)

#### download-models

- Syntax: `--download-models`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Download pinned Apache-2.0 semantic models once, then exit (no input needed)
- Requires: The semantic extra and explicit network access
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#models-setup)

#### device

- Syntax: `--device`
- Values: `auto`, `cpu`, `cuda`
- Units: not applicable
- Default: "auto"
- Applies: Semantic inference device; auto prefers available CUDA
- Requires: A segmented mode or --list-figures
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#tracking)

#### precision

- Syntax: `--precision`
- Values: `fp32`, `bf16`
- Units: not applicable
- Default: "fp32"
- Applies: Semantic model precision; bf16 is experimental and requires compatible CUDA
- Requires: bf16 needs compatible CUDA and a segmented mode
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#tracking)

#### warm-objects

- Syntax: `--warm-objects`
- Values: comma-separated category names
- Units: unitless
- Default: "person,bird,cat,dog,horse,sheep,cow,elephant,bear,zebra,giraffe"
- Applies: Comma-separated object categories to simulate as warm
- Requires: A segmented mode or --list-figures
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#fremont)

#### hot-objects

- Syntax: `--hot-objects`
- Values: comma-separated category names
- Units: unitless
- Default: ""
- Applies: Explicit comma-separated hot categories, e.g. fire; these are artistic overrides
- Requires: A segmented mode or --list-figures
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#tracking)

#### confidence

- Syntax: `--confidence`
- Values: 0.05–0.95
- Units: unitless
- Default: 0.3
- Applies: Object detection threshold, 0.05-0.95
- Requires: A segmented mode or --list-figures
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#tracking)

#### mask-stability

- Syntax: `--mask-stability`
- Values: 0–1
- Units: seconds
- Default: 0.18
- Applies: Flow-aligned mask smoothing in seconds, 0-1; 0 disables smoothing and hysteresis Applied to flow-aligned refinement; probability masks remain separate from stable overlay masks. Set both mask controls to zero for the old behavior.
- Requires: A segmented mode or --list-figures
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#tracking)

#### mask-min-region

- Syntax: `--mask-min-region`
- Values: 0–0.2
- Units: fraction of the largest mask component area
- Default: 0.02
- Applies: Minimum overlay island area relative to the largest component, 0-0.2; 0 disables closing and island removal
- Requires: A segmented mode or --list-figures
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#tracking)

#### detect-interval

- Syntax: `--detect-interval`
- Values: 0.05–2
- Units: seconds
- Default: 0.5
- Applies: Seconds between model detections; masks follow optical flow between them
- Requires: A segmented mode or --list-figures
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#tracking)

#### sensor-resolution

- Syntax: `--sensor-resolution`
- Values: integer 64–640
- Units: pixels on the longest edge
- Default: 256
- Applies: Heat-field and optional texture grid longest edge, 64-640; smaller is more abstract
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#sensor)

#### verbose

- Syntax: `--verbose`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Attach stable glyph callouts to subjects (requires a segmented thermal mode)
- Requires: --hud and a segmented mode
- Persistence: saved
- Example: [Complete recipe](examples.md#hero)

#### timecode

- Syntax: `--timecode`, `--no-timecode`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Human-readable elapsed HH:MM:SS.mmm at upper right (default: off)
- Requires: --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#hero)

#### timecode-start

- Syntax: `--timecode-start`
- Values: 0 or greater
- Units: seconds
- Default: 0.0
- Applies: Offset the displayed elapsed time, in seconds
- Requires: --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#hud-ink)

#### waveform

- Syntax: `--waveform`
- Values: `auto`, `audio`, `procedural`
- Units: not applicable
- Default: "auto"
- Applies: auto follows audio, with procedural motion for absent or silent sound; audio retains silent samples; procedural forces generated motion. Stills use procedural motion.
- Requires: --hud; audio mode requires an audio track on videos
- Persistence: saved
- Example: [Complete recipe](examples.md#vocoder)

#### wave-display

- Syntax: `--wave-display`
- Values: `plain`, `led`
- Units: not applicable
- Default: LED for digital-circuit; plain for the other six styles.
- Applies: Waveform device: plain ink or segmented LED cells; default led for digital-circuit, plain for other styles
- Requires: --hud
- Persistence: nullable
- Example: [Complete recipe](examples.md#vocoder)

#### wave-backlight

- Syntax: `--wave-backlight`
- Values: 0–1
- Units: unitless
- Default: 0.2
- Applies: Unlit LED cell brightness relative to waveform ink, 0-1; independent of glow/neon
- Requires: --wave-display led and --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#vocoder)

#### wave-style

- Syntax: `--wave-style`
- Values: `trace`, `rorschach`, `rorschach-split`, `rorschach-hollow`, `digital-blocks`, `digital-shards`, `digital-circuit`
- Units: not applicable
- Default: "trace"
- Applies: Trace, Rorschach filled/split/hollow, or digital distortion: blocks, shards, stacked segmented vocoder bars (digital-circuit)
- Requires: --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#vocoder)

#### wave-width

- Syntax: `--wave-width`
- Values: 0.02–0.3
- Units: fraction of the relevant frame dimension; see applicability
- Default: 0.12 of frame width for non-trace styles; trace has fixed layout.
- Applies: Styled waveform maximum width as a fraction of the frame, 0.02-0.3; default 0.12
- Requires: A non-trace --wave-style and --hud
- Persistence: nullable
- Example: [Complete recipe](examples.md#vocoder)

#### wave-height

- Syntax: `--wave-height`
- Values: 0.1–1
- Units: fraction of the relevant frame dimension; see applicability
- Default: 0.96 of frame height for non-trace styles; trace has fixed layout.
- Applies: Styled waveform height as a fraction of the frame, 0.1-1; default 0.96
- Requires: A non-trace --wave-style and --hud
- Persistence: nullable
- Example: [Complete recipe](examples.md#vocoder)

#### wave-detail

- Syntax: `--wave-detail`
- Values: 0–1
- Units: unitless
- Default: 0.6
- Applies: Detail, 0-1: sharper lobes in Rorschach styles or finer pixel blocks in digital styles
- Requires: --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#vocoder)

#### wave-window

- Syntax: `--wave-window`
- Values: 0.05–5
- Units: seconds
- Default: 0.6
- Applies: Trailing audio window in seconds
- Requires: --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#vocoder)

#### wave-gain

- Syntax: `--wave-gain`
- Values: 0.01–20
- Units: unitless
- Default: 1.0
- Applies: Audio waveform gain
- Requires: --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#vocoder)

#### audio-stream

- Syntax: `--audio-stream`
- Values: integer 0–100
- Units: unitless
- Default: 0
- Applies: Zero-based audio track used for waveform and output
- Requires: A video with that audio stream index
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#quality)

#### mute

- Syntax: `--mute`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Omit output audio; waveform can still follow source audio
- Requires: No additional enabling flag.
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#quality)

#### start

- Syntax: `--start`
- Values: 0 or greater
- Units: seconds
- Default: 0.0
- Applies: Trim start in seconds, relative to first video frame
- Requires: No additional enabling flag.
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#quality)

#### duration

- Syntax: `--duration`
- Values: 0.001 or greater
- Units: seconds
- Default: Remaining source duration.
- Applies: Limit conversion to this many seconds
- Requires: No additional enabling flag.
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#hero)

#### fps

- Syntax: `--fps`
- Values: 1–120
- Units: frames per second
- Default: Source frame rate; still images have one frame.
- Applies: Output constant frame rate (default: source average, capped at 60)
- Requires: No additional enabling flag.
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#catalog-scan)

#### max-size

- Syntax: `--max-size`
- Values: integer 160–8192
- Units: pixels on the longest edge
- Default: 1920
- Applies: Longest output edge; preserves aspect and never upscales
- Requires: No additional enabling flag.
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#lightweight)

#### crf

- Syntax: `--crf`
- Values: integer 0–51
- Units: unitless
- Default: 18
- Applies: H.264 quality; lower is higher quality (0-51)
- Requires: No additional enabling flag.
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#quality)

#### preset

- Syntax: `--preset`
- Values: `ultrafast`, `superfast`, `veryfast`, `faster`, `fast`, `medium`, `slow`
- Units: not applicable
- Default: "medium"
- Applies: Controls the preset.
- Requires: No additional enabling flag.
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#quality)

#### grain

- Syntax: `--grain`
- Values: 0–0.25; bare flag 0.035
- Units: unitless
- Default: 0; --sensor-texture uses 0.035 unless explicitly overridden.
- Applies: Optional grain strength, 0-0.25 (bare flag: 0.035); 0 disables. Default off unless sensor texture is enabled
- Requires: No additional enabling flag.
- Persistence: nullable
- Example: [Complete recipe](examples.md#sensor)

#### glow

- Syntax: `--glow`
- Values: 0–1
- Units: unitless
- Default: 0.65
- Applies: HUD bloom strength, 0-1
- Requires: --hud
- Persistence: saved
- Example: [Complete recipe](examples.md#lightweight)

#### seed

- Syntax: `--seed`
- Values: integer
- Units: unitless
- Default: 42
- Applies: Reproducible colors, glyphs, procedural waveform, and grain seed (default: 42)
- Requires: No additional enabling flag.
- Persistence: saved
- Example: [Complete recipe](examples.md#lightweight)

#### overwrite

- Syntax: `--overwrite`
- Values: Switch; no value argument.
- Units: not applicable
- Default: false
- Applies: Replace an existing output after successful conversion
- Requires: No additional enabling flag.
- Persistence: runtime-only
- Example: [Complete recipe](examples.md#quality)
