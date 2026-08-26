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
from src.systems.audio import handle_music_shortcut
import sys

from src.data.controls import CONTROL_NOTES, CONTROL_SECTIONS
from src.ui.theme import body_font, title_font

STONE_DARK = (28, 30, 38)
STONE_MID = (42, 46, 58)
STONE_LIGHT = (62, 68, 82)
METAL_FRAME = (90, 94, 110)
YELLOW_GLOW = (255, 220, 120)
BLUE_GLOW = (80, 180, 255)
WHITE = (255, 255, 255)
BODY_TEXT = (215, 215, 220)

# What the player is told about the rules of a challenge. Every line has
# been checked against what the game actually does - the old list
# promised automatic hints that no code provides, and charged a heart
# for failing a challenge when only losing all your HP costs one.
RULES_LINES = [
    "Search objects to find learning topics.",
    "Study a topic now, or store it in your bag.",
    "First time you pass a challenge: +1 key.",
    "Defeating an enemy adds bonus time.",
    "Losing all your HP costs 1 of your 5 hearts.",
    "Wrong code costs nothing - submit again.",
]

# Manual geometry. Both screens read these so the tutorial's copy and
# this panel are the same object at the same size.
MANUAL_WIDTH = 780
MANUAL_HEIGHT = 580
ROW_HEIGHT = 22          # one key/action row
HEADER_HEIGHT = 30       # a section heading plus its breathing room
SECTION_GAP = 12
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
    col_height = panel.height - 200

    left = pygame.Rect(panel.left + 40, col_top, col_width, col_height)
    right = pygame.Rect(left.right + col_gap, col_top, col_width, col_height)
    footer = pygame.Rect(panel.left + 40, panel.bottom - 104,
                         panel.width - 80, 44)

    return panel, left, right, footer


def draw_control_rows(surface, rect, sections, header_font, key_font, line_font):
    """
    The control table: a blue section heading, then one row per key with
    the key in gold and what it does beside it.

    Rows rather than wrapped sentences because a player scanning for
    "which key opens the bag" reads down the left edge, and a bulleted
    paragraph makes them read every line to find it.
    """

    y = rect.top
    for heading, rows in sections:
        surface.blit(header_font.render(heading, True, BLUE_GLOW), (rect.left, y))
        y += HEADER_HEIGHT
        for key, action in rows:
            surface.blit(key_font.render(key, True, YELLOW_GLOW), (rect.left, y))
            surface.blit(line_font.render(action, True, BODY_TEXT),
                         (rect.left + KEY_COLUMN, y))
            y += ROW_HEIGHT
        y += SECTION_GAP
    return y


def draw_rule_lines(surface, rect, lines, header_font, line_font, header):
    """The right-hand column: a heading and a bulleted list."""

    surface.blit(header_font.render(header, True, BLUE_GLOW), (rect.left, rect.top))
    y = rect.top + HEADER_HEIGHT + 6
    for entry in lines:
        for wrapped in _wrap(line_font, f"- {entry}", rect.width):
            surface.blit(line_font.render(wrapped, True, BODY_TEXT), (rect.left, y))
            y += 24
        y += 6
    return y


def draw_manual_footer(surface, rect, font):
    """
    The two notes that a key table cannot carry: E doing two jobs, and
    Run/Submit being mouse buttons. Centred under both columns because
    they apply to the whole sheet, not to one column.
    """

    y = rect.top
    for note in CONTROL_NOTES:
        rendered = font.render(note, True, (170, 175, 190))
        surface.blit(rendered, (rect.centerx - rendered.get_width() // 2, y))
        y += 22
    return y


def draw_manual_columns(surface, left_col, right_col, footer,
                        header_font, key_font, line_font, note_font,
                        rules_header="PYTHON CHALLENGE RULES"):
    """
    The whole manual body: controls on the left, rules and editor keys
    on the right, notes underneath.

    The editor section is split off to the right so the left column stays
    a single uninterrupted list of things you press while walking around.
    """

    world_sections = [s for s in CONTROL_SECTIONS if s[0] != "IN THE CODE EDITOR"]
    editor_sections = [s for s in CONTROL_SECTIONS if s[0] == "IN THE CODE EDITOR"]

    draw_control_rows(surface, left_col, world_sections,
                      header_font, key_font, line_font)

    y = draw_rule_lines(surface, right_col, RULES_LINES,
                        header_font, line_font, rules_header)

    editor_rect = pygame.Rect(right_col.left, y + 10, right_col.width,
                              right_col.bottom - y)
    draw_control_rows(surface, editor_rect, editor_sections,
                      header_font, key_font, line_font)

    draw_manual_footer(surface, footer, note_font)


def how_to_play_screen(screen):
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

    heading_font = title_font(30)
    header_font = title_font(20, bold=False)
    key_font = body_font(17, bold=True)
    line_font = body_font(17)
    note_font = body_font(15)
    btn_font = title_font(22)

    panel_rect, left_col, right_col, footer = manual_layout(SCREEN_WIDTH, SCREEN_HEIGHT)
    back_rect = pygame.Rect(panel_rect.centerx - 70, panel_rect.bottom - 56, 140, 36)

    background = screen.copy()

    clock = pygame.time.Clock()
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if handle_music_shortcut(event):
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            # Left button only - see the note in main_menu.py: the wheel
            # and the right button raise this event as well.
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(event.pos):
                    return

        screen.blit(background, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (36, 38, 48), panel_rect, border_radius=8)
        pygame.draw.rect(screen, METAL_FRAME, panel_rect, 4, border_radius=8)
        pygame.draw.rect(screen, (26, 28, 36), panel_rect.inflate(-24, -24), border_radius=6)

        title = heading_font.render("HOW TO PLAY", True, WHITE)
        screen.blit(title, (panel_rect.centerx - title.get_width() // 2, panel_rect.top + 24))
        pygame.draw.line(screen, YELLOW_GLOW,
                          (panel_rect.left + 40, panel_rect.top + 70),
                          (panel_rect.right - 40, panel_rect.top + 70), 1)

        draw_manual_columns(screen, left_col, right_col, footer,
                            header_font, key_font, line_font, note_font)

        back_hovered = back_rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (60, 90, 130) if back_hovered else STONE_MID, back_rect, border_radius=4)
        pygame.draw.rect(screen, STONE_LIGHT, back_rect, 2, border_radius=4)
        bt = btn_font.render("BACK", True, WHITE)
        screen.blit(bt, (back_rect.centerx - bt.get_width() // 2, back_rect.centery - bt.get_height() // 2))

        pygame.display.flip()
        clock.tick(60)
