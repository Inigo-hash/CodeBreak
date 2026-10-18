"""Small Castle console marker, cached at map zoom rather than per frame."""
from functools import lru_cache
import pygame
from src.ui.theme import UI_COLORS


@lru_cache(maxsize=12)
def terminal_art(size, mastered=False):
    size = max(16, int(size))
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    border = UI_COLORS['gold'] if not mastered else (126, 230, 154)
    pygame.draw.rect(surface, UI_COLORS['stone_deep'], (0, 2, size, size-2), border_radius=3)
    pygame.draw.rect(surface, border, (1, 2, size-2, size-3), 2, border_radius=3)
    pygame.draw.rect(surface, UI_COLORS['modal_inner'], (5, 6, size-10, size-12), border_radius=2)
    for offset in (0, 1, 2):
        y = round(size * (.3 + .14*offset))
        pygame.draw.line(surface, border, (round(size*.25), y), (round(size*.7), y), 2)
    return surface
