"""Blocking, beginner-readable boss introduction and outcome choices."""

import sys

import pygame
from src.ui.text_layout import fit_text, draw_text_block

from src.data.enemies import get_enemy
from src.systems.audio import handle_music_shortcut
from src.ui.theme import (
    TIER_PRIMARY, TIER_SECONDARY, TIER_SUCCESS, UI_COLORS, body_font, draw_button,
    draw_panel, title_font,
)


def open_boss_intro(screen, boss_id, background=None):
    """Announce the dedicated boss encounter; return ``fight`` or ``retreat``."""

    boss = get_enemy(boss_id) or {"name": "Unknown Warden"}
    return _boss_modal(
        screen,
        title="BOSS ENCOUNTER",
        subtitle="AKTAN'S THRONE" if boss_id == "zombie_aktan" else "THE CORRUPTED CORE",
        lines=(
            f"{boss['name']} guards the stage's final path.",
            "E attacks. Shift dodges. Watch the boss health bar.",
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
            title="BOSS DEFEATED",
            subtitle="BOSS VICTORY",
            lines=(
                "The boss requirement is complete and has been saved.",
                "The stage exit still checks all required keys and lessons.",
                "Continue exploring or head toward the stage exit.",
            ),
            primary=("CONTINUE TO EXIT", "continue"),
            secondary=("RETURN TO EXPLORING", "continue"),
            background=background,
        )
    return _boss_modal(
        screen,
        title="THE WARDEN PREVAILED",
        subtitle="BOSS DEFEAT",
        lines=(
            "Your stage progress is safe. The boss has reset.",
            "Press P while exploring if you want to enter combat practice.",
            "Retry now, or retreat and prepare first.",
        ),
        primary=("RETRY BOSS", "retry"),
        secondary=("RETREAT", "retreat"),
        background=background,
        danger=True,
    )


def open_boss_retreat_warning(screen, background=None):
    """Confirm leaving an unfinished boss encounter."""
    return _boss_modal(
        screen,
        title="LEAVE THE BOSS ARENA?",
        subtitle="ACTIVE BOSS ENCOUNTER",
        lines=(
            "Crossing this boundary abandons the current fight.",
            "The boss and its reinforcements will reset.",
            "Return to the battle now, or retreat and prepare.",
        ),
        primary=("RETURN TO BATTLE", "stay"),
        secondary=("RETREAT", "leave"),
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
    primary_rect.x, secondary_rect.x = secondary_rect.x, primary_rect.x

    focus = 0
    keyboard_focus = False
    while True:
        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if handle_music_shortcut(event):
                continue
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_TAB, pygame.K_LEFT, pygame.K_RIGHT):
                    focus = 1 - focus
                    keyboard_focus = True
                    continue
                if event.key in (
                    pygame.K_e, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE
                ):
                    return (primary if focus == 0 else secondary)[1]
                if event.key == pygame.K_ESCAPE:
                    return secondary[1]
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                keyboard_focus = False
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
        rendered_title = fit_text(title_font_obj, title, accent, (panel.width - 48, 48))
        screen.blit(rendered_title, rendered_title.get_rect(
            center=(panel.centerx, panel.top + 62)
        ))
        rendered_subtitle = subtitle_font.render(
            subtitle, True, UI_COLORS["gold"]
        )
        screen.blit(rendered_subtitle, rendered_subtitle.get_rect(
            center=(panel.centerx, panel.top + 99)
        ))

        draw_text_block(screen, "\n\n".join(lines), line_font, UI_COLORS["text"],
                        pygame.Rect(panel.left + 28, panel.top + 135,
                                    panel.width - 56, primary_rect.top - panel.top - 155),
                        center=True)

        draw_button(
            screen, primary_rect, primary[0], button_font,
            hovered=primary_rect.collidepoint(mouse),
            tier=TIER_SUCCESS if title == "BOSS DEFEATED" else TIER_PRIMARY,
            focused=keyboard_focus and focus == 0,
        )
        draw_button(
            screen, secondary_rect, secondary[0], button_font,
            hovered=secondary_rect.collidepoint(mouse), tier=TIER_SECONDARY,
            focused=keyboard_focus and focus == 1,
        )
        hint = hint_font.render(
            "TAB / ARROWS = choose    ENTER = confirm    ESC = back",
            True,
            UI_COLORS["text_dim"],
        )
        screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom - 16)))
        pygame.display.flip()
        clock.tick(60)
