"""
world_map.py

The full-screen world map, opened with M from the gameplay loop.

It is the minimap's big brother: same zone names (both read the pixel
rects game.py builds from src/data/zones.py), same fixed birds-eye
orientation, same "you are here" arrow that turns with the direction you
last walked. The difference is the framing - instead of a small live
panel cropped around the player, this shows the whole island at once,
drawn as an aged paper chart.

The paper look is built once when the screen opens, not per frame:

    1. the map texture is desaturated and tinted sepia, with a little of
       its original colour blended back so terrain is still readable,
    2. that is laid onto a parchment sheet with a torn, uneven edge and
       a few tea-stains,
    3. zone names, the border and the compass rose are inked on top.

Only the player marker is redrawn each frame (it pulses), so the loop
itself is just two blits and a marker.

Follows the same modal pattern as profile.py, the inventory bag and
stage_info.py: its own event loop over a blurred snapshot of the frozen
game, which is also what keeps the world paused while the map is open.
"""

import random
import sys

import pygame


# ---------------------------------------------------------------------------
# Palette - warm paper and brown ink rather than the stone/metal colours the
# rest of the HUD uses, because this is meant to read as a physical object
# the character is holding, not another window of the interface.
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

# Paper geometry. The drawing sits inside a wide margin - a map printed
# edge to edge would not read as a sheet of paper.
SCREEN_MARGIN  = 36
PAD_SIDE       = 34
PAD_TOP        = 68    # room for the title
PAD_BOTTOM     = 52    # room for the footer hint

TEAR_STEP      = 26    # distance between points along the torn edge
TEAR_DEPTH     = 7     # how far inward a torn point can bite

MARKER_SIZE    = 13    # matches the minimap arrow, scaled up a little


def _paper_font(size):
    """
    Cinzel if it is there, consolas if it is not.

    The map is the one screen where a serif face is worth loading: it is
    what makes the zone names read as engraved labels instead of UI text.
    Missing art must never take the game down, hence the fallback.
    """

    try:
        return pygame.font.Font("assets/fonts/Cinzel-Bold.ttf", size)
    except (pygame.error, FileNotFoundError, OSError):
        return pygame.font.SysFont("consolas", size, bold=True)


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


def _stain_layer(size, polygon, seed=11):
    """
    A few translucent blotches, masked to the paper's torn outline.

    The mask matters: the stain layer is a full rectangle, and blitting
    it straight onto the sheet would leave blotches floating in the
    corners the tear cut away.
    """

    rng = random.Random(seed)
    stains = pygame.Surface(size, pygame.SRCALPHA)

    for _ in range(16):
        cx = rng.randint(0, size[0])
        cy = rng.randint(0, size[1])
        radius = rng.randint(14, 46)
        alpha = rng.randint(10, 26)
        pygame.draw.circle(stains, (*PARCHMENT_DARK, alpha), (cx, cy), radius)

    mask = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255), polygon)
    stains.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return stains


def _ink_text(surface, font, text, center, color, halo=True, clamp_rect=None):
    """
    Draw one inked label: a parchment halo, a soft bleed, then the text.

    The halo is what keeps a zone name legible where it lands on dark
    terrain, without resorting to the black drop-shadow the minimap uses
    (which would look like UI text sitting on top of the paper rather
    than ink soaked into it).

    ``clamp_rect`` pulls a label back inside the drawing if its zone sits
    hard against the coast - the names of the edge zones are long enough
    to run off the plate otherwise.
    """

    label = font.render(text, True, color)
    rect = label.get_rect(center=center)

    if clamp_rect is not None:
        rect.clamp_ip(clamp_rect)

    if halo:
        halo_rect = rect.inflate(14, 8)
        halo_surf = pygame.Surface(halo_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(halo_surf, (*PARCHMENT, 120),
                         halo_surf.get_rect(), border_radius=6)
        surface.blit(halo_surf, halo_rect.topleft)

    bleed = font.render(text, True, (*INK_SOFT, 90))
    surface.blit(bleed, (rect.left + 1, rect.top + 1))
    surface.blit(label, rect.topleft)
    return rect


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

    letter_font = _paper_font(13)
    for text, pos in (
        ("N", (cx, cy - radius - 11)),
        ("S", (cx, cy + radius + 11)),
        ("W", (cx - radius - 11, cy)),
        ("E", (cx + radius + 11, cy)),
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

    # The chart itself.
    paper.blit(_age_map(map_texture, map_rect.size), map_rect.topleft)

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
    _draw_compass(paper, (PAD_SIDE + 30, PAD_TOP // 2 + 4), 18)

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

    # Aged edge: a soft wide stroke under a darker thin one, so the tear
    # looks worn rather than cut.
    pygame.draw.polygon(paper, (*INK_FADED, 70), polygon, 6)
    pygame.draw.polygon(paper, (*INK_SOFT, 150), polygon, 2)

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

    hx, hy = heading
    px, py = -hy, hx      # perpendicular to the heading

    def point(along, across):
        return (cx + (hx * along + px * across) * MARKER_SIZE,
                cy + (hy * along + py * across) * MARKER_SIZE)

    arrow = (
        point(1.15, 0),      # tip
        point(-0.7, 0.62),   # back corner
        point(-0.42, 0),     # notch, pulled forward between them
        point(-0.7, -0.62),  # back corner
    )
    pygame.draw.polygon(surface, MARKER_INK, arrow)
    pygame.draw.polygon(surface, INK, arrow, 1)


def open_world_map(screen, map_texture, player_rect, map_width, map_height,
                   zone_rects, heading=(1, 0), background=None,
                   title="Map of the Island", subtitle=""):
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

    paper, polygon = _build_paper(map_texture, map_width, map_height,
                                  zone_rects, paper_size, map_rect, scale,
                                  title, subtitle)

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

    marker_center = (
        paper_pos[0] + map_rect.left + player_rect.centerx * scale,
        paper_pos[1] + map_rect.top + player_rect.centery * scale,
    )

    # Rendered once, not per frame - the caption never changes while the
    # map is open. Kept below the marker unless that would push it off the
    # plate, in which case it flips above it.
    caption = _paper_font(12).render("YOU ARE HERE", True, MARKER_INK)
    caption_rect = caption.get_rect(
        center=(marker_center[0], marker_center[1] + 34)
    )
    plate = map_rect.move(paper_pos).inflate(-8, -8)
    if caption_rect.bottom > plate.bottom:
        caption_rect.center = (marker_center[0], marker_center[1] - 34)
    caption_rect.clamp_ip(plate)

    # A zero heading would collapse the arrow into a dot - only possible
    # if the player somehow opens the map before ever moving.
    if heading == (0, 0):
        heading = (1, 0)

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_m):
                    running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Clicking off the sheet closes it, the way putting a map
                # down does; clicking on the sheet does nothing.
                local = (event.pos[0] - paper_pos[0],
                         event.pos[1] - paper_pos[1])
                if not paper.get_rect().collidepoint(local):
                    running = False

        screen.blit(backdrop, (0, 0))
        screen.blit(shadow, (paper_pos[0] + 7, paper_pos[1] + 9))
        screen.blit(paper, paper_pos)

        # 0 -> 1 -> 0 over roughly a second and a half.
        ticks = pygame.time.get_ticks() % 1500
        pulse = ticks / 750.0
        if pulse > 1.0:
            pulse = 2.0 - pulse

        _draw_marker(screen, marker_center, heading, pulse)

        halo = pygame.Surface(caption_rect.inflate(10, 4).size, pygame.SRCALPHA)
        pygame.draw.rect(halo, (*PARCHMENT, 150), halo.get_rect(),
                         border_radius=5)
        screen.blit(halo, caption_rect.inflate(10, 4).topleft)
        screen.blit(caption, caption_rect.topleft)

        pygame.display.flip()
