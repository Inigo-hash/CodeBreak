"""
chart.py

The house style for every map surface in CodeBreak: the aged paper chart.

Two screens draw with this - the full sheet the M key opens
(screens/world_map.py) and the minimap in the corner of the HUD
(screens/game.py). Keeping the palette, the ageing pipeline, the ink
labels, the position marker and the night lighting in one place is what
stops those two from drifting apart, which is the entire point of the
minimap no longer being a crop of the world art: the minimap is meant to
be a piece of the same chart the player carries, not a live picture of
the ground they are standing on.

What is *not* here is the paper itself - the torn edge, the scorching
and the thumbed grime that make the M sheet feel like a physical object.
Those stay in world_map.py, because the minimap sits inside a carved
stone frame: a torn edge there would read as a gap between the chart and
the frame rather than as a worn sheet.

The chart texture this builds is deliberately opaque and rectangular.
The minimap crops a window out of it and needs every pixel of that
window filled; anywhere the crop runs past the coast, the caller fills
with `chart_sea_color()` so the paper appears to continue past the edge.
"""

import random

import pygame


# ---------------------------------------------------------------------------
# Palette - warm paper and brown ink rather than the stone/metal colours the
# rest of the HUD uses, because a map is a thing the character is carrying,
# not another window of the interface.
# ---------------------------------------------------------------------------
PARCHMENT      = (232, 209, 165)
PARCHMENT_DARK = (206, 180, 134)
INK            = (74, 52, 30)
INK_SOFT       = (120, 96, 62)
INK_FADED      = (150, 126, 92)
BOSS_INK       = (140, 44, 32)
MARKER_INK     = (176, 46, 34)

SEPIA_TINT     = (214, 176, 118)   # multiplied over the greyscale map
SEPIA_LIFT     = (38, 28, 14)      # added back so the map is not muddy
COLOR_HINT     = 62                # alpha of the original map blended back
MAP_ON_PAPER   = 232               # alpha of the map itself, so paper shows

# Night. One chart texture serves both times of day - darkness is a veil
# laid over the paper rather than a second bake of it, so F1 toggles
# instantly and there is only ever one chart to keep in memory.
#
# Evenly, across the whole sheet: a sheet of paper held at arm's length
# is lit all at once or not at all, so a pool of light around the
# player's own position on the drawing never made sense.
NIGHT_COLD     = (10, 16, 38)      # the colour the paper goes after dark
NIGHT_STRENGTH = 120               # how deeply the dark stains it

MARKER_SIZE    = 13                # arrowhead length; the minimap scales down


def _age_map(map_texture, size):
    """
    Return the map texture scaled to ``size`` and aged into sepia.

    Greyscale first, then a multiply/add pair to push the neutral tones
    into brown, then a thin pass of the original colours so water still
    looks like water. Doing it in that order keeps the whole image on one
    tonal range - tinting the colour image directly leaves the greens
    bright enough to fight the ink labels drawn over them.
    """

    scaled = pygame.transform.smoothscale(map_texture, size)

    try:
        aged = pygame.transform.grayscale(scaled)
    except AttributeError:       # very old pygame - skip the desaturation
        aged = scaled.copy()

    tint = pygame.Surface(size)
    tint.fill(SEPIA_TINT)
    aged.blit(tint, (0, 0), special_flags=pygame.BLEND_MULT)

    lift = pygame.Surface(size)
    lift.fill(SEPIA_LIFT)
    aged.blit(lift, (0, 0), special_flags=pygame.BLEND_ADD)

    color_hint = scaled.copy()
    color_hint.set_alpha(COLOR_HINT)
    aged.blit(color_hint, (0, 0))

    aged = aged.convert_alpha()
    aged.set_alpha(MAP_ON_PAPER)
    return aged


def build_chart_texture(map_texture, size):
    """
    The whole world drawn as a chart: parchment with the aged map on it.

    Composited onto parchment here rather than at the call site so the
    result is opaque, which is what the minimap needs - it blits a window
    of this straight into its frame with nothing behind it.
    """

    chart = pygame.Surface(size)
    chart.fill(PARCHMENT)
    chart.blit(_age_map(map_texture, size), (0, 0))
    return chart.convert()


def chart_sea_color(chart_texture, samples=64):
    """
    The tone to paint wherever a crop of the chart runs off the paper.

    Taken from the chart's own border rather than hard-coded, so it is
    this map's aged sea and stays right if the map or the ageing is ever
    retuned.

    The *commonest* border colour, not the average: the border is mostly
    open water with the odd headland or rock in it, and averaging those
    together lands on a muddy olive that matches nothing on the chart.
    Colours are bucketed before counting so near-identical shades of the
    same water count as one.
    """

    width, height = chart_texture.get_size()
    buckets = {}

    for i in range(samples):
        t = i / max(1, samples - 1)
        x = min(width - 1, int(t * (width - 1)))
        y = min(height - 1, int(t * (height - 1)))
        for point in ((x, 0), (x, height - 1), (0, y), (width - 1, y)):
            color = chart_texture.get_at(point)[:3]
            key = tuple(channel // 8 for channel in color)
            entry = buckets.setdefault(key, [0, [0, 0, 0]])
            entry[0] += 1
            for channel in range(3):
                entry[1][channel] += color[channel]

    count, total = max(buckets.values(), key=lambda entry: entry[0])
    return tuple(channel // count for channel in total)


def build_sea_tile(color, size=72, seed=5):
    """
    A tileable patch of open water in the chart's own hand: the flat wash
    of ``color`` with faint ink wave dashes drawn over it.

    This is what fills the minimap wherever its window runs off the
    island. A flat fill there reads as the panel behind the map showing
    through - which is exactly the thing this whole change is trying to
    stop - whereas hatched water reads as the chart carrying on.

    Every dash is drawn four times, offset by a full tile left and up, so
    a stroke that runs off one edge comes back in on the other and the
    tiling has no seam.
    """

    rng = random.Random(seed)
    tile = pygame.Surface((size, size))
    tile.fill(color)

    ink = pygame.Surface((size, size), pygame.SRCALPHA)

    for _ in range(10):
        x = rng.randint(0, size)
        y = rng.randint(0, size)
        length = rng.randint(7, 13)
        alpha = rng.randint(34, 58)

        for ox, oy in ((0, 0), (-size, 0), (0, -size), (-size, -size)):
            left = x + ox
            top = y + oy
            # A dash with a small hook on each end - the shorthand every
            # old chart uses for open water.
            pygame.draw.line(ink, (*INK_FADED, alpha),
                             (left, top), (left + length, top), 1)
            pygame.draw.line(ink, (*INK_FADED, alpha),
                             (left - 2, top + 2), (left, top), 1)
            pygame.draw.line(ink, (*INK_FADED, alpha),
                             (left + length, top),
                             (left + length + 2, top + 2), 1)

    tile.blit(ink, (0, 0))
    return tile.convert()


def fill_sea(surface, rect, tile, offset=(0, 0)):
    """
    Tile ``tile`` across ``rect``, phased by ``offset``.

    The offset is what pins the waves to the world rather than to the
    screen: pass the same crop offset the chart is drawn at and the water
    stays still as the map pans under it, instead of swimming along with
    the player.
    """

    size = tile.get_width()
    start_x = rect.left - int(offset[0]) % size
    start_y = rect.top - int(offset[1]) % size

    previous_clip = surface.get_clip()
    surface.set_clip(rect)
    for y in range(start_y, rect.bottom, size):
        for x in range(start_x, rect.right, size):
            surface.blit(tile, (x, y))
    surface.set_clip(previous_clip)


# Finished labels - halo, bleed and ink flattened into one surface -
# keyed by everything they were built from. The minimap re-inks every
# zone name it can see sixty times a second; without this each of those
# frames pays for two font renders and a fresh halo surface per name, to
# produce pixels that have not changed since the map loaded.
_label_cache = {}


def _label_surface(font, text, color, halo, halo_alpha, halo_pad):
    """
    Returns ``(surface, origin, text_size)``.

    ``origin`` is where the text sits inside the surface, so the caller
    can still position by the text's own rect and ignore the halo and the
    one-pixel slack the bleed needs.
    """

    key = (font, text, color, halo, halo_alpha, halo_pad)
    cached = _label_cache.get(key)

    if cached is None:
        label = font.render(text, True, color)
        bleed = font.render(text, True, (*INK_SOFT, 90))

        pad_x, pad_y = halo_pad if halo else (0, 0)
        width, height = label.get_size()

        # The +2 is room for the bleed, which sits a pixel down-right.
        surface = pygame.Surface((width + pad_x + 2, height + pad_y + 2),
                                 pygame.SRCALPHA)
        if halo:
            pygame.draw.rect(surface, (*PARCHMENT, halo_alpha),
                             pygame.Rect(1, 1, width + pad_x, height + pad_y),
                             border_radius=6)

        origin = (pad_x // 2 + 1, pad_y // 2 + 1)
        surface.blit(bleed, (origin[0] + 1, origin[1] + 1))
        surface.blit(label, origin)

        cached = (surface, origin, (width, height))
        _label_cache[key] = cached

    return cached


def ink_text(surface, font, text, center, color=INK, halo=True,
             clamp_rect=None, halo_alpha=150, halo_pad=(14, 8)):
    """
    Draw one inked label: a parchment halo, a soft bleed, then the text.

    The halo is what keeps a zone name legible where it lands on dark
    terrain, without resorting to a black drop-shadow (which would look
    like UI text sitting on top of the paper rather than ink soaked into
    it).

    ``clamp_rect`` pulls a label back inside the drawing if its zone sits
    hard against the coast - the names of the edge zones are long enough
    to run off the plate otherwise.
    """

    stamp, origin, text_size = _label_surface(font, text, color, halo,
                                              halo_alpha, halo_pad)

    rect = pygame.Rect((0, 0), text_size)
    rect.center = center

    if clamp_rect is not None:
        rect.clamp_ip(clamp_rect)

    surface.blit(stamp, (rect.left - origin[0], rect.top - origin[1]))
    return rect


def marker_arrow(center, heading, size=MARKER_SIZE):
    """
    The four points of the position arrowhead.

    Laid out along the heading vector (how far forward) and across it
    (how far out to the side): a long tip against a narrow tail, with a
    notch cut into the back so the pointed end is unmistakable. Both maps
    build their marker from this, so they always agree on which way the
    player is facing.
    """

    cx, cy = center
    hx, hy = heading
    px, py = -hy, hx      # perpendicular to the heading

    def point(along, across):
        return (cx + (hx * along + px * across) * size,
                cy + (hy * along + py * across) * size)

    return (
        point(1.15, 0),      # tip
        point(-0.7, 0.62),   # back corner
        point(-0.42, 0),     # notch, pulled forward between them
        point(-0.7, -0.62),  # back corner
    )


def draw_marker(surface, center, heading, size=MARKER_SIZE):
    """Red ink arrowhead with a dropped shadow, on either map."""

    arrow = marker_arrow(center, heading, size)
    pygame.draw.polygon(surface, (60, 38, 22),
                        [(x + 1, y + 2) for x, y in arrow])
    pygame.draw.polygon(surface, MARKER_INK, arrow)
    pygame.draw.polygon(surface, INK, arrow, 1)


def build_night_veil(size, strength=NIGHT_STRENGTH):
    """
    Nightfall on a chart: one cold, even wash to blit over the paper.

    Deliberately flat. It dims the map without ever hiding part of it,
    which is what a map read after dark should do - the whole sheet is in
    the same light, and the point of taking it out at night is still to
    be able to read it.
    """

    veil = pygame.Surface(size, pygame.SRCALPHA)
    veil.fill((*NIGHT_COLD, strength))
    return veil
