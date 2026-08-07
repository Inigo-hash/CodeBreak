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
        """Draw the code editor."""

        pygame.draw.rect(
            self.screen,
            EDITOR_COLOR,
            self.editor_rect,
            border_radius=PANEL_RADIUS
        )

        # Draw line numbers
        for i in range(10):

            number = SMALL_FONT.render(
                str(i + 1),
                True,
                SECONDARY_TEXT
            )

            self.screen.blit(
                number,
                (
                    self.editor_rect.x + 12,
                    self.editor_rect.y + 15 + (i * 20)
                )
            )

        # Divider between line numbers and code area
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
        # Draw User Code
        # ----------------------------------

        text_x = self.editor_rect.x + LINE_NUMBER_WIDTH + 15
        text_y = self.editor_rect.y + 15

        line_spacing = 20

        for line in self.text_buffer.lines:

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

        current_line = self.text_buffer.lines[self.text_buffer.cursor_row]

        text_before_cursor = current_line[:self.text_buffer.cursor_col]

        cursor_x = (
            self.editor_rect.x
            + LINE_NUMBER_WIDTH
            + 15
            + TEXT_FONT.size(text_before_cursor)[0]
        )

        cursor_y = (
            self.editor_rect.y
            + 15
            + self.text_buffer.cursor_row * line_spacing
        )

        # ----------------------------------
        # Draw Blinking Cursor
        # ----------------------------------
        current_time = pygame.time.get_ticks()

        # Stay solid for 500 ms after any keyboard input.
        if current_time - self.last_input_time < 500:
            show_cursor = True
        else:
            show_cursor = (current_time // 500) % 2 == 0

        if show_cursor:
            pygame.draw.line(
                self.screen,
                TEXT_COLOR,
                (cursor_x, cursor_y),
                (cursor_x, cursor_y + 18),
                2
            )

    def draw_output_panel(self):

        self.output_panel.draw(
            self.screen,
            self.output_rect
        )

    def draw_button_panel(self):
        """Draw the bottom button area."""

        pygame.draw.rect(
            self.screen,
            PANEL_COLOR,
            self.button_rect,
            border_radius=PANEL_RADIUS
        )

    def draw_button_panel(self):
        """Draw the bottom button area."""

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


    def get_output_panel(self):
        return self.output_panel
    
    def get_run_button(self):
        return self.run_button


    def get_submit_button(self):
        return self.submit_button


    def get_leave_button(self):
        return self.leave_button
    