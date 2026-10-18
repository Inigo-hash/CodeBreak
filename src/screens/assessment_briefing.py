"""Scrollable assessment instructions; the confirmation button stays visible."""
import pygame
from src.systems.audio import handle_music_shortcut
from src.ui.theme import UI_COLORS, body_font, title_font, draw_button, draw_panel, TIER_PRIMARY
from src.screens.learning_progress import _wrapped
from src.ui.text_layout import fit_text


def assessment_dialog(screen, title, lines, button='START ASSESSMENT', allow_back=True):
    background = screen.copy()
    width, height = screen.get_size()
    panel = pygame.Rect(20, 20, min(720, width - 40), min(570, height - 40))
    panel.center = screen.get_rect().center
    start = pygame.Rect(0, 0, min(300, panel.w - 48), 44)
    start.bottomright = (panel.right - 48, panel.bottom - 48)
    font = body_font(18)
    heading = title_font(26)
    title_surface = fit_text(heading, title, UI_COLORS['gold'], (panel.w - 96, 44))
    content = []
    for text in lines:
        content.extend(_wrapped(text, font, panel.width - 96))
        content.append('')
    top = panel.top + 48 + title_surface.get_height() + 18
    viewport = pygame.Rect(panel.left + 48, top, panel.w - 96, max(20, start.top - top - 38))
    line_height = font.get_linesize() + 3
    maximum_scroll = max(0, len(content) * line_height - viewport.h)
    scroll = 0
    clock = pygame.time.Clock()
    while True:
        screen.blit(background, (0, 0))
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        screen.blit(overlay, (0, 0))
        draw_panel(screen, panel, emphasized=True, radius=12)
        screen.blit(title_surface, title_surface.get_rect(midtop=(panel.centerx, panel.top + 42)))
        previous_clip = screen.get_clip()
        screen.set_clip(viewport)
        for index, line in enumerate(content):
            y = top + index * line_height - scroll
            if y + line_height >= viewport.top and y < viewport.bottom:
                screen.blit(font.render(line, True, UI_COLORS['text']), (viewport.x, y))
        screen.set_clip(previous_clip)
        if maximum_scroll:
            hint = fit_text(body_font(13), 'Scroll / Up / Down to read all instructions', UI_COLORS['text_dim'], (viewport.w, 20))
            screen.blit(hint, (viewport.x, start.top - 28))
        draw_button(screen, start, button, font, hovered=start.collidepoint(pygame.mouse.get_pos()), tier=TIER_PRIMARY)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if handle_music_shortcut(event):
                continue
            if event.type == pygame.MOUSEWHEEL:
                scroll = max(0, min(maximum_scroll, scroll - event.y * line_height * 3))
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return not allow_back
                if event.key == pygame.K_RETURN:
                    return True
                if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                    amount = viewport.h if event.key in (pygame.K_PAGEUP, pygame.K_PAGEDOWN) else line_height
                    scroll = max(0, min(maximum_scroll, scroll + amount * (1 if event.key in (pygame.K_DOWN, pygame.K_PAGEDOWN) else -1)))
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and start.collidepoint(event.pos):
                return True
        clock.tick(60)
