"""
practice_topics.py

Topic-selection screen for Code Practice.

Only topics already completed in the campaign can be selected.
Locked topics remain visible so the player can see what practice
content will become available later.
"""

import pygame
from src.ui.text_layout import fit_text, draw_text_block


def topic_card_layout(rect):
    """Separate icon, title and status even in a short three-row grid."""
    rect = pygame.Rect(rect)
    if rect.h < 150:
        icon_size = min(32, max(20, rect.h - 28))
        icon = pygame.Rect(rect.x + 12, rect.centery - icon_size // 2, icon_size, icon_size)
        title = pygame.Rect(icon.right + 10, rect.y + 7, rect.right - icon.right - 22, max(18, rect.h - 36))
        status = pygame.Rect(title.x, rect.bottom - 26, title.w, 18)
    else:
        icon = pygame.Rect(rect.centerx - 20, rect.y + 20, 40, 40)
        title = pygame.Rect(rect.x + 16, icon.bottom + 10, rect.w - 32, 48)
        status = pygame.Rect(rect.x + 16, rect.bottom - 42, rect.w - 32, 24)
    return icon, title, status

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
    developer_access=False,
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

    # The header text (stage label + info line) is drawn at panel.top
    # + 62 / + 88, so content has to start below that or the topic
    # cards paint over it - only a sliver survives in the 18px gaps
    # between columns, which is what shows up as stray text there.
    content = pygame.Rect(
        panel.left + 48,
        panel.top + 168,
        panel.width - 96,
        panel.height - 168 - 80,
    )

    topic_ids = _stage_topic_ids(stage)

    completed = set(_stage_topic_ids(stage) if developer_access else completed_topics)

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

        heading = fit_text(title, 'CODE PRACTICE', UI_COLORS['gold'], (panel.w - 160, 46))

        screen.blit(
            heading,
            (
                panel.centerx - heading.get_width() // 2,
                panel.top + 34,
            ),
        )

        stage_label = fit_text(subtitle, f"{stage.get('name', 'Stage')} Topics",
                               UI_COLORS['text_dim'], (panel.w - 96, 28))

        screen.blit(
            stage_label,
            (
                panel.left + 48,
                panel.top + 92,
            ),
        )

        info = fit_text(subtitle, 'Complete a campaign topic to unlock its practice problems.',
                        UI_COLORS['text'], (panel.w - 96, 28))

        screen.blit(
            info,
            (
                panel.left + 48,
                panel.top + 128,
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

            icon_rect, title_rect, status_rect = topic_card_layout(rect)
            icon = topic_icon(topic_id, icon_rect.w)

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

            draw_text_block(screen, topic['title'], card_title,
                            UI_COLORS['text'] if unlocked else UI_COLORS['text_dim'],
                            title_rect, center=True)

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

            status = fit_text(card_status, status_text, status_color, status_rect.size)
            screen.blit(status, status.get_rect(center=status_rect.center))

        # -----------------------------------------------------
        # Footer
        # -----------------------------------------------------

        footer = fit_text(footer_font, 'Click an available topic to practice   •   ESC = Back',
                          UI_COLORS['text_dim'], (panel.w - 128, 24))

        screen.blit(
            footer,
            (
                panel.left + 64,
                panel.bottom - 54,
            ),
        )

        pygame.display.flip()

        clock.tick(60)

    return None
