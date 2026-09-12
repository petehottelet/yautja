# Runtime and conversion details

## Setup

Requires Python 3.10+, FFmpeg/ffprobe 6+ with libx264 and AAC, and the packages in `requirements.txt`. Python 3.11 is the tested baseline. Create the environment inside the installed skill or repository:

```bash
python -m venv .venv
# macOS/Linux
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/yautja.py --doctor
# Windows
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts/yautja.py --doctor
```

FFmpeg must be installed separately. Use the user's package manager when available: `sudo apt install ffmpeg` on Debian/Ubuntu or `winget install Gyan.FFmpeg` on Windows. On macOS, use [Homebrew's full build](https://formulae.brew.sh/formula/ffmpeg-full) for the `zscale` filter needed by HDR inputs:

```bash
brew install ffmpeg-full
export PATH="$(brew --prefix ffmpeg-full)/bin:$PATH"
```

The full Homebrew build is keg-only, so keep that PATH entry in the shell profile for future sessions. Respect the environment's installation permissions. Restart the shell after PATH changes if necessary. Upstream downloads: https://ffmpeg.org/download.html.

Run commands with the environment's Python executable; activation is optional. If a Claude execution environment lacks FFmpeg or cannot install dependencies, explain that limitation and provide the command for a local environment. Do not claim conversion succeeded.

## Formats and timing

Inputs can be any local video FFmpeg can decode: common MP4, MOV, MKV, WebM, AVI, and others. DRM-protected content, damaged files, missing decoders, and audio-only files are outside the converter's capabilities. URLs are not fetched automatically. The first non-cover-art video stream is used.

Output is H.264/AAC MP4 with fast-start metadata and square pixels. Original aspect ratio, display rotation, and selected audio are retained; audio is re-encoded to AAC, not copied bit-for-bit. Subtitles, extra audio tracks, attachments, chapters, and metadata are not carried into the result. Odd dimensions are rounded to even values for H.264 compatibility. Very small videos can be converted, but the HUD may not be readable.

PQ/HLG inputs use FFmpeg's zscale and Hable tone mapping before the thermal palette. FFmpeg must include those filters for HDR input. The output is an SDR artistic rendering. Unusual transfer functions and inaccurate source metadata may need normalization before conversion.

Audio analysis decodes the selected track to 8 kHz floating-point samples in temporary storage, retaining channels separately. A trailing 0.6-second window is binned into real minimum/maximum excursions. Opposite-phase channels are not averaged away. Whole-track peak calibration bounds gain; `--wave-gain` adjusts it. A peak below 0.00001 counts as full-track silence. Pauses in otherwise audible material remain flat. Audio analysis is disk-backed, not a whole-video RAM buffer; allow roughly 115 MB per hour per channel for its scratch file, plus the encoded output. All scratch files are removed after success, failure, or cancellation.

By default, a fixed seed makes the procedural waveform reproducible. Grain is also deterministic for a given frame time and seed. The waveform's envelope and frequency come from audio in audio mode, not image brightness. The alien readout continues to respond to image statistics.

Audio timestamp gaps are padded before waveform analysis and soundtrack trimming, so a trim starting inside a gap retains its leading silence. Analysis still decodes the full selected track for peak calibration; short trims of long recordings therefore have setup costs proportional to the source duration.

For the optional subject-based heat simulation, model setup, GPU selection, and tracking limits, see [semantic.md](semantic.md). Classic mode does not import the machine-learning runtime or require model downloads.

## Verification

```bash
ffprobe -v error -show_entries stream=codec_type,width,height,avg_frame_rate,duration -of json "output-yautja.mp4"
ffmpeg -v error -ss 1 -i "output-yautja.mp4" -frames:v 1 "preview.png"
```

Compare video duration within one output-frame interval (plus container/audio packet rounding). Check for sound unless `--mute` or the source has none. Confirm timecode follows the user's choice, glyphs are inside the frame, and the waveform reaches the left glyph row. Input paths with spaces must be quoted; do not interpolate filenames into shell command strings in custom integrations.

For codec failures, read FFmpeg's reported error. For HDR filter failures, install a build with zscale/tonemap or normalize to SDR first. For memory or speed constraints, lower `--max-size` or render the requested trim; do not silently substitute a preview for the full output.
