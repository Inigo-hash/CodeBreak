"""
trap_alert.py

Red warning popup shown the moment a trap fires, before its coding
challenge opens. Gives the player a deliberate beat and a button press
("START") instead of getting dropped straight into an editor mid-step.

Only shown when there's actually a challenge to start - a trap with
nothing to ask (player hasn't completed any topics yet) skips this
and just applies its damage silently, same as before.
"""

import pygame

from src.ui.theme import (
    TIER_PRIMARY,
    UI_COLORS,
    body_font,
    draw_button,
    draw_panel,
    title_font,
)


def open_trap_alert(screen, background=None):
    """
    Warning shown the instant a trap triggers.

    Returns "start" once the player presses the START button. There is
    no way to back out - the trap has already triggered.
    """

    clock = pygame.time.Clock()

    screen_w, screen_h = screen.get_size()

    if background is None:
        background = screen.copy()

    panel = pygame.Rect(
        0,
        0,
        min(640, screen_w - 80),
        300,
    )

    panel.center = (
        screen_w // 2,
        screen_h // 2,
    )

    start_button = pygame.Rect(
        0,
        0,
        220,
        48,
    )

    start_button.midbottom = (
        panel.centerx,
        panel.bottom - 28,
    )

    heading_font = title_font(32)
    text_font = body_font(20)

    lines = [
        "You triggered a hidden trap!",
        "",
        "Solve the coding challenge before the timer",
        "runs out, or you'll take damage.",
    ]

    pygame.event.clear()

    while True:

        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:

                if event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                ):
                    return "start"

            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and start_button.collidepoint(event.pos)
            ):
                return "start"

        # -----------------------------------------------------
        # Background
        # -----------------------------------------------------

        screen.blit(
            background,
            (0, 0),
        )

        overlay = pygame.Surface(
            (screen_w, screen_h),
            pygame.SRCALPHA,
        )

        # A red-tinted dim instead of the usual neutral black - the
        # one visual cue shared by every other screen using draw_panel,
        # so a trap reads as a threat before the player even reads
        # the heading.
        overlay.fill(
            (70, 0, 0, 150)
        )

        screen.blit(
            overlay,
            (0, 0),
        )

        # -----------------------------------------------------
        # Panel
        # -----------------------------------------------------

        draw_panel(
            screen,
            panel,
            emphasized=False,
            radius=12,
        )

        # Crimson rim drawn over the panel's normal bronze border -
        # the only theme.py-level change needed to make this read as
        # dangerous rather than a regular menu.
        pygame.draw.rect(
            screen,
            UI_COLORS["crimson"],
            panel,
            3,
            border_radius=12,
        )

        heading = heading_font.render(
            "TRAP!",
            True,
            UI_COLORS["crimson"],
        )

        screen.blit(
            heading,
            heading.get_rect(
                centerx=panel.centerx,
                top=panel.top + 26,
            ),
        )

        # -----------------------------------------------------
        # Warning text
        # -----------------------------------------------------

        y = panel.top + 92

        for line in lines:

            if not line:

                y += 12
                continue

            rendered = text_font.render(
                line,
                True,
                UI_COLORS["text"],
            )

            screen.blit(
                rendered,
                rendered.get_rect(
                    centerx=panel.centerx,
                    top=y,
                ),
            )

            y += text_font.get_height() + 5

        # -----------------------------------------------------
        # Start button
        # -----------------------------------------------------

        draw_button(
            screen,
            start_button,
            "START",
            text_font,
            hovered=start_button.collidepoint(mouse_pos),
            tier=TIER_PRIMARY,
        )

        pygame.display.flip()

        clock.tick(60)