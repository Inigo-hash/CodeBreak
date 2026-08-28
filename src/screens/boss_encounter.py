"""Blocking, beginner-readable boss introduction and outcome choices."""

import sys

import pygame

from src.data.enemies import get_enemy
from src.systems.audio import handle_music_shortcut
from src.ui.theme import (
    TIER_PRIMARY, TIER_SECONDARY, UI_COLORS, body_font, draw_button,
    draw_panel, title_font,
)


def open_boss_intro(screen, boss_id, background=None):
    """Announce the dedicated boss encounter; return ``fight`` or ``retreat``."""

    boss = get_enemy(boss_id) or {"name": "Unknown Warden"}
    return _boss_modal(
        screen,
        title="BOSS ENCOUNTER",
        subtitle="THE CORRUPTED CORE",
        lines=(
            f"{boss['name']} blocks the path to the castle exit.",
            "E attacks. Left Shift dodges. Watch the boss health bar.",
            "You may retreat now and return after more practice.",
        ),
        primary=("BEGIN FIGHT", "fight"),
        secondary=("RETREAT", "retreat"),
        background=background,
        danger=True,
    )


def open_boss_result(screen, victory, background=None):
    """Return the explicit post-boss branch selected by the player."""

    if victory:
        return _boss_modal(
            screen,
            title="CORE WARDEN DEFEATED",
            subtitle="BOSS VICTORY",
            lines=(
                "The boss requirement is complete and has been saved.",
                "The castle exit still checks your 10 keys and all lessons.",
                "Continue now, or revisit the safe combat practice room.",
            ),
            primary=("CONTINUE TO EXIT", "continue"),
            secondary=("PRACTICE COMBAT", "practice"),
            background=background,
        )
    return _boss_modal(
        screen,
        title="THE WARDEN PREVAILED",
        subtitle="BOSS DEFEAT",
        lines=(
            "Your stage progress is safe. The boss has reset.",
            "Practice is safe and does not consume campaign hearts.",
            "Choose practice for a guided refresher, or retry immediately.",
        ),
        primary=("PRACTICE FIRST", "practice"),
        secondary=("RETRY BOSS", "retry"),
        background=background,
        danger=True,
    )


def _boss_modal(screen, title, subtitle, lines, primary, secondary,
                background=None, danger=False):
    clock = pygame.time.Clock()
    width, height = screen.get_size()
    backdrop = (screen if background is None else background).copy()
    panel = pygame.Rect(0, 0, min(820, width - 56), min(500, height - 56))
    panel.center = (width // 2, height // 2)

    title_font_obj = title_font(36)
    subtitle_font = title_font(18, bold=False)
    line_font = body_font(18)
    button_font = title_font(20)
    hint_font = body_font(13)

    button_width = min(300, panel.width // 2 - 34)
    primary_rect = pygame.Rect(
        panel.centerx - button_width - 9, panel.bottom - 82,
        button_width, 48,
    )
    secondary_rect = pygame.Rect(
        panel.centerx + 9, panel.bottom - 82,
        button_width, 48,
    )

    while True:
        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if handle_music_shortcut(event):
                continue
            if event.type == pygame.KEYDOWN:
                if event.key in (
                    pygame.K_e, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE
                ):
                    return primary[1]
                if event.key == pygame.K_ESCAPE:
                    return secondary[1]
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if primary_rect.collidepoint(event.pos):
                    return primary[1]
                if secondary_rect.collidepoint(event.pos):
                    return secondary[1]

        screen.blit(backdrop, (0, 0))
        shade = pygame.Surface((width, height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 195))
        screen.blit(shade, (0, 0))
        draw_panel(screen, panel, emphasized=not danger, radius=12)

        accent = UI_COLORS["crimson"] if danger else UI_COLORS["blue_bright"]
        rendered_title = title_font_obj.render(title, True, accent)
        screen.blit(rendered_title, rendered_title.get_rect(
            center=(panel.centerx, panel.top + 62)
        ))
        rendered_subtitle = subtitle_font.render(
            subtitle, True, UI_COLORS["gold"]
        )
        screen.blit(rendered_subtitle, rendered_subtitle.get_rect(
            center=(panel.centerx, panel.top + 99)
        ))

        for index, line in enumerate(lines):
            rendered = line_font.render(line, True, UI_COLORS["text"])
            screen.blit(rendered, rendered.get_rect(
                center=(panel.centerx, panel.top + 155 + index * 38)
            ))

        draw_button(
            screen, primary_rect, primary[0], button_font,
            hovered=primary_rect.collidepoint(mouse), tier=TIER_PRIMARY,
        )
        draw_button(
            screen, secondary_rect, secondary[0], button_font,
            hovered=secondary_rect.collidepoint(mouse), tier=TIER_SECONDARY,
        )
        hint = hint_font.render(
            "E / ENTER = first option    ESC = second option",
            True,
            UI_COLORS["text_dim"],
        )
        screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom - 16)))
        pygame.display.flip()
        clock.tick(60)
