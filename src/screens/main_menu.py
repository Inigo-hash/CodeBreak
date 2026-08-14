import math
import random
import sys
import pygame
from src.screens.game import game_screen
from src.settings_state import settings_state as _settings_state

# Import config first — it sets the SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS env var,
# which must exist before pygame.init() brings up the video subsystem.
from src.config import FULLSCREEN

# Initialize Pygame
pygame.init()

if FULLSCREEN:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    
else:
    screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    
    

SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()



pygame.display.set_caption("CodeBreak - Main Menu")

background = pygame.image.load("assets/images/backgrounds/mainMenuBg1.png").convert()
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
screen.blit(background, (0, 0))

# Palette
STONE_DARK = (14, 14, 18)
STONE_MID = (24, 25, 31)
STONE_LIGHT = (38, 39, 47)
BLUE_GLOW = (80, 180, 255)
BLUE_DEEP = (35, 90, 140)
YELLOW_GLOW = (255, 220, 120)
GREEN_TIP = (60, 255, 140)
GREEN_PLAY = (80, 220, 120)
WHITE = (255, 255, 255)
METAL_FRAME = (90, 94, 110)
ROBOT_BLUE = (70, 140, 220)
SILVER_LIGHT = (225, 228, 232)
SILVER_MID = (160, 165, 172)
SILVER_DARK = (95, 98, 105)
SILVER_SHINE = (250, 252, 255)

# Fonts
_CINZEL_BOLD_PATH = "assets/fonts/Cinzel-Bold.ttf"
_CINZEL_PATH = "assets/fonts/Cinzel-VariableFont_wght.ttf"



def _fallback_font(size, bold=False):
    return pygame.font.Font(None, size)


# Scale font sizes off screen height vs a 1080p reference, clamped so they
# never go microscopic on small laptop screens or oversized on big monitors.
_font_scale = max(0.65, min(1.25, SCREEN_HEIGHT / 1080))

try:
    _button_font = pygame.font.Font(_CINZEL_BOLD_PATH, max(14, int(26 * _font_scale)))
    _small = pygame.font.Font(_CINZEL_PATH, max(12, int(16 * _font_scale)))
    _tip_font = pygame.font.Font(_CINZEL_PATH, max(11, int(15 * _font_scale)))
    _ = _button_font.render("x", True, WHITE)
except Exception:
    _button_font = _fallback_font(max(14, int(24 * _font_scale)), True)
    _small = _fallback_font(max(12, int(18 * _font_scale)))
    _tip_font = _fallback_font(max(11, int(17 * _font_scale)))


def _stone_texture(surf: pygame.Surface, rect: pygame.Rect, seed: int) -> None:
    rng = random.Random(seed)

    MORTAR = (8, 8, 10)
    surf.fill(MORTAR, rect)

    brick_h = 22
    mortar_w = 3
    row = 0
    y = rect.top
    brick_cells = []  # track placed bricks so damage can reference them

    while y < rect.bottom:
        brick_w = rng.randint(58, 84)
        offset = (brick_w // 2) if row % 2 else 0
        x = rect.left - offset

        while x < rect.right:
            bw = rng.randint(58, 84)
            brick_rect = pygame.Rect(x, y, bw - mortar_w, min(brick_h, rect.bottom - y) - mortar_w)
            brick_rect = brick_rect.clip(rect)

            if brick_rect.width > 2 and brick_rect.height > 2:
                shade = rng.randint(-14, 10)
                base = tuple(max(0, min(255, c + shade)) for c in STONE_MID)
                pygame.draw.rect(surf, base, brick_rect)

                for _ in range(6):
                    sx = brick_rect.left + rng.randint(0, max(1, brick_rect.width - 2))
                    sy = brick_rect.top + rng.randint(0, max(1, brick_rect.height - 2))
                    c = rng.choice([STONE_DARK, STONE_LIGHT])
                    pygame.draw.rect(surf, c, (sx, sy, rng.randint(2, 4), rng.randint(1, 2)))

                hi = tuple(min(255, c + 30) for c in base)
                lo = tuple(max(0, c - 30) for c in base)
                pygame.draw.line(surf, hi, brick_rect.topleft, (brick_rect.right - 1, brick_rect.top), 1)
                pygame.draw.line(surf, hi, brick_rect.topleft, (brick_rect.left, brick_rect.bottom - 1), 1)
                pygame.draw.line(surf, lo, (brick_rect.left, brick_rect.bottom - 1), brick_rect.bottomright, 1)
                pygame.draw.line(surf, lo, (brick_rect.right - 1, brick_rect.top), brick_rect.bottomright, 1)

                brick_cells.append(brick_rect)

            x += bw
        y += brick_h
        row += 1

    # ---------- DAMAGE PASS ----------

    # 1. Chipped corners — carve small mortar-colored notches out of random bricks
    for b in brick_cells:
        if rng.random() < 0.35:
            corner = rng.choice(["tl", "tr", "bl", "br"])
            cw = rng.randint(4, 9)
            ch = rng.randint(4, 9)
            if corner == "tl":
                cx, cy = b.left, b.top
            elif corner == "tr":
                cx, cy = b.right - cw, b.top
            elif corner == "bl":
                cx, cy = b.left, b.bottom - ch
            else:
                cx, cy = b.right - cw, b.bottom - ch
            pygame.draw.rect(surf, MORTAR, (cx, cy, cw, ch))

    # 2. Hairline cracks — jagged dark lines crossing 1-3 bricks
    for _ in range(max(3, len(brick_cells) // 12)):
        start = rng.choice(brick_cells)
        px, py = rng.randint(start.left, start.right), rng.randint(start.top, start.bottom)
        length = rng.randint(3, 6)
        crack_color = (10, 10, 12)
        for _ in range(length):
            nx = px + rng.randint(-10, 10)
            ny = py + rng.randint(-4, 4)
            pygame.draw.line(surf, crack_color, (px, py), (nx, ny), 1)
            px, py = nx, ny

    # 3. Grime / moss patches — soft dark-green-ish blotches, mostly lower half
    moss = (26, 34, 22)
    for _ in range(max(2, len(brick_cells) // 20)):
        b = rng.choice(brick_cells)
        if b.top < rect.top + rect.height * 0.4 and rng.random() < 0.6:
            continue  # bias moss toward the lower/damp-looking area
        blot = pygame.Surface((rng.randint(10, 20), rng.randint(6, 12)), pygame.SRCALPHA)
        pygame.draw.ellipse(blot, (*moss, rng.randint(60, 110)), blot.get_rect())
        surf.blit(blot, (b.left + rng.randint(-4, 4), b.bottom - rng.randint(4, 10)))

    # 4. Crumbled mortar gaps — occasionally widen a mortar joint into a dark gap
    for b in brick_cells:
        if rng.random() < 0.12:
            gap_rect = pygame.Rect(b.right, b.top, mortar_w + rng.randint(2, 5), b.height)
            pygame.draw.rect(surf, (4, 4, 5), gap_rect.clip(rect))

    # ---------- END DAMAGE PASS ----------

    pygame.draw.rect(surf, STONE_LIGHT, rect, 2)
    hi = tuple(min(255, c + 35) for c in STONE_LIGHT)
    pygame.draw.line(surf, hi, rect.topleft, (rect.right - 1, rect.top), 1)
    lo = tuple(max(0, c - 25) for c in STONE_DARK)
    pygame.draw.line(surf, lo, (rect.left, rect.bottom - 1), rect.bottomright, 1)
    
_icon_anim = {"play": 0.0, "chest": 0.0, "gear": 0.0, "quit": 0.0}


def _update_icon_anims(hover_map: dict, dt: float, speed: float = 8.0) -> None:
    for kind, hovered in hover_map.items():
        target = 1.0 if hovered else 0.0
        current = _icon_anim.get(kind, 0.0)
        current += (target - current) * min(1.0, speed * dt)
        _icon_anim[kind] = current

def _draw_medallion(surf: pygame.Surface, center: tuple, radius: int, seed: int) -> None:
    rng = random.Random(seed)
    cx, cy = center

    # Outer metal ring
    pygame.draw.circle(surf, METAL_FRAME, (cx, cy), radius + 4)
    pygame.draw.circle(surf, STONE_DARK, (cx, cy), radius + 4, 2)

    # Inner stone fill
    pygame.draw.circle(surf, STONE_MID, (cx, cy), radius)

    # Subtle stone texture speckles
    for _ in range(14):
        ang = rng.uniform(0, math.tau)
        dist = rng.uniform(0, radius - 3)
        x = cx + int(dist * math.cos(ang))
        y = cy + int(dist * math.sin(ang))
        c = rng.choice([STONE_DARK, STONE_LIGHT])
        pygame.draw.circle(surf, c, (x, y), rng.randint(1, 2))

    # Beveled highlight (top-left) and shadow (bottom-right)
    hi = tuple(min(255, c + 40) for c in STONE_LIGHT)
    lo = tuple(max(0, c - 25) for c in STONE_DARK)
    bbox = (cx - radius, cy - radius, radius * 2, radius * 2)
    pygame.draw.arc(surf, hi, bbox, math.radians(135), math.radians(225), 2)
    pygame.draw.arc(surf, lo, bbox, math.radians(-45), math.radians(45), 2)

    # Gold engraved ring accent
    pygame.draw.circle(surf, YELLOW_GLOW, (cx, cy), radius, 1)
    
def _draw_menu_icon(surf: pygame.Surface, kind: str, rect: pygame.Rect, hovered: bool = False, t: float = 0.0) -> None:
    ix = rect.left + 34
    iy = rect.centery
    radius = 22
    anim = _icon_anim.get(kind, 0.0)  # 0 = idle, 1 = fully hovered

    _draw_medallion(surf, (ix, iy), radius, seed=sum(map(ord, kind)))

    if kind == "play":
        flicker = math.sin(t * 14) * (1 + anim * 4)
        sway = math.sin(t * 9) * anim * 3
        pygame.draw.rect(surf, (90, 60, 40), (ix - 3, iy - 2, 6, 16), border_radius=2)
        pygame.draw.rect(surf, (60, 40, 25), (ix - 3, iy - 2, 6, 16), 1, border_radius=2)
        flame_outer = [
            (ix + sway, iy - 20 - flicker),
            (ix - 8, iy - 4),
            (ix - 4, iy - 2),
            (ix + sway * 0.5, iy - 6),
            (ix + 4, iy - 2),
            (ix + 8, iy - 4),
        ]
        pygame.draw.polygon(surf, (255, 140, 60), flame_outer)
        flame_inner = [
            (ix + sway * 0.6, iy - 15 - flicker * 0.6),
            (ix - 4, iy - 4),
            (ix, iy - 7),
            (ix + 4, iy - 4),
        ]
        pygame.draw.polygon(surf, YELLOW_GLOW, flame_inner)

    elif kind == "chest":
        half_w = 6 + int(6 * anim)
        body = pygame.Rect(ix - half_w, iy - 7, half_w * 2, 14)
        pygame.draw.rect(surf, (225, 205, 160), body)
        pygame.draw.rect(surf, (140, 115, 80), body, 1)
        pygame.draw.circle(surf, (200, 175, 130), (ix - half_w, iy), 4)
        pygame.draw.circle(surf, (200, 175, 130), (ix + half_w, iy), 4)
        pygame.draw.circle(surf, (140, 115, 80), (ix - half_w, iy), 4, 1)
        pygame.draw.circle(surf, (140, 115, 80), (ix + half_w, iy), 4, 1)
        if anim > 0.3:
            fade = min(1.0, (anim - 0.3) / 0.7)
            line_w = int((half_w - 3) * fade)
            for i in range(3):
                y = iy - 4 + i * 4
                pygame.draw.line(surf, (150, 125, 90), (ix - line_w, y), (ix + line_w, y), 1)

    elif kind == "gear":
        speed = 0.4 + anim * 3.5
        base_angle = t * speed * 60

        # Base metal ring with dark edge for depth
        pygame.draw.circle(surf, SILVER_MID, (ix, iy), 13)
        pygame.draw.circle(surf, SILVER_DARK, (ix, iy), 13, 2)

        # Rotating spokes with light/dark faces to read as beveled metal
        for a in range(0, 360, 60):
            rad = math.radians(a + base_angle)
            x1 = ix + int(6 * math.cos(rad))
            y1 = iy + int(6 * math.sin(rad))
            x2 = ix + int(13 * math.cos(rad))
            y2 = iy + int(13 * math.sin(rad))
            pygame.draw.line(surf, SILVER_LIGHT, (x1, y1), (x2, y2), 2)
            pygame.draw.line(surf, SILVER_DARK, (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 1)

        # Inner hub
        pygame.draw.circle(surf, SILVER_DARK, (ix, iy), 7)
        pygame.draw.circle(surf, SILVER_MID, (ix, iy), 6)
        pygame.draw.circle(surf, SILVER_LIGHT, (ix, iy), 6, 1)

        # Fixed highlight arc (doesn't rotate) to sell the "shiny metal" look
        bbox = (ix - 12, iy - 12, 24, 24)
        pygame.draw.arc(surf, SILVER_SHINE, bbox, math.radians(120), math.radians(200), 2)

        # Center pin
        pygame.draw.circle(surf, WHITE, (ix, iy), 2)

    elif kind == "quit":
        doorway = pygame.Rect(ix - 10, iy - 14, 20, 28)
        pygame.draw.rect(surf, (15, 10, 8), doorway, border_radius=3)
        pygame.draw.rect(surf, (30, 18, 15), doorway, 2, border_radius=3)
        door_w = max(2, int(20 * (1 - 0.7 * anim)))
        panel = pygame.Rect(ix - 10, iy - 14, door_w, 28)
        pygame.draw.rect(surf, (60, 38, 30), panel, border_radius=2)
        pygame.draw.rect(surf, (35, 22, 18), panel, 1, border_radius=2)
        if door_w > 6:
            knob_x = ix - 10 + door_w - 4
            pygame.draw.circle(surf, YELLOW_GLOW, (knob_x, iy), 2)

def _draw_stone_button(
    surf: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    icon: str,
    hovered: bool,
    seed: int,
    t: float = 0.0,
) -> None:
    r = rect.inflate(4, 4) if hovered else rect
    tmp = pygame.Surface((r.w, r.h))
    _stone_texture(tmp, tmp.get_rect(), seed)
    if hovered:
        overlay = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        overlay.fill((*BLUE_GLOW[:3], 40))
        tmp.blit(overlay, (0, 0))
    surf.blit(tmp, r.topleft)
    _draw_menu_icon(surf, icon, pygame.Rect(r.left, r.top, r.w, r.h), hovered, t)
    txt = _button_font.render(label, True, WHITE)
    surf.blit(txt, (r.left + 68, r.centery - txt.get_height() // 2))


def _draw_robot_tip(surf: pygame.Surface, t: float) -> None:
    rx, ry = SCREEN_WIDTH - 90, SCREEN_HEIGHT - 140
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

    # Tip box anchored off the robot's own position (rx/ry) instead of a
    # fixed SCREEN_WIDTH offset, so moving the robot moves the box with it.
    robot_left_edge = rx - 50  # leftmost point of the robot (its arm)
    tip_gap = 20
    tip_w, tip_h = 300, 72
    tip_r = pygame.Rect(robot_left_edge - tip_gap - tip_w, ry + 22, tip_w, tip_h)

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
    panel_width = 380
    panel_height = 480

    pr = pygame.Rect(
        (SCREEN_WIDTH - panel_width) // 2,
        (SCREEN_HEIGHT - panel_height) // 2,
        panel_width,
        panel_height
    )

    # Rects
    music_bar   = pygame.Rect(pr.left + 28, pr.top + 160, pr.width - 56, 14)
    sfx_bar     = pygame.Rect(pr.left + 28, pr.top + 240, pr.width - 56, 14)
    arrow_y     = pr.top + 350
    left_arrow  = pygame.Rect(pr.left + 60,   arrow_y, 40, 28)
    right_arrow = pygame.Rect(pr.right - 100, arrow_y, 40, 28)
    back_r      = pygame.Rect(pr.centerx - 70, pr.bottom - 56, 140, 36)

    mouse_down = pygame.mouse.get_pressed()[0]
    # Edge-triggered click: True only on the frame the button first goes
    # down. Using the raw held state here made theme_index (and the back
    # button) fire on every frame the mouse stayed down, cycling through
    # syntax themes ~60x/sec and looking like a glitch/flicker.
    mouse_clicked = mouse_down and not _draw_interactive_settings.prev_pressed
    _draw_interactive_settings.prev_pressed = mouse_down

    # Click handling
    if mouse_down:
        if music_bar.collidepoint(mouse_pos):
            s["dragging_music"] = True
        if sfx_bar.collidepoint(mouse_pos):
            s["dragging_sfx"] = True
    else:
        s["dragging_music"] = False
        s["dragging_sfx"]   = False

    if mouse_clicked:
        if left_arrow.collidepoint(mouse_pos):
            s["theme_index"] = (s["theme_index"] - 1) % len(s["themes"])
        if right_arrow.collidepoint(mouse_pos):
            s["theme_index"] = (s["theme_index"] + 1) % len(s["themes"])
        if back_r.collidepoint(mouse_pos):
            return False  # close panel

    if s["dragging_music"]:
        s["music_vol"] = max(0.0, min(1.0, (mouse_pos[0] - music_bar.left) / music_bar.width))
        pygame.mixer.music.set_volume(s["music_vol"]) # update volume immediately
    if s["dragging_sfx"]:
        s["sfx_vol"] = max(0.0, min(1.0, (mouse_pos[0] - sfx_bar.left) / sfx_bar.width))

    # Draw panel
    # ---------- Blur Background ----------
    blur = pygame.transform.smoothscale(
        surf,
        (SCREEN_WIDTH // 8, SCREEN_HEIGHT // 8)
    )

    blur = pygame.transform.smoothscale(
        blur,
        (SCREEN_WIDTH, SCREEN_HEIGHT)
    )

    surf.blit(blur, (0, 0))

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))
    surf.blit(overlay, (0, 0))
    # -------------------------------------

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

_draw_interactive_settings.prev_pressed = False

def main_menu():
    from src.screens.settings import settings_screen
    from src.screens.tutorial import tutorial_screen

    show_settings = False

    # Load logo and compute its height FIRST
    logo = pygame.image.load("assets/images/logos/codebreakLogo.png").convert_alpha()
    logo_width = int(SCREEN_WIDTH * 0.50)
    aspect_ratio = logo.get_height() / logo.get_width()
    logo_height = int(logo_width * aspect_ratio)
    logo = pygame.transform.smoothscale(logo, (logo_width, logo_height))

    # This offset is used BOTH for the layout math below AND for the
    # actual blit position in the draw loop, so they can never drift
    # out of sync with each other again.
    logo_top_offset = int(SCREEN_HEIGHT * 0.04)
    logo_bottom = logo_top_offset + logo_height

    bw = int(SCREEN_WIDTH * 0.20)
    bh = int(SCREEN_HEIGHT * 0.075)
    gap = int(SCREEN_HEIGHT * 0.02)

    # Buttons can never shrink smaller than what the label/icon actually
    # need — this is what stops rows from visually colliding on smaller
    # or differently-scaled screens.
    min_bh = int(_button_font.get_height() * 1.8)
    min_gap = int(_button_font.get_height() * 0.3)
    bh = max(bh, min_bh)
    gap = max(gap, min_gap)

    bottom_reserved = int(SCREEN_HEIGHT * 0.18)
    available_top = int(SCREEN_HEIGHT * 0.5)
    available_bottom = SCREEN_HEIGHT - bottom_reserved
    available_height = max(1, available_bottom - available_top)

    block_height = 4 * bh + 3 * gap
    if block_height > available_height:
        shrink = available_height / block_height
        bh = max(min_bh, int(bh * shrink))   # never shrink below min_bh
        gap = max(min_gap, int(gap * shrink))  # never shrink below min_gap
        block_height = 4 * bh + 3 * gap

    by0 = available_top + max(0, (available_height - block_height) // 2)

    center_x = SCREEN_WIDTH // 2 - bw // 2   # horizontally centered

    rects = [
        pygame.Rect(center_x, by0 + 0 * (bh + gap), bw, bh),  # START
        pygame.Rect(center_x, by0 + 1 * (bh + gap), bw, bh),  # CONTINUE
        pygame.Rect(center_x, by0 + 2 * (bh + gap), bw, bh),  # SETTINGS
        pygame.Rect(center_x, by0 + 3 * (bh + gap), bw, bh),  # QUIT
    ]

    icons = ["play", "chest", "gear", "quit"]
    labels = ["START NEW GAME", "CONTINUE", "SETTINGS", "QUIT"]
    seeds = [11, 22, 33, 44]

    clock = pygame.time.Clock()
    clock.tick(60)
    running = True

    pygame.mixer.music.load("assets/audios/mainMenuBgm.mp3")
    pygame.mixer.music.set_volume(_settings_state["music_vol"])
    pygame.mixer.music.play(-1)  # -1 means loop forever

    while running:
        dt = clock.tick(60) / 1000.0
        t = pygame.time.get_ticks() / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        hovers = [r.collidepoint(mouse_pos) for r in rects]
        _update_icon_anims(dict(zip(icons, hovers)), dt)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not show_settings:
                    if rects[0].collidepoint(event.pos):
                        pygame.mixer.music.stop()
                        game_screen(screen)
                        pygame.mixer.music.load("assets/audios/mainMenuBgm.mp3")
                        pygame.mixer.music.set_volume(_settings_state["music_vol"])
                        pygame.mixer.music.play(-1)
                    if rects[1].collidepoint(event.pos):
                        pygame.mixer.music.stop()
                        tutorial_screen(screen)
                    if rects[2].collidepoint(event.pos):
                        show_settings = not show_settings
                    if rects[3].collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()

        screen.blit(background, (0, 0))
        screen.blit(
            logo,
            (
                SCREEN_WIDTH // 2 - logo.get_width() // 2,
                logo_top_offset
            )
        )

        for rect, label, icon, h, seed in zip(rects, labels, icons, hovers, seeds):
            _draw_stone_button(screen, rect, label, icon, h, seed, t)

        _draw_robot_tip(screen, t)
        ver = _small.render("v1.0", True, WHITE)
        screen.blit(ver, (16, SCREEN_HEIGHT - ver.get_height() - 12))

        if show_settings:
            show_settings = _draw_interactive_settings(screen, mouse_pos, show_settings)

        pygame.display.flip()
        