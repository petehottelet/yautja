# Focus, Relic, Murphy and holographic geometry

All capabilities are shared options; presets only provide saved values. See the [canonical option reference](options.md) for ranges, defaults, aliases and enabling flags, and the [HUD role table](hud-elements.md) for ink/opacity/blur/neon.

## Complete styles

**Focus** preserves scene detail under a dark, restrained blue tint. Its bluish-violet geodesic sphere slowly rotates, with broken lines fading toward the center, pulsing satellite dots and occasional seven-sided rings. Partial blue/lavender/white subject edges shimmer. One persistent hexagon glides between subjects, with a large circle at 90% of the inscribed radius, six small inner circles, four outer circles and a center square.

**Relic** inherits Focus's scene and grid. Violet broken triangles spawn on the selected figure, rise gently, then contract, spin and fade. Soft light filaments stream upward behind the body core, aligned to shoulder/hip joints with a solid-body mask fallback. Arms and held props do not widen the light column. All foreground silhouettes occlude the trails and their glow. [`--code-style`](options.md#code-style) selects `light` or `glyphs`; `--code-size`, `--code-density` and `--code-speed` control stream spacing/width, count and upward motion. Focus leaves this effect off. Both presets leave decorative weak-spot patches off; the optional capability remains available.

**Murphy** uses a slight blue source cast, glowing green center-crossing XY box, selected-subject outline and a large Orbitron Medium caption with a blinking underscore. Automatic targeting needs no catalog. Its upper-right readout and waveform are hidden by preset opacity.

```bash
yautja "clip.mov" "focus.mp4" --stylepreset focus
yautja "clip.mov" "relic.mp4" --stylepreset relic
yautja "clip.mov" "murphy.mp4" --stylepreset murphy
```

These need [segmented setup](semantic.md). [Runnable presets and customization](examples.md#focus).

## Subject edges and code

`--subject-outline` enables all-subject edges; `--outline-style` chooses solid, shimmer or holographic. Width controls thickness, coverage/arcs control partial edge regions, speed controls travel/texture, and shine controls moving-band brightness. Focus/Relic set width 6.4, speed 1.35, shine 0.75 and outline ink `#8FA6FF`. Stills freeze the clock.

The tracker keeps flow-aligned probability and binary masks. Overlay hysteresis reduces accessory flicker; closing and small-island suppression clean the shared silhouette. `--mask-stability` and `--mask-min-region` tune this at runtime. Set both to zero for the previous contour behavior; they are not stored in presets.

Behind-code keeps the previous stream count and glyph size, packing streams within the figure's horizontal bounds. The inward feather softens the sides, and code rises above the head. The final code and its glow are hidden by the union of visible silhouettes, including other figures. `--code-speed 0` freezes motion; `--code-density` controls density without shrinking glyphs. [Code options](options.md#code-density) · [Netrunner guide](cyber.md).

Optional `--target-weak-spots` draws fictional holographic patches clipped to selected current masks. It is not physical weakness detection. `target-weak-spots` controls the layer's styling; `--outline-shine` also affects its projection bands.

## Grid, targets, and captions

`--geo-grid-projection sphere` places great-circle arcs on a subdivided sphere viewed from inside; `flat` uses a planar triangular lattice. Scale and jitter alter its geometry. Center fade clears the middle, width thickens lines, and breaks insert seeded irregular gaps. Details add breathing satellite dots and seven-sided node rings.

`--geo-grid-speed` controls brightness and dot pulses; `--geo-grid-rotation` independently rotates the geometry. Rotation zero is stationary, speed zero freezes brightness, and stills freeze both. Breaks remain attached to their edges during rotation. [Complete grid example](examples.md#grid).

`--target-mode selected` uses catalog targets, `auto` considers visible subjects, and `cycle` selects one at a time. `--target-motion persistent` glides one reticle without zoom; hold sets dwell and response sets smoothing. Empty automatic scenes keep the reticle searching, but have no figure-bound ornaments. Cuts and backward seeks reset selection. Explicit maskless catalog targets retain reticle-anchored ornament fallback.

`--target-motif triangles` enables independently seeded ornaments. Count, scale, speed and breaks alter their density, size, lifetime movement and edge imperfections. In segmented scenes they follow the selected mask centroid rather than the gliding reticle. Stills freeze ornaments and code at time zero. [Relic example](examples.md#relic).

`--target-fill` supports filled and stroked treatment on all eleven shapes. `--target-stroke` is a separate optional colored border. `--target-outline` follows only selected subjects. Captions use `--target-label`, scale and cursor; they shrink to stay within frame margins and reserve cursor width while it blinks. `--no-target-label` clears an inherited caption. These layers have independent opacity and neon, while `--no-hud` hides all. [Geometric targets](targets.md) · [Murphy caption example](examples.md#murphy).

## Readable typography

Tech glyphs, Fremont descriptions and target captions use the selected `--hud-font`. Bundled choices are Michroma and Orbitron Light, Medium or Bold. Fremont defaults to Bold; Murphy to Medium. Numeric seven-segment timecode is separate. A local `--hud-font-file` overrides the bundled font, must cover printable ASCII, and is never saved in portable presets. [Font-file recipe](examples.md#font-file).
