"""A constant-size scan reticle with continuous, damped focus motion."""
import math

import numpy as np
from PIL import Image, ImageDraw


class AnalysisTarget:
    def __init__(self, size=.36, response=.6):
        self.size, self.response = size, response
        self.position, self.velocity = None, np.zeros(2)
        self.time, self.shot = None, None
        self.radius = None

    def advance(self, destination, time, shot, frame_size, static=False):
        """Exact critically damped step; response is seconds to 95% of a new aim."""
        dimensions = np.asarray(frame_size, dtype=float)
        self.radius = min(frame_size) * self.size / 2
        inset = self.radius / dimensions
        destination = np.clip(destination, inset, 1 - inset)
        reset = self.position is None or shot != self.shot or time < self.time
        if reset or static or not self.response:
            self.position = destination.copy()
            self.velocity = np.zeros(2)
        else:
            dt = max(0., time - self.time)
            omega = 4.744 / self.response
            decay = math.exp(-min(700., omega * dt))
            offset = self.position - destination
            momentum = self.velocity + omega * offset
            self.position = destination + (offset + momentum * dt) * decay
            self.velocity = (self.velocity - omega * momentum * dt) * decay
            # Keep the full disk in view even when a subject is partly offscreen.
            clipped = np.clip(self.position, inset, 1 - inset)
            self.velocity[clipped != self.position] = 0
            self.position = clipped
        self.time, self.shot = time, shot
        return self.position

    def draw(self, renderer, image):
        ss = 3
        radius = self.radius * ss
        center = self.position * np.asarray(image.size)
        # Rasterize only the disk's bounds. Integer origins preserve the global
        # supersampling grid; padding retains the complete antialiasing fringe.
        left, top = np.maximum(0, np.floor(center - self.radius).astype(int) - 4)
        right, bottom = np.minimum(image.size, np.ceil(center + self.radius).astype(int) + 4)
        tile_size = (int(right - left), int(bottom - top))
        cx, cy = (center - (left, top)) * ss
        size = (tile_size[0] * ss, tile_size[1] * ss)
        fill, marks = Image.new('RGBA', size), Image.new('RGBA', size)
        stroked = renderer.geometry.target_fill == 'stroked'
        # Native translucency is multiplied by the normal per-element opacity.
        ink = (*renderer.hud_colors['analysis-target-fill'], 102)
        if not stroked:
            ImageDraw.Draw(fill).ellipse((cx-radius, cy-radius, cx+radius, cy+radius), fill=ink)
        ink = (*renderer.hud_colors['analysis-target'], 230)
        draw = ImageDraw.Draw(marks)
        inner = radius * .65
        stroke = max(ss, round(3 * min(image.size) / 1080 * ss))
        if stroked:
            draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), outline=ink, width=stroke)
        draw.ellipse((cx-inner, cy-inner, cx+inner, cy+inner), outline=ink, width=stroke)
        draw.line((cx-inner, cy, cx+inner, cy), fill=ink, width=stroke)
        draw.line((cx, cy-radius, cx, cy-inner), fill=ink, width=stroke)
        draw.line((cx, cy+inner, cx, cy+radius), fill=ink, width=stroke)
        draw.line((cx, cy-radius*.11, cx, cy+radius*.11), fill=ink, width=stroke)
        panel = renderer.hud_panel(tile_size, 'analysis-target-fill', 'analysis-target')
        for key, layer in (('analysis-target-fill', fill), ('analysis-target', marks)):
            panel.replace(key, layer.resize(tile_size, Image.Resampling.LANCZOS))
        renderer.composite_panel(image, panel, int(left), int(top))
