"""Seeded pose/surface-guided synthetic warmth; no temperature measurement."""
from __future__ import annotations

import hashlib

import numpy as np
from PIL import Image, ImageFilter

THERMAL_MODES = ('classic', 'silhouette', 'cinematic', 'detailed')
THERMAL_ALIASES = {'semantic': 'silhouette', 'realistic': 'detailed'}


def resolve_thermal(mode):
    mode = THERMAL_ALIASES.get(mode, mode)
    if mode not in THERMAL_MODES:
        raise ValueError('Unknown thermal mode: ' + mode)
    return mode

# Label: (synthetic warmth, compositing priority, maximum person-area fraction,
# minimum detection confidence). These are visual priors, not material measurements.
SURFACE_RULES = {
    'jacket': (.67, 1, .90, .32), 'shirt': (.73, 1, .90, .32),
    'pants': (.63, 1, .85, .32), 'shorts': (.65, 1, .65, .35),
    'dress': (.66, 1, .95, .35), 'skirt': (.64, 1, .70, .35),
    'face': (.97, 3, .22, .30), 'hand': (.925, 3, .13, .30),
    'hair': (.61, 4, .22, .35), 'hat': (.48, 5, .23, .40),
    'shoes': (.43, 4, .22, .36), 'backpack': (.46, 2, .75, .43),
    'bag': (.44, 2, .75, .43), 'camera': (.34, 6, .40, .45),
    'glasses': (.32, 6, .06, .50),
}


def sensor_size(width, height, longest):
    scale = min(1., longest / max(width, height))
    return max(1, round(width * scale)), max(1, round(height * scale))


class HeatField:
    """Color broad anatomical regions without reconstructing faces or fabric."""

    def __init__(self, width, height, resolution=256, seed=42):
        self.size = sensor_size(width, height, resolution)
        self.seed = seed
        self.yy, self.xx = np.mgrid[:self.size[1], :self.size[0]].astype(np.float32)

    @staticmethod
    def variation(x, y, phase):
        # Smooth value noise avoids repeating stripes. Its coordinates come from
        # body/bone axes, never frame time or source-image brightness.
        def layer(scale, seed):
            u, v = x * scale + phase[1], y * scale + phase[2]
            ix, iy = np.floor(u).astype(np.int64), np.floor(v).astype(np.int64)
            fx, fy = u - ix, v - iy
            fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)

            def value(a, b):
                h = a.astype(np.uint32) * np.uint32(374761393) + b.astype(np.uint32) * np.uint32(668265263)
                h ^= np.uint32(seed)
                h = (h ^ (h >> 13)) * np.uint32(1274126177)
                return (h ^ (h >> 16)).astype(np.float32) / 4294967295. * 2 - 1

            top = value(ix, iy) * (1 - fx) + value(ix + 1, iy) * fx
            bottom = value(ix, iy + 1) * (1 - fx) + value(ix + 1, iy + 1) * fx
            return top * (1 - fy) + bottom * fy

        seed = int(phase[0] * 1000000)
        return .78 * layer(2.6, seed) + .22 * layer(6.1, seed ^ 0x9e3779b9)

    def surface(self, subject, hard):
        rows, cols = np.nonzero(hard)
        span = max(2., float(rows.max() - rows.min() + 1))
        origin = np.array([np.median(cols), rows.min() + .24 * span], dtype=np.float32)
        axis = np.array([0., 1.], dtype=np.float32)
        torso = .32 * span
        joints = getattr(subject, 'keypoints', None)
        valid = np.zeros(17, dtype=bool)
        if subject.label == 'person' and joints is not None and np.shape(joints) == (17, 3):
            joints = np.asarray(joints, dtype=np.float32).copy()
            joints[:, 0] *= self.size[0] / subject.mask.shape[1]
            joints[:, 1] *= self.size[1] / subject.mask.shape[0]
            valid = (np.isfinite(joints).all(axis=1) & (joints[:, 2] >= .3) &
                     (joints[:, 0] >= 0) & (joints[:, 0] < self.size[0]) &
                     (joints[:, 1] >= 0) & (joints[:, 1] < self.size[1]))
            if valid[[5, 6, 11, 12]].all():
                shoulders = joints[[5, 6], :2].mean(axis=0)
                hips = joints[[11, 12], :2].mean(axis=0)
                length = float(np.linalg.norm(hips - shoulders))
                if .1 * span < length < .8 * span:
                    origin, torso = shoulders, length
                    axis = (hips - shoulders) / torso
        torso = max(2., torso)
        lateral = np.array([axis[1], -axis[0]])
        dx, dy = self.xx - origin[0], self.yy - origin[1]
        x = (dx * lateral[0] + dy * lateral[1]) / torso
        y = (dx * axis[0] + dy * axis[1]) / torso
        identity = f'{self.seed}:{subject.track_id}:{subject.label}'.encode()
        rng = np.random.default_rng(int.from_bytes(hashlib.sha256(identity).digest()[:8], 'little'))
        phases = rng.uniform(0, 2 * np.pi, (16, 4))
        offset = float(rng.uniform(-.025, .025))
        mottling = self.variation(x, y, phases[0])
        base = .735 + offset + .06 * mottling
        total, weight = base * .25, np.full(hard.shape, .25, dtype=np.float32)

        def region(a, b, radius, target, index, confidence=1., texture=.04):
            delta = b - a
            length = max(.5, float(np.linalg.norm(delta)))
            direction = delta / length
            px, py = self.xx - a[0], self.yy - a[1]
            along = (px * direction[0] + py * direction[1]) / length
            t = np.clip(along, 0, 1)
            distance = np.hypot(px - t * delta[0], py - t * delta[1])
            influence = np.exp(-.5 * (distance / max(.8, radius)) ** 4) * confidence
            side = (px * direction[1] - py * direction[0]) / torso
            detail = self.variation(side * 2, along * 1.7, phases[index])
            value = target + offset + texture * detail
            total[:] += influence * value
            weight[:] += influence

        def bone(a, b, radius, target, index):
            if valid[a] and valid[b]:
                confidence = float(np.clip((min(joints[a, 2], joints[b, 2]) - .25) / .35, 0, 1))
                region(joints[a, :2], joints[b, :2], torso * radius, target, index, confidence)

        if valid.any():
            # Regions are artistic priors tied to actual joint estimates. A cooler
            # torso suggests insulation; it is not a clothing/material classifier.
            if valid[[5, 6, 11, 12]].all():
                shoulders = joints[[5, 6], :2].mean(axis=0)
                hips = joints[[11, 12], :2].mean(axis=0)
                width = float(np.linalg.norm(joints[5, :2] - joints[6, :2]))
                confidence = float(np.clip((joints[[5, 6, 11, 12], 2].min() - .25) / .35, 0, 1))
                region(shoulders, hips, max(.27 * torso, .40 * width), .71, 1, confidence, texture=.075)
            for args in [(5, 7, .17, .735, 2), (6, 8, .17, .75, 3),
                         (7, 9, .13, .79, 4), (8, 10, .13, .80, 5),
                         (11, 13, .23, .70, 6), (12, 14, .23, .72, 7),
                         (13, 15, .17, .735, 8), (14, 16, .17, .75, 9)]:
                bone(*args)
            for wrist, elbow, index in [(9, 7, 10), (10, 8, 11)]:
                if valid[wrist]:
                    hand = joints[wrist, :2].copy()
                    if valid[elbow]:
                        hand += .12 * (hand - joints[elbow, :2])
                    confidence = float(np.clip((joints[wrist, 2] - .25) / .35, 0, 1))
                    region(hand, hand, .18 * torso, .88, index, confidence, texture=.025)
            face = np.flatnonzero(valid[:5])
            if len(face) >= 2:
                # Collapse facial landmarks into ONE broad head region. Never draw
                # separate eyes, nose, mouth, or source-image facial features.
                head = joints[face, :2].mean(axis=0) - axis * .05 * torso
                confidence = float(np.clip((joints[face, 2].mean() - .25) / .35, 0, 1))
                if valid[[5, 6]].all():
                    neck = joints[[5, 6], :2].mean(axis=0)
                    region(head, neck, .14 * torso, .825, 12, confidence, texture=.025)
                region(head, head, .29 * torso, .915, 13, confidence, texture=.025)
        warmth = np.clip(total / weight, .59, .965)
        if subject.hot:
            warmth = np.clip(warmth + .10, 0, .99)
        return warmth

    def build(self, frame, subjects):
        # A very low-bandwidth environment stays cool even under bright sunlight.
        coarse = frame.convert('L').resize(sensor_size(*frame.size, 64), Image.Resampling.BOX)
        coarse = coarse.filter(ImageFilter.GaussianBlur(1.2)).resize(self.size, Image.Resampling.BILINEAR)
        ambient = .16 + np.asarray(coarse, dtype=np.float32) / 255 * .22
        heat = ambient.copy()
        for subject in subjects:
            mask_image = Image.fromarray(np.uint8(np.clip(subject.mask, 0, 1) * 255))
            mask_image = mask_image.resize(self.size, Image.Resampling.BILINEAR)
            hard = np.asarray(mask_image) > 127
            if not hard.any():
                continue
            warmth = self.surface(subject, hard)
            alpha = np.asarray(mask_image.filter(ImageFilter.GaussianBlur(.8)), dtype=np.float32) / 255
            alpha *= subject.opacity
            heat = np.maximum(heat, ambient * (1 - alpha) + warmth * alpha)
        field = Image.fromarray(np.uint8(np.clip(heat, 0, 1) * 255))
        field = field.filter(ImageFilter.GaussianBlur(.65))
        return np.asarray(field.resize(frame.size, Image.Resampling.BILINEAR), dtype=np.uint8)


class SurfaceHeatField(HeatField):
    """Visible surface segmentation with sharper boundaries and a cool scene."""

    ambient_resolution, ambient_blur = 192, .65
    edge_blur, field_blur = .25, .30

    def detailed_surface(self, frame, subject, hard, garment_shading=True):
        warmth = .70 + (self.surface(subject, hard) - .735) * .65
        rows, cols = np.nonzero(hard)
        span = max(2, rows.max() - rows.min() + 1)
        x = (self.xx - np.median(cols)) / span
        y = (self.yy - rows.min()) / span
        gray = np.asarray(frame.convert('L').resize(self.size, Image.Resampling.BOX), dtype=np.float32) / 255
        for part in sorted(subject.parts, key=lambda p: (SURFACE_RULES.get(p.label, (0, 0))[1], p.score, p.label)):
            if part.label not in SURFACE_RULES:
                continue
            target, priority, _, minimum = SURFACE_RULES[part.label]
            if not np.isfinite(part.score) or part.score < minimum:
                continue
            mask = Image.fromarray(np.uint8(np.clip(part.mask, 0, 1) * 255)).resize(self.size, Image.Resampling.BILINEAR)
            mask = np.asarray(mask, dtype=np.float32) / 255 * hard
            if mask.sum() < 1:
                continue
            identity = f'{self.seed}:{subject.track_id}:{part.label}'.encode()
            rng = np.random.default_rng(int.from_bytes(hashlib.sha256(identity).digest()[:8], 'little'))
            phase = rng.uniform(0, 2 * np.pi, 4)
            value = target + float(rng.uniform(-.015, .015)) + .025 * self.variation(x * 2, y * 2, phase)
            if priority == 1 and garment_shading:
                # Only segmented garments get low-frequency fold/shading cues.
                # Normalize within the garment: visible dark cloth is not colder.
                radius = max(1.2, float(span * .015))
                weight = np.asarray(Image.fromarray(np.uint8(mask * 255)).filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255
                blurred = np.asarray(Image.fromarray(np.uint8(gray * mask * 255)).filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255
                smooth = blurred / np.maximum(weight, .01)
                mean = float((smooth * mask).sum() / mask.sum())
                deviation = max(.035, float(np.sqrt(((smooth - mean) ** 2 * mask).sum() / mask.sum())))
                value += .022 * np.clip((smooth - mean) / deviation, -1.5, 1.5)
            if subject.hot:
                value += .07
            # Confidence suppresses marginal proposals instead of forcing a cold cutout.
            alpha = np.asarray(Image.fromarray(np.uint8(mask * 255)).filter(ImageFilter.GaussianBlur(.35)), dtype=np.float32) / 255
            alpha *= min(1., .70 + max(0., part.score - minimum) * 2)
            warmth = warmth * (1 - alpha) + value * alpha
        return np.clip(warmth, .20, .995)

    def build(self, frame, subjects):
        # Retain broad scenery structure without reading its brightness as heat.
        coarse = frame.convert('L').resize(sensor_size(*frame.size, self.ambient_resolution), Image.Resampling.BOX)
        coarse = coarse.filter(ImageFilter.GaussianBlur(self.ambient_blur)).resize(self.size, Image.Resampling.BILINEAR)
        ambient = .17 + np.asarray(coarse, dtype=np.float32) / 255 * .22
        heat = ambient.copy()
        # Larger silhouettes are an explicit foreground approximation. Unlike max
        # heat compositing, this lets cool gear occlude a warm overlapping person.
        ordered = sorted(subjects, key=lambda s: (float(s.mask.sum()), s.track_id))
        for subject in ordered:
            mask = Image.fromarray(np.uint8(np.clip(subject.mask, 0, 1) * 255)).resize(self.size, Image.Resampling.BILINEAR)
            hard = np.asarray(mask) > 127
            if not hard.any():
                continue
            warmth = self.detailed_surface(frame, subject, hard)
            alpha = np.asarray(mask.filter(ImageFilter.GaussianBlur(self.edge_blur)), dtype=np.float32) / 255 * subject.opacity
            heat = heat * (1 - alpha) + warmth * alpha
        field = Image.fromarray(np.uint8(np.clip(heat, 0, 1) * 255))
        field = field.filter(ImageFilter.GaussianBlur(self.field_blur))
        return np.asarray(field.resize(frame.size, Image.Resampling.BILINEAR), dtype=np.uint8)


class CinematicHeatField(SurfaceHeatField):
    """Broad surface patches between soft silhouettes and detailed segmentation."""

    ambient_resolution, ambient_blur = 112, .95
    edge_blur, field_blur = .55, .5

    def detailed_surface(self, frame, subject, hard, garment_shading=False):
        # Keep skin/gear cues but soften small parts into broad heat patches.
        # Mask-normalized blur avoids drawing a cold fringe inside the body.
        surface = super().detailed_surface(frame, subject, hard, garment_shading=False)
        rows = np.nonzero(hard)[0]
        radius = max(.9, float((rows.max() - rows.min() + 1) * .025))
        support = Image.fromarray(np.uint8(hard) * 255)
        weight = np.asarray(support.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255
        samples = Image.fromarray(np.uint8(np.clip(surface * hard, 0, 1) * 255))
        broad = np.asarray(samples.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255
        broad /= np.maximum(weight, .01)
        anatomy = self.surface(subject, hard)
        # Retain the fuller warmth and organic body variation of the older look.
        warmth = .45 * anatomy + .55 * broad
        # Gentle temperature-like bands, applied to the synthetic field only.
        warmth = .8 * warmth + .2 * np.round(warmth * 16) / 16
        return np.clip(warmth, .20, .995)
