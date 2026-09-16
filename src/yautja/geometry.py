"""Seeded lattice artwork and independent target ornaments and captions."""
import math
from .masks import subject_binary
from functools import lru_cache

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .signal import stable_number
from .aim import Aim
from .hologram import weak_spot_ink

GEO_OPTIONS = ('geo_grid', 'geo_grid_scale', 'geo_grid_jitter', 'geo_grid_speed', 'geo_grid_projection',
               'geo_grid_center_fade', 'geo_grid_width', 'geo_grid_breaks', 'geo_grid_details', 'geo_grid_rotation')
TARGET_OPTIONS = ('target_mode', 'target_motif', 'target_motif_count', 'target_motif_scale', 'target_label',
                  'target_motion', 'target_hold', 'target_response', 'target_fill', 'target_outline',
                  'target_label_scale', 'target_cursor', 'target_motif_speed', 'target_motif_breaks', 'target_weak_spots')
GEOMETRY_ELEMENTS = ('geo-grid', 'target-motif', 'target-label', 'target-outline', 'target-weak-spots')


def noise(seed, time):
    index = math.floor(time)
    fraction = time - index
    blend = fraction * fraction * (3 - 2 * fraction)
    a, b = ((stable_number(seed, 'value', n) % 65536) / 65535 for n in (index, index + 1))
    return a + (b - a) * blend


def smoothstep(value):
    value = np.clip(value, 0, 1)
    return value * value * (3 - 2 * value)


@lru_cache(maxsize=8192)
def break_intervals(seed, amount):
    """Time-invariant gaps in edge parameter space, shared by rotating paths."""
    if not amount:
        return ((0., 1.),)
    rng = np.random.default_rng(seed)
    gaps = sorted((center, rng.uniform(.035, .13) * amount)
                  for center in rng.uniform(.10, .90, int(rng.integers(2, 5))))
    intervals, start = [], 0.
    for center, width in gaps:
        left, right = max(0., center-width/2), min(1., center+width/2)
        if left > start:
            intervals.append((start, left))
        start = max(start, right)
    if start < 1:
        intervals.append((start, 1.))
    return tuple(intervals)


def broken_path(points, seed, amount, *, parameterized=False):
    """Stable unequal gaps, optionally attached to a reprojected 3D edge."""
    points = np.asarray(points, float)
    if not np.isfinite(points).all():
        return []
    if not amount:
        return [points]
    distance = np.r_[0., np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    if distance[-1] < 1e-8:
        return []
    distance = np.linspace(0, 1, len(points)) if parameterized else distance / distance[-1]
    return [np.column_stack([np.interp(np.r_[a, distance[(distance>a)&(distance<b)], b], distance, points[:,axis])
                             for axis in (0,1)]) for a,b in break_intervals(seed, amount)]


class GeometryStyle:
    def __init__(self, *, geo_grid=False, geo_grid_scale=160., geo_grid_jitter=.65, geo_grid_speed=1.,
                 geo_grid_projection='flat', target_mode='selected', target_motif='none', target_motif_count=7,
                 target_motif_scale=1., target_label=None, target_motion='acquire', target_hold=3.,
                 target_response=.6, target_fill='auto', target_outline=False, target_label_scale=1., target_cursor=False,
                 geo_grid_center_fade=0., geo_grid_width=1.3, geo_grid_breaks=0.,
                 target_motif_speed=1., target_motif_breaks=0., geo_grid_details=False, target_weak_spots=False,
                 geo_grid_rotation=0.):
        for key, value, choices in (
                ('target-mode', target_mode, ('selected', 'auto', 'cycle')),
                ('target-motion', target_motion, ('acquire', 'persistent')),
                ('target-fill', target_fill, ('auto', 'filled', 'stroked')),
                ('geo-grid-projection', geo_grid_projection, ('flat', 'sphere'))):
            if value not in choices:
                raise ValueError(f'--{key} must be one of: {", ".join(choices)}')
        if target_motif not in ('none', 'triangles'):
            raise ValueError('--target-motif must be none or triangles')
        if type(target_motif_count) is not int or not 0 <= target_motif_count <= 24:
            raise ValueError('--target-motif-count must be an integer between 0 and 24')
        if target_label is not None and (not isinstance(target_label, str) or not 1 <= len(target_label) <= 24 or
                                         any(not 32 <= ord(c) <= 126 for c in target_label) or not target_label.strip()):
            raise ValueError('--target-label must contain 1-24 printable ASCII characters')
        for key, value, low, high in (('geo-grid-scale', geo_grid_scale, 40, 480),
                                    ('geo-grid-jitter', geo_grid_jitter, 0, 1), ('geo-grid-speed', geo_grid_speed, 0, 5),
                                    ('geo-grid-rotation', geo_grid_rotation, -10, 10),
                                    ('target-motif-scale', target_motif_scale, .25, 3),
                                    ('target-hold', target_hold, .5, 30), ('target-response', target_response, 0, 3),
                                    ('target-label-scale', target_label_scale, .5, 4),
                                    ('geo-grid-center-fade', geo_grid_center_fade, 0, 1),
                                    ('geo-grid-width', geo_grid_width, .5, 6), ('geo-grid-breaks', geo_grid_breaks, 0, 1),
                                    ('target-motif-speed', target_motif_speed, 0, 5),
                                    ('target-motif-breaks', target_motif_breaks, 0, 1)):
            if not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f'--{key} must be between {low} and {high}')
        for key in (*GEO_OPTIONS, *TARGET_OPTIONS):
            setattr(self, key, locals()[key])
        self.geometry = None
        self.sphere_cache = self.flat_cache = None
        self.curves = None
        self.grid_paths = self.grid_paths_key = None
        self.grid_fade = self.grid_fade_key = None
        self.accents = self.accents_key = None
        self.label_box = None
        self.aim = Aim(target_hold, target_response)
        self.selected = []
        self.automatic = False
        self.motif_anchors = {}
        self.motif_time = self.motif_shot = None

    def report(self, hud=True):
        return {**{key: getattr(self, key) for key in (*GEO_OPTIONS, *TARGET_OPTIONS)},
                'geo_grid': bool(hud and self.geo_grid), 'target_outline': bool(hud and self.target_outline),
                'target_weak_spots': bool(hud and self.target_weak_spots)}

    def lattice(self, size, seed, time=0., static=False):
        rotating = bool(self.geo_grid_rotation and not static)
        angle = math.radians(self.geo_grid_rotation * time % 360) if rotating else 0.
        base = (size, seed, self.geo_grid_projection, self.geo_grid_scale, self.geo_grid_jitter, rotating)
        signature = (*base, angle)
        if self.geometry and self.geometry[0] == signature:
            return self.geometry[1:]
        if self.geo_grid_projection == 'sphere':
            return self.sphere_lattice(size, seed, signature, angle, rotating)
        self.curves = None
        if self.flat_cache is not None and self.flat_cache[0] == base:
            _, original, edges, nodes = self.flat_cache
            matrix = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])
            vertices = (original-np.array(size)/2) @ matrix + np.array(size)/2 if rotating else original
            self.geometry = (signature, vertices, edges, nodes)
            return vertices, edges, nodes
        width, height = size
        spacing = self.geo_grid_scale * min(size) / 1080
        dy = spacing * math.sqrt(3) / 2
        rng = np.random.default_rng(stable_number(seed, 'geo-grid'))
        vertices, indices = [], {}
        radius = np.linalg.norm(size)/2 + spacing
        row_start, row_end = (math.floor((height/2-radius)/dy), math.ceil((height/2+radius)/dy)) if rotating else (-2, math.ceil(height/dy)+2)
        col_start, col_end = (math.floor((width/2-radius)/spacing), math.ceil((width/2+radius)/spacing)) if rotating else (-2, math.ceil(width/spacing)+2)
        for row in range(row_start, row_end):
            for col in range(col_start, col_end):
                angle, length = rng.uniform(0, math.tau), math.sqrt(rng.random()) * .32 * spacing * self.geo_grid_jitter
                indices[row, col] = len(vertices)
                vertices.append((col * spacing + (row % 2) * spacing / 2 + math.cos(angle) * length,
                                 row * dy + math.sin(angle) * length))
        edges = []
        for (row, col), i in indices.items():
            for neighbor in ((row, col + 1), (row + 1, col), (row + 1, col + (1 if row % 2 else -1))):
                if neighbor in indices:
                    edges.append((i, indices[neighbor]))
        nodes = [i for i in range(len(vertices)) if rng.random() < .3]
        self.flat_cache = (base, np.asarray(vertices), edges, nodes)
        return self.lattice(size, seed, time, static)

    def sphere_lattice(self, size, seed, signature, angle=0., rotating=False):
        key = (seed, self.geo_grid_scale, self.geo_grid_jitter)
        if self.sphere_cache is not None and self.sphere_cache[0] == key:
            _, vectors, faces, depth, state = self.sphere_cache
            rng = np.random.default_rng()
            rng.bit_generator.state = state
            return self.project_sphere(size, signature, vectors, faces, depth, rng, angle, rotating)
        # Subdivide an icosahedron on the unit sphere. Project its shared vertices
        # and join them with straight edges, so triangular facets imply curvature.
        phi = (1 + math.sqrt(5)) / 2
        vertices = np.array([(-1,phi,0),(1,phi,0),(-1,-phi,0),(1,-phi,0),
                             (0,-1,phi),(0,1,phi),(0,-1,-phi),(0,1,-phi),
                             (phi,0,-1),(phi,0,1),(-phi,0,-1),(-phi,0,1)], dtype=float)
        vertices /= np.linalg.norm(vertices, axis=1)[:, None]
        faces = [(0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),(1,5,9),(5,11,4),
                 (11,10,2),(10,7,6),(7,1,8),(3,9,4),(3,4,2),(3,2,6),(3,6,8),
                 (3,8,9),(4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1)]
        depth = max(1, min(4, int(math.log2(1080 / self.geo_grid_scale))))
        vertices = list(vertices)
        for _ in range(depth):
            midpoints, divided = {}, []
            def midpoint(a, b):
                key = tuple(sorted((a, b)))
                if key not in midpoints:
                    point = vertices[a] + vertices[b]
                    midpoints[key] = len(vertices)
                    vertices.append(point / np.linalg.norm(point))
                return midpoints[key]
            for a, b, c in faces:
                ab, bc, ca = midpoint(a,b), midpoint(b,c), midpoint(c,a)
                divided.extend(((a,ab,ca),(b,bc,ab),(c,ca,bc),(ab,bc,ca)))
            faces = divided
        vectors = np.asarray(vertices)
        rng = np.random.default_rng(stable_number(seed, 'sphere-grid'))
        vectors += rng.normal(0, .16 / 2**depth * self.geo_grid_jitter, vectors.shape)
        vectors /= np.linalg.norm(vectors, axis=1)[:, None]
        self.sphere_cache = (key, vectors, faces, depth, rng.bit_generator.state)
        return self.project_sphere(size, signature, vectors, faces, depth, rng, angle, rotating)

    def project_sphere(self, size, signature, vectors, faces, depth, rng, angle, rotating):
        if angle:
            axis = np.array([.18, 1., .12])
            axis /= np.linalg.norm(axis)
            x, y, z = axis
            cross = np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
            matrix = np.eye(3)*math.cos(angle) + (1-math.cos(angle))*np.outer(axis,axis) + math.sin(angle)*cross
            vectors = vectors @ matrix
        # Tilt avoids a pole or a conspicuous horizontal seam in the viewport.
        ax, ay = .31, .47
        vectors = vectors @ np.array([[math.cos(ay),0,math.sin(ay)],[0,1,0],[-math.sin(ay),0,math.cos(ay)]])
        vectors = vectors @ np.array([[1,0,0],[0,math.cos(ax),-math.sin(ax)],[0,math.sin(ax),math.cos(ax)]])
        focal = min(size) * .72 * self.geo_grid_scale / (640 / 2**depth)
        def project(points):
            return points[:, :2] / np.maximum(.02, 1 + points[:, 2:]) * focal + np.array(size) / 2
        corner_radius = np.linalg.norm(size) / 2 + min(size) * .1
        near_limit = min(-.65, max(-.99, (focal**2 - corner_radius**2) / (focal**2 + corner_radius**2) - .1))
        edges = sorted({tuple(sorted((a,b))) for face in faces for a,b in zip(face, (*face[1:],face[0]))
                        if rotating or min(vectors[a,2], vectors[b,2]) > near_limit})
        vertices = project(vectors)
        # Keep complete edge IDs during rotation, including hidden edges. The
        # breaks and satellite dots follow the same straight segment as its ink.
        self.curves = [vertices[[a,b]] if not rotating or min(vectors[a,2], vectors[b,2]) > near_limit
                       else np.full((2,2), np.nan) for a,b in edges]
        nodes = [i for i in range(len(vertices)) if (rotating or vectors[i,2] > near_limit) and rng.random() < .45]
        if rotating:
            vertices[vectors[:,2] <= near_limit] = np.nan
        self.geometry = (signature, vertices, edges, nodes)
        return vertices, edges, nodes

    def grid_accents(self, size, seed, time, static=False):
        """Seeded node rings and satellites breathing along incident mesh edges."""
        vertices, edges, nodes = self.lattice(size, seed, time, static)
        if self.accents_key != self.geometry[0][:-1]:
            neighbors = {i: [] for i in nodes}
            for index, (a, b) in enumerate(edges):
                for node, curve in ((a, (index, False)), (b, (index, True))):
                    if node in neighbors:
                        neighbors[node].append(curve)
            self.accents = []
            for node, curves in neighbors.items():
                rng = np.random.default_rng(stable_number(seed, 'grid-accents', node))
                self.accents.append((node, curves, rng.random() < .28, rng.uniform(0, math.tau),
                                     rng.uniform(2.4, 4.8), rng.uniform(8, 14)))
            self.accents_key = self.geometry[0][:-1]
        t = 0 if static else time * self.geo_grid_speed
        scale = min(size) / 1080
        for node, curves, ring, phase, period, radius in self.accents:
            center = vertices[node]
            if not (-30 <= center[0] <= size[0]+30 and -30 <= center[1] <= size[1]+30):
                continue
            breath = .5 - .5 * math.cos(t * math.tau / period + phase)
            points = [center + max(2., radius * scale) * np.array([math.cos(a), math.sin(a)])
                      for a in np.arange(7) * math.tau / 7 + phase] if ring else []
            dots = []
            for index, reverse in curves:
                a, b = edges[index]
                curve = self.curves[index] if self.curves is not None else np.array([vertices[a], vertices[b]])
                if reverse:
                    curve = curve[::-1]
                if not np.isfinite(curve).all():
                    continue
                distance = np.r_[0., np.cumsum(np.linalg.norm(np.diff(curve, axis=0), axis=1))]
                length = distance[-1]
                if length < 1:
                    continue
                reach = min(length * .27, 74 * scale) * (.27 + .73 * breath)
                for fraction in (.45, .72, 1.):
                    offset = max(2 * scale, reach * fraction)
                    dots.append(tuple(np.interp(offset, distance, curve[:, axis]) for axis in (0, 1)))
            yield {'node': node, 'ring': points, 'dots': dots, 'brightness': .6 + .4 * breath}

    def draw_grid(self, renderer, image, time, static=False, *, clearance=None):
        if not self.geo_grid:
            return
        vertices, edges, nodes = self.lattice(image.size, renderer.seed, time, static)
        ss, scale = 3, min(image.size) / 1080
        ink = Image.new('RGBA', (image.width * ss, image.height * ss))
        draw = ImageDraw.Draw(ink)
        color = renderer.hud_colors['geo-grid']
        t = 0 if static else time * self.geo_grid_speed
        key = (self.geometry[0], self.geo_grid_breaks)
        if self.grid_paths_key != key:
            self.grid_paths = [broken_path(self.curves[index] if self.curves is not None else (vertices[a],vertices[b]),
                                           stable_number(renderer.seed, 'grid-gaps', index), self.geo_grid_breaks,
                                           parameterized=bool(self.geo_grid_rotation and not static))
                               for index,(a,b) in enumerate(edges)]
            self.grid_paths_key = key
        for index, paths in enumerate(self.grid_paths):
            alpha = round(255 * (.45 + .55 * noise(stable_number(renderer.seed, 'grid-edge', index), t)))
            for points in paths:
                draw.line([tuple(v * ss for v in point) for point in points],
                          fill=(*color, alpha), width=max(1, round(self.geo_grid_width * scale * ss)))
        radius = max(.8, 2.2 * scale) * ss
        for i in nodes:
            if not np.isfinite(vertices[i]).all():
                continue
            x, y = (v * ss for v in vertices[i])
            draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(*color, 230))
        if self.geo_grid_details:
            accent_color = tuple(round(c + (255-c) * .55) for c in color) if max(color) else color
            for accent in self.grid_accents(image.size, renderer.seed, time, static):
                if accent['ring']:
                    points = [tuple(p * ss) for p in accent['ring']]
                    draw.line(points + points[:1], fill=(*accent_color, 215),
                              width=max(1, round(1.6 * scale * ss)), joint='curve')
                for x, y in accent['dots']:
                    r = max(.5, 1.35 * scale) * ss
                    draw.ellipse((x*ss-r, y*ss-r, x*ss+r, y*ss+r),
                                 fill=(*accent_color, round(240 * accent['brightness'])))
        panel = renderer.hud_panel(image.size, 'geo-grid')
        ink = ink.resize(image.size, Image.Resampling.LANCZOS)
        if self.geo_grid_center_fade:
            key = (image.size, self.geo_grid_center_fade)
            if self.grid_fade_key != key:
                x = (np.arange(image.width) + .5 - image.width/2) / (image.width/2)
                y = (np.arange(image.height) + .5 - image.height/2) / (image.height/2)
                fade = smoothstep((np.hypot(x[None,:], y[:,None]) - .12) / .88)
                self.grid_fade = Image.fromarray(np.uint8(255 * (1 - self.geo_grid_center_fade * (1-fade))))
                self.grid_fade_key = key
            ink.putalpha(ImageChops.multiply(ink.getchannel('A'), self.grid_fade))
        panel.replace('geo-grid', ink)
        before = image.copy() if clearance is not None else None
        renderer.composite_panel(image, panel, 0, 0)
        if before is not None:
            # Fade the complete grid emission, including neon halos. Masking
            # the ink first would change neon normalization elsewhere too.
            image.paste(before, (0, 0), clearance)

    def motif_particles(self, seed, identity, time, static=False):
        """Ornaments emerge at their anchor, rise, then collapse and spin away."""
        rng = np.random.default_rng(stable_number(seed, 'motifs', identity))
        t = 0 if static else time * self.target_motif_speed
        for i in range(self.target_motif_count):
            angle, distance = rng.uniform(0, math.tau), rng.uniform(1.1, 2.3)
            radius, direction = rng.uniform(.16, .45), (1 if rng.random() < .7 else -1)
            nested, lifetime, offset = rng.random() < .25, rng.uniform(2.8, 4.4), rng.uniform(.15, .75)
            phase = (t / lifetime + offset) % 1
            collapse = float(smoothstep((phase - .66) / .34))
            alpha = float(smoothstep(phase / .12) * (1 - smoothstep((phase - .80) / .20)))
            yield {'index': i, 'x': math.cos(angle) * distance * .25 * phase * self.target_motif_scale,
                   'y': -phase * self.target_motif_scale,
                   'radius': radius * self.target_motif_scale * (1-collapse)**1.2,
                   'rotation': (0 if direction == 1 else math.pi) + direction * math.tau * 1.15 * collapse**1.6,
                   'nested': nested, 'collapse': collapse, 'alpha': alpha, 'phase': phase, 'lifetime': lifetime}

    def targets(self, subjects):
        result = []
        for subject in subjects:
            yy, xx = np.nonzero(np.asarray(subject_binary(subject)))
            if subject.opacity <= 0 or not len(xx):
                continue
            h, w = subject.mask.shape
            result.append({'id': f'auto-{subject.track_id}', 'track_id': subject.track_id, 'bbox': (xx.min()/w, yy.min()/h,
                          (xx.max()+1)/w, (yy.max()+1)/h), 'opacity': subject.opacity})
        return result

    def prepare_targets(self, subjects, targets, time, shot, size, static=False):
        if shot != self.motif_shot or self.motif_time is None or not 0 < time-self.motif_time <= .5:
            self.motif_anchors.clear()
        dt = time-self.motif_time if self.motif_time is not None else 0
        self.motif_time, self.motif_shot = time, shot
        anchors = {}
        for subject in subjects if self.target_motif != 'none' else ():
            yy, xx = np.nonzero(np.asarray(subject_binary(subject, size)))
            if not len(xx) or subject.opacity <= 0:
                continue
            current = np.array([xx.mean(), yy.mean()])
            previous = self.motif_anchors.get(subject.track_id)
            if previous is not None and np.linalg.norm(current-previous) < min(size)*.15:
                current = previous + (current-previous) * (1-math.exp(-dt/.09))
            anchors[subject.track_id] = current
        self.motif_anchors = anchors
        automatic = targets is None and self.target_mode != 'selected'
        self.automatic = automatic
        candidates = self.targets(subjects) if automatic else list(targets or ())
        threshold = .25 if self.target_mode == 'cycle' or self.target_motion == 'persistent' else 0
        candidates = [item for item in candidates if item.get('opacity', 1) > threshold]
        if self.target_mode == 'cycle' or self.target_motion == 'persistent':
            selected = self.aim.select(candidates, time, shot, static)
            self.selected = [selected] if selected else []
            if self.target_motion == 'persistent' and (automatic or candidates):
                return [self.aim.advance(selected, time, shot, size, static)]
            return self.selected
        self.selected = candidates
        return candidates

    def selected_subjects(self, subjects):
        """Resolve explicit catalog boxes as well as automatic tracking IDs."""
        available = self.targets(subjects)
        chosen = set()
        for target in self.selected:
            if 'track_id' in target:
                chosen.add(target['track_id'])
                continue
            def overlap(candidate):
                a, b = target['bbox'], candidate['bbox']
                intersection = max(0, min(a[2],b[2])-max(a[0],b[0])) * max(0, min(a[3],b[3])-max(a[1],b[1]))
                union = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - intersection
                return intersection / max(union, 1e-9)
            match = max(available, key=overlap, default=None)
            if match and overlap(match) > .15:
                chosen.add(match['track_id'])
        return [subject for subject in subjects if subject.track_id in chosen and subject.opacity > 0]

    def draw_weak_spots(self, renderer, image, subjects, time, shot, static=False):
        if not self.target_weak_spots or not self.selected:
            return
        panel = renderer.hud_panel(image.size, 'target-weak-spots')
        for subject in self.selected_subjects(subjects):
            mask = subject_binary(subject, image.size)
            bounds = mask.getbbox()
            if bounds is None:
                continue
            ink = weak_spot_ink(mask.crop(bounds), renderer.hud_colors['target-weak-spots'],
                                0 if static else time, stable_number(renderer.seed, 'weak-spots', shot, subject.track_id), shine=renderer.signal.outline_shine)
            ink.putalpha(ink.getchannel('A').point(lambda v: round(v * min(1., subject.opacity))))
            panel.layer('target-weak-spots').alpha_composite(ink, bounds[:2])
        renderer.composite_panel(image, panel, 0, 0)

    def draw_outline(self, renderer, image, subjects):
        if not self.target_outline or not self.selected:
            return
        panel = renderer.hud_panel(image.size, 'target-outline')
        for subject in self.selected_subjects(subjects):
            mask = subject_binary(subject, image.size)
            width = max(1, round(3 * min(image.size) / 1080))
            inner = mask.filter(ImageFilter.MinFilter(width * 2 + 1))
            edge = np.maximum(0, np.asarray(mask, dtype=np.int16) - np.asarray(inner, dtype=np.int16))
            ink = Image.new('RGBA', image.size, (*renderer.hud_colors['target-outline'], 0))
            ink.putalpha(Image.fromarray(np.uint8(edge * subject.opacity)))
            panel.layer('target-outline').alpha_composite(ink)
        renderer.composite_panel(image, panel, 0, 0)

    def draw_targets(self, renderer, image, time, static=False, subjects=()):
        states = renderer.target_overlay.placements
        self.label_box = None
        if not states or (self.target_motif == 'none' and self.target_label is None):
            return
        panel = renderer.hud_panel(image.size, 'target-motif', 'target-label')
        scale = min(image.size) / 1080
        if self.target_motif == 'triangles' and self.target_motif_count:
            ss = 2
            ink = Image.new('RGBA', (image.width * ss, image.height * ss))
            draw = ImageDraw.Draw(ink)
            color = renderer.hud_colors['target-motif']
            attached = []
            for subject in self.selected_subjects(subjects):
                yy, xx = np.nonzero(np.asarray(subject_binary(subject, image.size)))
                if len(xx):
                    attached.append((subject, xx, yy))
            # Searching in automatic mode has no selected figure to ornament.
            # Explicit maskless targets retain the original reticle fallback.
            motif_states = [] if attached or self.automatic else list(states)
            for subject, xx, yy in attached:
                center = self.motif_anchors[subject.track_id]
                motif_states.append((f'subject-{subject.track_id}', *center, (xx.max()-xx.min()+1)*.28, subject.opacity))
            figures = {f'subject-{s.track_id}': (s, xx, yy) for s, xx, yy in attached}
            for identity, cx, cy, radius, opacity in motif_states:
                for part in self.motif_particles(renderer.seed, identity, time, static):
                    x, y = cx + radius * part['x'], cy + radius * 3 * part['y']
                    if identity in figures:
                        subject, xx, yy = figures[identity]
                        # Spawn below the selected silhouette's center of mass.
                        # Height, rather than width or a held prop, sets the rise.
                        bh = yy.max()-yy.min()+1
                        y = cy + bh * (.18 + .45 * part['y'])
                    r = radius * part['radius']
                    alpha = round(255 * opacity * part['alpha'])
                    if r < .25 or not alpha:
                        continue
                    for multiplier in ((1, .55) if part['nested'] else (1,)):
                        points = np.array([(r * multiplier * math.cos(a + part['rotation']),
                                            r * multiplier * math.sin(a + part['rotation']))
                                           for a in (math.pi/2, math.pi/2+math.tau/3, math.pi/2+2*math.tau/3)])
                        for edge, (a,b) in enumerate(zip(points, np.roll(points,-1,axis=0))):
                            middle = (a+b)/2 * (1-part['collapse'])
                            for path in broken_path(np.array([a,middle,b]) + (x,y),
                                                    stable_number(renderer.seed, identity, part['index'], edge),
                                                    self.target_motif_breaks):
                                draw.line([tuple(v * ss for v in p) for p in path], fill=(*color, alpha),
                                          width=max(2, round(2 * scale * ss)), joint='curve')
            panel.replace('target-motif', ink.resize(image.size, Image.Resampling.LANCZOS))
        if self.target_label is not None:
            opacity = max(state[-1] for state in states)
            margin = max(2, round(42 * scale))
            # Reserve the cursor's width even while it is dark, keeping the
            # caption at a fixed size and position throughout its blink cycle.
            font_size = max(6, round(26 * scale * self.target_label_scale))
            ink = renderer.typography.mask(self.target_label, font_size, .12)
            if self.target_cursor:
                cursor_width, gap = max(3, round(font_size * .65)), max(2, round(font_size * .3))
                caption = ink
                ink = Image.new('L', (caption.width + gap + cursor_width, caption.height + max(1, round(font_size * .15))))
                ink.paste(caption, (0, 0))
                if static or int(time * 2) % 2 == 0:
                    ImageDraw.Draw(ink).line((caption.width + gap, ink.height-1, ink.width-1, ink.height-1),
                                            fill=255, width=max(1, round(font_size * .12)))
            max_width = max(1, image.width - 2 * margin)
            if ink.width > max_width:
                ink = ink.resize((max_width, max(1, round(ink.height * max_width / ink.width))), Image.Resampling.LANCZOS)
            y = max(margin, min(image.height - margin - ink.height, round(image.height - 64 * scale - ink.height)))
            layer = Image.new('RGBA', ink.size, (*renderer.hud_colors['target-label'], 0))
            layer.putalpha(ink.point(lambda v: round(v * opacity)))
            panel.layer('target-label').paste(layer, (margin, y))
            self.label_box = (margin, y, margin + ink.width, y + ink.height)
        renderer.composite_panel(image, panel, 0, 0)
