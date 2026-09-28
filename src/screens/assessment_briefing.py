"""Explain timed attempts before starting; report retakes after they end."""
import pygame
from src.ui.theme import UI_COLORS, body_font, title_font, draw_button, draw_panel
from src.screens.learning_progress import _wrapped


def assessment_dialog(screen, title, lines, button='START ASSESSMENT', allow_back=True):
    background = screen.copy()
    width, height = screen.get_size()
    panel = pygame.Rect(20, 20, min(720, width - 40), min(500, height - 40))
    panel.center = screen.get_rect().center
    start = pygame.Rect(0, 0, 260, 44)
    start.midbottom = (panel.centerx, panel.bottom - 26)
    font = body_font(18)
    heading = title_font(26)
    clock = pygame.time.Clock()
    while True:
        screen.blit(background, (0, 0))
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175)); screen.blit(overlay, (0, 0))
        draw_panel(screen, panel, emphasized=True, radius=12)
        y = panel.top + 24
        for line in _wrapped(title, heading, panel.width - 48):
            screen.blit(heading.render(line, True, UI_COLORS['gold']), (panel.left + 24, y))
            y += heading.get_linesize()
        y += 18
        for text in lines:
            for line in _wrapped(text, font, panel.width - 48):
                screen.blit(font.render(line, True, UI_COLORS['text']), (panel.left + 24, y))
                y += font.get_linesize() + 3
            y += 9
        draw_button(screen, start, button, font, hovered=start.collidepoint(pygame.mouse.get_pos()))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return not allow_back
                if event.key == pygame.K_RETURN:
                    return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and start.collidepoint(event.pos):
                return True
        clock.tick(60)
