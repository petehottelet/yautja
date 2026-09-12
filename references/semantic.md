# Segmentation and thermal-style re-skinning

The optional semantic mode detects subjects with Grounding DINO tiny, segments their silhouettes with SAM 2.1 tiny, and re-skins them with algorithmically generated color fields for a sci-fi thermal-imaging look. It keeps vegetation and scenery cool, even when they are bright. Body interiors use smooth, object-relative color regions rather than facial features or clothing texture. Seeded grain adds some random variation. This effect is for entertainment only; neither model measures temperature, clothing insulation, engine state, or whether an object is alive.

## Setup and use

Keep the lightweight environment if you only need classic mode. For semantic mode, install the optional dependencies in a virtual environment:

```bash
python -m pip install -r requirements-semantic.txt
python scripts/yautja.py --download-models
python scripts/yautja.py "clip.mov" "outputs/clip-semantic.mp4" --thermal semantic --verbose --timecode
```

Use your environment's Python executable for these commands. The explicit download command fetches about 850 MB of pinned model weights and configuration from Hugging Face into its standard cache. It requires network access once. Subsequent conversions require cached files and do not download models or upload frames. No account is normally required. The archive does not include weights, Python packages, or FFmpeg. For a fully offline machine, transfer the complete Hugging Face cache and preserve its upstream notices.

`--device auto` selects CUDA if available, otherwise CPU. A CUDA-capable card also needs CUDA-enabled PyTorch; CPU-only PyTorch will use CPU even if a GPU is installed. Install a compatible PyTorch/torchvision pair using the [official PyTorch installer](https://pytorch.org/get-started/locally/). Start with a five-second sample. CPU processing is substantially slower than classic mode.

### Diagnose before conversion

```bash
python scripts/yautja.py --doctor
python scripts/yautja.py --doctor --thermal semantic --device cuda
```

Doctor reports the executable, environment, package versions and import failures, CUDA build, selected device and reason, GPU name/VRAM, and required files from both pinned model snapshots. A selected CUDA device must complete a small tensor operation. It never downloads weights or performs model inference; `ready` means the prerequisites passed, not that weight integrity or a real model render has been verified. Missing or broken optional ML packages remain nonfatal for the default classic check. A semantic check exits with status 1 if prerequisites fail.

Conversions print the actual device and selection reason. An explicit CUDA request never retries inference on CPU. Memory or driver failures preserve the protected output and remove conversion scratch files. `--verbose` continues to control glyph annotations.

### Isolated CUDA environment on Windows

The phase 1 comparison uses Python 3.11 with PyTorch 2.6.0/torchvision 0.21.0 CUDA 12.4, matching the historical CPU versions. This is a reproducible comparison pair, not a claim that it is the newest release. The pair and wheel index are listed in the [official versioned installation instructions](https://pytorch.org/get-started/previous-versions/#v260). Preserve your working environment:

```powershell
python -m venv .venv-gpu
.venv-gpu\Scripts\python.exe -m pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cu124
.venv-gpu\Scripts\python.exe -m pip install -r requirements-semantic.txt
.venv-gpu\Scripts\python.exe scripts/yautja.py --doctor --thermal semantic --device cuda
.venv-gpu\Scripts\python.exe scripts/yautja.py "clip.mov" "outputs/clip-cuda.mp4" --thermal semantic --device cuda --verbose --timecode
```

Do not add `--system-site-packages`. CUDA-specific wheels stay separate from portable requirements. The regular Hugging Face model cache can be shared with the CPU environment; if doctor finds missing files, run `--download-models` explicitly with the new environment's Python. The converter neither downloads a driver nor changes your existing environment.

Full precision (`--precision fp32`) remains the default. `--precision bf16` enables experimental CUDA bfloat16 autocast on compatible hardware and fails clearly on CPU or unsupported GPUs. Compare masks and final footage before adopting it; reduced precision can change detections and silhouettes.

The JSON conversion report includes actual PyTorch/device/precision information, pinned model revisions, the tracking backend, model setup, audio analysis, frame processing and mux timings, processing fps, and peak CUDA allocated/reserved memory. Model inference time is synchronized and is a subset of processing time; do not add it again to the total. Peak VRAM describes this PyTorch allocator, not total GPU use by all programs. Every CLI invocation reloads models; a repeat invocation may benefit from the operating system's file cache.

## Controls

| Option | Purpose |
| --- | --- |
| `--thermal classic` | Original lightweight luminance effect; still the default |
| `--thermal semantic` | Subject masks and a low-resolution heat field |
| `--sensor-resolution 160` | More abstraction; default 256, range 64–640 on the longest edge |
| `--warm-objects "person,dog,bird"` | Categories to simulate as warm |
| `--hot-objects "fire"` | Explicit artistic hot-object overrides; empty by default |
| `--confidence 0.4` | Stricter detection; may miss small or obscured subjects |
| `--detect-interval 0.25` | More frequent detection at a higher computational cost; default 0.5 seconds |
| `--verbose` | Cyan leaders and varied, stable six-symbol labels per track; requires semantic mode |
| `--device cpu` / `--device cuda` | Select the inference device explicitly |
| `--precision fp32` / `--precision bf16` | Full precision by default; experimental bfloat16 requires supported CUDA |

Warm defaults are people, birds, cats, dogs, horses, sheep, cows, elephants, bears, zebras, and giraffes. This is a category list, not a universal detector of living things. Add a category when relevant; detection of arbitrary objects is not guaranteed. Cars and appliances are not automatically assumed hot. When nothing is detected, the environment remains cool and the converter reports that result explicitly.

## Tracking and annotations

Detection and SAM image segmentation run periodically at up to 640 pixels on the longest edge. Backward optical flow moves masks on intervening frames. Matched, aligned masks are lightly blended; missed detections fade and expire. Coarse image changes trigger immediate re-detection at cuts. Memory usage is bounded by the current frame, model memory, and active masks; no whole-video frame cache is built.

This uses SAM's image predictor with our optical-flow tracker, not SAM's video-memory predictor. Occlusion, crossings, abrupt camera motion, low contrast, and subtle cuts can still cause missed masks or ID changes. At most 16 detections are segmented per detection frame. `--detect-interval 0.1` can improve fast action at significant cost. Scene-cut detection can also reset on a large exposure change.

Person masks can include held objects, backpacks, and clothing, which then share the simulated body field. This first implementation does not estimate material-specific insulation or separate exposed skin from clothing. The bundled checkpoint describes a SAM video configuration; Transformers may print a model-type warning when loading its compatible SAM image component. The pinned image inference path was verified on the demo clip.

Verbose labels use six distinct decorative patterns built from the bundled broad, nine-segment geometry. Dim outlines preserve the complete shape, while selected segments receive shaded cyan highlights and the HUD's glow. A seeded shuffle assigns separate groups of patterns to consecutive track IDs, reducing repetition across nearby targets. Each track keeps its combination as it moves, independent of frame time or detection order; `--seed` changes the combinations. The symbols are fictional readouts, not a translation, literal numeric ID, or thermometer. Glyph rows sit beside each silhouette, with short connectors to its boundary. Labels follow track motion, reserve space for the main HUD, avoid subjects and other labels, and fade with lost tracks. Up to eight labels are shown; a label is omitted when there is no nearby clear space. Track IDs identify detections within a shot, not individual people; no face recognition is performed.

The JSON conversion report includes the selected mode, model revisions, device, detection-frame count, maximum concurrent subjects, and detected scene cuts. See [dependencies.md](dependencies.md) for licenses.
