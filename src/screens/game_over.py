"""Defeat modal with a carved stone card and a clear route back to play."""

import math
import random

import pygame

from src.config import DEBUG_MODE
from src.systems.audio import handle_music_shortcut
from src.ui.text_layout import draw_text_block, fit_text
from src.ui.theme import UI_COLORS, body_font, title_font


ACTIONS = (
    ('retry', 'RETRY', 'Return to the adventure', 'ENTER'),
    ('review', 'REVIEW', 'Regroup for another attempt', 'R'),
    ('main_menu', 'MAIN MENU', 'Return to the main menu', 'M'),
)


def _make_blurred_backdrop(source, width, height):
    small = pygame.transform.smoothscale(source, (max(1, width // 14), max(1, height // 14)))
    blurred = pygame.transform.smoothscale(small, (width, height))
    tint = pygame.Surface((width, height), pygame.SRCALPHA)
    tint.fill((7, 10, 17, 194))
    blurred.blit(tint, (0, 0))
    return blurred


def _build_blood_vignette(width, height):
    small = pygame.Surface((160, 90), pygame.SRCALPHA)
    for y in range(90):
        for x in range(160):
            distance = math.hypot((x - 79.5) / 79.5, (y - 44.5) / 44.5)
            fade = max(0.0, min(1.0, (distance - .5) / .85))
            small.set_at((x, y), (66, 13, 25, round(145 * fade * fade)))
    return pygame.transform.smoothscale(small, (width, height))


def _game_over_layout(size):
    width, height = size
    panel = pygame.Rect(0, 0, min(740, width - 32), min(790, height - 32))
    panel.center = (width // 2, height // 2)
    inset = max(18, min(48, panel.w // 14))
    content = panel.inflate(-inset * 2, 0)

    def slot(top, bottom):
        return pygame.Rect(content.x, panel.y + round(panel.h * top),
                           content.w, round(panel.h * (bottom - top)))

    return {
        'panel': panel,
        'overline': slot(.045, .078),
        'emblem': slot(.098, .237),
        'title': slot(.254, .352),
        'subtitle': slot(.365, .412),
        'tip': slot(.447, .574),
        'buttons': [slot(.619 + index * .101, .705 + index * .101)
                    for index in range(3)],
        'footer': slot(.939, .974),
    }


def _center_text(screen, text, font, color, rect):
    image = fit_text(font, text, color, rect.size)
    screen.blit(image, image.get_rect(center=rect.center))


def _build_card(rect):
    """Static stone, inset bronze trim and restrained crimson illumination."""
    card = pygame.Surface(rect.size, pygame.SRCALPHA)
    local = card.get_rect()
    pygame.draw.rect(card, (*UI_COLORS['stone_deep'], 252), local, border_radius=14)
    for y in range(5, local.h - 5):
        glow = max(0.0, 1.0 - y / (local.h * .46))
        color = (round(22 + 18 * glow), round(24 - 2 * glow), round(32 + 2 * glow))
        pygame.draw.line(card, color, (6, y), (local.w - 7, y))
    pygame.draw.rect(card, UI_COLORS['bronze_dark'], local, 1, border_radius=14)
    pygame.draw.rect(card, UI_COLORS['stone_light'], local.inflate(-12, -12), 1, border_radius=9)
    # Short corner ornaments carry the same bronze as the gameplay HUD.
    length = max(16, min(32, rect.h // 18))
    for x, y, dx, dy in ((14, 14, 1, 1), (rect.w - 15, 14, -1, 1),
                         (14, rect.h - 15, 1, -1), (rect.w - 15, rect.h - 15, -1, -1)):
        pygame.draw.line(card, UI_COLORS['bronze'], (x, y), (x + length * dx, y), 2)
        pygame.draw.line(card, UI_COLORS['bronze'], (x, y), (x, y + length * dy), 2)
    return card


def _draw_emblem(screen, rect):
    cx, cy = rect.center
    radius = max(12, min(rect.h // 2 - 2, 46))
    # A broken seal: warm metal around an unlit crimson heart.
    pygame.draw.circle(screen, (54, 26, 34), (cx, cy), radius)
    ring = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
    pygame.draw.arc(screen, UI_COLORS['bronze'], ring, .18, math.pi - .18, 1)
    pygame.draw.arc(screen, UI_COLORS['bronze_dark'], ring, math.pi + .18, math.tau - .18, 1)
    s = radius * .53
    heart = [(cx, cy + s * .70), (cx - s, cy - s * .08),
             (cx - s, cy - s * .58), (cx - s * .45, cy - s * .83),
             (cx, cy - s * .40), (cx + s * .45, cy - s * .83),
             (cx + s, cy - s * .58), (cx + s, cy - s * .08)]
    pygame.draw.polygon(screen, UI_COLORS['crimson'], heart)
    pygame.draw.lines(screen, (28, 19, 27), False,
                      [(cx + 2, cy - s * .43), (cx - 3, cy - 1),
                       (cx + 4, cy + 3), (cx - 1, cy + s * .70)], 3)
    for direction in (-1, 1):
        edge = cx + direction * (radius + 16)
        pygame.draw.line(screen, UI_COLORS['bronze_dark'],
                         (edge, cy), (edge + direction * min(90, rect.w // 6), cy))
        pygame.draw.circle(screen, UI_COLORS['bronze'], (edge, cy), 2)


def _build_buttons(layout):
    """Cache button artwork; only the chosen hover state changes per frame."""
    result = []
    for index, ((action, label, description, key), rect) in enumerate(zip(ACTIONS, layout['buttons'])):
        states = []
        for selected in (False, True):
            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            local = panel.get_rect()
            primary = index == 0
            if primary:
                fill = UI_COLORS['gold_bright' if selected else 'gold']
                ink, secondary = UI_COLORS['gold_text_dark'], (69, 47, 18)
                border = UI_COLORS['gold_bright']
            else:
                fill = UI_COLORS['button_fill_hover' if selected else 'button_fill']
                ink, secondary = UI_COLORS['text'], UI_COLORS['text_dim']
                border = UI_COLORS['gold'] if selected else UI_COLORS['modal_button_edge']
            pygame.draw.rect(panel, fill, local, border_radius=7)
            pygame.draw.rect(panel, border, local, 2 if selected else 1, border_radius=7)
            pygame.draw.line(panel, (*ink, 36), (12, 4), (rect.w - 13, 4))
            pad = max(10, min(20, rect.h // 3))
            key_w = min(76, max(46, rect.w // 7))
            key_rect = pygame.Rect(rect.w - pad - key_w, rect.h // 2 - max(10, rect.h // 4),
                                   key_w, max(20, rect.h // 2))
            pygame.draw.rect(panel, (*ink, 48), key_rect, 1, border_radius=4)
            _center_text(panel, key, body_font(12, bold=True), ink, key_rect.inflate(-6, -4))
            label_rect = pygame.Rect(pad, round(rect.h * .12),
                                     key_rect.left - pad * 2, round(rect.h * .43))
            title = fit_text(title_font(22), label, ink, label_rect.size)
            panel.blit(title, title.get_rect(midleft=label_rect.midleft))
            description_rect = pygame.Rect(pad, round(rect.h * .57),
                                           label_rect.w, max(1, round(rect.h * .26)))
            text = fit_text(body_font(13), description, secondary, description_rect.size)
            panel.blit(text, text.get_rect(midleft=description_rect.midleft))
            states.append(panel)
        result.append({'key': action, 'rect': rect, 'states': states})
    return result


def _draw_game_over_frame(screen, backdrop, vignette, layout, card, buttons,
                          focused=0):
    screen.blit(backdrop, (0, 0))
    screen.blit(vignette, (0, 0))
    panel = layout['panel']
    # Shadow sits outside the card instead of muddying the contents.
    pygame.draw.rect(screen, (5, 6, 10), panel.inflate(12, 12).move(0, 6), border_radius=18)
    screen.blit(card, panel)
    _center_text(screen, 'JOURNEY INTERRUPTED', body_font(12, bold=True),
                 UI_COLORS['gold'], layout['overline'])
    _draw_emblem(screen, layout['emblem'])
    _center_text(screen, 'GAME OVER', title_font(58), UI_COLORS['text'], layout['title'])
    _center_text(screen, 'Every explorer falls. Your journey continues.', body_font(16),
                 UI_COLORS['text_dim'], layout['subtitle'])

    tip = layout['tip']
    pygame.draw.rect(screen, UI_COLORS['stone_deep'], tip, border_radius=6)
    pygame.draw.line(screen, UI_COLORS['bronze'], (tip.left, tip.top + 7),
                     (tip.left, tip.bottom - 7), 2)
    pad = max(8, min(16, tip.h // 5))
    name_rect = pygame.Rect(tip.x + pad, tip.y + pad, tip.w - 2 * pad, max(10, round(tip.h * .24)))
    name = fit_text(title_font(14), 'MANG TAHIMIK', UI_COLORS['gold'], name_rect.size)
    screen.blit(name, name_rect.topleft)
    message = pygame.Rect(name_rect.x, name_rect.bottom + 3, name_rect.w,
                          max(1, tip.bottom - name_rect.bottom - pad - 3))
    draw_text_block(screen, 'Keep moving, use Shift to dodge, and retreat to torchlight to recover.',
                    body_font(17), UI_COLORS['text_dim'], message)

    for index, button in enumerate(buttons):
        selected = index == focused
        screen.blit(button['states'][int(selected)], button['rect'])
    _center_text(screen, 'TAB / ARROWS  Choose     ENTER  Select', body_font(11),
                 UI_COLORS['text_dim'], layout['footer'])


def game_over_screen(screen, background=None, failed_snippet=None):
    """Return retry, review or main_menu; preserve existing campaign actions."""
    width, height = screen.get_size()
    background = screen.copy() if background is None else background
    backdrop = _make_blurred_backdrop(background, width, height)
    vignette = _build_blood_vignette(width, height)
    layout = _game_over_layout((width, height))
    card = _build_card(layout['panel'])
    buttons = _build_buttons(layout)
    focused = 0
    clock = pygame.time.Clock()
    # Let the click/key that led into the death modal settle before selecting.
    started = pygame.time.get_ticks()
    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if handle_music_shortcut(event):
                continue
            if DEBUG_MODE and event.type == pygame.KEYDOWN and event.key == pygame.K_F8:
                return 'debug_close'
            if pygame.time.get_ticks() - started < 250:
                continue
            if event.type == pygame.MOUSEMOTION:
                for index, button in enumerate(buttons):
                    if button['rect'].collidepoint(event.pos):
                        focused = index
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_TAB, pygame.K_DOWN, pygame.K_UP):
                    step = -1 if event.key == pygame.K_UP or (
                        event.key == pygame.K_TAB and getattr(event, 'mod', 0) & pygame.KMOD_SHIFT) else 1
                    focused = (focused + step) % len(buttons)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return buttons[focused]['key']
                elif event.key == pygame.K_ESCAPE:
                    return 'retry'
                elif event.key == pygame.K_r:
                    return 'review'
                elif event.key == pygame.K_m:
                    return 'main_menu'
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in buttons:
                    if button['rect'].collidepoint(event.pos):
                        return button['key']
        _draw_game_over_frame(screen, backdrop, vignette, layout, card, buttons, focused)
        pygame.display.flip()


if __name__ == '__main__':
    pygame.init()
    demo_screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption('CodeBreak - Game Over')
    backdrop = pygame.Surface((1280, 720))
    backdrop.fill((35, 55, 38))
    rng = random.Random(1)
    for _ in range(400):
        x, y = rng.randrange(1280), rng.randrange(720)
        shade = rng.randrange(20, 80)
        pygame.draw.rect(backdrop, (shade, shade + 10, shade), (x, y, 20, 20))
    print('Player chose:', game_over_screen(demo_screen, background=backdrop))
    pygame.quit()
