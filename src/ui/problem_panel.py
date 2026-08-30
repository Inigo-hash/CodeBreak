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

# Height of one line of body text. Every row uses the same height,
# which is what lets the scrollbar treat the content as a simple
# list of lines regardless of which font each row uses.
ROW_HEIGHT = 24

# Space between the pane's edge and its text.
INNER_PADDING = 14

# Height of the fixed "OBJECTIVE" strip at the top of the pane.
TITLE_STRIP_HEIGHT = 38
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
        # Some challenges can be defined inline without a difficulty field,
        # so it is only drawn when it actually exists.

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

        rows.append(("", SMALL_FONT, SECONDARY_TEXT))
        if self.hint_level:
            hint = self.hint_steps()[self.hint_level - 1]
            rows.append((
                f"HINT {self.hint_level} OF {MAX_HINT_LEVEL}",
                SMALL_FONT,
                SUCCESS_COLOR,
            ))
            for line in wrap_text(hint, SMALL_FONT, max_width):
                rows.append((line, SMALL_FONT, SECONDARY_TEXT))
            if self.hint_level < MAX_HINT_LEVEL:
                rows.append((
                    "Another failed SUBMIT reveals the next hint.",
                    SMALL_FONT,
                    SECONDARY_TEXT,
                ))
        else:
            rows.append((
                "Hints unlock after an unsuccessful SUBMIT.",
                SMALL_FONT,
                SECONDARY_TEXT,
            ))
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
