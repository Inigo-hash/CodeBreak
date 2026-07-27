import pygame

from .editor_theme import *


class Button:

    def __init__(self, x, y, width, height, text):

        self.rect = pygame.Rect(x, y, width, height)

        self.text = text

        self.hover = False

    def update(self):

        self.hover = self.rect.collidepoint(pygame.mouse.get_pos())

    def draw(self, screen):

        color = BUTTON_HOVER if self.hover else BUTTON

        pygame.draw.rect(screen, color, self.rect, border_radius=6)

        pygame.draw.rect(screen, BORDER, self.rect, 2, border_radius=6)

        txt = BUTTON_FONT.render(self.text, True, BUTTON_TEXT)

        screen.blit(
            txt,
            txt.get_rect(center=self.rect.center)
        )

    def clicked(self, event):

        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )