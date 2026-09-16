# Additional gallery details

The README shows looks, palettes, effects, two animated lock-dot reticles and a contact sheet. This guide records their comparison recipes and preview details; media dimensions and durations are checked in [media.json](media.json).

## Custom preset


Start from a built-in preset, a saved preset, or individual options. Customize the settings, then save your own named style preset:

**Tropic Glow is the custom-preset example: Yautja + palette-matched HUD + heat glow + neon.** It demonstrates how to modify a built-in style and save that combination under your own name. Its thermal colors, detail mode, and levels come from Yautja.

| Setting | Yautja · built-in style preset | Tropic Glow · editable custom preset |
| --- | --- | --- |
| Thermal image | Thermal Spectrum colors, Cinematic detail, 12 soft levels, dark scenery | Same thermal recipe |
| HUD and callouts | Red HUD and cyan annotations | Palette-matched colors, with timecode |
| CRT lines | On | On |
| Heat glow | Off | 0.6 |
| Neon HUD | Off | On |

```bash
yautja --list-presets
yautja --stylepreset yautja --hud --hud-theme palette --neon --heat-glow 0.6 --timecode --verbose --save-preset "tropic-glow.json" --preset-name "Tropic Glow"
yautja "clip.mov" "glowing.mp4" --preset-file "tropic-glow.json"
```

Saving needs no source or models. `--save-preset` writes a complete snapshot of the resolved visual settings, including defaults, so the exported file can be reused without its starting preset. Share the JSON file with another person or agent, then override individual choices when using it, such as `--heat-glow 0.2`. Existing saves require `--overwrite`.

| Tropic Glow · Yautja with neon HUD and heat glow |
| --- |
| [![Tropic Glow: Yautja with palette-matched neon HUD and animated heat glow](https://raw.githubusercontent.com/petehottelet/yautja/main/assets/examples/preset-tropic-glow.gif?v=2.10.0)](https://github.com/petehottelet/yautja/blob/main/assets/examples/large/preset-tropic-glow.gif) |
| [Editable JSON preset](../skills/yautja/assets/presets/tropic-glow.json) · [Creation, schema, and sharing guide](../skills/yautja/references/presets.md) |

The editable JSON example uses `"base": "yautja"` to inherit the starting settings and lists its changes under `settings`, including `"neon": true`. Load it with `--preset-file "tropic-glow.json"`. Presets exported with `--save-preset` contain the full settings, so they can be reused without the starting preset. Add `--no-neon` when loading Tropic Glow to disable only its neon styling.


## Exact comparison recipes

The shared comparison base is `yautja "clip.mov" "comparison.mp4" --thermal cinematic --palette costa-rica --verbose --timecode --grain 0 --pixelation 0 --no-crt-lines`. Apply the option shown in each README caption; target comparisons also use a [catalog selection](../README.md#choose-a-figure-and-add-a-target). Complete-look previews identify their preset. The [gallery builder](../tools/build_gallery.py) records each variant’s resolved settings and source hash; [development instructions](DEVELOPMENT.md#development) explain regeneration.

Thermal detail comparisons use `yautja "clip.mov" "detail.mp4" --palette costa-rica --verbose --timecode --grain 0 --pixelation 0 --no-crt-lines`, with one of the pictured `--thermal` settings. This isolates the change in detail from changes in palette or texture.

All comparisons use the same local source footage, with ranges chosen for each effect. Embedded previews are 480×270; their GitHub links open the corresponding 960×540 file page. The large versions render HUD artwork and textures at that resolution. The hero is also 960×540. GIFs compare styling choices rather than model accuracy; the source footage stays local.

Focus, Relic and the four presets below the hero play four seconds at normal source speed and 24 fps. The two lock-dot reticles also play at normal source speed and 24 fps. Target acquisition, neon, reticle stroke/blur and transparency examples show seconds 0–3.25 with matching target selections, callouts and timecode. These selections follow the foreground explorer separately in the first two shots. The checked media manifest records each file's frame count and duration.

### LED waveform

The README's LED Rorschach preview uses this complete recipe. The waveform gain compensates for the quiet demonstration soundtrack. The gallery builder samples the original clip at 24 fps and creates 480 × 270 and 960 × 540 GIFs; both play four seconds of footage in four seconds.

```bash
yautja "clip.mov" "led-preview.mp4" --thermal cinematic --palette redline --verbose --timecode --grain 0 --pixelation 0 --no-crt-lines --wave-style rorschach --wave-width 0.14 --wave-height 1 --wave-gain 4 --wave-display led --wave-backlight 0 --hud-theme custom --hud-colors "waveform=#FF302B" --neon --neon-intensity 0 --neon-elements "waveform=1.2" --neon-spread 0.4 --neon-core-whiten 0 --duration 4 --fps 24
```
