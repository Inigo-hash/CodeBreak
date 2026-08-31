"""The explanatory modal shown when the player inspects a stage exit."""

import sys

import pygame

from src.data.enemies import get_enemy
from src.systems.audio import handle_music_shortcut
from src.ui.theme import (
    TIER_PRIMARY, TIER_TERTIARY, UI_COLORS, body_font, draw_button,
    draw_panel, title_font,
)


def open_stage_gate(screen, status, gate_name="Stage Exit", background=None,
                    show_boss_requirement=True):
    """Explain the gate requirements and confirm an unlocked stage exit.

    Returns ``"exit"`` only after the player deliberately confirms an
    unlocked gate. Every other close path returns ``"stay"``.
    """

    clock = pygame.time.Clock()
    width, height = screen.get_size()
    backdrop = (screen if background is None else background).copy()

    panel = pygame.Rect(0, 0, min(760, width - 48), min(620, height - 48))
    panel.center = (width // 2, height // 2)
    title = title_font(34)
    heading = title_font(21)
    text_font = body_font(17)
    small = body_font(14)
    button_font = title_font(20)

    button_width = min(280, panel.width // 2 - 34)
    primary = pygame.Rect(
        panel.centerx - button_width - 8,
        panel.bottom - 72,
        button_width,
        44,
    )
    secondary = pygame.Rect(
        panel.centerx + 8,
        panel.bottom - 72,
        button_width,
        44,
    )

    if status.unlocked:
        title_text = "STAGE COMPLETE"
        primary_label = "COMPLETE STAGE"
    else:
        title_text = "THE GATE IS SEALED"
        primary_label = "RETURN TO ISLAND"

    while True:
        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if handle_music_shortcut(event):
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "stay"
                if event.key in (
                    pygame.K_e, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE
                ):
                    return "exit" if status.unlocked else "stay"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if primary.collidepoint(event.pos):
                    return "exit" if status.unlocked else "stay"
                if secondary.collidepoint(event.pos):
                    return "stay"

        screen.blit(backdrop, (0, 0))
        shade = pygame.Surface((width, height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 180))
        screen.blit(shade, (0, 0))
        draw_panel(screen, panel, emphasized=status.unlocked, radius=12)

        title_surface = title.render(
            title_text,
            True,
            UI_COLORS["blue_bright"] if status.unlocked else UI_COLORS["gold"],
        )
        screen.blit(title_surface, title_surface.get_rect(
            center=(panel.centerx, panel.top + 48)
        ))
        gate_surface = small.render(gate_name.upper(), True, UI_COLORS["text_dim"])
        screen.blit(gate_surface, gate_surface.get_rect(
            center=(panel.centerx, panel.top + 78)
        ))

        row_left = panel.left + 52
        row_right = panel.right - 52
        row_width = row_right - row_left
        rows = (
            (
                "KEYS COLLECTED",
                f"{status.keys} / {status.required_keys}",
                status.keys >= status.required_keys,
            ),
            (
                "REQUIRED TOPICS",
                f"{status.completed_topics} / {status.required_topics}",
                not status.missing_topic_ids,
            ),
        )
        if status.required_boss_id and show_boss_requirement:
            boss = get_enemy(status.required_boss_id) or {}
            rows += ((
                boss.get("name", "CORE BOSS").upper(),
                "DEFEATED" if status.boss_defeated else "NOT DEFEATED",
                status.boss_defeated,
            ),)
        for index, (label, value, complete) in enumerate(rows):
            rect = pygame.Rect(row_left, panel.top + 105 + index * 54, row_width, 44)
            pygame.draw.rect(screen, UI_COLORS["stone_deep"], rect, border_radius=6)
            pygame.draw.rect(
                screen,
                (82, 184, 118) if complete else UI_COLORS["crimson"],
                rect,
                2,
                border_radius=6,
            )
            screen.blit(heading.render(label, True, UI_COLORS["text"]),
                        (rect.left + 14, rect.top + 10))
            value_surface = heading.render(
                value, True, (126, 230, 154) if complete else (255, 128, 128)
            )
            screen.blit(value_surface, (rect.right - value_surface.get_width() - 14,
                                        rect.top + 10))

        list_y = panel.top + 285
        if status.unlocked:
            lines = (
                "All 10 keys are accounted for.",
                "Every required coding topic is complete.",
                "The Corrupted Core boss has been defeated.",
                "You may now leave the island. Your completion will be saved.",
            )
            for index, line in enumerate(lines):
                rendered = text_font.render(line, True, UI_COLORS["text"])
                screen.blit(rendered, rendered.get_rect(
                    center=(panel.centerx, list_y + index * 34)
                ))
        else:
            instruction_text = (
                "Finish every requirement before this exit can open."
                if show_boss_requirement else
                "Collect every key and finish every lesson to enter the Core."
            )
            instruction = text_font.render(
                instruction_text,
                True,
                UI_COLORS["text"],
            )
            screen.blit(instruction, instruction.get_rect(
                center=(panel.centerx, list_y)
            ))
            if status.missing_topic_titles:
                missing_heading = heading.render(
                    "LESSONS STILL REQUIRED", True, UI_COLORS["gold"]
                )
                screen.blit(missing_heading, missing_heading.get_rect(
                    center=(panel.centerx, list_y + 44)
                ))
                for index, topic_title in enumerate(status.missing_topic_titles):
                    column = index % 2
                    row = index // 2
                    line = text_font.render(f"- {topic_title}", True, UI_COLORS["text"])
                    x = panel.left + 74 + column * (panel.width // 2 - 36)
                    y = list_y + 80 + row * 29
                    screen.blit(line, (x, y))

        draw_button(
            screen, primary, primary_label, button_font,
            hovered=primary.collidepoint(mouse),
            tier=TIER_PRIMARY if status.unlocked else TIER_TERTIARY,
        )
        draw_button(
            screen, secondary, "STAY ON ISLAND", button_font,
            hovered=secondary.collidepoint(mouse), tier=TIER_TERTIARY,
        )
        hint = small.render(
            "E / ENTER = confirm    ESC = stay",
            True,
            UI_COLORS["text_dim"],
        )
        screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom - 15)))
        pygame.display.flip()
        clock.tick(60)
