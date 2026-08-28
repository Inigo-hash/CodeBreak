"""Ambient light overlay for the main menu's dungeon.

`mainMenuBg1.png` already paints blue motes and gold specks into the wall,
but they are baked into the image and so can never move or breathe on their
own. Rather than re-export the art, this module draws a matching overlay on
top of it, so the room reads as alive while the background stays untouched.

Two populations, deliberately different in character:

* Blue motes hold a fixed position and only breathe -- dim, slowly glow,
  peak briefly, slowly fade back down. They read as magic embedded in the
  stone rather than as anything flying around.
* Gold fireflies wander along slow curved paths and pulse while they
  travel. They are few and slow on purpose: a dense, quick field turns a
  menu into a screensaver and starts competing with START GAME.

Everything drawn is a pure function of the elapsed time `t` -- no value is
ever accumulated frame to frame. That is what keeps the effect stable for an
indefinitely long session: nothing integrates, so nothing can drift, speed
up, brighten or wander outside its intended area, and every cycle joins back
onto itself seamlessly.
"""

import math
import random

import numpy as np
import pygame

TAU = math.tau

# Brightness is quantised so a particle can reuse a pre-multiplied sprite
# every frame instead of tinting a fresh surface. 24 steps is far finer than
# the eye can resolve on a glow this dim.
_LEVELS = 24

# Sampled from the motes already painted in the background so the overlay
# sits inside the existing palette instead of introducing a new colour.
_BLUE_TINTS = ((86, 168, 255), (120, 205, 255), (64, 140, 235))
_GOLD_TINTS = ((255, 186, 92), (255, 208, 126), (240, 160, 70))

# The diffuse pool a firefly casts on the wall around itself. Deliberately
# stored already-dim rather than as a bright tint scaled down at draw time:
# a faint pool covers a lot of pixels, and driving a bright colour at a low
# rung of the ladder would quantise it into three or four visible bands
# across a swell. Dim at full resolution breathes smoothly instead.
_FIREFLY_HALO = (54, 42, 24)

# Thresholds for finding the points of light already painted into the
# background. Tuned upward until only real specks qualify: lit brick edges are
# plentiful and start registering as specks well before this.
_SPECK_MIN_LUM = 170
_SPECK_SURROUND_MAX = 62
_SPECK_PATCH = 9          # half-width of the cut-out taken around each speck

# Normalised areas of mainMenuBg1.png that are already light sources -- the
# arched window and the crystal on its pedestal. Extra glow stacked on top of
# those only muddies the art, so motes are kept out of them.
_BRIGHT_ZONES = (
    (0.12, 0.38, 0.26, 0.63),
    (0.34, 0.51, 0.50, 0.69),
)

# Mirrors _dim_code_wall() in main_menu.py: the painted code column on the
# right is deliberately pushed back into being texture, so particles over it
# are damped by the same curve instead of undoing that work.
_CODE_WALL_START = 0.56
_CODE_WALL_DAMP = 0.72

_SPRITE_CACHE = {}


def _build_glow(color, radius, exponent=2.4, core=6):
    """Render one soft bloom: a bright core fading into nothing at the rim.

    A lower `exponent` spreads the light further out from the middle. `core`
    is the divisor giving the solid centre dot its size; pass 0 for a
    coreless, purely diffuse pool.
    """

    # Drawn at 4x and scaled down, because concentric filled circles alone
    # leave visible steps in a gradient this gentle. Big radii are already
    # smooth enough at 2x, and the cost here grows with the square of it.
    supersample = 4 if radius <= 16 else 2
    big = radius * supersample
    canvas = pygame.Surface((big * 2, big * 2), pygame.SRCALPHA)
    center = (big, big)
    for index in range(big, 0, -1):
        distance = index / big          # 1.0 at the rim, ~0 at the core
        falloff = (1.0 - distance) ** exponent
        pygame.draw.circle(
            canvas,
            (round(color[0] * falloff), round(color[1] * falloff),
             round(color[2] * falloff), 255),
            center,
            max(1, round(big * distance)),
        )
    if core:
        pygame.draw.circle(canvas, (*color, 255), center, max(1, big // core))
    return pygame.transform.smoothscale(canvas, (radius * 2, radius * 2))


def _glow_ladder(color, radius, exponent=2.4, core=6):
    """Return the sprite for every brightness step of one colour and size.

    The ladder is built once and shared, so adding particles costs almost
    nothing and no surface is allocated while the menu is running.
    """

    key = (color, radius, exponent, core)
    cached = _SPRITE_CACHE.get(key)
    if cached is not None:
        return cached

    base = _build_glow(color, radius, exponent, core)
    ladder = []
    for step in range(_LEVELS):
        scale = round(255 * step / (_LEVELS - 1))
        frame = base.copy()
        frame.fill((scale, scale, scale, 255), special_flags=pygame.BLEND_RGB_MULT)
        ladder.append(frame)
    ladder = tuple(ladder)
    _SPRITE_CACHE[key] = ladder
    return ladder


def _code_wall_damp(x, width):
    """Fade a particle's peak brightness across the dimmed code column."""

    start = width * _CODE_WALL_START
    if x <= start:
        return 1.0
    blend = (x - start) / max(1.0, width - start)
    return 1.0 - _CODE_WALL_DAMP * (blend ** 1.5)


def _breath(t, rate, offset, gamma):
    """A seamless 0..1 swell, held near zero for most of its cycle.

    The cosine gives a loop with no seam and no sudden edges; the gamma is
    what makes a light linger dim and then peak only briefly, instead of
    spending half of every cycle bright like a blinking LED.
    """

    swell = 0.5 - 0.5 * math.cos(TAU * ((t * rate + offset) % 1.0))
    return swell ** gamma


class _Mote:
    """A blue light embedded in the wall: fixed in place, breathing."""

    __slots__ = ("x", "y", "radius", "ladder", "rate", "offset", "gamma",
                 "floor", "span")

    def __init__(self, rng, x, y, damp):
        self.x = round(x)
        self.y = round(y)
        self.radius = rng.choice((5, 7, 7, 10))
        self.ladder = _glow_ladder(rng.choice(_BLUE_TINTS), self.radius)
        # 5-13 second periods, so no two motes ever look synchronised.
        self.rate = 1.0 / rng.uniform(5.0, 13.0)
        self.offset = rng.random()
        self.gamma = rng.uniform(1.7, 3.4)
        self.floor = rng.uniform(0.0, 0.10) * damp
        self.span = rng.uniform(0.30, 0.55) * damp - self.floor

    def level(self, t):
        return self.floor + self.span * _breath(t, self.rate, self.offset, self.gamma)


class _Firefly:
    """A gold light that wanders slowly and pulses as it goes."""

    __slots__ = ("ax", "ay", "radius", "ladder", "halo", "halo_radius",
                 "drift_x", "drift_y", "rate", "offset", "gamma",
                 "floor", "span", "flare_rate", "flare_offset", "flare")

    def __init__(self, rng, x, y, damp):
        self.ax = x
        self.ay = y
        self.radius = rng.choice((7, 9, 9, 12))
        self.ladder = _glow_ladder(rng.choice(_GOLD_TINTS), self.radius)
        # A wide, dim pool of light beneath the core. Without it a firefly is
        # a hard dot that can only switch on and off; with it the light has a
        # footprint on the wall, so a swell reads as something brightening in
        # place, and a firefly crossing behind a button fades at the edge
        # instead of blinking out. Coreless and gently sloped so it stays a
        # pool rather than a second, bigger dot.
        self.halo_radius = self.radius * 4
        self.halo = _glow_ladder(_FIREFLY_HALO, self.halo_radius,
                                 exponent=1.6, core=0)
        # Two out-of-step sines per axis. Their sum is a slow curved wander
        # that never quite repeats -- so each firefly keeps changing heading
        # on its own -- yet is hard-bounded by the sum of its amplitudes, so
        # it can never creep out of its patch of the room.
        # Speed lives in the periods, not the amplitudes -- shortening these
        # quickens the wander by about a third while leaving the bounds where
        # they were, so the `margin` the anchors were placed against still
        # holds and no firefly can reach an edge.
        self.drift_x = (
            rng.uniform(20.0, 40.0), TAU / rng.uniform(14.0, 25.0), rng.uniform(0.0, TAU),
            rng.uniform(7.0, 16.0), TAU / rng.uniform(5.5, 9.0), rng.uniform(0.0, TAU),
        )
        self.drift_y = (
            rng.uniform(14.0, 30.0), TAU / rng.uniform(17.0, 30.0), rng.uniform(0.0, TAU),
            rng.uniform(5.0, 12.0), TAU / rng.uniform(7.0, 11.0), rng.uniform(0.0, TAU),
        )
        self.rate = 1.0 / rng.uniform(3.4, 7.0)
        self.offset = rng.random()
        self.gamma = rng.uniform(1.4, 2.6)
        # Matched to the specks already painted into mainMenuBg1.png, whose
        # bright cores measure about (240, 205, 115) against a wall with a
        # median luminance of 16. Since the overlay blends additively onto that
        # near-black wall, the level lands almost directly on that value -- so
        # the floor sits high and the breath rides the top of the range rather
        # than swinging up from darkness. The ceiling leaves room for the halo,
        # which adds its own centre value on top of the core.
        self.floor = rng.uniform(0.54, 0.66) * damp
        self.span = rng.uniform(0.74, 0.84) * damp - self.floor
        # A far slower second cycle, steeply gamma'd, so a firefly flares a
        # little brighter now and then rather than on every breath. Small now,
        # because there is only so much headroom left below the ceiling.
        self.flare_rate = 1.0 / rng.uniform(17.0, 29.0)
        self.flare_offset = rng.random()
        self.flare = rng.uniform(0.05, 0.10) * damp

    def position(self, t):
        a1, w1, p1, a2, w2, p2 = self.drift_x
        b1, v1, q1, b2, v2, q2 = self.drift_y
        return (
            self.ax + a1 * math.sin(w1 * t + p1) + a2 * math.sin(w2 * t + p2),
            self.ay + b1 * math.sin(v1 * t + q1) + b2 * math.sin(v2 * t + q2),
        )

    def level(self, t):
        glow = self.floor + self.span * _breath(t, self.rate, self.offset, self.gamma)
        return glow + self.flare * _breath(t, self.flare_rate, self.flare_offset, 7.0)


def _find_static_specks(rgb, limit=160):
    """Locate the points of light painted into the background image.

    Returns (x, y) centres of isolated, bright, warm pixels. Lit brick edges
    are bright too, so a candidate has to be a local maximum *and* sit on dark
    surroundings before it counts as a speck.
    """

    lum = rgb.max(axis=2)
    height, width = lum.shape
    edge = _SPECK_PATCH + 1

    ys, xs = np.nonzero(lum >= _SPECK_MIN_LUM)
    inside = ((ys >= edge) & (ys < height - edge)
              & (xs >= edge) & (xs < width - edge))
    ys, xs = ys[inside], xs[inside]
    if not len(ys):
        return []

    # Local maxima over a 9x9 window. The tie-break on (dy, dx) keeps exactly
    # one pixel of a flat-topped speck rather than every pixel on the plateau.
    peak = lum[ys, xs]
    is_max = np.ones(len(ys), bool)
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            if dy or dx:
                other = lum[ys + dy, xs + dx]
                is_max &= (peak > other) | ((peak == other) & ((dy, dx) < (0, 0)))
    ys, xs = ys[is_max], xs[is_max]

    # Mean of a 29x29 box, via an integral image so the window size is free.
    # A speck sitting on an already-lit surface belongs to a bigger feature --
    # the crystal, the doorway, a painted torch pool -- and is not ours.
    integral = np.cumsum(np.cumsum(lum.astype(np.int64), 0), 1)
    y0, y1 = np.clip(ys - 14, 0, height - 1), np.clip(ys + 14, 0, height - 1)
    x0, x1 = np.clip(xs - 14, 0, width - 1), np.clip(xs + 14, 0, width - 1)
    surround = ((integral[y1, x1] - integral[y0, x1]
                 - integral[y1, x0] + integral[y0, x0])
                / np.maximum(1, (y1 - y0) * (x1 - x0)))
    lone = surround < _SPECK_SURROUND_MAX
    ys, xs = ys[lone], xs[lone]

    colour = rgb[ys, xs]
    warm = colour[:, 0] > colour[:, 2] + 20
    ys, xs = ys[warm], xs[warm]

    if len(ys) > limit:                    # keep the brightest if we must trim
        pick = np.argsort(-lum[ys, xs])[:limit]
        ys, xs = ys[pick], xs[pick]
    return list(zip(xs.tolist(), ys.tolist()))


class _StaticSpeck:
    """A speck painted into the background, given a breath of its own.

    Additive blending can only ever brighten, so a painted light cannot be
    dimmed by drawing over it. Each speck therefore carries a cut-out of its
    own light -- its patch of background with the surrounding wall level
    removed -- which is subtracted to dim it and added to brighten it. Using
    the speck's real shape instead of a modelled one is what lets it walk
    smoothly down toward bare wall rather than having a dark hole punched
    through its middle.
    """

    __slots__ = ("x", "y", "half", "ladder", "rate", "offset", "gamma",
                 "dim", "lift")

    def __init__(self, rng, rgb, x, y):
        half = _SPECK_PATCH
        self.x, self.y, self.half = x, y, half
        patch = rgb[y - half:y + half + 1, x - half:x + half + 1].astype(np.float32)

        # The wall level under the speck, per channel. A low percentile rather
        # than the minimum, which would be mortar shadow and would leave the
        # surrounding brick inside the cut-out.
        base_level = np.percentile(patch.reshape(-1, 3), 20, axis=0)
        excess = np.clip(patch - base_level, 0.0, 255.0)

        # Feather the rim so subtracting the cut-out can never leave a square
        # seam, whatever the speck's own falloff happens to do at the edge.
        span = np.arange(-half, half + 1, dtype=np.float32)
        radius = np.sqrt(span[:, None] ** 2 + span[None, :] ** 2) / half
        excess *= np.clip(1.0 - radius ** 2, 0.0, 1.0)[..., None]

        base = pygame.surfarray.make_surface(
            excess.transpose(1, 0, 2).astype(np.uint8))
        ladder = []
        for step in range(_LEVELS):
            scale = round(255 * step / (_LEVELS - 1))
            frame = base.copy()
            frame.fill((scale, scale, scale, 255), special_flags=pygame.BLEND_RGB_MULT)
            ladder.append(frame)
        self.ladder = tuple(ladder)

        self.rate = 1.0 / rng.uniform(4.5, 14.0)
        self.offset = rng.random()
        self.gamma = rng.uniform(1.0, 2.2)
        # Asymmetric deliberately: the art already has these near the top of
        # their range, so there is far more room below them than above.
        self.dim = rng.uniform(0.35, 0.68)
        self.lift = rng.uniform(0.10, 0.26)

    def delta(self, t):
        """Signed -1..1: negative takes light away, positive adds it."""

        swing = _breath(t, self.rate, self.offset, self.gamma) * 2.0 - 1.0
        return swing * (self.lift if swing > 0.0 else self.dim)


def _scatter(rng, width, height, count, margin, blocked):
    """Pick `count` points spread across the room, avoiding `blocked` rects.

    Best-candidate sampling rather than plain uniform placement: each point is
    whichever of several tries lands farthest from everything already placed.
    Uniform random leaves clumps and bare patches, and on a field this sparse
    that reads as a mistake rather than as scattered dungeon light.
    """

    low_x, high_x = margin, max(margin + 1.0, width - margin)
    low_y, high_y = margin, max(margin + 1.0, height - margin)
    points = []
    for _ in range(count):
        best = None
        best_score = -1.0
        for _ in range(14):
            x = rng.uniform(low_x, high_x)
            y = rng.uniform(low_y, high_y)
            if any(rect.collidepoint(x, y) for rect in blocked):
                continue
            score = min(
                ((x - px) ** 2 + (y - py) ** 2 for px, py in points),
                default=float("inf"),
            )
            if score > best_score:
                best_score = score
                best = (x, y)
        if best is not None:
            points.append(best)
    return points


class AmbientParticles:
    """The main menu's breathing motes and wandering fireflies.

    Build one per screen size and call `draw()` every frame with the elapsed
    time in seconds. The instance is immutable once created, so the same
    seed always produces the same room.
    """

    def __init__(self, width, height, avoid=(), background=None,
                 seed=20260828):
        rng = random.Random(seed)
        area_scale = (width * height) / (1920.0 * 1080.0)

        bright = [
            pygame.Rect(round(x0 * width), round(y0 * height),
                        round((x1 - x0) * width), round((y1 - y0) * height))
            for x0, y0, x1, y1 in _BRIGHT_ZONES
        ]
        avoid = list(avoid)

        # Motes may sit anywhere the art is dark: the logo and the buttons are
        # drawn over them, and a mote that only peeks out beside the logo is
        # exactly the effect wanted.
        mote_count = max(28, min(70, round(52 * area_scale)))
        self._motes = [
            _Mote(rng, x, y, _code_wall_damp(x, width))
            for x, y in _scatter(rng, width, height, mote_count, 14.0, bright)
        ]

        # Fireflies additionally keep their anchor clear of the logo and the
        # button column. Their wander may still carry them behind either --
        # drifting out from behind a button looks right -- but none of them
        # spends its whole life hidden. The margin is the widest excursion
        # (40 + 16 px) plus the largest halo radius (48 px), so the pool of
        # light stays whole instead of being sliced off at the screen edge.
        firefly_count = max(5, min(12, round(9 * area_scale)))
        self._fireflies = [
            _Firefly(rng, x, y, _code_wall_damp(x, width))
            for x, y in _scatter(rng, width, height, firefly_count, 104.0,
                                 bright + avoid)
        ]

        # Finally the specks the artist already painted in. Built last so that
        # adding them cannot shift the random draws above, and the motes and
        # fireflies keep the layout they were tuned with.
        self._specks = []
        if background is not None:
            rgb = pygame.surfarray.array3d(background).transpose(1, 0, 2)
            self._specks = [_StaticSpeck(rng, rgb, x, y)
                            for x, y in _find_static_specks(rgb)]

    def draw(self, surface, t):
        """Blit every particle additively, brightest-pixel-first, at time `t`."""

        blit = surface.blit
        additive = pygame.BLEND_RGB_ADD
        subtractive = pygame.BLEND_RGB_SUB
        top = _LEVELS - 1

        # Painted specks first: they modify the wall itself, and the overlay
        # lights belong on top of the result.
        for speck in self._specks:
            delta = speck.delta(t)
            step = int(abs(delta) * top)
            if step <= 0:
                continue
            half = speck.half
            blit(speck.ladder[min(top, step)],
                 (speck.x - half, speck.y - half), None,
                 additive if delta > 0.0 else subtractive)

        for mote in self._motes:
            step = int(mote.level(t) * top)
            if step <= 0:
                continue
            radius = mote.radius
            blit(mote.ladder[min(top, step)],
                 (mote.x - radius, mote.y - radius), None, additive)

        for fly in self._fireflies:
            step = int(fly.level(t) * top)
            if step <= 0:
                continue
            step = min(top, step)
            x, y = fly.position(t)
            x, y = round(x), round(y)
            # Pool first, core over it, both on the same rung so they breathe
            # together and the light never separates from its own glow.
            radius = fly.halo_radius
            blit(fly.halo[step], (x - radius, y - radius), None, additive)
            radius = fly.radius
            blit(fly.ladder[step], (x - radius, y - radius), None, additive)
