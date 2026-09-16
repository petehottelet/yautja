# Focus, Relic, Murphy and holographic geometry

All capabilities are shared options; presets only provide saved values. See the [canonical option reference](options.md) for ranges, defaults, aliases and enabling flags, and the [HUD role table](hud-elements.md) for ink/opacity/blur/neon.

## Complete styles

**Focus** preserves scene detail under a dark, restrained blue tint. Neon-purple HUD glyphs and targeting contrast with a blue grid and matching waveform. Its geodesic sphere slowly rotates, with broken lines fading toward the center, pulsing satellite dots and occasional seven-sided rings. Thin, partial blue holographic subject edges shimmer with pale highlights. One persistent hexagon glides between subjects, with a large circle at 90% of the inscribed radius, six small inner circles, four outer circles and a center square.

**Relic** inherits Focus's scene, purple HUD and blue grid. Neon hot-pink broken triangles emerge below the selected silhouette's center of mass, float upward, then contract, spin and fade. Soft hot-pink light filaments stream upward behind the body core, aligned to shoulder/hip joints with a solid-body mask fallback. Arms and held props do not widen the light column. All foreground silhouettes occlude the trails and their glow. [`--code-style`](options.md#code-style) selects `light` or `glyphs`; `--code-size`, `--code-density` and `--code-speed` control stream spacing/width, count and upward motion. Focus leaves this effect off. Both presets leave decorative weak-spot patches off; the optional capability remains available.

**Murphy** uses a slight blue source cast, glowing green center-crossing XY box, selected-subject outline and a large Michroma caption with a synthesized medium weight and blinking underscore. Automatic targeting needs no catalog. Its upper-right readout and waveform are hidden by preset opacity.

Focus and Relic use these independently configurable [HUD color roles](hud-elements.md):

| Elements | Ink |
| --- | --- |
| HUD, glyphs and reticle | Neon purple `#8833FF` |
| `geo-grid`, `waveform` | Blue `#507CFF` |
| `subject-outline` | Holographic blue `#6099FF` |
| Relic's `subject-code`, `target-motif` | Violet-leaning neon pink `#F745FF` |

```bash
yautja "clip.mov" "focus.mp4" --stylepreset focus
yautja "clip.mov" "relic.mp4" --stylepreset relic
yautja "clip.mov" "murphy.mp4" --stylepreset murphy
```

These need [segmented setup](semantic.md). [Runnable presets and customization](examples.md#focus).

## Subject edges and code

`--subject-outline` enables all-subject edges; `--outline-style` chooses solid, shimmer or holographic. Width controls thickness, coverage/arcs control partial edge regions, speed controls travel/texture, and shine controls moving-band brightness. Focus/Relic set width 4.8, speed 1.35, shine 0.65 and outline ink `#6099FF`. Stills freeze the clock.

The tracker keeps flow-aligned probability and binary masks. Overlay hysteresis reduces accessory flicker; closing and small-island suppression clean the shared silhouette. `--mask-stability` and `--mask-min-region` tune this at runtime. Set both to zero for the previous contour behavior; they are not stored in presets.

Behind-code keeps the previous stream count and glyph size, packing streams within the figure's horizontal bounds. The inward feather softens the sides, and code rises above the head. The final code and its glow are hidden by the union of visible silhouettes, including other figures. `--code-speed 0` freezes motion; `--code-density` controls density without shrinking glyphs. [Code options](options.md#code-density) · [Netrunner guide](cyber.md).

Optional `--target-weak-spots` draws fictional holographic patches clipped to selected current masks. It is not physical weakness detection. `target-weak-spots` controls the layer's styling; `--outline-shine` also affects its projection bands.

## Grid, targets, and captions

`--geo-grid-projection sphere` places vertices on a subdivided sphere and joins them with straight edges. The triangles' arrangement and rotation create a curved, faceted surface around the viewer; `flat` uses a planar triangular lattice. Scale and jitter alter its geometry. Center fade clears the middle, width thickens lines, and breaks insert seeded irregular gaps. Details add breathing satellite dots along the edges and seven-sided node rings.

The grid and its glow automatically fade around visible waveforms, waveform glyphs and the upper-right readout. Soft borders preserve the grid elsewhere; fully transparent HUD elements do not clear space. This applies to both projections and all waveform styles.

`--geo-grid-speed` controls brightness and dot pulses; `--geo-grid-rotation` independently rotates the geometry in degrees per second. Focus and Relic use 1.8 for a gentle, visible drift. Rotation zero is stationary, speed zero freezes brightness, and stills freeze both. Breaks remain attached to their edges during rotation. [Complete grid example](examples.md#grid).

`--target-mode selected` uses catalog targets, `auto` considers visible subjects, and `cycle` selects one at a time. `--target-motion persistent` glides one reticle without zoom; hold sets dwell and response sets smoothing. Empty automatic scenes keep the reticle searching, but have no figure-bound ornaments. Cuts and backward seeks reset selection. Explicit maskless catalog targets retain reticle-anchored ornament fallback.

`--target-motif triangles` enables independently seeded ornaments. Count, scale, speed and breaks alter their density, size, lifetime movement and edge imperfections. In segmented scenes they start 18% of the silhouette height below its center of mass, then rise with a small sideways drift. Their origin follows the selected figure rather than the gliding reticle. Stills freeze ornaments and code at time zero. [Relic example](examples.md#relic).

`--target-fill` supports filled and stroked treatment on all eleven shapes. `--target-stroke` is a separate optional colored border. `--target-outline` follows only selected subjects. Captions use `--target-label`, scale and cursor; they shrink to stay within frame margins and reserve cursor width while it blinks. `--no-target-label` clears an inherited caption. These layers have independent opacity and neon, while `--no-hud` hides all. [Geometric targets](targets.md) · [Murphy caption example](examples.md#murphy).

## Readable typography

Tech glyphs, Fremont descriptions and target captions use the selected `--hud-font`. Choices are Michroma Regular (`michroma`), a synthesized Michroma Medium (`michroma-medium`), and Orbitron Light, Medium or Bold. Michroma's upstream font has only a Regular face; the medium treatment lightly thickens its rasterized strokes and reports `Medium (synthetic)`. The bundled font file stays unmodified. Fremont defaults to Orbitron Bold; Murphy to Michroma Medium. Numeric seven-segment timecode is separate. A local `--hud-font-file` overrides the bundled face and its synthesized weight, must cover printable ASCII, and is never saved in portable presets. [Font-file recipe](examples.md#font-file).
