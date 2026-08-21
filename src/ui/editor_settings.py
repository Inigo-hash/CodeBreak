"""
editor_settings.py

The settings panel that opens inside the coding environment.

Players used to have to leave a challenge and walk back to the main
menu to change the volume or the color theme - and since the editor
does not save work in progress, that meant losing whatever code was
already typed. This panel puts the same controls on top of the editor
instead, so nothing is lost.

It is drawn with the editor's own theme colors rather than a fixed
palette, which means switching the theme here repaints the panel
immediately and doubles as a live preview of the choice.
"""

import pygame

from src.ui.editor_theme import *
from src.settings_state import (
    settings_state,
    current_theme_name,
    cycle_theme,
)

# Height of a volume slider's track.
BAR_HEIGHT = 14

# The draggable knob that rides along a slider track.
KNOB_WIDTH = 16

KNOB_HEIGHT = 18

ARROW_WIDTH = 40

ARROW_HEIGHT = 28


class EditorSettingsPanel:
    """
    Overlay with MUSIC / SFX sliders and the COLOR THEME picker.

    While it is open the editor hands it every event, so typing and
    clicking cannot reach the code underneath.
    """

    def __init__(self, screen):

        self.screen = screen

        self.is_open = False

        # Which slider, if any, the mouse is currently dragging.
        self.dragging = None

        # Rects are built in layout(), which the renderer calls with the
        # editor popup's own rect so the panel stays centered on it even
        # after the window is resized.
        self.panel_rect = pygame.Rect(0, 0, 0, 0)
        self.music_bar = pygame.Rect(0, 0, 0, 0)
        self.sfx_bar = pygame.Rect(0, 0, 0, 0)
        self.theme_left_rect = pygame.Rect(0, 0, 0, 0)
        self.theme_right_rect = pygame.Rect(0, 0, 0, 0)
        self.close_rect = pygame.Rect(0, 0, 0, 0)

    # -------------------------------------------------
    # Open / Close
    # -------------------------------------------------

    def open(self):

        self.is_open = True

    def close(self):

        self.is_open = False

        # Never leave a drag running across an open/close, or the next
        # opening would jump the slider to wherever the mouse happens
        # to be.
        self.dragging = None

    # -------------------------------------------------
    # Layout
    # -------------------------------------------------

    def layout(self, editor_panel_rect):
        """
        Positions the panel centered on the editor popup.
        """

        width = max(340, min(440, int(editor_panel_rect.width * 0.55)))
        height = max(280, min(340, int(editor_panel_rect.height * 0.62)))

        self.panel_rect = pygame.Rect(
            editor_panel_rect.centerx - width // 2,
            editor_panel_rect.centery - height // 2,
            width,
            height
        )

        padding = 28
        inner_width = width - padding * 2

        self.music_bar = pygame.Rect(
            self.panel_rect.left + padding,
            self.panel_rect.top + int(height * 0.30),
            inner_width,
            BAR_HEIGHT
        )

        self.sfx_bar = pygame.Rect(
            self.panel_rect.left + padding,
            self.panel_rect.top + int(height * 0.50),
            inner_width,
            BAR_HEIGHT
        )

        arrow_y = self.panel_rect.top + int(height * 0.70)

        self.theme_left_rect = pygame.Rect(
            self.panel_rect.left + padding,
            arrow_y,
            ARROW_WIDTH,
            ARROW_HEIGHT
        )

        self.theme_right_rect = pygame.Rect(
            self.panel_rect.right - padding - ARROW_WIDTH,
            arrow_y,
            ARROW_WIDTH,
            ARROW_HEIGHT
        )

        self.close_rect = pygame.Rect(
            self.panel_rect.centerx - 70,
            self.panel_rect.bottom - 52,
            140,
            34
        )

    # -------------------------------------------------
    # Events
    # -------------------------------------------------

    def handle_event(self, event):
        """
        Consumes one event.

        Returns True when the panel should stay open, False once the
        player has closed it. The editor calls this for every event
        while the panel is up and never looks at the event itself, so
        keystrokes can't slip through into the code buffer.
        """

        if event.type == pygame.KEYDOWN:

            # Escape closes the settings, not the whole editor - losing
            # a challenge's code to a stray Escape would be exactly the
            # problem this panel exists to avoid.
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.close()
                return False

            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            if self.close_rect.collidepoint(event.pos):
                self.close()
                return False

            if self.music_bar.collidepoint(event.pos):
                self.dragging = "music"
                self._set_volume_from_mouse(event.pos[0])

            elif self.sfx_bar.collidepoint(event.pos):
                self.dragging = "sfx"
                self._set_volume_from_mouse(event.pos[0])

            elif self.theme_left_rect.collidepoint(event.pos):
                cycle_theme(-1)

            elif self.theme_right_rect.collidepoint(event.pos):
                cycle_theme(1)

            return True

        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = None
            return True

        if event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_volume_from_mouse(event.pos[0])
            return True

        return True

    def _set_volume_from_mouse(self, mouse_x):
        """Maps a mouse x position onto the slider being dragged."""

        bar = self.music_bar if self.dragging == "music" else self.sfx_bar

        ratio = (mouse_x - bar.left) / max(1, bar.width)
        ratio = max(0.0, min(1.0, ratio))

        if self.dragging == "music":
            settings_state["music_vol"] = ratio
            pygame.mixer.music.set_volume(ratio)
        else:
            settings_state["sfx_vol"] = ratio

    # -------------------------------------------------
    # Draw
    # -------------------------------------------------

    def draw(self):

        if not self.is_open:
            return

        mouse_position = pygame.mouse.get_pos()

        # Dim the editor so the panel clearly has focus.
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        pygame.draw.rect(
            self.screen,
            PANEL_COLOR,
            self.panel_rect,
            border_radius=PANEL_RADIUS
        )
        pygame.draw.rect(
            self.screen,
            BORDER_COLOR,
            self.panel_rect,
            2,
            border_radius=PANEL_RADIUS
        )

        title = HEADER_FONT.render("SETTINGS", True, TEXT_COLOR)
        self.screen.blit(
            title,
            (
                self.panel_rect.centerx - title.get_width() // 2,
                self.panel_rect.top + 16
            )
        )

        self._draw_slider("MUSIC", self.music_bar, settings_state["music_vol"])
        self._draw_slider("SFX", self.sfx_bar, settings_state["sfx_vol"])

        self._draw_theme_row(mouse_position)

        self._draw_close_button(mouse_position)

    def _draw_slider(self, label, bar, value):

        self.screen.blit(
            SMALL_FONT.render(label, True, SECONDARY_TEXT),
            (bar.left, bar.top - 22)
        )

        pygame.draw.rect(
            self.screen,
            SCROLLBAR_TRACK_COLOR,
            bar,
            border_radius=4
        )

        # Filled portion, so the level is readable at a glance and not
        # only from the knob's position.
        filled = pygame.Rect(bar.left, bar.top, int(bar.width * value), bar.height)
        pygame.draw.rect(self.screen, BUTTON_COLOR, filled, border_radius=4)

        knob_x = bar.left + int((bar.width - KNOB_WIDTH) * value)
        pygame.draw.rect(
            self.screen,
            SCROLLBAR_THUMB_COLOR,
            (knob_x, bar.top - 2, KNOB_WIDTH, KNOB_HEIGHT),
            border_radius=3
        )

    def _draw_theme_row(self, mouse_position):

        self.screen.blit(
            SMALL_FONT.render("COLOR THEME", True, SECONDARY_TEXT),
            (self.theme_left_rect.left, self.theme_left_rect.top - 22)
        )

        for rect in (self.theme_left_rect, self.theme_right_rect):
            hovered = rect.collidepoint(mouse_position)
            pygame.draw.rect(
                self.screen,
                BUTTON_HOVER_COLOR if hovered else BUTTON_COLOR,
                rect,
                border_radius=4
            )

        left_arrow = [
            (self.theme_left_rect.right - 8, self.theme_left_rect.top + 6),
            (self.theme_left_rect.right - 8, self.theme_left_rect.bottom - 6),
            (self.theme_left_rect.left + 6, self.theme_left_rect.centery),
        ]
        right_arrow = [
            (self.theme_right_rect.left + 8, self.theme_right_rect.top + 6),
            (self.theme_right_rect.left + 8, self.theme_right_rect.bottom - 6),
            (self.theme_right_rect.right - 6, self.theme_right_rect.centery),
        ]
        pygame.draw.polygon(self.screen, BUTTON_TEXT_COLOR, left_arrow)
        pygame.draw.polygon(self.screen, BUTTON_TEXT_COLOR, right_arrow)

        # Plain body text rather than a per-theme swatch color: the
        # panel is already painted in the theme being previewed, so the
        # name only has to stay readable.
        name = BUTTON_FONT.render(current_theme_name(), True, TEXT_COLOR)
        self.screen.blit(
            name,
            (
                self.panel_rect.centerx - name.get_width() // 2,
                self.theme_left_rect.centery - name.get_height() // 2
            )
        )

    def _draw_close_button(self, mouse_position):

        hovered = self.close_rect.collidepoint(mouse_position)

        pygame.draw.rect(
            self.screen,
            BUTTON_HOVER_COLOR if hovered else BUTTON_COLOR,
            self.close_rect,
            border_radius=BUTTON_RADIUS
        )

        label = BUTTON_FONT.render("CLOSE", True, BUTTON_TEXT_COLOR)
        self.screen.blit(
            label,
            (
                self.close_rect.centerx - label.get_width() // 2,
                self.close_rect.centery - label.get_height() // 2
            )
        )
