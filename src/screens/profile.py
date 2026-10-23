"""
profile.py

The player profile screen — portrait, name, hearts and HP/energy bars.
Opened by clicking the portrait card in the top-left corner during
gameplay (see game.py's gameplay_hud.profile_rect click handling).

Deliberately the *same card, larger*: the frame, portrait trim, heart row
and stat bars are all drawn by the shared helpers in ui/gameplay_hud.py,
so tapping the HUD card expands it rather than swapping it for a
differently-styled panel.

Blurs whatever's currently on screen behind the panel, same
downscale/upscale trick used for main_menu's settings panel
(_draw_interactive_settings) and game.py's pause menu.

Energy comes from PlayerCombat: it is the dodge budget, spent per dodge
and regenerating over time. Callers with no energy to report can still
pass max_pp=0, which renders the bar as "-- / --" instead of a
full-looking empty bar.
"""

import pygame
from src.data.characters import character_title
from src.ui.text_layout import fit_text
import sys
from src.systems.audio import handle_music_shortcut

from src.ui.gameplay_hud import (
    NAME_GOLD,
    draw_framed_portrait,
    draw_heart_row,
    draw_profile_frame,
    draw_resource_meter,
    load_hud_icons,
    load_portrait,
)
from src.ui.theme import UI_COLORS, body_font, draw_button, title_font


def profile_layout(size, title_height=40, name_height=38, stat_height=16):
    """One portrait and separate measured text rows, including at 640x480."""
    width, height = size
    pad, gap = 24, 24
    panel_width = min(640, width-32)
    portrait_size = min(200, round(panel_width*.32))
    lives_height = max(24, stat_height)
    meter_height = stat_height+14
    column_height = name_height+8+lives_height+16+meter_height*2+12
    body_height = max(portrait_size, column_height)
    panel = pygame.Rect(0, 0, panel_width,
                        pad+title_height+16+body_height+20+42+pad)
    panel.center = (width//2, height//2)
    title = pygame.Rect(panel.x+pad, panel.y+pad, panel.width-pad*2, title_height)
    top = title.bottom+16
    portrait = pygame.Rect(panel.x+pad, top+(body_height-portrait_size)//2,
                           portrait_size, portrait_size)
    left = portrait.right+gap
    col_width = panel.right-pad-left
    name = pygame.Rect(left, top+(body_height-column_height)//2, col_width, name_height)
    lives = pygame.Rect(left, name.bottom+8, col_width, lives_height)
    health = pygame.Rect(left, lives.bottom+16, col_width, meter_height)
    energy = pygame.Rect(left, health.bottom+12, col_width, meter_height)
    back = pygame.Rect(0, 0, 150, 42)
    back.midbottom = (panel.centerx, panel.bottom-pad)
    return dict(panel=panel, title=title, portrait=portrait, name=name, lives=lives,
                health=health, energy=energy, back=back)


def profile_screen(screen, background=None, name=None,
                    hp=100, max_hp=100, pp=100, max_pp=100, hearts=5, character_id='man'):
    SCREEN_W, SCREEN_H = screen.get_size()
    if name is None:
        name = character_title(character_id)
    clock = pygame.time.Clock()

    if background is None:
        background = screen.copy()

    font_title = title_font(26)
    font_name = title_font(24)
    font_bar = body_font(15, bold=True)
    font_button = title_font(20)

    portrait = load_portrait(character_id)
    icons = load_hud_icons()

    layout = profile_layout(screen.get_size(), font_title.get_height(),
                            font_name.get_height(), font_bar.get_height())
    pr, back_r = layout['panel'], layout['back']
    title_surface = fit_text(font_title, 'EXPLORER PROFILE', UI_COLORS['gold'], layout['title'].size)
    name_surface = fit_text(font_name, name.title(), NAME_GOLD, layout['name'].size)
    # The snapshot never changes while this modal is open.
    small = pygame.transform.smoothscale(background, (SCREEN_W//8, SCREEN_H//8))
    blurred = pygame.transform.smoothscale(small, (SCREEN_W, SCREEN_H))
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))
    blurred.blit(overlay, (0, 0))

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if handle_music_shortcut(event):
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_r.collidepoint(event.pos):
                    running = False

        # ---- Blurred backdrop ----
        screen.blit(blurred, (0, 0))

        # ---- Panel: the HUD card's own frame, at full size ----
        draw_profile_frame(screen, pr)

        screen.blit(title_surface,
                    title_surface.get_rect(midtop=(pr.centerx, layout['title'].y)))

        draw_framed_portrait(screen, portrait, layout['portrait'])

        # ---- Name, hearts, bars ----
        screen.blit(name_surface, layout['name'])
        lives = layout['lives']
        lives_label = fit_text(font_bar, 'LIVES', UI_COLORS['text_dim'], (50, lives.height))
        screen.blit(lives_label, lives)
        heart_size = min(24, max(12, (lives.width-70)//5))
        draw_heart_row(screen, icons, lives.x+58, lives.y, hearts,
                       size=heart_size, gap=heart_size+3)
        draw_resource_meter(screen, font_bar, layout['health'], 'HEALTH', hp, max_hp)
        draw_resource_meter(screen, font_bar, layout['energy'], 'ENERGY', pp, max_pp,
                            fill_color=UI_COLORS['gold'])

        # ---- Back button ----
        mouse_pos = pygame.mouse.get_pos()
        draw_button(screen, back_r, "BACK", font_button,
                    hovered=back_r.collidepoint(mouse_pos))

        pygame.display.flip()
