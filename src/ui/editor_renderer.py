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

from src.ui.editor_theme import *


class EditorRenderer:
    """
    Responsible for drawing every visual part
    of the coding environment.
    """

    def __init__(self, screen, challenge, background=None):

        self.screen = screen
        self.challenge = challenge
        self.background = background  # snapshot of the game screen behind the popup

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
        """Draw the challenge objective panel."""

        pygame.draw.rect(
            self.screen,
            PANEL_COLOR,
            self.problem_rect,
            border_radius=PANEL_RADIUS
        )

        title = HEADER_FONT.render(
            "OBJECTIVE",
            True,
            TEXT_COLOR
        )

        self.screen.blit(
            title,
            (self.problem_rect.x + 15,
             self.problem_rect.y + 10)
        )

        objective = SMALL_FONT.render(
            self.challenge["objective"],
            True,
            SECONDARY_TEXT
        )

        self.screen.blit(
            objective,
            (self.problem_rect.x + 15,
             self.problem_rect.y + 50)
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

    def draw_output_panel(self):
        """Draw the output area."""

        pygame.draw.rect(
            self.screen,
            OUTPUT_COLOR,
            self.output_rect,
            border_radius=PANEL_RADIUS
        )

        title = HEADER_FONT.render(
            "OUTPUT",
            True,
            TEXT_COLOR
        )

        self.screen.blit(
            title,
            (
                self.output_rect.x + 15,
                self.output_rect.y + 10
            )
        )

        message = SMALL_FONT.render(
            "Waiting for execution...",
            True,
            SECONDARY_TEXT
        )

        self.screen.blit(
            message,
            (
                self.output_rect.x + 15,
                self.output_rect.y + 50
            )
        )

    def draw_button_panel(self):
        """Draw the bottom button area."""

        pygame.draw.rect(
            self.screen,
            PANEL_COLOR,
            self.button_rect,
            border_radius=PANEL_RADIUS
        )

        button_names = [
            "Run",
            "Submit",
            "Leave"
        ]

        spacing = 25

        total_width = (
            BUTTON_WIDTH * len(button_names)
        ) + (
            spacing * (len(button_names) - 1)
        )

        start_x = self.panel_rect.x + (
            PANEL_WIDTH - total_width
        ) // 2

        for index, text in enumerate(button_names):

            x = start_x + (
                index * (BUTTON_WIDTH + spacing)
            )

            button = pygame.Rect(
                x,
                self.button_rect.y + 5,
                BUTTON_WIDTH,
                BUTTON_HEIGHT - 10
            )

            pygame.draw.rect(
                self.screen,
                BUTTON_COLOR,
                button,
                border_radius=BUTTON_RADIUS
            )

            label = TEXT_FONT.render(
                text,
                True,
                TEXT_COLOR
            )

            self.screen.blit(
                label,
                label.get_rect(center=button.center)
            )