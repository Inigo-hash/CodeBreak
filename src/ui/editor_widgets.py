"""
editor_widgets.py

Reusable UI widgets for the CodeBreak project.

Currently contains:
- Button
- VerticalScrollbar
- wrap_text()

Future widgets:
- TextBox
- CheckBox
- ProgressBar
"""

import pygame

from src.ui.editor_theme import *


class Button:
    """
    Reusable button for the game's user interface.

    Responsibilities
    ----------------
    - Draw itself.
    - Detect mouse hovering.
    - Detect mouse clicks.

    The button does NOT perform any action itself.
    CodeEditor decides what happens when the button is clicked.
    """

    def __init__(self, x, y, width, height, text, variant="secondary"):

        self.rect = pygame.Rect(
            x,
            y,
            width,
            height
        )

        self.text = text
        self.variant = variant

        self.hovered = False

    # -------------------------------------------------
    # Draw
    # -------------------------------------------------

    def draw(self, screen):

        if self.variant == "primary":
            base = pygame.Color(SUCCESS_COLOR)
            color = tuple(min(255, channel + (28 if self.hovered else 0))
                          for channel in base[:3])
            border = tuple(min(255, channel + 45) for channel in base[:3])
        elif self.variant == "tertiary":
            color = BUTTON_COLOR if self.hovered else HEADER_COLOR
            border = BUTTON_HOVER_COLOR if self.hovered else BORDER_COLOR
        else:
            color = BUTTON_HOVER_COLOR if self.hovered else BUTTON_COLOR
            border = BORDER_COLOR

        # Small shadow and top highlight make the action hierarchy readable
        # without relying on color alone.
        pygame.draw.rect(
            screen, (10, 12, 18), self.rect.move(0, 3),
            border_radius=BUTTON_RADIUS
        )

        pygame.draw.rect(
            screen,
            color,
            self.rect,
            border_radius=BUTTON_RADIUS
        )

        pygame.draw.rect(
            screen,
            border,
            self.rect,
            2,
            border_radius=BUTTON_RADIUS
        )

        pygame.draw.line(
            screen, tuple(min(255, channel + 35) for channel in color[:3]),
            (self.rect.left + 8, self.rect.top + 3),
            (self.rect.right - 8, self.rect.top + 3), 1
        )

        label = BUTTON_FONT.render(
            self.text,
            True,
            BUTTON_TEXT_COLOR
        )

        screen.blit(
            label,
            label.get_rect(center=self.rect.center)
        )

    # -------------------------------------------------
    # Update Hover State
    # -------------------------------------------------

    def update(self):

        mouse_position = pygame.mouse.get_pos()

        self.hovered = self.rect.collidepoint(
            mouse_position
        )

    # -------------------------------------------------
    # Click Detection
    # -------------------------------------------------

    def is_clicked(self, event):

        if event.type != pygame.MOUSEBUTTONDOWN:
            return False

        if event.button != 1:
            return False

        return self.rect.collidepoint(event.pos)


class VerticalScrollbar:
    """
    A vertical scrollbar shared by every scrollable pane of the
    coding environment (objective, code editor, output).

    Responsibilities
    ----------------
    - Work out where the track and thumb belong.
    - Draw itself.
    - Answer "did the mouse hit me?".
    - Convert a mouse Y position into a scroll offset.

    It deliberately stores NO scroll state of its own. Each pane
    keeps its own scroll offset and simply hands the current
    numbers over on every frame - that way the scrollbar can never
    drift out of sync with what is actually drawn.

    Everything is measured in *lines*, not pixels, because all three
    panes draw evenly spaced lines of text.
    """

    def __init__(self, width=SCROLLBAR_WIDTH, margin=SCROLLBAR_MARGIN):

        self.width = width

        self.margin = margin

        # Both stay None while the content fits and no
        # scrollbar is needed.
        self.track_rect = None

        self.thumb_rect = None

    # -------------------------------------------------
    # Geometry
    # -------------------------------------------------

    def update(self, area_rect, total_lines, visible_lines, scroll_offset):
        """
        Recalculate the track and thumb for the current content.

        Parameters
        ----------
        area_rect : pygame.Rect
            The pane the scrollbar belongs to.

        total_lines : int
            How many lines the content has in total.

        visible_lines : int
            How many of those lines fit on screen at once.

        scroll_offset : int
            The first line currently shown.
        """

        # Nothing to scroll - hide the scrollbar entirely.
        if visible_lines <= 0 or total_lines <= visible_lines:

            self.track_rect = None
            self.thumb_rect = None

            return

        self.track_rect = pygame.Rect(
            area_rect.right - self.width - self.margin,
            area_rect.y + self.margin,
            self.width,
            area_rect.height - (self.margin * 2)
        )

        # A smaller thumb means more content is hidden.
        thumb_height = max(
            SCROLLBAR_MIN_THUMB,
            int(
                self.track_rect.height
                * (visible_lines / total_lines)
            )
        )

        max_scroll_offset = total_lines - visible_lines

        scroll_ratio = (
            scroll_offset / max_scroll_offset
            if max_scroll_offset > 0
            else 0
        )

        # Keep the thumb inside the track even if the caller
        # hands over a slightly out-of-range offset.
        scroll_ratio = max(0.0, min(1.0, scroll_ratio))

        thumb_y = (
            self.track_rect.y
            + int(
                (self.track_rect.height - thumb_height)
                * scroll_ratio
            )
        )

        self.thumb_rect = pygame.Rect(
            self.track_rect.x,
            thumb_y,
            self.width,
            thumb_height
        )

    # -------------------------------------------------
    # Draw
    # -------------------------------------------------

    def draw(self, screen):

        if not self.track_rect:
            return

        pygame.draw.rect(
            screen,
            SCROLLBAR_TRACK_COLOR,
            self.track_rect,
            border_radius=self.width // 2
        )

        pygame.draw.rect(
            screen,
            SCROLLBAR_THUMB_COLOR,
            self.thumb_rect,
            border_radius=self.width // 2
        )

    # -------------------------------------------------
    # Mouse Interaction
    # -------------------------------------------------

    def hit_thumb(self, position):
        """True if the given point is on the draggable thumb."""

        return bool(
            self.thumb_rect
            and self.thumb_rect.collidepoint(position)
        )

    def hit_track(self, position):
        """True if the given point is on the track (but not the thumb)."""

        return bool(
            self.track_rect
            and self.track_rect.collidepoint(position)
        )

    def offset_from_mouse_y(self, mouse_y, max_scroll_offset):
        """
        Convert a mouse Y position on the track into a scroll offset.

        Returns the current offset unchanged (0) when there is
        nothing to scroll.
        """

        if not self.track_rect or max_scroll_offset <= 0:
            return 0

        relative_y = mouse_y - self.track_rect.y

        ratio = relative_y / self.track_rect.height

        ratio = max(0.0, min(1.0, ratio))

        return int(max_scroll_offset * ratio)


# =====================================================
# Text Helpers
# =====================================================

def wrap_text(text, font, max_width):
    """
    Break `text` into a list of lines that each fit within
    `max_width` pixels when rendered with `font`.

    Wrapping happens at spaces where possible. A single "word" too
    long to fit on its own line (a long error message with no
    spaces, say) is split mid-word rather than allowed to overflow
    the pane.

    Existing newlines in the text are preserved as line breaks.
    """

    # A pane too narrow to fit anything - return the text as-is
    # rather than looping forever trying to break it up.
    if max_width <= 0:
        return [text]

    lines = []

    for paragraph in text.split("\n"):

        # Preserve deliberate blank lines.
        if not paragraph:
            lines.append("")
            continue

        current = ""

        for word in paragraph.split(" "):

            candidate = word if not current else current + " " + word

            # The word still fits on the current line.
            if font.size(candidate)[0] <= max_width:
                current = candidate
                continue

            # It does not fit, so the line ends here.
            if current:
                lines.append(current)
                current = ""

            # The word alone is wider than the pane - chop it into
            # pieces that do fit, one line at a time.
            while font.size(word)[0] > max_width:

                cut = 1

                while (
                    cut < len(word)
                    and font.size(word[:cut + 1])[0] <= max_width
                ):
                    cut += 1

                lines.append(word[:cut])

                word = word[cut:]

            current = word

        lines.append(current)

    return lines
