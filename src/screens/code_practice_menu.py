"""
code_practice_menu.py

Landing screen for the CODE PRACTICE button.

Lets the player choose between practicing already-unlocked campaign
topics (practice_topics.py) or opening a free, ungraded coding
sandbox (Free Coding, via CodeEditor mode="free"). Neither branch is
opened from here - this screen only reports the player's choice back
to game.py, the same way the topic cards in practice_topics.py report
a topic_id rather than opening the editor themselves.
"""

import pygame

from src.ui.theme import (
    UI_COLORS,
    body_font,
    title_font,
    draw_panel,
    draw_button,
    TIER_PRIMARY,
    TIER_SECONDARY,
)


PANEL_WIDTH_RATIO = 0.5
PANEL_HEIGHT_RATIO = 0.42

# Buttons are compressed to this fraction of the panel's width
# rather than stretched edge to edge - a long, thin gold bar reads
# worse than a shorter, more square button.
BUTTON_WIDTH_RATIO = 0.62

OPTIONS = [
    {
        "result": "topics",
        "label": "PRACTICE BY TOPIC",
        "description": "Randomized problems from topics you've already unlocked.",
        "tier": TIER_PRIMARY,
    },
    {
        "result": "free",
        "label": "FREE CODING",
        "description": "Write and run any Python code. Nothing here is graded or saved.",
        "tier": TIER_SECONDARY,
    },
]


def open_code_practice_menu(screen, background=None):
    """
    Open the Code Practice landing screen.

    Returns
    -------
    str | None

        "topics"
            Player chose to practice unlocked campaign topics.

        "free"
            Player chose the free coding sandbox.

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
    option_font = title_font(18)
    desc_font = body_font(14)
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

    # Reserved so the button block never starts under the "CODE
    # PRACTICE" heading / subtitle drawn near the panel's top edge,
    # and so there's real breathing room above the footer line.
    HEADER_HEIGHT = 112
    FOOTER_HEIGHT = 46

    content_top = panel.top + HEADER_HEIGHT
    content_bottom = panel.bottom - FOOTER_HEIGHT
    available_height = content_bottom - content_top

    # ---------------------------------------------------------
    # Option buttons (stacked, shorter than the panel and
    # centered horizontally - not stretched edge to edge)
    # ---------------------------------------------------------

    gap = 26
    max_button_height = 86

    button_height = min(
        max_button_height,
        (available_height - gap * (len(OPTIONS) - 1)) // len(OPTIONS),
    )

    block_height = (
        button_height * len(OPTIONS)
        + gap * (len(OPTIONS) - 1)
    )

    # Center the whole button block in the space left after the
    # header and footer, rather than pinning it to the top.
    block_top = content_top + (available_height - block_height) // 2

    button_width = int(panel.width * BUTTON_WIDTH_RATIO)
    button_left = panel.centerx - button_width // 2

    buttons = []

    for index, option in enumerate(OPTIONS):

        rect = pygame.Rect(
            button_left,
            block_top + index * (button_height + gap),
            button_width,
            button_height,
        )

        buttons.append(
            {
                "option": option,
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

                for button in buttons:

                    if button["rect"].collidepoint(event.pos):
                        return button["option"]["result"]

        # -----------------------------------------------------
        # Draw background
        # -----------------------------------------------------

        screen.blit(blurred_background, (0, 0))

        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 125))
        screen.blit(overlay, (0, 0))

        # -----------------------------------------------------
        # Main panel
        # -----------------------------------------------------

        draw_panel(screen, panel, emphasized=True, radius=12)

        heading = title.render("CODE PRACTICE", True, UI_COLORS["gold"])

        screen.blit(
            heading,
            (panel.left + 28, panel.top + 22),
        )

        info = body_font(17).render(
            "Choose how you want to code.",
            True,
            UI_COLORS["text"],
        )

        screen.blit(
            info,
            (panel.left + 30, panel.top + 62),
        )

        # -----------------------------------------------------
        # Option buttons
        # -----------------------------------------------------

        for button in buttons:

            rect = button["rect"]
            option = button["option"]

            # The clickable/hover area is the full card, but draw_button
            # always centers its label inside the rect it's given - so it
            # only gets the top slice, leaving room below for the
            # description without the two overlapping.
            label_rect = pygame.Rect(
                rect.left,
                rect.top,
                rect.width,
                int(rect.height * 0.55),
            )

            hovered = rect.collidepoint(mouse)

            draw_button(
                screen,
                label_rect,
                option["label"],
                option_font,
                hovered=hovered,
                tier=option["tier"],
            )

            desc_surface = desc_font.render(
                option["description"],
                True,
                UI_COLORS["text_dim"],
            )

            screen.blit(
                desc_surface,
                desc_surface.get_rect(
                    center=(rect.centerx, label_rect.bottom + 20)
                ),
            )

        # -----------------------------------------------------
        # Footer
        # -----------------------------------------------------

        footer = footer_font.render(
            "Click an option   •   ESC = Back",
            True,
            UI_COLORS["text_dim"],
        )

        screen.blit(
            footer,
            (panel.left + 30, panel.bottom - 32),
        )

        pygame.display.flip()

        clock.tick(60)

    return None