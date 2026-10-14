"""10x10 synthetic visual scenes and transparent perceptual heuristics."""
import math
import random

SCENES = [('moving', 'Moving circle'), ('approach', 'Approaching object'),
          ('flash', 'Flash'), ('smile', 'Smiling face'), ('frown', 'Frowning face'),
          ('wave', 'Flowing wave'), ('noise', 'Random image'), ('still', 'Static square')]


def face(smiling):
    pixels = [0.] * 100
    for y, x in [(2, 3), (2, 6), (3, 3), (3, 6)]:
        pixels[y * 10 + x] = 1.
    mouth = [(6, 2), (7, 3), (8, 4), (8, 5), (7, 6), (6, 7)] if smiling else [
        (8, 2), (7, 3), (6, 4), (6, 5), (7, 6), (8, 7)]
    for y, x in mouth:
        pixels[y * 10 + x] = 1.
    return pixels


class VisualScene:
    def __init__(self, seed=123):
        self.rng = random.Random(seed)
        self.kind = 'moving'

    def frame(self, cycle, strength=1.):
        strength = max(0., min(1., strength))
        if self.kind in ('smile', 'frown'):
            return [v * strength for v in face(self.kind == 'smile')]
        if self.kind == 'noise':
            return [self.rng.random() * strength for _ in range(100)]
        values = []
        for y in range(10):
            for x in range(10):
                if self.kind == 'moving':
                    cx = 4.5 + 3 * math.sin(cycle * .23)
                    cy = 4.5 + 2 * math.cos(cycle * .17)
                    value = float((x - cx) ** 2 + (y - cy) ** 2 <= 2.5 ** 2)
                elif self.kind == 'approach':
                    radius = .7 + (cycle % 36) / 35 * 6
                    value = float((x - 4.5) ** 2 + (y - 4.5) ** 2 <= radius ** 2)
                elif self.kind == 'flash':
                    value = float(cycle % 8 < 4)
                elif self.kind == 'wave':
                    value = .5 + .5 * math.sin(x * .7 + y * .3 - cycle * .25)
                else:
                    value = float(2 <= x <= 7 and 2 <= y <= 7)
                values.append(value * strength)
        return values


def visual_features(pixels, previous):
    brightness = sum(pixels) / 100
    motion = sum(abs(a - b) for a, b in zip(pixels, previous)) / 100
    edges = sum(abs(pixels[y * 10 + x] - pixels[y * 10 + x + 1])
                for y in range(10) for x in range(9))
    edges += sum(abs(pixels[y * 10 + x] - pixels[(y + 1) * 10 + x])
                 for y in range(9) for x in range(10))
    edges /= 180
    area = sum(v > .3 for v in pixels) / 100
    old_area = sum(v > .3 for v in previous) / 100
    looming = max(0., area - old_area)
    contrast = max(pixels) - min(pixels)
    def similarity(template):
        if contrast < .1:
            return 0.
        normalized = [(v - min(pixels)) / contrast for v in pixels]
        return max(0., 1 - sum(abs(a - b) for a, b in zip(normalized, template)) / 100 * 8)
    return {'brightness': brightness, 'motion': motion, 'edges': edges, 'looming': looming,
            'smile': similarity(face(True)), 'frown': similarity(face(False))}


def signal_order(pixels):
    """Synthetic spatial predictability from short-range linear correlations.

    Absolute correlation recognizes alternating as well as smooth patterns.
    Uniform fields have maximal order. This is not an entropy measurement.
    """
    def correlation(a, b):
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        va, vb = sum((v-ma)**2 for v in a), sum((v-mb)**2 for v in b)
        if va * vb < 1e-12:
            return 1. if va + vb < 1e-12 else 0.
        return abs(sum((x-ma)*(y-mb) for x, y in zip(a, b)) / math.sqrt(va*vb))
    values = []
    for lag in (1, 2, 3):
        a = [pixels[y*10+x] for y in range(10) for x in range(10-lag)]
        b = [pixels[y*10+x+lag] for y in range(10) for x in range(10-lag)]
        values.append(correlation(a, b))
        a = [pixels[y*10+x] for y in range(10-lag) for x in range(10)]
        b = [pixels[(y+lag)*10+x] for y in range(10-lag) for x in range(10)]
        values.append(correlation(a, b))
    return max(values)
