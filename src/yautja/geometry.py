"""Seeded lattice artwork and independent target ornaments and captions."""
import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .signal import stable_number
from .aim import Aim
from .hologram import weak_spot_ink

GEO_OPTIONS = ('geo_grid', 'geo_grid_scale', 'geo_grid_jitter', 'geo_grid_speed', 'geo_grid_projection',
               'geo_grid_center_fade', 'geo_grid_width', 'geo_grid_breaks', 'geo_grid_details')
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


def broken_path(points, seed, amount):
    """Stable, unequal gaps measured along a straight or curved polyline."""
    points = np.asarray(points, float)
    if not amount:
        return [points]
    distance = np.r_[0., np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    if distance[-1] < 1e-8:
        return []
    distance /= distance[-1]
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
    return [np.column_stack([np.interp(np.r_[a, distance[(distance>a)&(distance<b)], b], distance, points[:,axis])
                             for axis in (0,1)]) for a,b in intervals]


class GeometryStyle:
    def __init__(self, *, geo_grid=False, geo_grid_scale=160., geo_grid_jitter=.65, geo_grid_speed=1.,
                 geo_grid_projection='flat', target_mode='selected', target_motif='none', target_motif_count=7,
                 target_motif_scale=1., target_label=None, target_motion='acquire', target_hold=3.,
                 target_response=.6, target_fill='auto', target_outline=False, target_label_scale=1., target_cursor=False,
                 geo_grid_center_fade=0., geo_grid_width=1.3, geo_grid_breaks=0.,
                 target_motif_speed=1., target_motif_breaks=0., geo_grid_details=False, target_weak_spots=False):
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
        self.curves = None
        self.grid_paths = self.grid_paths_key = None
        self.grid_fade = self.grid_fade_key = None
        self.accents = self.accents_key = None
        self.label_box = None
        self.aim = Aim(target_hold, target_response)
        self.selected = []

    def report(self, hud=True):
        return {**{key: getattr(self, key) for key in (*GEO_OPTIONS, *TARGET_OPTIONS)},
                'geo_grid': bool(hud and self.geo_grid), 'target_outline': bool(hud and self.target_outline),
                'target_weak_spots': bool(hud and self.target_weak_spots)}

    def lattice(self, size, seed):
        signature = (size, seed, self.geo_grid_projection, self.geo_grid_scale, self.geo_grid_jitter)
        if self.geometry and self.geometry[0] == signature:
            return self.geometry[1:]
        if self.geo_grid_projection == 'sphere':
            return self.sphere_lattice(size, seed, signature)
        self.curves = None
        width, height = size
        spacing = self.geo_grid_scale * min(size) / 1080
        dy = spacing * math.sqrt(3) / 2
        rng = np.random.default_rng(stable_number(seed, 'geo-grid'))
        vertices, indices = [], {}
        for row in range(-2, math.ceil(height / dy) + 2):
            for col in range(-2, math.ceil(width / spacing) + 2):
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
        self.geometry = (signature, vertices, edges, nodes)
        return vertices, edges, nodes

    def sphere_lattice(self, size, seed, signature):
        # Subdivide an icosahedron on the unit sphere. Stereographic projection
        # from its center makes great-circle edges bow across a wide field of view.
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
                        if min(vectors[a,2], vectors[b,2]) > near_limit})
        self.curves = []
        for a, b in edges:
            t = np.linspace(0, 1, 9)[:, None]
            arc = vectors[a] * (1-t) + vectors[b] * t
            arc /= np.linalg.norm(arc, axis=1)[:, None]
            self.curves.append(project(arc))
        vertices = project(vectors)
        nodes = [i for i in range(len(vertices)) if vectors[i,2] > near_limit and rng.random() < .45]
        self.geometry = (signature, vertices, edges, nodes)
        return vertices, edges, nodes

    def grid_accents(self, size, seed, time, static=False):
        """Seeded node rings and satellites breathing along incident sphere arcs."""
        vertices, edges, nodes = self.lattice(size, seed)
        if self.accents_key != self.geometry[0]:
            neighbors = {i: [] for i in nodes}
            for index, (a, b) in enumerate(edges):
                path = self.curves[index] if self.curves is not None else np.array([vertices[a], vertices[b]])
                for node, curve in ((a, path), (b, path[::-1])):
                    if node in neighbors:
                        neighbors[node].append(curve)
            self.accents = []
            for node, curves in neighbors.items():
                rng = np.random.default_rng(stable_number(seed, 'grid-accents', node))
                self.accents.append((node, curves, rng.random() < .28, rng.uniform(0, math.tau),
                                     rng.uniform(2.4, 4.8), rng.uniform(8, 14)))
            self.accents_key = self.geometry[0]
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
            for curve in curves:
                distance = np.r_[0., np.cumsum(np.linalg.norm(np.diff(curve, axis=0), axis=1))]
                length = distance[-1]
                if length < 1:
                    continue
                reach = min(length * .27, 74 * scale) * (.27 + .73 * breath)
                for fraction in (.45, .72, 1.):
                    offset = max(2 * scale, reach * fraction)
                    dots.append(tuple(np.interp(offset, distance, curve[:, axis]) for axis in (0, 1)))
            yield {'node': node, 'ring': points, 'dots': dots, 'brightness': .6 + .4 * breath}

    def draw_grid(self, renderer, image, time, static=False):
        if not self.geo_grid:
            return
        vertices, edges, nodes = self.lattice(image.size, renderer.seed)
        ss, scale = 3, min(image.size) / 1080
        ink = Image.new('RGBA', (image.width * ss, image.height * ss))
        draw = ImageDraw.Draw(ink)
        color = renderer.hud_colors['geo-grid']
        t = 0 if static else time * self.geo_grid_speed
        key = (self.geometry[0], self.geo_grid_breaks)
        if self.grid_paths_key != key:
            self.grid_paths = [broken_path(self.curves[index] if self.curves is not None else (vertices[a],vertices[b]),
                                           stable_number(renderer.seed, 'grid-gaps', index), self.geo_grid_breaks)
                               for index,(a,b) in enumerate(edges)]
            self.grid_paths_key = key
        for index, paths in enumerate(self.grid_paths):
            alpha = round(255 * (.45 + .55 * noise(stable_number(renderer.seed, 'grid-edge', index), t)))
            for points in paths:
                draw.line([tuple(v * ss for v in point) for point in points],
                          fill=(*color, alpha), width=max(1, round(self.geo_grid_width * scale * ss)))
        radius = max(.8, 2.2 * scale) * ss
        for i in nodes:
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
        renderer.composite_panel(image, panel, 0, 0)

    def motif_particles(self, seed, identity, time, static=False):
        """Local ornaments rise, then collapse and spin away before respawning."""
        rng = np.random.default_rng(stable_number(seed, 'motifs', identity))
        t = 0 if static else time * self.target_motif_speed
        for i in range(self.target_motif_count):
            angle, distance = rng.uniform(0, math.tau), rng.uniform(1.1, 2.3)
            radius, direction = rng.uniform(.16, .45), (1 if rng.random() < .7 else -1)
            nested, lifetime, offset = rng.random() < .25, rng.uniform(2.8, 4.4), rng.uniform(.15, .75)
            phase = (t / lifetime + offset) % 1
            collapse = float(smoothstep((phase - .66) / .34))
            alpha = float(smoothstep(phase / .12) * (1 - smoothstep((phase - .80) / .20)))
            yield {'index': i, 'x': math.cos(angle) * distance * self.target_motif_scale,
                   'y': (math.sin(angle) * distance * 1.2 - .4 - phase * .7) * self.target_motif_scale,
                   'radius': radius * self.target_motif_scale * (1-collapse)**1.2,
                   'rotation': (0 if direction == 1 else math.pi) + direction * math.tau * 1.15 * collapse**1.6,
                   'nested': nested, 'collapse': collapse, 'alpha': alpha, 'phase': phase, 'lifetime': lifetime}

    def targets(self, subjects):
        result = []
        for subject in subjects:
            yy, xx = np.nonzero(subject.mask >= .5)
            if subject.opacity <= 0 or not len(xx):
                continue
            h, w = subject.mask.shape
            result.append({'id': f'auto-{subject.track_id}', 'track_id': subject.track_id, 'bbox': (xx.min()/w, yy.min()/h,
                          (xx.max()+1)/w, (yy.max()+1)/h), 'opacity': subject.opacity})
        return result

    def prepare_targets(self, subjects, targets, time, shot, size, static=False):
        automatic = targets is None and self.target_mode != 'selected'
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
            mask = Image.fromarray(np.uint8(subject.mask >= .5) * 255).resize(image.size, Image.Resampling.NEAREST)
            bounds = mask.getbbox()
            if bounds is None:
                continue
            ink = weak_spot_ink(mask.crop(bounds), renderer.hud_colors['target-weak-spots'],
                                0 if static else time, stable_number(renderer.seed, 'weak-spots', shot, subject.track_id))
            ink.putalpha(ink.getchannel('A').point(lambda v: round(v * min(1., subject.opacity))))
            panel.layer('target-weak-spots').alpha_composite(ink, bounds[:2])
        renderer.composite_panel(image, panel, 0, 0)

    def draw_outline(self, renderer, image, subjects):
        if not self.target_outline or not self.selected:
            return
        panel = renderer.hud_panel(image.size, 'target-outline')
        for subject in self.selected_subjects(subjects):
            mask = Image.fromarray(np.uint8(subject.mask >= .5) * 255).resize(image.size, Image.Resampling.NEAREST)
            width = max(1, round(3 * min(image.size) / 1080))
            inner = mask.filter(ImageFilter.MinFilter(width * 2 + 1))
            edge = np.maximum(0, np.asarray(mask, dtype=np.int16) - np.asarray(inner, dtype=np.int16))
            ink = Image.new('RGBA', image.size, (*renderer.hud_colors['target-outline'], 0))
            ink.putalpha(Image.fromarray(np.uint8(edge * subject.opacity)))
            panel.layer('target-outline').alpha_composite(ink)
        renderer.composite_panel(image, panel, 0, 0)

    def draw_targets(self, renderer, image, time, static=False):
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
            for identity, cx, cy, radius, opacity in states:
                for part in self.motif_particles(renderer.seed, identity, time, static):
                    x, y = cx + radius * part['x'], cy + radius * part['y']
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
