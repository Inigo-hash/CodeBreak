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

        # Each message is (text, color), so callers can show plain
        # info, printed output, success, and error lines all in
        # their own color.
        self.messages = [
            ("Waiting for execution...", SECONDARY_TEXT)
        ]

    # ---------------------------------------------------------
    # Public Methods
    # ---------------------------------------------------------

    def clear(self):
        """
        Clears every output message.
        """

        self.messages = []

    def add(self, message, color=None):
        """
        Adds a new message to the output panel.
        """

        self.messages.append((message, color or SECONDARY_TEXT))

    def set_message(self, message, color=None):
        """
        Replaces the output with a single message.
        """

        self.messages = [(message, color or SECONDARY_TEXT)]

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

        for message, color in self.messages[-5:]:

            text = SMALL_FONT.render(
                message,
                True,
                color
            )

            screen.blit(
                text,
                (
                    rect.x + 15,
                    y
                )
            )

            y += 22