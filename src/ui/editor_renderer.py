"""
editor_renderer.py

Draws the entire CodeBreak coding environment.

Responsibilities:
- Draw background
- Draw header
- Draw objective panel
- Draw code editor panel
- Draw output panel
- Draw button area

This class ONLY draws.
It does not handle typing, validation, or game logic.
"""

import pygame

from src.ui.editor_widgets import Button
from src.ui.output_panel import OutputPanel
from src.ui.problem_panel import ProblemPanel
from src.ui.editor_theme import *

SCROLLBAR_WIDTH = 8
SCROLLBAR_MARGIN = 4

class EditorRenderer:
    """
    Responsible for drawing every visual part
    of the coding environment.
    """

    def __init__(self, screen, challenge, text_buffer, background=None):

        self.screen = screen
        self.challenge = challenge
        self.text_buffer = text_buffer
        self.background = background
        self.last_input_time = 0
        self.scroll_offset = 0

        # UI Components
        self.problem_panel = ProblemPanel(challenge)
        self.output_panel = OutputPanel()

        # ----------------------------------
        # Popup Panel Rect (centered, medium-sized)
        # ----------------------------------

        self.panel_rect = pygame.Rect(0, 0, PANEL_WIDTH, PANEL_HEIGHT)
        self.panel_rect.center = self.screen.get_rect().center

        # ----------------------------------
        # Layout Rectangles (relative to panel, not the whole screen)
        # ----------------------------------

        self.header_rect = pygame.Rect(
            self.panel_rect.x + PADDING,
            self.panel_rect.y + PADDING,
            PANEL_WIDTH - (PADDING * 2),
            HEADER_HEIGHT
        )

        self.problem_rect = pygame.Rect(
            self.panel_rect.x + PADDING,
            self.header_rect.bottom + PADDING,
            PANEL_WIDTH - (PADDING * 2),
            OBJECTIVE_HEIGHT
        )

        self.editor_rect = pygame.Rect(
            self.panel_rect.x + PADDING,
            self.problem_rect.bottom + PADDING,
            PANEL_WIDTH - (PADDING * 2),
            EDITOR_HEIGHT
        )

        self.output_rect = pygame.Rect(
            self.panel_rect.x + PADDING,
            self.editor_rect.bottom + PADDING,
            PANEL_WIDTH - (PADDING * 2),
            OUTPUT_HEIGHT
        )

        self.button_rect = pygame.Rect(
            self.panel_rect.x + PADDING,
            self.output_rect.bottom + PADDING,
            PANEL_WIDTH - (PADDING * 2),
            BUTTON_HEIGHT
        )

        # ----------------------------------
        # Buttons
        # ----------------------------------

        spacing = 25

        total_width = (BUTTON_WIDTH * 3) + (spacing * 2)

        start_x = self.panel_rect.x + (
            PANEL_WIDTH - total_width
        ) // 2

        self.run_button = Button(
            start_x,
            self.button_rect.y + 5,
            BUTTON_WIDTH,
            BUTTON_HEIGHT - 10,
            "Run"
        )

        self.submit_button = Button(
            start_x + BUTTON_WIDTH + spacing,
            self.button_rect.y + 5,
            BUTTON_WIDTH,
            BUTTON_HEIGHT - 10,
            "Submit"
        )

        self.leave_button = Button(
            start_x + (BUTTON_WIDTH + spacing) * 2,
            self.button_rect.y + 5,
            BUTTON_WIDTH,
            BUTTON_HEIGHT - 10,
            "Leave"
        )

        self.scrollbar_track_rect = None
        self.scrollbar_thumb_rect = None
    # ==================================================
    # Public Draw Function
    # ==================================================

    def draw(self):

        self.draw_background()

        self.draw_panel_frame()

        self.draw_header()

        self.draw_problem_panel()

        self.draw_editor_panel()

        self.draw_output_panel()

        self.draw_button_panel()

    # ==================================================
    # Individual Sections
    # ==================================================

    def draw_background(self):
        """Draw the dimmed game screen behind the popup."""

        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(BACKGROUND_COLOR)

        # Dark translucent overlay so the popup reads as a popup
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

    def draw_panel_frame(self):
        """Draw the popup panel itself, behind all the sections."""

        pygame.draw.rect(
            self.screen,
            BACKGROUND_COLOR,
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

    def draw_header(self):
        """Draw the title bar."""

        pygame.draw.rect(
            self.screen,
            HEADER_COLOR,
            self.header_rect,
            border_radius=PANEL_RADIUS
        )

        title = TITLE_FONT.render(
            f'CodeBreak - {self.challenge["title"]}',
            True,
            TEXT_COLOR
        )

        self.screen.blit(
            title,
            (self.header_rect.x + 20,
             self.header_rect.y + 15)
        )

    def draw_problem_panel(self):

        self.problem_panel.draw(
            self.screen,
            self.problem_rect
        )

    def draw_editor_panel(self):
        """Draw the code editor with automatic vertical scrolling."""

        pygame.draw.rect(
            self.screen,
            EDITOR_COLOR,
            self.editor_rect,
            border_radius=PANEL_RADIUS
        )

        # ----------------------------------
        # Editor Settings
        # ----------------------------------

        line_spacing = 20

        max_visible_lines = (
            self.editor_rect.height - 30
        ) // line_spacing

        # ----------------------------------
        # Clamp scroll to valid range (does NOT force-follow cursor)
        # ----------------------------------

        self.clamp_scroll_offset()

        # ----------------------------------
        # Draw Line Numbers
        # ----------------------------------

        visible_lines = self.text_buffer.lines[
            self.scroll_offset:
            self.scroll_offset + max_visible_lines
        ]

        for i in range(len(visible_lines)):

            line_number = self.scroll_offset + i + 1

            number = SMALL_FONT.render(
                str(line_number),
                True,
                SECONDARY_TEXT
            )

            self.screen.blit(
                number,
                (
                    self.editor_rect.x + 12,
                    self.editor_rect.y + 15 + (i * line_spacing)
                )
            )

        # ----------------------------------
        # Divider
        # ----------------------------------

        pygame.draw.line(
            self.screen,
            BORDER_COLOR,
            (
                self.editor_rect.x + LINE_NUMBER_WIDTH,
                self.editor_rect.y
            ),
            (
                self.editor_rect.x + LINE_NUMBER_WIDTH,
                self.editor_rect.bottom
            ),
            2
        )

        # ----------------------------------
        # Draw Selection Highlight
        # ----------------------------------
        # Drawn before the text so highlighted characters
        # remain fully readable on top of the highlight.

        self.draw_selection()
        
        # ----------------------------------
        # Draw User Code
        # ----------------------------------

        text_x = (
            self.editor_rect.x
            + LINE_NUMBER_WIDTH
            + 15
        )

        text_y = self.editor_rect.y + 15

        for line in visible_lines:

            rendered = TEXT_FONT.render(
                line,
                True,
                TEXT_COLOR
            )

            self.screen.blit(
                rendered,
                (text_x, text_y)
            )

            text_y += line_spacing

        # ----------------------------------
        # Draw Cursor
        # ----------------------------------

        current_line = self.text_buffer.lines[
            self.text_buffer.cursor_row
        ]

        text_before_cursor = current_line[
            :self.text_buffer.cursor_col
        ]

        cursor_x = (
            self.editor_rect.x
            + LINE_NUMBER_WIDTH
            + 15
            + TEXT_FONT.size(text_before_cursor)[0]
        )

        # Convert actual cursor row into visible row
        visible_cursor_row = (
            self.text_buffer.cursor_row
            - self.scroll_offset
        )

        cursor_y = (
            self.editor_rect.y
            + 15
            + visible_cursor_row * line_spacing
        )

        # ----------------------------------
        # Blinking Cursor
        # ----------------------------------

        current_time = pygame.time.get_ticks()

        if current_time - self.last_input_time < 500:
            show_cursor = True
        else:
            show_cursor = (current_time // 500) % 2 == 0

        if (
            show_cursor
            and 0 <= visible_cursor_row < max_visible_lines
        ):
            pygame.draw.line(
                self.screen,
                TEXT_COLOR,
                (cursor_x, cursor_y),
                (cursor_x, cursor_y + 18),
                2
            )

        self.draw_scrollbar()

    # ==========================================================
    # Selection Highlight
    # ==========================================================

    def draw_selection(self):
        """
        Draws a translucent highlight rectangle behind every
        selected character, one row at a time. Only draws over
        rows that are currently scrolled into view.
        """

        if not self.text_buffer.has_selection():
            return

        start_row, start_col, end_row, end_col = (
            self.text_buffer.get_selection_range()
        )

        line_spacing = 20
        max_visible_lines = self.get_max_visible_lines()

        text_x = self.editor_rect.x + LINE_NUMBER_WIDTH + 15
        text_y = self.editor_rect.y + 15

        # Only rows within this range are actually drawn on screen.
        first_visible_row = self.scroll_offset
        last_visible_row = self.scroll_offset + max_visible_lines - 1

        # Walk through every line the selection touches.
        for row in range(start_row, end_row + 1):

            # Skip rows that are scrolled out of view -
            # no point highlighting something that isn't drawn.
            if row < first_visible_row or row > last_visible_row:
                continue

            line = self.text_buffer.lines[row]

            # The first and last selected lines are only
            # partially highlighted; lines in between are
            # highlighted in full.
            col_start = start_col if row == start_row else 0
            col_end = end_col if row == end_row else len(line)

            # Measure pixel positions using the font, so the
            # highlight lines up exactly with the rendered text.
            x_start = text_x + TEXT_FONT.size(line[:col_start])[0]
            x_end = text_x + TEXT_FONT.size(line[:col_end])[0]

            # Guarantee a minimum width so an empty selected
            # line (e.g. a fully selected blank line) still
            # shows a visible highlight sliver.
            width = max(4, x_end - x_start)

            row_in_view = row - self.scroll_offset

            highlight_rect = pygame.Rect(
                x_start,
                text_y + (row_in_view * line_spacing),
                width,
                18
            )

            # Use a separate surface with per-pixel alpha so the
            # highlight can be semi-transparent over the code.
            highlight_surface = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
            highlight_surface.fill((100, 150, 255, 90))

            self.screen.blit(highlight_surface, highlight_rect.topleft)

    def draw_output_panel(self):
        """Draw the output panel."""

        self.output_panel.draw(
            self.screen,
            self.output_rect
        )


    # ==========================================================
    # Scrolling Helpers
    # ==========================================================

    def get_max_visible_lines(self):
        """Calculate how many code lines can fit inside the editor."""

        line_spacing = 20

        return (
            self.editor_rect.height - 30
        ) // line_spacing


    def get_max_scroll_offset(self):
        """Calculate the furthest position the editor can scroll down."""

        max_visible_lines = self.get_max_visible_lines()

        return max(
            0,
            len(self.text_buffer.lines) - max_visible_lines
        )


    def clamp_scroll_offset(self):
        """Keep the scroll position within the valid range."""

        self.scroll_offset = max(
            0,
            min(
                self.scroll_offset,
                self.get_max_scroll_offset()
            )
        )


    def ensure_cursor_visible(self):
        """
        Automatically scroll the editor when the cursor
        moves outside the currently visible lines.
        """

        max_visible_lines = self.get_max_visible_lines()
        cursor_row = self.text_buffer.cursor_row

        # Cursor moved above the visible area.
        if cursor_row < self.scroll_offset:

            self.scroll_offset = cursor_row

        # Cursor moved below the visible area.
        elif cursor_row >= self.scroll_offset + max_visible_lines:

            self.scroll_offset = (
                cursor_row
                - max_visible_lines
                + 1
            )

        # Make sure the new scroll position is valid.
        self.clamp_scroll_offset()


    # ==========================================================
    # Mouse Cursor Position
    # ==========================================================

    def get_cursor_position_from_mouse(self, mouse_pos):
        """
        Convert a mouse click inside the editor
        into a text buffer row and column.
        """

        mouse_x, mouse_y = mouse_pos

        line_spacing = 20
        max_visible_lines = self.get_max_visible_lines()

        text_x = (
            self.editor_rect.x
            + LINE_NUMBER_WIDTH
            + 15
        )

        text_y = self.editor_rect.y + 15

        # ----------------------------------
        # Determine Which Line Was Clicked
        # ----------------------------------

        # Calculate the line position relative
        # to the visible editor area.
        row_in_view = (
            mouse_y - text_y
        ) // line_spacing

        row_in_view = max(
            0,
            min(
                row_in_view,
                max_visible_lines - 1
            )
        )

        # Convert the visible line position
        # into the actual line in the text buffer.
        row = self.scroll_offset + row_in_view

        row = max(
            0,
            min(
                row,
                len(self.text_buffer.lines) - 1
            )
        )

        line = self.text_buffer.lines[row]

        # ----------------------------------
        # Determine Which Column Was Clicked
        # ----------------------------------

        relative_x = mouse_x - text_x

        # Default to the end of the line.
        col = len(line)

        # Compare the mouse position with the
        # width of each section of the text.
        for i in range(len(line) + 1):

            width = TEXT_FONT.size(line[:i])[0]

            if width > relative_x:

                col = i - 1
                break

        # Keep the column within the valid range.
        col = max(
            0,
            min(col, len(line))
        )

        return row, col


    # ==========================================================
    # Scrollbar
    # ==========================================================

    def set_scroll_from_mouse_y(self, mouse_y):
        """Set the scroll position based on the mouse Y position."""

        # No scrollbar means there is nothing to scroll.
        if not self.scrollbar_track_rect:
            return

        max_scroll_offset = self.get_max_scroll_offset()

        # No scrolling is needed if all lines are visible.
        if max_scroll_offset == 0:
            return

        # Convert the mouse position into a position
        # relative to the scrollbar track.
        relative_y = (
            mouse_y
            - self.scrollbar_track_rect.y
        )

        # Convert the position into a 0.0 - 1.0 ratio.
        ratio = (
            relative_y
            / self.scrollbar_track_rect.height
        )

        ratio = max(
            0,
            min(1, ratio)
        )

        # Convert the ratio into an actual line offset.
        self.scroll_offset = int(
            max_scroll_offset * ratio
        )

        self.clamp_scroll_offset()


    def draw_scrollbar(self):
        """Draw the editor scrollbar and draggable thumb."""

        max_visible_lines = self.get_max_visible_lines()
        total_lines = len(self.text_buffer.lines)

        # Hide the scrollbar when all lines fit
        # inside the editor.
        if total_lines <= max_visible_lines:

            self.scrollbar_track_rect = None
            self.scrollbar_thumb_rect = None

            return

        # ----------------------------------
        # Scrollbar Track
        # ----------------------------------

        track_rect = pygame.Rect(
            self.editor_rect.right
            - SCROLLBAR_WIDTH
            - SCROLLBAR_MARGIN,

            self.editor_rect.y
            + SCROLLBAR_MARGIN,

            SCROLLBAR_WIDTH,

            self.editor_rect.height
            - (SCROLLBAR_MARGIN * 2)
        )

        pygame.draw.rect(
            self.screen,
            BORDER_COLOR,
            track_rect,
            border_radius=SCROLLBAR_WIDTH // 2
        )

        # ----------------------------------
        # Scrollbar Thumb
        # ----------------------------------

        max_scroll_offset = self.get_max_scroll_offset()

        # Make the thumb smaller when there are
        # more lines than can fit on screen.
        thumb_height = max(
            20,
            int(
                track_rect.height
                * (max_visible_lines / total_lines)
            )
        )

        # Determine the thumb's position based
        # on the current scroll position.
        scroll_ratio = (
            self.scroll_offset / max_scroll_offset
            if max_scroll_offset > 0
            else 0
        )

        thumb_y = (
            track_rect.y
            + int(
                (track_rect.height - thumb_height)
                * scroll_ratio
            )
        )

        thumb_rect = pygame.Rect(
            track_rect.x,
            thumb_y,
            SCROLLBAR_WIDTH,
            thumb_height
        )

        pygame.draw.rect(
            self.screen,
            TEXT_COLOR,
            thumb_rect,
            border_radius=SCROLLBAR_WIDTH // 2
        )

        # Store the rectangles so CodeEditor
        # can detect mouse interaction with them.
        self.scrollbar_track_rect = track_rect
        self.scrollbar_thumb_rect = thumb_rect


    # ==========================================================
    # Button Panel
    # ==========================================================

    def draw_button_panel(self):
        """Draw the buttons at the bottom of the editor."""

        pygame.draw.rect(
            self.screen,
            PANEL_COLOR,
            self.button_rect,
            border_radius=PANEL_RADIUS
        )

        self.run_button.update()
        self.submit_button.update()
        self.leave_button.update()

        self.run_button.draw(self.screen)
        self.submit_button.draw(self.screen)
        self.leave_button.draw(self.screen)


    # ==========================================================
    # Component Getters
    # ==========================================================

    def get_output_panel(self):
        """Return the output panel."""

        return self.output_panel


    def get_run_button(self):
        """Return the Run button."""

        return self.run_button


    def get_submit_button(self):
        """Return the Submit button."""

        return self.submit_button


    def get_leave_button(self):
        """Return the Leave button."""

        return self.leave_button
    