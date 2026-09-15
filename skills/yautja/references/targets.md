# Figure selection, targets, and display effects

This guide covers geometric reticles (`--target-*`). Fremont's independently styled persistent scan disk uses `--analysis-target-*`; see [the analysis guide](analysis.md). [All target options](options.md#target-mode) and [HUD roles](hud-elements.md) are authoritative.

All effects are optional. A scan lists detected figures, not people's identities. IDs belong to the saved catalog and its detected shots.

## List, inspect, select

Scanning needs the semantic extra and the three cached models described in [semantic.md](semantic.md). It works with both videos and JPEG/PNG stills. A video scan also needs FFmpeg. Run doctor with `--list-figures` to check scan dependencies.

```bash
yautja "clip.mov" "figures.json" --list-figures
yautja "photo.jpg" "photo-figures.json" --list-figures
```

The scan writes `figures.json` and an adjacent `figures.html` contact sheet, with cropped thumbnails, shot times, category labels, and IDs such as `S001-F003`. Standard output is a compact JSON summary; progress goes to stderr. Omitting the output path creates `<input-stem>-figures.json`. Existing catalog and contact-sheet files are protected unless `--overwrite` is authorized.

Show the contact sheet or summarized IDs. If the user specified a visible figure (for example, the rightmost explorer), resolve that choice from the thumbnails. If the selection remains ambiguous, ask which ID they want. Preserve the saved catalog when changing colors or effects; do not silently rescan or select another figure.

```bash
yautja "clip.mov" "targeted.mp4" --thermal cinematic --figures "figures.json" --target S001-F003
yautja "clip.mov" "several.mp4" --figures "figures.json" --target S001-F003,S002-F002 --target S004-F001
yautja "photo.jpg" "targeted.png" --figures "photo-figures.json" --target S001-F001
```

Select up to 16 IDs. Figures are numbered left to right when first discovered within each shot. A reappearing subject can have a new ID after a cut or track loss; select each relevant ID explicitly. Detection, shot boundaries, and tracking can be imperfect, especially during fast movement, overlaps, or occlusion. Inspect the output rather than assuming a track is always correct.

The catalog stores normalized bounding boxes, source-relative times, opacity, and the source's SHA-256. It can be reused at different output resolutions, frame rates, or trims of the **same file**. Sample interpolation stays within a shot and does not bridge missing detections. Scans default to 24 fps; change `--fps`, `--start`, or `--duration` for video when needed. A scan above 500,000 figure samples must be split into shorter sections. Editing or transcoding the source invalidates its catalog. Catalogs contain thumbnails from the original footage; keep them local unless sharing is requested.

Using a saved catalog with Classic needs only the base runtime. Selecting a segmented thermal look still needs its models. `--no-hud` suppresses targets and other overlays and skips loading the catalog. Reports include `targets`, `targets_seen`, `targets_unseen`, and `target_frames`; an unseen selection also produces a warning. Check that the requested IDs appeared in the rendered range.

## Target animation and color

Select geometry with `--target-shape`. Every shape uses the same selected figure tracks, acquisition duration, scale, red/white flash defaults, custom colors, inward outline, target blur, and opacity controls. Default `triangle` retains the existing three-blade design. Hollow Cross replaces Vector Lock; `vector-lock` and `iron-sights` remain aliases for the replacement in commands and saved presets.

| Shape | Geometry / center detail |
| --- | --- |
| `triangle-dots` | Original triangle plus three center dots; dots appear when acquisition completes |
| `crosshair` | Four radial arms and a segmented circular ring, with an open center |
| `hollow-cross` | Four thick, square-cornered L bands outline a plus; the center and all four arm ends stay open, including on lock |
| `square` | Four open corner brackets |
| `round-dot` | Circular outline with four evenly spaced gaps and three center dots arranged in a triangle: one above and two below; dots appear on lock |
| `square-cross` | Corner brackets with an open-center cross |
| `square-mil` | Corner brackets with a graduated cross |
| `square-x` | Corner brackets with four diagonal center marks |
| `hexagon` | Hexagon, circle at 90% of the inscribed radius, four outer and six inner targeting circles, central square |
| `frame-box` | Rectangle with horizontal and vertical axes crossing at its center and extending to the frame edges |

`crosshair`, `hollow-cross`, `round-dot`, `square`, `square-cross`, `square-mil`, and `square-x` lock at a compact locked size. Their acquisition still starts at the same size and contracts to the smaller final shape; `--target-scale` multiplies this final size.

Shapes contract and settle with `--target-motion acquire`. `--target-motion persistent` keeps one constant-size reticle moving fluidly between subjects. Lock dots vanish on target loss and reappear only after reacquisition; still images show the locked state immediately. Center details share the target's colors and transparency. `--no-hud` hides all shapes. Reports include `target_shape`.

Three solid-color blades contract into a compact reticle centered on the selected bounding box, with a narrow, clear gap through each corner. The landed radius is 39% of the original enclosing-triangle radius; `--target-scale 1` selects this compact size. The broad acquisition sweep remains animated. The reticle lands in red, then alternates between red and white. A lost target disappears and reacquires when it returns; a cut resets the acquisition. Stills show the assembled primary-color triangle immediately.

[All option ranges, defaults and examples](options.md); [HUD element roles](hud-elements.md).

`--no-target-flash` keeps the assembly animation. Equal colors also hold a constant hue. The target honors `--hud-theme palette`, `--hud-theme random`, and custom `target` / `target-flash` HUD keys. An explicit `--target-colors` pair overrides those two theme colors. Defaults on Abyss remain red/white against its muted cyan HUD. White Hot uses light gray and Black Hot uses black for both target states with standard or palette-matched HUD colors. Virtual Boy keeps standard/matched targets red-only; explicit target colors or custom/random HUD themes can introduce other hues.

```bash
yautja "clip.mov" "abyss-target.mp4" --thermal cinematic --palette abyss --figures "figures.json" --target S001-F003 --no-target-flash --crt-vertical-lines --crt-strength 0.25 --heat-glow 0.65
```

## Neon HUD

`--neon` illuminates all active HUD elements with a bright core and two colored halos, inspired by Saber Alight's neon tube rendering. It works on stills and video, with every palette and target shape. Default off; `--no-neon` overrides a preset.

[All option ranges, defaults and examples](options.md); [HUD element roles](hud-elements.md).

Keys: `waveform`, `waveform-axis`, `waveform-ticks`, `waveform-glyphs`, `readout`, `timecode`, `callouts`, `leaders`, `markers`, `target`. The target override covers both flash states. Hidden elements emit nothing. Tuning flags without `--neon` are validated and saved but inactive; the CLI prints a notice on stderr.

Neon follows resolved HUD colors and each reticle's current flash state. Muted cyan `#267085` emits normalized cyan `#49D7FF`; thick cores approach white. White ink gets a white halo; black ink gets dark diffusion and keeps a black core. Virtual Boy's final red-only clamp remains active for its standard and palette HUD themes.

HUD blur softens the visible core while light is derived from sharp coverage. HUD opacity and tracking fades scale core and light together, including zero. Outlines remain part of the target artwork and the halo follows its fill color. `--glow` is ignored while neon is on, with a notice for nondefault values; no legacy bloom is stacked. Heat glow is independent and runs first; CRT patterns, persistence, bleed and VHS affect the completed frame afterward. `--no-hud` disables neon with the rest of the HUD.

```bash
yautja "clip.mov" "neon.mp4" --thermal cinematic --verbose --timecode --neon
yautja "clip.mov" "cyan-target.mp4" --thermal cinematic --palette abyss --figures "figures.json" --target S001-F003 --target-colors "#267085,#267085" --no-target-flash --neon
yautja "photo.jpg" "neon.png" --neon --neon-spread 0.4 --neon-elements "waveform=0.6,timecode=0"
```

Save all controls with `--save-preset`, or start with [Abyss Neon](../assets/presets/abyss-neon.json). Reports contain requested options in `settings` and effective `neon`, `neon_intensity`, `neon_spread`, `neon_flicker`, `neon_elements`, `neon_intensities`, and `neon_flicker_seed_stream`. Effective values are false/zero when neon or HUD is off.

## Reticle stroke and independent HUD blur

Both options are off by default and work for images and videos. The reticle remains solid-colored without a stroke. Its size, blade thickness, acquisition animation, and corner gaps use the existing settings.

[All option ranges, defaults and examples](options.md); [HUD element roles](hud-elements.md).

Stroke widths and blur radii are **reference pixels at a 1080px short edge**. A value of 4 becomes 2 output pixels at 960×540 and 1 at 480×270. The same scaling applies to portrait and still outputs. Very fine outlines may round away at low resolution. Large stroke widths can cover a narrow blade; they never expand its outer boundary or close its corner gaps. Explicit outline colors remain independent of fill colors and can introduce other hues in Virtual Boy when the stroke is enabled. Black Hot's automatic outline remains black; choose an explicit color for contrast.

Available blur keys: `waveform`, `waveform-axis`, `waveform-ticks`, `waveform-glyphs`, `readout`, `timecode`, `callouts`, `leaders`, `markers`, `target`, `subject-outline`, `subject-code`, `subject-labels`, and `subject-carets`. The `waveform` key affects the trace itself or the selected Rorschach or digital shape. Axis, ticks, and flanking glyph rows have separate controls; they are absent in styled waveform modes. `readout` means the upper-right alien glyph row. `target` softens both landing and flash states, including its optional outline. There is no separate `target-flash` blur key. Changing blur does not enable a disabled timecode, callout, or target. The four subject elements are described in [Cyber and Netrunner](cyber.md).

```bash
# Soft waveform and target; keep all other HUD artwork sharp.
yautja "clip.mov" "soft-target.mp4" --figures "figures.json" --target S001-F003 --hud-blur-elements "waveform=6,target=4"

# Blur the HUD as a whole, then restore a sharp timecode and target.
yautja "clip.mov" "soft-hud.mp4" --timecode --hud-blur 3 --hud-blur-elements "timecode=0,target=0"

# Add an outline with fixed color, while retaining the red/white fill flash.
yautja "clip.mov" "outlined.mp4" --figures "figures.json" --target S001-F003 --target-stroke 4 --target-stroke-colors "#420910"
```

HUD blur softens transparent artwork before it is placed on the scene. It does not blur the underlying thermal image, change audio, alter figure tracking, or change the readout values. The existing `--glow` bloom and `--heat-glow` remain separate; CRT bleed, VHS, and motion blur still treat the finished image and can further soften overlays. `--no-hud` hides every stroke and blurred element. Explicit zero settings preserve the current sharp rendering.

Conversion reports record resolved per-element radii in `hud_blur_elements`, the outline width in `target_stroke`, its resolved landing/flash colors in `target_stroke_colors`, and reference units in `hud_effect_units`. Effective blur/stroke values become zero with HUD off; `settings` retains the user's requested values.

## HUD transparency

Use `--hud-opacity 0.5` for a shared visibility multiplier. The range is 0–1, with **0 invisible and 1 full existing visibility** (default). This is an opacity value: 0.3 means 30% opacity / 70% transparency. It scales the artwork's existing shading, subject fade, and glow, rather than removing its original styling.

Use `--hud-opacity-elements "waveform=0.3,target=0.7,timecode=0.9"` for independent overrides. Valid keys are `waveform`, `waveform-axis`, `waveform-ticks`, `waveform-glyphs`, `readout`, `timecode`, `callouts`, `leaders`, `markers`, `target`, and `target-flash`. Unspecified keys inherit the shared value. A `target` override also controls the flash unless `target-flash` is explicitly supplied. For example, `target=0.4,target-flash=0.8` makes the flash more opaque. Target opacity includes its outline and glow. Zero hides the selected element entirely, including its glow.

```bash
# Translucent HUD with a fully visible timecode.
yautja "clip.mov" "translucent.mp4" --timecode --hud-opacity 0.5 --hud-opacity-elements "timecode=1"

# Independently soften and fade a Rorschach waveform while keeping the target crisp.
yautja "clip.mov" "faded-wave.mp4" --figures "figures.json" --target S001-F003 --wave-style rorschach --hud-blur-elements "waveform=6" --hud-opacity-elements "waveform=0.3,target=0.7"
```

Opacity works with any palette, black or custom HUD ink, images, videos, blur, and reticle strokes. It affects HUD artwork only. Disabled elements stay disabled, and `--no-hud` overrides all opacity settings. Zero opacity hides artwork but does not turn off analysis; use `--no-hud` to skip unused HUD analysis entirely. Reports contain the resolved `hud_opacity` and `hud_opacity_elements`; effective values are zero with HUD off while `settings` retains the requested values.

For the same red in the waveform, timecode, and both reticle states, set `--hud-theme custom --hud-colors "waveform=#ff302b,timecode=#ff302b" --target-colors "#ff302b,#ff302b"`. Custom ink uses alpha compositing; the standard screen blend can shift red toward pink over a blue background. Soft edges and partially transparent artwork still blend naturally with the scene.

## Independent heat glow, trails, and CRT controls

For HUD-only softness and target outlines, see [reticle stroke and independent HUD blur](#reticle-stroke-and-independent-hud-blur).

[All option ranges, defaults and examples](options.md); [HUD element roles](hud-elements.md).

Heat glow works with every palette, including custom and random ramps, before HUD composition. It follows synthetic heat rather than merely bright source pixels, and retains the palette's color channels. In inverted palettes such as Black Hot, it produces dark diffusion around hot regions. `--heat-glow 0` disables it. This is separate from `--glow`, the existing HUD bloom setting. Still images show a fixed glow pattern.

Motion blur is a frame-persistence effect, not an optical-flow exposure reconstruction. Higher values leave longer trails on moving subjects and overlays. It resets at detected cuts, nonmonotonic timestamps, or frame gaps over half a second. It needs successive video frames; a still has no temporal trail. CRT bleed works on both stills and videos. Both affect the complete image including selected targets, and neither changes the soundtrack or detection.

Grid is equivalent to enabling vertical and horizontal lines together. Requesting grid alongside either individual direction does not double that direction's darkening. Crosshatch can be combined with either direction or grid; intersections are darker. All line patterns are fixed to the display on both stills and videos, affect the HUD, and work with every palette. Save `crt_grid` and `crt_crosshatch` as booleans in custom presets; their independent disable flags override saved settings. Conversion reports include both resolved values and requested settings.

VHS, grain, pixelation, and the sensor-texture preset remain independently available. Sensor texture enables its original horizontal lines; it does not enable vertical lines, grid, crosshatch, heat glow, motion blur, or CRT bleed. All new effects remain off unless requested.

## Waveforms

For a wide, mirrored inkblot column in place of the thin trace, select a Rorschach style. These work with every palette and HUD theme, using the existing `waveform` color key. The default `--wave-style trace` keeps the original waveform, its aligned glyph rows, and scale. Rorschach replaces that left panel with a nearly full-height column, leaving the upper-right readout, timecode, callouts, and targets alone.

| Setting | Shape |
| --- | --- |
| `--wave-style rorschach` | Broad, connected, mirrored lobes with shaded, spiky edges driven by waveform peaks |
| `--wave-style rorschach-split` | Broken-up lobes separated by dark gaps |
| `--wave-style rorschach-hollow` | Mirrored rings and lobes with dark interior pockets |
| `--wave-style digital-blocks` | Bitcrush Blocks: broad pixel slabs with square cutouts |
| `--wave-style digital-shards` | Packet Shards: detached, unequal pixel packets displaced around the axis |
| `--wave-style digital-circuit` | Vocoder Bars: rounded horizontal bars filled with vertical LED segments, bright active segments over dim, persistent inactive bars |
| `--wave-width 0.14` | Maximum styled waveform width as a frame fraction, 0.02–0.3; default 0.12 |
| `--wave-height 1` | Styled waveform height as a frame fraction, 0.1–1; default 0.96, vertically centered |
| `--wave-detail 0.6` | Detail, 0–1; 0 is broad/smooth, higher values strengthen audio-driven edge spikes and lobe complexity |

```bash
yautja "clip.mov" "inkblot.mp4" --thermal cinematic --palette redline --wave-style rorschach-hollow --wave-width 0.14 --wave-height 1 --wave-detail 0.6
```

The Rorschach transform mirrors, smooths, and compresses waveform energy so quiet ambience remains visible, shapes it into slowly drifting lobes, and optionally cuts gaps or interior pockets. Audio level controls the occupied width within the specified maximum. `--wave-gain` changes audio response and `--wave-window` changes its trailing time window. Silence inside an audible track stays empty. The existing `--waveform auto` fallback still uses a procedural signal for a wholly silent or missing track; `--waveform audio` keeps actual silence. `--waveform procedural` forces generated motion. The decorative contours are a stylized transformation, not a literal audio measurement.

Blocks and Shards quantize audio energy onto square pixel cells. Lower `--wave-detail` makes larger blocks, while higher values increase pixel density. Width, height, audio controls, HUD color, blur, opacity, and neon apply to all six styled waveforms. Blocks and Shards disappear at silence; Vocoder Bars retain their dim inactive segments. Stronger audio widens all three styles; Vocoder Bars also brighten. Packet Shards also rearranges packets in seeded time steps.

Stills show the time-zero procedural shape. `--no-hud` hides it entirely. `--glow` adjusts its HUD bloom; `--crt-bleed` softens it horizontally, and `--motion-blur` leaves video trails. Higher width/detail can occupy more of the scene, so inspect the result at the intended resolution. Width and height overrides require a non-trace style. Reports include effective `wave_style`, `wave_width`, `wave_height`, and `wave_detail`, alongside requested settings.

Vocoder Bars use one vertical stack of rounded horizontal rows, alternating shorter and longer bars. Each contains small vertical LED segments. Audio activates bright segments with a pronounced response; inactive segments remain dim burgundy-to-black with red ink, or a dim version of another chosen ink color. The dark casing and inactive segments share waveform opacity and blur, and emit no light. Use `--wave-width 0.09 --wave-height 1` to match the narrow, full-height gallery example. Casings and idle segments stay fixed while local audio energy controls the width and brightness of the illuminated segments. `--wave-detail` controls row count; silence turns active lights off while keeping the inactive bars visible. The reference preview uses `--hud-theme custom --hud-colors "waveform=#FF302B"` and `--neon --neon-intensity 0 --neon-elements "waveform=1.2" --neon-spread 0.4 --neon-core-whiten 0` for vivid red active segments with a strong halo above dim burgundy inactive segments. All colors and neon controls remain configurable.

## Shared targeting controls

All 11 target types accept `--target-fill filled` and `--target-fill stroked`. Filled mode uses solid marks and dots, plus translucent enclosed interiors. Stroked mode traces the edges of every mark: blades, curved bands, crosshairs and brackets become hollow outlines, and lock dots become rings. Thin enclosure lines remain contours. `auto` keeps each shape's original treatment. `--target-stroke` is a separate optional colored border. `--target-mode cycle` selects one subject at a time, and `--target-hold` sets its dwell time. Persistent motion uses `--target-response`; current-mask outlines use `--target-outline` and the independent `target-outline` HUD role. Caption size and blinking cursor are controlled by `--target-label-scale` and `--target-cursor`. See the [full ranges and examples](focus.md#grid-targets-and-captions).

The three lock dots in `triangle-dots` are 12% smaller in diameter, with their positions and acquisition timing unchanged. The `round-dot` dots retain their size. The README shows these two animations at normal source speed and 24 fps, followed by a [compact filled/stroked contact sheet](https://github.com/petehottelet/yautja/blob/main/assets/examples/target-shapes.png) of the other nine types.
