"""Original MIT-licensed heat synthesis; no learned weights or temperature claims."""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter


def sensor_size(width, height, longest):
    scale = min(1., longest / max(width, height))
    return max(1, round(width * scale)), max(1, round(height * scale))


class HeatField:
    """Synthesize scalar warmth before coloring; never blend photographic detail back in."""

    def __init__(self, width, height, resolution=256):
        self.size = sensor_size(width, height, resolution)

    def build(self, frame, subjects):
        # A very low-bandwidth environment stays cool even under bright sunlight.
        coarse = frame.convert('L').resize(sensor_size(*frame.size, 64), Image.Resampling.BOX)
        coarse = coarse.filter(ImageFilter.GaussianBlur(1.2)).resize(self.size, Image.Resampling.BILINEAR)
        ambient = .16 + np.asarray(coarse, dtype=np.float32) / 255 * .22
        heat = ambient.copy()
        yy, xx = np.mgrid[:self.size[1], :self.size[0]]
        for subject in subjects:
            mask_image = Image.fromarray(np.uint8(np.clip(subject.mask, 0, 1) * 255))
            mask_image = mask_image.resize(self.size, Image.Resampling.BILINEAR)
            hard = np.asarray(mask_image) > 127
            rows, cols = np.nonzero(hard)
            if not len(rows):
                continue
            # Object-relative fields move with the silhouette; faces and fabric never
            # contribute to internal warmth. These are aesthetic priors, not anatomy.
            x = (xx - cols.min()) / max(1, cols.max() - cols.min())
            y = (yy - rows.min()) / max(1, rows.max() - rows.min())
            core = np.exp(-((x - .5) / .40) ** 2 - ((y - .44) / .43) ** 2)
            crown = np.exp(-((x - .5) / .25) ** 2 - ((y - .13) / .16) ** 2)
            warmth = np.clip(.64 + .22 * core + .10 * crown, 0, .98)
            if subject.hot:
                warmth = np.clip(warmth + .10, 0, .99)
            alpha = np.asarray(mask_image.filter(ImageFilter.GaussianBlur(.8)), dtype=np.float32) / 255
            alpha *= subject.opacity
            # Max composition makes overlap independent of detection ordering.
            heat = np.maximum(heat, ambient * (1 - alpha) + warmth * alpha)
        # A sensor response is applied to the scalar field, before the palette.
        field = Image.fromarray(np.uint8(np.clip(heat, 0, 1) * 255))
        field = field.filter(ImageFilter.GaussianBlur(.65))
        return np.asarray(field.resize(frame.size, Image.Resampling.BILINEAR), dtype=np.uint8)
