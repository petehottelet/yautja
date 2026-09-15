# Dependency and model licensing

Yautja uses the root MIT license. Dependencies and model weights keep their upstream terms. The release skill includes one Yautja wheel. Dependency wheels, model weights and FFmpeg binaries are installed separately. Base, tracking, semantic and development dependencies are declared in the repository's `pyproject.toml`; the semantic model revisions remain fixed in the installed `yautja.runtime` module.

## Semantic dependencies

The following upstream licenses were checked on 2026-09-11. Model revisions are pinned in `yautja.runtime` (also exported by `yautja.semantic`), and loading uses safetensors without remote Python code.

| Component | License | Source |
| --- | --- | --- |
| Grounding DINO tiny weights/configuration | Apache-2.0 | [Publisher model card](https://huggingface.co/IDEA-Research/grounding-dino-tiny/blob/a2bb814dd30d776dcf7e30523b00659f4f141c71/README.md), [upstream code license](https://github.com/IDEA-Research/GroundingDINO/blob/main/LICENSE) |
| SAM 2.1 Hiera tiny weights/configuration | Apache-2.0 | [Publisher model card](https://huggingface.co/facebook/sam2.1-hiera-tiny/blob/de431c4043854a71d8101e17995dfe596bf101a5/README.md), [upstream licensing statement](https://github.com/facebookresearch/sam2#license) |
| ViTPose base simple weights/configuration (checked 2026-09-12) | Apache-2.0 | [Publisher model card at the pinned revision](https://huggingface.co/usyd-community/vitpose-base-simple/blob/a93ac0c67e0b7e2c55287d21d4c460c8f3c54d45/README.md) |
| SciPy (1.17.1 validated for the pose preview) | BSD-3-Clause | [Versioned license](https://github.com/scipy/scipy/blob/v1.17.1/LICENSE.txt) |
| Transformers 4.57.6 | Apache-2.0 | [Upstream license](https://github.com/huggingface/transformers/blob/v4.57.6/LICENSE) |
| PyTorch 2.6.0 / torchvision 0.21.0 (historical comparison) | BSD-3-Clause | [PyTorch versioned license](https://github.com/pytorch/pytorch/blob/v2.6.0/LICENSE), [torchvision versioned license](https://github.com/pytorch/vision/blob/v0.21.0/LICENSE) |
| OpenCV 4.10+ | Apache-2.0 | [Upstream license](https://github.com/opencv/opencv/blob/4.x/LICENSE) |

This separation permits an MIT project to use these independently licensed components while retaining their upstream terms. Redistribution of an Apache-licensed component requires its license, relevant attribution and NOTICE information, and notices for modified upstream files. See [Apache-2.0, section 4](https://www.apache.org/licenses/LICENSE-2.0). The dependency packages may also include components with their own notices; retain the licenses supplied with each distribution if bundling them. Do not label a bundle containing these dependencies as entirely MIT.


## Existing runtime

NumPy uses BSD-3-Clause, Pillow uses HPND, and fonttools uses MIT. Installed distributions carry their licenses and dependency notices. FFmpeg is a separately installed command-line executable. [FFmpeg's licensing page](https://ffmpeg.org/legal.html) explains that its applicable license depends on build configuration; the libx264-enabled build this converter needs includes GPL components. The project does not distribute that executable or claim it is MIT. Any future bundled installer needs to preserve and meet the licenses of the exact binaries it ships.

Input footage and output media are not licensed by the project's software license. This dependency review records the chosen software/model distribution strategy, not a clearance of arbitrary input media.

## Bundled readable fonts

Michroma Regular is bundled unmodified under SIL Open Font License 1.1, with its copyright and full license in `yautja/assets/fonts/Michroma-OFL.txt`. It remains OFL rather than MIT. The font source is pinned to [Google Fonts revision 8b0a1d0](https://github.com/google/fonts/tree/8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5/ofl/michroma). It adds no runtime download.

Orbitron Light, Medium and Bold are bundled as unmodified static TTFs under SIL OFL 1.1. The copyright, Reserved Font Name notice and license are in `yautja/assets/fonts/Orbitron-OFL.txt`. Source files are pinned to [The League of Moveable Type revision 13e6a52](https://github.com/theleagueof/orbitron/tree/13e6a5222aa6818d81c9acd27edd701a2d744152); only filenames replace spaces with hyphens. No font conversion or internal renaming is performed.
