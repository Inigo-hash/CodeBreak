import pygame
import sys
from src.settings_state import settings_state as _settings_state

def settings_screen(screen):
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

    # Colors
    STONE_DARK = (28, 30, 38)
    STONE_MID = (42, 46, 58)
    STONE_LIGHT = (62, 68, 82)
    BLUE_GLOW = (80, 180, 255)
    YELLOW_GLOW = (255, 220, 120)
    GREEN_TIP = (60, 255, 140)
    WHITE = (255, 255, 255)
    METAL_FRAME = (90, 94, 110)

    # Fonts
    font_title = pygame.font.SysFont("consolas", 32, bold=True)
    font_label = pygame.font.SysFont("consolas", 18)
    font_btn   = pygame.font.SysFont("consolas", 22, bold=True)

    # State
    themes      = ["GREEN", "BLUE", "ORANGE", "PURPLE"]
    theme_index = 0
    dragging_music = False
    dragging_sfx   = False

    # Panel rect
    pr = pygame.Rect(SCREEN_WIDTH // 2 - 190, SCREEN_HEIGHT // 2 - 240, 380, 480)

    # Slider rects
    music_bar = pygame.Rect(pr.left + 28, pr.top + 160, pr.width - 56, 14)
    sfx_bar   = pygame.Rect(pr.left + 28, pr.top + 240, pr.width - 56, 14)

    # Arrow rects
    arrow_y     = pr.top + 320
    left_arrow  = pygame.Rect(pr.left + 60,   arrow_y, 40, 28)
    right_arrow = pygame.Rect(pr.right - 100, arrow_y, 40, 28)

    # Back button rect
    back_r = pygame.Rect(pr.centerx - 70, pr.bottom - 56, 140, 36)

    clock = pygame.time.Clock()
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if music_bar.collidepoint(event.pos):
                    dragging_music = True
                if sfx_bar.collidepoint(event.pos):
                    dragging_sfx = True
                if left_arrow.collidepoint(event.pos):
                    theme_index = (theme_index - 1) % len(themes)
                if right_arrow.collidepoint(event.pos):
                    theme_index = (theme_index + 1) % len(themes)
                if back_r.collidepoint(event.pos):
                    return  # back to main menu

            if event.type == pygame.MOUSEBUTTONUP:
                dragging_music = False
                dragging_sfx   = False

            if event.type == pygame.MOUSEMOTION:
                if dragging_music:
                    _settings_state["music_vol"] = max(0.0, min(1.0, (event.pos[0] - music_bar.left) / music_bar.width))
                    pygame.mixer.music.set_volume(_settings_state["music_vol"])
                if dragging_sfx:
                    _settings_state["sfx_vol"] = max(0.0, min(1.0, (event.pos[0] - sfx_bar.left) / sfx_bar.width))

        # --- Draw ---
        # Dim overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # Panel background
        pygame.draw.rect(screen, (36, 38, 48), pr)
        pygame.draw.rect(screen, METAL_FRAME, pr, 4)
        pygame.draw.rect(screen, (26, 28, 36), pr.inflate(-24, -24))

        # Title
        title = font_title.render("SETTINGS", True, WHITE)
        screen.blit(title, (pr.centerx - title.get_width() // 2, pr.top + 16))

        # TEXT SPEED
        screen.blit(font_label.render("TEXT SPEED", True, (200, 200, 210)), (pr.left + 28, pr.top + 70))
        screen.blit(font_label.render("SLOW    NORMAL    INSTANT", True, (160, 170, 190)), (pr.left + 28, pr.top + 96))

        # MUSIC slider
        screen.blit(font_label.render("MUSIC", True, (200, 200, 210)), (pr.left + 28, pr.top + 140))
        pygame.draw.rect(screen, (30, 32, 40), music_bar, border_radius=4)
        mx = music_bar.left + int((music_bar.width - 16) * _settings_state["music_vol"])
        pygame.draw.rect(screen, YELLOW_GLOW, (mx, music_bar.top - 2, 16, 18), border_radius=3)

        # SFX slider
        screen.blit(font_label.render("SFX", True, (200, 200, 210)), (pr.left + 28, pr.top + 220))
        pygame.draw.rect(screen, (30, 32, 40), sfx_bar, border_radius=4)
        sx = sfx_bar.left + int((sfx_bar.width - 16) * _settings_state["sfx_vol"])
        pygame.draw.rect(screen, YELLOW_GLOW, (sx, sfx_bar.top - 2, 16, 18), border_radius=3)

        # SYNTAX THEME
        screen.blit(font_label.render("SYNTAX THEME", True, (200, 200, 210)), (pr.left + 28, pr.top + 300))

        # Left arrow
        pygame.draw.rect(screen, (50, 55, 70), left_arrow, border_radius=4)
        tri_l = [
            (left_arrow.right - 8,  left_arrow.top + 6),
            (left_arrow.right - 8,  left_arrow.bottom - 6),
            (left_arrow.left + 6,   left_arrow.centery),
        ]
        pygame.draw.polygon(screen, BLUE_GLOW, tri_l)

        # Right arrow
        pygame.draw.rect(screen, (50, 55, 70), right_arrow, border_radius=4)
        tri_r = [
            (right_arrow.left + 8,  right_arrow.top + 6),
            (right_arrow.left + 8,  right_arrow.bottom - 6),
            (right_arrow.right - 6, right_arrow.centery),
        ]
        pygame.draw.polygon(screen, BLUE_GLOW, tri_r)

        # Theme label
        theme_colors = {
            "GREEN":  (60, 255, 140),
            "BLUE":   (80, 180, 255),
            "ORANGE": (255, 160, 60),
            "PURPLE": (180, 100, 255),
        }
        current_theme = themes[theme_index]
        th = font_btn.render(current_theme, True, theme_colors[current_theme])
        screen.blit(th, (pr.centerx - th.get_width() // 2, arrow_y + 4))

        # Back button
        pygame.draw.rect(screen, STONE_MID, back_r, border_radius=4)
        pygame.draw.rect(screen, STONE_LIGHT, back_r, 2, border_radius=4)
        bt = font_btn.render("BACK", True, WHITE)
        screen.blit(bt, (back_r.centerx - bt.get_width() // 2, back_r.centery - bt.get_height() // 2))

        pygame.display.flip()
        clock.tick(60)