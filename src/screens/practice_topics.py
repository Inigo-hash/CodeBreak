"""
practice_topics.py

Topic-selection screen for Code Practice.

Only topics already completed in the campaign can be selected.
Locked topics remain visible so the player can see what practice
content will become available later.
"""

import pygame

from src.data.topics import TOPICS
from src.ui.theme import (
    UI_COLORS,
    body_font,
    title_font,
    draw_panel,
)
from src.ui.topic_icons import topic_icon


COLUMNS = 3
CARD_GAP = 18

PANEL_WIDTH_RATIO = 0.72
PANEL_HEIGHT_RATIO = 0.72


def _stage_topic_ids(stage):
    """
    Return topic IDs belonging to this stage.

    stages.py stores challenge IDs in manual.topics, while Practice
    Mode works with topic IDs. Match them through topics.py.
    """

    challenge_ids = set(
        stage.get("manual", {}).get("topics", [])
    )

    return [
        topic_id
        for topic_id, topic in TOPICS.items()
        if topic.get("challenge_id") in challenge_ids
    ]


def open_practice_topics(
    screen,
    stage,
    completed_topics,
    background=None,
):
    """
    Open the Code Practice topic selector.

    Returns
    -------
    str | None

        topic_id
            Player selected an unlocked topic.

        None
            Player closed the screen.
    """

    clock = pygame.time.Clock()

    screen_w, screen_h = screen.get_size()

    # ---------------------------------------------------------
    # Background
    # ---------------------------------------------------------

    if background is None:
        background = screen.copy()

    # Light blur so the practice window clearly sits above gameplay.
    small = pygame.transform.smoothscale(
        background,
        (
            max(1, screen_w // 8),
            max(1, screen_h // 8),
        ),
    )

    blurred_background = pygame.transform.smoothscale(
        small,
        (screen_w, screen_h),
    )

    # ---------------------------------------------------------
    # Fonts
    # ---------------------------------------------------------

    title = title_font(30)
    subtitle = body_font(17)
    card_title = title_font(15)
    card_status = body_font(14, bold=True)
    footer_font = body_font(14)

    # ---------------------------------------------------------
    # Main panel
    # ---------------------------------------------------------

    panel = pygame.Rect(
        0,
        0,
        int(screen_w * PANEL_WIDTH_RATIO),
        int(screen_h * PANEL_HEIGHT_RATIO),
    )

    panel.center = (
        screen_w // 2,
        screen_h // 2,
    )

    content = panel.inflate(-54, -130)

    topic_ids = _stage_topic_ids(stage)

    completed = set(completed_topics)

    # ---------------------------------------------------------
    # Topic cards
    # ---------------------------------------------------------

    rows = max(
        1,
        (len(topic_ids) + COLUMNS - 1) // COLUMNS,
    )

    card_width = (
        content.width
        - CARD_GAP * (COLUMNS - 1)
    ) // COLUMNS

    card_height = (
        content.height
        - CARD_GAP * (rows - 1)
    ) // rows

    cards = []

    for index, topic_id in enumerate(topic_ids):

        row = index // COLUMNS
        column = index % COLUMNS

        rect = pygame.Rect(
            content.left
            + column * (card_width + CARD_GAP),

            content.top
            + row * (card_height + CARD_GAP),

            card_width,
            card_height,
        )

        cards.append(
            {
                "topic_id": topic_id,
                "rect": rect,
            }
        )

    # ---------------------------------------------------------
    # Main loop
    # ---------------------------------------------------------

    running = True

    while running:

        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    return None

            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            ):

                for card in cards:

                    if not card["rect"].collidepoint(
                        event.pos
                    ):
                        continue

                    topic_id = card["topic_id"]

                    if topic_id in completed:
                        return topic_id

        # -----------------------------------------------------
        # Draw background
        # -----------------------------------------------------

        screen.blit(
            blurred_background,
            (0, 0),
        )

        overlay = pygame.Surface(
            (screen_w, screen_h),
            pygame.SRCALPHA,
        )

        overlay.fill(
            (0, 0, 0, 125)
        )

        screen.blit(
            overlay,
            (0, 0),
        )

        # -----------------------------------------------------
        # Main panel
        # -----------------------------------------------------

        draw_panel(
            screen,
            panel,
            emphasized=True,
            radius=12,
        )

        heading = title.render(
            "CODE PRACTICE",
            True,
            UI_COLORS["gold"],
        )

        screen.blit(
            heading,
            (
                panel.left + 28,
                panel.top + 22,
            ),
        )

        stage_label = subtitle.render(
            f"{stage.get('name', 'Stage')} Topics",
            True,
            UI_COLORS["text_dim"],
        )

        screen.blit(
            stage_label,
            (
                panel.left + 30,
                panel.top + 62,
            ),
        )

        info = subtitle.render(
            "Complete a campaign topic to unlock its practice problems.",
            True,
            UI_COLORS["text"],
        )

        screen.blit(
            info,
            (
                panel.left + 30,
                panel.top + 88,
            ),
        )

        # -----------------------------------------------------
        # Cards
        # -----------------------------------------------------

        for card in cards:

            topic_id = card["topic_id"]
            rect = card["rect"]

            topic = TOPICS[topic_id]

            unlocked = (
                topic_id in completed
            )

            hovered = (
                unlocked
                and rect.collidepoint(mouse)
            )

            if unlocked:

                fill = (
                    UI_COLORS["button_fill_hover"]
                    if hovered
                    else UI_COLORS["button_fill"]
                )

                border = (
                    UI_COLORS["blue_bright"]
                    if hovered
                    else UI_COLORS["bronze"]
                )

            else:

                fill = UI_COLORS["stone_deep"]
                border = UI_COLORS["bronze_dark"]

            pygame.draw.rect(
                screen,
                fill,
                rect,
                border_radius=9,
            )

            pygame.draw.rect(
                screen,
                border,
                rect,
                2,
                border_radius=9,
            )

            # -------------------------------------------------
            # Topic icon
            # -------------------------------------------------

            icon = topic_icon(
                topic_id,
                48,
            )

            icon_rect = icon.get_rect(
                center=(
                    rect.centerx,
                    rect.top + 48,
                )
            )

            if unlocked:

                screen.blit(
                    icon,
                    icon_rect,
                )

            else:

                # Darken the icon while keeping it recognizable.
                locked_icon = icon.copy()

                locked_icon.fill(
                    (80, 80, 80, 170),
                    special_flags=pygame.BLEND_RGBA_MULT,
                )

                screen.blit(
                    locked_icon,
                    icon_rect,
                )

            # -------------------------------------------------
            # Topic title
            # -------------------------------------------------

            title_surface = card_title.render(
                topic["title"],
                True,
                (
                    UI_COLORS["text"]
                    if unlocked
                    else UI_COLORS["text_dim"]
                ),
            )

            screen.blit(
                title_surface,
                title_surface.get_rect(
                    center=(
                        rect.centerx,
                        rect.top + 88,
                    )
                ),
            )

            # -------------------------------------------------
            # Status
            # -------------------------------------------------

            if unlocked:

                status_text = (
                    "AVAILABLE"
                )

                status_color = (
                    UI_COLORS["modal_success"]
                )

            else:

                status_text = (
                    "LOCKED"
                )

                status_color = (
                    UI_COLORS["text_dim"]
                )

            status = card_status.render(
                status_text,
                True,
                status_color,
            )

            screen.blit(
                status,
                status.get_rect(
                    center=(
                        rect.centerx,
                        rect.bottom - 24,
                    )
                ),
            )

        # -----------------------------------------------------
        # Footer
        # -----------------------------------------------------

        footer = footer_font.render(
            "Click an available topic to practice   •   ESC = Back",
            True,
            UI_COLORS["text_dim"],
        )

        screen.blit(
            footer,
            (
                panel.left + 30,
                panel.bottom - 32,
            ),
        )

        pygame.display.flip()

        clock.tick(60)

    return None