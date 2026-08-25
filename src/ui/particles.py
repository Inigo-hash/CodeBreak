"""Turns the background art's painted sparkles into live, drifting particles.

The main menu background ships with gold and blue motes painted directly
into the image. They look good but they are dead pixels — they never move
and never breathe. Rather than asking an artist to re-export the plate
without them, this module finds them at load time, paints them out using
the surrounding wall texture, and hands back their positions and colours so
a `ParticleField` can redraw them as animated lights.

Detection leans on one property that separates a painted mote from
everything else in the plate: motes have a blown-out near-white core
(brightness 250+), while the code text on the arch tops out around 175 and
brick edge highlights lower still. Size caps then reject the portal and the
torch glows, which are bright but far too large to be motes.

numpy is required for the extraction pass (it runs over ~2M pixels). If it
is unavailable the module degrades gracefully: the plate is left untouched
and the field falls back to procedurally scattered particles.
"""

import math
import random

import pygame

try:
    import numpy as np
except ImportError:  # pragma: no cover - exercised only on a numpy-less install
    np = None


# --- detection tuning -------------------------------------------------
# A mote's core is blown out to near-white; the arch's code text peaks
# around 175 and brick highlights below that, so this single gate does
# most of the separating.
CORE_BRIGHTNESS_MIN = 200
# Local-contrast gate that builds the candidate mask in the first place.
LOCAL_CONTRAST_MIN = 70
# Motes are small and roughly round. The portal and torch glows blow past
# every one of these caps, which is exactly how they get rejected.
MAX_BLOB_DIM = 14
MAX_BLOB_PIXELS = 90
MIN_BLOB_PIXELS = 4
MAX_ASPECT = 2.2
# Removal reaches past the detected core to catch the painted halo too.
HALO_PAD = 5

# --- motion tuning ----------------------------------------------------
# Embers are carried by a wind blowing left-to-right, but nothing here is
# constant: the gust surges and eases, every mote is grabbed by it a bit
# differently, and a turbulence field braids their paths so they never run
# parallel. Rising is what sells it as sparks off a flame rather than dust.
WIND_BASE = 85.0        # px/sec rightward before gusting is applied
TURBULENCE = 26.0       # px/sec of swirl from the flow field
LIFT_MIN, LIFT_MAX = 14.0, 68.0   # px/sec of buoyancy, per mote
FADE_SECONDS = 0.8      # spawn fade-in, so nothing pops into existence
# Additive blending clamps at 255, so pushing past 1.0 blows the core out to
# white while the halo keeps its colour — which is what a hot spark does.
BRIGHTNESS = 1.5


class Sparkle:
    """One live ember: how the wind grabs it, how it rises, how it breathes."""

    __slots__ = ("x", "y", "radius", "color", "phase", "rate",
                 "drag", "lift", "swirl", "age")

    def __init__(self, x, y, radius, color, rng):
        self.x = float(x)
        self.y = float(y)
        self.radius = radius
        self.color = color
        # Independent phase and rate per mote, so the field never pulses in
        # unison — that reads as a flashing bug rather than as atmosphere.
        self.phase = rng.uniform(0.0, math.tau)
        self.rate = rng.uniform(1.1, 2.8)
        self.reset_drift(rng)
        # Start fully lit: the menu opens on embers already mid-flight.
        self.age = FADE_SECONDS

    def reset_drift(self, rng):
        """Re-roll how this ember rides the wind.

        Rolled fresh on every respawn so a mote does not retrace the same
        path each time it crosses the screen.
        """
        self.drag = rng.uniform(0.55, 1.7)   # how hard the wind grabs it
        self.lift = rng.uniform(LIFT_MIN, LIFT_MAX)
        self.swirl = rng.uniform(0.0, math.tau)  # offset into the flow field


def _local_background(surface, size):
    """Cheap box blur: downscale hard, scale back up."""
    w, h = size
    small = pygame.transform.smoothscale(surface, (max(1, w // 10), max(1, h // 10)))
    return pygame.transform.smoothscale(small, (w, h))


def _components(mask, width, height):
    """8-connected blobs in `mask`, as (min_x, max_x, min_y, max_y, pixels).

    Written out rather than pulled from scipy.ndimage — scipy is not a
    dependency of this project and one flood fill is not worth adding it.
    """
    from collections import deque

    seen = np.zeros_like(mask)
    out = []
    xs, ys = np.nonzero(mask)
    for sx, sy in zip(xs, ys):
        if seen[sx, sy]:
            continue
        queue = deque([(sx, sy)])
        seen[sx, sy] = True
        pixels = []
        overflow = False
        while queue:
            x, y = queue.popleft()
            pixels.append((x, y))
            if len(pixels) > MAX_BLOB_PIXELS * 8:
                # Far too big to be a mote (this is the portal or a torch).
                # Stop walking it; the size filter will discard it anyway.
                overflow = True
                break
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < width and 0 <= ny < height
                            and mask[nx, ny] and not seen[nx, ny]):
                        seen[nx, ny] = True
                        queue.append((nx, ny))
        if overflow:
            continue
        arr = np.array(pixels)
        out.append((arr[:, 0].min(), arr[:, 0].max(),
                    arr[:, 1].min(), arr[:, 1].max(), arr))
    return out


def extract_sparkles(surface):
    """Find painted motes, paint them out, and return (cleaned, seeds).

    `seeds` is a list of (x, y, radius, (r, g, b)). The returned surface is
    a new copy — the caller's original is left alone.
    """
    if np is None:
        return surface, []

    width, height = surface.get_size()
    source = surface.convert(24)
    pixels = pygame.surfarray.array3d(source).astype(np.int16)
    blurred = pygame.surfarray.array3d(
        _local_background(source, (width, height))).astype(np.int16)

    contrast = (pixels - blurred).max(axis=2)
    mask = contrast > LOCAL_CONTRAST_MIN

    seeds = []
    # Accumulates how strongly each pixel should be replaced by the local
    # background. Float so overlapping haloes blend instead of banding.
    removal = np.zeros((width, height), dtype=np.float32)

    for min_x, max_x, min_y, max_y, blob in _components(mask, width, height):
        count = len(blob)
        box_w = int(max_x - min_x + 1)
        box_h = int(max_y - min_y + 1)
        if not (MIN_BLOB_PIXELS <= count <= MAX_BLOB_PIXELS):
            continue
        if box_w > MAX_BLOB_DIM or box_h > MAX_BLOB_DIM:
            continue
        aspect = box_w / box_h
        if not (1.0 / MAX_ASPECT <= aspect <= MAX_ASPECT):
            continue

        blob_px = pixels[blob[:, 0], blob[:, 1]]
        brightest = int(blob_px.max(axis=1).argmax())
        peak = int(blob_px[brightest].max())
        if peak < CORE_BRIGHTNESS_MIN:
            continue  # code text and brick highlights fall out here

        cx = int((min_x + max_x) // 2)
        cy = int((min_y + max_y) // 2)
        radius = max(2, (box_w + box_h) // 4)
        colour = tuple(int(c) for c in blob_px[brightest])
        seeds.append((cx, cy, radius, colour))

        # Feathered disc over core + painted halo.
        reach = radius + HALO_PAD
        x0, x1 = max(0, cx - reach), min(width, cx + reach + 1)
        y0, y1 = max(0, cy - reach), min(height, cy + reach + 1)
        gx = np.arange(x0, x1)[:, None] - cx
        gy = np.arange(y0, y1)[None, :] - cy
        dist = np.sqrt(gx * gx + gy * gy) / reach
        falloff = np.clip(1.0 - dist, 0.0, 1.0) ** 0.6
        np.maximum(removal[x0:x1, y0:y1], falloff, out=removal[x0:x1, y0:y1])

    if not seeds:
        return surface, []

    weight = removal[:, :, None]
    cleaned = (pixels * (1.0 - weight) + blurred * weight).astype(np.uint8)
    out = pygame.surfarray.make_surface(cleaned).convert(surface)
    return out, seeds


class ParticleField:
    """Draws and animates the motes lifted out of the background plate."""

    # Discrete brightness steps, so glow sprites can be pre-rendered and
    # cached instead of rebuilt every frame.
    LEVELS = 12
    # Motes never fully vanish; they dim to an ember and swell back.
    MIN_LEVEL = 0.30

    def __init__(self, seeds, width, height, seed=1337, fallback_count=140,
                 extra=110):
        self.width = width
        self.height = height
        rng = random.Random(seed)

        if not seeds:
            # No plate data (numpy missing, or art without motes): scatter a
            # plausible field so the menu still breathes.
            palette = [(255, 214, 140), (255, 236, 200), (120, 210, 255),
                       (170, 232, 255)]
            seeds = [
                (rng.randrange(width), rng.randrange(height),
                 rng.choice([2, 2, 3, 3, 4]), rng.choice(palette))
                for _ in range(fallback_count)
            ]
        elif extra:
            # The plate only carries a few dozen motes bright enough to detect
            # safely. Scatter more, drawn from the colours and sizes actually
            # found in the art, so the field reads as dense without loosening
            # detection into territory where it starts eating the code text.
            palette = [(r, c) for _, _, r, c in seeds]
            seeds = list(seeds) + [
                (rng.randrange(width), rng.randrange(height), *rng.choice(palette))
                for _ in range(extra)
            ]

        self.particles = [Sparkle(x, y, r, c, rng) for x, y, r, c in seeds]
        self._rng = rng
        self._sprites = {}
        self._time = 0.0

    def _sprite(self, color, radius, level):
        """Pre-multiplied additive glow, cached per colour/size/brightness."""
        key = (color[0] >> 4, color[1] >> 4, color[2] >> 4, radius, level)
        cached = self._sprites.get(key)
        if cached is not None:
            return cached

        scale = self.MIN_LEVEL + (1.0 - self.MIN_LEVEL) * (level / (self.LEVELS - 1))
        scale *= BRIGHTNESS
        reach = radius * 4  # halo extends well past the core
        size = reach * 2 + 1

        if np is not None:
            # surfarray is (x, y, 3), so build the grid in that order.
            gx, gy = np.mgrid[0:size, 0:size]
            dist = np.hypot(gx - reach, gy - reach) / reach
            glow = np.clip(1.0 - dist, 0.0, 1.0) ** 2.4
            core = np.where(dist < 0.34,
                            np.clip(1.0 - dist / 0.34, 0.0, 1.0) ** 2 * 0.95,
                            0.0)
            factor = np.clip(glow + core, 0.0, 1.0) * scale
            rgb = np.clip(factor[:, :, None] * np.array(color), 0, 255)
            surf = pygame.surfarray.make_surface(rgb.astype(np.uint8))
        else:
            surf = pygame.Surface((size, size))
            surf.fill((0, 0, 0))
            for dy in range(size):
                for dx in range(size):
                    dist = math.hypot(dx - reach, dy - reach) / reach
                    if dist >= 1.0:
                        continue
                    # Soft halo plus a hot core, scaled by the twinkle level.
                    glow = (1.0 - dist) ** 2.4
                    if dist < 0.34:
                        glow += (1.0 - dist / 0.34) ** 2 * 0.95
                    factor = min(1.0, glow) * scale
                    surf.set_at((dx, dy), (
                        min(255, int(color[0] * factor)),
                        min(255, int(color[1] * factor)),
                        min(255, int(color[2] * factor)),
                    ))

        surf = surf.convert()
        self._sprites[key] = surf
        return surf

    def _respawn(self, p, rng):
        """Re-enter from the floor or the left wall, never as a flat curtain.

        Weighting most respawns onto the floor and biasing both cases toward
        the left is what keeps this reading as sparks coming off something,
        rather than a row of dots marching in from the edge.
        """
        if rng.random() < 0.58:
            # Rising off the floor, biased left where the gust comes from.
            p.x = -40 + self.width * 0.95 * rng.random() ** 1.7
            p.y = self.height + rng.uniform(5, 70)
        else:
            # Blown in through the left wall, biased toward the lower half.
            p.x = rng.uniform(-60, -10)
            p.y = self.height * (1.0 - rng.random() ** 1.5)
        p.reset_drift(rng)
        p.age = 0.0

    def update(self, dt):
        # Guard against huge dt after a stall, which would teleport the field.
        step = min(dt, 0.05)
        self._time += step
        t = self._time
        rng = self._rng

        # Gusting wind: two slow sines beating against each other, so the air
        # surges and eases instead of blowing at one flat rate.
        gust = 1.0 + 0.42 * math.sin(t * 0.37 + 1.3) + 0.22 * math.sin(t * 0.93)
        wind = WIND_BASE * gust

        for p in self.particles:
            p.age += step
            # Cheap curl-like flow field. Sampling each axis against the
            # *other* one is what makes paths cross and braid instead of
            # running parallel — real turbulence without noise tables.
            swirl_x = math.sin(p.y * 0.011 + t * 1.05 + p.swirl)
            swirl_y = math.cos(p.x * 0.009 + t * 0.83 + p.swirl)

            p.x += (wind * p.drag + swirl_x * TURBULENCE) * step
            p.y += (-p.lift * gust + swirl_y * TURBULENCE * 0.7) * step

            if p.x > self.width + 30 or p.y < -30:
                self._respawn(p, rng)

    def draw(self, surface):
        add = pygame.BLEND_RGB_ADD
        span = self.LEVELS - 1
        t = self._time
        for p in self.particles:
            fade = p.age / FADE_SECONDS if p.age < FADE_SECONDS else 1.0
            # Ease off near the top and right edges so embers dissolve into
            # the dark rather than clipping out mid-glow.
            fade = min(fade, p.y / 140.0, (self.width + 30 - p.x) / 200.0, 1.0)
            if fade <= 0.02:
                continue
            wave = 0.5 + 0.5 * math.sin(t * p.rate + p.phase)
            # Folding the fade into the twinkle level reuses the sprite cache
            # instead of needing a second brightness dimension.
            level = int(wave * fade * span)
            sprite = self._sprite(p.color, p.radius, level)
            half = sprite.get_width() // 2
            surface.blit(sprite, (int(p.x) - half, int(p.y) - half),
                         special_flags=add)
