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

Energy is not wired to a real system yet; passing max_pp=0 makes the bar
render as "-- / --" instead of a full-looking empty bar.
"""

import pygame
import sys
from src.systems.audio import handle_music_shortcut

from src.ui.gameplay_hud import (
    NAME_GOLD,
    draw_framed_portrait,
    draw_heart_row,
    draw_profile_frame,
    draw_stat_bar,
    load_hud_icons,
    load_portrait,
)
from src.ui.theme import UI_COLORS, body_font, draw_button, title_font


def profile_screen(screen, background=None, name="Bobiles the explorer the great",
                    hp=100, max_hp=100, pp=100, max_pp=100, hearts=5):
    SCREEN_W, SCREEN_H = screen.get_size()
    clock = pygame.time.Clock()

    if background is None:
        background = screen.copy()

    font_title = title_font(26)
    font_name = title_font(24)
    font_bar = body_font(15, bold=True)
    font_button = title_font(20)

    portrait = load_portrait()
    icons = load_hud_icons()

    # --- Layout -------------------------------------------------------------
    # Sized around its content, like the HUD card it grows out of: portrait on
    # the left, name / hearts / bars stacked to the right of it.
    PAD = 30
    PORTRAIT_SIZE = 190
    PORTRAIT_GAP = 26
    ROW_GAP = 24
    HEART_SIZE = 30
    BACK_HEIGHT = 42

    panel_width = max(520, min(620, int(SCREEN_W * 0.55)))
    col_offset = PAD + PORTRAIT_SIZE + PORTRAIT_GAP
    col_width = panel_width - PAD - col_offset

    # Both bars share a gutter wide enough for the longer of the two labels,
    # so their fills start on the same x.
    bar_label_width = max(font_bar.size("HP 000 / 000")[0],
                          font_bar.size("ENERGY -- / --")[0]) + 14

    title_surface = font_title.render("PROFILE", True, UI_COLORS["gold"])
    name_surface = font_name.render(name.upper(), True, NAME_GOLD)
    # The name is the one piece that can outgrow its column, so shrink it
    # until it fits rather than letting it run under the panel edge.
    name_size = 24
    while name_surface.get_width() > col_width and name_size > 12:
        name_size -= 1
        name_surface = title_font(name_size).render(name.upper(), True, NAME_GOLD)

    bar_height = font_bar.get_height()
    column_height = (name_surface.get_height() + ROW_GAP + HEART_SIZE
                     + ROW_GAP + bar_height + ROW_GAP + bar_height)
    body_height = max(PORTRAIT_SIZE, column_height)

    pr = pygame.Rect(0, 0, panel_width,
                     PAD + font_title.get_height() + 22 + body_height
                     + 28 + BACK_HEIGHT + PAD)
    pr.center = (SCREEN_W // 2, SCREEN_H // 2)

    title_pos_y = pr.top + PAD
    body_top = title_pos_y + font_title.get_height() + 22

    portrait_rect = pygame.Rect(pr.left + PAD, 0, PORTRAIT_SIZE, PORTRAIT_SIZE)
    portrait_rect.top = body_top + (body_height - PORTRAIT_SIZE) // 2

    col_x = pr.left + col_offset
    col_top = body_top + (body_height - column_height) // 2

    back_r = pygame.Rect(0, 0, 150, BACK_HEIGHT)
    back_r.midbottom = (pr.centerx, pr.bottom - PAD)

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
        small = pygame.transform.smoothscale(background, (SCREEN_W // 8, SCREEN_H // 8))
        blurred = pygame.transform.smoothscale(small, (SCREEN_W, SCREEN_H))
        screen.blit(blurred, (0, 0))

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        # ---- Panel: the HUD card's own frame, at full size ----
        draw_profile_frame(screen, pr)

        screen.blit(title_surface,
                    (pr.centerx - title_surface.get_width() // 2, title_pos_y))

        draw_framed_portrait(screen, portrait, portrait_rect)

        # ---- Name, hearts, bars ----
        y = col_top
        screen.blit(name_surface, (col_x, y))

        y += name_surface.get_height() + ROW_GAP
        draw_heart_row(screen, icons, col_x, y, hearts,
                       size=HEART_SIZE, gap=HEART_SIZE + 5)

        y += HEART_SIZE + ROW_GAP
        draw_stat_bar(screen, font_bar, col_x, y, col_width, "HP", hp, max_hp,
                      label_width=bar_label_width)

        y += bar_height + ROW_GAP
        draw_stat_bar(screen, font_bar, col_x, y, col_width, "ENERGY", pp, max_pp,
                      fill_color=UI_COLORS["gold"], label_width=bar_label_width)

        # ---- Back button ----
        mouse_pos = pygame.mouse.get_pos()
        draw_button(screen, back_r, "BACK", font_button,
                    hovered=back_r.collidepoint(mouse_pos))

        pygame.display.flip()
