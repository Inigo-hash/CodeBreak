"""
topic_requirements.py

Displays prerequisite topics that must be completed
before a learning topic can be challenged.
"""

import pygame

from src.data.topics import get_topic
from src.systems.audio import handle_music_shortcut
from src.ui.stage_panel import (
    ACCENT,
    PANEL_INNER,
    TEXT_DIM,
    TEXT_DONE,
    TEXT_MAIN,
)
from src.ui.theme import (
    UI_COLORS,
    body_font,
    draw_button,
    draw_panel,
    title_font,
)


def open_topic_requirements(
    screen,
    topic_id,
    completed_topics,
    background=None,
):
    """
    Show the requirement checklist for a topic.

    Returns:
        "continue" - all requirements are complete
        "locked"   - player closes the popup while requirements are missing
    """

    topic = get_topic(topic_id)

    if topic is None:
        return "locked"

    requirements = topic.get(
        "requirements",
        []
    )

    # Topics without requirements remain immediately accessible.
    if not requirements:
        return "continue"

    screen_w, screen_h = screen.get_size()

    if background is None:
        background = screen.copy()

    # ---------------------------------------------------------
    # Fonts
    # ---------------------------------------------------------

    title = title_font(28)
    topic_font = title_font(21)

    text_font = body_font(17)
    requirement_font = body_font(18, bold=True)

    button_font = title_font(
        16,
        bold=False
    )

    # ---------------------------------------------------------
    # Panel
    # ---------------------------------------------------------

    panel_width = min(
        680,
        int(screen_w * 0.60)
    )

    panel_height = 420

    panel_rect = pygame.Rect(
        0,
        0,
        panel_width,
        panel_height
    )

    panel_rect.center = (
        screen_w // 2,
        screen_h // 2
    )

    requirements_rect = pygame.Rect(
        panel_rect.left + 35,
        panel_rect.top + 145,
        panel_rect.width - 70,
        170
    )

    button_rect = pygame.Rect(
        0,
        0,
        190,
        48
    )

    button_rect.centerx = panel_rect.centerx
    button_rect.bottom = panel_rect.bottom - 25

    clock = pygame.time.Clock()

    pygame.event.clear()

    # ---------------------------------------------------------
    # Main loop
    # ---------------------------------------------------------

    while True:

        completed = set(
            completed_topics
        )

        unlocked = all(
            requirement_id in completed
            for requirement_id in requirements
        )

        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()

                raise SystemExit

            if handle_music_shortcut(event):
                continue

            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE
            ):
                return "locked"

            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and button_rect.collidepoint(event.pos)
            ):

                if unlocked:
                    return "continue"

                return "locked"

        # -----------------------------------------------------
        # Background
        # -----------------------------------------------------

        screen.blit(
            background,
            (0, 0)
        )

        overlay = pygame.Surface(
            (screen_w, screen_h),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 0, 0, 175)
        )

        screen.blit(
            overlay,
            (0, 0)
        )

        # -----------------------------------------------------
        # Main panel
        # -----------------------------------------------------

        draw_panel(
            screen,
            panel_rect,
            emphasized=unlocked,
            radius=10
        )

        # -----------------------------------------------------
        # Heading
        # -----------------------------------------------------

        heading_surface = title.render(
            "TOPIC REQUIREMENTS",
            True,
            TEXT_DONE if unlocked else ACCENT
        )

        screen.blit(
            heading_surface,
            (
                panel_rect.centerx
                - heading_surface.get_width() // 2,

                panel_rect.top + 22
            )
        )

        # -----------------------------------------------------
        # Topic name
        # -----------------------------------------------------

        topic_surface = topic_font.render(
            topic["title"],
            True,
            TEXT_MAIN
        )

        screen.blit(
            topic_surface,
            (
                panel_rect.centerx
                - topic_surface.get_width() // 2,

                panel_rect.top + 65
            )
        )

        # -----------------------------------------------------
        # Status message
        # -----------------------------------------------------

        if unlocked:

            message_text = (
                "All requirements are complete. "
                "You may challenge this topic."
            )

        else:

            message_text = (
                "You don't meet the requirements "
                "to challenge this topic."
            )

        message_surface = text_font.render(
            message_text,
            True,
            TEXT_DIM
        )

        screen.blit(
            message_surface,
            (
                panel_rect.centerx
                - message_surface.get_width() // 2,

                panel_rect.top + 105
            )
        )

        # -----------------------------------------------------
        # Requirements area
        # -----------------------------------------------------

        pygame.draw.rect(
            screen,
            PANEL_INNER,
            requirements_rect,
            border_radius=7
        )

        pygame.draw.rect(
            screen,
            UI_COLORS["bronze_dark"],
            requirements_rect,
            1,
            border_radius=7
        )

        requirement_y = (
            requirements_rect.top + 25
        )

        for requirement_id in requirements:

            requirement_topic = get_topic(
                requirement_id
            )

            requirement_name = (
                requirement_topic["title"]
                if requirement_topic
                else requirement_id
            )

            requirement_done = (
                requirement_id in completed
            )

            # Same visual language as Objectives:
            #
            # [x] completed -> green
            # [ ] incomplete -> gold
            marker = (
                "[x]"
                if requirement_done
                else "[ ]"
            )

            marker_surface = (
                requirement_font.render(
                    marker,
                    True,
                    TEXT_DONE
                    if requirement_done
                    else ACCENT
                )
            )

            screen.blit(
                marker_surface,
                (
                    requirements_rect.left + 24,
                    requirement_y
                )
            )

            requirement_surface = (
                requirement_font.render(
                    f"Complete {requirement_name}",
                    True,
                    TEXT_DIM
                    if requirement_done
                    else TEXT_MAIN
                )
            )

            screen.blit(
                requirement_surface,
                (
                    requirements_rect.left + 82,
                    requirement_y
                )
            )

            requirement_y += 58

        # -----------------------------------------------------
        # Button
        # -----------------------------------------------------

        button_label = (
            "CONTINUE"
            if unlocked
            else "BACK"
        )

        draw_button(
            screen,
            button_rect,
            button_label,
            button_font,
            hovered=button_rect.collidepoint(
                mouse_pos
            )
        )

        pygame.display.flip()

        clock.tick(60)