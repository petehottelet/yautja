# Runtime and conversion details

## Setup

Requires Python 3.10+ and the packages in `requirements.txt`. Video conversion also requires FFmpeg/ffprobe 6+ with libx264 and AAC; still images do not. Python 3.11 is the tested baseline. Create the environment inside the installed skill or repository:

```bash
python -m venv .venv
# macOS/Linux
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/yautja.py --doctor
# Windows
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts/yautja.py --doctor
```

For an image-only setup, add `--media image` to doctor to skip video tool checks. For semantic coloring, also add `--thermal semantic` and install the requirements and cached models described in [semantic.md](semantic.md).

FFmpeg for video must be installed separately. Use the user's package manager when available: `sudo apt install ffmpeg` on Debian/Ubuntu or `winget install Gyan.FFmpeg` on Windows. On macOS, use [Homebrew's full build](https://formulae.brew.sh/formula/ffmpeg-full) for the `zscale` filter needed by HDR inputs:

```bash
brew install ffmpeg-full
export PATH="$(brew --prefix ffmpeg-full)/bin:$PATH"
```

The full Homebrew build is keg-only, so keep that PATH entry in the shell profile for future sessions. Respect the environment's installation permissions. Restart the shell after PATH changes if necessary. Upstream downloads: https://ffmpeg.org/download.html.

Run commands with the environment's Python executable; activation is optional. If a Claude execution environment lacks FFmpeg or cannot install dependencies, explain that limitation and provide the command for a local environment. Do not claim conversion succeeded.

## Formats and timing

Still-image input supports single-frame JPEG and PNG, decoded locally with Pillow. JPEG/PNG input suffixes or a PNG output select image mode; `--media image` can also select it explicitly. The output must be PNG. EXIF rotation/mirroring is applied before resizing, aspect ratio and odd dimensions are retained, and `--max-size` limits the longest edge without upscaling. Transparency is flattened over black before coloring, and source metadata is omitted from the RGB PNG. Animated PNG and other still formats are rejected.

Images use the same Silhouette, Cinematic, Detailed, or legacy Classic renderer at time zero. Segmentation modes run detection, segmentation, and human pose estimation once, without temporal tracking. The waveform is a static procedural pattern, with no audio. Optional `--timecode` shows `--timecode-start` (default zero). Nondefault video controls for trim, duration, frame rate, encoding, audio, or detection interval produce an error. Use the shared thermal, palette, grain, pixelation, scanlines, sensor texture, annotation, glow, size, and seed controls for stills.

Inputs can be any local video FFmpeg can decode: common MP4, MOV, MKV, WebM, AVI, and others. DRM-protected content, damaged files, missing decoders, and audio-only files are outside the converter's capabilities. URLs are not fetched automatically. The first non-cover-art video stream is used.

Output is H.264/AAC MP4 with fast-start metadata and square pixels. Original aspect ratio, display rotation, and selected audio are retained; audio is re-encoded to AAC, not copied bit-for-bit. Subtitles, extra audio tracks, attachments, chapters, and metadata are not carried into the result. Odd dimensions are rounded to even values for H.264 compatibility. Very small videos can be converted, but the HUD may not be readable.

PQ/HLG inputs use FFmpeg's zscale and Hable tone mapping before the thermal palette. FFmpeg must include those filters for HDR input. The output is an SDR artistic rendering. Unusual transfer functions and inaccurate source metadata may need normalization before conversion.

Audio analysis decodes the selected track to 8 kHz floating-point samples in temporary storage, retaining channels separately. A trailing 0.6-second window is binned into real minimum/maximum excursions. Opposite-phase channels are not averaged away. Whole-track peak calibration bounds gain; `--wave-gain` adjusts it. A peak below 0.00001 counts as full-track silence. Pauses in otherwise audible material remain flat. Audio analysis is disk-backed, not a whole-video RAM buffer; allow roughly 115 MB per hour per channel for its scratch file, plus the encoded output. All scratch files are removed after success, failure, or cancellation.

By default, a fixed seed makes the procedural waveform reproducible. Grain is also deterministic for a given frame time and seed. The waveform's envelope and frequency come from audio in audio mode, not image brightness. The alien readout continues to respond to image statistics.

Grain, chunky pixels, and scanlines are independently optional and off by default. Use `--grain 0.02`, `--pixelation 80`, or `--scanlines` on their own or together. Bare `--grain` means 0.035; bare `--pixelation` means a longest grid edge of 96. `--grain 0`, `--pixelation 0`, and `--no-scanlines` disable individual components. `--sensor-texture` is a combined preset with grain 0.035, a grid at `--sensor-resolution`, scanlines, and light intensity quantization; explicit controls override its defaults. Disabling the preset does not cancel explicit individual effects. Display treatments do not change the underlying detections or HUD readouts. The original Yautja palette is the default in every mode; `auto` also means Yautja. Redline, red-only Virtual Boy, Ironbow, Green Phosphor, Amber Phosphor, White Hot, and Black Hot are optional palettes.

Audio timestamp gaps are padded before waveform analysis and soundtrack trimming, so a trim starting inside a gap retains its leading silence. Analysis still decodes the full selected track for peak calibration; short trims of long recordings therefore have setup costs proportional to the source duration.

For the optional subject-based heat simulation, model setup, GPU selection, and tracking limits, see [semantic.md](semantic.md). Classic mode does not import the machine-learning runtime or require model downloads.

## CRT and VHS display effects

`--crt-lines` (alias `--scanlines`) adds horizontal dark rows across the final picture, including the HUD; `--no-crt-lines` disables them. `--vhs` adds seeded color bleed, reduced color detail, slight horizontal wobble, tape noise, dropouts, and tracking defects. These animate with video time; still images get a fixed frame. VHS can be combined with CRT lines or other effects, and `--no-vhs` disables it independently. The sensor-texture preset enables CRT lines but does not enable VHS. These are visual treatments only: they do not alter the soundtrack, tracking results, or timecode values. Virtual Boy keeps even the HUD and analog defects red-only.

## Verification

For a still image, check `media_type: image`, `output_format: PNG`, dimensions, and the single-frame JSON report. Open the PNG to check orientation, subject colors, and HUD placement; no audio or duration check is needed. Both image and video conversions protect the input, require `--overwrite` for existing output, and commit a temporary result only after successful encoding.

```bash
ffprobe -v error -show_entries stream=codec_type,width,height,avg_frame_rate,duration -of json "output-yautja.mp4"
ffmpeg -v error -ss 1 -i "output-yautja.mp4" -frames:v 1 "preview.png"
```

Compare video duration within one output-frame interval (plus container/audio packet rounding). Check for sound unless `--mute` or the source has none. Confirm timecode follows the user's choice, glyphs are inside the frame, and the waveform reaches the left glyph row. Input paths with spaces must be quoted; do not interpolate filenames into shell command strings in custom integrations.

For codec failures, read FFmpeg's reported error. For HDR filter failures, install a build with zscale/tonemap or normalize to SDR first. For memory or speed constraints, lower `--max-size` or render the requested trim; do not silently substitute a preview for the full output.
