# Yautja 1.0 review — 2026-09-12

The release has a clear visual identity, a portable local converter, and strong coverage of media handling. A ten-out-of-ten assessment would need broader footage evaluation and better temporal consistency; one attractive demo cannot establish either.

## Verified strengths

- Semantic mode creates smooth warm silhouettes against cool backgrounds, with shaded cyan callouts, compact LCD timecode, and a waveform driven by the source audio.
- The latest cached-model render processed the complete ten-second explorer clip into 240 frames at 1280×720/24 fps. Video and audio both last ten seconds; decoded audio correlation with the source is 0.99992.
- That render took 60.3 seconds on the RTX 4090 in fp32, including 8.705 seconds of model inference. This is one measured run, not a general performance guarantee. Historical repeated CPU/CUDA comparisons are recorded in the [phase 1 report](references/phase1-validation.md).
- The current suite contains 44 tests. CI covers Windows, macOS, and Linux, including Python 3.10/3.11 and lightweight/optional-tracking configurations. Release automation tests the tagged source and publishes a reproducible archive and checksum.
- The portable archive has an explicit 15-file manifest. Demo media, Python environments, model weights, and private source footage are excluded. Runtime diagnosis and explicit model downloads make setup failures easier to understand.

## Improvements with the highest return

1. **Make motion more stable.** Build a small annotated set of crossings, occlusion, arm movements, camera pans, and cuts. Compare the existing optical-flow tracker with [SAM 2 video-memory propagation](https://huggingface.co/docs/transformers/model_doc/sam2_video) in the pinned runtime. Promote it only if ID switches, lost masks, false warm regions, runtime, and memory improve enough for the intended use. Carry each subject's heat field through motion so an extended arm does not shift the entire body gradient. Keep heat inside the current visible mask.
2. **Make visual iteration faster.** Cache segmentation and track results independently of the palette and HUD, with source/settings hashes, bounded storage, and invalidation checks. Then changing glyph size, glow, or color can reuse the expensive analysis. Profile heat rendering, HUD composition, optical flow, and encoding first: model inference accounted for only about 14% of the latest end-to-end render.
3. **Make the first result match the promo.** Add a guided local setup and short-preview command that checks the environment, explains model downloads, and uses semantic mode with the shown HUD settings. Offer a small set of named looks with explicit overrides, while keeping the encoder's existing `--preset` option unambiguous. Keep the CLI usable independently of any future interface.
4. **Prove quality beyond the explorer clip.** Add permissioned examples covering portrait video, animals, crowds, low light, held objects, bright foliage, and no-subject scenes. Measure missed/false masks, heat flicker, label readability, runtime, and memory. Add a controlled real-model smoke check alongside the existing offline CI.

The [implementation plan](IMPLEMENTATION_PLAN.md) gives acceptance criteria for these changes. The next engineering step should establish the evaluation baseline before replacing tracking or heat synthesis.

## Presentation refinements included

The regenerated five-second promo appears before setup instructions. A matching still, the full demo with sound, and a downloadable promo GIF make the effect easier to inspect. The source remains local; the processed demo is distributed separately from the skill archive.

## Limits

The current tracker uses periodic SAM image masks and optical flow. It can lose tracks during occlusion and confuse exposure changes with cuts. Heat is recomputed from each current mask's bounding rectangle; held objects may share a person's warmth. Offline tests check implementation mechanics, not general detection accuracy. The colors are an entertainment effect and do not measure temperature or guarantee anonymity.
