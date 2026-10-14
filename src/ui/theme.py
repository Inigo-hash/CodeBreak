"""Shared visual language for CodeBreak menus and compact gameplay UI."""

import math
from functools import lru_cache

import pygame
from src.ui.text_layout import fit_text

from src.settings_state import font_scale


UI_COLORS = {
    "stone_deep": (12, 13, 18),
    "stone": (29, 31, 40),
    "stone_light": (45, 48, 59),
    "bronze_dark": (91, 62, 34),
    "bronze": (171, 119, 55),
    "gold": (218, 177, 86),
    "blue": (72, 166, 224),
    # 80,180,255 rather than the brighter 120,205,255 this used to hold:
    # the menu, How To Play and Game Over were all already drawing this
    # value by hand, so hover now looks the same on every screen.
    "blue_bright": (80, 180, 255),
    "crimson": (190, 42, 52),
    "parchment": (226, 207, 164),
    "text": (240, 237, 224),
    # One grey for secondary text everywhere. Seven had accumulated across
    # the screens, none of them chosen; this is the lightest of the
    # cluster, which holds up best on small labels over dark panels.
    "text_dim": (170, 175, 190),
    # Buttons pull their fill from these rather than from "stone". The menu
    # art is entirely warm gold and cool blue, so a near-neutral grey button
    # reads as unstyled placeholder UI sitting on top of finished artwork.
    # A deep navy belongs to the same world the background does.
    "button_fill": (20, 26, 42),
    "button_fill_hover": (34, 45, 69),
    "gold_deep": (171, 132, 38),
    "gold_bright": (226, 186, 96),
    "gold_text_dark": (26, 19, 6),

    # Modal window palette. The dark carved panel above belongs to the HUD,
    # which sits on top of the world and must not compete with it; these
    # lighter values belong to the full-screen windows the game pauses for.
    # They are not new - How To Play, Topic Found, Topic Lesson and the
    # inventory each defined the same numbers privately under four
    # different names. Naming them here is what makes them one system.
    # See docs/style-guide.md.
    "modal_panel": (36, 38, 48),
    "modal_inner": (26, 28, 36),
    "modal_frame": (90, 94, 110),
    "modal_frame_hover": (140, 146, 165),
    "modal_accent": (255, 220, 120),
    "modal_heading": (80, 180, 255),
    "modal_button": (42, 46, 58),
    "modal_button_hover": (60, 90, 130),
    "modal_button_edge": (62, 68, 82),
    "modal_text": (255, 255, 255),
    "modal_text_soft": (215, 215, 220),
    "modal_text_dim": (170, 175, 190),
    "modal_success": (120, 200, 140),
    "modal_danger": (220, 110, 110),
    # The empty inventory slot: darker than the window it sits in, so a slot
    # reads as a hole in the panel rather than a tile on top of it.
    "modal_slot": (20, 22, 28),
    "action_success": (28, 104, 70),
    "action_danger": (153, 39, 49),
    "action_disabled": (40, 43, 52),
}

# Button emphasis tiers. A menu where every row looks identical gives the eye
# nothing to land on, so the primary action is filled and the exit recedes.
TIER_PRIMARY = "primary"
TIER_SECONDARY = "secondary"
TIER_TERTIARY = "tertiary"
TIER_SUCCESS = "success"
TIER_DANGER = "danger"


def readable_button_text(fill):
    """Choose light or dark text with the stronger luminance contrast."""
    def luminance(color):
        channels = [value / 255 for value in color[:3]]
        linear = [value / 12.92 if value <= .04045
                  else ((value + .055) / 1.055) ** 2.4 for value in channels]
        return sum(value * weight for value, weight in zip(linear, (.2126, .7152, .0722)))

    def contrast(text):
        a, b = sorted((luminance(fill), luminance(text)))
        return (b + .05) / (a + .05)

    return max((UI_COLORS["text"], (12, 24, 18)), key=contrast)

# Every font in the game comes from here. Two families only: Exo 2 for
# headings, buttons and menu chrome (it echoes the blocky sans of the
# CodeBreak logo), JetBrains Mono for body copy and anything code-shaped.
# Both are bundled under assets/fonts/ so the game looks identical on a
# machine that has neither installed.
DISPLAY_REGULAR = "assets/fonts/Exo2-Regular.ttf"
DISPLAY_SEMIBOLD = "assets/fonts/Exo2-SemiBold.ttf"
DISPLAY_BOLD = "assets/fonts/Exo2-Bold.ttf"
# The "NL" (no-ligature) cut of JetBrains Mono on purpose: the ligature cut
# draws `==` and `!=` as single arrow-like glyphs, which is the last thing a
# player learning Python operators should be reading off the screen.
MONO_REGULAR = "assets/fonts/JetBrainsMonoNL-Regular.ttf"
MONO_BOLD = "assets/fonts/JetBrainsMonoNL-Bold.ttf"

# The sizes passed in by callers were tuned against Cinzel and Consolas, and
# these two families render taller at the same nominal size. Scaling the
# request keeps the rendered pixel height where it was, so the panel and
# button math scattered across the screens still lines up.
_DISPLAY_RATIO = 1.11  # Exo 2 vs the Cinzel sizes the menus were built around
_MONO_RATIO = 0.74     # JetBrains Mono vs Consolas


def _load(path, size):
    """Load a bundled face, falling back to pygame's built-in sans.

    The fallback is deliberately the same everywhere: if an asset goes
    missing the whole game degrades to one font rather than to a different
    one per screen.
    """
    try:
        return pygame.font.Font(path, size)
    except (FileNotFoundError, pygame.error):
        return pygame.font.Font(None, size)


@lru_cache(maxsize=128)
def _title_font(size, bold=True):
    path = DISPLAY_BOLD if bold else DISPLAY_SEMIBOLD
    return _load(path, max(8, int(size * _DISPLAY_RATIO)))


def title_font(size, bold=True):
    """Display face for titles, headings and button labels."""
    return _title_font(max(8, round(size * font_scale())), bold)


@lru_cache(maxsize=128)
def _ui_font(size, bold=False):
    path = DISPLAY_SEMIBOLD if bold else DISPLAY_REGULAR
    return _load(path, max(8, int(size * _DISPLAY_RATIO)))


def ui_font(size, bold=False):
    """Display face at text weights, for menu chrome that is not a heading."""
    return _ui_font(max(8, round(size * font_scale())), bold)


@lru_cache(maxsize=128)
def _body_font(size, bold=False):
    path = MONO_BOLD if bold else MONO_REGULAR
    return _load(path, max(8, int(size * _MONO_RATIO)))


def body_font(size, bold=False):
    """Monospace face for body copy, stats, and code."""
    return _body_font(max(8, round(size * font_scale())), bold)


def clear_font_cache():
    """Discard loaded faces after the accessibility scale changes."""

    _title_font.cache_clear()
    _ui_font.cache_clear()
    _body_font.cache_clear()


def draw_panel(surface, rect, emphasized=False, radius=8, alpha=238):
    """Draw the standard inset stone panel with a bronze/blue focus rim."""
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    local = panel.get_rect()
    shadow = local.move(0, 4)
    pygame.draw.rect(panel, (5, 6, 9, 150), shadow, border_radius=radius)
    pygame.draw.rect(panel, (*UI_COLORS["stone_deep"], alpha), local, border_radius=radius)
    pygame.draw.rect(panel, (*UI_COLORS["stone"], alpha), local.inflate(-8, -8),
                     border_radius=max(2, radius - 2))
    pygame.draw.rect(panel, UI_COLORS["blue"] if emphasized else UI_COLORS["bronze"],
                     local, 2, border_radius=radius)
    pygame.draw.line(panel, UI_COLORS["stone_light"], (radius, 5),
                     (local.right - radius, 5), 1)
    pygame.draw.line(panel, UI_COLORS["bronze_dark"], (radius, local.bottom - 5),
                     (local.right - radius, local.bottom - 5), 1)
    surface.blit(panel, rect.topleft)
    if rect.width >= 580 and rect.height >= 300:
        draw_codex_frame(surface, rect)


@lru_cache(maxsize=16)
def _codex_art(size):
    try:
        image = pygame.image.load('assets/images/ui/codex_frame.png').convert_alpha()
        image = image.subsurface(image.get_bounding_rect(min_alpha=8)).copy()
        return pygame.transform.smoothscale(image, size)
    except (OSError, pygame.error):
        return None


def draw_codex_frame(surface, rect):
    """Illustrated slate, bronze and ivy frame shared by large information UI."""
    art = _codex_art(tuple(rect.size))
    if art is not None:
        surface.blit(art, rect)


def _rounded_vgradient(surface, rect, top_color, bottom_color, radius):
    """Fill a rounded rect with a vertical gradient.

    pygame has no gradient primitive and no cheap way to mask one into a
    rounded shape, so each row is drawn as a single line inset by however
    much the corner arc eats into it at that height. Exact corners, no
    per-frame surface allocation.
    """
    height = max(1, rect.height)
    for y in range(height):
        blend = y / (height - 1) if height > 1 else 0.0
        color = tuple(
            round(top_color[i] + (bottom_color[i] - top_color[i]) * blend)
            for i in range(3)
        )
        # Distance into the corner arc, if this row is inside one.
        dy = 0
        if y < radius:
            dy = radius - y
        elif y >= height - radius:
            dy = y - (height - radius - 1)
        inset = radius - round(math.sqrt(max(0, radius * radius - dy * dy))) if dy else 0
        pygame.draw.line(
            surface, color,
            (rect.left + inset, rect.top + y),
            (rect.right - 1 - inset, rect.top + y),
        )


def draw_button(surface, rect, label, font, hovered=False, text_offset=0,
                tier=TIER_SECONDARY, enabled=True, focused=False):
    """Shared carved stone button used by the Main and Pause menus.

    `tier` controls emphasis only — geometry, hit area and the returned rect
    are unchanged, so callers that do their own layout math stay correct.
    """
    hovered = hovered and enabled
    grow = 4 if hovered else 0
    if tier == TIER_PRIMARY and enabled:
        grow += 3  # the hero action sits slightly proud of the rest
    draw_rect = rect.inflate(grow, grow) if grow else rect

    # Outer glow: always lit on the primary action, hover-only elsewhere.
    if enabled and (tier == TIER_PRIMARY or hovered):
        glow_color = UI_COLORS["gold"] if tier == TIER_PRIMARY else UI_COLORS["blue"]
        glow_alpha = 70 if (tier == TIER_PRIMARY and hovered) else (
            46 if tier == TIER_PRIMARY else 55)
        glow = pygame.Surface((draw_rect.w + 14, draw_rect.h + 14), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*glow_color, glow_alpha), glow.get_rect(),
                         border_radius=10)
        surface.blit(glow, (draw_rect.x - 7, draw_rect.y - 7))

    pygame.draw.rect(surface, (6, 7, 10), draw_rect.move(0, 4), border_radius=7)

    if not enabled:
        pygame.draw.rect(surface, UI_COLORS["action_disabled"], draw_rect, border_radius=7)
        border = UI_COLORS["modal_frame"]
        text_color = UI_COLORS["text_dim"]
        inner_line = border
    elif tier in (TIER_SUCCESS, TIER_DANGER):
        base = UI_COLORS["action_success" if tier == TIER_SUCCESS else "action_danger"]
        fill = tuple(min(255, value + (15 if hovered else 0)) for value in base)
        pygame.draw.rect(surface, fill, draw_rect, border_radius=7)
        border = UI_COLORS["modal_success" if tier == TIER_SUCCESS else "modal_danger"]
        text_color = UI_COLORS["text"]
        inner_line = border
    elif tier == TIER_PRIMARY:
        top = UI_COLORS["gold_bright"] if hovered else UI_COLORS["gold"]
        _rounded_vgradient(surface, draw_rect, top, UI_COLORS["gold_deep"], 7)
        border = UI_COLORS["gold_bright"] if hovered else UI_COLORS["bronze"]
        text_color = UI_COLORS["gold_text_dark"]
        inner_line = UI_COLORS["gold_bright"]
    else:
        fill = (UI_COLORS["button_fill_hover"] if hovered
                else UI_COLORS["button_fill"])
        pygame.draw.rect(surface, fill, draw_rect, border_radius=7)
        if tier == TIER_TERTIARY:
            border = UI_COLORS["blue_bright"] if hovered else UI_COLORS["bronze_dark"]
            text_color = UI_COLORS["text_dim"]
        else:
            border = UI_COLORS["blue_bright"] if hovered else UI_COLORS["bronze"]
            text_color = UI_COLORS["text"]
        inner_line = (69, 76, 96)

    # Thicker rim than the old 1px hairline — it has to hold its own against
    # the beveled logo directly above it.
    pygame.draw.rect(surface, border, draw_rect, 3, border_radius=7)
    inner = draw_rect.inflate(-8, -8)
    pygame.draw.rect(surface, UI_COLORS["bronze_dark"], inner, 1, border_radius=4)
    pygame.draw.line(surface, inner_line,
                     (inner.left + 5, inner.top + 2),
                     (inner.right - 5, inner.top + 2), 1)

    text = fit_text(font, label, text_color,
                    (draw_rect.width - 24 - abs(text_offset) * 2, draw_rect.height - 12))
    text_rect = text.get_rect(center=(draw_rect.centerx + text_offset, draw_rect.centery))
    surface.blit(text, text_rect)
    if focused and enabled:
        pygame.draw.rect(surface, UI_COLORS["text"], draw_rect.inflate(10, 10),
                         2, border_radius=10)
    return draw_rect
