"""
profile.py

The player profile screen — portrait, name, and HP/PP bars. Opened by
clicking the portrait HUD in the top-left corner during gameplay (see
game.py's draw_profile_hud / portrait_rect click handling).

Blurs whatever's currently on screen behind the panel, same
downscale/upscale trick used for main_menu's settings panel
(_draw_interactive_settings) and game.py's pause menu.

This is a first draft: HP/PP are just displayed, not yet wired to
real damage/energy systems.
"""

import pygame
import sys
from src.ui.theme import body_font, title_font


def profile_screen(screen, background=None, name="Bobiles the explorer the great",
                    hp=100, max_hp=100, pp=100, max_pp=100):
    SCREEN_W, SCREEN_H = screen.get_size()
    clock = pygame.time.Clock()

    if background is None:
        background = screen.copy()

    # Palette — matches settings.py / main_menu's settings panel
    STONE_MID   = (42, 46, 58)
    STONE_LIGHT = (62, 68, 82)
    METAL_FRAME = (90, 94, 110)
    WHITE       = (255, 255, 255)
    BAR_BG      = (20, 22, 28)
    HP_FILL     = (200, 40, 40)
    HP_EDGE     = (255, 90, 90)
    PP_FILL     = (210, 175, 40)
    PP_EDGE     = (255, 220, 120)

    font_title = title_font(30)
    font_name  = title_font(22)
    font_tag   = body_font(15, bold=True)
    font_bar   = body_font(16, bold=True)

    # A bit bigger than the settings panel (380x480)
    panel_width, panel_height = 460, 560
    pr = pygame.Rect(
        (SCREEN_W - panel_width) // 2,
        (SCREEN_H - panel_height) // 2,
        panel_width,
        panel_height
    )

    back_r = pygame.Rect(pr.centerx - 70, pr.bottom - 56, 140, 36)

    portrait_size = 140
    portrait = pygame.image.load("assets/images/logos/codebreakLogo.png").convert_alpha()
    portrait = pygame.transform.smoothscale(portrait, (portrait_size, portrait_size))
    portrait_rect = pygame.Rect(0, 0, portrait_size, portrait_size)
    portrait_rect.centerx = pr.centerx
    portrait_rect.top = pr.top + 74

    bar_width = panel_width - 80
    bar_height = 26
    hp_bar_rect = pygame.Rect(pr.left + 40, 0, bar_width, bar_height)
    pp_bar_rect = pygame.Rect(pr.left + 40, 0, bar_width, bar_height)

    def draw_stat_bar(rect, value, max_value, fill_color, edge_color, label):
        tag = font_tag.render(label, True, (200, 200, 210))
        screen.blit(tag, (rect.left, rect.top - tag.get_height() - 4))

        pygame.draw.rect(screen, BAR_BG, rect, border_radius=6)
        ratio = 0 if max_value <= 0 else max(0.0, min(1.0, value / max_value))
        fill_rect = pygame.Rect(rect.left, rect.top, int(rect.width * ratio), rect.height)
        if fill_rect.width > 0:
            pygame.draw.rect(screen, fill_color, fill_rect, border_radius=6)
        pygame.draw.rect(screen, edge_color, rect, 2, border_radius=6)

        text = font_bar.render(f"{value}/{max_value}", True, WHITE)
        screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
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

        # ---- Panel ----
        pygame.draw.rect(screen, (36, 38, 48), pr)
        pygame.draw.rect(screen, METAL_FRAME, pr, 4)
        pygame.draw.rect(screen, (26, 28, 36), pr.inflate(-24, -24))

        title = font_title.render("PROFILE", True, WHITE)
        screen.blit(title, (pr.centerx - title.get_width() // 2, pr.top + 16))

        # Portrait
        pygame.draw.rect(screen, (20, 20, 26), portrait_rect.inflate(8, 8), border_radius=6)
        screen.blit(portrait, portrait_rect)
        pygame.draw.rect(screen, METAL_FRAME, portrait_rect.inflate(8, 8), 3, border_radius=6)

        # Name
        name_surf = font_name.render(name, True, WHITE)
        name_y = portrait_rect.bottom + 20
        screen.blit(name_surf, (pr.centerx - name_surf.get_width() // 2, name_y))

        # Bars (positioned below the name)
        hp_bar_rect.top = name_y + name_surf.get_height() + 34
        pp_bar_rect.top = hp_bar_rect.bottom + 30
        draw_stat_bar(hp_bar_rect, hp, max_hp, HP_FILL, HP_EDGE, "HEALTH")
        draw_stat_bar(pp_bar_rect, pp, max_pp, PP_FILL, PP_EDGE, "ENERGY")

        # Back button
        mouse_pos = pygame.mouse.get_pos()
        back_hovered = back_r.collidepoint(mouse_pos)
        pygame.draw.rect(screen, STONE_MID if not back_hovered else STONE_LIGHT, back_r, border_radius=4)
        pygame.draw.rect(screen, STONE_LIGHT, back_r, 2, border_radius=4)
        bt = font_name.render("BACK", True, WHITE)
        screen.blit(bt, (back_r.centerx - bt.get_width() // 2, back_r.centery - bt.get_height() // 2))

        pygame.display.flip()
