# Segmentation and thermal-style re-skinning

All four segmented thermal looks detect subjects with Grounding DINO tiny, segment their silhouettes with SAM 2.1 tiny, and estimate 17 human body landmarks with ViTPose base simple. Low Detail (`--thermal low-detail`, also `silhouette` or `semantic`) strongly reduces anatomical variation to broad, soft heat blobs. It uses soft edges; it does not copy facial or clothing texture. Uncertain landmarks and nonhuman subjects use a mask-based fallback. Vegetation and scenery stay cool, even when bright. This is an entertainment effect; the models do not measure temperature, clothing insulation, engine state, or whether an object is alive.

Detailed (`--thermal detailed`, alias `realistic`) adds a second detection/segmentation pass inside each person crop, using the same cached Grounding DINO and SAM models. It assigns separate synthetic warmth to detected faces, hands, hair, garments, shoes, and carried equipment. Exposed skin appears brighter, garments vary more gently, and equipment can appear cooler. Only garment regions use normalized, coarse source shading to suggest folds; photographic facial detail is not copied. It keeps more scenery structure and reduces glowing silhouette borders. These are visual priors, not recovered infrared data or measured material properties.

Cinematic (`--thermal cinematic`) is the middle ground: it softens the same surface regions into broad patches, blends them with anatomy-guided warmth, and uses moderate scenery detail and edge softness. Small equipment/skin boundaries are less pronounced than Detailed. It does not copy source garment or facial texture. All styles use the Yautja palette by default; `--palette auto` also selects Yautja.

Very Detailed (`--thermal very-detailed`) uses Detailed's surface segmentation and adds fine and medium-scale source contrast at output resolution. Visible eyes, nose, lips, hair, and fabric folds remain recognizable when the source resolves them. Face and hand regions receive stronger feature contrast, while the scene remains cool. It uses the same cached models; no face-generation or recognition model is added. Distant, blurred, occluded, or absent features cannot be recovered. This is a stylized rendering of visible-light structure, not infrared measurement.

## Setup and use

The base `yautja` package provides the default luminance filter (`--thermal luminance`). To use the segmented gallery looks, install `yautja[semantic]` in the selected virtual environment; it can also be installed directly as your first Yautja installation. Keep installation, model setup, diagnosis, and conversion in the same environment:

```bash
python -m pip install "yautja[semantic]"
python -m yautja --download-models
python -m yautja --doctor --media image --thermal cinematic
python -m yautja "photo.jpg" "outputs/photo-cinematic.png" --thermal cinematic --verbose
# Videos also require FFmpeg and ffprobe:
python -m yautja --doctor --thermal cinematic
python -m yautja "clip.mov" "outputs/clip-cinematic.mp4" --thermal cinematic --verbose --timecode
```

Use your environment's Python executable for these commands. Palettes work with the base filter. Palette starter presets select Cinematic; complete scene/HUD presets use segmented overlays. Thermal-only presets can use `--thermal luminance` as an override. The explicit download command fetches about 1.2 GB of pinned model weights and configuration from Hugging Face into its standard cache. ViTPose accounts for about 344 MB; the semantic extra includes its SciPy dependency. Subsequent conversions require cached files and do not download models or upload frames. No account is normally required. The release skill includes the Yautja wheel, but not model weights, dependency wheels, Python or FFmpeg. Follow the [complete offline setup](runtime.md#offline-install) for a disconnected machine. For a fully offline machine, transfer the complete Hugging Face cache and preserve its upstream notices.

`--device auto` selects CUDA if available, otherwise CPU. A CUDA-capable card also needs CUDA-enabled PyTorch; CPU-only PyTorch will use CPU even if a GPU is installed. Install a compatible PyTorch/torchvision pair using the [official PyTorch installer](https://pytorch.org/get-started/locally/). Start with a five-second sample. CPU processing is substantially slower than luminance mode.

### Diagnose before conversion

```bash
python -m yautja --doctor
python -m yautja --doctor --thermal semantic --device cuda
```

Doctor reports the executable, environment, package versions and import failures, CUDA build, selected device and reason, GPU name/VRAM, and required files from all three pinned model snapshots. A selected CUDA device must complete a small tensor operation. It never downloads weights or performs model inference; `ready` means the prerequisites passed, not that weight integrity or a real model render has been verified. Missing or broken optional ML packages remain nonfatal for the default luminance check. A semantic check exits with status 1 if prerequisites fail.

Conversions print the actual device and selection reason. An explicit CUDA request never retries inference on CPU. Memory or driver failures preserve the protected output and remove conversion scratch files. `--verbose` controls glyph annotations.

### Isolated CUDA environment on Windows

The historical comparison uses Python 3.11 with PyTorch 2.6.0/torchvision 0.21.0 CUDA 12.4, matching the historical CPU versions. This is a reproducible comparison pair, not a claim that it is the newest release. The pair and wheel index are listed in the [official versioned installation instructions](https://pytorch.org/get-started/previous-versions/#v260). Preserve your working environment:

```powershell
python -m venv .venv-gpu
.venv-gpu\Scripts\python.exe -m pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cu124
.venv-gpu\Scripts\python.exe -m pip install "yautja[semantic]"
.venv-gpu\Scripts\python.exe -m yautja --doctor --thermal semantic --device cuda
.venv-gpu\Scripts\python.exe -m yautja "clip.mov" "outputs/clip-cuda.mp4" --thermal semantic --device cuda --verbose --timecode
```

Do not add `--system-site-packages`. CUDA-specific wheels stay separate from base dependencies. The regular Hugging Face model cache can be shared with the CPU environment; if doctor finds missing files, run `--download-models` explicitly with the new environment's Python. The converter neither downloads a driver nor changes your existing environment.

Full precision (`--precision fp32`) remains the default. `--precision bf16` enables experimental CUDA bfloat16 autocast on compatible hardware and fails clearly on CPU or unsupported GPUs. Compare masks and final footage before adopting it; reduced precision can change detections and silhouettes.

The JSON conversion report includes actual PyTorch/device/precision information, pinned model revisions, the tracking backend, model setup, audio analysis, frame processing and mux timings, processing fps, and peak CUDA allocated/reserved memory. Model inference time is synchronized and is a subset of processing time; do not add it again to the total. Peak VRAM describes this PyTorch allocator, not total GPU use by all programs. Every CLI invocation reloads models; a repeat invocation may benefit from the operating system's file cache.

## Controls

[All option ranges, defaults and examples](options.md); [HUD element roles](hud-elements.md).

Warm defaults are people, birds, cats, dogs, horses, sheep, cows, elephants, bears, zebras, and giraffes. This is a category list, not a universal detector of living things. Add a category when relevant; detection of arbitrary objects is not guaranteed. Cars and appliances are not automatically assumed hot. When nothing is detected, the environment remains cool and the converter reports that result explicitly.

## Tracking and annotations

Detection and SAM image segmentation run periodically at up to 640 pixels on the longest edge. Backward optical flow moves masks on intervening frames. Matched, aligned masks are lightly blended; missed detections fade and expire. Coarse image changes trigger immediate re-detection at cuts. Memory usage is bounded by the current frame, model memory, and active masks; no whole-video frame cache is built.

ViTPose runs on the detected person regions at the same detection cadence. Landmarks move with optical flow between updates, and reliable matched estimates are lightly smoothed. Pose head landmarks collapse into one broad region. Very Detailed separately retains visible facial contrast from the input; it does not synthesize facial features from the pose. Wrist locations approximate hand regions. Colors are clipped to each visible silhouette and fade with the track. Low-confidence joints are omitted, and anatomical region strengths ramp up with confidence. Seeded variation stays attached to the estimated torso and limb axes instead of changing randomly each frame. Pose errors, cropped bodies, and ID changes can still move or reset the pattern; this is not a persistent heat simulation or a material classifier.

This uses SAM's image predictor with our optical-flow tracker, not SAM's video-memory predictor. Occlusion, crossings, abrupt camera motion, low contrast, and subtle cuts can still cause missed masks or ID changes. At most 16 detections are segmented per detection frame. `--detect-interval 0.1` can improve fast action at significant cost. Scene-cut detection can also reset on a large exposure change.

In Low Detail, held objects, backpacks, and clothing inside person masks share the body field. Cinematic, Detailed, and Very Detailed instead propose up to 12 surface regions per person at each detection refresh, reject low-confidence or implausibly large masks and masks mostly outside the owner, and clip accepted regions to that person. Equipment and eyewear can override warm skin; larger silhouettes are a foreground approximation when people overlap. Surface masks follow optical flow and matched updates are smoothed. Regions absent from a fresh detection revert to the anatomy fallback. Small hands, eyewear, distant subjects, ambiguous garments, and crossings can still be missed or misclassified, and colors can change at detection refreshes. There is no depth reconstruction, insulation estimate, or persistent heat simulation. Extra inference makes these three modes slower as the number of people increases; they do not need another model download beyond the three-model setup.

All display effects are independent of segmentation and palette, and default off. `--grain` adds seeded fixed-pattern and time-varying noise without adding a pixel grid or scanlines. `--pixelation` downsamples the heat field and enlarges it with nearest-neighbor sampling; smaller grids make chunkier blocks without changing subject masks or heat-field resolution. `--scanlines` adds a subtle alternating-row treatment. The combined `--sensor-texture` preset supplies grain 0.035, pixels at `--sensor-resolution`, scanlines, and light intensity quantization. Explicit grain, pixelation, or scanline options override those preset components. Turning the preset off leaves explicit individual effects intact; disable all of them for a completely clean result. These controls never change detection, tracking, audio, glyph selection, or timecode, and work for both stills and videos. Reports include resolved `grain`, `pixelation`, `scanlines`/`crt_lines`, and `vhs` values as well as requested settings. CRT lines affect the finished picture and HUD. Optional `--vhs` adds time-varying analog color bleed, wobble, noise, dropouts, and tracking defects to that same final display without altering segmentation or audio. It remains independent of the sensor-texture preset.

The bundled checkpoint describes a SAM video configuration; Transformers may print a model-type warning when loading its compatible SAM image component. The pinned image inference path was verified on the demo clip.

Verbose labels use six distinct decorative patterns built from the bundled broad, nine-segment geometry. Dim outlines preserve the complete shape, while selected segments receive shaded cyan highlights and the HUD's glow. A seeded shuffle assigns separate groups of patterns to consecutive track IDs, reducing repetition across nearby targets. Each track keeps its combination as it moves, independent of frame time or detection order; `--seed` changes the combinations. The symbols are fictional readouts, not a translation, literal numeric ID, or thermometer. Glyph rows sit beside each silhouette, with connectors aimed at its smoothed center of area (an image-based approximation of center of mass). If that center falls outside a concave or partly occluded mask, the marker uses the nearest visible point. Labels retain their relative positions while clear, reserve space for the main HUD, avoid subjects and other labels, and fade with lost tracks. Time-based smoothing damps small mask changes with bounded lag during fast motion; cuts, reversed or repeated time, long frame gaps, and lost tracks reset its history. This stabilization is automatic. Up to eight labels are shown; a label is omitted when there is no nearby clear space. Track IDs identify detections within a shot, not individual people; no face recognition is performed.

The JSON conversion report includes the selected mode, model revisions, device, detection-frame count, maximum concurrent subjects, and detected scene cuts. See [dependencies.md](dependencies.md) for licenses.

## Mask stability

Overlay silhouettes use flow-aligned hysteresis, closing and small-island filtering. The probability field remains separate for thermal coloring. `--mask-stability 0 --mask-min-region 0` disables stabilization. These are semantic runtime settings, alongside detection interval, and are never saved with a visual preset. [Defaults, ranges and examples](options.md#mask-stability).
