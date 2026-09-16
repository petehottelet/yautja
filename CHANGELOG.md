# Changelog

## 2.12.1

- Emit Relic triangles below the selected silhouette's center of mass, then float them upward before they contract and spin out. Refresh both normal-speed Relic previews.
- Draw the spherical geodesic grid with straight triangle edges, letting the 3D mesh form the curved surface. Set Focus/Relic rotation to a gentle but visible 1.8 degrees per second, preserving center fade, broken edges, pulsing satellites and node rings.
- Use Michroma with a synthesized medium weight for Murphy. Add the portable `michroma-medium` HUD font choice for captions, Tech glyphs and analysis, with accurate weight reporting and unchanged bundled font files.
- Apply the shared filled/stroked control to Fremont's scan disk, with a clear interior and complete outer/inner circles in stroked mode. Show both variants in red on neutral contact-sheet backgrounds, retaining the preset's original colors.
- Separate Focus/Relic's neon-purple HUD and glyphs from their blue grid and matching waveform. Make holographic outlines 25% thinner and bluer; give Relic's body-centered light streams and triangles a distinct violet-leaning neon pink glow matched to the reference.
- Center Relic's effect on the body core using shoulder/hip joints with a mask fallback, and replace its readable code with soft rising light filaments. Add portable [`--code-style`](skills/yautja/references/options.md#code-style) (`glyphs` or `light`); Netrunner retains glyphs and Focus keeps the effect off.
- Bring the triangle's three lock dots 15% closer together while retaining their existing sizes and cluster center. Refresh the triangle previews and complete target contact sheet.
- Reorganize the README around installation, choosing a look, customization, portable presets, output controls and troubleshooting. Retain the hero, four leading presets and two animated lock-dot reticles. The complete contact sheet shows all 11 geometric shapes, including both lock-dot designs, plus Fremont's scan disk with its fill on and off.
- Add a canonical reference covering every option family, alias, effective default, prerequisite and persistence rule, with complete runnable examples and one authoritative HUD role table. Include all three resources in the skill bundle.
- Add documentation checks for parser/reference drift, example coverage, repository links/anchors and measured preview metadata. Exercise tagged README/reference commands on generated fixtures; opt-in segmented verification uses cached local models.
- Correct comparison baselines, preview timing and dimensions, update instructions, all three glyph choices, automatic Murphy targeting and CRF/encoder examples. Move maintainer workflows and redundant comparisons into development/gallery documentation.

## 2.12.0

- Stabilize flow-aligned overlay masks with temporal blending, hysteresis, seam closing and small-island removal. New runtime controls: [`--mask-stability`](skills/yautja/references/options.md#mask-stability) and [`--mask-min-region`](skills/yautja/references/options.md#mask-min-region). Set both to zero to restore the previous contour behavior.
- Attach Relic's broken triangles to the selected figure and pack its existing code streams into the figure's width. Keep code off in Focus.
- Cool and darken Focus/Relic's source grade, grid and waveform; make their holographic outlines 20% thinner and faster. Disable decorative yellow patches in these recipes while retaining the general capability.
- Add [`--wave-display`](skills/yautja/references/options.md#wave-display) and [`--wave-backlight`](skills/yautja/references/options.md#wave-backlight): all seven waveform shapes can use segmented LED cells, with non-emissive idle ink controlled separately from glow/neon. The default digital-circuit device is unchanged.
- Add [`--outline-shine`](skills/yautja/references/options.md#outline-shine) for holographic band brightness and [`--geo-grid-rotation`](skills/yautja/references/options.md#geo-grid-rotation) for independent flat/spherical grid drift. Both remain general, portable visual settings.
- Refresh the affected segmented preset previews at normal source speed, 24 fps. Stabilized silhouettes intentionally change their former visual baselines.

## 2.11.0

- Make filled/stroked treatment distinct for all 11 target types, including hollow curved bands, crosshairs, brackets and dot rings. Reduce the triangle lock dots by 12% without changing their positions or timing.
- Replace the README target-shape GIF grid with two real-time 24 fps animations and a compact filled/stroked contact sheet for the other nine types.

- Add pulsing geodesic satellite dots and seven-sided node rings to Focus/Relic, with an independent detail switch and shared grid speed.
- Add thicker partial holographic contours with blue/lavender/white texture, plus independently styled yellow decorative scan patches on the selected current silhouette. Support both effects in CLI, reports and portable presets.

- Inset the large circle inside the Focus/Relic hexagon by 10%, keeping the smaller circles and center square unchanged.
- Fade the geodesic grid toward the center, with thicker purple lines and seeded irregular breaks. Add independent center-fade, line-width and break controls.
- Animate Relic's broken-edge triangles upward, then contract, spin and fade them away. Add ornament speed and break controls, including a frozen state.
- Triple Relic's code stream density without shrinking its glyphs; extend `--code-density` to 0–3 while preserving sparse values. Focus keeps code off and dense Relic code remains behind every subject.
- Refresh Focus, Relic and Murphy GIFs at normal source speed and 24 fps, with matching small and large previews. Keep all controls in portable schema-1 presets.

## 2.10.0

- Rename the original look to Costa Rica and HotTropic to Yautja; the new Yautja includes red HUD, cyan annotations and CRT lines. Refresh the large README hero and four compact style previews.
- Focus uses neon-purple spherical geodesic geometry and one persistent, smoothly moving hexagon with an inscribed circle, ten small targeting circles and center square.
- Add shared target movement, dwell, response, fill/stroke, selected-subject outline, caption scale and blinking cursor controls. Preserve schema-1 visual presets and explicit overrides.
- Murphy adds a blue source tint, stronger green glow, current-mask outlines, a larger center-crossing XY box, and larger Orbitron Medium captions with a thinking cursor; hide the upper-right readout.
- Remove per-feature runtime-version notes from usage documentation.

## 2.9.0

- Enable Fremont's persistent translucent circular scan target, with dark ring/crosshair marks, constant size, and smooth motion between analysis subjects. It stays visible during search and track loss, resets on cuts, and never uses the legacy acquisition zoom or flash.
- Add independent scan-target enablement, diameter and response-time controls, plus separate fill/mark HUD elements supporting color, opacity, blur and neon. Share selection and scan speed with readable analysis; keep current-frame outlines and safe text placement.
- Preserve flat schema-1 visual presets, explicit-option precedence, existing catalog targets, and the completed Focus, Relic and Murphy styles. Expand motion, lifecycle, per-element and packaged-runtime checks; refresh both Fremont GIF sizes with a full subject handoff.

## 2.8.0

- Add Focus and Relic source-scene presets with shimmering triangular grids, partial moving edge highlights, automatic hexagon targets, and pink ornaments/code behind figures.
- Add Murphy with a readable green Tech HUD, CRT scanlines, frame-spanning box reticles and target captions. Catalog-based conversion uses the lightweight runtime.
- Add independent grid, shimmer, code-layer, automatic targeting, ornament and caption options. All new HUD elements support color, opacity, blur, and neon; behind-code clips final glow against all visible silhouettes.
- Add bundled Orbitron Light, Medium and Bold fonts, selectable readable typography and validated local font overrides. Fremont now uses Orbitron Bold and thicker adjustable analysis outlines.
- Keep visual presets flat and portable in schema version 1; custom font paths remain per-conversion. Update recipes, controls, GIF examples and packaged-font checks.

## 2.7.0 — 2026-09-14

- Add Fremont: detailed red/burgundy source grading with pale highlights, white readable analysis text, moving XY search grid, automatic subject selection, and blinking white outlines. Text stays within safe margins; cuts and lost tracks restart search. Decorative telemetry is seeded, while category labels come from detections.
- Add independent analysis, cycle speed, blink rate, safe margin and source-highlight controls, per-element HUD styling, preset/report integration, and two Fremont preview sizes. Analysis outlines use current-frame contour refinement.
- Bundle unmodified Michroma Regular with its SIL Open Font License 1.1 and attribution. The font retains its own license; code remains MIT.

- Refine Vocoder Bars into rounded dark housings filled with small vertical LED segments. Audio activates bright segments with an exaggerated response above persistent dark burgundy-to-black inactive bars. Alternating row lengths stay fixed while the lit width expands with audio. Housing and idle segments follow waveform opacity and blur without emitting neon light.
- Refresh both GIF sizes with vivid red ink, stronger neon, and a wider column that makes the waveform stand out; document the matching color and glow settings.

## 2.6.2 — 2026-09-14

- Arrange Vocoder Bars as horizontal LED rows in one narrow vertical stack spanning the left edge. Local audio controls each row’s width and brightness; silent portions stay dark. Refresh both neon preview sizes.
- Halve Netrunner’s head-to-caret and caret-to-title gaps to 30/20 reference pixels while preserving caret thickness, cyan titles, and independent cropping at frame edges. Refresh both preview sizes.

## 2.6.1 — 2026-09-14

- Rename Ghost Signal to Netrunner (`--stylepreset netrunner`) and place its README example below the other presets. Existing `ghost-signal` commands and preset bases still resolve to Netrunner.
- Thicken yellow carets, expand head/caret/title spacing, and crop annotations naturally at screen edges without moving them inward or hiding a visible caret when its title is offscreen.
- Halve silhouette outline thickness and increase Netrunner code density from 65% to 95% of available columns. Refresh both animated preview sizes.
- Replace the digital circuit ladder with three segmented vocoder columns inspired by KITT’s voice display: a taller center column, shorter flanking columns, and audio-driven illumination expanding from the middle. Refresh the waveform preview with neon on its bars only.

## 2.6.0 — 2026-09-13

- Add the Ghost Signal style preset: green-tinted source scenery, warm-red neon HUD and silhouette outlines, upward-flowing code clipped to detected people/animals, and stable overhead glyph titles with yellow downward carets. Add source tint/exposure and independent subject overlay, code size/speed/density, color, blur, opacity, and neon controls.
- Add `--HUDglyphs cyber|yautja` for every alien HUD readout, waveform decoration, callout, subject title, and code stream. Bundle 192 Cyber vector glyphs with their MIT notice; human-readable timecode stays numeric. Add `--neon-core-whiten` to preserve colored cores when desired.
- Save and restore all new visual choices in presets, publish matched small/large animated examples, and document the scene/palette/glyph hierarchy. Keep prior thermal rendering and default glyphs unchanged.
- Use cyan overhead titles with consistent visible-artwork centering, larger yellow carets, and independent spacing controls. Refresh subject contours on each frame when outlines are enabled; render upward rain as bright heads and fading tails on a fixed glyph grid.
- Rename the README section to Waveforms and add three digital-distortion options with animated examples: Bitcrush Blocks, Packet Shards, and Circuit Ladder.

## 2.5.9 — 2026-09-13

- Make `pip install yautja` the primary README installation route, distinguish lightweight Classic from the segmented gallery setup, and present the agent skill as optional. Align environment and model setup guidance, retain working installations, and verify the README quick start in clean environments.
- Keep private plans and draft PRDs in the ignored `00_project_files/` directory, document the repository rule, and exclude planning-file patterns from source distributions.

## 2.5.8 — 2026-09-13

- Give the round reticle three center dots arranged in a triangle, appearing only on lock. Preserve its reduced size, four outline gaps, and existing `--target-shape round-dot` setting. Rename the gallery label to Round with three lock dots, refresh both GIF sizes, and update the CLI, API, and skill documentation (runtime 2.5.8+).

## 2.5.7 — 2026-09-13

- Reduce the final locked size of Circular crosshair, Hollow Cross, Round with lock dot, and all four square reticles by 15%. Preserve the acquisition starting size, lock timing, and both triangle designs. Refresh all seven examples in both GIF sizes with versioned README URLs. The agent skill now requires runtime 2.5.7+.

## 2.5.6 — 2026-09-13

- Add four evenly spaced gaps to the Round with lock dot outline (`--target-shape round-dot`). Keep its circular size, line thickness, center dot, and lock animation. Refresh both GIF sizes and version their README URLs. Update the agent skill to require runtime 2.5.6+.

## 2.5.5 — 2026-09-13

- Enable neon in the bundled Tropic Glow custom preset, alongside its palette-matched HUD and animated heat glow. Keep the built-in HotTropic recipe unchanged. Explain the relationship in the README and preset guide, update the save command and JSON example, and refresh both Tropic Glow GIFs with versioned image URLs.

## 2.5.4 — 2026-09-13

- Set every White Hot HUD element to light gray (`#D0D0D0`) by default, including waveform, glyphs, timecode, callouts, and both target states. Standard and palette-matched themes share this ink; alpha compositing keeps it gray over bright areas, and explicit color overrides remain available. Refresh both animated White Hot previews and version their README image URLs so stale cached previews are not reused. The agent skill now requires runtime 2.5.4+.

## 2.5.3 — 2026-09-13

- Replace Square + lock dot with Round with lock dot (`--target-shape round-dot`): a continuous circular outline with a center dot that appears only on lock. Refresh both animated preview sizes and the documentation. The former `square-dot` name is removed; other square designs remain available. The agent skill now requires runtime 2.5.3+.

## 2.5.2 — 2026-09-13

- Rename the built-in visual preset flag from `--look-preset` to `--stylepreset`, with no old flag alias. Update commands, help, examples, and the agent skill, which now requires runtime 2.5.2+. Preserve preset behavior, JSON preset files, the Python `look_preset` keyword and report key, and encoder `--preset`.

## 2.5.1 — 2026-09-13

- Remove the old `thermal-spectrum-reference-v1` preset alias. Use `--look-preset hottropic` or `"base": "hottropic"` in a preset file. Keep HotTropic's appearance unchanged and remove the compatibility wording from current documentation.

## 2.5.0 — 2026-09-13

- Add optional neon illumination for every HUD vector and text element, with bright cores, two colored halos, adjustable intensity/spread, synchronized seeded flicker, and per-element overrides. Preserve existing output when disabled; respect color, blur, opacity, target flash and final CRT/VHS controls. Black ink uses dark diffusion.
- Add the portable Abyss Neon preset, update the steady Abyss target to glowing cyan, and publish matched steady/flickering neon GIFs in both sizes. Include all controls in preset saves, conversion reports, API documentation, and the agent skill (runtime 2.5+).
- Crop reticle resampling to occupied artwork and composite emission without large float RGB buffers. A warmed 1080p CPU fixture measured 352.4 ms/frame with existing bloom and 279.6 ms/frame with neon, meeting the PRD's maximum 25% overhead target for that fixture. These figures exclude media I/O and segmentation and are not a general speed guarantee; see [method and scope](docs/performance-validation.md#neon-hud-250).

## 2.4.2 — 2026-09-13

- Replace Vector Lock with Hollow Cross: four solid, square-cornered L bands outlining an open plus, with a hollow center and uncapped arm ends. Preserve target colors, acquisition, flash, outline, blur, and opacity controls; old `vector-lock` and `iron-sights` commands and saved presets resolve to the replacement.
- Rename the style in the CLI, README, and agent skill, and refresh both GIF sizes while preserving their published image URLs.

## 2.4.1 — 2026-09-13

- Stabilize HUD callout leaders by aiming at each visible silhouette's smoothed center of area, with a nearby visible-point fallback for concave or occluded masks. Bound tracking lag during fast motion and reset history at cuts, time jumps, and track loss.
- Retain clear label positions relative to their tracks instead of repeatedly choosing a new boundary point or marginally shorter placement. Preserve fractional motion so slow pans do not accumulate rounding drift.
- Refresh the main and CRT example GIFs and document the updated default annotation behavior.

## 2.4.0 — 2026-09-13

- Add optional CRT grid and 45-degree crosshatch patterns across the complete image and HUD, with shared strength control, independent disable flags, saved-preset support, and conversion reports. Keep both off by default.
- Add labeled small and large animated examples and update the agent skill. Match the steady Abyss example's target to its muted cyan HUD.

## 2.3.1 — 2026-09-13

- Replace the iron-sights reticle with Vector Lock: angular outer guards, inward chevrons, and a center diamond that appears on lock. Preserve acquisition, flash, color, outline, blur, and opacity controls; keep `iron-sights` as an alias in commands and saved presets.
- Refresh both GIF sizes, retain their existing image URLs, and update the skill and examples for `--target-shape vector-lock`.

## 2.3.0 — 2026-09-13

- Name the eleven-color, twelve-level reference look HotTropic; preserve its exact appearance and the `thermal-spectrum-reference-v1` alias.
- Add a Cinematic starter preset for every existing palette and JSON preset discovery through `--list-presets`. Keep palettes independently adjustable and preserve the encoder's `--preset` option.
- Add local JSON preset loading, named visual-setting exports, built-in inheritance, and explicit CLI overrides. Validate data-only schemas and protect existing saves; omit source-specific selections, paths, and output/runtime settings.
- Document creation and sharing, ship an editable Tropic Glow example with the skill, and include matched small/large animated previews. Raise the skill's minimum runtime to 2.3.

## 2.2.1 — 2026-09-13

- Make White Hot's default and palette-matched waveform, glyphs, timecode, callouts, and both target states white. Preserve explicit HUD and target color overrides and refresh its small/large palette GIFs.

## 2.2.0 — 2026-09-13

- Add Thermal Spectrum — Reference 12 as a named look preset with the frozen eleven-stop palette, twelve soft thermal levels, tonal range, gamma, scalar softness, and clean HUD-free presentation. Expose independent thermal level and grading controls, preserving legacy defaults and explicit option precedence.
- Add Very Detailed thermal rendering with visible source facial features, hair, and fabric contrast. Rename Silhouette to Low Detail and simplify it to broad soft heat blobs; keep `silhouette` and `semantic` as aliases.
- Add triangle-with-lock-dots, circular crosshair, iron sights, and five square target variants. Retain the original triangle and share target acquisition, colors, flash, outline, blur, and transparency across all shapes.
- Add labelled small and large animated GIFs for the new modes, reference treatment, palette, and every target shape; raise the agent skill's minimum runtime to 2.2.

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
