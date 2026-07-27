import pygame

from .editor_theme import *


class OutputPanel:

    def __init__(self):

        self.lines = []

    def clear(self):

        self.lines.clear()

    def add(self, message):

        self.lines.append(message)

        if len(self.lines) > 7:

            self.lines.pop(0)

    def draw(self, screen):

        rect = pygame.Rect(

            PROBLEM_PANEL_WIDTH,

            WINDOW_HEIGHT - OUTPUT_HEIGHT,

            WINDOW_WIDTH - PROBLEM_PANEL_WIDTH,

            OUTPUT_HEIGHT

        )

        pygame.draw.rect(

            screen,

            OUTPUT_BG,

            rect

        )

        pygame.draw.line(

            screen,

            BORDER,

            (PROBLEM_PANEL_WIDTH,
             WINDOW_HEIGHT - OUTPUT_HEIGHT),

            (WINDOW_WIDTH,
             WINDOW_HEIGHT - OUTPUT_HEIGHT),

            2

        )

        title = HEADER_FONT.render(

            "Output",

            True,

            TEXT

        )

        screen.blit(

            title,

            (PROBLEM_PANEL_WIDTH + 15,
             WINDOW_HEIGHT - OUTPUT_HEIGHT + 10)

        )

        y = WINDOW_HEIGHT - OUTPUT_HEIGHT + 45

        for line in self.lines:

            txt = OUTPUT_FONT.render(

                line,

                True,

                TEXT

            )

            screen.blit(

                txt,

                (PROBLEM_PANEL_WIDTH + 20, y)

            )

            y += 24