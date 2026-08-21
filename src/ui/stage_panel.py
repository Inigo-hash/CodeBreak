"""
stage_panel.py

The right-hand side of the gameplay HUD: an always-visible objectives
tracker, with a rail of four buttons underneath it that open the full
Stage Information screen (src/screens/stage_info.py).

    +-----------------------------+
    | OBJECTIVES            1/3   |
    | [ ] Search anything you...  |
    | [x] Repair a terminal...    |
    +-----------------------------+
    | (icon) STAGE MANUAL      I  |
    | (icon) ENEMIES           J  |
    | (icon) ITEMS             K  |
    | (icon) OBJECTIVES        O  |
    +-----------------------------+

The tracker sits on top because it is the part the player glances at
constantly; the rail below it is the "I want more detail" row.

This class is a passive widget in the same mould as Toolbar in
screens/inventory.py - it owns no loop and never blocks. The one
difference is what handle_event() returns: Toolbar returns True/False
because it can settle its own input, while opening a modal is not this
widget's job, so handle_event() hands back the tab the player asked for
("manual", "enemies", "items", "objectives") or None. game.py decides
what to do with that.

Geometry is fixed at construction, including the tracker's height, which
is sized for TRACKER_ROWS objectives whether or not that many are
showing. A tracker that grew and shrank with its contents would drag the
rail up and down underneath it, and buttons that move while you are
reaching for them are worse than a little empty space.

Icons are drawn with pygame primitives rather than loaded from files or
typed as emoji: the bundled UI fonts have no emoji glyphs and would render
empty boxes, and there is no icon art in assets/ yet.
"""

import pygame

from src.ui.editor_widgets import wrap_text
from src.ui.theme import UI_COLORS, body_font, title_font


# ---------------------------------------------------------------------------
# Palette - same stone/metal colours as profile.py, inventory.py and the
# pause menu, so this panel reads as part of the same UI. stage_info.py
# imports these rather than redefining them, so the rail and the screen it
# opens can never drift apart.
# ---------------------------------------------------------------------------
PANEL_BG      = UI_COLORS["stone"]
PANEL_INNER   = UI_COLORS["stone_deep"]
PANEL_ALPHA   = 205             # tracker/rail are see-through, like the hotbar
METAL_FRAME   = UI_COLORS["bronze_dark"]
FRAME_HOVER   = UI_COLORS["blue_bright"]
ACCENT        = UI_COLORS["gold"]
ACCENT_DIM    = UI_COLORS["bronze"]
TEXT_MAIN     = UI_COLORS["text"]
TEXT_DIM      = UI_COLORS["text_dim"]
TEXT_DONE     = (120, 200, 140)
BUTTON_BG     = UI_COLORS["stone_light"]
BUTTON_HOVER  = (43, 73, 101)

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
PANEL_WIDTH   = 300
EDGE_MARGIN   = 14   # gap from the right edge of the screen
TOP_MARGIN    = 40   # clears the "ESC = Pause" hint game.py draws at y=10
PAD           = 10
TRACKER_ROWS  = 3    # objectives shown at once (see the note above)
ROW_LINES     = 2    # wrapped lines allowed per objective before ellipsis
BUTTON_HEIGHT = 34
BUTTON_GAP    = 6
GROUP_GAP     = 10   # between the tracker and the rail

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

        stage_panel = StagePanel(screen, stage, stage_progress)
        ...
        tab = stage_panel.handle_event(event)   # in the event loop
        if tab:
            open_stage_info(screen, stage, stage_progress, snapshot, tab)
        ...
        stage_panel.draw(mouse_pos)             # once per frame, on top

    ``stage`` and ``progress`` are held by reference and re-read every
    frame, so completing an objective updates the tracker immediately
    with no call back into this class.
    """

    def __init__(self, screen, stage, progress):
        self.screen = screen
        self.stage = stage
        self.progress = progress

        screen_w, _ = screen.get_size()

        self.font_title = title_font(14)
        self.font_row = body_font(13)
        self.font_button = title_font(13)
        self.font_key = body_font(12, bold=True)

        self.row_height = self.font_row.get_height()

        # --- Tracker -------------------------------------------------------
        # Height is reserved for the worst case: TRACKER_ROWS objectives,
        # each wrapping to ROW_LINES lines.
        header_height = self.font_title.get_height() + 6
        rows_height = TRACKER_ROWS * (self.row_height * ROW_LINES + 4)

        panel_left = screen_w - EDGE_MARGIN - PANEL_WIDTH

        self.tracker_rect = pygame.Rect(
            panel_left,
            TOP_MARGIN,
            PANEL_WIDTH,
            header_height + rows_height + PAD * 2
        )

        # --- Rail ----------------------------------------------------------
        rail_height = (
            len(RAIL_BUTTONS) * BUTTON_HEIGHT
            + (len(RAIL_BUTTONS) - 1) * BUTTON_GAP
            + PAD * 2
        )

        self.rail_rect = pygame.Rect(
            panel_left,
            self.tracker_rect.bottom + GROUP_GAP,
            PANEL_WIDTH,
            rail_height
        )

        # tab id -> clickable rect, built once so hit-testing is a lookup.
        self.button_rects = {}
        for i, (tab, _, _, _) in enumerate(RAIL_BUTTONS):
            self.button_rects[tab] = pygame.Rect(
                self.rail_rect.left + PAD,
                self.rail_rect.top + PAD + i * (BUTTON_HEIGHT + BUTTON_GAP),
                PANEL_WIDTH - PAD * 2,
                BUTTON_HEIGHT
            )

        # Wrapping width for objective text: panel minus padding minus the
        # checkbox column.
        self._text_indent = 28
        self._text_width = PANEL_WIDTH - PAD * 2 - self._text_indent

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
        """Draw the tracker and the rail. Call after the world and HUD."""

        self._draw_tracker()
        self._draw_rail(mouse_pos)

    def _panel_surface(self, rect):
        """A translucent stone panel with a metal frame, sized to rect."""

        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (*PANEL_BG, PANEL_ALPHA),
                         surf.get_rect(), border_radius=8)
        pygame.draw.rect(surf, METAL_FRAME, surf.get_rect(), 2,
                         border_radius=8)
        return surf

    def _tracker_entries(self):
        """
        The objectives to show, unfinished ones first.

        Finished objectives fill any leftover space instead of being
        dropped, so a nearly-complete stage still shows a full box rather
        than a mostly empty one.
        """

        objectives = self.stage.get("objectives", [])

        pending = [o for o in objectives
                   if not self.progress.is_objective_done(o["id"])]
        done = [o for o in objectives
                if self.progress.is_objective_done(o["id"])]

        return (pending + done)[:TRACKER_ROWS]

    def _draw_tracker(self):
        panel = self._panel_surface(self.tracker_rect)

        title = self.font_title.render("OBJECTIVES", True, ACCENT)
        panel.blit(title, (PAD, PAD))

        done_count, total = self.progress.objective_counts(self.stage)
        counter = self.font_title.render(
            f"{done_count}/{total}", True,
            TEXT_DONE if total and done_count >= total else TEXT_DIM
        )
        panel.blit(counter, (self.tracker_rect.width - PAD
                             - counter.get_width(), PAD))

        y = PAD + self.font_title.get_height() + 6

        entries = self._tracker_entries()

        if not entries:
            empty = self.font_row.render("No objectives yet.", True, TEXT_DIM)
            panel.blit(empty, (PAD, y))
        else:
            for objective in entries:
                y = self._draw_tracker_row(panel, objective, y)

        self.screen.blit(panel, self.tracker_rect.topleft)

    def _draw_tracker_row(self, panel, objective, y):
        """Draw one objective line; returns the y for the next row."""

        finished = self.progress.is_objective_done(objective["id"])

        marker = "[x]" if finished else "[ ]"
        marker_color = TEXT_DONE if finished else ACCENT_DIM
        panel.blit(self.font_row.render(marker, True, marker_color), (PAD, y))

        text = objective["text"]
        if objective.get("optional"):
            text = f"(Optional) {text}"

        lines = wrap_text(text, self.font_row, self._text_width)

        # Too long to fit its two lines - cut the last one short rather
        # than let the row spill into the next objective.
        if len(lines) > ROW_LINES:
            lines = lines[:ROW_LINES]
            lines[-1] = lines[-1][:max(0, len(lines[-1]) - 1)] + "..."

        color = TEXT_DIM if finished else TEXT_MAIN
        line_y = y

        for line in lines:
            panel.blit(self.font_row.render(line, True, color),
                       (PAD + self._text_indent, line_y))
            line_y += self.row_height

        # Advance by the lines this row actually used, not the reserved
        # ROW_LINES: a one-line objective followed by a two-line one should
        # not have a hole between them. The panel is still *sized* for the
        # worst case, so the rail below never moves.
        return line_y + 6

    def _draw_rail(self, mouse_pos):
        panel = self._panel_surface(self.rail_rect)

        for tab, label, key_label, _ in RAIL_BUTTONS:
            rect = self.button_rects[tab]
            hovered = rect.collidepoint(mouse_pos)

            # Button rects are in screen space; shift them into the
            # panel surface's own coordinates to draw.
            local = rect.move(-self.rail_rect.left, -self.rail_rect.top)

            pygame.draw.rect(panel, BUTTON_HOVER if hovered else BUTTON_BG,
                             local, border_radius=5)
            pygame.draw.rect(panel, ACCENT if hovered else METAL_FRAME,
                             local, 2, border_radius=5)

            icon_rect = pygame.Rect(local.left + 9, local.centery - 8, 16, 16)
            draw_tab_icon(panel, icon_rect, tab,
                          ACCENT if hovered else TEXT_DIM)

            text = self.font_button.render(label, True, TEXT_MAIN)
            panel.blit(text, (icon_rect.right + 10,
                              local.centery - text.get_height() // 2))

            key_surf = self.font_key.render(key_label, True,
                                            ACCENT if hovered else TEXT_DIM)
            panel.blit(key_surf, (local.right - 12 - key_surf.get_width(),
                                  local.centery - key_surf.get_height() // 2))

        self.screen.blit(panel, self.rail_rect.topleft)
