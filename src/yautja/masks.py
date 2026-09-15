"""Current-frame overlay silhouettes, independent of optional model imports."""
import numpy as np
from PIL import Image


def subject_binary(subject, size=None, *, resample=Image.Resampling.NEAREST):
    """Use the tracker's stabilized silhouette when available, otherwise threshold."""
    stable = getattr(subject, 'binary_mask', None)
    if stable is not None:
        mask = Image.fromarray(np.uint8(stable) * 255)
        return mask.resize(size, Image.Resampling.NEAREST) if size else mask
    if resample == Image.Resampling.NEAREST:
        mask = Image.fromarray(np.uint8(subject.mask >= .5) * 255)
        return mask.resize(size, resample) if size else mask
    mask = Image.fromarray(np.uint8(np.clip(subject.mask, 0, 1) * 255))
    if size:
        mask = mask.resize(size, resample)
    return mask.point(lambda v: 255 if v >= 128 else 0)


def stabilize_binary(mask, previous, stability, min_region, scale=1.):
    """Flow-aligned hysteresis followed by closing and small-island removal."""
    if stability:
        binary = mask >= .58 if previous is None else ((mask >= .58) | ((mask >= .42) & previous))
    else:
        binary = mask >= .5
    if not min_region:
        return binary
    import cv2
    radius = max(1, round(2 * scale))
    kernel = np.ones((2 * radius + 1, 2 * radius + 1), np.uint8)
    closed = cv2.morphologyEx(np.uint8(binary), cv2.MORPH_CLOSE, kernel)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
    if count <= 1:
        return closed.astype(bool)
    sizes = stats[1:, cv2.CC_STAT_AREA]
    keep = np.r_[False, sizes >= sizes.max() * min_region]
    return keep[labels]
