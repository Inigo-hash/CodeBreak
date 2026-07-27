import pygame

from .editor_theme import *


class ProblemPanel:

    def __init__(self, challenge):

        self.challenge = challenge

    def wrap_text(self, text, font, width):

        words = text.split()

        lines = []

        current = ""

        for word in words:

            test = current + word + " "

            if font.size(test)[0] < width:

                current = test

            else:

                lines.append(current)

                current = word + " "

        if current:

            lines.append(current)

        return lines

    def draw(self, screen):

        rect = pygame.Rect(
            0,
            TOP_BAR_HEIGHT,
            PROBLEM_PANEL_WIDTH,
            WINDOW_HEIGHT - TOP_BAR_HEIGHT
        )

        pygame.draw.rect(screen, PANEL_BG, rect)

        pygame.draw.line(
            screen,
            BORDER,
            (PROBLEM_PANEL_WIDTH, TOP_BAR_HEIGHT),
            (PROBLEM_PANEL_WIDTH, WINDOW_HEIGHT),
            2
        )

        x = 15
        y = TOP_BAR_HEIGHT + 15

        title = TITLE_FONT.render(
            self.challenge["title"],
            True,
            TEXT
        )

        screen.blit(title, (x, y))

        y += 40

        diff = HEADER_FONT.render(
            f'Difficulty: {self.challenge["difficulty"]}',
            True,
            TEXT_SECONDARY
        )

        screen.blit(diff, (x, y))

        y += 45

        lesson = HEADER_FONT.render(
            "Problem",
            True,
            TEXT
        )

        screen.blit(lesson, (x, y))

        y += 35

        wrapped = self.wrap_text(
            self.challenge["problem"],
            TEXT_FONT,
            PROBLEM_PANEL_WIDTH - 30
        )

        for line in wrapped:

            txt = TEXT_FONT.render(
                line,
                True,
                TEXT
            )

            screen.blit(txt, (x, y))

            y += LINE_HEIGHT