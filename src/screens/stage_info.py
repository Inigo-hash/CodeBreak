"""
stage_info.py

The Stage Information screen - the full-size panel behind the rail
buttons in src/ui/stage_panel.py. Four tabs share one window:

    STAGE MANUAL   what this stage is, how it works, the controls,
                   and which coding topics it teaches
    ENEMIES        bestiary entries for enemies the player has met
    ITEMS          searchable objects, collectibles and characters
    OBJECTIVES     the full checklist, including optional objectives

One screen with tabs rather than four separate screens: the player can
go Enemies -> Items without closing anything, and the blur, panel,
scrolling and close handling are written once instead of four times.

It follows the same modal pattern as profile.py and the inventory bag -
its own event loop over a blurred snapshot of the frozen game - which is
also what pauses the game while it is open.

Content is drawn once per tab switch into a tall off-screen surface, then
blitted through a clip rect at a scroll offset. Rendering the text every
frame would mean re-wrapping every paragraph 60 times a second for a
screen that only changes when you scroll it.
"""

import sys

import pygame

from src.data.challenges import CHALLENGES
from src.data.enemies import get_enemy
from src.data.items import get_item
from src.data.stages import stage_challenges
from src.ui.editor_widgets import wrap_text
from src.ui.stage_panel import (
    ACCENT,
    ACCENT_DIM,
    METAL_FRAME,
    PANEL_BG,
    PANEL_INNER,
    RAIL_BUTTONS,
    TEXT_DIM,
    TEXT_DONE,
    TEXT_MAIN,
    draw_tab_icon,
)


# Tab order and titles come straight from the rail, so the two can never
# disagree about which tabs exist or what they are called.
TABS = [(tab, label, key_label, key) for tab, label, key_label, key
        in RAIL_BUTTONS]
TAB_IDS = [tab for tab, _, _, _ in TABS]

CARD_BG      = (32, 35, 44)
DIVIDER      = (58, 62, 76)
SCROLL_STEP  = 48   # pixels per mouse-wheel notch

THREAT_COLORS = {
    "Low": (120, 200, 140),
    "Moderate": (230, 200, 110),
    "High": (230, 140, 90),
    "Boss": (230, 100, 100),
}

# Portraits are loaded on demand and kept here, so reopening the screen
# does not hit the disk again.
_portrait_cache = {}


def _load_portrait(path, size):
    """
    Load and scale a portrait, or return None if it cannot be read.

    Missing art must never take the game down: these paths point at
    animation frames that may well be renamed while the art is still in
    progress, and the caller draws a placeholder box instead.
    """

    if not path:
        return None

    key = (path, size)
    if key in _portrait_cache:
        return _portrait_cache[key]

    try:
        image = pygame.image.load(path).convert_alpha()
        image = pygame.transform.smoothscale(image, (size, size))
    except (pygame.error, FileNotFoundError):
        image = None

    _portrait_cache[key] = image
    return image


class _Fonts:
    """The one set of fonts every tab renderer draws with."""

    def __init__(self):
        self.title = pygame.font.SysFont("consolas", 24, bold=True)
        self.subtitle = pygame.font.SysFont("consolas", 14, bold=True)
        self.heading = pygame.font.SysFont("consolas", 17, bold=True)
        self.entry = pygame.font.SysFont("consolas", 16, bold=True)
        self.body = pygame.font.SysFont("consolas", 14)
        self.small = pygame.font.SysFont("consolas", 12, bold=True)
        self.tab = pygame.font.SysFont("consolas", 13, bold=True)


# ===========================================================================
#  SMALL DRAWING HELPERS
#  Each takes the y it should start at and returns the y the next block
#  should start at, so a tab renderer reads as a straight run of calls.
# ===========================================================================

def _heading(surface, fonts, text, x, y, width):
    label = fonts.heading.render(text, True, ACCENT)
    surface.blit(label, (x, y))
    y += label.get_height() + 4
    pygame.draw.line(surface, DIVIDER, (x, y), (x + width, y), 1)
    return y + 10


def _paragraph(surface, fonts, text, x, y, width, color=TEXT_MAIN,
               font=None):
    font = font or fonts.body
    for line in wrap_text(text, font, width):
        surface.blit(font.render(line, True, color), (x, y))
        y += font.get_height()
    return y


def _bullet(surface, fonts, text, x, y, width, color=TEXT_MAIN):
    surface.blit(fonts.body.render("-", True, ACCENT_DIM), (x, y))
    return _paragraph(surface, fonts, text, x + 16, y, width - 16, color)


def _key_row(surface, fonts, key, description, x, y, width):
    """A control row: the key on the left, what it does on the right."""

    key_col = 150
    surface.blit(fonts.small.render(key, True, ACCENT), (x, y + 2))
    return _paragraph(surface, fonts, description, x + key_col, y,
                      width - key_col, TEXT_MAIN)


def _text_block_height(fonts, texts, width, font=None):
    """
    How tall a group of paragraphs will be once wrapped, without drawing
    any of it. Cards need this up front: the box has to be filled before
    the text goes on top of it, but its height depends on that text.
    """

    font = font or fonts.body
    lines = 0
    for text in texts:
        lines += len(wrap_text(text, font, width))
    return lines * font.get_height()


# ===========================================================================
#  TAB RENDERERS
# ===========================================================================

def _render_manual(surface, fonts, stage, progress, x, y, width):
    manual = stage.get("manual", {})

    y = _paragraph(surface, fonts, manual.get("summary", ""), x, y, width)
    y += 18

    mechanics = manual.get("mechanics", [])
    if mechanics:
        y = _heading(surface, fonts, "HOW THIS STAGE WORKS", x, y, width)
        for line in mechanics:
            y = _bullet(surface, fonts, line, x, y, width) + 6
        y += 12

    controls = manual.get("controls", [])
    if controls:
        y = _heading(surface, fonts, "CONTROLS", x, y, width)
        for key, description in controls:
            y = _key_row(surface, fonts, key, description, x, y, width) + 6
        y += 12

    topics = stage_challenges(stage)
    if topics:
        y = _heading(surface, fonts, "TOPICS YOU WILL PRACTICE", x, y, width)
        for challenge_id, challenge in topics:
            title = fonts.entry.render(challenge.get("title", challenge_id),
                                       True, TEXT_MAIN)
            surface.blit(title, (x, y))

            difficulty = challenge.get("difficulty", "")
            if difficulty:
                tag = fonts.small.render(difficulty.upper(), True, TEXT_DIM)
                surface.blit(tag, (x + title.get_width() + 10, y + 4))

            y += title.get_height() + 2
            y = _paragraph(surface, fonts, challenge.get("objective", ""),
                           x, y, width, TEXT_DIM) + 10
        y += 12

    tips = manual.get("tips", [])
    if tips:
        y = _heading(surface, fonts, "TIPS", x, y, width)
        for tip in tips:
            y = _bullet(surface, fonts, tip, x, y, width, TEXT_DIM) + 6

    return y


def _render_enemies(surface, fonts, stage, progress, x, y, width):
    enemy_ids = stage.get("enemies", [])

    met = sum(1 for e in enemy_ids if progress.knows_enemy(e))
    y = _paragraph(
        surface, fonts,
        f"{met} of {len(enemy_ids)} recorded. Entries fill in once you "
        f"have met the enemy in person.",
        x, y, width, TEXT_DIM
    ) + 16

    for enemy_id in enemy_ids:
        enemy = get_enemy(enemy_id)
        if enemy is None:
            continue
        y = _render_enemy_card(surface, fonts, enemy,
                               progress.knows_enemy(enemy_id),
                               x, y, width) + 12

    return y


def _render_enemy_card(surface, fonts, enemy, known, x, y, width):
    portrait_size = 72
    pad = 12
    text_x = x + pad + portrait_size + pad
    text_width = width - (text_x - x) - pad

    # The card has to be filled before the text is drawn on top of it, so
    # its height is worked out first. These numbers mirror the drawing
    # order below exactly - change one and change the other.
    name_block = fonts.entry.get_height() + 6

    if known:
        text_height = (
            name_block
            + fonts.small.get_height() + 8                       # threat line
            + _text_block_height(fonts, [enemy.get("description", "")],
                                 text_width) + 8
            # BEHAVIOR and WEAKNESS: a small header above each paragraph.
            + 2 * (fonts.small.get_height() + 2 + 8)
            + _text_block_height(fonts, [enemy.get("behavior", ""),
                                         enemy.get("weakness", "")],
                                 text_width)
        )
    else:
        text_height = name_block + _text_block_height(
            fonts, ["You have not met this one yet."], text_width
        )

    card_height = max(portrait_size + pad * 2, text_height + pad * 2)
    card = pygame.Rect(x, y, width, card_height)

    pygame.draw.rect(surface, CARD_BG, card, border_radius=6)
    pygame.draw.rect(surface, METAL_FRAME if known else DIVIDER, card, 2,
                     border_radius=6)

    # -- portrait --
    portrait_rect = pygame.Rect(x + pad, y + pad, portrait_size, portrait_size)
    pygame.draw.rect(surface, (18, 20, 26), portrait_rect, border_radius=4)

    portrait = _load_portrait(enemy.get("portrait"), portrait_size) \
        if known else None

    if portrait is not None:
        surface.blit(portrait, portrait_rect)
    else:
        # Unknown enemies (and any missing art) get a question mark.
        mark = fonts.title.render("?", True, TEXT_DIM)
        surface.blit(mark, (portrait_rect.centerx - mark.get_width() // 2,
                            portrait_rect.centery - mark.get_height() // 2))

    pygame.draw.rect(surface, DIVIDER, portrait_rect, 2, border_radius=4)

    # -- text --
    ty = y + pad

    name = enemy["name"] if known else "???"
    surface.blit(fonts.entry.render(name, True,
                                    TEXT_MAIN if known else TEXT_DIM),
                 (text_x, ty))
    ty += fonts.entry.get_height() + 6

    if not known:
        _paragraph(surface, fonts, "You have not met this one yet.",
                   text_x, ty, text_width, TEXT_DIM)
        return card.bottom

    threat = enemy.get("threat", "Unknown")
    threat_color = THREAT_COLORS.get(threat, TEXT_DIM)
    threat_surf = fonts.small.render(f"THREAT: {threat.upper()}", True,
                                     threat_color)
    surface.blit(threat_surf, (text_x, ty))

    family = enemy.get("family")
    if family:
        family_surf = fonts.small.render(family.upper(), True, TEXT_DIM)
        surface.blit(family_surf,
                     (text_x + threat_surf.get_width() + 14, ty))

    ty += threat_surf.get_height() + 8

    ty = _paragraph(surface, fonts, enemy.get("description", ""),
                    text_x, ty, text_width, TEXT_MAIN) + 8

    for label, key in (("BEHAVIOR", "behavior"), ("WEAKNESS", "weakness")):
        surface.blit(fonts.small.render(label, True, ACCENT_DIM),
                     (text_x, ty))
        ty += fonts.small.get_height() + 2
        ty = _paragraph(surface, fonts, enemy.get(key, ""), text_x, ty,
                        text_width, TEXT_DIM) + 8

    return card.bottom


def _render_items(surface, fonts, stage, progress, x, y, width):
    item_ids = stage.get("items", [])

    found = sum(1 for i in item_ids if progress.knows_item(i))
    y = _paragraph(
        surface, fonts,
        f"{found} of {len(item_ids)} discovered. Search the world to fill "
        f"in the rest.",
        x, y, width, TEXT_DIM
    ) + 16

    # Grouped so the list stays readable as more entries are added.
    groups = [
        ("interactable", "INTERACTABLES"),
        ("collectible", "COLLECTIBLES"),
        ("npc", "CHARACTERS"),
    ]

    for kind, heading in groups:
        entries = [get_item(i) for i in item_ids
                   if get_item(i) and get_item(i).get("kind") == kind]
        if not entries:
            continue

        y = _heading(surface, fonts, heading, x, y, width)

        for entry in entries:
            y = _render_item_row(surface, fonts, entry,
                                 progress.knows_item(entry["id"]),
                                 x, y, width) + 10

        y += 8

    return y


def _render_item_row(surface, fonts, item, known, x, y, width):
    marker = "[x]" if known else "[ ]"
    surface.blit(fonts.body.render(marker, True,
                                   TEXT_DONE if known else ACCENT_DIM),
                 (x, y + 2))

    text_x = x + 34
    text_width = width - 34

    name = item["name"] if known else "???"
    surface.blit(fonts.entry.render(name, True,
                                    TEXT_MAIN if known else TEXT_DIM),
                 (text_x, y))
    y += fonts.entry.get_height() + 2

    if not known:
        return _paragraph(surface, fonts, "Not yet discovered.",
                          text_x, y, text_width, TEXT_DIM)

    y = _paragraph(surface, fonts, item.get("description", ""),
                   text_x, y, text_width, TEXT_DIM)

    hint = item.get("hint")
    if hint:
        y = _paragraph(surface, fonts, hint, text_x, y + 2, text_width,
                       ACCENT_DIM, fonts.small)

    return y


def _render_objectives(surface, fonts, stage, progress, x, y, width):
    objectives = stage.get("objectives", [])
    done, total = progress.objective_counts(stage)

    y = _paragraph(
        surface, fonts,
        f"{done} of {total} required objectives complete."
        + ("  Optional objectives are listed too." if any(
            o.get("optional") for o in objectives) else ""),
        x, y, width, TEXT_DIM
    ) + 16

    for objective in objectives:
        finished = progress.is_objective_done(objective["id"])

        marker = "[x]" if finished else "[ ]"
        surface.blit(fonts.entry.render(marker, True,
                                        TEXT_DONE if finished else ACCENT),
                     (x, y))

        text_x = x + 40
        text_width = width - 40

        y = _paragraph(surface, fonts, objective["text"], text_x, y,
                       text_width, TEXT_DIM if finished else TEXT_MAIN,
                       fonts.entry)

        # A second line naming what actually completes it, so an
        # objective is never a riddle about which barrel or which lesson.
        detail = _objective_detail(objective)
        if detail:
            y = _paragraph(surface, fonts, detail, text_x, y + 2,
                           text_width, TEXT_DIM, fonts.small)

        if objective.get("optional"):
            y = _paragraph(surface, fonts, "OPTIONAL", text_x, y + 2,
                           text_width, ACCENT_DIM, fonts.small)

        y += 14

    return y


def _objective_detail(objective):
    """One line explaining how an objective is completed, or None."""

    kind = objective.get("kind")
    target = objective.get("target")

    if kind == "interact":
        item = get_item(target)
        return f"Search: {item['name']}" if item else None

    if kind == "challenge":
        challenge = CHALLENGES.get(target)
        return f"Challenge: {challenge['title']}" if challenge else None

    if kind == "explore":
        return f"Reach: {target}"

    return None


_RENDERERS = {
    "manual": _render_manual,
    "enemies": _render_enemies,
    "items": _render_items,
    "objectives": _render_objectives,
}


def _build_content(tab, fonts, stage, progress, width):
    """
    Draw one tab into a surface tall enough to hold it, then trim that
    surface to the height actually used.

    Drawing into a deliberately over-tall scratch surface and cropping
    afterwards avoids a separate measuring pass: the renderers report the
    y they finished at, which is exactly the height needed.
    """

    scratch_height = 6000
    scratch = pygame.Surface((width, scratch_height))
    scratch.fill(PANEL_INNER)

    renderer = _RENDERERS[tab]
    used = renderer(scratch, fonts, stage, progress, 0, 0, width)

    height = max(1, min(scratch_height, int(used) + 4))
    return scratch.subsurface((0, 0, width, height)).copy()


# ===========================================================================
#  THE SCREEN ITSELF
# ===========================================================================

def open_stage_info(screen, stage, progress, background=None, tab="manual"):
    """
    Show the Stage Information screen and block until the player closes
    it, exactly like profile_screen().

    ``tab`` picks which tab opens first - the rail buttons in
    stage_panel.py pass the one that was clicked.
    """

    SCREEN_W, SCREEN_H = screen.get_size()
    clock = pygame.time.Clock()
    fonts = _Fonts()

    if background is None:
        background = screen.copy()

    if tab not in _RENDERERS:
        tab = "manual"

    # ---- Geometry ----
    panel_w = min(840, SCREEN_W - 100)
    panel_h = min(620, SCREEN_H - 80)
    panel = pygame.Rect((SCREEN_W - panel_w) // 2, (SCREEN_H - panel_h) // 2,
                        panel_w, panel_h)

    header_h = 56
    tab_h = 38
    footer_h = 54
    inner_pad = 16

    tab_bar = pygame.Rect(panel.left + inner_pad, panel.top + header_h,
                          panel.width - inner_pad * 2, tab_h)

    tab_width = tab_bar.width // len(TABS)
    tab_rects = {
        tab_id: pygame.Rect(tab_bar.left + i * tab_width, tab_bar.top,
                            tab_width, tab_h)
        for i, (tab_id, _, _, _) in enumerate(TABS)
    }

    view = pygame.Rect(
        panel.left + inner_pad,
        tab_bar.bottom + 12,
        panel.width - inner_pad * 2,
        panel.bottom - footer_h - (tab_bar.bottom + 12) - 8
    )

    content_pad = 14
    content_width = view.width - content_pad * 2 - 12  # 12 = scrollbar gutter

    back_rect = pygame.Rect(panel.right - inner_pad - 130,
                            panel.bottom - footer_h + 8, 130, 34)

    # ---- Content, rebuilt only when the tab changes ----
    content = _build_content(tab, fonts, stage, progress, content_width)
    scroll = 0

    def max_scroll():
        return max(0, content.get_height() - (view.height - content_pad * 2))

    def switch_tab(new_tab):
        nonlocal tab, content, scroll
        if new_tab == tab:
            return
        tab = new_tab
        content = _build_content(tab, fonts, stage, progress, content_width)
        scroll = 0

    running = True
    while running:
        clock.tick(60)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                # The rail's own hotkeys keep working in here, so M/J/K/O
                # jump between tabs instead of doing nothing.
                for tab_id, _, _, key in TABS:
                    if event.key == key:
                        switch_tab(tab_id)

                if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    step = -1 if event.key == pygame.K_LEFT else 1
                    index = (TAB_IDS.index(tab) + step) % len(TAB_IDS)
                    switch_tab(TAB_IDS[index])

                elif event.key == pygame.K_DOWN:
                    scroll = min(max_scroll(), scroll + SCROLL_STEP)
                elif event.key == pygame.K_UP:
                    scroll = max(0, scroll - SCROLL_STEP)
                elif event.key == pygame.K_PAGEDOWN:
                    scroll = min(max_scroll(), scroll + view.height)
                elif event.key == pygame.K_PAGEUP:
                    scroll = max(0, scroll - view.height)

            if event.type == pygame.MOUSEWHEEL and event.y != 0:
                scroll = max(0, min(max_scroll(),
                                    scroll - event.y * SCROLL_STEP))

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(event.pos):
                    running = False
                for tab_id, rect in tab_rects.items():
                    if rect.collidepoint(event.pos):
                        switch_tab(tab_id)

        # A tab switch can leave the offset past the end of shorter content.
        scroll = max(0, min(max_scroll(), scroll))

        # ---- Blurred backdrop (same trick as profile.py) ----
        small = pygame.transform.smoothscale(background,
                                             (SCREEN_W // 8, SCREEN_H // 8))
        screen.blit(pygame.transform.smoothscale(small, (SCREEN_W, SCREEN_H)),
                    (0, 0))

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

        # ---- Panel ----
        pygame.draw.rect(screen, PANEL_BG, panel, border_radius=10)
        pygame.draw.rect(screen, METAL_FRAME, panel, 3, border_radius=10)

        title = fonts.title.render("STAGE INFORMATION", True, TEXT_MAIN)
        screen.blit(title, (panel.left + inner_pad, panel.top + 14))

        stage_label = f"{stage.get('subtitle', '')}  {stage.get('name', '')}"
        subtitle = fonts.subtitle.render(stage_label.strip().upper(), True,
                                         ACCENT)
        screen.blit(subtitle, (panel.right - inner_pad - subtitle.get_width(),
                               panel.top + 22))

        # ---- Tabs ----
        for tab_id, label, key_label, _ in TABS:
            rect = tab_rects[tab_id]
            active = tab_id == tab
            hovered = rect.collidepoint(mouse_pos)

            pygame.draw.rect(screen,
                             PANEL_INNER if active else (30, 32, 40),
                             rect, border_radius=6)
            pygame.draw.rect(screen,
                             ACCENT if active else
                             (METAL_FRAME if hovered else DIVIDER),
                             rect, 2, border_radius=6)

            icon_rect = pygame.Rect(rect.left + 10, rect.centery - 8, 16, 16)
            draw_tab_icon(screen, icon_rect, tab_id,
                          ACCENT if active else TEXT_DIM)

            text = fonts.tab.render(f"{label}  ({key_label})", True,
                                    TEXT_MAIN if active else TEXT_DIM)
            screen.blit(text, (icon_rect.right + 8,
                               rect.centery - text.get_height() // 2))

        # ---- Content ----
        pygame.draw.rect(screen, PANEL_INNER, view, border_radius=6)
        pygame.draw.rect(screen, DIVIDER, view, 2, border_radius=6)

        previous_clip = screen.get_clip()
        screen.set_clip(view.inflate(-4, -4))
        screen.blit(content, (view.left + content_pad,
                              view.top + content_pad - scroll))
        screen.set_clip(previous_clip)

        # ---- Scrollbar (only when there is something to scroll) ----
        limit = max_scroll()
        if limit > 0:
            track = pygame.Rect(view.right - 12, view.top + 6, 6,
                                view.height - 12)
            pygame.draw.rect(screen, (22, 24, 30), track, border_radius=3)

            visible_ratio = (view.height - content_pad * 2) \
                / content.get_height()
            thumb_h = max(24, int(track.height * visible_ratio))
            thumb_y = track.top + int((track.height - thumb_h)
                                      * (scroll / limit))
            pygame.draw.rect(screen, METAL_FRAME,
                             (track.left, thumb_y, track.width, thumb_h),
                             border_radius=3)

        # ---- Footer ----
        hint = fonts.small.render(
            "ARROWS / WHEEL SCROLL    LEFT-RIGHT SWITCH TABS    ESC CLOSE",
            True, TEXT_DIM
        )
        screen.blit(hint, (panel.left + inner_pad,
                           panel.bottom - footer_h + 18))

        back_hovered = back_rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (60, 90, 130) if back_hovered else (42, 46, 58),
                         back_rect, border_radius=5)
        pygame.draw.rect(screen, ACCENT if back_hovered else METAL_FRAME,
                         back_rect, 2, border_radius=5)
        back_text = fonts.subtitle.render("BACK", True, TEXT_MAIN)
        screen.blit(back_text,
                    (back_rect.centerx - back_text.get_width() // 2,
                     back_rect.centery - back_text.get_height() // 2))

        pygame.display.flip()
