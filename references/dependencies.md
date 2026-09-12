# Dependency and model licensing

Yautja uses the root MIT license. Dependencies and model weights keep their upstream terms. The portable skill includes the fixed runtime manifest, without dependency wheels, model weights, or FFmpeg binaries.

## New semantic dependencies

The following upstream licenses were checked on 2026-09-11. Model revisions are pinned in `scripts/runtime.py` (also exported by `scripts/semantic.py`), and loading uses safetensors without remote Python code.

| Component | License | Source |
| --- | --- | --- |
| Grounding DINO tiny weights/configuration | Apache-2.0 | [Publisher model card](https://huggingface.co/IDEA-Research/grounding-dino-tiny/blob/a2bb814dd30d776dcf7e30523b00659f4f141c71/README.md), [upstream code license](https://github.com/IDEA-Research/GroundingDINO/blob/main/LICENSE) |
| SAM 2.1 Hiera tiny weights/configuration | Apache-2.0 | [Publisher model card](https://huggingface.co/facebook/sam2.1-hiera-tiny/blob/de431c4043854a71d8101e17995dfe596bf101a5/README.md), [upstream licensing statement](https://github.com/facebookresearch/sam2#license) |
| Transformers 4.57.6 | Apache-2.0 | [Upstream license](https://github.com/huggingface/transformers/blob/v4.57.6/LICENSE) |
| PyTorch 2.6.0 / torchvision 0.21.0 (phase 1 comparison) | BSD-3-Clause | [PyTorch versioned license](https://github.com/pytorch/pytorch/blob/v2.6.0/LICENSE), [torchvision versioned license](https://github.com/pytorch/vision/blob/v0.21.0/LICENSE) |
| OpenCV 4.10+ | Apache-2.0 | [Upstream license](https://github.com/opencv/opencv/blob/4.x/LICENSE) |

This separation permits an MIT project to use these independently licensed components while retaining their upstream terms. Redistribution of an Apache-licensed component requires its license, relevant attribution and NOTICE information, and notices for modified upstream files. See [Apache-2.0, section 4](https://www.apache.org/licenses/LICENSE-2.0). The dependency packages may also include components with their own notices; retain the licenses supplied with each distribution if bundling them. Do not label a bundle containing these dependencies as entirely MIT.

SAM 3 was considered in the attached design discussion but is not used. Its [custom SAM license](https://github.com/facebookresearch/sam3/blob/main/LICENSE) is distinct from SAM 2's Apache-2.0 license.

## Existing runtime

NumPy uses BSD-3-Clause, Pillow uses HPND, and fonttools uses MIT. Installed distributions carry their licenses and dependency notices. FFmpeg is a separately installed command-line executable. [FFmpeg's licensing page](https://ffmpeg.org/legal.html) explains that its applicable license depends on build configuration; the libx264-enabled build this converter needs includes GPL components. The project does not distribute that executable or claim it is MIT. Any future bundled installer needs to preserve and meet the licenses of the exact binaries it ships.

Input footage and output media are not licensed by the project's software license. This dependency review records the chosen software/model distribution strategy, not a clearance of arbitrary input media.
