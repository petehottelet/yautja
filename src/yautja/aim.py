"""Single-subject selection and persistent, frame-rate-independent reticle motion."""
import math

from .analysis_target import AnalysisTarget


class Aim:
    def __init__(self, hold=3., response=.6):
        self.hold = hold
        self.motion = AnalysisTarget(size=.4, response=response)
        self.identity = None
        self.since = None
        self.time = None
        self.shot = None

    def select(self, candidates, time, shot, static=False):
        if self.time is None or time < self.time or shot != self.shot:
            self.identity, self.since = None, time
        self.time, self.shot = time, shot
        candidates = sorted(candidates, key=lambda item: str(item['id']))
        ids = [item['id'] for item in candidates]
        if not ids:
            self.identity, self.since = None, time
            return None
        if self.identity not in ids:
            self.identity = max(candidates, key=lambda item: round(
                                (item['bbox'][2] - item['bbox'][0]) *
                                (item['bbox'][3] - item['bbox'][1]), 12))['id']
            self.since = time
        elif not static and time - self.since >= self.hold:
            steps = int((time - self.since) / self.hold)
            self.identity = ids[(ids.index(self.identity) + steps) % len(ids)]
            self.since += steps * self.hold
        return next(item for item in candidates if item['id'] == self.identity)

    def advance(self, item, time, shot, size, static=False):
        if item:
            x0, y0, x1, y1 = item['bbox']
            destination = ((x0 + x1) / 2, y0 + (y1 - y0) * .38)
        else:
            t = 0 if static else time
            destination = (.5 + .3 * math.sin(t * .6), .5 + .24 * math.sin(t * .43))
        center = self.motion.advance(destination, time, shot, size, static=static)
        return {**(item or {'id': 'search', 'bbox': (0, 0, 1, 1)}),
                'center': tuple(center), 'persistent': True}
