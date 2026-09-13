# Integration contract

The supported 2.x interface is the `yautja` CLI, equivalently the chosen environment's `python -m yautja`, its exit codes (0 success, 1 conversion/runtime failure, 2 invalid arguments, 130 cancellation), and the versioned JSON conversion report. Existing flags retain their meanings within the major version; new flags can require a newer minor version. Inspect `--help` and the installed `__version__` before using newly added controls.

`import yautja` exposes `__version__` without loading image or ML libraries. `yautja.runtime` is also safe to import without those dependencies. Installation metadata comes from the installed distribution; contributors should use an editable install.

Python rendering APIs are **experimental**: `yautja.render.Renderer(...).render(PIL_image, seconds, wave=None, subjects=())` returns a new RGB Pillow image. `render_field(uint8_array, seconds, wave=None, subjects=())` accepts an already computed two-dimensional field matching the renderer's height and width. The defaults use Classic luminance mapping. Segmented rendering requires subject masks from a separately configured semantic pipeline.

```python
from PIL import Image
from yautja.render import Renderer

with Image.open('photo.jpg') as source:
    image = source.convert('RGB')
    result = Renderer(*image.size, palette='green-phosphor', hud=False).render(image, 0)
    result.save('restyled.png')
```

This low-level example does not perform the CLI's orientation, metadata, input/output protection or atomic-write checks. Prefer the CLI for end-user conversion. Other helpers, classes and module internals are not a promised stable API merely because tests or repository tools import them.
