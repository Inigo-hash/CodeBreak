"""Opening story and beginner walkthrough shown before the main menu."""

import math
import sys

import pygame

from src.systems.audio import apply_music_volume, handle_music_shortcut, music_shortcut_label
from src.ui.theme import UI_COLORS, body_font, draw_button, draw_panel, title_font


PAGES = (
    (
        "WELCOME TO CODEBREAK",
        "A dungeon adventure where your sword handles monsters and Python code unlocks the path ahead.",
        ("No programming experience is required.", "Mang Tahimik will guide you step by step."),
    ),
    (
        "YOUR FIRST STEPS",
        "Move, practise one attack, and solve a guided Hello, World! challenge before the real adventure begins.",
        ("W A S D / Arrow keys = move", "E = attack, interact, and continue dialogue"),
    ),
    (
        "YOU CAN ALWAYS GET HELP",
        "The menu keeps the two important choices first: Start Game, then How To Play. Question marks explain unfamiliar settings.",
        ("HELP ? reopens this walkthrough", "Gear = settings  |  F10 = mute background music"),
    ),
)


def opening_walkthrough(screen, replay=False):
    """Run the short, skippable launch guide; HELP can replay it later."""

    width, height = screen.get_size()
    try:
        backdrop = pygame.image.load(
            "assets/images/backgrounds/mainMenuBg1.png"
        ).convert()
        backdrop = pygame.transform.smoothscale(backdrop, (width, height))
    except (pygame.error, FileNotFoundError):
        backdrop = pygame.Surface((width, height))
        backdrop.fill(UI_COLORS["stone_deep"])

    if not replay:
        try:
            pygame.mixer.music.load("assets/audios/tutorial_background_music.mp3")
            apply_music_volume()
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    title = title_font(max(28, round(height * 0.045)))
    body = body_font(max(18, round(height * 0.025)))
    small = body_font(max(15, round(height * 0.019)), bold=True)
    button_font = title_font(max(18, round(height * 0.025)))
    panel = pygame.Rect(0, 0, min(920, width - 80), min(550, height - 90))
    panel.center = (width // 2, height // 2)
    next_button = pygame.Rect(panel.centerx - 125, panel.bottom - 76, 250, 48)
    skip_button = pygame.Rect(panel.right - 148, panel.top + 18, 120, 36)
    page = 0
    clock = pygame.time.Clock()
    shade = pygame.Surface((width, height), pygame.SRCALPHA)

    def wrap(text, font, max_width):
        lines, current = [], ""
        for word in text.split():
            candidate = f"{current} {word}".strip()
            if not current or font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if handle_music_shortcut(event):
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN,
                                 pygame.K_RIGHT):
                    page += 1
                    if page >= len(PAGES):
                        return
                elif event.key == pygame.K_LEFT and page > 0:
                    page -= 1
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if skip_button.collidepoint(event.pos):
                    return
                if next_button.collidepoint(event.pos):
                    page += 1
                    if page >= len(PAGES):
                        return

        t = pygame.time.get_ticks() / 1000.0
        screen.blit(backdrop, (0, 0))
        shade.fill((5, 8, 16, 181 + round(6 * math.sin(t * 0.65))))
        screen.blit(shade, (0, 0))
        draw_panel(screen, panel, emphasized=True, radius=12, alpha=248)

        heading, description, tips = PAGES[page]
        label = title.render(heading, True, UI_COLORS["gold"])
        screen.blit(label, label.get_rect(center=(panel.centerx, panel.top + 88)))
        y = panel.top + 150
        for line in wrap(description, body, panel.width - 100):
            rendered = body.render(line, True, UI_COLORS["text"])
            screen.blit(rendered, rendered.get_rect(center=(panel.centerx, y)))
            y += body.get_height() + 8
        y += 24
        for tip in tips:
            icon = small.render("?", True, UI_COLORS["stone_deep"])
            pygame.draw.circle(screen, UI_COLORS["blue_bright"], (panel.left + 78, y + 10), 14)
            screen.blit(icon, icon.get_rect(center=(panel.left + 78, y + 10)))
            screen.blit(small.render(tip, True, UI_COLORS["parchment"]),
                        (panel.left + 108, y))
            y += small.get_height() + 20

        draw_button(screen, next_button,
                    "OPEN MAIN MENU" if page == len(PAGES) - 1 else "NEXT",
                    button_font, hovered=next_button.collidepoint(pygame.mouse.get_pos()))
        draw_button(screen, skip_button, "SKIP", title_font(15),
                    hovered=skip_button.collidepoint(pygame.mouse.get_pos()))
        footer = small.render(
            f"Page {page + 1}/{len(PAGES)}  |  E / ENTER = continue  |  {music_shortcut_label()}",
            True, UI_COLORS["text_dim"],
        )
        screen.blit(footer, footer.get_rect(center=(panel.centerx, panel.bottom - 12)))
        pygame.display.flip()
