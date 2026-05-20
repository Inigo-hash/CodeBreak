import math
import random
import sys

import pygame

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("CodeBreak - Main Menu")

background = pygame.image.load("src/assets/images/mainMenuBg.png").convert()
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
screen.blit(background, (0, 0))

# Palette — dungeon + digital accents
STONE_DARK = (28, 30, 38)
STONE_MID = (42, 46, 58)
STONE_LIGHT = (62, 68, 82)
BLUE_GLOW = (80, 180, 255)
BLUE_DEEP = (35, 90, 140)
ORANGE_ACCENT = (255, 160, 60)
YELLOW_GLOW = (255, 220, 120)
PYTHON_BLUE = (55, 118, 200)
PYTHON_YELLOW = (255, 212, 59)
GREEN_TIP = (60, 255, 140)
GREEN_PLAY = (80, 220, 120)
WHITE = (255, 255, 255)
METAL_FRAME = (90, 94, 110)
ROBOT_BLUE = (70, 140, 220)

# Fonts
_title_large = pygame.font.SysFont("consolas", 52, bold=True)
_title_sub = pygame.font.SysFont("consolas", 38, bold=True)
_button_font = pygame.font.SysFont("consolas", 22, bold=True)
_small = pygame.font.SysFont("consolas", 18)
_tip_font = pygame.font.SysFont("consolas", 17)
_panel_title = pygame.font.SysFont("consolas", 26, bold=True)
_label_font = pygame.font.SysFont("consolas", 16)


def _fallback_font(size, bold=False):
    f = pygame.font.Font(None, size)
    return f


try:
    _ = _title_large.render("x", True, WHITE)
except Exception:
    _title_large = _fallback_font(52, True)
    _title_sub = _fallback_font(38, True)
    _button_font = _fallback_font(24, True)
    _small = _fallback_font(18)
    _tip_font = _fallback_font(17)
    _panel_title = _fallback_font(26, True)
    _label_font = _fallback_font(16)


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


def _draw_settings_panel(surf: pygame.Surface, t: float) -> None:
    pr = pygame.Rect(SCREEN_WIDTH - 420, 70, 380, 480)
    pygame.draw.rect(surf, (36, 38, 48), pr)
    pygame.draw.rect(surf, METAL_FRAME, pr, 4)
    inner = pr.inflate(-24, -24)
    pygame.draw.rect(surf, (26, 28, 36), inner)
    title = _panel_title.render("SETTINGS", True, WHITE)
    surf.blit(title, (pr.centerx - title.get_width() // 2, pr.top + 16))
    # window controls
    pygame.draw.rect(surf, (100, 100, 110), (pr.right - 52, pr.top + 14, 18, 18), 1)
    pygame.draw.rect(surf, (100, 100, 110), (pr.right - 28, pr.top + 14, 18, 18), 1)
    y = pr.top + 70
    surf.blit(_label_font.render("TEXT SPEED", True, (200, 200, 210)), (pr.left + 28, y))
    opts = "SLOW    NORMAL    INSTANT"
    surf.blit(_small.render(opts, True, (160, 170, 190)), (pr.left + 28, y + 26))
    y += 72
    surf.blit(_label_font.render("MUSIC", True, (200, 200, 210)), (pr.left + 28, y))
    bar = pygame.Rect(pr.left + 28, y + 28, pr.width - 56, 14)
    pygame.draw.rect(surf, (30, 32, 40), bar, border_radius=4)
    hx = bar.left + int((bar.w - 16) * (0.55 + 0.05 * math.sin(t)))
    pygame.draw.rect(surf, YELLOW_GLOW, (hx, bar.top - 2, 16, 18), border_radius=3)
    y += 72
    surf.blit(_label_font.render("SFX", True, (200, 200, 210)), (pr.left + 28, y))
    bar2 = pygame.Rect(pr.left + 28, y + 28, pr.width - 56, 14)
    pygame.draw.rect(surf, (30, 32, 40), bar2, border_radius=4)
    hx2 = bar2.left + int((bar2.w - 16) * (0.45 + 0.04 * math.cos(t * 1.3)))
    pygame.draw.rect(surf, YELLOW_GLOW, (hx2, bar2.top - 2, 16, 18), border_radius=3)
    y += 72
    surf.blit(_label_font.render("SYNTAX THEME", True, (200, 200, 210)), (pr.left + 28, y))
    row_y = y + 30
    pygame.draw.rect(surf, (50, 55, 70), (pr.left + 60, row_y, 40, 28), border_radius=4)
    pygame.draw.rect(surf, (50, 55, 70), (pr.right - 100, row_y, 40, 28), border_radius=4)
    tri_l = [(pr.left + 78, row_y + 6), (pr.left + 78, row_y + 22), (pr.left + 68, row_y + 14)]
    tri_r = [(pr.right - 78, row_y + 6), (pr.right - 78, row_y + 22), (pr.right - 68, row_y + 14)]
    pygame.draw.polygon(surf, BLUE_GLOW, tri_l)
    pygame.draw.polygon(surf, BLUE_GLOW, tri_r)
    th = _button_font.render("GREEN", True, GREEN_TIP)
    surf.blit(th, (pr.centerx - th.get_width() // 2, row_y + 4))
    back_r = pygame.Rect(pr.centerx - 70, pr.bottom - 56, 140, 36)
    back_sub = surf.subsurface(back_r)
    _stone_texture(back_sub, pygame.Rect(0, 0, back_r.width, back_r.height), 99)
    pygame.draw.rect(surf, STONE_LIGHT, back_r, 2)
    bt = _button_font.render("BACK", True, WHITE)
    surf.blit(bt, (back_r.centerx - bt.get_width() // 2, back_r.centery - bt.get_height() // 2))


def _draw_robot_tip(surf: pygame.Surface, t: float) -> None:
    rx, ry = SCREEN_WIDTH - 200, SCREEN_HEIGHT - 140
    # Robot body
    pygame.draw.rect(surf, ROBOT_BLUE, (rx - 36, ry - 50, 72, 70), border_radius=6)
    pygame.draw.rect(surf, (40, 90, 150), (rx - 36, ry - 50, 72, 70), 2, border_radius=6)
    pygame.draw.rect(surf, (20, 40, 70), (rx - 24, ry - 42, 48, 28))
    # face
    eye_y = ry - 32
    pygame.draw.rect(surf, (180, 220, 255), (rx - 16, eye_y, 12, 8))
    pygame.draw.rect(surf, (180, 220, 255), (rx + 4, eye_y, 12, 8))
    pygame.draw.rect(surf, (60, 80, 120), (rx - 6, eye_y + 12, 12, 3))
    # arms + scroll
    pygame.draw.rect(surf, ROBOT_BLUE, (rx - 50, ry - 30, 14, 36), border_radius=3)
    pygame.draw.rect(surf, ROBOT_BLUE, (rx + 36, ry - 30, 14, 36), border_radius=3)
    scr = pygame.Rect(rx + 44, ry - 38, 28, 40)
    pygame.draw.rect(surf, (230, 210, 160), scr, border_radius=2)
    pygame.draw.rect(surf, (120, 100, 70), scr, 1, border_radius=2)
    # legs
    pygame.draw.rect(surf, ROBOT_BLUE, (rx - 22, ry + 18, 16, 22), border_radius=3)
    pygame.draw.rect(surf, ROBOT_BLUE, (rx + 6, ry + 18, 16, 22), border_radius=3)
    # Tip box
    tip_r = pygame.Rect(SCREEN_WIDTH - 520, SCREEN_HEIGHT - 118, 300, 72)
    pulse = int(80 + 40 * math.sin(t * 3))
    pygame.draw.rect(surf, (10, 40, 20), tip_r, border_radius=4)
    pygame.draw.rect(surf, (GREEN_TIP[0] // 2, GREEN_TIP[1] // 2, GREEN_TIP[2] // 2), tip_r, 2, border_radius=4)
    glow_s = pygame.Surface((tip_r.w, tip_r.h), pygame.SRCALPHA)
    pygame.draw.rect(glow_s, (*GREEN_TIP[:3], pulse // 4), glow_s.get_rect(), border_radius=4)
    surf.blit(glow_s, tip_r.topleft)
    tip_lines = [
        "TIP: Think before you type...",
        "The dungeon punishes mistakes.",
    ]
    for i, line in enumerate(tip_lines):
        surf.blit(_tip_font.render(line, True, GREEN_TIP), (tip_r.left + 12, tip_r.top + 10 + i * 22))


def main_menu():
    from src.screens.settings import settings_screen
    from src.screens.tutorial import tutorial_screen

    bw, bh = 300, 52
    by0 = 250
    gap = 16
    rects = [
        pygame.Rect(380, by0 + 0 * (bh + gap), bw, bh),  # START
        pygame.Rect(380, by0 + 1 * (bh + gap), bw, bh),  # CONTINUE
        pygame.Rect(160,  320 + 2 * (bh + gap), bw, bh),  # SETTINGS
        pygame.Rect(160,  320 + 3 * (bh + gap), bw, bh),  # QUIT
    ]

    icons = ["play", "chest", "gear", "quit"]
    labels = ["START NEW GAME", "CONTINUE", "SETTINGS", "QUIT"]
    seeds = [11, 22, 33, 44]

    clock = pygame.time.Clock()
    running = True

    while running:
        t = pygame.time.get_ticks() / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        hovers = [r.collidepoint(mouse_pos) for r in rects]

        if rects[0].collidepoint(mouse_pos) and mouse_pressed[0]:
            tutorial_screen(screen)
        if rects[1].collidepoint(mouse_pos) and mouse_pressed[0]:
            tutorial_screen(screen)
        if rects[2].collidepoint(mouse_pos) and mouse_pressed[0]:
            settings_screen(screen)
        if rects[3].collidepoint(mouse_pos) and mouse_pressed[0]:
            pygame.quit()
            sys.exit()

        # Draw background first
        screen.blit(background, (0, 0))

        for rect, label, icon, h, seed in zip(rects, labels, icons, hovers, seeds):
            _draw_stone_button(screen, rect, label, icon, h, seed)

        _draw_settings_panel(screen, t)
        _draw_robot_tip(screen, t)
        ver = _small.render("v1.0", True, WHITE)
        screen.blit(ver, (16, SCREEN_HEIGHT - ver.get_height() - 12))

        pygame.display.flip()
        clock.tick(60)
