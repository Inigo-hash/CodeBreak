"""Shared visual language for CodeBreak menus and compact gameplay UI."""

from functools import lru_cache

import pygame


UI_COLORS = {
    "stone_deep": (12, 13, 18),
    "stone": (29, 31, 40),
    "stone_light": (45, 48, 59),
    "bronze_dark": (91, 62, 34),
    "bronze": (171, 119, 55),
    "gold": (218, 177, 86),
    "blue": (72, 166, 224),
    "blue_bright": (120, 205, 255),
    "crimson": (190, 42, 52),
    "parchment": (226, 207, 164),
    "text": (240, 237, 224),
    "text_dim": (156, 161, 174),
}

CINZEL = "assets/fonts/Cinzel-VariableFont_wght.ttf"
CINZEL_BOLD = "assets/fonts/Cinzel-Bold.ttf"


@lru_cache(maxsize=24)
def title_font(size, bold=True):
    path = CINZEL_BOLD if bold else CINZEL
    try:
        return pygame.font.Font(path, size)
    except (FileNotFoundError, pygame.error):
        return pygame.font.Font(None, size)


@lru_cache(maxsize=24)
def body_font(size, bold=False):
    return pygame.font.SysFont("consolas", size, bold=bold)


def draw_panel(surface, rect, emphasized=False, radius=8, alpha=238):
    """Draw the standard inset stone panel with a bronze/blue focus rim."""
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    local = panel.get_rect()
    shadow = local.move(0, 4)
    pygame.draw.rect(panel, (5, 6, 9, 150), shadow, border_radius=radius)
    pygame.draw.rect(panel, (*UI_COLORS["stone_deep"], alpha), local, border_radius=radius)
    pygame.draw.rect(panel, (*UI_COLORS["stone"], alpha), local.inflate(-8, -8),
                     border_radius=max(2, radius - 2))
    pygame.draw.rect(panel, UI_COLORS["blue"] if emphasized else UI_COLORS["bronze"],
                     local, 2, border_radius=radius)
    pygame.draw.line(panel, UI_COLORS["stone_light"], (radius, 5),
                     (local.right - radius, 5), 1)
    pygame.draw.line(panel, UI_COLORS["bronze_dark"], (radius, local.bottom - 5),
                     (local.right - radius, local.bottom - 5), 1)
    surface.blit(panel, rect.topleft)


def draw_button(surface, rect, label, font, hovered=False, text_offset=0):
    """Shared carved stone button used by the Main and Pause menus."""
    draw_rect = rect.inflate(4, 4) if hovered else rect
    glow = pygame.Surface((draw_rect.w + 14, draw_rect.h + 14), pygame.SRCALPHA)
    if hovered:
        pygame.draw.rect(glow, (*UI_COLORS["blue"], 55), glow.get_rect(),
                         border_radius=10)
        surface.blit(glow, (draw_rect.x - 7, draw_rect.y - 7))

    pygame.draw.rect(surface, (6, 7, 10), draw_rect.move(0, 4), border_radius=7)
    pygame.draw.rect(surface,
                     UI_COLORS["stone_light"] if hovered else UI_COLORS["stone"],
                     draw_rect, border_radius=7)
    pygame.draw.rect(surface,
                     UI_COLORS["blue_bright"] if hovered else UI_COLORS["bronze"],
                     draw_rect, 2, border_radius=7)
    inner = draw_rect.inflate(-8, -8)
    pygame.draw.rect(surface, UI_COLORS["bronze_dark"], inner, 1, border_radius=4)
    pygame.draw.line(surface, (69, 72, 84),
                     (inner.left + 5, inner.top + 2),
                     (inner.right - 5, inner.top + 2), 1)

    text = font.render(label, True, UI_COLORS["text"])
    text_rect = text.get_rect(center=(draw_rect.centerx + text_offset, draw_rect.centery))
    surface.blit(text, text_rect)
    return draw_rect
