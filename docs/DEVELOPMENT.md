# Development


```bash
python -m pip install -e ".[dev,tracking]"
python -m tools.prepare_release
python -m unittest discover -s tests -v
python -m tools.verify_install
```

Tests include JPEG/PNG conversion without FFmpeg, EXIF orientation, transparency, deterministic stills, output protection, and real FFmpeg conversions with audio timing, timecode, and aspect handling.

Semantic heat and tracking tests use deterministic masks and optional OpenCV, without downloading models. They check cool backgrounds, texture suppression, tracking and fading, scene cuts, and CLI validation. A real model render should also be checked when changing segmentation dependencies.

CI runs the full test suite and fresh installed-wheel/extracted-skill image and video conversions on Windows, macOS, and Linux, with Python 3.10/3.11 coverage. Offline install checks disable package-index access and pip caches after preparing a complete dependency wheelhouse. Builds compare repeated wheel/bundle bytes and rebuild the wheel from the sdist. Build before running tests that inspect the release bundle.

Release versions live in `pyproject.toml`. The release workflow prepares and validates every artifact before its gated PyPI publish step. [Publishing and maintainer setup](https://github.com/petehottelet/yautja/blob/main/docs/PUBLISHING.md), [limited Python API](https://github.com/petehottelet/yautja/blob/main/docs/API.md), and [future improvements](https://github.com/petehottelet/yautja/blob/main/docs/ROADMAP.md).

For repeatable local performance comparisons, run these sequentially with each environment's Python. Use the same input and settings; the runner creates a new output directory for every invocation, records a source hash and exact commands, and verifies decoded frames and audio timing. It requires cached models and never downloads them.

```bash
python -m tools.benchmark "clip.mov" --device cpu --runs 2
python -m tools.benchmark "clip.mov" --device cuda --runs 2
python -m tools.benchmark "clip.mov" --device cuda --precision bf16 --runs 2
python -m tools.compare_precision "clip.mov" --times 0 2 4 6 8
```

Every benchmark run starts a fresh process and reloads models. Operating-system file caches are uncontrolled, so a first run is not necessarily cold. `compare_precision.py` compares sampled mask agreement; it does not establish detection accuracy. These developer tools stay in the repository, outside the portable skill manifest.

<details>
<summary>Regenerate the labelled README GIF gallery</summary>

The generated demo source is kept locally in the ignored `00_project_files/` folder and is not included in a clone. With the semantic environment and cached models ready:

```bash
yautja "00_project_files/create_a_video_of_explorers_wa.mp4" "outputs/figures.json" --list-figures --fps 12 --max-size 640 --device cuda
# Inspect outputs/figures.html and use the IDs from your scan.
python -m tools.build_gallery "00_project_files/create_a_video_of_explorers_wa.mp4" --device cuda --figures outputs/figures.json --target S001-F003,S002-F002,S003-F002 --overwrite
python -m tools.build_gallery "00_project_files/create_a_video_of_explorers_wa.mp4" --device cuda --figures outputs/figures.json --target S001-F003,S002-F002 --start 0 --duration 3.25 --only target-lock target-abyss-steady target-custom --overwrite
python -m tools.build_gallery "00_project_files/create_a_video_of_explorers_wa.mp4" --device cuda --wave-gain 4 --only waveform-rorschach waveform-rorschach-split waveform-rorschach-hollow --overwrite
```

The first gallery command processes seconds 0.5–3.5 once, shares tracked masks and heat fields across matched variants, and exports all labelled examples into `assets/examples/`, with larger versions in `assets/examples/large/`. Add `--only colors-matched-green texture-crt-lines` to regenerate selected previews and their large versions. The second gallery command gives target acquisition and flashing a longer first shot (seconds 0–3.25); the third raises audio gain for the Rorschach comparisons. It applies texture at the final display size so GIF downsampling does not erase grain or scanlines. It verifies animation timing before replacing the GIFs. The source and temporary decoded frames are never included in the skill archive. The helper is for short SDR gallery clips; use the main converter for normal images and videos.

</details>

## Local skill bundles and updates

From a developer checkout, build the wheel first, then build or install the small skill:

```bash
python -m tools.prepare_release
python -m tools.build_skill_bundle --zip dist/yautja-skill.zip
python -m tools.build_skill_bundle --install both
```

Choose `--install claude`, `--install codex`, or `--install both`. Codex respects `CODEX_HOME`; Claude uses `~/.claude/skills/yautja`. Existing installs require `--replace`, which updates known skill files and removes obsolete bundled runtime files/wheels while keeping personal files and environments. New bundles contain instructions, references, the MIT license and one application wheel. Dependencies, FFmpeg, models and gallery media are separate. See the [complete offline wheelhouse procedure](https://github.com/petehottelet/yautja/blob/main/skills/yautja/references/runtime.md#offline-install).

Use the original skill installer to update instructions. Upgrade the runtime in its original environment: `pipx runpip yautja install --upgrade "yautja[semantic]"`, or that venv's `python -m pip install --upgrade "yautja[semantic]"` (retain the semantic extra when used). Verify the compatible version and rerun doctor before converting; restart the agent session after updating the skill. Conversion never updates either component automatically. See the [changelog](https://github.com/petehottelet/yautja/blob/main/CHANGELOG.md) and [release instructions](https://github.com/petehottelet/yautja/blob/main/docs/PUBLISHING.md).


## Documentation checks

Run `python -m tools.check_docs` and `python -m tools.verify_readme` after changing documentation or the parser. Add `--models` locally to exercise segmented examples using cached models. New options need a canonical entry, runnable example mapping and a CHANGELOG link. The skill manifest includes the canonical reference.

README prose should describe current behavior. `check_docs` reports advisory warnings for likely revision narration, with line numbers; warnings do not fail CI. Judge them in context: still images, existing output files, and original artwork are valid descriptions. Commands, URLs, inline literals, and machine markers are excluded. Option/schema, link, and media errors fail the check. Update CLI help and the hand-maintained option reference together; the checker does not generate prose.

After reorganizing the README, preserve command blocks, machine markers, licensing, existing anchors and preview destinations. GIF clicks should open the large file's GitHub page. Review rendered headings and tables as well as automated results. Record setup and model examples skipped by verification rather than calling a partial run complete.
