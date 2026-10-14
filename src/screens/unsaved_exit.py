"""Explicit save, discard and cancel choices before leaving an adventure."""
import pygame
from src.ui.theme import (UI_COLORS, title_font, body_font, draw_panel, draw_button,
                          TIER_PRIMARY, TIER_DANGER, TIER_SECONDARY)
from src.ui.text_layout import fit_text, draw_text_block


def confirm_unsaved_exit(screen, save=None, destination='exit the game'):
    background = screen.copy()
    panel = pygame.Rect(0, 0, min(780, screen.get_width()-48), 360)
    panel.center = screen.get_rect().center
    gap, padding = 14, 26
    button_w = (panel.w-padding*2-gap*2)//3
    buttons = [pygame.Rect(panel.x+padding+i*(button_w+gap), panel.bottom-88, button_w, 48) for i in range(3)]
    buttons[0].x, buttons[2].x = buttons[2].x, buttons[0].x
    labels = ('SAVE & LEAVE' if save else 'NO SAVE SLOT', 'LEAVE WITHOUT SAVING', 'KEEP PLAYING')
    focus = 2  # Never default a keyboard confirmation to discarding progress.
    error = ''
    clock = pygame.time.Clock()
    while True:
        screen.blit(background, (0, 0))
        shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 200))
        screen.blit(shade, (0, 0))
        draw_panel(screen, panel, radius=12, alpha=255)
        title = fit_text(title_font(30), 'UNSAVED PROGRESS', UI_COLORS['gold'], (panel.w-56, 48))
        screen.blit(title, title.get_rect(midtop=(panel.centerx, panel.top+30)))
        message = f'You have changes since your last save. Save before you {destination}, or they will be lost.'
        if save is None:
            message += ' This session has no save slot. Keep playing to stay in the game.'
        draw_text_block(screen, error or message, body_font(18), UI_COLORS['modal_danger'] if error else UI_COLORS['text'],
                        pygame.Rect(panel.x+30, panel.y+106, panel.w-60, 112), center=True)
        for index, (rect, label, tier) in enumerate(zip(buttons, labels, (TIER_PRIMARY, TIER_DANGER, TIER_SECONDARY))):
            draw_button(screen, rect, label, title_font(16), tier=tier,
                        enabled=index != 0 or save is not None, focused=index == focus,
                        hovered=rect.collidepoint(pygame.mouse.get_pos()))
        hint = fit_text(body_font(12), 'TAB / ARROWS: choose   ENTER: confirm   ESC: keep playing', UI_COLORS['text_dim'], (panel.w-48, 20))
        screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom-20)))
        pygame.display.flip()
        action = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key in (pygame.K_TAB, pygame.K_RIGHT, pygame.K_LEFT):
                    order = (2, 1, 0)  # Left to right: keep, discard, save.
                    focus = order[(order.index(focus)+(-1 if event.key == pygame.K_LEFT else 1)) % 3]
                    if focus == 0 and save is None:
                        focus = 2 if event.key != pygame.K_LEFT else 1
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    action = focus
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action = next((i for i, rect in enumerate(buttons) if rect.collidepoint(event.pos)), None)
            if action is not None:
                break
        if action == 2:
            return False
        if action == 1:
            return True
        if action == 0 and save is not None:
            try:
                save()
            except Exception:
                error = 'Your save could not be written. You are still in the game. Try again or keep playing.'
                focus = 2
            else:
                return True
        clock.tick(60)
