# GPU/runtime implementation and validation — 2026-09-11

The complete ten-second demo averages **55.92 seconds on CUDA versus 228.68 seconds on CPU: 4.09× faster**. Full precision remains the default. This increment improves execution, diagnosis, and reproducibility; it does not change the optical-flow tracker or heat synthesis and does not establish a higher visual-quality rating.

## Delivered

- Offline `--doctor` reports the executable and environment, package metadata and actual imports, CPU selection reasons, CUDA build and hardware, a CUDA tensor execution check, and required files in both pinned model snapshots. Missing semantic dependencies are nonfatal for classic diagnosis. Doctor explicitly reports that model inference has not run.
- Semantic conversion checks actual CUDA execution before loading models, reports device/precision/backend and synchronized inference timing, and produces useful memory/driver errors without retrying on CPU. Failed or cancelled conversion preserves an existing output and removes scratch files.
- Added explicit `--precision fp32|bf16`; fp32 remains the default and bf16 requires supported CUDA. Model forwards use autocast only when requested.
- Reports separate model setup, audio analysis, frame processing, and audio mux time, with processing fps, settings, environment versions, and peak allocated/reserved CUDA memory.
- Added repository-only `scripts/benchmark.py` and `scripts/compare_precision.py`. Benchmarks use new directories, source SHA-256 hashes, exact command arrays, per-run logs/reports, output probes, and full decode checks. No model downloads occur.
- Created isolated `.venv-gpu` and `.venv-classic` environments. Preserved the existing `.venv`, which inherits system packages. Added environment ignores and `scripts/runtime.py` to the portable archive manifest.

## Workload and results

Local source: `00_project_files/create_a_video_of_explorers_wa.mp4`, SHA-256 `8709e305b32da94df5405f21639843b8e36d4301394c88425dbafcab26d0e7b4`. This private fixture and the generated evidence are ignored and absent from a fresh clone.

All runs use the complete input, 1280×720, 24 fps, 240 frames, H.264 CRF 18/medium, default warm categories and confidence 0.30, detection every 0.5 seconds, sensor resolution 256, seed 42, grain 0.035, glow 0.65, verbose annotations, timecode, and preserved audio. Models and revisions are unchanged. All six outputs completed a full FFmpeg decode and probed as exactly ten seconds of video and audio. All reported 24 detection frames, six possible cut resets, and a maximum of four tracks; those counts are not annotated accuracy measurements.

Windows, Python 3.11.9, NVIDIA RTX 4090 (24,564 MiB reported VRAM), driver 591.86. CPU uses PyTorch 2.6.0+cpu/torchvision 0.21.0+cpu. CUDA uses PyTorch 2.6.0+cu124/torchvision 0.21.0+cu124. Both use Transformers 4.57.6, NumPy 2.2.6, Pillow 11.1.0, fonttools 4.58.1, OpenCV 4.12.0.88, huggingface-hub 0.36.2, and safetensors 0.5.2. The CUDA installation passes `pip check`. The [versioned PyTorch installer](https://pytorch.org/get-started/previous-versions/#v260) supplies this matched CUDA 12.4 pair; it was chosen to match the existing CPU version, not to upgrade to the newest release.

| Metric | CPU fp32 | CUDA fp32 | CUDA bf16 |
| --- | ---: | ---: | ---: |
| Conversion run 1 | 230.77 s | 56.02 s | 55.89 s |
| Conversion run 2 | 226.59 s | 55.81 s | 54.42 s |
| Mean conversion time | 228.68 s | 55.92 s | 55.16 s |
| Mean model setup | 9.51 s | 6.59 s | 6.59 s |
| Mean frame processing | 218.79 s | 48.89 s | 48.15 s |
| Mean model inference, within frame processing | 177.27 s | 8.38 s | 7.93 s |
| Peak allocated CUDA memory | Not applicable | 2.10 GiB | 2.35 GiB |

Conversion time starts at input probing and includes model setup, processing, and muxing. The benchmark also records fresh-process wall time separately. Inference timing is synchronized and is a subset of processing time. CUDA memory is PyTorch allocator usage, not total board usage. The roughly 40.5 seconds outside model inference includes rendering, optical flow, waveform construction, decoding, and encoding; finer profiling is needed to divide that remainder.

The CPU, CUDA fp32, and CUDA bf16 series ran sequentially. Every run used a fresh process and reloaded cached models. OS file caches were not flushed, and ordinary desktop activity was uncontrolled; lightweight installation/tests also ran during the CPU series. These are repeatable local observations with two samples per mode, not isolated laboratory measurements or guaranteed cold-start figures.

## Precision and visual comparison

The precision evaluator compared five source-frame samples at 0, 2, 4, 6, and 8 seconds, resized to a 640-pixel longest edge. All 12 reference masks found same-category matches in bf16, with no unmatched subjects. Mean mask intersection-over-union was **0.99864**, minimum **0.99695**. This measures agreement with fp32, not labeled detection accuracy or tracking through occlusion. The evaluator resizes source frames directly; it is a controlled precision comparison, not an exact replay of the converter's two-stage resizing and tracking history.

Decoded final frames at 2, 5, and 8 seconds were inspected side by side. All modes retain broad warm silhouettes, cool surroundings, glyph annotations, the waveform, and the right-aligned timecode. Mean absolute RGB differences on the 0–255 scale were 1.81–2.49 for CPU versus CUDA fp32 and 2.18–3.03 for CUDA fp32 versus bf16. These differences include codec, heat-boundary, and accumulated tracking effects and are not a quality score.

For the second output in each mode, FFmpeg-decoded mono 48 kHz audio correlated with the source at **0.99982049**, measured at zero offset over their common samples. All six outputs independently passed stream-presence and duration checks. AAC re-encoding is expected to change samples.

**Decision:** retain fp32 as the default. Bf16 reduced mean total time by only 1.36% and increased peak allocated memory by about 12% in this workload. Keep it experimental until other clips show a useful benefit.

Local evidence:

- `outputs/benchmarks/cpu-fp32-2dc9h7kg/benchmark.json`
- `outputs/benchmarks/cuda-fp32-nr6l_j6n/benchmark.json`
- `outputs/benchmarks/cuda-bf16-61k3j09s/benchmark.json`
- `outputs/phase1-baseline-environment.json`, `outputs/phase1-*-doctor.json`
- `outputs/phase1-precision-masks.json`, `outputs/phase1-verification.json`
- Inspected frame comparison: `outputs/phase1-comparison.png`
- CUDA fp32 full demo: `outputs/benchmarks/cuda-fp32-nr6l_j6n/run-2.mp4`

## Reproduce

Follow the [isolated CUDA setup](semantic.md#isolated-cuda-environment-on-windows). The comparison additionally pinned the shared package versions listed above during optional-dependency installation. Existing pinned weights were reused; no model download was required. Use a local clip if the private fixture is unavailable. Run benchmark commands sequentially:

```powershell
.venv\Scripts\python.exe scripts/benchmark.py "00_project_files/create_a_video_of_explorers_wa.mp4" --device cpu --runs 2
.venv-gpu\Scripts\python.exe scripts/benchmark.py "00_project_files/create_a_video_of_explorers_wa.mp4" --device cuda --runs 2
.venv-gpu\Scripts\python.exe scripts/benchmark.py "00_project_files/create_a_video_of_explorers_wa.mp4" --device cuda --precision bf16 --runs 2
.venv-gpu\Scripts\python.exe scripts/compare_precision.py "00_project_files/create_a_video_of_explorers_wa.mp4" --times 0 2 4 6 8
```

For an independently installed CPU environment, select the matching CPU wheel pair from the official versioned installer. The historical `.venv` above is preserved for this machine's comparison; it should not be copied as an installation template. For identical rendering settings, use the saved report's `settings` object, along with its thermal/timecode/verbose values, if defaults later change.

## Automated and installation checks

Before implementation, all **27 existing tests passed**. After implementation:

- **34 tests passed** in the isolated semantic/CUDA environment, without downloading or loading model weights in tests.
- Fresh classic environment: **30 passed, four expected OpenCV tracking skips**, using NumPy 2.4.6, Pillow 12.3.0, and fonttools 4.65.0. Doctor confirms no ML packages are installed and classic readiness succeeds.
- Seven runtime/failure tests passed again after the final error-message and model-load error-handling changes. They cover partial/empty model caches, missing dependencies, device selection, unsupported bfloat16, failed CUDA tensor execution, inference failures, and real FFmpeg scratch cleanup after injected OOM/cancellation.
- Existing tests continue covering audio gaps, trim timing, HDR, rotation, frame coverage, waveform behavior, output protection, and the explicit archive manifest.
- The extracted portable archive passes classic doctor and renders a six-frame, quarter-second clip with audio and timecode. The archive contains 14 source/configuration/documentation files, with no models, private media, environments, or executables. Installed skills were not replaced.

## Remaining work

Video-memory tracking, persistent heat fields, look presets, segmentation caching, and cross-platform CI remain future phases. The image predictor still emits the existing upstream `sam2_video` configuration versus `sam2` class warning; both pinned models nevertheless executed successfully in these CPU/CUDA checks. Evaluate the actual video model/processor API in phase 2 rather than treating this image path as video memory.

The next quality experiment needs annotated crossings, occlusion, entry/exit, and true cuts, with ID-switch/lost-mask metrics and bounded history storage. The pinned Transformers version already supplies a video session API, but its feature-cache limit does not bound all frame and per-object history. GPU speed and sampled precision agreement do not establish those tracking properties.
