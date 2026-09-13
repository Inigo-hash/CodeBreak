import pygame

from src.ui.theme import (
    UI_COLORS,
    body_font,
    draw_button,
    draw_panel,
    title_font,
)


def open_final_challenge_warning(screen, background=None):
    """
    Warning shown after defeating the Stage 1 boss
    and before opening the final coding challenge.
    """

    clock = pygame.time.Clock()

    screen_w, screen_h = screen.get_size()

    if background is None:
        background = screen.copy()

    panel = pygame.Rect(
        0,
        0,
        min(680, screen_w - 80),
        360,
    )

    panel.center = (
        screen_w // 2,
        screen_h // 2,
    )

    continue_button = pygame.Rect(
        0,
        0,
        220,
        48,
    )

    continue_button.midbottom = (
        panel.centerx,
        panel.bottom - 28,
    )

    heading_font = title_font(32)
    text_font = body_font(20)

    lines = [
        "Warning: Before you can proceed to the next stage,",
        "you must complete one final coding challenge.",
        "",
        "This challenge will test the Python concepts",
        "you learned throughout Stage 1.",
        "",
        "Complete it to unlock the Corrupted Core Gate.",
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
                    return "continue"

            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and continue_button.collidepoint(event.pos)
            ):
                return "continue"

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

        overlay.fill(
            (0, 0, 0, 150)
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
            emphasized=True,
            radius=12,
        )

        heading = heading_font.render(
            "FINAL CHALLENGE",
            True,
            UI_COLORS["gold"],
        )

        screen.blit(
            heading,
            heading.get_rect(
                centerx=panel.centerx,
                top=panel.top + 28,
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
        # Continue button
        # -----------------------------------------------------

        draw_button(
            screen,
            continue_button,
            "CONTINUE",
            text_font,
            hovered=continue_button.collidepoint(mouse_pos),
        )

        pygame.display.flip()

        clock.tick(60)