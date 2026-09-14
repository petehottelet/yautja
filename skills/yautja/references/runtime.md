# Runtime and conversion details

## Install one runtime

Requires Python 3.10+; Python 3.10 and 3.11 are covered by CI. Classic needs only the base package. Low Detail, Cinematic, Detailed, and Very Detailed also need the `semantic` extra and explicit model setup in [semantic.md](semantic.md). The `tracking` extra supplies OpenCV for tracker development but does not install the models.

Use the [PyPI package](https://pypi.org/project/yautja/) with the compatible commands below, or the matching wheel from a [GitHub release](https://github.com/petehottelet/yautja/releases). For development, install the GitHub source with `python -m pip install "yautja @ git+https://github.com/petehottelet/yautja.git@main"`. Add `[semantic]` after `yautja` for segmentation. The source route requires Git and can include changes beyond the latest release.

Choose the first usable route:

1. **pipx:** `pipx install "yautja>=2.5.3,<3"`, or `pipx install "yautja[semantic]>=2.5.3,<3"` for segmentation. Run `yautja --version` and `yautja --doctor`. Locate its Python with `pipx environment --value PIPX_LOCAL_VENVS`: under that directory use `yautja/bin/python` on Unix or `yautja/Scripts/python.exe` on Windows. Use this exact interpreter for any later extras or GPU setup; a different Python installs into a different environment. A dedicated venv is easier for a custom CUDA stack.
2. **Dedicated venv outside the skill:** create and use the environment below. All `python` examples thereafter mean its exact executable, or the activated environment.
3. **User site:** `python -m pip install --user "yautja>=2.5.3,<3"` only when supported. Invoke `python -m yautja` using that same Python if the console script is not on PATH. If Python is externally managed (PEP 668), use route 2. Never use `--break-system-packages`.

```bash
python -m venv .venv-yautja
# macOS/Linux
.venv-yautja/bin/python -m pip install "yautja>=2.5.3,<3"
.venv-yautja/bin/python -m yautja --version
.venv-yautja/bin/python -m yautja --doctor
```

```powershell
# Windows, after creating the venv
.venv-yautja\Scripts\python.exe -m pip install "yautja>=2.5.3,<3"
.venv-yautja\Scripts\python.exe -m yautja --version
.venv-yautja\Scripts\python.exe -m yautja --doctor
```

Confirm a stable version in `>=2.5.3,<3` before using this skill. `--doctor` reports the package version/location, exact Python, virtual-environment status, script directory, PATH membership, a conflicting CLI if found, and a `module_command` array for this interpreter. It reports observed environment facts; it does not infer pipx ownership from a path name. For image-only setup use `--doctor --media image` to skip video tool checks.

## Offline install

The release skill zip contains one application wheel in `yautja/wheels/`. It does **not** contain dependency wheels, model weights, Python, or FFmpeg. On a connected computer with the same OS, architecture, Python version and ABI as the destination, extract the bundle and run these commands from its `yautja/` directory. The environment must have no preinstalled Yautja; pinning to the supplied wheel keeps the application bytes exact:

```bash
python -c "from pathlib import Path; import subprocess,sys; w, = Path('wheels').glob('*.whl'); subprocess.run([sys.executable,'-m','pip','download','--only-binary=:all:','--dest','wheelhouse',str(w)],check=True)"
```

For segmentation, change `str(w)` to `str(w) + '[semantic]'` in the preparation command. For cross-platform preparation, specify pip's `--platform`, `--python-version`, `--implementation`, and `--abi` together; preparing on a matching target is easier. Keep the upstream licenses packaged with each wheel.

Transfer the extracted bundle and complete wheelhouse. In a fresh target venv, from `yautja/`, run:

<!-- offline-install: tested from the extracted skill by tools.verify_install -->
```bash
python -m pip install --no-index --no-cache-dir --find-links wheelhouse --find-links wheels "yautja>=2.5.3,<3"
yautja --version
yautja --doctor --media image
```

Use `"yautja[semantic]>=2.5.3,<3"` in that install for a semantic wheelhouse. If a dependency is missing, stop and complete the wheelhouse on the connected computer; do not drop `--no-index`. Model use is independently offline: transfer the complete cache of the three pinned snapshots after an explicit connected `yautja --download-models`, then set `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` and run `yautja --doctor --thermal cinematic`. These variables do not disable pip networking. For videos separately install FFmpeg/ffprobe and their system libraries before going offline.

## Updates

Use the original environment. For pipx use `pipx runpip yautja install --upgrade "yautja>=2.5.3,<3"` to keep the major-version bound (retain `[semantic]` when used), then verify the compatible major and diagnose again. For a venv/user install use its Python with `python -m pip install --upgrade "yautja>=2.5.3,<3"` (retain `[semantic]` when used). For a GitHub source installation, upgrade from the same source URL to follow development; check the resulting version before conversion. Update skill instructions separately with the original skill installer and restart the agent session. The 2.x CLI preserves existing flags; newly documented flags require raising the skill's minimum minor version or checking availability. No conversion automatically updates packages or the skill.

## Video tools

FFmpeg for video must be installed separately. Use the user's package manager when available: `sudo apt install ffmpeg` on Debian/Ubuntu or `winget install Gyan.FFmpeg` on Windows. On macOS, use [Homebrew's full build](https://formulae.brew.sh/formula/ffmpeg-full) for the `zscale` filter needed by HDR inputs:

```bash
brew install ffmpeg-full
export PATH="$(brew --prefix ffmpeg-full)/bin:$PATH"
```

The full Homebrew build is keg-only, so keep that PATH entry in the shell profile for future sessions. Respect the environment's installation permissions. Restart the shell after PATH changes if necessary. Upstream downloads: https://ffmpeg.org/download.html.

Run commands with the environment's Python executable; activation is optional. If a Claude execution environment lacks FFmpeg or cannot install dependencies, explain that limitation and provide the command for a local environment. Do not claim conversion succeeded.

## Formats and timing

Still-image input supports single-frame JPEG and PNG, decoded locally with Pillow. JPEG/PNG input suffixes or a PNG output select image mode; `--media image` can also select it explicitly. The output must be PNG. EXIF rotation/mirroring is applied before resizing, aspect ratio and odd dimensions are retained, and `--max-size` limits the longest edge without upscaling. Transparency is flattened over black before coloring, and source metadata is omitted from the RGB PNG. Animated PNG and other still formats are rejected.

Images use the same Low Detail, Cinematic, Detailed, Very Detailed, or legacy Classic renderer at time zero. Segmentation modes run detection, segmentation, and human pose estimation once, without temporal tracking. The waveform is a static procedural pattern, with no audio. Optional `--timecode` shows `--timecode-start` (default zero). Nondefault video controls for trim, duration, frame rate, encoding, audio, or detection interval produce an error. Use the shared thermal, palette, grain, pixelation, scanlines, sensor texture, annotation, glow, size, and seed controls for stills.

Inputs can be any local video FFmpeg can decode: common MP4, MOV, MKV, WebM, AVI, and others. DRM-protected content, damaged files, missing decoders, and audio-only files are outside the converter's capabilities. URLs are not fetched automatically. The first non-cover-art video stream is used.

Output is H.264/AAC MP4 with fast-start metadata and square pixels. Original aspect ratio, display rotation, and selected audio are retained; audio is re-encoded to AAC, not copied bit-for-bit. Subtitles, extra audio tracks, attachments, chapters, and metadata are not carried into the result. Odd dimensions are rounded to even values for H.264 compatibility. Very small videos can be converted, but the HUD may not be readable.

PQ/HLG inputs use FFmpeg's zscale and Hable tone mapping before the thermal palette. FFmpeg must include those filters for HDR input. The output is an SDR artistic rendering. Unusual transfer functions and inaccurate source metadata may need normalization before conversion.

Audio analysis decodes the selected track to 8 kHz floating-point samples in temporary storage, retaining channels separately. A trailing 0.6-second window is binned into real minimum/maximum excursions. Opposite-phase channels are not averaged away. Whole-track peak calibration bounds gain; `--wave-gain` adjusts it. A peak below 0.00001 counts as full-track silence. Pauses in otherwise audible material remain flat. Audio analysis is disk-backed, not a whole-video RAM buffer; allow roughly 115 MB per hour per channel for its scratch file, plus the encoded output. All scratch files are removed after success, failure, or cancellation.

By default, a fixed seed makes the procedural waveform reproducible. Grain is also deterministic for a given frame time and seed. The waveform's envelope and frequency come from audio in audio mode, not image brightness. The alien readout continues to respond to image statistics.

Grain, chunky pixels, and scanlines are independently optional and off by default. Use `--grain 0.02`, `--pixelation 80`, or `--scanlines` on their own or together. Bare `--grain` means 0.035; bare `--pixelation` means a longest grid edge of 96. `--grain 0`, `--pixelation 0`, and `--no-scanlines` disable individual components. `--sensor-texture` is a combined preset with grain 0.035, a grid at `--sensor-resolution`, scanlines, and light intensity quantization; explicit controls override its defaults. Disabling the preset does not cancel explicit individual effects. Display treatments do not change the underlying detections or HUD readouts. The original Yautja palette is the default in every mode; `auto` also means Yautja. Redline, red-only Virtual Boy, Ironbow, Green Phosphor, Amber Phosphor, White Hot, and Black Hot are optional palettes.

Audio timestamp gaps are padded before waveform analysis and soundtrack trimming, so a trim starting inside a gap retains its leading silence. Analysis still decodes the full selected track for peak calibration; short trims of long recordings therefore have setup costs proportional to the source duration.

For the optional subject-based heat simulation, model setup, GPU selection, and tracking limits, see [semantic.md](semantic.md). Classic mode does not import the machine-learning runtime or require model downloads.

## CRT and VHS display effects

`--crt-lines` (alias `--scanlines`) adds horizontal dark rows across the final picture, including the HUD; `--no-crt-lines` disables them. `--vhs` adds seeded color bleed, reduced color detail, slight horizontal wobble, tape noise, dropouts, and tracking defects. These animate with video time; still images get a fixed frame. VHS can be combined with CRT lines or other effects, and `--no-vhs` disables it independently. The sensor-texture preset enables CRT lines but does not enable VHS. These are visual treatments only: they do not alter the soundtrack, tracking results, or timecode values. Virtual Boy keeps the HUD and analog defects red-only with standard or palette-matched HUD colors; explicit custom/random HUD colors can override this. See [color controls](colors.md) for palette matching and per-element hex values.

## Verification

For a still image, check `media_type: image`, `output_format: PNG`, dimensions, and the single-frame JSON report. Open the PNG to check orientation, subject colors, and HUD placement; no audio or duration check is needed. Both image and video conversions protect the input, require `--overwrite` for existing output, and commit a temporary result only after successful encoding.

```bash
ffprobe -v error -show_entries stream=codec_type,width,height,avg_frame_rate,duration -of json "output-yautja.mp4"
ffmpeg -v error -ss 1 -i "output-yautja.mp4" -frames:v 1 "preview.png"
```

Compare video duration within one output-frame interval (plus container/audio packet rounding). Check for sound unless `--mute` or the source has none. Confirm timecode follows the user's choice, glyphs are inside the frame, and the waveform reaches the left glyph row. Input paths with spaces must be quoted; do not interpolate filenames into shell command strings in custom integrations.

For codec failures, read FFmpeg's reported error. For HDR filter failures, install a build with zscale/tonemap or normalize to SDR first. For memory or speed constraints, lower `--max-size` or render the requested trim; do not silently substitute a preview for the full output.
