"""
game_over.py

The "GAME OVER" screen shown after the player dies / fails a
challenge for good. Same stone-and-blood visual language as the rest
of CodeBreak's UI (main_menu's stone buttons, game.py's blurred pause
menu), just re-themed in red for a defeat state.

--------------------------------------------------------------------
Typical usage from src/screens/game.py
--------------------------------------------------------------------

    from src.screens.game_over import game_over_screen

    ...inside the game loop, once the player has died...
    snapshot = screen.copy()
    outcome = game_over_screen(screen, background=snapshot)

    if outcome == "retry":
        ...reset player / challenge state and keep looping...
    elif outcome == "review":
        ...reopen CodeEditor on the challenge that was failed...
    elif outcome == "main_menu":
        pygame.mixer.music.stop()
        return   # bail out of game_screen() back to main_menu()

--------------------------------------------------------------------
Preview without wiring it into the full game
--------------------------------------------------------------------

    python -m src.screens.game_over

(runs the __main__ block at the bottom, which opens a small window
and drops you straight into the game-over screen)
"""

import math
import random

import pygame


# ======================================================================
# Palette
# ======================================================================

BLOOD_RED    = (200, 40, 40)
BLOOD_BRIGHT = (255, 100, 100)
TEXT_WHITE   = (225, 225, 230)
TEXT_GREY    = (185, 188, 196)
BLUE_GLOW    = (80, 180, 255)   # matches the hover-glow used elsewhere in the UI

STONE_BASE   = (26, 27, 34)
STONE_DARK   = (14, 14, 18)
STONE_LIGHT  = (40, 41, 50)
PANEL_INNER  = (18, 18, 24)
RIVET_COLOR  = (150, 150, 160)


# ======================================================================
# Title: chunky "written out" GAME OVER text
# ======================================================================

def _build_pixel_title(text, target_height, color):
    """
    Renders `text` in a chunky pixel-art style.

    If a real pixel font is dropped at assets/fonts/PressStart2P-Regular.ttf
    (or any other path you swap in below), it's used directly at full
    size. Otherwise this fakes the blocky look by rendering small with
    a bold monospace font and upscaling with nearest-neighbor scaling
    (pygame.transform.scale, NOT smoothscale) — that's what gives the
    hard pixel edges even without a dedicated font file.
    """
    pixel_font_path = "assets/fonts/PressStart2P-Regular.ttf"

    try:
        size = int(target_height)
        font = pygame.font.Font(pixel_font_path, size)
        base_surf = font.render(text, True, color)
        scale = 1
    except Exception:
        base_size = max(10, int(target_height / 5))
        font = pygame.font.SysFont("consolas", base_size, bold=True)
        base_surf = font.render(text, True, color)
        scale = 5

    if scale != 1:
        big_surf = pygame.transform.scale(
            base_surf,
            (base_surf.get_width() * scale, base_surf.get_height() * scale)
        )
    else:
        big_surf = base_surf

    return big_surf, font, scale


def _build_title_surfaces(text, target_height):
    """
    Builds the crisp red title plus a soft red glow layer behind it,
    cached once so the (relatively expensive) font render/scale work
    doesn't happen every frame of the typewriter animation.
    """
    crisp, font, scale = _build_pixel_title(text, target_height, (235, 40, 40))
    glow_base, _, _ = _build_pixel_title(text, target_height, BLOOD_BRIGHT)

    pad = 12
    glow = pygame.Surface(
        (crisp.get_width() + pad * 2, crisp.get_height() + pad * 2),
        pygame.SRCALPHA
    )
    glow_base.set_alpha(55)
    for ox, oy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, 3), (-3, 3), (3, -3)):
        glow.blit(glow_base, (pad + ox, pad + oy))

    return {"crisp": crisp, "glow": glow, "font": font, "scale": scale, "pad": pad}


def _draw_title(screen, assets, text, now_ms, letter_ms, screen_w, screen_h):
    """
    Draws the title, revealing one character at a time (a typewriter
    effect) until the whole thing is on screen, with a blinking block
    cursor while it's still "typing".
    """
    crisp, glow = assets["crisp"], assets["glow"]
    font, scale, pad = assets["font"], assets["scale"], assets["pad"]

    revealed_chars = min(len(text), now_ms // letter_ms + 1)
    shown = text[:revealed_chars]

    crop_w = min(crisp.get_width(), font.size(shown)[0] * scale)
    if crop_w <= 0:
        return

    x = screen_w // 2 - crisp.get_width() // 2
    y = int(screen_h * 0.20)

    glow_crop_w = min(glow.get_width(), crop_w + pad * 2)
    screen.blit(glow, (x - pad, y - pad), pygame.Rect(0, 0, glow_crop_w, glow.get_height()))
    screen.blit(crisp, (x, y), pygame.Rect(0, 0, crop_w, crisp.get_height()))

    if revealed_chars < len(text) and (now_ms // 250) % 2 == 0:
        cursor_h = crisp.get_height()
        cursor_w = max(6, cursor_h // 6)
        pygame.draw.rect(screen, BLOOD_BRIGHT, (x + crop_w + 6, y, cursor_w, cursor_h))


def _draw_divider(surface, screen_w, y):
    """The thin line-skull-line divider under the title."""
    line_color = (90, 20, 20)
    gap = 22
    center_x = screen_w // 2
    half_len = min(260, screen_w // 4)

    pygame.draw.line(surface, line_color, (center_x - half_len, y), (center_x - gap, y), 2)
    pygame.draw.line(surface, line_color, (center_x + gap, y), (center_x + half_len, y), 2)
    _draw_skull_icon(surface, center_x, y, 15, (170, 30, 30))


# ======================================================================
# Backdrop: blur + red corner vignette
# ======================================================================

def _make_blurred_backdrop(source, width, height):
    """
    Same cheap downscale/upscale blur trick already used for the
    in-game pause menu (see game.py's draw_pause_menu), plus a dark
    red tint so the gameplay behind the panel reads as "you died"
    instead of a plain pause.
    """
    down_w = max(1, width // 10)
    down_h = max(1, height // 10)
    small = pygame.transform.smoothscale(source, (down_w, down_h))
    blurred = pygame.transform.smoothscale(small, (width, height))

    tint = pygame.Surface((width, height), pygame.SRCALPHA)
    tint.fill((35, 0, 0, 150))
    blurred.blit(tint, (0, 0))
    return blurred


def _build_blood_vignette(width, height):
    """
    Builds a translucent red glow that's strongest at the corners and
    fades out toward the center of the screen, matching the reference
    art. Built once at low resolution and smoothscaled up since a
    true per-pixel gradient at full screen size would be far too slow
    to redo every frame — this only needs to happen once per screen.
    """
    sw, sh = 160, 90
    small = pygame.Surface((sw, sh), pygame.SRCALPHA)
    cx, cy = sw / 2, sh / 2
    max_dist = math.hypot(cx, cy)

    for y in range(sh):
        for x in range(sw):
            dist = math.hypot(x - cx, y - cy)
            t = max(0.0, (dist / max_dist - 0.35) / 0.65)
            alpha = int(min(230, (t ** 2) * 230))
            if alpha:
                small.set_at((x, y), (60, 0, 0, alpha))

    return pygame.transform.smoothscale(small, (width, height))


# ======================================================================
# Small reusable pieces: stone fill + procedural icons
# ======================================================================

def _stone_fill(surf, rect, seed):
    rng = random.Random(seed)
    surf.fill(STONE_BASE, rect)
    for _ in range(80):
        x = rect.left + rng.randint(0, max(1, rect.width - 1))
        y = rect.top + rng.randint(0, max(1, rect.height - 1))
        shade = rng.choice([STONE_DARK, STONE_LIGHT, (24, 17, 18)])
        pygame.draw.rect(surf, shade, (x, y, rng.randint(3, 7), rng.randint(2, 4)))


def _draw_skull_icon(surface, cx, cy, size, color):
    s = size
    dome = pygame.Rect(cx - s, cy - s, s * 2, int(s * 1.5))
    pygame.draw.ellipse(surface, color, dome)

    jaw = pygame.Rect(cx - int(s * 0.55), cy + int(s * 0.2), int(s * 1.1), int(s * 0.55))
    pygame.draw.rect(surface, color, jaw, border_radius=2)

    bg = (12, 12, 16)
    eye = max(2, s // 3)
    pygame.draw.rect(surface, bg, (cx - eye - 2, cy - eye // 2, eye, eye))
    pygame.draw.rect(surface, bg, (cx + 2, cy - eye // 2, eye, eye))
    pygame.draw.polygon(surface, bg, [(cx, cy + 1), (cx - 2, cy + 5), (cx + 2, cy + 5)])

    tooth_w = max(1, s // 6)
    tooth_y0 = cy + int(s * 0.45)
    tooth_y1 = cy + int(s * 0.7)
    for i in range(3):
        tx = cx - int(s * 0.4) + i * int(s * 0.4)
        pygame.draw.line(surface, bg, (tx, tooth_y0), (tx, tooth_y1), tooth_w)


def _draw_home_icon(surface, cx, cy, size, color):
    s = size
    roof = [(cx - s, cy - int(s * 0.05)), (cx, cy - s), (cx + s, cy - int(s * 0.05))]
    pygame.draw.polygon(surface, color, roof)

    body = pygame.Rect(cx - int(s * 0.7), cy - int(s * 0.05), int(s * 1.4), int(s * 1.05))
    pygame.draw.rect(surface, color, body)

    door = pygame.Rect(cx - int(s * 0.22), cy + int(s * 0.25), int(s * 0.44), int(s * 0.75))
    pygame.draw.rect(surface, (12, 12, 16), door)


def _draw_code_icon(surface, cx, cy, font, color):
    txt = font.render("</>", True, color)
    surface.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))


# ======================================================================
# Buttons
# ======================================================================

def _draw_menu_button(screen, button, label_font, icon_font, hovered, progress):
    """
    Draws one stone button, faded/slid in according to `progress`
    (0 = invisible, 1 = fully settled).
    """
    rect = button["rect"]
    offset_y = int((1 - progress) * 18)
    draw_pos = (rect.left, rect.top + offset_y)

    panel = pygame.Surface(rect.size)
    _stone_fill(panel, panel.get_rect(), seed=button["seed"])

    inner = panel.get_rect().inflate(-6, -6)
    pygame.draw.rect(panel, PANEL_INNER, inner)

    accent = button["accent"]
    border_color = BLOOD_RED if accent else (95, 98, 112)
    pygame.draw.rect(panel, border_color, panel.get_rect(), 3 if accent else 2)

    for cx, cy in (
        (6, 6), (rect.width - 6, 6),
        (6, rect.height - 6), (rect.width - 6, rect.height - 6),
    ):
        pygame.draw.circle(panel, RIVET_COLOR, (cx, cy), 2)

    if hovered:
        glow = pygame.Surface(rect.size, pygame.SRCALPHA)
        glow.fill((*BLUE_GLOW, 45))
        panel.blit(glow, (0, 0))

    icon_cx, icon_cy = 42, rect.height // 2
    icon_color = BLOOD_RED if accent else TEXT_GREY
    if button["icon"] == "skull":
        _draw_skull_icon(panel, icon_cx, icon_cy, 13, icon_color)
    elif button["icon"] == "code":
        _draw_code_icon(panel, icon_cx, icon_cy, icon_font, icon_color)
    elif button["icon"] == "home":
        _draw_home_icon(panel, icon_cx, icon_cy, 12, icon_color)

    label_color = BLOOD_RED if accent else TEXT_WHITE
    label = label_font.render(button["label"], True, label_color)
    panel.blit(label, (rect.width // 2 - label.get_width() // 2,
                        rect.height // 2 - label.get_height() // 2))

    panel.set_alpha(int(255 * progress))
    screen.blit(panel, draw_pos)


# ======================================================================
# Main entry point
# ======================================================================

def game_over_screen(screen, background=None, failed_snippet=None):
    """
    Runs the modal Game Over screen until the player picks a button.

    Parameters
    ----------
    screen : pygame.Surface
        The main display surface — drawn onto every frame.
    background : pygame.Surface, optional
        A snapshot of the gameplay frame taken right when the player
        died. This is what gets blurred behind the panel. If omitted,
        whatever's currently on `screen` is captured instead.
    failed_snippet : str, optional
        The code that caused the loss. Not rendered yet — it's just
        threaded through so whoever wires up "REVIEW" has it handy
        (e.g. to reopen CodeEditor pre-filled with this code).

    Returns
    -------
    str
        "retry", "review", or "main_menu".
    """
    SCREEN_W, SCREEN_H = screen.get_size()
    clock = pygame.time.Clock()

    if background is None:
        background = screen.copy()

    # ---- one-time setup (safe to do every call — game-over doesn't
    #      need to happen 60 times a second) ------------------------
    blurred_bg = _make_blurred_backdrop(background, SCREEN_W, SCREEN_H)
    vignette = _build_blood_vignette(SCREEN_W, SCREEN_H)
    title_assets = _build_title_surfaces("GAME OVER", int(SCREEN_H * 0.11))

    label_font = pygame.font.SysFont("consolas", max(14, int(SCREEN_H * 0.026)), bold=True)
    icon_font = pygame.font.SysFont("consolas", max(16, int(SCREEN_H * 0.03)), bold=True)

    title_text = "GAME OVER"
    LETTER_MS = 90                              # ms per letter of the typewriter reveal
    TITLE_DONE_MS = len(title_text) * LETTER_MS
    BUTTON_STAGGER_MS = 220                      # delay between each button starting to appear
    BUTTON_FADE_MS = 260                         # how long each button takes to fully fade in

    btn_w = min(560, int(SCREEN_W * 0.30))
    btn_h = max(50, int(SCREEN_H * 0.075))
    btn_gap = max(12, int(SCREEN_H * 0.018))
    btn_x = SCREEN_W // 2 - btn_w // 2
    first_btn_y = int(SCREEN_H * 0.56)

    buttons = [
        {"key": "retry", "label": "RETRY", "icon": "skull",
         "accent": True, "seed": 101,
         "rect": pygame.Rect(btn_x, first_btn_y, btn_w, btn_h)},
        {"key": "review", "label": "REVIEW", "icon": "code",
         "accent": False, "seed": 202,
         "rect": pygame.Rect(btn_x, first_btn_y + (btn_h + btn_gap), btn_w, btn_h)},
        {"key": "main_menu", "label": "RETURN TO MAIN MENU", "icon": "home",
         "accent": False, "seed": 303,
         "rect": pygame.Rect(btn_x, first_btn_y + (btn_h + btn_gap) * 2, btn_w, btn_h)},
    ]

    all_shown_ms = TITLE_DONE_MS + (len(buttons) - 1) * BUTTON_STAGGER_MS + BUTTON_FADE_MS

    start_ticks = pygame.time.get_ticks()
    result = None
    running = True

    while running:
        clock.tick(60)
        now = pygame.time.get_ticks() - start_ticks
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            # F8 is the dev/debug toggle used to preview this screen from
            # game.py (press F8 to open, F8 again to close) — it works even
            # mid-animation so you're not stuck waiting to back out of it.
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F8:
                result = "debug_close"
                running = False
                break

            # Ignore input until everything has finished animating in,
            # so you can't accidentally click through a half-faded button.
            if now < all_shown_ms:
                continue

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    result = "retry"
                    running = False
                elif event.key == pygame.K_r:
                    result = "review"
                    running = False
                elif event.key == pygame.K_m:
                    result = "main_menu"
                    running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for b in buttons:
                    if b["rect"].collidepoint(event.pos):
                        result = b["key"]
                        running = False

        # ---- draw -----------------------------------------------------
        screen.blit(blurred_bg, (0, 0))
        screen.blit(vignette, (0, 0))

        _draw_title(screen, title_assets, title_text, now, LETTER_MS, SCREEN_W, SCREEN_H)

        if now >= TITLE_DONE_MS:
            _draw_divider(screen, SCREEN_W, int(SCREEN_H * 0.46))

            for i, b in enumerate(buttons):
                reveal_at = TITLE_DONE_MS + i * BUTTON_STAGGER_MS
                progress = max(0.0, min(1.0, (now - reveal_at) / BUTTON_FADE_MS))
                if progress > 0:
                    hovered = progress >= 1.0 and b["rect"].collidepoint(mouse_pos)
                    _draw_menu_button(screen, b, label_font, icon_font, hovered, progress)

        pygame.display.flip()

    return result


# ======================================================================
# Standalone preview — run this file directly to see the screen without
# wiring it into the rest of the game.
# ======================================================================

if __name__ == "__main__":
    pygame.init()
    demo_screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Game Over — preview")

    # Fake a "gameplay" frame so there's something to blur behind the panel.
    fake_bg = pygame.Surface((1280, 720))
    fake_bg.fill((35, 55, 38))
    _rng = random.Random(1)
    for _ in range(400):
        gx, gy = _rng.randint(0, 1280), _rng.randint(0, 720)
        shade = _rng.randint(20, 90)
        pygame.draw.rect(fake_bg, (shade, shade + 10, shade), (gx, gy, 20, 20))

    outcome = game_over_screen(demo_screen, background=fake_bg)
    print("Player chose:", outcome)
    pygame.quit()
