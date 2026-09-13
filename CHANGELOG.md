# Changelog

## 2.1.0 — 2026-09-13

- First PyPI release of the pip-first runtime, with the matching wheel and portable agent skill bundle on GitHub. Includes the 2.0 architecture changes below.

- Add shared and per-element HUD opacity, including separate target flash opacity when requested. Apply transparency to outlines and glow as well as artwork, preserve existing defaults, and report resolved values. Match waveform, reticle, and timecode red in the Rorschach example, with blur on both waveform and reticle; add small/large transparency GIFs.

- Add an optional inward reticle outline with adjustable width and independent landing/flash colors. Add HUD-only Gaussian blur with a shared radius and separate controls for every HUD element, including targets and all waveform styles. Keep both effects off by default, preserve sharp zero overrides and black ink, report resolved settings, and include small/large animated comparisons.

- Make Black Hot's default and palette-matched waveform, glyphs, timecode, callouts, and targets black. Draw black HUD ink with alpha compositing, retain explicit color overrides, and refresh its small/large palette GIFs.
- Use a compact landed target at 39% of the original enclosing radius, with solid-color sides and open corners. Enlarge the initial compact design by 30%, reduce its stroke thickness independently by 25%, narrow its corner gaps by 40.5% (30% followed by another 15%), and remove the dark inner accent. Keep the acquisition sweep, configurable size/colors, and red/white flash; refresh small/large target GIFs.
- Sharpen Rorschach waveform edges using short audio peaks and troughs, retaining the thick mirrored core and shading. Let `--wave-detail` control edge intensity as well as lobe complexity, and refresh all three small/large animated examples.
- Add three optional audio-reactive Rorschach waveform shapes: filled mirrored lobes, separated inkblots, and hollow pockets. Expose column width, full-height layout, and lobe complexity; keep the aligned thin trace as the default. Include matched small/large animated examples.
- Add local figure scans with shot-local IDs, thumbnail contact sheets, source verification, and reusable selections for images and videos. Saved tracks support new frame rates, resolutions, and trims; conversion reports identify selected figures that did or did not appear.
- Add an animated three-blade target that assembles around selected figures, lands red, and flashes red/white. Expose assembly duration, size, flash rate, flash disable, and independent primary/flash colors. Targets support matched, custom, and random HUD colors, and disappear with `--no-hud`.
- Add the optional Abyss palette: deep blue-black scenery, amber/white-hot regions, and a muted cyan HUD. Make muted cyan available as its own HUD theme. Keep the original palette and existing defaults.
- Add independent, adjustable heat glow for every palette with configurable movement speed; retain the separate HUD glow control. Add adjustable video frame persistence, horizontal CRT phosphor bleed, and vertical CRT stripes, with shared line-strength control for either direction. All new effects default off.
- Document the complete selection workflow and controls in the CLI and thin skill. Raise its minimum runtime to 2.1, and add labelled small/large GIFs for targets, Abyss, glow in several palettes, vertical lines, and softer/stronger trails and bleed.

## 2.0 architecture — included in 2.1.0

- **Breaking:** install Yautja with pip/pipx and invoke `yautja` or `python -m yautja`. The copied-script entrypoint has been removed. The package uses a standard source layout, bundled glyph resources and a single version in `pyproject.toml`.
- Move the thin agent skill into `skills/yautja/`; build `yautja-skill.zip` with its matching application wheel. Add explicit same-environment and complete offline-wheelhouse setup, reproducible wheel/bundle checks, clean installs on every CI platform, and gated PyPI Trusted Publishing.
- Add installation context and PATH diagnostics to doctor. Keep all current flags, dependency constraints, model revisions, rendering modes and media safeguards.
- Center the audio waveform beneath the middle alien glyph, aligning the visible glyph shapes across both rows without moving the signal when symbols change. Refresh the labelled small/large GIF gallery.

- Add `--no-hud` to hide every overlay while retaining thermal coloring, textures, and sound. It overrides timecode and annotations, skips waveform analysis and glyph loading, and has linked small/large GIF examples. HUD remains enabled by default.
- Add optional palette-matched HUD colors, custom hex ramps and nine independent HUD element colors, and seeded random colors for the thermal palette, HUD, or both. Reports include the resolved color values; colors stay fixed throughout a video. Standard colors remain unchanged.
- Add three segmented looks: Silhouette for soft anatomy-guided warmth, Cinematic for broad surface patches, and Detailed for distinct exposed skin, clothing, hair, shoes, and gear. The `semantic` and `realistic` names remain aliases for Silhouette and Detailed. All three reuse the same cached models.
- Keep the original Yautja palette as the default in every mode. Add optional Redline (red/blue/black), red-only Virtual Boy, Ironbow, Green Phosphor, Amber Phosphor, White Hot, and Black Hot palettes.
- Add independent optional grain, chunky pixelation, and scanlines for both images and videos, plus the combined sensor-texture preset. Clean output remains the default; explicit controls override preset components. Detection and HUD readouts remain independent of display effects.
- Add horizontal CRT lines and seeded VHS-style color bleed, wobble, tape noise, dropouts, and tracking defects across the final image and HUD. VHS leaves the soundtrack unchanged. Virtual Boy keeps the entire result red-only, including glyphs and defects, with standard or palette-matched HUD colors.
- Add labelled, matched animated GIFs for every thermal look, palette, HUD color option, and texture in the README. Every preview links to a 960×540 version with HUD and textures rendered at that size. The reproducible gallery builder can regenerate selected examples. Preview media stays outside the portable skill archive.
- Add direct JPEG/PNG-to-PNG conversion with the shared classic and anatomy-guided semantic renderer, shaded glyph callouts, and a static HUD. Still-image conversion and `--doctor --media image` work without FFmpeg.
- Apply EXIF orientation, preserve image aspect ratio and odd dimensions, flatten transparency onto black, and omit source metadata. Protect inputs and existing outputs, reject animated PNG and video-only options, and clean up failed image exports.
- Guide human color regions with 17 estimated body landmarks from pinned ViTPose weights, including broad head, torso, arm, wrist, and leg regions.
- Replace repeated body gradients with seeded surface variation tied to body and limb axes. Uncertain landmarks and nonhuman subjects use a conservative mask-based fallback.
- Move landmarks with optical flow and smooth matched pose updates, while keeping photographic face and clothing texture out of the heat field.
- Add SciPy to semantic dependencies and include the additional pose snapshot in explicit model downloads and offline runtime checks. Existing semantic installations need to update dependencies and run `--download-models` once.

## 1.0.0 — 2026-09-12

- Local Python/FFmpeg video conversion and a portable agent skill for Claude and OpenAI Codex.
- Classic false-color rendering and optional semantic segmentation for smooth warm silhouettes against cool surroundings.
- Shaded cyan glyph callouts with varied, stable combinations and short connectors near each subject.
- Compact seven-segment LCD timecode, an audio-reactive waveform, and preserved soundtrack timing.
- A refreshed promo loop and a full ten-second demo with sound, available separately from the portable skill.
- Explicit model downloads, CPU/CUDA selection, runtime checks, and support for trims, aspect ratio, and rotation.
- Reproducible release packages, offline tests, and CI on Windows, macOS, and Linux.

Yautja uses the MIT license. Separately installed dependencies and model weights retain their upstream terms; see [dependency details](skills/yautja/references/dependencies.md).
