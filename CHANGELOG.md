# Changelog

## Unreleased

- Add three segmented looks: Silhouette for soft anatomy-guided warmth, Cinematic for broad surface patches, and Detailed for distinct exposed skin, clothing, hair, shoes, and gear. The `semantic` and `realistic` names remain aliases for Silhouette and Detailed. All three reuse the same cached models.
- Keep the original Yautja palette as the default in every mode. Add optional Redline (red/blue/black), red-only Virtual Boy, Ironbow, Green Phosphor, Amber Phosphor, White Hot, and Black Hot palettes.
- Add independent optional grain, chunky pixelation, and scanlines for both images and videos, plus the combined sensor-texture preset. Clean output remains the default; explicit controls override preset components. Detection and HUD readouts remain independent of display effects.
- Add horizontal CRT lines and seeded VHS-style color bleed, wobble, tape noise, dropouts, and tracking defects across the final image and HUD. VHS leaves the soundtrack unchanged. Virtual Boy keeps the entire result red-only, including glyphs and defects.
- Add labelled, matched animated GIFs for every thermal look, palette, and texture option in the README, with a reproducible gallery builder. Preview media stays outside the portable skill archive.
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

Yautja uses the MIT license. Separately installed dependencies and model weights retain their upstream terms; see [dependency details](references/dependencies.md).
