"""
stage_panel.py

The right-hand side of the gameplay HUD: a rail of four buttons that
open the full Stage Information screen (src/screens/stage_info.py).

    [ (icon) STAGE MANUAL     I ]
    [ (icon) ENEMIES          J ]
    [ (icon) ITEMS            K ]
    [ (icon) OBJECTIVES       O ]

Objectives are still tracked while the stage is played - the progress
lives in StageProgress and is read by the OBJECTIVES tab of the Stage
Information screen. There is just no always-on tracker box on the HUD
any more, so the world is what the right-hand side of the screen shows.

The rail buttons are deliberately NOT wrapped in a panel of their own:
each one is a standalone carved plaque, wood for the two "your stuff"
tabs and stone for the two "the world" tabs, so they read as four
separate things to press rather than one list inside a window.

This class is a passive widget in the same mould as Toolbar in
screens/inventory.py - it owns no loop and never blocks. The one
difference is what handle_event() returns: Toolbar returns True/False
because it can settle its own input, while opening a modal is not this
widget's job, so handle_event() hands back the tab the player asked for
("manual", "enemies", "items", "objectives") or None. game.py decides
what to do with that.

Geometry is fixed at construction: nothing here is data-driven, so the
buttons never move while the player is reaching for one.

Icons and plaques are drawn with pygame primitives rather than loaded from
files or typed as emoji: the bundled UI fonts have no emoji glyphs and would
render empty boxes, and there is no icon art in assets/ yet. Each plaque is
rendered once into a cached surface per hover state, so a frame only costs
four blits.
"""

import random

import pygame

from src.ui.theme import UI_COLORS, body_font, title_font


# ---------------------------------------------------------------------------
# Palette - same stone/metal colours as profile.py, inventory.py and the
# pause menu, so this panel reads as part of the same UI. stage_info.py
# imports these rather than redefining them, so the rail and the screen it
# opens can never drift apart.
# ---------------------------------------------------------------------------
PANEL_BG      = UI_COLORS["stone"]
PANEL_INNER   = UI_COLORS["stone_deep"]
METAL_FRAME   = UI_COLORS["bronze_dark"]
FRAME_HOVER   = UI_COLORS["blue_bright"]
ACCENT        = UI_COLORS["gold"]
ACCENT_DIM    = UI_COLORS["bronze"]
TEXT_MAIN     = UI_COLORS["text"]
TEXT_DIM      = UI_COLORS["text_dim"]
TEXT_DONE     = (120, 200, 140)

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
PANEL_WIDTH   = 460  # width of a drawn plaque, and the column's right edge
EDGE_MARGIN   = 14   # gap from the right edge of the screen
TOP_MARGIN    = 82   # clears the persistent gameplay settings gear
BUTTON_HEIGHT = 42
BUTTON_GAP    = 9    # wide enough that the plaques read as separate objects
PLAQUE_BLEED  = 6    # room around the rect for the shadow and hover glow

# Tab id -> (button label, hotkey, pygame key). The order here is the
# order the buttons appear in.
RAIL_BUTTONS = [
    # M is the world map (src/screens/world_map.py), so the manual sits
    # on I - "information" - rather than the initial of its own name.
    ("manual",     "STAGE MANUAL", "I", pygame.K_i),
    ("enemies",    "ENEMIES",      "J", pygame.K_j),
    ("items",      "ITEMS",        "K", pygame.K_k),
    ("objectives", "OBJECTIVES",   "O", pygame.K_o),
]


# Per-tab materials. Wood for the two tabs about the player's own kit,
# stone for the two about the world around them - the same split the
# reference art uses, and a cue the player can read before the label.
WOOD = {
    "outline": (26, 16, 9),
    "face": (94, 59, 34),
    "face_hi": (122, 78, 45),
    "grain": (74, 45, 25),
    "bevel_hi": (142, 96, 56),
    "bevel_lo": (58, 35, 19),
    "trim": (150, 101, 47),
    "material": "wood",
}
STONE = {
    "outline": (18, 20, 26),
    "face": (62, 67, 82),
    "face_hi": (84, 91, 110),
    "grain": (48, 52, 65),
    "bevel_hi": (104, 111, 130),
    "bevel_lo": (38, 41, 52),
    "trim": (126, 133, 152),
    "material": "stone",
}

# Painted button art, one trimmed PNG per tab, produced from the 2x2 reference
# sheet by tools/prepare_rail_buttons.py. The labels are baked into the art, so
# in sprite mode this widget draws no text of its own beyond the hotkey.
# If any file is missing the rail silently falls back to the drawn plaques
# below, so a checkout without the art still runs.
RAIL_SPRITE_DIR = "assets/images/ui"
# Buttons are matched on WIDTH, not height. The plaques are all about the same
# size in the source sheet, but they carry different amounts of scenery hanging
# off the top - the mushroom-and-hat cluster on ENEMIES most of all - so
# matching heights would shrink the busiest plaque and leave the column ragged.
RAIL_SPRITE_WIDTH = 205
HOTKEY_GUTTER = 30          # space to the left of a button for its key badge


def _load_rail_sprites():
    """Return {tab: surface} at rail size, or None if the art is not present."""
    sprites = {}
    for tab, _, _, _ in RAIL_BUTTONS:
        path = f"{RAIL_SPRITE_DIR}/rail_{tab}.png"
        try:
            image = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError, OSError):
            return None

        scale = RAIL_SPRITE_WIDTH / image.get_width()
        size = (RAIL_SPRITE_WIDTH, max(1, round(image.get_height() * scale)))
        sprites[tab] = pygame.transform.smoothscale(image, size)
    return sprites


def _highlight(sprite, accent):
    """Hover version of a sprite: the tab's accent added as light.

    BLEND_RGB_ADD rather than RGBA, so the plaque brightens without the
    transparent margin around it picking up any colour.
    """
    lifted = sprite.copy()
    lifted.fill(tuple(min(64, channel // 4) for channel in accent),
                special_flags=pygame.BLEND_RGB_ADD)
    return lifted


RAIL_STYLES = {
    "manual":     dict(WOOD,  accent=(236, 205, 149)),   # parchment map
    "enemies":    dict(STONE, accent=(178, 132, 224)),   # cursed purple
    "items":      dict(WOOD,  accent=(120, 196, 236)),   # potion blue
    "objectives": dict(STONE, accent=(226, 197, 128)),   # quill-and-ink gold
}

LEAF_DARK  = (44, 96, 40)
LEAF_MID   = (78, 148, 56)
LEAF_LIGHT = (128, 196, 84)


def _leaf(surface, center, length, height, tilt, tone):
    """One outlined leaf, drawn as a tilted ellipse with a centre vein."""
    leaf = pygame.Surface((length + 4, height + 4), pygame.SRCALPHA)
    body = leaf.get_rect().inflate(-4, -4)
    pygame.draw.ellipse(leaf, LEAF_DARK, body.inflate(3, 3))
    pygame.draw.ellipse(leaf, tone, body)
    pygame.draw.line(leaf, LEAF_DARK, (body.left + 1, body.centery),
                     (body.right - 1, body.centery), 1)
    leaf = pygame.transform.rotate(leaf, tilt)
    surface.blit(leaf, leaf.get_rect(center=center))


def _draw_vines(surface, rect, seed):
    """Wrap a vine around the left end of a plaque, plus a sprig top-right.

    The reference art hangs its foliage off the frame corners rather than
    scattering it, so the vine follows the left edge as a stem with leaves
    alternating off it. Positions come from a seeded RNG so a given button's
    foliage is identical in both hover states.
    """
    rng = random.Random(seed)

    # Stem: a short curve hugging the left edge, drawn as a few segments.
    stem_x = rect.left + 4
    points = [(stem_x + rng.randint(-1, 2), y)
              for y in range(rect.top + 2, rect.bottom - 1, 6)]
    if len(points) > 1:
        pygame.draw.lines(surface, LEAF_DARK, False, points, 3)
        pygame.draw.lines(surface, LEAF_MID, False,
                          [(x + 1, y) for x, y in points], 1)

    # Leaves alternating off the stem, then a couple curling onto the face.
    for index, (x, y) in enumerate(points):
        side = 1 if index % 2 else -1
        _leaf(surface, (x + side * 7, y + 1), rng.randint(11, 14),
              rng.randint(6, 8), rng.choice((25, 40, -20, -35)),
              rng.choice((LEAF_MID, LEAF_LIGHT)))

    # A small sprig on the opposite corner keeps the plaque from looking
    # like it is only decorated on one side.
    for offset in (0, 9):
        _leaf(surface, (rect.right - 16 - offset, rect.top + 3),
              rng.randint(10, 13), rng.randint(5, 7),
              rng.choice((-30, -15, 20)), rng.choice((LEAF_MID, LEAF_DARK)))


def draw_tab_icon(surface, rect, tab, color):
    """
    Draw the little glyph for one tab inside ``rect``.

    Shared with stage_info.py so the icon on a rail button and the icon
    on the matching tab of the opened screen are the same drawing.
    """

    x, y, w, h = rect

    if tab == "manual":
        # An open book: two leaves either side of a spine.
        pygame.draw.rect(surface, color, (x, y + 2, w, h - 4), 2)
        pygame.draw.line(surface, color, (x + w // 2, y + 2),
                         (x + w // 2, y + h - 2), 2)
        for i in range(2):
            line_y = y + 6 + i * 5
            pygame.draw.line(surface, color, (x + 3, line_y),
                             (x + w // 2 - 3, line_y), 1)
            pygame.draw.line(surface, color, (x + w // 2 + 3, line_y),
                             (x + w - 3, line_y), 1)

    elif tab == "enemies":
        # A skull: domed head, two eyes, a squared-off jaw.
        pygame.draw.circle(surface, color, (x + w // 2, y + h // 2 - 1),
                           w // 2 - 1, 2)
        eye = max(2, w // 7)
        pygame.draw.circle(surface, color, (x + w // 2 - eye - 1,
                                            y + h // 2 - 1), eye)
        pygame.draw.circle(surface, color, (x + w // 2 + eye + 1,
                                            y + h // 2 - 1), eye)
        pygame.draw.rect(surface, color,
                         (x + w // 2 - 3, y + h - 5, 6, 4), 2)

    elif tab == "items":
        # A cut gem.
        pygame.draw.polygon(surface, color, [
            (x + w // 2, y + 1),
            (x + w - 1, y + h // 2),
            (x + w // 2, y + h - 1),
            (x + 1, y + h // 2),
        ], 2)
        pygame.draw.line(surface, color, (x + 1, y + h // 2),
                         (x + w - 1, y + h // 2), 1)

    else:  # objectives
        # A target with a filled bullseye.
        pygame.draw.circle(surface, color, (x + w // 2, y + h // 2),
                           w // 2 - 1, 2)
        pygame.draw.circle(surface, color, (x + w // 2, y + h // 2),
                           max(2, w // 4), 1)
        pygame.draw.circle(surface, color, (x + w // 2, y + h // 2), 2)


class StagePanel:
    """
    Usage from the game loop:

        stage_panel = StagePanel(screen)
        ...
        tab = stage_panel.handle_event(event)   # in the event loop
        if tab:
            open_stage_info(screen, stage, stage_progress, snapshot, tab)
        ...
        stage_panel.draw(mouse_pos)             # once per frame, on top

    The panel holds no stage state: it only reports which tab the player
    asked for, and the caller passes the stage and its progress to the
    screen that opens.
    """

    def __init__(self, screen):
        self.screen = screen

        screen_w, _ = screen.get_size()

        self.font_button = title_font(13)
        self.font_key = body_font(17, bold=True)

        panel_left = screen_w - EDGE_MARGIN - PANEL_WIDTH

        # --- Rail ----------------------------------------------------------
        # No enclosing panel: the buttons are placed straight onto the screen,
        # each one its own object. Painted art is used when it is available and
        # the drawn plaques stand in when it is not; either way the result is
        # both hover states of every button, rendered up front, plus a tab id
        # -> clickable rect so hit-testing is a lookup.
        self._sprites = _load_rail_sprites()
        self._plaques = {}
        self.button_rects = {}

        y = TOP_MARGIN

        for i, (tab, label, key_label, _) in enumerate(RAIL_BUTTONS):
            if self._sprites:
                art = self._sprites[tab]
                # Right-aligned, so the column has one clean edge.
                rect = pygame.Rect(0, y, art.get_width(), art.get_height())
                rect.right = panel_left + PANEL_WIDTH
                self._plaques[(tab, False)] = art
                self._plaques[(tab, True)] = _highlight(
                    art, RAIL_STYLES[tab]["accent"])
            else:
                rect = pygame.Rect(panel_left, y, PANEL_WIDTH, BUTTON_HEIGHT)
                for hovered in (False, True):
                    self._plaques[(tab, hovered)] = self._build_plaque(
                        tab, label, key_label, hovered, seed=i
                    )

            self.button_rects[tab] = rect
            y = rect.bottom + BUTTON_GAP

        # The drawn plaques carry a bleed margin for their shadow; the painted
        # ones are already trimmed to their own edges.
        self._bleed = 0 if self._sprites else PLAQUE_BLEED

    # -- input --------------------------------------------------------------
    def handle_event(self, event):
        """
        Returns the tab id the player asked to open, or None.

        Both a click on a rail button and its hotkey count. The caller is
        expected to only forward events while unpaused - the panel has no
        idea whether the game is paused.
        """

        if event.type == pygame.KEYDOWN:
            for tab, _, _, key in RAIL_BUTTONS:
                if event.key == key:
                    return tab

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for tab, rect in self.button_rects.items():
                if rect.collidepoint(event.pos):
                    return tab

        return None

    # -- drawing ------------------------------------------------------------
    def draw(self, mouse_pos=(-1, -1)):
        """Draw the rail. Call after the world and HUD."""

        self._draw_rail(mouse_pos)

    def _draw_hotkey_badge(self, rect, key_label, tab, hovered):
        """Small carved chip showing the hotkey, in the gutter beside a button.

        The painted plaques have no clear space for it - every part of the
        face is either lettering or scenery - so the badge sits just off the
        left edge instead of being stamped on top of the artwork.
        """
        key_surf = self.font_key.render(
            key_label, True,
            RAIL_STYLES[tab]["accent"] if hovered else TEXT_DIM)

        chip = pygame.Rect(0, 0, 26, 26)
        # Anchored off the bottom: the plaque body sits at the foot of every
        # sprite, whatever scenery overhangs the top.
        chip.center = (rect.left - HOTKEY_GUTTER // 2 - 2, rect.bottom - 46)

        badge = pygame.Surface(chip.size, pygame.SRCALPHA)
        pygame.draw.rect(badge, (*PANEL_INNER, 210), badge.get_rect(),
                         border_radius=5)
        pygame.draw.rect(badge,
                         RAIL_STYLES[tab]["accent"] if hovered else METAL_FRAME,
                         badge.get_rect(), 2, border_radius=5)
        self.screen.blit(badge, chip)
        self.screen.blit(key_surf, key_surf.get_rect(center=chip.center))

    def _build_plaque(self, tab, label, key_label, hovered, seed):
        """Render one carved plaque, label and all, into its own surface.

        The surface is PLAQUE_BLEED bigger than the button on every side so
        the drop shadow and the hover glow have somewhere to go; draw() lines
        it back up by blitting at the button rect minus the bleed.
        """
        style = RAIL_STYLES[tab]
        radius = 10

        surf = pygame.Surface(
            (PANEL_WIDTH + PLAQUE_BLEED * 2, BUTTON_HEIGHT + PLAQUE_BLEED * 2),
            pygame.SRCALPHA,
        )
        body = pygame.Rect(PLAQUE_BLEED, PLAQUE_BLEED, PANEL_WIDTH, BUTTON_HEIGHT)

        if hovered:
            glow = body.inflate(8, 8)
            pygame.draw.rect(surf, (*style["accent"], 60), glow, border_radius=radius + 3)

        # Sits-on-the-world drop shadow, then the heavy dark outline that
        # gives each plaque its own silhouette.
        pygame.draw.rect(surf, (0, 0, 0, 120), body.move(0, 4), border_radius=radius)
        pygame.draw.rect(surf, style["outline"], body, border_radius=radius)

        face = body.inflate(-6, -6)
        pygame.draw.rect(surf, style["face_hi"] if hovered else style["face"],
                         face, border_radius=radius - 3)

        # Material texture: plank grain for wood, staggered masonry for stone.
        # Both stay low-contrast on purpose - at this size a strong pattern
        # stops reading as material and starts reading as a widget.
        rng = random.Random(seed + 100)
        clip = surf.get_clip()
        surf.set_clip(face)
        if style["material"] == "wood":
            for offset in (6, 13, 22, 30):
                y = face.top + offset
                wobble = rng.randint(-1, 1)
                pygame.draw.line(surf, style["grain"],
                                 (face.left + 4, y),
                                 (face.right - 4, y + wobble), 1)
            # Knot, so the grain has something to bend around.
            knot = (face.left + rng.randint(60, 200), face.centery + rng.randint(-6, 6))
            pygame.draw.ellipse(surf, style["grain"],
                                pygame.Rect(0, 0, 9, 6).move(knot[0], knot[1]), 1)
        else:
            # Rough rock rather than laid masonry: short broken joints and a
            # few chips. A full course-and-joint grid at this height stops
            # looking like stone and starts looking like a table or a meter.
            for _ in range(7):
                x = rng.randint(face.left + 28, face.right - 14)
                y = rng.randint(face.top + 5, face.bottom - 8)
                if rng.random() < 0.5:
                    pygame.draw.line(surf, style["grain"],
                                     (x, y), (x + rng.randint(7, 15), y), 1)
                else:
                    pygame.draw.line(surf, style["grain"],
                                     (x, y), (x, y + rng.randint(4, 8)), 1)
            for _ in range(6):
                x = rng.randint(face.left + 28, face.right - 14)
                y = rng.randint(face.top + 5, face.bottom - 6)
                pygame.draw.circle(surf, style["bevel_lo"], (x, y), 1)
        surf.set_clip(clip)

        # Carved bevel: catches light along the top, falls into shadow at the
        # bottom, then a metal trim line around the whole face.
        pygame.draw.line(surf, style["bevel_hi"],
                         (face.left + 6, face.top + 2), (face.right - 6, face.top + 2), 2)
        pygame.draw.line(surf, style["bevel_lo"],
                         (face.left + 6, face.bottom - 3), (face.right - 6, face.bottom - 3), 2)
        pygame.draw.rect(surf, style["accent"] if hovered else style["trim"],
                         face, 2, border_radius=radius - 3)

        _draw_vines(surf, body, seed=seed)

        # Icon, label, hotkey. The icon starts clear of the vine on the left
        # edge rather than being drawn over by it.
        icon_rect = pygame.Rect(face.left + 20, face.centery - 9, 18, 18)
        draw_tab_icon(surf, icon_rect, tab, style["accent"])

        text = self.font_button.render(label, True, TEXT_MAIN)
        surf.blit(text, (icon_rect.right + 11,
                         face.centery - text.get_height() // 2))

        key_surf = self.font_key.render(key_label, True,
                                        style["accent"] if hovered else TEXT_DIM)
        surf.blit(key_surf, (face.right - 12 - key_surf.get_width(),
                             face.centery - key_surf.get_height() // 2))
        return surf

    def _draw_rail(self, mouse_pos):
        for tab, _, key_label, _ in RAIL_BUTTONS:
            rect = self.button_rects[tab]
            hovered = rect.collidepoint(mouse_pos)
            self.screen.blit(self._plaques[(tab, hovered)],
                             (rect.left - self._bleed, rect.top - self._bleed))
            if self._sprites:
                self._draw_hotkey_badge(rect, key_label, tab, hovered)
