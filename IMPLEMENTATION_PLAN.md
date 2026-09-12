# Yautja: implementation plan for 9/10 and 10/10 quality

## 1.0 release status — 2026-09-12

The current release has 44 automated tests, a 15-file portable archive, CI on Windows/macOS/Linux, and automated release packaging. Shaded callouts, compact LCD timecode, and refreshed promo media are implemented. Historical counts and timings below describe earlier milestones; use the [current review](REVIEW.md) for the latest assessment. Video-memory tracking, persistent heat fields, named looks, segmentation caching, and a broader real-footage benchmark remain planned work.

## Objective

Improve Yautja's sci-fi-styled image segmentation, re-skinning, and annotation of local video through faster inference and stable subject tracking. Preserve the abstract thermal-imaging look, alien glyphs, audio-driven waveform, and optional timecode. Output is for entertainment only: re-skinning colors are algorithmically generated with some randomness, not measured temperatures.

Implement phases 1–3 first. They are the highest-value next release. Phases 4–6 add usability and the validation needed to justify a higher quality rating. These ratings are review goals, not measured guarantees.

This is a staged roadmap. The first implementation increment adds GPU/runtime diagnosis, explicit device errors, precision controls, and a repeatable benchmark runner. Video-memory tracking, persistent heat fields, visual presets, and segmentation caching remain future work. Completion requires the evidence listed under each phase.

## Review improvements — 2026-09-11

1. **Move baseline evidence ahead of algorithm changes.** Start the benchmark harness and offline failure tests in phase 1, then add a small annotated tracking set before phase 2. Leave the larger release matrix in phase 6. Record source hashes, complete settings, actual loaded runtime versions, synchronized GPU inference time, processing time, and end-to-end time. Compare repeated runs sequentially; a second fresh process has warm file caches, not resident models. Do not call the first run cold unless caches are controlled.
2. **Make diagnosis a readiness ladder.** Distinguish installed package metadata, successful imports, complete pinned cache files, a CUDA tensor operation, and real model inference. A directory or CUDA availability flag is insufficient. A doctor check must explicitly state that it does not validate model inference or weight integrity. Use an isolated environment without inherited system packages; the existing `.venv` inherits them and is retained as a historical baseline.
3. **Keep phase 2 an experiment with a promotion gate.** Transformers 4.57.6 already contains `Sam2VideoModel`, `Sam2VideoProcessor.init_video_session`, and streaming frame support. Evaluate that pinned API before upgrading dependencies. Its vision-feature cache limit does not bound `processed_frames`, per-object outputs, or tracking history. Design and test eviction/chunk boundaries explicitly. Keep optical flow as the default until matched examples demonstrate an improvement.
4. **Define the tracker/heat contract before persistence.** Require a shot generation, track ID, current visible mask, confidence/visibility, timestamp, and alignment information. Test resets, re-entry, expiry, and occlusion against that contract before attaching heat memory. A bounding-box translation alone cannot establish stability under articulation.
5. **Avoid ambiguous controls.** `--preset` already selects the H.264 encoder preset; introduce `--look` for cinematic/abstract/clean styles. Keep inference precision explicit (`fp32` default, experimental `bf16` on compatible CUDA). Define future cold-object subtraction before warm/hot composition, including how an explicit hot override wins; validate held-object masks before promising that behavior.
6. **Follow the measured bottleneck.** Initial full-clip CUDA runs take about 56 seconds versus 229 seconds on CPU. Only about 8.5 seconds of CUDA processing is model inference; roughly 40 seconds is the rest of frame processing, including heat/HUD rendering, optical flow, decoding, and encoding. Add finer profiling before pursuing more inference-only speedups. GPU acceleration alone does not improve silhouettes or justify a higher visual-quality rating.

Phase 1 is implemented and verified: **228.68 seconds CPU versus 55.92 seconds CUDA fp32**, averaged over two full-clip runs each. All 34 tests pass in the isolated semantic environment; a fresh classic environment passes 30 with four expected optional-tracking skips. Bfloat16 remains experimental after measured comparison. See [commands, evidence, and limitations](references/phase1-validation.md). Phase 2 starts with an annotated evaluation of the existing video API; it does not automatically replace the tracker.

## Existing implementation and baseline

- `scripts/yautja.py`: CLI, FFmpeg decoding/encoding, audio analysis, conversion reports.
- `scripts/semantic.py`: Grounding DINO tiny detection, SAM 2.1 tiny image masks, optical-flow tracking, periodic detection, shot-local IDs.
- `scripts/runtime.py`: pinned model metadata, offline dependency/cache diagnosis, device execution checks.
- `scripts/benchmark.py`, `scripts/compare_precision.py`: reproducible developer benchmarks and sampled precision agreement.
- `scripts/thermal.py`: smooth simulated heat fields derived from subject masks.
- `scripts/render.py`: thermal palette, glyph HUD, annotations, and timecode.
- `requirements-semantic.txt`: optional ML dependencies; Transformers is currently pinned to `4.57.6`.
- `scripts/package_skill.py`: explicit manifest for portable skill archives.
- `tests/test_yautja.py`, `tests/test_thermal.py`: conversion and rendering/tracking tests.
- `tests/test_runtime.py`: offline diagnosis, CUDA error behavior, and failed/cancelled conversion cleanup.
- `references/dependencies.md`, `references/semantic.md`, `references/runtime.md`: licenses, setup, behavior, and limitations.

Recorded baseline: 27 automated tests passed before the subsequent timecode alignment change; the relevant existing timecode test passed after that change. Rerun the suite before implementation.

The complete local jungle demo rendered in **228.31 seconds on CPU**, producing **240 frames at 1280×720/24 fps**, with ten seconds of video and audio. Hardware inspection confirmed an **RTX 4090 with approximately 24 GB VRAM**, but the tested Python environment used CPU-only PyTorch.

The existing demo source is `00_project_files/create_a_video_of_explorers_wa.mp4`. It is private, ignored, and unavailable in a fresh clone. Do not make portable tests depend on it. Previous verification is in `outputs/explorers-semantic-verification.json` when present.

## Constraints to preserve

- Keep the project's new code MIT. Dependencies and model weights retain their upstream licenses. Use the strategy recorded in `references/dependencies.md`; do not describe the entire runtime as MIT.
- Continue using the currently selected Apache-2.0 Grounding DINO and SAM 2.1 models unless a replacement's code and weight licenses are separately verified. Do not substitute SAM 3 by name similarity.
- Pin model revisions. Require explicit model downloads, use cached files for ordinary conversion, and do not execute remote model code or upload footage.
- Keep `--thermal classic` as the default lightweight mode. It must work without the ML dependencies.
- Preserve `--verbose` as the option for glyph annotations, not diagnostic logging.
- With `--timecode`, align the alien glyph block and timecode to the same right edge in the top-right corner. Keep them inside the frame.
- Preserve aspect ratio, rotation, audio selection, audio timestamp gaps, trim timing, and output protection. Commit output only after successful conversion; clean temporary files on failure or cancellation.
- Preserve existing unrelated worktree changes. Inspect the current diff before editing. The deleted CI workflow is an existing change; adding a replacement belongs to phase 6.
- Keep private footage, weights, caches, credentials, and executables out of Git and the portable skill archive. Update the explicit archive manifest only for files the installed skill needs.
- Describe the result as an artistic heat simulation. It does not measure temperature, material insulation, or whether equipment is operating.

## Phase 1 — GPU execution and runtime diagnostics

**Purpose:** use the available GPU and make setup failures understandable.

Primary files: `scripts/yautja.py`, `scripts/semantic.py`, dependency/setup documentation.

- [x] Record the current dependency versions and benchmark command before changing the environment.
- [x] Create a separate isolated GPU environment, preserving the working CPU environment. Install a compatible CUDA-enabled PyTorch/torchvision pair using current official installation guidance. Keep CUDA-specific installation separate from portable CPU requirements.
- [x] Verify CUDA with an actual tensor operation and a real model inference. Driver presence alone is insufficient.
- [x] Extend `--doctor` to report the selected environment, PyTorch version, CUDA availability, GPU name/VRAM, optional dependency status, and availability of both pinned model snapshots. Do not download models during diagnosis.
- [x] Make missing semantic dependencies nonfatal for a classic-mode runtime check. A semantic-mode check should clearly report what needs installation.
- [x] Keep `--device cuda` failures explicit. If `auto` selects CPU, report that choice and the reason. Never silently retry an explicit CUDA request on CPU after an inference error.
- [x] Evaluate mixed precision where supported; compare masks and final output before enabling it. Handle out-of-memory failures with a useful error and normal output cleanup. Bfloat16 is opt-in, not the default.
- [x] Benchmark CPU and GPU with identical footage, resolution, frame rate, detection settings, and output quality. Report model-loading time separately from processing time and distinguish cold/warm runs. Both repeat runs reload cached models; OS cache state is explicitly uncontrolled, with no guaranteed cold-cache claim.

**Acceptance:** the real demo completes on CUDA, preserves all frames and audio, reports its actual device, and has a recorded comparison against the CPU baseline. Classic mode still works in an environment without ML packages. GPU acceleration must not be called complete based only on `torch.cuda.is_available()`.

## Phase 2 — Video-memory tracking

**Purpose:** improve silhouettes and IDs through movement and partial occlusion.

Primary files: `scripts/semantic.py`, CLI integration, tracking tests.

- [ ] Evaluate SAM 2.1's video-memory predictor against the existing optical-flow implementation on the same clips. Verify the API against the installed Transformers version before changing dependencies; assess Windows portability if using Meta's native implementation.
- [ ] Keep Grounding DINO for initial discovery, periodic discovery of new subjects, and recovery of lost tracks. Preserve warm/hot category controls and confidence thresholds.
- [ ] Introduce a small tracking-backend interface so the current optical-flow implementation remains available for comparison and lightweight fallback. Report the selected backend explicitly.
- [ ] Maintain IDs within each shot without treating them as individual identities. Define matching, disappearance, re-entry, duplicate suppression, confidence decay, and expiry behavior.
- [ ] Reset state at cuts. Evaluate cut detection against actual cuts, flashes, exposure changes, and fast pans so a brightness change alone does not unnecessarily discard all tracks.
- [ ] Prevent masks from persisting visibly over an occluder or after the subject disappears.
- [ ] Bound frame and tracking memory for long videos. If processing in chunks, verify that boundaries preserve IDs and heat continuity; do not assume the upstream predictor automatically bounds every frame cache.
- [ ] Include tracking backend, resets, model revisions, and relevant timing in the conversion report.

**Acceptance:** annotated examples of crossing subjects, partial occlusion, new arrivals, and scene cuts show a documented improvement over optical flow. Report ID switches, lost subjects, false masks, runtime, and peak memory. Tests cover state reset and expiry without requiring network access.

## Phase 3 — Persistent, more plausible heat fields

**Purpose:** keep simulated warmth attached to the subject while maintaining abstraction.

Primary files: `scripts/thermal.py`, tracker-to-renderer data flow, thermal tests.

Current weakness: heat gradients are recalculated from each mask's bounding rectangle. Extending an arm changes that rectangle and can shift warmth across the whole body.

- [ ] Maintain a low-resolution scalar heat field per track. Move it with the subject and reconcile it gradually with updated masks instead of rebuilding the entire pattern from a changing rectangle.
- [ ] Initialize newly visible regions smoothly, constrain heat to the current visible mask, and reset appropriately at cuts or expired tracks. Avoid trails, sudden reheating, and heat leaking onto an occluder.
- [ ] Use silhouette-aware, broad variations that follow body regions. Preserve the absence of facial features and clothing texture. Do not blend source RGB detail back into the subject.
- [ ] Add conservative controls for objects accidentally included in person masks, such as backpacks, paper, and bottles. A proposed `--cold-objects` option should have documented precedence relative to warm/hot overrides. Do not claim material understanding unless it is actually implemented and validated.
- [ ] Keep undecided environmental regions cool. Preserve the explicit cool-only result when no requested subject is detected.
- [ ] Tune boundary softness, internal contrast, and optional heat bloom in scalar space before applying the palette. Keep HUD rendering afterward so glyphs remain crisp.
- [ ] Keep sensor/grain behavior reproducible for a seed. Test for temporal flicker and boundary stability as well as attractive still frames.

**Acceptance:** compare clips containing arm extension, turning, walking, and partial occlusion. Interior warmth should remain stable under articulation, backgrounds should stay cool, and identifying photographic detail should remain suppressed. Include both qualitative comparisons and measured frame-to-frame heat changes in aligned subject regions.

## Phase 4 — Annotation and preset polish

Primary files: `scripts/render.py`, `scripts/yautja.py`, documentation.

- [ ] Improve annotation placement to reduce crossing leaders and avoid covering other labels, major subject regions, or the existing HUD.
- [ ] Smooth anchor motion, fade uncertain/lost targets, and suppress duplicate targets. Preserve stable category and ID glyphs while a track exists.
- [ ] Handle portrait, square, and small outputs with fewer labels when necessary. Keep the shared right alignment of the top-right glyph block and timecode.
- [ ] Add tested `--look cinematic`, `--look abstract`, and `--look clean` styles with clear differences. Keep the existing encoder `--preset` unchanged. Explicit CLI arguments must override look defaults; do not silently switch inference backends or thermal modes.
- [ ] Add a convenient short-preview workflow with a new output path and clear trim/timing information. Keep full conversion separate from preview completion.
- [ ] Refresh examples only from actual converter output and record the exact commands used.

**Acceptance:** compare presets on the same footage, inspect labels through movement, and check portrait and landscape layouts. Preset precedence is documented and tested. No labels overlap the timecode or main waveform panel.

## Phase 5 — Reuse segmentation and support long work

Primary files: new cache module if justified, `scripts/yautja.py`, package manifest, documentation.

- [ ] Cache masks and track metadata separately from heat rendering and HUD composition so palette, grain, glow, timecode, and label changes can reuse segmentation.
- [ ] Define a versioned cache format. Key it on source content, trim, rotation/orientation, analysis dimensions, frame timestamps, model revisions, backend, categories, thresholds, and other settings that affect segmentation. Do not rely only on the filename.
- [ ] Write cache chunks atomically and reject incompatible or incomplete entries. Make cache location, storage use, invalidation, and cleanup explicit.
- [ ] Add resumable analysis without duplicate/missing frames or discontinuous IDs at resume boundaries. Keep final output protected until encoding and audio muxing succeed.
- [ ] Add an explicit trim-only audio-calibration option for short previews of long recordings. Retain whole-track calibration as a documented option and preserve timestamp gaps in both modes.

**Acceptance:** changing only HUD/palette settings invokes no model inference when the cache is valid. Changing an analysis setting invalidates the appropriate cache. Interrupted analysis resumes with verified frame coverage and stable timing. A long-video run demonstrates bounded RAM and documents scratch-disk requirements.

## Phase 6 — Quality evidence and release reliability

- [ ] Assemble a small, rights-cleared benchmark covering people, animals, crowds, bright foliage, low light, held objects, camera movement, occlusion, cuts, portrait video, and clips with no warm subjects. Keep private fixtures separate and document their absence in a clone.
- [ ] Annotate representative masks and track identities. Establish baseline measurements before tuning, then set acceptance thresholds for the intended use. Include difficult clips, not only the jungle demo.
- [ ] Record mask quality, ID switches, false hot regions, aligned heat flicker, annotation readability, render speed, and peak RAM/VRAM. Report failures and skipped checks alongside successes.
- [ ] Add Windows/macOS/Linux CI for classic conversions and offline unit tests, plus optional tracking tests. Use a separate opt-in or scheduled real-model job with a controlled model cache; ordinary tests must not download weights.
- [ ] Verify a fresh classic installation, a fresh semantic installation, a cached offline conversion, and installation/execution from the extracted portable archive.
- [ ] Test cancellation, missing models, corrupt inputs, existing outputs, audio gaps, trims, HDR, rotation, and variable frame rate after pipeline changes. Reuse existing tests where they already establish the behavior.
- [ ] Verify licenses of exact new dependency/model versions, update provenance documentation, and keep dependencies under their own terms. Recheck the fixed archive manifest for accidental media or weight inclusion.

**Acceptance:** publish a reproducible benchmark report and install instructions with tested versions. A 9/10 claim should be supported by better output and usable performance; a 10/10 claim also needs repeatable results across the supported cases and environments.

## Implementation order and handoff

1. Inspect the worktree, preserve existing changes, run the current suite, and record the baseline. Introduce the benchmark harness and offline failure tests now, before changing tracking or heat synthesis.
2. Complete phase 1 and retain a working CPU path.
3. Annotate a small set of actual video examples, establish optical-flow metrics, then compare and implement phase 2. Promote video memory only after its quality and memory gates pass.
4. Build phase 3 on the stabilized tracking interface.
5. Finish annotation/preset polish, caching, and release validation in that order.

For each phase, deliver the focused code changes, relevant tests, a reproducible verification command, observed limitations, and documentation updates. Build a new skill archive when its runtime files change. Keep model downloads, environment changes, and measured results explicit in the handoff.

Do not publish a repository, create a release, upload footage, or replace installed skills as an incidental part of implementing this plan. Those are separate delivery actions.

## Primary references

- [PyTorch installation and CUDA selection](https://pytorch.org/get-started/locally/)
- [SAM 2 repository, video predictor, and licensing](https://github.com/facebookresearch/sam2)
- [Transformers SAM 2 video documentation](https://huggingface.co/docs/transformers/model_doc/sam2_video)
- [Grounding DINO tiny model card](https://huggingface.co/IDEA-Research/grounding-dino-tiny)
- [SAM 2.1 tiny model card](https://huggingface.co/facebook/sam2.1-hiera-tiny)
- [Project dependency review](references/dependencies.md)
- [Existing project review](REVIEW.md)

Upstream documentation can change. Check API compatibility and license terms against the exact versions selected during implementation.
