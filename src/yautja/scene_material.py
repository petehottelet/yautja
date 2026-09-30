"""Visible ownership, conservative room planes and persistent scene coordinates."""
from copy import deepcopy
from collections import OrderedDict, deque
import importlib.util
import math
import time as clock

import numpy as np
from PIL import Image, ImageFilter

from .noumenon import (MaterialStyle, NoumenonMaterial, SOURCE_REVISION, TICK_RATE,
                       WARMUP_TICKS, linear_to_srgb, shade)
from .signal import stable_number


def resized_mask(mask, size):
    values = np.clip(np.nan_to_num(np.asarray(mask, np.float32), nan=0, posinf=0, neginf=0), 0, 1)
    return np.asarray(Image.fromarray(values).resize(size, Image.Resampling.BILINEAR))


def blurred_coverage(mask, radius):
    """Bounded soft coverage; filtering never requires an optional dependency."""
    image = Image.fromarray(np.uint8(np.rint(np.clip(mask, 0, 1) * 255)))
    return np.asarray(image.filter(ImageFilter.GaussianBlur(radius)), np.float32) / 255


def surface_key(subject):
    return ('track', subject.track_id) if subject.track_id else ('untracked', subject.label)


def visible_ownership(subjects, size):
    """Front-over soft ownership; residual plus weights sum to one (atol 2e-6).

    Lower image contact points are a conservative visibility cue, not metric
    depth. Stable track IDs break ties; confidence is never a depth ordering.
    Duplicate track IDs do not add a second material layer. Keep at most 64
    visible candidates; anything else still receives the environment material.
    """
    candidates = []
    seen = set()
    for subject in subjects:
        source = np.asarray(subject.mask)
        ys, xs = np.nonzero(source > .1)
        if not len(ys):
            continue
        key = surface_key(subject)
        if subject.track_id and key in seen:
            continue
        seen.add(key)
        candidates.append((float(ys.max()) / source.shape[0], subject.track_id, subject))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    residual = np.ones(size[::-1], np.float32)
    for _, _, subject in candidates[:64]:
        opacity = float(np.clip(np.nan_to_num(subject.opacity), 0, 1))
        alpha = resized_mask(subject.mask, size) * opacity
        weight = alpha * residual
        residual = residual * (1 - alpha)
        yield subject, weight
    yield None, residual


def homography(source, destination):
    """Four point projective mapping with an explicit, testable convention."""
    rows, values = [], []
    for (x, y), (u, v) in zip(source, destination):
        rows.extend([[x, y, 1, 0, 0, 0, -u * x, -u * y],
                     [0, 0, 0, x, y, 1, -v * x, -v * y]])
        values.extend([u, v])
    return np.append(np.linalg.solve(rows, values), 1).reshape(3, 3)


def project(matrix, x, y):
    denominator = matrix[2, 0] * x + matrix[2, 1] * y + matrix[2, 2]
    denominator = np.where(np.abs(denominator) < 1e-5, 1e-5, denominator)
    return ((matrix[0, 0] * x + matrix[0, 1] * y + matrix[0, 2]) / denominator,
            (matrix[1, 0] * x + matrix[1, 1] * y + matrix[1, 2]) / denominator)


def estimate_room(gray, foreground=None):
    """Require convergence plus a supported, closed far-wall boundary.

    No geometry model is downloaded. Reject unsupported closeups/outdoor views.
    The result is an image-based plane hypothesis, not recovered metric depth.
    """
    try:
        import cv2
    except ImportError:
        return None
    h, w = gray.shape
    edges = cv2.Canny(gray, 55, 140)
    if foreground is not None:
        edges[foreground > .2] = 0
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 28, minLineLength=w * .10, maxLineGap=w * .03)
    if lines is None:
        return None
    segments = lines[:, 0].astype(float).reshape(-1, 2, 2)
    diagonals, verticals = [], []
    for x0, y0, x1, y1 in lines[:, 0]:
        dx, dy = float(x1 - x0), float(y1 - y0)
        if abs(dx) < max(2, abs(dy) * .12) and abs(dy) > h * .14:
            verticals.append((x0 + x1) / 2)
        if abs(dx) < w * .04 or not .12 < abs(dy / dx) < 2.8:
            continue
        length = math.hypot(dx, dy)
        a, b = -dy / length, dx / length
        diagonals.append((a, b, -(a * x0 + b * y0), (x0 + x1) / 2, (y0 + y1) / 2, length))
    diagonals = sorted(diagonals, key=lambda line: -line[5])[:40]
    if len(diagonals) < 4 or len(verticals) < 2:
        return None
    lines = np.asarray(diagonals)
    best = None
    for i, first in enumerate(lines):
        for second in lines[i + 1:]:
            if abs(first[0] * second[1] - first[1] * second[0]) < .22:
                continue
            vp = np.linalg.solve(np.array([first[:2], second[:2]]), -np.array([first[2], second[2]]))
            if not (.22 * w < vp[0] < .78 * w and .2 * h < vp[1] < .7 * h):
                continue
            good = np.abs(lines[:, :2] @ vp + lines[:, 2]) < max(3, w * .018)
            supporting = lines[good]
            quadrants = {(int(line[3] > vp[0]), int(line[4] > vp[1])) for line in supporting}
            if len(quadrants) != 4:
                continue
            score = supporting[:, 5].sum()
            if best is None or score > best[0]:
                best = (score, vp, supporting)
    if best is None:
        return None
    _, (vx, vy), supporting = best
    left = [v for v in verticals if .07 * w < v < vx - .06 * w]
    right = [v for v in verticals if vx + .06 * w < v < .93 * w]
    if not left or not right:
        return None
    xl, xr = max(left), min(right)
    corners = []
    for x, right_side, bottom in ((xl, False, False), (xr, True, False), (xr, True, True), (xl, False, True)):
        group = [line for line in supporting if (line[3] > vx) == right_side and (line[4] > vy) == bottom]
        y = float(np.median([-(line[0] * x + line[2]) / line[1] for line in group]))
        corners.append((x / w, y / h))
    tl, tr, br, bl = corners
    if min(bl[1], br[1]) - max(tl[1], tr[1]) < .08 or any(not 0 < y < 1 for _, y in corners):
        return None
    corners = np.array(corners, np.float32)
    # Trees and branches can supply a vanishing point and upright lines. They
    # do not establish room planes unless long, aligned segments also close all
    # four sides of the far wall. Count union coverage, never duplicate edges.
    boundary = corners * [w, h]
    for start, end in zip(boundary, np.roll(boundary, -1, axis=0)):
        delta = end - start
        length = np.linalg.norm(delta)
        direction = delta / length
        normal = np.array([-direction[1], direction[0]])
        distance = np.abs((segments - start) @ normal)
        vectors = segments[:, 1] - segments[:, 0]
        aligned = np.abs(vectors @ normal) <= np.linalg.norm(vectors, axis=1) * .08
        close = np.max(distance, axis=1) < max(3., w * .012)
        intervals = np.clip((segments[aligned & close] - start) @ direction / length, 0, 1)
        covered, previous = 0., 0.
        for low, high in sorted(np.sort(intervals, axis=1).tolist()):
            covered += max(0., high - max(low, previous))
            previous = max(previous, high)
        if covered < .65:
            return None
    return corners


class SurfaceMapper:
    def __init__(self, size, strength=1.):
        self.size, self.strength = size, strength
        self.reset()

    def reset(self):
        self.room = None
        self.camera = np.eye(3)
        self.previous = None
        self.previous_foreground = None
        self.time = self.shot = None
        self.last_estimate = -math.inf
        self.confidence = 1.
        self.mode = 'stable-flat'
        self.fallback = 'insufficient-room-evidence' if importlib.util.find_spec('cv2') else 'opencv-unavailable'

    def checkpoint(self):
        return deepcopy(self.__dict__)

    def restore(self, state):
        if state.get('size') != self.size or state.get('strength') != self.strength:
            raise ValueError('Surface checkpoint dimensions/settings do not match')
        self.__dict__.update(deepcopy(state))

    def update(self, frame, subjects, time, shot):
        width, height = self.size
        small_size = (min(480, width), max(2, round(height * min(480, width) / width)))
        gray = np.asarray(frame.convert('L').resize(small_size), np.uint8)
        foreground = np.zeros(gray.shape, np.float32)
        for subject in subjects:
            np.maximum(foreground, resized_mask(subject.mask, small_size), out=foreground)
        rewind = self.time is not None and time < self.time
        cut = self.previous is not None and np.abs(gray.astype(float) - self.previous).mean() > 48
        if (self.time is not None and shot != self.shot) or rewind or cut:
            self.reset()
        dt = max(0., time - self.time) if self.time is not None else 0.
        if self.strength and self.room is not None and self.previous is not None and dt > 0:
            self._track_camera(gray, foreground, dt)
        if self.strength and time - self.last_estimate >= 1:
            self.last_estimate = time
            room = estimate_room(gray, foreground)
            if room is None:
                self.room = None
                self.camera = np.eye(3)
                self.confidence = 1.
            elif self.room is None:
                # Convert the current plane corners to the persistent anchor view.
                x, y = project(self.camera, room[:, 0] * width, room[:, 1] * height)
                self.room = np.column_stack((x / width, y / height))
        self.previous, self.previous_foreground = gray, foreground
        self.mode = ('room-planes' if self.room_supported else 'stable-flat') if self.strength else 'flat-disabled'
        if not self.strength:
            self.fallback = 'mapping-disabled'
        elif self.room is not None:
            self.fallback = 'none' if self.confidence > .8 else 'weak-image-correspondence'
        else:
            self.fallback = 'insufficient-room-evidence' if importlib.util.find_spec('cv2') else 'opencv-unavailable'
        self.time, self.shot = time, shot

    def _track_camera(self, gray, foreground, dt):
        try:
            import cv2
        except ImportError:
            self.fallback = 'opencv-unavailable'
            return
        allowed = np.uint8((self.previous_foreground < .1) * 255)
        points = cv2.goodFeaturesToTrack(self.previous, 160, .02, 9, mask=allowed)
        valid = False
        if points is not None and len(points) >= 10:
            moved, status, _ = cv2.calcOpticalFlowPyrLK(self.previous, gray, points, None)
            back, reverse, _ = cv2.calcOpticalFlowPyrLK(gray, self.previous, moved, None)
            old, new = points[:, 0], moved[:, 0]
            xy = np.rint(new).astype(int)
            inside = (xy[:, 0] >= 0) & (xy[:, 0] < gray.shape[1]) & (xy[:, 1] >= 0) & (xy[:, 1] < gray.shape[0])
            keep = status.ravel().astype(bool) & reverse.ravel().astype(bool) & inside
            keep &= np.linalg.norm(back[:, 0] - old, axis=1) < 1
            keep[inside] &= foreground[xy[inside, 1], xy[inside, 0]] < .1
            if np.count_nonzero(keep) >= 10:
                # Least-squares affine mapping is deterministic; reject outliers,
                # excessive scale/skew, and weak spatial feature support.
                design = np.column_stack((new[keep], np.ones(keep.sum())))
                fit = np.linalg.lstsq(design, old[keep], rcond=None)[0].T
                errors = np.linalg.norm(design @ fit.T - old[keep], axis=1)
                inliers = errors < 1.5
                if inliers.sum() >= 10 and inliers.mean() > .7:
                    fit = np.linalg.lstsq(design[inliers], old[keep][inliers], rcond=None)[0].T
                    scale = np.linalg.svd(fit[:, :2], compute_uv=False)
                    span = np.ptp(new[keep][inliers], axis=0) / np.array(gray.shape[::-1])
                    if min(scale) > .94 and max(scale) < 1.06 and min(span) > .25:
                        transform = np.vstack((fit, [0, 0, 1]))
                        zoom = np.diag([self.size[0] / gray.shape[1], self.size[1] / gray.shape[0], 1])
                        self.camera = self.camera @ zoom @ transform @ np.linalg.inv(zoom)
                        valid = True
        # Deformation relaxes smoothly if correspondence is lost; no phase reset.
        target = 1. if valid else 0.
        self.confidence += (target - self.confidence) * (1 - math.exp(-dt / 1.5))

    def flat(self, x, y):
        """Screen-vertical fallback; camera roll, skew and zoom never affect it."""
        return x, y

    @property
    def room_supported(self):
        return self.room is not None and bool(self.strength) and self.confidence >= .65

    def environment(self, x, y):
        width, height = self.size
        if not self.room_supported:
            return self.flat(x, y)
        ax, ay = project(self.camera, x, y)
        u, v = ax.copy(), ay.copy()
        tl, tr, br, bl = self.room * np.array(self.size)
        # Floor/ceiling flow is a stable in-plane depth axis. Walls retain an
        # upright axis; opposing walls have distinct projective coordinates.
        planes = [([tl, tr, br, bl], [(0, 0), (width * .5, 0), (width * .5, height), (0, height)]),
                  ([(0, height), (width, height), br, bl], [(0, 0), (width, 0), (width, -height * 1.5), (0, -height * 1.5)]),
                  ([(0, 0), (width, 0), tr, tl], [(0, 0), (width, 0), (width, height * 1.5), (0, height * 1.5)]),
                  ([(0, 0), tl, bl, (0, height)], [(0, 0), (width * .65, 0), (width * .65, height), (0, height)]),
                  ([tr, (width, 0), (width, height), br], [(0, 0), (width * .65, 0), (width * .65, height), (0, height)])]
        for corners, target in planes:
            corners = np.asarray(corners)
            # Convex polygon membership in the anchor view, including camera motion.
            crosses = [(b[0] - a[0]) * (ay - a[1]) - (b[1] - a[1]) * (ax - a[0])
                       for a, b in zip(corners, np.roll(corners, -1, axis=0))]
            inside = np.logical_or(np.logical_and.reduce([c >= 0 for c in crosses]),
                                   np.logical_and.reduce([c <= 0 for c in crosses]))
            pu, pv = project(homography(corners, target), ax, ay)
            amount = self.strength * self.confidence
            u[inside] = ax[inside] + (pu[inside] - ax[inside]) * amount
            v[inside] = ay[inside] + (pv[inside] - ay[inside]) * amount
        return u, v

class SceneMaterial:
    def __init__(self, size, seed=42, code_size=22., code_speed=1., code_density=1., **options):
        self.style = MaterialStyle(**options)
        self.size, self.seed = size, seed
        # Classic uses 80 square cells along the longer viewport dimension.
        # A 24-pixel cell at a 1920-pixel long edge preserves that density.
        self.cell = max(2., code_size * max(size) / 1920)
        self.inner_edge_radius = max(.6, self.cell * .12)
        self.outer_edge_radius = max(1., self.cell * .45)
        self.pitch = self.cell / max(1., code_density)
        self.material = NoumenonMaterial(seed, self.style.material_face, self.style.material_mix, code_speed, code_density)
        self.subject_density = min(3., code_density * self.style.material_subject_density)
        self.subject_materials = OrderedDict()
        self.layer_shot = None
        self.mapper = SurfaceMapper(size, self.style.material_mapping)
        self.frames = 0
        self.material_seconds = self.mapping_seconds = 0.
        self.modes = set()
        self.frame_seconds = deque(maxlen=512)

    def checkpoint(self):
        """In-memory chunk checkpoint; material state is reconstructed from time."""
        return {'version': 2, 'size': self.size, 'seed': self.seed, 'cell': self.cell, 'pitch': self.pitch,
                'style': self.style.report(), 'speed': self.material.speed, 'density': self.material.density,
                'mapper': self.mapper.checkpoint()}

    def restore(self, checkpoint):
        current = self.checkpoint()
        if any(checkpoint.get(key) != current[key] for key in current if key != 'mapper'):
            raise ValueError('Scene material checkpoint configuration does not match')
        self.mapper.restore(checkpoint['mapper'])
        self.subject_materials.clear()
        self.layer_shot = self.mapper.shot

    def subject_material(self, subject, ordinal=0):
        """A deterministic instance per shot/track, with a bounded shared-atlas cache."""
        if self.layer_shot != self.mapper.shot:
            self.subject_materials.clear()
            self.layer_shot = self.mapper.shot
        key = surface_key(subject) if subject.track_id else (*surface_key(subject), ordinal)
        if key not in self.subject_materials:
            seed = stable_number(self.seed, 'noumenon-silhouette', self.layer_shot, *key)
            self.subject_materials[key] = NoumenonMaterial(seed, self.style.material_face, self.style.material_mix,
                                                          self.material.speed, self.subject_density,
                                                          self.style.material_subject_trail)
        self.subject_materials.move_to_end(key)
        if len(self.subject_materials) > 64:
            self.subject_materials.popitem(last=False)
        return self.subject_materials[key]

    def report(self):
        return {**self.style.report(), 'material_backend': 'numpy-classic-v1', 'material_source_revision': SOURCE_REVISION,
                'material_parity': 'behavioral-port; not WebGL pixel parity', 'material_tick_hz': TICK_RATE,
                'material_warmup_ticks': WARMUP_TICKS, 'material_time_origin': 'output-relative',
                'material_color_space': 'linear-light composition; sRGB output',
                'material_cell_pixels': self.cell, 'material_subject_mapping': 'independent-screen-vertical-rain',
                'material_subject_density_resolved': self.subject_density,
                'material_subject_instances_cached': len(self.subject_materials),
                'material_inner_edge_radius_pixels': self.inner_edge_radius,
                'material_outer_edge_radius_pixels': self.outer_edge_radius,
                'material_mapping_modes': sorted(self.modes), 'material_mapping_mode': self.mapper.mode,
                'material_mapping_fallback': self.mapper.fallback,
                'material_plane_confidence': round(self.mapper.confidence, 4) if self.mapper.room is not None else 0.,
                'material_frames': self.frames, 'material_generation_seconds': round(self.material_seconds, 4),
                'material_mapping_compositing_seconds': round(self.mapping_seconds, 4),
                'material_frame_sample_count': len(self.frame_seconds),
                'material_frame_sample_scope': 'most recent 512 frames maximum',
                'material_frame_median_seconds': round(float(np.median(self.frame_seconds)), 6) if self.frame_seconds else None,
                'material_frame_p95_seconds': round(float(np.percentile(self.frame_seconds, 95)), 6) if self.frame_seconds else None}

    def render(self, frame, time, subjects=(), shot=None, *, material_subjects=None):
        """Highlight selected live track IDs; None selects all, an empty set none."""
        if frame.size != self.size:
            raise ValueError('Code scene frame must match renderer dimensions')
        started = clock.perf_counter()
        self.material.field(time)
        generation_seconds = clock.perf_counter() - started
        background_generation_seconds = generation_seconds
        self.material_seconds += generation_seconds
        started = clock.perf_counter()
        self.mapper.update(frame, subjects, time, shot)
        self.modes.add(self.mapper.mode)
        luma = np.asarray(frame.convert('L').filter(ImageFilter.GaussianBlur(max(.5, self.cell * .16))), np.float32) / 255
        broad = np.asarray(frame.convert('L').filter(ImageFilter.GaussianBlur(self.cell)), np.float32) / 255
        # Source luminance always shades unselected glyphs. Structure adds local
        # contrast without lifting black surfaces to a uniform emissive floor.
        gain = luma * np.clip(1 + 2 * self.style.material_structure * (luma - broad), .5, 1.5)
        y, x = np.mgrid[:self.size[1], :self.size[0]].astype(np.float32)
        emission = np.zeros((*x.shape, 3), np.float32)
        selected_coverage = np.zeros(x.shape, np.float32) if self.style.material_edge_shade else None
        for ordinal, (subject, weight) in enumerate(visible_ownership(subjects, self.size)):
            visible = weight > 0
            if not np.any(visible):
                continue
            if subject is None:
                material = self.material
                u, v = self.mapper.environment(x, y)
                u, v = (u / self.pitch).astype(np.float32), (v / self.cell).astype(np.float32)
                footprint = np.maximum(np.hypot(*np.gradient(u)) / max(1., material.density),
                                       np.hypot(*np.gradient(v)))[visible]
                u, v = u[visible], v[visible]
                local_gain = gain[visible] * self.style.material_background
                if selected_coverage is not None and np.any(selected_coverage):
                    # Background is yielded last. Use visible selected coverage
                    # so hidden people cannot cast halos through their occluders.
                    nearby = np.minimum(1., 2 * blurred_coverage(selected_coverage, self.outer_edge_radius))
                    local_gain *= 1 - self.style.material_edge_shade * nearby[visible]
            else:
                begun = clock.perf_counter()
                material = self.subject_material(subject, ordinal)
                material.field(time)
                duration = clock.perf_counter() - begun
                generation_seconds += duration
                self.material_seconds += duration
                pitch = self.cell / max(1., material.density)
                u, v = x[visible] / pitch, y[visible] / self.cell
                footprint = np.full_like(u, 1 / self.cell)
                highlighted = material_subjects is None or subject.track_id in material_subjects
                if highlighted and selected_coverage is not None:
                    selected_coverage += weight
                local_gain = (np.maximum(gain[visible], .8) * self.style.material_foreground if highlighted
                              else gain[visible] * self.style.material_background)
            # Composite opaque silhouette ownership before the optical glow.
            # Dark gaps in its independent rain cannot reveal background cores.
            sample = material.sample(u, v, time, footprint)
            light = shade(sample, local_gain)
            if subject is not None and highlighted and self.style.material_edge_glow:
                alpha = resized_mask(subject.mask, self.size)
                inner = np.clip(2 * (alpha - blurred_coverage(alpha, self.inner_edge_radius)), 0, 1)
                strength = self.style.material_edge_glow * self.style.material_foreground / 2.1
                light += (inner[visible] * strength)[:, None] * np.array([.12, 1., .36], np.float32)
            # Ownership clips both rain and its rim before the optical glow.
            emission[visible] += light * weight[visible, None]
        if self.style.material_glow:
            # Blur quantized linear emission before the final display transform.
            glow = np.stack([np.asarray(Image.fromarray(np.uint8(np.clip(emission[..., c], 0, 2) * 127.5))
                                       .filter(ImageFilter.GaussianBlur(max(.6, self.cell * .16))), np.float32) / 127.5
                             for c in range(3)], axis=-1)
            emission += glow * self.style.material_glow
        image = Image.fromarray(np.uint8(np.rint(linear_to_srgb(emission) * 255)))
        self.frames += 1
        mapping_seconds = clock.perf_counter() - started - (generation_seconds - background_generation_seconds)
        self.mapping_seconds += mapping_seconds
        self.frame_seconds.append(generation_seconds + mapping_seconds)
        return image
