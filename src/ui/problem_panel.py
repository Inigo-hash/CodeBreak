"""
problem_panel.py

Displays the current coding challenge information.

Responsibilities:
- Draw the objective panel.
- Show the challenge title.
- Show the objective.
- Wrap long text so it fits the pane's width.
- Scroll when the text is taller than the pane.
- Reveal progressively stronger hints after unsuccessful submissions.

This class ONLY draws the problem information.
It never validates code and never decides layout - the renderer
tells it which rectangle to draw inside, and that rectangle can
change at any moment because the player can drag the divider
between the panes.
"""

import pygame

from src.ui.editor_theme import *
from src.ui.editor_widgets import VerticalScrollbar, wrap_text

# Every row carries its own height instead of sharing one fixed number.
# The panel mixes three faces - a big title, body copy and small grey
# labels - and forcing all of them into a single 24px slot was what made
# the title collide with the difficulty line underneath it.
def row_height(font):
    """Vertical space one line drawn in `font` needs."""

    return font.get_linesize() + 2


# Blank rows used purely as breathing room between sections.
GAP_SMALL = 6

GAP_MEDIUM = 12

GAP_LARGE = 20

# Space between the pane's edge and its text.
INNER_PADDING = 14

# Gap between the title strip and the first row of body text.
BODY_TOP_PADDING = 10

# Height of the fixed "OBJECTIVE" strip at the top of the pane.
TITLE_STRIP_HEIGHT = PANE_TITLE_HEIGHT
MAX_HINT_LEVEL = 4


DEFAULT_HINTS = {
    "print": (
        "Use Python's print() function.",
        "Put the requested message between quotation marks.",
        "The shape is print(\"message\"). Check spelling and punctuation.",
        "Copy the requested text exactly inside print(...).",
    ),
    "variable": (
        "A variable needs a name, an equals sign, and a value.",
        "Use the exact variable name shown in the objective.",
        "Numbers do not need quotation marks.",
        "Follow this shape: name = value, using the requested name and value.",
    ),
    "data_type": (
        "Create one clearly named variable on each line.",
        "Strings use quotes; integers and floats do not.",
        "Python booleans are written True and False with capital letters.",
        "Recheck every required name, type, and value against the problem.",
    ),
    "type_casting": (
        "Create the source text variable before converting it.",
        "int(), float(), and str() convert values to another type.",
        "Pass the source variable into the requested conversion function.",
        "Store the converted result in the exact target variable named above.",
    ),
    "input": (
        "input() reads one value supplied by the player.",
        "Store the result of input() in the requested variable.",
        "Put the exact requested prompt inside input(...).",
        "Use this shape: name = input(\"the exact prompt\").",
    ),
    "formatted_output": (
        "An f-string starts with the letter f before its opening quote.",
        "Put a variable inside braces to insert its value: {name}.",
        "Pass the complete f-string to print().",
        "Match the required prefix, variable, suffix, spaces, and punctuation exactly.",
    ),
    "operator": (
        "Use a Python arithmetic operator between two values.",
        "The + operator performs addition.",
        "Store the expression itself in the requested variable.",
        "Follow this shape: result = left_value + right_value.",
    ),
    "string": (
        "String values are surrounded by quotation marks.",
        "The + operator can join two strings.",
        "Keep required spaces inside one of the quoted pieces.",
        "Assign the complete joined string to the requested variable.",
    ),
    "conditional": (
        "Use if, elif, and else to choose between outcomes.",
        "Each condition ends with a colon and its body is indented.",
        "elif is attached to the first if; else has no condition.",
        "Assign the requested result in all three branches.",
    ),
    "boolean_logic": (
        "Boolean values are True or False.",
        "Use and when both conditions must be true.",
        "Use not to reverse a boolean value.",
        "Build the requested expression with both named variables, and, and not.",
    ),
}


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

        # One stronger hint unlocks after each failed Submit, capped at four.
        # Run-only errors do not advance this because they are not submissions.
        self.failure_count = 0
        self.hint_level = 0

    def hint_steps(self):
        """Return exactly four progressively stronger hints."""

        authored = self.challenge.get("hints") or ()
        if isinstance(authored, str):
            authored = (authored,)
        steps = [str(hint).strip() for hint in authored if str(hint).strip()]
        legacy_hint = self.challenge.get("hint")
        if legacy_hint and not steps:
            steps.append(str(legacy_hint).strip())
        fallbacks = DEFAULT_HINTS.get(
            self.challenge.get("type"),
            DEFAULT_HINTS["variable"],
        )
        for fallback in fallbacks:
            if len(steps) >= MAX_HINT_LEVEL:
                break
            if fallback not in steps:
                steps.append(fallback)
        while len(steps) < MAX_HINT_LEVEL:
            steps.append("Compare every name, value, and symbol with the objective.")
        return tuple(steps[:MAX_HINT_LEVEL])

    def record_failure(self):
        """Unlock the next hint and return its one-based level."""

        self.failure_count += 1
        self.hint_level = min(MAX_HINT_LEVEL, self.failure_count)
        self._wrapped_rows = []
        self._wrapped_width = None
        if self.rect:
            # Put the newly unlocked hint on screen immediately instead of
            # leaving it below the previous scroll position.
            self.scroll_offset = self.get_max_scroll_offset(self.rect)
        return self.hint_level

    # ---------------------------------------------------------
    # Content
    # ---------------------------------------------------------

    def _build_rows(self, max_width):
        """
        Turn the challenge into a flat list of drawable rows:

            (text, font, color, height)

        Each row is one line that already fits inside `max_width`, and
        each carries the vertical space it needs. Rows with empty text
        are pure spacers - that is how the sections are kept apart.
        """

        rows = []

        def line(text, font, color):
            rows.append((text, font, color, row_height(font)))

        def gap(height):
            rows.append(("", SMALL_FONT, SECONDARY_TEXT, height))

        def paragraph(text, font, color):
            for wrapped in wrap_text(text, font, max_width):
                line(wrapped, font, color)

        # --------------------------------------
        # Challenge Title
        # --------------------------------------

        paragraph(
            self.challenge.get("title", "Challenge"),
            HEADER_FONT,
            TEXT_COLOR
        )

        # --------------------------------------
        # Difficulty (optional)
        # --------------------------------------
        # Some challenges can be defined inline without a difficulty field,
        # so it is only drawn when it actually exists.

        difficulty = self.challenge.get("difficulty")

        if difficulty:
            gap(GAP_SMALL)
            line(str(difficulty).upper(), SMALL_FONT, SECONDARY_TEXT)

        gap(GAP_LARGE)

        # --------------------------------------
        # Problem
        # --------------------------------------

        problem = self.challenge.get("problem", "")

        if problem:

            line("PROBLEM", SMALL_FONT, SECONDARY_TEXT)

            gap(GAP_SMALL)

            for raw_line in problem.strip().splitlines():

                if not raw_line.strip():
                    gap(GAP_MEDIUM)
                    continue

                paragraph(raw_line, TEXT_FONT, TEXT_COLOR)

            gap(GAP_LARGE)

        # --------------------------------------
        # Objective
        # --------------------------------------

        line("OBJECTIVE", SMALL_FONT, SECONDARY_TEXT)

        gap(GAP_SMALL)

        paragraph(
            self.challenge.get("objective", ""),
            TEXT_FONT,
            TEXT_COLOR
        )

        gap(GAP_LARGE)

        # --------------------------------------
        # Hints
        # --------------------------------------
        # Every string here goes through wrap_text. The locked-hint
        # notice used to be appended raw, so it ran straight off the
        # side of the pane the moment the divider was dragged inward.

        if self.hint_level:

            line(
                f"HINT {self.hint_level} OF {MAX_HINT_LEVEL}",
                SMALL_FONT,
                SUCCESS_COLOR
            )

            gap(GAP_SMALL)

            paragraph(
                self.hint_steps()[self.hint_level - 1],
                TEXT_FONT,
                TEXT_COLOR
            )

            if self.hint_level < MAX_HINT_LEVEL:
                gap(GAP_MEDIUM)
                paragraph(
                    "Another failed SUBMIT reveals the next hint.",
                    SMALL_FONT,
                    SECONDARY_TEXT
                )

        else:

            paragraph(
                "Hints unlock after an unsuccessful SUBMIT.",
                SMALL_FONT,
                SECONDARY_TEXT
            )

        gap(GAP_MEDIUM)

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

    def _body_capacity(self, rect):
        """Pixels of vertical room the body has for text."""

        body = self.get_body_rect(rect)

        return max(0, body.height - BODY_TOP_PADDING - INNER_PADDING)

    def get_visible_rows(self, rect, start=None):
        """
        How many rows fit inside the pane when drawing begins at row
        `start`. Rows are different heights now, so this has to be
        measured rather than divided out.
        """

        if start is None:
            start = self.scroll_offset

        rows = self._rows_for_width(self._text_width(rect))

        capacity = self._body_capacity(rect)

        used = 0
        count = 0

        for _, _, _, height in rows[max(0, start):]:

            if used + height > capacity:
                break

            used += height
            count += 1

        return count

    def get_max_scroll_offset(self, rect):
        """
        The furthest down the panel can be scrolled: the first row that
        still leaves every remaining row on screen.
        """

        rows = self._rows_for_width(self._text_width(rect))

        capacity = self._body_capacity(rect)

        used = 0
        index = len(rows)

        while index > 0:

            height = rows[index - 1][3]

            if used + height > capacity:
                break

            used += height
            index -= 1

        return index

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

        # Centered in the strip rather than nailed to a fixed offset, so
        # the heading keeps its breathing room at any font size.
        screen.blit(
            label,
            (
                rect.x + INNER_PADDING,
                rect.y + (TITLE_STRIP_HEIGHT - label.get_height()) // 2
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

        self.clamp_scroll()

        visible_rows = self.get_visible_rows(rect)

        # Text is clipped to the body so a long word can never
        # spill over the divider into the code editor.
        previous_clip = screen.get_clip()

        screen.set_clip(body.clip(previous_clip) if previous_clip else body)

        y = body.y + BODY_TOP_PADDING

        for text, font, color, height in rows[
            self.scroll_offset:
            self.scroll_offset + visible_rows
        ]:

            if text:

                screen.blit(
                    font.render(text, True, color),
                    (rect.x + INNER_PADDING, y)
                )

            y += height

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
