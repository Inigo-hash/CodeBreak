"""
editor_widgets.py

Reusable UI widgets for the CodeBreak project.

Currently contains:
- Button

Future widgets:
- TextBox
- ScrollBar
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

    def __init__(self, x, y, width, height, text):

        self.rect = pygame.Rect(
            x,
            y,
            width,
            height
        )

        self.text = text

        self.hovered = False

    # -------------------------------------------------
    # Draw
    # -------------------------------------------------

    def draw(self, screen):

        color = BUTTON_HOVER_COLOR if self.hovered else BUTTON_COLOR

        pygame.draw.rect(
            screen,
            color,
            self.rect,
            border_radius=BUTTON_RADIUS
        )

        pygame.draw.rect(
            screen,
            BORDER_COLOR,
            self.rect,
            2,
            border_radius=BUTTON_RADIUS
        )

        label = TEXT_FONT.render(
            self.text,
            True,
            TEXT_COLOR
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