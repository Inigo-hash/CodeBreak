import math
import random
import sys
import pygame
from src.screens.game import game_screen
from src.settings_state import settings_state as _settings_state

# Initialize Pygame
pygame.init()

# Screen settings
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
pygame.display.set_caption("CodeBreak - Main Menu")

background = pygame.image.load("assets/images/backgrounds/mainMenuBg.png").convert()
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
screen.blit(background, (0, 0))

# Palette
STONE_DARK = (28, 30, 38)
STONE_MID = (42, 46, 58)
STONE_LIGHT = (62, 68, 82)
BLUE_GLOW = (80, 180, 255)
BLUE_DEEP = (35, 90, 140)
YELLOW_GLOW = (255, 220, 120)
GREEN_TIP = (60, 255, 140)
GREEN_PLAY = (80, 220, 120)
WHITE = (255, 255, 255)
METAL_FRAME = (90, 94, 110)
ROBOT_BLUE = (70, 140, 220)

# Fonts
_button_font = pygame.font.SysFont("consolas", 22, bold=True)
_small = pygame.font.SysFont("consolas", 18)
_tip_font = pygame.font.SysFont("consolas", 17)


def _fallback_font(size, bold=False):
    return pygame.font.Font(None, size)


try:
    _ = _button_font.render("x", True, WHITE)
except Exception:
    _button_font = _fallback_font(24, True)
    _small = _fallback_font(18)
    _tip_font = _fallback_font(17)


def _stone_texture(surf: pygame.Surface, rect: pygame.Rect, seed: int) -> None:
    rng = random.Random(seed)
    surf.fill(STONE_MID, rect)
    for _ in range(120):
        x = rect.left + rng.randint(0, rect.width - 1)
        y = rect.top + rng.randint(0, rect.height - 1)
        c = rng.choice([STONE_DARK, STONE_LIGHT, (50, 54, 68)])
        pygame.draw.rect(surf, c, (x, y, rng.randint(2, 5), rng.randint(1, 3)))
    pygame.draw.rect(surf, STONE_LIGHT, rect, 2)
    hi = tuple(min(255, c + 35) for c in STONE_LIGHT)
    pygame.draw.line(surf, hi, rect.topleft, (rect.right - 1, rect.top), 1)
    lo = tuple(max(0, c - 25) for c in STONE_DARK)
    pygame.draw.line(surf, lo, (rect.left, rect.bottom - 1), rect.bottomright, 1)


def _draw_menu_icon(surf: pygame.Surface, kind: str, rect: pygame.Rect) -> None:
    ix = rect.left + 28
    iy = rect.centery
    if kind == "play":
        pygame.draw.polygon(surf, GREEN_PLAY, [(ix - 10, iy - 14), (ix - 10, iy + 14), (ix + 14, iy)])
    elif kind == "chest":
        pygame.draw.rect(surf, BLUE_DEEP, (ix - 14, iy - 10, 28, 20), border_radius=2)
        pygame.draw.rect(surf, BLUE_GLOW, (ix - 14, iy - 14, 28, 6), border_radius=2)
        pygame.draw.rect(surf, STONE_LIGHT, (ix - 14, iy - 10, 28, 20), 2, border_radius=2)
    elif kind == "gear":
        pygame.draw.circle(surf, (140, 140, 150), (ix, iy), 14)
        for a in range(0, 360, 45):
            rad = math.radians(a)
            x1 = ix + int(10 * math.cos(rad))
            y1 = iy + int(10 * math.sin(rad))
            x2 = ix + int(18 * math.cos(rad))
            y2 = iy + int(18 * math.sin(rad))
            pygame.draw.line(surf, (180, 180, 190), (x1, y1), (x2, y2), 4)
        pygame.draw.circle(surf, (60, 62, 72), (ix, iy), 6)
    elif kind == "quit":
        pygame.draw.line(surf, (255, 80, 80), (ix - 12, iy - 12), (ix + 12, iy + 12), 5)
        pygame.draw.line(surf, (255, 80, 80), (ix - 12, iy + 12), (ix + 12, iy - 12), 5)


def _draw_stone_button(
    surf: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    icon: str,
    hovered: bool,
    seed: int,
) -> None:
    r = rect.inflate(4, 4) if hovered else rect
    tmp = pygame.Surface((r.w, r.h))
    _stone_texture(tmp, tmp.get_rect(), seed)
    if hovered:
        overlay = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        overlay.fill((*BLUE_GLOW[:3], 40))
        tmp.blit(overlay, (0, 0))
    surf.blit(tmp, r.topleft)
    _draw_menu_icon(surf, icon, pygame.Rect(r.left, r.top, r.w, r.h))
    txt = _button_font.render(label, True, WHITE)
    surf.blit(txt, (r.left + 52, r.centery - txt.get_height() // 2))


def _draw_robot_tip(surf: pygame.Surface, t: float) -> None:
    rx, ry = SCREEN_WIDTH - 200, SCREEN_HEIGHT - 140
    pygame.draw.rect(surf, ROBOT_BLUE, (rx - 36, ry - 50, 72, 70), border_radius=6)
    pygame.draw.rect(surf, (40, 90, 150), (rx - 36, ry - 50, 72, 70), 2, border_radius=6)
    pygame.draw.rect(surf, (20, 40, 70), (rx - 24, ry - 42, 48, 28))
    eye_y = ry - 32
    pygame.draw.rect(surf, (180, 220, 255), (rx - 16, eye_y, 12, 8))
    pygame.draw.rect(surf, (180, 220, 255), (rx + 4, eye_y, 12, 8))
    pygame.draw.rect(surf, (60, 80, 120), (rx - 6, eye_y + 12, 12, 3))
    pygame.draw.rect(surf, ROBOT_BLUE, (rx - 50, ry - 30, 14, 36), border_radius=3)
    pygame.draw.rect(surf, ROBOT_BLUE, (rx + 36, ry - 30, 14, 36), border_radius=3)
    scr = pygame.Rect(rx + 44, ry - 38, 28, 40)
    pygame.draw.rect(surf, (230, 210, 160), scr, border_radius=2)
    pygame.draw.rect(surf, (120, 100, 70), scr, 1, border_radius=2)
    pygame.draw.rect(surf, ROBOT_BLUE, (rx - 22, ry + 18, 16, 22), border_radius=3)
    pygame.draw.rect(surf, ROBOT_BLUE, (rx + 6, ry + 18, 16, 22), border_radius=3)
    tip_r = pygame.Rect(SCREEN_WIDTH - 520, SCREEN_HEIGHT - 118, 300, 72)
    pulse = int(80 + 40 * math.sin(t * 3))
    pygame.draw.rect(surf, (10, 40, 20), tip_r, border_radius=4)
    pygame.draw.rect(surf, (GREEN_TIP[0] // 2, GREEN_TIP[1] // 2, GREEN_TIP[2] // 2), tip_r, 2, border_radius=4)
    glow_s = pygame.Surface((tip_r.w, tip_r.h), pygame.SRCALPHA)
    pygame.draw.rect(glow_s, (*GREEN_TIP[:3], pulse // 4), glow_s.get_rect(), border_radius=4)
    surf.blit(glow_s, tip_r.topleft)
    tip_lines = ["TIP: Think before you type...", "The dungeon punishes mistakes."]
    for i, line in enumerate(tip_lines):
        surf.blit(_tip_font.render(line, True, GREEN_TIP), (tip_r.left + 12, tip_r.top + 10 + i * 22))


def _draw_interactive_settings(surf: pygame.Surface, mouse_pos, show: bool) -> bool:
    s = _settings_state
    pr = pygame.Rect(SCREEN_WIDTH - 620, 200, 380, 480)

    # Rects
    music_bar   = pygame.Rect(pr.left + 28, pr.top + 160, pr.width - 56, 14)
    sfx_bar     = pygame.Rect(pr.left + 28, pr.top + 240, pr.width - 56, 14)
    arrow_y     = pr.top + 350
    left_arrow  = pygame.Rect(pr.left + 60,   arrow_y, 40, 28)
    right_arrow = pygame.Rect(pr.right - 100, arrow_y, 40, 28)
    back_r      = pygame.Rect(pr.centerx - 70, pr.bottom - 56, 140, 36)

    mouse_pressed = pygame.mouse.get_pressed()

    # Click handling
    if mouse_pressed[0]:
        if music_bar.collidepoint(mouse_pos):
            s["dragging_music"] = True
        if sfx_bar.collidepoint(mouse_pos):
            s["dragging_sfx"] = True
        if left_arrow.collidepoint(mouse_pos):
            s["theme_index"] = (s["theme_index"] - 1) % len(s["themes"])
        if right_arrow.collidepoint(mouse_pos):
            s["theme_index"] = (s["theme_index"] + 1) % len(s["themes"])
        if back_r.collidepoint(mouse_pos):
            return False  # close panel
    else:
        s["dragging_music"] = False
        s["dragging_sfx"]   = False

    if s["dragging_music"]:
        s["music_vol"] = max(0.0, min(1.0, (mouse_pos[0] - music_bar.left) / music_bar.width))
        pygame.mixer.music.set_volume(s["music_vol"]) # update volume immediately
    if s["dragging_sfx"]:
        s["sfx_vol"] = max(0.0, min(1.0, (mouse_pos[0] - sfx_bar.left) / sfx_bar.width))

    # Draw panel
    pygame.draw.rect(surf, (36, 38, 48), pr)
    pygame.draw.rect(surf, METAL_FRAME, pr, 4)
    pygame.draw.rect(surf, (26, 28, 36), pr.inflate(-24, -24))

    title = _button_font.render("SETTINGS", True, WHITE)
    surf.blit(title, (pr.centerx - title.get_width() // 2, pr.top + 16))

    # Text speed
    surf.blit(_small.render("TEXT SPEED", True, (200, 200, 210)), (pr.left + 28, pr.top + 70))
    surf.blit(_small.render("SLOW    NORMAL    INSTANT", True, (160, 170, 190)), (pr.left + 28, pr.top + 96))

    # Music
    surf.blit(_small.render("MUSIC", True, (200, 200, 210)), (pr.left + 28, pr.top + 140))
    pygame.draw.rect(surf, (30, 32, 40), music_bar, border_radius=4)
    mx = music_bar.left + int((music_bar.width - 16) * s["music_vol"])
    pygame.draw.rect(surf, YELLOW_GLOW, (mx, music_bar.top - 2, 16, 18), border_radius=3)

    # SFX
    surf.blit(_small.render("SFX", True, (200, 200, 210)), (pr.left + 28, pr.top + 220))
    pygame.draw.rect(surf, (30, 32, 40), sfx_bar, border_radius=4)
    sx = sfx_bar.left + int((sfx_bar.width - 16) * s["sfx_vol"])
    pygame.draw.rect(surf, YELLOW_GLOW, (sx, sfx_bar.top - 2, 16, 18), border_radius=3)

    # Syntax theme
    surf.blit(_small.render("SYNTAX THEME", True, (200, 200, 210)), (pr.left + 28, pr.top + 300))
    pygame.draw.rect(surf, (50, 55, 70), left_arrow, border_radius=4)
    pygame.draw.rect(surf, (50, 55, 70), right_arrow, border_radius=4)
    tri_l = [(left_arrow.right - 8, left_arrow.top + 6), (left_arrow.right - 8, left_arrow.bottom - 6), (left_arrow.left + 6, left_arrow.centery)]
    tri_r = [(right_arrow.left + 8, right_arrow.top + 6), (right_arrow.left + 8, right_arrow.bottom - 6), (right_arrow.right - 6, right_arrow.centery)]
    pygame.draw.polygon(surf, BLUE_GLOW, tri_l)
    pygame.draw.polygon(surf, BLUE_GLOW, tri_r)
    theme_colors = {"GREEN": (60, 255, 140), "BLUE": (80, 180, 255), "ORANGE": (255, 160, 60), "PURPLE": (180, 100, 255)}
    current = s["themes"][s["theme_index"]]
    th = _button_font.render(current, True, theme_colors[current])
    surf.blit(th, (pr.centerx - th.get_width() // 2, arrow_y + 4))

    # Back button
    pygame.draw.rect(surf, STONE_MID, back_r, border_radius=4)
    pygame.draw.rect(surf, STONE_LIGHT, back_r, 2, border_radius=4)
    bt = _button_font.render("BACK", True, WHITE)
    surf.blit(bt, (back_r.centerx - bt.get_width() // 2, back_r.centery - bt.get_height() // 2))

    return True  # keep panel open

def main_menu():
    from src.screens.settings import settings_screen
    from src.screens.tutorial import tutorial_screen

    show_settings = False

    bw, bh = 300, 52
    by0 = 340
    gap = 16

    rects = [
        pygame.Rect(480, by0 + 0 * (bh + gap), bw, bh),  # START
        pygame.Rect(480, by0 + 1 * (bh + gap), bw, bh),  # CONTINUE
        pygame.Rect(240, 460 + 2 * (bh + gap), bw, bh),  # SETTINGS
        pygame.Rect(240, 460 + 3 * (bh + gap), bw, bh),  # QUIT
    ]

    icons = ["play", "chest", "gear", "quit"]
    labels = ["START NEW GAME", "CONTINUE", "SETTINGS", "QUIT"]
    seeds = [11, 22, 33, 44]

    clock = pygame.time.Clock()
    logo = pygame.image.load("assets/images/logos/codebreakLogo.png").convert_alpha()
    logo = pygame.transform.scale(logo, (620, 400))
    running = True

    pygame.mixer.music.load("assets/audios/mainMenuBgm.mp3")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)  # -1 means loop forever

    while running:
        t = pygame.time.get_ticks() / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        hovers = [r.collidepoint(mouse_pos) for r in rects]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if rects[0].collidepoint(event.pos):
                    pygame.mixer.music.stop()
                    game_screen(screen)
                    pygame.mixer.music.load("assets/audios/mainMenuBgm.mp3")  # ← add
                    pygame.mixer.music.set_volume(0.5)                         # ← add
                    pygame.mixer.music.play(-1) # resume when back
                if rects[1].collidepoint(event.pos):
                    pygame.mixer.music.stop()
                    tutorial_screen(screen)
                if rects[2].collidepoint(event.pos):
                    show_settings = not show_settings
                if rects[3].collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()


        screen.blit(background, (0, 0))
        screen.blit(logo, (190, 0))

        for rect, label, icon, h, seed in zip(rects, labels, icons, hovers, seeds):
            _draw_stone_button(screen, rect, label, icon, h, seed)

        _draw_robot_tip(screen, t)
        ver = _small.render("v1.0", True, WHITE)
        screen.blit(ver, (16, SCREEN_HEIGHT - ver.get_height() - 12))

        if show_settings:
            show_settings = _draw_interactive_settings(screen, mouse_pos, show_settings)

        pygame.display.flip()
        clock.tick(60)