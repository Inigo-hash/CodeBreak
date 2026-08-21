"""
problem_panel.py

Displays the current coding challenge information.

Responsibilities:
- Draw the objective panel.
- Show the challenge title.
- Show the objective.
- Wrap long text so it fits the pane's width.
- Scroll when the text is taller than the pane.
- (Future) Show hints and difficulty.

This class ONLY draws the problem information.
It never validates code and never decides layout - the renderer
tells it which rectangle to draw inside, and that rectangle can
change at any moment because the player can drag the divider
between the panes.
"""

import pygame

from src.ui.editor_theme import *
from src.ui.editor_widgets import VerticalScrollbar, wrap_text

# Height of one line of body text. Every row uses the same height,
# which is what lets the scrollbar treat the content as a simple
# list of lines regardless of which font each row uses.
ROW_HEIGHT = 24

# Space between the pane's edge and its text.
INNER_PADDING = 14

# Height of the fixed "OBJECTIVE" strip at the top of the pane.
TITLE_STRIP_HEIGHT = 38


class ProblemPanel:

    def __init__(self, challenge):

        self.challenge = challenge

        # First body row currently shown.
        self.scroll_offset = 0

        self.scrollbar = VerticalScrollbar()

        # Rectangle the panel was last drawn in. Stored so scrolling
        # can be clamped correctly between frames.
        self.rect = None

        # Wrapping is only redone when the pane's width changes,
        # rather than on every single frame.
        self._wrapped_rows = []
        self._wrapped_width = None

    # ---------------------------------------------------------
    # Content
    # ---------------------------------------------------------

    def _build_rows(self, max_width):
        """
        Turn the challenge into a flat list of drawable rows:

            (text, font, color)

        Each row is one line that already fits inside `max_width`.
        """

        rows = []

        # --------------------------------------
        # Challenge Title
        # --------------------------------------

        for line in wrap_text(
            self.challenge.get("title", "Challenge"),
            HEADER_FONT,
            max_width
        ):
            rows.append((line, HEADER_FONT, TEXT_COLOR))

        # --------------------------------------
        # Difficulty (optional)
        # --------------------------------------
        # Some challenges are defined inline (e.g. the dev-only F5
        # challenge in game.py) and have no difficulty field, so it
        # is only drawn when it actually exists.

        difficulty = self.challenge.get("difficulty")

        if difficulty:
            rows.append((difficulty, SMALL_FONT, SECONDARY_TEXT))

        rows.append(("", SMALL_FONT, SECONDARY_TEXT))

        # --------------------------------------
        # Problem
        # --------------------------------------

        problem = self.challenge.get(
            "problem",
            ""
        )

        if problem:

            rows.append(
                ("Problem", SMALL_FONT, SECONDARY_TEXT)
            )

            for raw_line in problem.strip().splitlines():

                if not raw_line.strip():

                    rows.append(
                        ("", TEXT_FONT, TEXT_COLOR)
                    )

                    continue

                for line in wrap_text(
                    raw_line,
                    TEXT_FONT,
                    max_width
                ):

                    rows.append(
                        (
                            line,
                            TEXT_FONT,
                            TEXT_COLOR
                        )
                    )

            rows.append(
                ("", SMALL_FONT, SECONDARY_TEXT)
            )

        # --------------------------------------
        # Objective
        # --------------------------------------

        rows.append(
            ("Objective", SMALL_FONT, SECONDARY_TEXT)
        )

        for line in wrap_text(
            self.challenge.get("objective", ""),
            TEXT_FONT,
            max_width
        ):

            rows.append(
                (
                    line,
                    TEXT_FONT,
                    TEXT_COLOR
                )
            )
        return rows

    def _rows_for_width(self, max_width):
        """Return the wrapped rows, rebuilding them only if needed."""

        if max_width != self._wrapped_width:

            self._wrapped_rows = self._build_rows(max_width)
            self._wrapped_width = max_width

        return self._wrapped_rows

    # ---------------------------------------------------------
    # Scrolling
    # ---------------------------------------------------------

    def get_body_rect(self, rect):
        """The area below the title strip, where the text is drawn."""

        return pygame.Rect(
            rect.x,
            rect.y + TITLE_STRIP_HEIGHT,
            rect.width,
            rect.height - TITLE_STRIP_HEIGHT
        )

    def get_visible_rows(self, rect):
        """How many rows of text fit inside the pane at once."""

        body = self.get_body_rect(rect)

        return max(
            0,
            (body.height - INNER_PADDING) // ROW_HEIGHT
        )

    def get_max_scroll_offset(self, rect):
        """The furthest down the panel can be scrolled."""

        text_width = self._text_width(rect)

        total_rows = len(self._rows_for_width(text_width))

        return max(
            0,
            total_rows - self.get_visible_rows(rect)
        )

    def clamp_scroll(self):
        """Keep the scroll position inside the valid range."""

        if not self.rect:

            self.scroll_offset = max(0, self.scroll_offset)

            return

        self.scroll_offset = max(
            0,
            min(
                self.scroll_offset,
                self.get_max_scroll_offset(self.rect)
            )
        )

    def scroll(self, amount):
        """Scroll by a number of rows (positive scrolls downward)."""

        self.scroll_offset += amount

        self.clamp_scroll()

    def set_scroll_from_mouse_y(self, mouse_y):
        """Jump the scroll position to match a mouse Y position."""

        if not self.rect:
            return

        self.scroll_offset = self.scrollbar.offset_from_mouse_y(
            mouse_y,
            self.get_max_scroll_offset(self.rect)
        )

        self.clamp_scroll()

    # ---------------------------------------------------------
    # Internal Helpers
    # ---------------------------------------------------------

    def _text_width(self, rect):
        """
        Usable width for text: the pane minus its padding, minus the
        strip of space the scrollbar sits in. The scrollbar's width
        is always subtracted - even when no scrollbar is showing -
        so text never reflows the moment one appears.
        """

        return (
            rect.width
            - (INNER_PADDING * 2)
            - SCROLLBAR_WIDTH
            - SCROLLBAR_MARGIN
        )

    # ---------------------------------------------------------
    # Draw
    # ---------------------------------------------------------

    def draw(self, screen, rect):
        """
        Draw the challenge panel.

        Parameters
        ----------
        screen : pygame.Surface
            Main display surface.

        rect : pygame.Rect
            Area where the panel should be drawn.
        """

        self.rect = rect.copy()

        # --------------------------------------
        # Panel Background
        # --------------------------------------

        pygame.draw.rect(
            screen,
            PANEL_COLOR,
            rect,
            border_radius=PANEL_RADIUS
        )

        # --------------------------------------
        # Panel Border
        # --------------------------------------

        pygame.draw.rect(
            screen,
            BORDER_COLOR,
            rect,
            2,
            border_radius=PANEL_RADIUS
        )

        # --------------------------------------
        # Fixed Title Strip
        # --------------------------------------

        label = HEADER_FONT.render(
            "OBJECTIVE",
            True,
            TEXT_COLOR
        )

        screen.blit(
            label,
            (
                rect.x + INNER_PADDING,
                rect.y + 8
            )
        )

        pygame.draw.line(
            screen,
            BORDER_COLOR,
            (rect.x + 1, rect.y + TITLE_STRIP_HEIGHT),
            (rect.right - 2, rect.y + TITLE_STRIP_HEIGHT),
            1
        )

        # --------------------------------------
        # Scrollable Body
        # --------------------------------------

        body = self.get_body_rect(rect)

        rows = self._rows_for_width(self._text_width(rect))

        visible_rows = self.get_visible_rows(rect)

        self.clamp_scroll()

        # Text is clipped to the body so a long word can never
        # spill over the divider into the code editor.
        previous_clip = screen.get_clip()

        screen.set_clip(body.clip(previous_clip) if previous_clip else body)

        y = body.y + 6

        for text, font, color in rows[
            self.scroll_offset:
            self.scroll_offset + visible_rows
        ]:

            if text:

                screen.blit(
                    font.render(text, True, color),
                    (rect.x + INNER_PADDING, y)
                )

            y += ROW_HEIGHT

        screen.set_clip(previous_clip)

        # --------------------------------------
        # Scrollbar
        # --------------------------------------

        self.scrollbar.update(
            body,
            len(rows),
            visible_rows,
            self.scroll_offset
        )

        self.scrollbar.draw(screen)
