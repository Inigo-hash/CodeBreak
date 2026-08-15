"""
output_panel.py

Displays messages produced by the coding environment.

Responsibilities
----------------
- Display validation results
- Display syntax errors
- Display challenge completion messages
- Display general information
- Wrap long lines and scroll through long output

The output panel does NOT validate code.
It only displays messages.

It also never decides its own position or size: the renderer hands
it a rectangle every frame, and that rectangle changes whenever the
player drags the divider between the panes.
"""

import pygame

from src.ui.editor_theme import *
from src.ui.editor_widgets import VerticalScrollbar, wrap_text

# Height of one output line.
ROW_HEIGHT = 22

# Space between the pane's edge and its text.
INNER_PADDING = 14

# Height of the fixed "OUTPUT" strip at the top of the pane.
TITLE_STRIP_HEIGHT = 38


class OutputPanel:

    def __init__(self):

        # Each message is (text, color), so callers can show plain
        # info, printed output, success, and error lines all in
        # their own color.
        self.messages = [
            ("Waiting for execution...", SECONDARY_TEXT)
        ]

        # First wrapped line currently shown.
        self.scroll_offset = 0

        self.scrollbar = VerticalScrollbar()

        # Rectangle the panel was last drawn in.
        self.rect = None

        # Wrapped lines are cached and only rebuilt when either the
        # messages or the pane's width actually change.
        self._wrapped_rows = []
        self._wrapped_width = None
        self._wrapped_version = None

        # Bumped every time the messages change, so the cache above
        # knows it is stale.
        self._version = 0

    # ---------------------------------------------------------
    # Public Methods
    # ---------------------------------------------------------

    def clear(self):
        """
        Clears every output message.
        """

        self.messages = []

        # A fresh run starts reading from the first line again.
        self.scroll_offset = 0

        self._version += 1

    def add(self, message, color=None):
        """
        Adds a new message to the output panel.
        """

        self.messages.append((message, color or SECONDARY_TEXT))

        self._version += 1

    def set_message(self, message, color=None):
        """
        Replaces the output with a single message.
        """

        self.messages = [(message, color or SECONDARY_TEXT)]

        self.scroll_offset = 0

        self._version += 1

    # ---------------------------------------------------------
    # Content
    # ---------------------------------------------------------

    def _rows_for_width(self, max_width):
        """
        Return every message split into lines that fit the pane,
        rebuilding the cache only when something changed.
        """

        if (
            max_width != self._wrapped_width
            or self._version != self._wrapped_version
        ):

            rows = []

            for message, color in self.messages:

                for line in wrap_text(str(message), SMALL_FONT, max_width):
                    rows.append((line, color))

            self._wrapped_rows = rows
            self._wrapped_width = max_width
            self._wrapped_version = self._version

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
        """How many output lines fit inside the pane at once."""

        body = self.get_body_rect(rect)

        return max(
            0,
            (body.height - INNER_PADDING) // ROW_HEIGHT
        )

    def get_max_scroll_offset(self, rect):
        """The furthest down the output can be scrolled."""

        total_rows = len(self._rows_for_width(self._text_width(rect)))

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
        """Scroll by a number of lines (positive scrolls downward)."""

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
        strip the scrollbar sits in (always reserved, so text does
        not reflow the moment a scrollbar appears).
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

        self.rect = rect.copy()

        # Background
        pygame.draw.rect(
            screen,
            OUTPUT_COLOR,
            rect,
            border_radius=PANEL_RADIUS
        )

        # Border
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

        title = HEADER_FONT.render(
            "OUTPUT",
            True,
            TEXT_COLOR
        )

        screen.blit(
            title,
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
        # Scrollable Messages
        # --------------------------------------

        body = self.get_body_rect(rect)

        rows = self._rows_for_width(self._text_width(rect))

        visible_rows = self.get_visible_rows(rect)

        self.clamp_scroll()

        previous_clip = screen.get_clip()

        screen.set_clip(body.clip(previous_clip) if previous_clip else body)

        y = body.y + 6

        for text, color in rows[
            self.scroll_offset:
            self.scroll_offset + visible_rows
        ]:

            if text:

                screen.blit(
                    SMALL_FONT.render(text, True, color),
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
