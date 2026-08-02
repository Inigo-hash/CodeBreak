"""
output_panel.py

Displays messages produced by the coding environment.

Responsibilities
----------------
- Display validation results
- Display syntax errors
- Display challenge completion messages
- Display general information

The output panel does NOT validate code.
It only displays messages.
"""

import pygame

from src.ui.editor_theme import *


class OutputPanel:

    def __init__(self):

        # Default message shown when opening the editor.
        self.messages = [
            "Waiting for execution..."
        ]

    # ---------------------------------------------------------
    # Public Methods
    # ---------------------------------------------------------

    def clear(self):
        """
        Clears every output message.
        """

        self.messages.clear()

    def add(self, message):
        """
        Adds a new message to the output panel.
        """

        self.messages.append(message)

    def set_message(self, message):
        """
        Replaces the output with a single message.
        """

        self.messages = [message]

    # ---------------------------------------------------------
    # Draw
    # ---------------------------------------------------------

    def draw(self, screen, rect):

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

        # Header
        title = HEADER_FONT.render(
            "OUTPUT",
            True,
            TEXT_COLOR
        )

        screen.blit(
            title,
            (
                rect.x + 15,
                rect.y + 10
            )
        )

        # Draw messages
        y = rect.y + 45

        for message in self.messages[-5:]:

            text = SMALL_FONT.render(
                message,
                True,
                SECONDARY_TEXT
            )

            screen.blit(
                text,
                (
                    rect.x + 15,
                    y
                )
            )

            y += 22