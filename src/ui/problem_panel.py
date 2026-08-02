"""
problem_panel.py

Displays the current coding challenge information.

Responsibilities:
- Draw the objective panel.
- Show the challenge title.
- Show the objective.
- (Future) Show hints and difficulty.

This class ONLY draws the problem information.
"""

import pygame

from src.ui.editor_theme import *


class ProblemPanel:

    def __init__(self, challenge):

        self.challenge = challenge

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
        # Title
        # --------------------------------------

        title = HEADER_FONT.render(
            self.challenge["title"],
            True,
            TEXT_COLOR
        )

        screen.blit(
            title,
            (
                rect.x + 15,
                rect.y + 12
            )
        )

        # --------------------------------------
        # Objective Label
        # --------------------------------------

        objective_label = SMALL_FONT.render(
            "Objective",
            True,
            SECONDARY_TEXT
        )

        screen.blit(
            objective_label,
            (
                rect.x + 15,
                rect.y + 48
            )
        )

        # --------------------------------------
        # Objective Text
        # --------------------------------------

        objective = TEXT_FONT.render(
            self.challenge["objective"],
            True,
            TEXT_COLOR
        )

        screen.blit(
            objective,
            (
                rect.x + 15,
                rect.y + 72
            )
        )