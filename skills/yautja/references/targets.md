# Figure selection, targets, and display effects

These options require Yautja 2.1 or newer within the supported 2.x range. All effects are optional. A scan lists detected figures, not people's identities. IDs belong to the saved catalog and its detected shots.

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

Three solid-color blades contract into a compact reticle centered on the selected bounding box, with a narrow, clear gap through each corner. The landed radius is 39% of the original enclosing-triangle radius; `--target-scale 1` selects this compact size. The broad acquisition sweep remains animated. The reticle lands in red, then alternates between red and white. A lost target disappears and reacquires when it returns; a cut resets the acquisition. Stills show the assembled primary-color triangle immediately.

| Control | Default and range |
| --- | --- |
| `--target-acquire 0.8` | Assembly duration in seconds; 0.1–5 |
| `--target-scale 1` | Multiplier for the compact reticle centered on the detected box; 0.25–3 |
| `--target-colors "#ff302b,#ffffff"` | Primary/landing and flash color, in that order; RGB hex pair |
| `--target-flash` / `--no-target-flash` | Flashing on by default for videos; off holds the primary color |
| `--target-flash-rate 1.5` | Full red/white cycles per second; 0–3; 0 disables flashing |

`--no-target-flash` keeps the assembly animation. Equal colors also hold a constant hue. The target honors `--hud-theme palette`, `--hud-theme random`, and custom `target` / `target-flash` HUD keys. An explicit `--target-colors` pair overrides those two theme colors. Defaults on Abyss remain red/white against its muted cyan HUD. Black Hot uses black for both target states with standard or palette-matched HUD colors. Virtual Boy keeps standard/matched targets red-only; explicit target colors or custom/random HUD themes can introduce other hues.

```bash
yautja "clip.mov" "abyss-target.mp4" --thermal cinematic --palette abyss --figures "figures.json" --target S001-F003 --no-target-flash --crt-vertical-lines --crt-strength 0.25 --heat-glow 0.65
```

## Independent heat glow, trails, and CRT controls

| Control | Effect |
| --- | --- |
| `--heat-glow 0.6` | Bloom and moving luminous patches from the synthetic hot regions; strength 0–1, default 0 |
| `--heat-glow-speed 1` | Glow movement rate 0–5; 0 freezes the pattern |
| `--motion-blur 0.4` | Temporal frame persistence/trails; strength 0–1, default 0 |
| `--crt-bleed 0.4` | Horizontal phosphor smear across the finished picture and HUD; strength 0–1, default 0 |
| `--crt-vertical-lines` / `--no-crt-vertical-lines` | Vertical CRT stripes, off by default; `--vertical-crt-lines` is an alias |
| `--crt-lines` / `--no-crt-lines` | Existing horizontal CRT stripes, independently selectable |
| `--crt-strength 0.12` | Darkness of either stripe direction, 0–1; 0 hides the lines |

Heat glow works with every palette, including custom and random ramps, before HUD composition. It follows synthetic heat rather than merely bright source pixels, and retains the palette's color channels. In inverted palettes such as Black Hot, it produces dark diffusion around hot regions. `--heat-glow 0` disables it. This is separate from `--glow`, the existing HUD bloom setting. Still images show a fixed glow pattern.

Motion blur is a frame-persistence effect, not an optical-flow exposure reconstruction. Higher values leave longer trails on moving subjects and overlays. It resets at detected cuts, nonmonotonic timestamps, or frame gaps over half a second. It needs successive video frames; a still has no temporal trail. CRT bleed works on both stills and videos. Both affect the complete image including selected targets, and neither changes the soundtrack or detection.

Vertical and horizontal lines can be combined. VHS, grain, pixelation, and the sensor-texture preset remain independently available. Sensor texture enables its original horizontal lines; it does not enable vertical lines, heat glow, motion blur, or CRT bleed. All new effects remain off unless requested.

## Rorschach waveforms

For a wide, mirrored inkblot column in place of the thin trace, select a Rorschach style. These work with every palette and HUD theme, using the existing `waveform` color key. The default `--wave-style trace` keeps the original waveform, its aligned glyph rows, and scale. Rorschach replaces that left panel with a nearly full-height column, leaving the upper-right readout, timecode, callouts, and targets alone.

| Setting | Shape |
| --- | --- |
| `--wave-style rorschach` | Broad, connected, mirrored lobes with shaded, spiky edges driven by waveform peaks |
| `--wave-style rorschach-split` | Broken-up lobes separated by dark gaps |
| `--wave-style rorschach-hollow` | Mirrored rings and lobes with dark interior pockets |
| `--wave-width 0.14` | Maximum Rorschach column width as a frame fraction, 0.02–0.3; default 0.12 |
| `--wave-height 1` | Rorschach height as a frame fraction, 0.1–1; default 0.96, vertically centered |
| `--wave-detail 0.6` | Detail, 0–1; 0 is broad/smooth, higher values strengthen audio-driven edge spikes and lobe complexity |

```bash
yautja "clip.mov" "inkblot.mp4" --thermal cinematic --palette redline --wave-style rorschach-hollow --wave-width 0.14 --wave-height 1 --wave-detail 0.6
```

The Rorschach transform mirrors, smooths, and compresses waveform energy so quiet ambience remains visible, shapes it into slowly drifting lobes, and optionally cuts gaps or interior pockets. Audio level controls the occupied width within the specified maximum. `--wave-gain` changes audio response and `--wave-window` changes its trailing time window. Silence inside an audible track stays empty. The existing `--waveform auto` fallback still uses a procedural signal for a wholly silent or missing track; `--waveform audio` keeps actual silence. `--waveform procedural` forces generated motion. The decorative contours are a stylized transformation, not a literal audio measurement.

Stills show the time-zero procedural shape. `--no-hud` hides it entirely. `--glow` adjusts its HUD bloom; `--crt-bleed` softens it horizontally, and `--motion-blur` leaves video trails. Higher width/detail can occupy more of the scene, so inspect the result at the intended resolution. Width and height overrides require a Rorschach style. Reports include effective `wave_style`, `wave_width`, `wave_height`, and `wave_detail`, alongside requested settings.
