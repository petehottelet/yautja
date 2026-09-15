"""Seeded lattice artwork and independent target ornaments and captions."""
import math

import numpy as np
from PIL import Image, ImageDraw

from .signal import stable_number

GEO_OPTIONS = ('geo_grid', 'geo_grid_scale', 'geo_grid_jitter', 'geo_grid_speed')
TARGET_OPTIONS = ('target_mode', 'target_motif', 'target_motif_count', 'target_motif_scale', 'target_label')
GEOMETRY_ELEMENTS = ('geo-grid', 'target-motif', 'target-label')


def noise(seed, time):
    index = math.floor(time)
    fraction = time - index
    blend = fraction * fraction * (3 - 2 * fraction)
    a, b = ((stable_number(seed, 'value', n) % 65536) / 65535 for n in (index, index + 1))
    return a + (b - a) * blend


class GeometryStyle:
    def __init__(self, *, geo_grid=False, geo_grid_scale=160., geo_grid_jitter=.65, geo_grid_speed=1.,
                 target_mode='selected', target_motif='none', target_motif_count=7, target_motif_scale=1., target_label=None):
        if target_mode not in ('selected', 'auto'):
            raise ValueError('--target-mode must be selected or auto')
        if target_motif not in ('none', 'triangles'):
            raise ValueError('--target-motif must be none or triangles')
        if type(target_motif_count) is not int or not 0 <= target_motif_count <= 24:
            raise ValueError('--target-motif-count must be an integer between 0 and 24')
        if target_label is not None and (not isinstance(target_label, str) or not 1 <= len(target_label) <= 24 or
                                         any(not 32 <= ord(c) <= 126 for c in target_label) or not target_label.strip()):
            raise ValueError('--target-label must contain 1-24 printable ASCII characters')
        for key, value, low, high in (('geo-grid-scale', geo_grid_scale, 40, 480),
                                    ('geo-grid-jitter', geo_grid_jitter, 0, 1), ('geo-grid-speed', geo_grid_speed, 0, 5),
                                    ('target-motif-scale', target_motif_scale, .25, 3)):
            if not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f'--{key} must be between {low} and {high}')
        for key in (*GEO_OPTIONS, *TARGET_OPTIONS):
            setattr(self, key, locals()[key])
        self.geometry = None
        self.label_box = None

    def report(self, hud=True):
        return {**{key: getattr(self, key) for key in (*GEO_OPTIONS, *TARGET_OPTIONS)},
                'geo_grid': bool(hud and self.geo_grid)}

    def lattice(self, size, seed):
        signature = (size, seed)
        if self.geometry and self.geometry[0] == signature:
            return self.geometry[1:]
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

    def draw_grid(self, renderer, image, time, static=False):
        if not self.geo_grid:
            return
        vertices, edges, nodes = self.lattice(image.size, renderer.seed)
        ss, scale = 2, min(image.size) / 1080
        ink = Image.new('RGBA', (image.width * ss, image.height * ss))
        draw = ImageDraw.Draw(ink)
        color = renderer.hud_colors['geo-grid']
        t = 0 if static else time * self.geo_grid_speed
        for index, (a, b) in enumerate(edges):
            alpha = round(255 * (.45 + .55 * noise(stable_number(renderer.seed, 'grid-edge', index), t)))
            draw.line([tuple(v * ss for v in vertices[i]) for i in (a, b)],
                      fill=(*color, alpha), width=max(1, round(1.3 * scale * ss)))
        radius = max(.8, 2.2 * scale) * ss
        for i in nodes:
            x, y = (v * ss for v in vertices[i])
            draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(*color, 230))
        panel = renderer.hud_panel(image.size, 'geo-grid')
        panel.replace('geo-grid', ink.resize(image.size, Image.Resampling.LANCZOS))
        renderer.composite_panel(image, panel, 0, 0)

    def targets(self, subjects):
        result = []
        for subject in subjects:
            yy, xx = np.nonzero(subject.mask >= .5)
            if subject.opacity <= 0 or not len(xx):
                continue
            h, w = subject.mask.shape
            result.append({'id': f'auto-{subject.track_id}', 'bbox': (xx.min()/w, yy.min()/h,
                          (xx.max()+1)/w, (yy.max()+1)/h), 'opacity': subject.opacity})
        return result

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
                rng = np.random.default_rng(stable_number(renderer.seed, 'motifs', identity))
                for i in range(self.target_motif_count):
                    angle = rng.uniform(0, math.tau)
                    distance = rng.uniform(1.1, 2.3) * radius * self.target_motif_scale
                    x, y = cx + math.cos(angle) * distance, cy + math.sin(angle) * distance * 1.2 - radius * .4
                    r = radius * rng.uniform(.16, .45) * self.target_motif_scale
                    direction = 1 if rng.random() < .7 else -1
                    nested = rng.random() < .4
                    alpha = round(255 * opacity * (.55 + .45 * noise(stable_number(renderer.seed, identity, 'motif', i), 0 if static else time * 1.5)))
                    for multiplier in ((1, .55) if nested else (1,)):
                        points = [(x + r * multiplier * math.cos(a), y + direction * r * multiplier * math.sin(a))
                                  for a in (math.pi/2, math.pi/2+math.tau/3, math.pi/2+2*math.tau/3)]
                        draw.line([tuple(v * ss for v in p) for p in (*points, points[0])],
                                  fill=(*color, alpha), width=max(2, round(2 * scale * ss)), joint='curve')
            panel.replace('target-motif', ink.resize(image.size, Image.Resampling.LANCZOS))
        if self.target_label is not None:
            opacity = max(state[-1] for state in states)
            margin = max(2, round(42 * scale))
            ink = renderer.typography.mask(self.target_label, max(6, round(26 * scale)), .12)
            max_width = max(1, image.width - 2 * margin)
            if ink.width > max_width:
                ink = ink.resize((max_width, max(1, round(ink.height * max_width / ink.width))), Image.Resampling.LANCZOS)
            y = max(margin, min(image.height - margin - ink.height, round(image.height - 64 * scale - ink.height)))
            layer = Image.new('RGBA', ink.size, (*renderer.hud_colors['target-label'], 0))
            layer.putalpha(ink.point(lambda v: round(v * opacity)))
            panel.layer('target-label').paste(layer, (margin, y))
            self.label_box = (margin, y, margin + ink.width, y + ink.height)
        renderer.composite_panel(image, panel, 0, 0)
