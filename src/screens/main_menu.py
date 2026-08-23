import math
import random
import sys
from pathlib import Path
import pygame
from src.screens.game import game_screen
from src.settings_state import settings_state as _settings_state
from src.screens.settings import SettingsPanel
from src.screens.how_to_play import how_to_play_screen
from src.screens.start_game_menu import start_game_menu
from src.ui.gear_icon import draw_gear, draw_medallion
from src.ui.theme import UI_COLORS, draw_button, draw_panel, title_font, ui_font

MM_ICONS = ["play", "book", "gear", "quit"]
MM_LABELS = ["START GAME", "HOW TO PLAY", "SETTINGS", "QUIT"]
MM_SEEDS = [11, 22, 33, 44]


def render_main_menu_buttons(surface, rects, t=0.0):
    """Draw the main menu's buttons onto an OFFSCREEN surface — used by
    start_game_menu.py to build the crumble-transition target when
    returning to the main menu, without touching the visible screen."""
    for rect, label, icon, seed in zip(rects, MM_LABELS, MM_ICONS, MM_SEEDS):
        _draw_stone_button(surface, rect, label, icon, False, seed, t)

# Import config first — it sets the SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS env var,
# which must exist before pygame.init() brings up the video subsystem.
from src.config import FULLSCREEN
from src.display import create_display

# Initialize Pygame
pygame.init()

screen = create_display(FULLSCREEN)
    
    

SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()



pygame.display.set_caption("CodeBreak - Main Menu")

background = pygame.image.load("assets/images/backgrounds/mainMenuBg1.png").convert()
background = pygame.transform.smoothscale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))

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

def compute_menu_layout(screen_w, screen_h, count):
    """Shared button-layout math so every menu screen (main menu,
    start-game menu, etc.) lines up under the logo identically."""
    bw = int(screen_w * 0.20)
    bh = int(screen_h * 0.075)
    gap = int(screen_h * 0.02)

    min_bh = int(_button_font.get_height() * 1.8)
    min_gap = int(_button_font.get_height() * 0.3)
    bh = max(bh, min_bh)
    gap = max(gap, min_gap)

    bottom_reserved = int(screen_h * 0.18)
    available_top = int(screen_h * 0.5)
    available_bottom = screen_h - bottom_reserved
    available_height = max(1, available_bottom - available_top)

    block_height = count * bh + (count - 1) * gap
    if block_height > available_height:
        shrink = available_height / block_height
        bh = max(min_bh, int(bh * shrink))
        gap = max(min_gap, int(gap * shrink))
        block_height = count * bh + (count - 1) * gap

    by0 = available_top + max(0, (available_height - block_height) // 2)
    center_x = screen_w // 2 - bw // 2

    rects = [pygame.Rect(center_x, by0 + i * (bh + gap), bw, bh) for i in range(count)]
    return rects, bw, bh, gap, center_x, by0

# Scale font sizes off screen height vs a 1080p reference, clamped so they
# never go microscopic on small laptop screens or oversized on big monitors.
_font_scale = max(0.65, min(1.25, SCREEN_HEIGHT / 1080))

_button_font = title_font(max(14, int(26 * _font_scale)))
_small = ui_font(max(12, int(16 * _font_scale)))
_tip_font = ui_font(max(11, int(15 * _font_scale)))


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
    
_icon_anim = {"play": 0.0, "chest": 0.0, "gear": 0.0, "quit": 0.0, "book": 0.0}


def _update_icon_anims(hover_map: dict, dt: float, speed: float = 8.0) -> None:
    for kind, hovered in hover_map.items():
        target = 1.0 if hovered else 0.0
        current = _icon_anim.get(kind, 0.0)
        current += (target - current) * min(1.0, speed * dt)
        _icon_anim[kind] = current

# The medallion and gear artwork now lives in src/ui/gear_icon.py, so
# the settings button inside the coding environment draws the exact
# same wheel instead of keeping a second copy of it here.
_draw_medallion = draw_medallion


def _draw_menu_icon(surf: pygame.Surface, kind: str, rect: pygame.Rect, hovered: bool = False, t: float = 0.0) -> None:
    ix = rect.left + 34
    iy = rect.centery
    radius = 22
    anim = _icon_anim.get(kind, 0.0)  # 0 = idle, 1 = fully hovered

    if anim > 0.02:
        glow = pygame.Surface((radius * 3, radius * 3), pygame.SRCALPHA)
        pygame.draw.circle(
            glow, (*BLUE_GLOW, round(42 * anim)), glow.get_rect().center,
            round(radius * (1.15 + 0.08 * anim)),
        )
        surf.blit(glow, (ix - glow.get_width() // 2, iy - glow.get_height() // 2))

    _draw_medallion(surf, (ix, iy), radius, seed=sum(map(ord, kind)))

    if kind == "play":
        # Animated dungeon torch retained as the adventure/start symbol.
        flicker = math.sin(t * 14) * (1 + anim * 4)
        sway = math.sin(t * 9) * anim * 3
        pygame.draw.rect(surf, (112, 72, 37),
                         (ix - 3, iy - 1, 6, 17), border_radius=2)
        pygame.draw.rect(surf, (61, 39, 24),
                         (ix - 3, iy - 1, 6, 17), 1, border_radius=2)
        pygame.draw.line(surf, (198, 137, 61),
                         (ix - 7, iy + 1), (ix + 7, iy + 1), 3)
        flame_outer = [
            (ix + sway, iy - 20 - flicker),
            (ix - 8, iy - 5),
            (ix - 3, iy - 1),
            (ix + sway * 0.5, iy - 7),
            (ix + 4, iy - 1),
            (ix + 8, iy - 5),
        ]
        pygame.draw.polygon(surf, (235, 105, 38), flame_outer)
        flame_inner = [
            (ix + sway * 0.6, iy - 15 - flicker * 0.6),
            (ix - 4, iy - 4),
            (ix, iy - 8),
            (ix + 4, iy - 4),
        ]
        pygame.draw.polygon(surf, YELLOW_GLOW, flame_inner)
        pygame.draw.circle(surf, (255, 241, 178), (ix, iy - 6), 2)

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
        draw_gear(surf, (ix, iy), radius, spin_degrees=t * speed * 60)

    elif kind == "quit":
        doorway = pygame.Rect(ix - 11, iy - 15, 22, 30)
        pygame.draw.rect(surf, (13, 12, 15), doorway, border_radius=2)
        pygame.draw.rect(surf, (151, 100, 46), doorway, 3, border_radius=2)
        door_w = max(5, round(19 * (1 - 0.45 * anim)))
        door = pygame.Rect(ix - 9, iy - 12, door_w, 25)
        pygame.draw.rect(surf, (72, 45, 31), door)
        pygame.draw.rect(surf, (120, 76, 40), door, 2)
        pygame.draw.line(surf, (190, 139, 66), (door.left + 3, door.top + 3),
                         (door.right - 3, door.top + 3), 1)
        if door_w > 9:
            pygame.draw.circle(surf, YELLOW_GLOW, (door.right - 4, door.centery), 2)
        # Small outward arrow clarifies that this doorway exits the game.
        arrow_x = ix + 8 + round(3 * anim)
        pygame.draw.line(surf, BLUE_GLOW, (ix, iy), (arrow_x, iy), 2)
        pygame.draw.polygon(surf, BLUE_GLOW,
                            [(arrow_x, iy - 4), (arrow_x + 5, iy), (arrow_x, iy + 4)])
            
    elif kind == "book":
        # Open book — pages spread wider on hover, text lines fade in once mostly open
        spread = 6 + int(4 * anim)
        left_page = pygame.Rect(ix - spread - 10, iy - 10, spread + 10, 20)
        right_page = pygame.Rect(ix, iy - 10, spread + 10, 20)

        pygame.draw.rect(surf, (218, 198, 151), left_page,
                          border_top_left_radius=2, border_bottom_left_radius=2)
        pygame.draw.rect(surf, (230, 211, 165), right_page,
                          border_top_right_radius=2, border_bottom_right_radius=2)
        pygame.draw.rect(surf, (140, 115, 80), left_page, 1,
                          border_top_left_radius=2, border_bottom_left_radius=2)
        pygame.draw.rect(surf, (140, 115, 80), right_page, 1,
                          border_top_right_radius=2, border_bottom_right_radius=2)

        pygame.draw.line(surf, (90, 60, 40), (ix, iy - 11), (ix, iy + 11), 2)

        if anim > 0.3:
            fade = min(1.0, (anim - 0.3) / 0.7)
            for i in range(3):
                y = iy - 5 + i * 5
                lw = int((spread + 4) * fade)
                pygame.draw.line(surf, (150, 125, 90), (ix - 4 - lw, y), (ix - 4, y), 1)
                pygame.draw.line(surf, (150, 125, 90), (ix + 4, y), (ix + 4 + lw, y), 1)

        pygame.draw.circle(surf, YELLOW_GLOW, (ix, iy - 12), 2)  # gold bookmark clasp

        # Blue Python-like rune gives the manual a CodeBreak-specific mark.
        pygame.draw.line(surf, BLUE_GLOW, (ix + 5, iy - 5), (ix + 10, iy - 5), 1)
        pygame.draw.line(surf, BLUE_GLOW, (ix + 5, iy - 5), (ix + 5, iy), 1)
        pygame.draw.circle(surf, BLUE_GLOW, (ix + 9, iy), 1)

def _draw_stone_button(
    surf: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    icon: str,
    hovered: bool,
    seed: int,
    t: float = 0.0,
) -> None:
    preview_rect = rect.inflate(4, 4) if hovered else rect
    text_width = _button_font.size(label)[0]
    centered_left = preview_rect.centerx - text_width // 2
    # Keep the label truly centered whenever there is room. Only narrow
    # buttons receive the minimum shift needed to clear the medallion.
    minimum_text_left = preview_rect.left + 68
    text_offset = max(0, minimum_text_left - centered_left)
    r = draw_button(
        surf, rect, label, _button_font, hovered=hovered,
        text_offset=text_offset,
    )
    _draw_menu_icon(surf, icon, pygame.Rect(r.left, r.top, r.w, r.h), hovered, t)


_mang_idle_cache = None


def _load_mang_tahimik_idle():
    """Load authored idle frames when present, otherwise the existing portrait."""
    global _mang_idle_cache
    if _mang_idle_cache is not None:
        return _mang_idle_cache

    idle_root = Path("assets/images/characters/mang_tahimik/idle")
    paths = sorted(
        idle_root.rglob("frame_*.png"),
        key=lambda path: int(path.stem.rsplit("_", 1)[1]),
    ) if idle_root.exists() else []
    if not paths:
        paths = [Path("assets/images/characters/mang_tahimik/portrait.png")]

    originals = [pygame.image.load(str(path)).convert_alpha() for path in paths]
    target_height = max(96, min(136, round(SCREEN_HEIGHT * 0.145)))
    scale = target_height / max(frame.get_height() for frame in originals)
    scaled = [
        pygame.transform.scale(
            frame,
            (max(1, round(frame.get_width() * scale)),
             max(1, round(frame.get_height() * scale))),
        )
        for frame in originals
    ]
    canvas_size = (max(frame.get_width() for frame in scaled), target_height)
    _mang_idle_cache = []
    for frame in scaled:
        canvas = pygame.Surface(canvas_size, pygame.SRCALPHA)
        canvas.blit(frame, frame.get_rect(midbottom=canvas.get_rect().midbottom))
        _mang_idle_cache.append(canvas)
    return _mang_idle_cache


def _draw_mang_tahimik_tip(surf: pygame.Surface, t: float) -> None:
    frames = _load_mang_tahimik_idle()
    frame = frames[int(t / 0.14) % len(frames)]
    ground_y = SCREEN_HEIGHT - 98
    center_x = SCREEN_WIDTH - 92
    idle_bob = round(math.sin(t * 2.4) * 2)
    character_rect = frame.get_rect(midbottom=(center_x, ground_y + idle_bob))

    # A soft floor shadow keeps the transparent pixel art visually grounded.
    shadow = pygame.Surface((frame.get_width(), 18), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 105), shadow.get_rect().inflate(-16, -8))
    surf.blit(shadow, (character_rect.centerx - shadow.get_width() // 2,
                       ground_y - shadow.get_height() // 2 + 4))
    surf.blit(frame, character_rect)

    # Preserve the existing tip-box footprint, anchored just left of Mang.
    character_left_edge = character_rect.left
    tip_gap = 20
    tip_lines = ["Think before you type...", "The dungeon punishes mistakes."]
    minimum_tip_width = max(_tip_font.size(line)[0] for line in tip_lines) + 24
    # The fixed menu column ends at 60% of the screen width. On smaller
    # windows, narrow the tip rather than allowing it beneath a button.
    menu_right = round(SCREEN_WIDTH * 0.60)
    available_width = character_left_edge - tip_gap - (menu_right + 18)
    tip_w = max(minimum_tip_width, min(300, available_width))
    tip_h = 88
    tip_r = pygame.Rect(character_left_edge - tip_gap - tip_w,
                        ground_y - tip_h + 18, tip_w, tip_h)

    draw_panel(surf, tip_r, radius=7, alpha=246)

    # Small bronze pins and a magical-blue gem echo the menu medallions.
    for corner in (
        (tip_r.left + 8, tip_r.top + 8),
        (tip_r.right - 8, tip_r.top + 8),
        (tip_r.left + 8, tip_r.bottom - 8),
        (tip_r.right - 8, tip_r.bottom - 8),
    ):
        pygame.draw.circle(surf, UI_COLORS["bronze"], corner, 2)

    gem_x = tip_r.centerx
    pygame.draw.polygon(surf, UI_COLORS["bronze_dark"], [
        (gem_x, tip_r.top - 3), (gem_x + 8, tip_r.top + 4),
        (gem_x, tip_r.top + 11), (gem_x - 8, tip_r.top + 4),
    ])
    pygame.draw.circle(surf, UI_COLORS["blue_bright"],
                       (gem_x, tip_r.top + 4), 3)

    heading = _tip_font.render(
        "MANG TAHIMIK'S WISDOM", True, UI_COLORS["gold"]
    )
    surf.blit(heading, (tip_r.left + 14, tip_r.top + 10))
    divider_y = tip_r.top + 34
    pygame.draw.line(surf, UI_COLORS["bronze_dark"],
                     (tip_r.left + 12, divider_y),
                     (tip_r.right - 12, divider_y), 1)
    for i, line in enumerate(tip_lines):
        color = UI_COLORS["parchment"] if i == 0 else UI_COLORS["text_dim"]
        surf.blit(_tip_font.render(line, True, color),
                  (tip_r.left + 14, tip_r.top + 42 + i * 20))


def main_menu():
    from src.screens.tutorial import tutorial_screen

    show_settings = False
    settings_panel = SettingsPanel(screen)
    settings_panel.close()

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

    rects, bw, bh, gap, center_x, by0 = compute_menu_layout(SCREEN_WIDTH, SCREEN_HEIGHT, 4)

    icons, labels, seeds = MM_ICONS, MM_LABELS, MM_SEEDS

    # Clean backdrop (background + logo, no buttons) — captured once here,
    # after the logo is loaded/positioned, reused every frame instead of
    # re-copying the screen 60x/sec.
    screen.blit(background, (0, 0))
    screen.blit(logo, (SCREEN_WIDTH // 2 - logo.get_width() // 2, logo_top_offset))
    menu_backdrop = screen.copy()

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
                        from src.ui.transitions import crumble_transition
                        from src.screens.start_game_menu import start_game_menu, render_start_menu_buttons

                        old_source = screen.copy()  # current frame, main menu buttons already on it

                        new_rects, *_ = compute_menu_layout(SCREEN_WIDTH, SCREEN_HEIGHT, 3)
                        new_source = menu_backdrop.copy()
                        render_start_menu_buttons(new_source, new_rects, t)

                        crumble_transition(screen, menu_backdrop, old_source, rects,
                                            new_source, new_rects, seed=99,
                                            burst_duration=0.52, assemble_duration=0.56)
                        start_game_menu(screen, clean_backdrop=menu_backdrop)
                    if rects[1].collidepoint(event.pos):                      
                        how_to_play_screen(screen)
                    if rects[2].collidepoint(event.pos):
                        show_settings = True
                        settings_panel.open()
                        # Do not pass the opening click into the panel. At
                        # some resolutions it overlaps the panel's Back button.
                        continue
                    if rects[3].collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()
            if show_settings:
                settings_panel.handle_event(event)
                show_settings = settings_panel.is_open

        screen.blit(menu_backdrop, (0, 0))
    

        for rect, label, icon, h, seed in zip(rects, labels, icons, hovers, seeds):
            _draw_stone_button(screen, rect, label, icon, h, seed, t)

        _draw_mang_tahimik_tip(screen, t)
        ver = _small.render("v1.0", True, WHITE)
        screen.blit(ver, (16, SCREEN_HEIGHT - ver.get_height() - 12))

        if show_settings:
            settings_panel.draw()

        pygame.display.flip()
