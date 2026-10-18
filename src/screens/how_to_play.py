"""
how_to_play.py

The How To Play panel, and the shared drawing of the manual it holds.

The tutorial shows the player the same manual before the first stage
(see draw_stage_manual in src/screens/tutorial.py), so the layout, the
fonts and the content all live here and both screens call into them.
That is deliberate: this panel and the tutorial's copy used to be two
hand-written lists, and they drifted.

The controls themselves are not written here either - they come from
src/data/controls.py, which is checked against the actual key handlers.
"""

import pygame
from functools import lru_cache
from src.ui.text_layout import fit_text, wrap_text
from src.systems.audio import handle_music_shortcut
import sys

from src.data.controls import CONTROL_NOTES, CONTROL_SECTIONS
from src.ui.theme import UI_COLORS, body_font, title_font

# Every color here now comes from the shared modal palette in
# ui/theme.py rather than being redeclared. The old names are kept because
# tutorial.py imports two of them to draw the same manual - see
# docs/style-guide.md for what each token means.
STONE_DARK = UI_COLORS["modal_inner"]
STONE_MID = UI_COLORS["modal_button"]
STONE_LIGHT = UI_COLORS["modal_button_edge"]
METAL_FRAME = UI_COLORS["modal_frame"]
YELLOW_GLOW = UI_COLORS["modal_accent"]
BLUE_GLOW = UI_COLORS["modal_heading"]
WHITE = UI_COLORS["modal_text"]
BODY_TEXT = UI_COLORS["modal_text_soft"]

# What the player is told about the rules of a challenge. Every line has
# been checked against what the game actually does - the old list
# promised automatic hints that no code provides, and charged a heart
# for failing a challenge when only losing all your HP costs one.
RULES_LINES = [
    "Search objects to find learning topics.",
    "Study a topic now, or store it in your bag.",
    "Defeating an area full of enemies: +1 key.",
    "Defeating an enemy adds bonus time.",
    "Losing all your HP costs 1 of your 5 hearts.",
    "Wrong code costs nothing - submit again.",
]

# Manual geometry. Both screens read these so the tutorial's copy and
# this panel are the same object at the same size.
MANUAL_WIDTH = 900
MANUAL_HEIGHT = 700
ROW_HEIGHT = 20
HEADER_HEIGHT = 27
SECTION_GAP = 5
FOOTER_LINE_HEIGHT = 18
KEY_COLUMN = 130         # where the action text starts, measured from the
                         # column's left edge - wide enough for the longest
                         # key label ("Ctrl + C / X / V")


def _wrap(font, text, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current}{word} "
        if font.size(test)[0] <= max_width:
            current = test
        else:
            lines.append(current.rstrip())
            current = f"{word} "
    if current:
        lines.append(current.rstrip())
    return lines


def manual_layout(screen_width, screen_height):
    """
    Panel, the two column rects and the footer strip.

    Clamped to the screen so a windowed 1366x768 laptop gets a panel
    that still fits rather than one running off the bottom edge.
    """

    panel = pygame.Rect(0, 0,
                        min(MANUAL_WIDTH, screen_width - 40),
                        min(MANUAL_HEIGHT, screen_height - 40))
    panel.center = (screen_width // 2, screen_height // 2)

    col_gap = 30
    col_width = (panel.width - 80 - col_gap) // 2
    col_top = panel.top + 100
    # The footer contains three separate notes and the Back button has its
    # own row below them. Derive the column height from those reserved areas
    # instead of letting the manual body continue underneath both.
    footer_height = 32
    footer_bottom = panel.bottom - 72

    footer = pygame.Rect(
        panel.left + 40,
        footer_bottom - footer_height,
        panel.width - 80,
        footer_height,
    )
    col_height = max(0, footer.top - col_top - 12)

    left = pygame.Rect(panel.left + 40, col_top, col_width, col_height)
    right = pygame.Rect(left.right + col_gap, col_top, col_width, col_height)

    return panel, left, right, footer


def draw_control_rows(surface, rect, sections, header_font, key_font, line_font):
    """
    The control table: a blue section heading, then one row per key with
    the key in gold and what it does beside it.

    Rows rather than wrapped sentences because a player scanning for
    "which key opens the bag" reads down the left edge, and a bulleted
    paragraph makes them read every line to find it.

    The spacing tightens itself when the list outgrows its column. The
    control scheme has gained keys twice since this panel was written, and
    each time the last rows quietly slid underneath the footer - so the
    column now shrinks its own line height rather than overflowing.
    """

    key_width = min(rect.w // 2, max(key_font.size(key)[0] for _, rows in sections for key, _ in rows) + 16)
    line_height = max(line_font.get_linesize(), key_font.get_linesize()) + 4
    y = rect.top
    for heading, rows in sections:
        label = fit_text(header_font, heading, BLUE_GLOW, (rect.w, header_font.get_height()))
        surface.blit(label, (rect.left, y))
        y += label.get_height() + 12
        for key, action in rows:
            key_label = fit_text(key_font, key, YELLOW_GLOW, (key_width - 12, line_height))
            surface.blit(key_label, (rect.left, y))
            lines = wrap_text(action, line_font, rect.w - key_width)
            for index, line in enumerate(lines):
                surface.blit(line_font.render(line, True, BODY_TEXT), (rect.left + key_width, y + index * line_height))
            y += max(1, len(lines)) * line_height + 7
        y += 16
    return y


def draw_rule_lines(surface, rect, lines, header_font, line_font, header):
    """The right-hand column: a heading and a bulleted list."""

    title = fit_text(header_font, header, BLUE_GLOW, (rect.w, header_font.get_height()))
    surface.blit(title, (rect.left, rect.top))
    y = rect.top + title.get_height() + 12
    for entry in lines:
        for wrapped in wrap_text(f"- {entry}", line_font, rect.width):
            surface.blit(line_font.render(wrapped, True, BODY_TEXT), (rect.left, y))
            y += line_font.get_linesize() + 4
        y += 10
    return y


def draw_manual_footer(surface, rect, font):
    """
    The two notes that a key table cannot carry: E doing two jobs, and
    Run/Submit being mouse buttons. Centred under both columns because
    they apply to the whole sheet, not to one column.
    """

    y = rect.top
    for note in CONTROL_NOTES:
        for line in wrap_text(note, font, rect.w):
            rendered = font.render(line, True, UI_COLORS["modal_text_dim"])
            surface.blit(rendered, (rect.x, y))
            y += font.get_linesize() + 3
        y += 8
    return y


@lru_cache(maxsize=8)
def _manual_content(width, left_width, right_x, right_width,
                    header_font, key_font, line_font, note_font, rules_header):
    """Build once per geometry/font setting; scrolling only blits the result."""
    world_sections = [s for s in CONTROL_SECTIONS if s[0] != "IN THE CODE EDITOR"]
    editor_sections = [s for s in CONTROL_SECTIONS if s[0] == "IN THE CODE EDITOR"]

    # Measure/draw onto a tall content surface. Scrolling moves complete rows;
    # reducing row spacing independently of glyph height caused the overlaps.
    body = pygame.Surface((width, 6000), pygame.SRCALPHA)
    left = pygame.Rect(0, 0, left_width, 6000)
    right = pygame.Rect(right_x, 0, right_width, 6000)
    left_bottom = draw_control_rows(body, left, world_sections,
                      header_font, key_font, line_font)

    y = draw_rule_lines(body, right, RULES_LINES,
                        header_font, line_font, rules_header)

    editor_rect = pygame.Rect(right.left, y + 20, right.width, 6000 - y)
    right_bottom = draw_control_rows(body, editor_rect, editor_sections,
                      header_font, key_font, line_font)

    notes = pygame.Rect(0, max(left_bottom, right_bottom) + 24, width - 14, 1000)
    used = draw_manual_footer(body, notes, note_font)
    return body.subsurface((0,0,width,min(6000,max(1,used)))).copy(), used


def draw_manual_columns(surface, left_col, right_col, footer,
                        header_font, key_font, line_font, note_font,
                        rules_header="PYTHON CHALLENGE RULES", scroll=0):
    """Scrollable measured columns shared by How To Play and the tutorial."""
    viewport = left_col.union(right_col).union(footer)
    body, used = _manual_content(viewport.w - 14, left_col.w - 14,
                                right_col.x - viewport.x, right_col.w - 14,
                                header_font,key_font,line_font,note_font,rules_header)
    limit = max(0, used - viewport.h)
    scroll = max(0, min(scroll, limit))
    old_clip = surface.get_clip()
    surface.set_clip(viewport)
    surface.blit(body, (viewport.x, viewport.y - scroll))
    surface.set_clip(old_clip)
    if limit:
        track = pygame.Rect(viewport.right - 5, viewport.y, 4, viewport.h)
        pygame.draw.rect(surface, UI_COLORS['bronze_dark'], track)
        height = max(24, round(track.h * viewport.h / used))
        thumb = pygame.Rect(track.x, track.y + round((track.h-height)*scroll/limit), 4, height)
        pygame.draw.rect(surface, UI_COLORS['gold'], thumb)
    return limit


def how_to_play_screen(screen):
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

    heading_font = title_font(30)
    header_font = title_font(18, bold=False)
    key_font = body_font(14, bold=True)
    line_font = body_font(14)
    note_font = body_font(12)
    btn_font = title_font(22)

    panel_rect, left_col, right_col, footer = manual_layout(SCREEN_WIDTH, SCREEN_HEIGHT)
    back_rect = pygame.Rect(panel_rect.centerx - 70, panel_rect.bottom - 56, 140, 36)
    back_rect.right = panel_rect.right - 40

    # Imported here, not at module scope: main_menu imports this module, so
    # naming it up top would close the import loop.
    from src.screens.main_menu import paint_menu_backdrop

    clock = pygame.time.Clock()
    running = True
    scroll = 0
    limit = 0

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if handle_music_shortcut(event):
                continue
            if (event.type == pygame.KEYDOWN
                    and event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE)):
                return
            if event.type == pygame.MOUSEWHEEL:
                scroll = max(0, min(limit, scroll - event.y * 70))
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                amount = 280 if event.key in (pygame.K_PAGEUP, pygame.K_PAGEDOWN) else 50
                scroll = max(0, min(limit, scroll + amount * (1 if event.key in (pygame.K_DOWN, pygame.K_PAGEDOWN) else -1)))
            # Left button only - see the note in main_menu.py: the wheel
            # and the right button raise this event as well.
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(event.pos):
                    return

        # Repainted every frame rather than held as the snapshot this screen
        # used to take on entry, so the dungeon behind the panel stays alive.
        paint_menu_backdrop(screen, pygame.time.get_ticks() / 1000.0)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, UI_COLORS["modal_panel"], panel_rect, border_radius=8)
        pygame.draw.rect(screen, METAL_FRAME, panel_rect, 4, border_radius=8)
        pygame.draw.rect(screen, UI_COLORS["modal_inner"], panel_rect.inflate(-24, -24),
                         border_radius=6)

        title = fit_text(heading_font, 'HOW TO PLAY', WHITE, (panel_rect.w - 100, 42))
        screen.blit(title, title.get_rect(midtop=(panel_rect.centerx,panel_rect.top+20)))
        pygame.draw.line(screen, YELLOW_GLOW,
                          (panel_rect.left + 40, panel_rect.top + 70),
                          (panel_rect.right - 40, panel_rect.top + 70), 1)

        limit = draw_manual_columns(screen, left_col, right_col, footer,
                                    header_font, key_font, line_font, note_font, scroll=scroll)
        hint = fit_text(note_font, 'Scroll / Up / Down to read all controls', BODY_TEXT,
                        (back_rect.left-panel_rect.left-64, 22))
        screen.blit(hint, (panel_rect.left + 40, back_rect.y + 8))

        back_hovered = back_rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen,
                         UI_COLORS["modal_button_hover"] if back_hovered else STONE_MID,
                         back_rect, border_radius=4)
        pygame.draw.rect(screen, STONE_LIGHT, back_rect, 2, border_radius=4)
        bt = fit_text(btn_font, 'BACK', WHITE, (back_rect.w - 20, back_rect.h - 10))
        screen.blit(bt, (back_rect.centerx - bt.get_width() // 2, back_rect.centery - bt.get_height() // 2))

        pygame.display.flip()
        clock.tick(60)
