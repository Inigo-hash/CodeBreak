import pygame
import sys

STONE_DARK = (28, 30, 38)
STONE_MID = (42, 46, 58)
STONE_LIGHT = (62, 68, 82)
METAL_FRAME = (90, 94, 110)
YELLOW_GLOW = (255, 220, 120)
BLUE_GLOW = (80, 180, 255)
WHITE = (255, 255, 255)

CONTROLS_LINES = [
    "W A S D  -  Move",
    "E  -  Attack",
    "L-SHIFT  -  Dodge",
    "F  -  Interact",
    "Code Editor opens automatically at coding challenges.",
]

RULES_LINES = [
    "Solve the challenge to pass a trap or defeat a stage boss.",
    "Failing a trap or losing a fight costs 1 heart (5 total).",
    "0 hearts restarts the current stage; completed stages stay unlocked.",
    "Stuck? Repeated fails unlock progressive hints automatically.",
    "A topic is 'learned' once every challenge for it is passed.",
]


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


def how_to_play_screen(screen):
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

    title_font = pygame.font.SysFont("consolas", 30, bold=True)
    header_font = pygame.font.SysFont("consolas", 20, bold=True)
    line_font = pygame.font.SysFont("consolas", 17)
    btn_font = pygame.font.SysFont("consolas", 22, bold=True)

    panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 340, SCREEN_HEIGHT // 2 - 260, 680, 520)
    back_rect = pygame.Rect(panel_rect.centerx - 70, panel_rect.bottom - 56, 140, 36)

    col_gap = 30
    col_width = (panel_rect.width - 80 - col_gap) // 2
    left_col = pygame.Rect(panel_rect.left + 40, panel_rect.top + 100, col_width, panel_rect.height - 180)
    right_col = pygame.Rect(left_col.right + col_gap, panel_rect.top + 100, col_width, panel_rect.height - 180)

    background = screen.copy()

    clock = pygame.time.Clock()
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):
                    return

        screen.blit(background, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (36, 38, 48), panel_rect, border_radius=8)
        pygame.draw.rect(screen, METAL_FRAME, panel_rect, 4, border_radius=8)
        pygame.draw.rect(screen, (26, 28, 36), panel_rect.inflate(-24, -24), border_radius=6)

        title = title_font.render("HOW TO PLAY", True, WHITE)
        screen.blit(title, (panel_rect.centerx - title.get_width() // 2, panel_rect.top + 24))
        pygame.draw.line(screen, YELLOW_GLOW,
                          (panel_rect.left + 40, panel_rect.top + 70),
                          (panel_rect.right - 40, panel_rect.top + 70), 1)

        for col_rect, header, lines in (
            (left_col, "CONTROLS + MECHANICS", CONTROLS_LINES),
            (right_col, "PYTHON CHALLENGE RULES", RULES_LINES),
        ):
            h = header_font.render(header, True, BLUE_GLOW)
            screen.blit(h, (col_rect.left, col_rect.top))
            y = col_rect.top + 36
            for entry in lines:
                for wrapped in _wrap(line_font, f"- {entry}", col_rect.width):
                    txt = line_font.render(wrapped, True, (215, 215, 220))
                    screen.blit(txt, (col_rect.left, y))
                    y += 24
                y += 6

        back_hovered = back_rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (60, 90, 130) if back_hovered else STONE_MID, back_rect, border_radius=4)
        pygame.draw.rect(screen, STONE_LIGHT, back_rect, 2, border_radius=4)
        bt = btn_font.render("BACK", True, WHITE)
        screen.blit(bt, (back_rect.centerx - bt.get_width() // 2, back_rect.centery - bt.get_height() // 2))

        pygame.display.flip()
        clock.tick(60)