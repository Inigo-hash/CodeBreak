"""
world_map.py

The full-screen world map, opened with M from the gameplay loop.

It is the minimap's big brother, and now literally so: the chart on this
sheet and the chart in the minimap come from the same builder in
src/ui/chart.py, so they share a palette, an ageing pass, an ink hand
and a position marker. Both also read their zone rects from the same
list game.py builds out of src/data/zones.py. The difference is only the
framing - the minimap crops a window around the player, while this shows
the whole island at once on a sheet of paper.

The sheet is built once when the screen opens, not per frame:

    1. the chart is drawn by ui/chart.py - aged, sepia, on parchment,
    2. that is laid onto a paper sheet with a torn, uneven edge and a
       few tea-stains,
    3. zone names, the border and the compass rose are inked on top,
    4. grime and scorching are worked into the margins last.

At night the whole sheet dims evenly - a map is read in whatever light
there is, all of it at once - and only the position marker stays bright
on top.

Only the player marker is redrawn each frame (it pulses), so the loop
itself is just two blits and a marker.

Follows the same modal pattern as profile.py, the inventory bag and
stage_info.py: its own event loop over a blurred snapshot of the frozen
game, which is also what keeps the world paused while the map is open.
"""

import random
import sys

import pygame
from src.config import DEBUG_MODE
from src.systems.audio import handle_music_shortcut

# Aliased because this module uses `title_font` as a local variable name.
from src.ui.theme import title_font as _display_font
# The chart look itself - palette, ageing, ink labels, marker, night -
# lives in ui/chart.py, shared with the minimap in game.py. Only the
# paper this module prints it on is local.
from src.ui.chart import (
    BOSS_INK, INK, INK_FADED, INK_SOFT, MARKER_INK, MARKER_SIZE, PARCHMENT,
    PARCHMENT_DARK, build_chart_texture, build_night_veil, draw_marker,
    ink_text as _ink_text,
)


# ---------------------------------------------------------------------------
# Paper. Fire and dirt along the margins - the part of the look that is
# about the sheet being a physical object rather than about the chart.
# ---------------------------------------------------------------------------
SCORCH_EDGE    = (36, 22, 13)      # near-black char right at the torn edge
SCORCH_MID     = (94, 55, 26)      # brown scorch just inside it
SCORCH_SOFT    = (154, 110, 60)    # toasted tone fading into clean paper
GRIME          = (104, 84, 54)     # thumbed dirt worked into the margins

# Paper geometry. The drawing sits inside a wide margin - a map printed
# edge to edge would not read as a sheet of paper.
SCREEN_MARGIN  = 36
PAD_SIDE       = 40
PAD_TOP        = 96    # room for the title and the compass rose beside it
PAD_BOTTOM     = 58    # room for the footer hint

TEAR_STEP      = 18    # distance between points along the torn edge
TEAR_DEPTH     = 8     # how far inward an ordinary torn point can bite
TEAR_BITE      = 12    # extra depth on the occasional deeper bite

COMPASS_RADIUS = 16    # rose arm length; letters sit outside this


def _paper_font(size):
    """
    The shared display face, at the sizes the map's engraved labels use.

    The sepia paper and ink colours already carry the aged look, so the
    labels only need to read as map lettering rather than UI text.
    """

    return _display_font(size)


def _tear_polygon(width, height, seed=7):
    """
    Points tracing a rectangle whose edges wobble inward a few pixels.

    Seeded so the sheet has the same silhouette every time the map is
    opened - a paper edge that reshuffles itself on every keypress would
    look like a rendering glitch.
    """

    rng = random.Random(seed)
    points = []

    def edge(x0, y0, x1, y1):
        length = max(abs(x1 - x0), abs(y1 - y0))
        steps = max(2, int(length // TEAR_STEP))
        for i in range(steps):
            t = i / steps
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            # Bite inward only, so the sheet never grows past its rect.
            bite = rng.uniform(0, TEAR_DEPTH)
            if rng.random() < 0.14:
                # Every so often a chunk is missing outright - an edge that
                # nibbles evenly all the way round reads as a deckle-cut
                # border rather than a sheet that has been through something.
                bite += rng.uniform(TEAR_DEPTH * 0.5, TEAR_BITE)
            if y0 == y1:                      # horizontal edge
                y += bite if y0 == 0 else -bite
            else:                             # vertical edge
                x += bite if x0 == 0 else -bite
            points.append((x, y))

    edge(0, 0, width, 0)
    edge(width, 0, width, height)
    edge(width, height, 0, height)
    edge(0, height, 0, 0)
    return points


def _clip_to_paper(layer, size, polygon):
    """
    Multiply a layer's alpha by the sheet's silhouette.

    Every layer here is built as a full rectangle, so without this the
    stains, soot and ink would carry on into the corners the tear cut
    away and the sheet would stop looking torn at all.
    """

    mask = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255), polygon)
    layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return layer


def _stain_layer(size, polygon, seed=11):
    """A few translucent blotches, masked to the paper's torn outline."""

    rng = random.Random(seed)
    stains = pygame.Surface(size, pygame.SRCALPHA)

    for _ in range(16):
        cx = rng.randint(0, size[0])
        cy = rng.randint(0, size[1])
        radius = rng.randint(14, 46)
        alpha = rng.randint(10, 26)
        pygame.draw.circle(stains, (*PARCHMENT_DARK, alpha), (cx, cy), radius)

    return _clip_to_paper(stains, size, polygon)


def _edge_weighted_point(rng, size, band):
    """
    A random point biased towards the edges of the sheet.

    Dirt collects where a map is held and folded, so grime sampled
    uniformly over the whole sheet would just look like fog over the
    drawing. Rejection sampling keeps it in the margins.
    """

    width, height = size
    x = y = 0
    for _ in range(24):
        x = rng.randint(0, width)
        y = rng.randint(0, height)
        distance = min(x, y, width - x, height - y)
        if rng.random() > min(1.0, distance / band):
            break
    return x, y


def _grime_layer(size, polygon, seed=29):
    """Smudges and speckled dirt worked into the margins of the sheet."""

    rng = random.Random(seed)
    grime = pygame.Surface(size, pygame.SRCALPHA)
    band = max(70, min(size) // 5)

    for _ in range(30):
        cx, cy = _edge_weighted_point(rng, size, band)
        pygame.draw.circle(grime, (*GRIME, rng.randint(8, 20)),
                           (cx, cy), rng.randint(18, 58))

    # Fine grit on top of the smudges, so the dirt has texture up close
    # instead of reading as a flat brown wash.
    for _ in range(260):
        cx, cy = _edge_weighted_point(rng, size, band)
        pygame.draw.circle(grime, (*GRIME, rng.randint(20, 60)),
                           (cx, cy), rng.randint(1, 2))

    return _clip_to_paper(grime, size, polygon)


def _burn_layer(size, polygon, seed=23):
    """
    The scorched border, as a **multiply** map: white where the sheet is
    untouched, darkening to near-black char at the torn edge.

    It has to multiply rather than paint. Scorching is the paper itself
    going dark, so laying opaque brown over it just looks like a printed
    border - and over the drawing, where the ink and terrain already
    vary, only a multiply keeps what is underneath visible through the
    burn.

    Two consequences of that, both easy to get wrong: the map is white
    outside the sheet (multiplying by white is a no-op, so the burn
    cannot spill), and it must never be alpha-masked to the torn outline
    the way the painted layers are - multiplying the paper's alpha by
    zero would erase the sheet instead of charring it.

    The gradient is built at a fraction of the size and scaled back up.
    That upscale is the blur: drawn full size, the concentric outlines
    read as contour lines on the paper rather than one scorch.
    """

    rng = random.Random(seed)
    shrink = 3
    small_size = (max(1, size[0] // shrink), max(1, size[1] // shrink))
    small_poly = [(x / shrink, y / shrink) for x, y in polygon]

    soft = pygame.Surface(small_size)
    soft.fill((255, 255, 255))

    # Widths are effectively halved: a stroke straddles the outline and
    # only its inner half falls on the sheet. Widest and palest first -
    # each stroke overwrites the middle of the one before it.
    for width, color in (
        (13, (231, 210, 176)),   # barely toasted
        (8, (191, 155, 108)),
        (5, (134, 92, 52)),
        (2, (74, 46, 26)),       # char
    ):
        pygame.draw.polygon(soft, color, small_poly, width)

    # Corners catch first and burn deepest; the rest of the char lands
    # wherever the flame happened to linger.
    corners = ((0, 0), (small_size[0], 0),
               (small_size[0], small_size[1]), (0, small_size[1]))
    for index in range(26):
        if index < len(corners):
            x, y = corners[index]
        else:
            x, y = small_poly[rng.randrange(len(small_poly))]
        radius = rng.randint(3, 6)
        pygame.draw.circle(soft, (170, 128, 82), (int(x), int(y)), radius * 2)
        pygame.draw.circle(soft, (108, 70, 40), (int(x), int(y)), radius)
        pygame.draw.circle(soft, (58, 34, 20), (int(x), int(y)),
                           max(2, radius // 2))

    # Two interpolation passes rather than one: a single jump from a third
    # of the size leaves the gradient stepped in blocks the width of the
    # scale factor.
    burn = pygame.transform.smoothscale(soft, (size[0] * 2 // 3, size[1] * 2 // 3))
    burn = pygame.transform.smoothscale(burn, size).convert_alpha()

    # Pull the burn back towards white in patches, so its depth varies
    # round the sheet - a scorch of even width reads as a border again.
    lighten = pygame.Surface(size, pygame.SRCALPHA)
    for _ in range(46):
        x, y = polygon[rng.randrange(len(polygon))]
        pygame.draw.circle(lighten, (255, 255, 255, rng.randint(60, 165)),
                           (int(x), int(y)), rng.randint(20, 60))
    burn.blit(lighten, (0, 0))

    # The rim itself stays crisp - that is the line the paper burned to.
    pygame.draw.polygon(burn, (26, 15, 9), polygon, 3)
    return burn


def _compass_extent(radius):
    """
    Half-height of the whole rose, letters included.

    The letters sit outside the arms, so the rose needs noticeably more
    room than its radius - sizing the margin by the radius alone is what
    used to push N off the top edge and S down onto the map border.
    """

    return radius + _compass_gap(radius) + _paper_font(_compass_face(radius)).get_height() // 2


def _compass_face(radius):
    return max(11, int(radius * 0.72))


def _compass_gap(radius):
    return max(9, int(radius * 0.62))


def _draw_compass(surface, center, radius):
    """A four-point star rose with N marked, drawn into the paper."""

    cx, cy = center
    pygame.draw.circle(surface, INK_FADED, center, radius, 1)
    pygame.draw.circle(surface, INK_FADED, center, int(radius * 0.72), 1)

    long_arm = radius * 0.95
    short_arm = radius * 0.22

    for angle in (0, 1):   # 0 = N/S star, 1 = the same star turned 90 degrees
        if angle == 0:
            star = [(cx, cy - long_arm), (cx + short_arm, cy),
                    (cx, cy + long_arm), (cx - short_arm, cy)]
        else:
            star = [(cx - long_arm, cy), (cx, cy - short_arm),
                    (cx + long_arm, cy), (cx, cy + short_arm)]
        pygame.draw.polygon(surface, INK_SOFT, star)
        pygame.draw.polygon(surface, INK, star, 1)

    letter_font = _paper_font(_compass_face(radius))
    gap = radius + _compass_gap(radius)
    for text, pos in (
        ("N", (cx, cy - gap)),
        ("S", (cx, cy + gap)),
        ("W", (cx - gap, cy)),
        ("E", (cx + gap, cy)),
    ):
        _ink_text(surface, letter_font, text, pos, INK, halo=False)


def _build_paper(map_texture, map_width, map_height, zone_rects,
                 paper_size, map_rect, scale, title, subtitle):
    """
    Render the entire static sheet - parchment, aged map, zone names,
    border and compass - into one surface.

    Everything here is fixed for as long as the map is open, so it is
    worth paying for once at open time rather than 60 times a second.
    """

    paper = pygame.Surface(paper_size, pygame.SRCALPHA)
    polygon = _tear_polygon(*paper_size)

    pygame.draw.polygon(paper, PARCHMENT, polygon)
    paper.blit(_stain_layer(paper_size, polygon), (0, 0))

    # The chart itself - the same drawing, from the same builder, that
    # the minimap crops its window out of.
    paper.blit(build_chart_texture(map_texture, map_rect.size),
               map_rect.topleft)

    # Double border around the drawing, the way printed charts frame the
    # plate: a heavy line just outside the map, a hairline outside that.
    pygame.draw.rect(paper, INK, map_rect.inflate(12, 12), 3)
    pygame.draw.rect(paper, INK_FADED, map_rect.inflate(22, 22), 1)

    # --- Zone regions and names -------------------------------------------
    # Same rects the minimap labels, converted from world pixels into
    # positions on the sheet, so a name lands on the terrain it names.
    region_layer = pygame.Surface(paper_size, pygame.SRCALPHA)
    label_font = _paper_font(15)

    for zone in zone_rects:
        rect = zone["rect"]
        on_paper = pygame.Rect(
            map_rect.left + rect.left * scale,
            map_rect.top + rect.top * scale,
            max(1, rect.width * scale),
            max(1, rect.height * scale),
        )
        boss = zone.get("is_boss_zone", False)
        pygame.draw.rect(
            region_layer,
            (*(BOSS_INK if boss else INK_SOFT), 70 if boss else 45),
            on_paper, 1, border_radius=8
        )

    paper.blit(region_layer, (0, 0))

    for zone in zone_rects:
        rect = zone["rect"]
        center = (
            map_rect.left + rect.centerx * scale,
            map_rect.top + rect.centery * scale,
        )
        boss = zone.get("is_boss_zone", False)
        label_rect = _ink_text(paper, label_font, zone["name"], center,
                               BOSS_INK if boss else INK,
                               clamp_rect=map_rect.inflate(-12, -12))

        # A short rule under each name, dotted at both ends - the same
        # flourish old charts use to separate a label from the terrain.
        rule_y = label_rect.bottom + 3
        pygame.draw.line(paper, INK_FADED,
                         (label_rect.left + 6, rule_y),
                         (label_rect.right - 6, rule_y), 1)
        pygame.draw.circle(paper, INK_FADED, (label_rect.left + 3, rule_y), 2)
        pygame.draw.circle(paper, INK_FADED, (label_rect.right - 3, rule_y), 2)

    # The rose goes in the top-left margin, not on the drawing: every
    # corner of the island itself belongs to some zone, so a rose placed
    # on the plate lands on top of that zone's name.
    #
    # It is centred in the band actually available - between the torn top
    # edge and the outer border of the plate - and shrunk if that band is
    # tight, rather than being centred on PAD_TOP and trusting it to fit.
    band_top = TEAR_DEPTH + TEAR_BITE + 4
    band_bottom = map_rect.top - 14
    radius = COMPASS_RADIUS
    while radius > 9 and _compass_extent(radius) * 2 > band_bottom - band_top:
        radius -= 1
    _draw_compass(paper, (PAD_SIDE + _compass_extent(radius),
                          (band_top + band_bottom) // 2), radius)

    # --- Title and footer --------------------------------------------------
    title_font = _paper_font(26)
    _ink_text(paper, title_font, title,
              (paper_size[0] // 2, PAD_TOP // 2 - 6), INK, halo=False)

    if subtitle:
        sub_font = _paper_font(14)
        _ink_text(paper, sub_font, subtitle,
                  (paper_size[0] // 2, PAD_TOP // 2 + 17), INK_SOFT,
                  halo=False)

    hint_font = _paper_font(13)
    _ink_text(paper, hint_font, "M or ESC  -  close the map",
              (paper_size[0] // 2, paper_size[1] - PAD_BOTTOM // 2 - 4),
              INK_SOFT, halo=False)

    # --- Aging, over the top of everything --------------------------------
    # Dirt first, then fire: soot sits on top of the grime it burned past.
    paper.blit(_grime_layer(paper_size, polygon), (0, 0))
    paper.blit(_burn_layer(paper_size, polygon), (0, 0),
               special_flags=pygame.BLEND_RGBA_MULT)

    # Trim the whole sheet - ink, grime and all - back to its silhouette.
    # Without this the compass letters and the outer strokes spill into the
    # bites the tear took out, and the missing chunks fill back in.
    _clip_to_paper(paper, paper_size, polygon)

    return paper, polygon


def _draw_marker(surface, center, heading, pulse):
    """
    The "you are here" mark: a pulsing ring with the same arrowhead the
    minimap uses, so the two agree on both position and facing.

    The halo and ring are built on their own SRCALPHA surface because
    ``screen`` is an opaque display surface - draw a translucent colour
    straight onto it and the alpha is thrown away, leaving a solid disc
    that buries the arrow it was meant to sit behind.
    """

    cx, cy = center

    glow = pygame.Surface((96, 96), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*MARKER_INK, 48), (48, 48), 15)
    radius = int(15 + pulse * 10)
    pygame.draw.circle(glow, (*MARKER_INK, int(165 - pulse * 125)),
                       (48, 48), radius, 2)
    surface.blit(glow, (cx - 48, cy - 48))

    draw_marker(surface, center, heading, MARKER_SIZE)


def enemy_is_tracking_player(enemy):
    """Whether an enemy currently knows where the player is.

    Alert, chase, and attack are direct acquisition states. A flinching enemy
    remains visible only when it will resume chasing; returning and idle
    enemies disappear so neither map acts as permanent radar.
    """

    state = getattr(enemy, "state", "")
    if state == "flinch":
        return getattr(enemy, "_resume_state", "") == "chase"
    return state in {"alert", "chase", "attack"}


def enemy_marker_positions(enemies, paper_pos, map_rect, scale, zoom=1.0):
    """Translate only player-aware enemies onto the paper map.

    ``zoom`` is the viewer's magnification: the chart is drawn once at the
    fitted size, so a mark is placed on the sheet first and then scaled
    with it, exactly like every other feature printed on the paper.
    """
    return [
        (
            round(paper_pos[0] + (map_rect.left + enemy.rect.centerx * scale) * zoom),
            round(paper_pos[1] + (map_rect.top + enemy.rect.centery * scale) * zoom),
        )
        for enemy in enemies
        if enemy.active and enemy_is_tracking_player(enemy)
    ]


# --- Viewing the sheet: how close the reader leans, and where they hold it -
MAP_ZOOM_MIN = 1.0          # the whole island on one sheet
MAP_ZOOM_MAX = 3.0          # about as far as a rasterised chart bears
MAP_ZOOM_STEP = 1.25        # one wheel notch


def zoomed_view(view, zoom, new_zoom, anchor):
    """The sheet's new top-left after zooming about ``anchor``.

    Whatever sits under the cursor stays under it, so scrolling reads as
    leaning closer to a point on the chart rather than the map jumping.
    """

    paper_x = (anchor[0] - view[0]) / zoom
    paper_y = (anchor[1] - view[1]) / zoom
    return (anchor[0] - paper_x * new_zoom, anchor[1] - paper_y * new_zoom)


def clamped_view(view, sheet_size, screen_size):
    """Keep the sheet over the screen, or centred while it is smaller.

    An axis with room to spare is centred rather than pannable: there is
    nothing to look for out in the dark beyond the paper's edge.
    """

    placed = []
    for axis in (0, 1):
        size, screen = sheet_size[axis], screen_size[axis]
        if size <= screen:
            placed.append((screen - size) / 2)
        else:
            placed.append(min(0, max(screen - size, view[axis])))
    return tuple(placed)


def _blit_scaled(target, source, dest_rect):
    """Draw ``source`` into ``dest_rect``, scaling only what is on screen.

    Scaling the whole sheet at high zoom would build a surface many times
    the screen and throw most of it away; this pays for visible pixels
    only, so the cost of zooming in does not grow with the zoom.
    """

    visible = dest_rect.clip(target.get_rect())
    if not visible.width or not visible.height:
        return
    scale_x = source.get_width() / dest_rect.width
    scale_y = source.get_height() / dest_rect.height
    source_rect = pygame.Rect(
        int((visible.x - dest_rect.x) * scale_x),
        int((visible.y - dest_rect.y) * scale_y),
        max(1, round(visible.width * scale_x)),
        max(1, round(visible.height * scale_y)),
    ).clip(source.get_rect())
    if not source_rect.width or not source_rect.height:
        return
    patch = source.subsurface(source_rect)
    target.blit(
        pygame.transform.smoothscale(patch, visible.size), visible.topleft
    )


def _draw_enemy_marker(surface, center):
    """Small hostile ink mark that stays readable without hiding terrain."""
    pygame.draw.circle(surface, (78, 18, 18), center, 5)
    pygame.draw.circle(surface, (232, 72, 55), center, 3)
    pygame.draw.line(surface, PARCHMENT, (center[0] - 2, center[1] - 2),
                     (center[0] + 2, center[1] + 2), 1)
    pygame.draw.line(surface, PARCHMENT, (center[0] + 2, center[1] - 2),
                     (center[0] - 2, center[1] + 2), 1)


def open_world_map(screen, map_texture, player_rect, map_width, map_height,
                   zone_rects, heading=(1, 0), background=None,
                   title="Map of the Island", subtitle="", night=False,
                   enemies=()):
    """
    Show the world map and block until the player closes it.

    ``map_texture``  the full-size baked map surface (game.py passes the
                     same one the minimap is scaled from, so the chart
                     includes trees and other object-layer props).
    ``player_rect``  the player in unscaled world pixels.
    ``zone_rects``   game.py's zone list: {"name", "rect", "is_boss_zone"},
                     rects already converted to world pixels.
    ``heading``      the unit vector the player last moved along, so the
                     marker points the same way as the minimap arrow.
    ``night``        whether the world is currently in night mode. The
                     sheet is then lit by the player's own lantern rather
                     than daylight, so the country around them is legible
                     and the far corners fall into gloom.

    Returns the current night flag because F1 can also change it while this
    screen is open.
    """

    SCREEN_W, SCREEN_H = screen.get_size()
    clock = pygame.time.Clock()

    if background is None:
        background = screen.copy()

    # --- Fit the whole map onto a sheet of paper ---------------------------
    max_map_w = SCREEN_W - SCREEN_MARGIN * 2 - PAD_SIDE * 2
    max_map_h = SCREEN_H - SCREEN_MARGIN * 2 - PAD_TOP - PAD_BOTTOM
    scale = min(max_map_w / map_width, max_map_h / map_height)

    draw_w = max(1, int(map_width * scale))
    draw_h = max(1, int(map_height * scale))

    paper_size = (draw_w + PAD_SIDE * 2, draw_h + PAD_TOP + PAD_BOTTOM)
    map_rect = pygame.Rect(PAD_SIDE, PAD_TOP, draw_w, draw_h)

    paper_pos = ((SCREEN_W - paper_size[0]) // 2,
                 (SCREEN_H - paper_size[1]) // 2)

    paper, polygon = _build_paper(
        map_texture, map_width, map_height, zone_rects, paper_size,
        map_rect, scale, title, subtitle
    )

    # Silhouette of the sheet, offset behind it, so the paper reads as
    # lying on top of the scene rather than printed into it.
    shadow = paper.copy()
    shadow.fill((0, 0, 0, 120), special_flags=pygame.BLEND_RGBA_MULT)

    # The blurred backdrop never changes while the map is open either.
    small = pygame.transform.smoothscale(background,
                                         (SCREEN_W // 8, SCREEN_H // 8))
    backdrop = pygame.transform.smoothscale(small, (SCREEN_W, SCREEN_H))
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    backdrop.blit(overlay, (0, 0))

    # --- Viewing state ----------------------------------------------------
    # The sheet is rasterised once at the fitted size; zoom and pan are a
    # transform applied when it is drawn, so leaning in costs no rebuild.
    zoom = MAP_ZOOM_MIN
    view = tuple(float(value) for value in paper_pos)
    dragging = False
    drag_from = (0, 0)
    drag_distance = 0.0

    # Rendered once - the caption never changes while the map is open.
    caption = _paper_font(12).render("YOU ARE HERE", True, MARKER_INK)
    hint = _paper_font(12).render(
        "SCROLL to zoom     DRAG to pan     R to reset", True, PARCHMENT
    )
    # Bottom-left, where the menus put their control hints - the centre
    # belongs to the sheet's own footer and the "you are here" caption.
    hint_rect = hint.get_rect(bottomleft=(28, SCREEN_H - 20))

    # A zero heading would collapse the arrow into a dot - only possible
    # if the player somehow opens the map before ever moving.
    if heading == (0, 0):
        heading = (1, 0)

    # --- Night ------------------------------------------------------------
    # Clipped to the sheet: the veil is a full rectangle, so without the
    # clip the dark would square off the torn edges and hang in the air
    # beyond them.
    def make_night_veil():
        return _clip_to_paper(build_night_veil(paper_size),
                              paper_size, polygon)

    night_veil = make_night_veil() if night else None

    def sheet_rect():
        """Where the paper currently lies on screen."""

        return pygame.Rect(
            round(view[0]), round(view[1]),
            max(1, round(paper_size[0] * zoom)),
            max(1, round(paper_size[1] * zoom)),
        )

    def settle_view():
        """Re-clamp after a zoom or a drag, and repaint the static layers."""

        nonlocal view
        view = clamped_view(
            view, (paper_size[0] * zoom, paper_size[1] * zoom),
            (SCREEN_W, SCREEN_H),
        )
        compose()

    # The backdrop, the sheet and the night veil only change when the view
    # does, so they are composed into one surface and reused every frame.
    composed = pygame.Surface((SCREEN_W, SCREEN_H)).convert()

    def compose():
        placed = sheet_rect()
        # Zoomed in far enough, the sheet covers the screen: the blurred
        # scene behind it and its drop shadow are then invisible, and
        # scaling them anyway is what would make dragging stutter.
        covered = placed.contains(composed.get_rect())
        if not covered:
            composed.blit(backdrop, (0, 0))
            _blit_scaled(
                composed, shadow,
                placed.move(round(7 * zoom), round(9 * zoom)),
            )
        _blit_scaled(composed, paper, placed)
        if night_veil is not None:
            _blit_scaled(composed, night_veil, placed)

    def apply_zoom(direction, anchor):
        """One wheel notch in or out, about the cursor."""

        nonlocal zoom, view
        target = zoom * (MAP_ZOOM_STEP if direction > 0 else 1 / MAP_ZOOM_STEP)
        target = max(MAP_ZOOM_MIN, min(MAP_ZOOM_MAX, target))
        if target == zoom:
            return
        view = zoomed_view(view, zoom, target, anchor)
        zoom = target
        settle_view()

    def on_paper(position):
        return sheet_rect().collidepoint(position)

    settle_view()

    running = True
    # pygame can report a wheel notch twice - as MOUSEWHEEL and as button
    # 4/5 - depending on platform. Once a real wheel event has been seen,
    # the button form is ignored so one notch never zooms two steps.
    wheel_events_seen = False

    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if handle_music_shortcut(event):
                continue

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_m):
                    running = False

                elif event.key == pygame.K_r:
                    zoom = MAP_ZOOM_MIN
                    view = tuple(float(value) for value in paper_pos)
                    settle_view()

                elif event.key == pygame.K_F1:
                    night = not night
                    night_veil = make_night_veil() if night else None
                    compose()

            elif event.type == pygame.MOUSEWHEEL:
                wheel_events_seen = True
                apply_zoom(event.y, pygame.mouse.get_pos())

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (4, 5) and not wheel_events_seen:
                    apply_zoom(1 if event.button == 4 else -1, event.pos)
                elif event.button == 1:
                    dragging = True
                    drag_from = event.pos
                    drag_distance = 0.0

            elif event.type == pygame.MOUSEMOTION and dragging:
                shift = (event.pos[0] - drag_from[0],
                         event.pos[1] - drag_from[1])
                drag_distance += abs(shift[0]) + abs(shift[1])
                view = (view[0] + shift[0], view[1] + shift[1])
                drag_from = event.pos
                settle_view()

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # A release with no press behind it belongs to the click
                # that opened this map - clicking the minimap presses in
                # the gameplay loop and releases in this one. Closing on
                # it would shut the sheet the instant it appeared.
                if not dragging:
                    continue
                # Putting the sheet down: a click off the paper closes the
                # map, but only when it was a click rather than a drag that
                # happened to finish out in the dark.
                was_drag = drag_distance > 6
                dragging = False
                if not was_drag and not on_paper(event.pos):
                    running = False

        screen.blit(composed, (0, 0))

        # Marks are placed on the sheet, then carried by the view, so they
        # track the chart under any zoom or pan.
        def to_screen(paper_x, paper_y):
            return (round(view[0] + paper_x * zoom),
                    round(view[1] + paper_y * zoom))

        marker_center = to_screen(
            map_rect.left + player_rect.centerx * scale,
            map_rect.top + player_rect.centery * scale,
        )
        for enemy_center in enemy_marker_positions(
            enemies, view, map_rect, scale, zoom
        ):
            _draw_enemy_marker(screen, enemy_center)

        # 0 -> 1 -> 0 over roughly a second and a half.
        ticks = pygame.time.get_ticks() % 1500
        pulse = ticks / 750.0
        if pulse > 1.0:
            pulse = 2.0 - pulse

        # Panning can carry the player off the edge of the view. Neither
        # the mark nor its caption is drawn then - a label pinned to the
        # screen edge would point at nothing. R brings the sheet back.
        marker_on_screen = screen.get_rect().collidepoint(marker_center)
        if marker_on_screen:
            _draw_marker(screen, marker_center, heading, pulse)

            # Kept below the marker unless that would push it off the
            # plate, in which case it flips above it.
            plate = pygame.Rect(
                to_screen(map_rect.left, map_rect.top),
                (round(map_rect.width * zoom), round(map_rect.height * zoom)),
            ).inflate(-8, -8).clip(screen.get_rect())
            caption_rect = caption.get_rect(
                center=(marker_center[0], marker_center[1] + 34)
            )
            if caption_rect.bottom > plate.bottom:
                caption_rect.center = (marker_center[0], marker_center[1] - 34)
            if (plate.width > caption_rect.width
                    and plate.height > caption_rect.height):
                caption_rect.clamp_ip(plate)

            halo = pygame.Surface(
                caption_rect.inflate(10, 4).size, pygame.SRCALPHA
            )
            pygame.draw.rect(halo, (*PARCHMENT, 150), halo.get_rect(),
                             border_radius=5)
            screen.blit(halo, caption_rect.inflate(10, 4).topleft)
            screen.blit(caption, caption_rect.topleft)

        hint_halo = pygame.Surface(hint_rect.inflate(20, 10).size,
                                   pygame.SRCALPHA)
        pygame.draw.rect(hint_halo, (12, 12, 16, 170), hint_halo.get_rect(),
                         border_radius=6)
        screen.blit(hint_halo, hint_rect.inflate(20, 10).topleft)
        screen.blit(hint, hint_rect.topleft)

        pygame.display.flip()

    # Let the gameplay scene inherit any F1 change made while viewing the map.
    return night
