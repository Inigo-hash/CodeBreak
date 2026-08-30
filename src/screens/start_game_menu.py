import sys

import math
import time

import pygame

from src.screens.game import game_screen
from src.screens.tutorial import tutorial_screen
from src.systems import save_manager
from src.systems.audio import apply_music_volume, handle_music_shortcut, music_shortcut_label
from src.ui.theme import TIER_PRIMARY, TIER_SECONDARY, TIER_TERTIARY


SG_ICONS = ["play", "chest", "quit"]
SG_LABELS = ["START NEW GAME", "CONTINUE GAME", "RETURN TO MAIN MENU"]
SG_SEEDS = [55, 66, 77]
SG_TIERS = [TIER_PRIMARY, TIER_SECONDARY, TIER_TERTIARY]

PASSWORD_MAX_ATTEMPTS = 3
PASSWORD_LOCKOUT_SECONDS = 30
_password_failures = {}
_password_locked_until = {}


def render_start_menu_buttons(surface, rects, t=0.0):
    from src.screens.main_menu import _draw_stone_button
    for rect, label, icon, seed, tier in zip(
        rects, SG_LABELS, SG_ICONS, SG_SEEDS, SG_TIERS
    ):
        _draw_stone_button(surface, rect, label, icon, False, seed, t, tier)


def start_game_menu(screen, clean_backdrop=None):
    from src.screens.main_menu import (
        STONE_DARK, STONE_MID, STONE_LIGHT, METAL_FRAME, BLUE_GLOW, WHITE,
        _button_font, _small, _draw_stone_button, _update_icon_anims,
        compute_menu_layout, paint_menu_backdrop,
    )

    width, height = screen.get_size()
    # Kept as a still frame for the crumble transition's debris pass, but no
    # longer what this menu paints each frame: blitting a snapshot is what
    # used to stop the dungeon's lights dead the moment this screen opened.
    background = clean_backdrop.copy() if clean_backdrop is not None else screen.copy()
    rects, *_ = compute_menu_layout(width, height, len(SG_LABELS))
    icons, labels, seeds, tiers = SG_ICONS, SG_LABELS, SG_SEEDS, SG_TIERS

    show_slot_panel = None
    confirm_slot = None
    password_action = None
    password_stage = "enter"
    password_slot = None
    password_text = ""
    first_password = ""
    password_error = ""

    panel_rect = pygame.Rect(
        0, 0, min(720, width - 60), min(620, height - 50)
    )
    panel_rect.center = (width // 2, height // 2)
    slot_rects = [
        pygame.Rect(panel_rect.left + 40, panel_rect.top + 122 + i * 136,
                    panel_rect.width - 80, 124)
        for i in range(save_manager.NUM_SLOTS)
    ]
    back_rect = pygame.Rect(panel_rect.centerx - 80, panel_rect.bottom - 56, 160, 38)
    confirm_rect = pygame.Rect(width // 2 - 240, height // 2 - 100, 480, 200)
    confirm_yes = pygame.Rect(confirm_rect.centerx - 160, confirm_rect.bottom - 58, 140, 42)
    confirm_no = pygame.Rect(confirm_rect.centerx + 20, confirm_rect.bottom - 58, 140, 42)
    password_rect = pygame.Rect(width // 2 - 290, height // 2 - 180, 580, 360)
    password_input = pygame.Rect(password_rect.left + 48, password_rect.top + 145,
                                 password_rect.width - 96, 54)
    password_ok = pygame.Rect(password_rect.centerx - 170, password_rect.bottom - 70, 150, 44)
    password_cancel = pygame.Rect(password_rect.centerx + 20, password_rect.bottom - 70, 150, 44)

    def _draw_slot_panel(surf, mode):
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        surf.blit(overlay, (0, 0))
        pygame.draw.rect(surf, (36, 38, 48), panel_rect, border_radius=8)
        pygame.draw.rect(surf, METAL_FRAME, panel_rect, 4, border_radius=8)
        pygame.draw.rect(
            surf, (108, 76, 42), panel_rect.inflate(-14, -14), 2,
            border_radius=7,
        )
        heading = "CHOOSE A SLOT FOR A NEW GAME" if mode == "new" else "CHOOSE YOUR ADVENTURE"
        title = _button_font.render(heading, True, WHITE)
        surf.blit(title, title.get_rect(
            center=(panel_rect.centerx, panel_rect.top + 45)
        ))
        pygame.draw.line(
            surf, (205, 164, 88),
            (panel_rect.left + 52, panel_rect.top + 79),
            (panel_rect.right - 52, panel_rect.top + 79), 2,
        )
        mouse = pygame.mouse.get_pos()
        for i, rect in enumerate(slot_rects):
            slot_num = i + 1
            filled = save_manager.slot_exists(slot_num)
            clickable = filled or mode == "new"
            shadow_rect = rect.move(0, 4)
            pygame.draw.rect(
                surf, (12, 14, 20), shadow_rect, border_radius=7
            )
            pygame.draw.rect(
                surf, STONE_MID if clickable else STONE_DARK,
                rect, border_radius=7,
            )
            if rect.collidepoint(mouse) and clickable:
                hi = pygame.Surface(rect.size, pygame.SRCALPHA)
                hi.fill((*BLUE_GLOW[:3], 35))
                surf.blit(hi, rect.topleft)
            pygame.draw.rect(
                surf, STONE_LIGHT if clickable else (60, 60, 65),
                rect, 2, border_radius=7,
            )
            pygame.draw.rect(
                surf, (117, 79, 39),
                (rect.left + 5, rect.top + 7, 5, rect.height - 14),
                border_radius=2,
            )
            for rivet_y in (rect.top + 12, rect.bottom - 12):
                pygame.draw.circle(
                    surf, (193, 151, 77),
                    (rect.left + 7, rivet_y), 2,
                )
            name = _button_font.render(f"SLOT {slot_num}", True, WHITE if clickable else (110, 110, 115))
            content_left = rect.left + 24
            name_y = rect.top + 8
            surf.blit(name, (content_left, name_y))
            summary = _small.render(save_manager.slot_summary(slot_num), True,
                                    (205, 205, 215) if filled else (125, 125, 132))
            summary_y = name_y + name.get_height() + 3
            surf.blit(summary, (content_left, summary_y))
            if filled:
                protected = save_manager.is_protected(
                    save_manager.load_slot(slot_num)
                )
                badge_text = "PROTECTED" if protected else "SET PASSWORD"
                lock = _small.render(
                    badge_text, True,
                    (140, 220, 255) if protected else (215, 180, 105),
                )
                badge = lock.get_rect()
                badge.inflate_ip(18, 10)
                badge.topright = (rect.right - 14, rect.top + 12)
                pygame.draw.rect(
                    surf, (20, 34, 46) if protected else (48, 39, 24),
                    badge, border_radius=4,
                )
                pygame.draw.rect(
                    surf, BLUE_GLOW if protected else (154, 112, 52),
                    badge, 1, border_radius=4,
                )
                surf.blit(lock, lock.get_rect(center=badge.center))
                progress = save_manager.slot_progress(slot_num)
                progress_label = _small.render(
                    f"PROGRESS {progress}%", True, (150, 215, 255)
                )
                progress_label_y = summary_y + summary.get_height() + 5
                progress_bar = pygame.Rect(
                    content_left,
                    progress_label_y + progress_label.get_height() + 1,
                    rect.right - content_left - 18, 10,
                )
                pygame.draw.rect(
                    surf, (18, 20, 28), progress_bar, border_radius=3
                )
                progress_fill = progress_bar.copy()
                progress_fill.width = round(
                    progress_bar.width * progress / 100
                )
                if progress_fill.width:
                    pygame.draw.rect(
                        surf, BLUE_GLOW, progress_fill, border_radius=3
                    )
                pygame.draw.rect(
                    surf, (105, 113, 132), progress_bar, 1,
                    border_radius=3,
                )
                surf.blit(progress_label, (
                    content_left,
                    progress_label_y,
                ))
        pygame.draw.rect(surf, STONE_MID, back_rect, border_radius=4)
        pygame.draw.rect(surf, STONE_LIGHT, back_rect, 2, border_radius=4)
        label = _button_font.render("BACK", True, WHITE)
        surf.blit(label, label.get_rect(center=back_rect.center))

    def _draw_confirm(surf, slot_num):
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        surf.blit(overlay, (0, 0))
        pygame.draw.rect(surf, (36, 38, 48), confirm_rect, border_radius=8)
        pygame.draw.rect(surf, (200, 90, 90), confirm_rect, 3, border_radius=8)
        line = _button_font.render("REPLACE THIS ADVENTURE?", True, WHITE)
        surf.blit(line, line.get_rect(center=(confirm_rect.centerx, confirm_rect.top + 42)))
        note = _small.render(f"Slot {slot_num} progress will be overwritten.", True, (210, 210, 220))
        surf.blit(note, note.get_rect(center=(confirm_rect.centerx, confirm_rect.top + 82)))
        for rect, label, color in ((confirm_yes, "YES", (70, 140, 70)),
                                   (confirm_no, "NO", (140, 70, 70))):
            pygame.draw.rect(surf, color, rect, border_radius=4)
            text = _button_font.render(label, True, WHITE)
            surf.blit(text, text.get_rect(center=rect.center))

    def _password_heading():
        if password_action in ("load_unlock", "overwrite_unlock"):
            return "ENTER SAVE PASSWORD"
        if password_stage == "confirm":
            return "CONFIRM PASSWORD"
        return "CREATE SAVE PASSWORD"

    def _lockout_remaining(slot_num):
        deadline = _password_locked_until.get(slot_num, 0.0)
        return max(0, math.ceil(deadline - time.monotonic()))

    def _draw_password(surf):
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 195))
        surf.blit(overlay, (0, 0))
        pygame.draw.rect(surf, (30, 34, 46), password_rect, border_radius=10)
        pygame.draw.rect(surf, BLUE_GLOW, password_rect, 3, border_radius=10)
        heading = _button_font.render(_password_heading(), True, WHITE)
        surf.blit(heading, heading.get_rect(center=(password_rect.centerx, password_rect.top + 44)))
        if password_action in ("load_unlock", "overwrite_unlock"):
            instruction = "This save is protected. Type its password to continue."
        elif password_stage == "confirm":
            instruction = "Type the same password again."
        else:
            instruction = f"Use at least {save_manager.PASSWORD_MIN_LENGTH} characters."
        info = _small.render(instruction, True, (195, 200, 215))
        surf.blit(info, info.get_rect(center=(password_rect.centerx, password_rect.top + 92)))
        pygame.draw.rect(surf, STONE_DARK, password_input, border_radius=5)
        pygame.draw.rect(surf, BLUE_GLOW, password_input, 2, border_radius=5)
        masked = "*" * len(password_text)
        field = _button_font.render(masked or "TYPE PASSWORD", True,
                                    WHITE if masked else (105, 110, 125))
        field_pos = (password_input.left + 16,
                     password_input.centery - field.get_height() // 2)
        surf.blit(field, field_pos)
        # The modal owns keyboard input as soon as it opens. A blinking caret
        # makes that focus visible even before the first character is typed.
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            caret_x = field_pos[0] + (field.get_width() if masked else 0)
            caret_top = password_input.centery - _button_font.get_height() // 2
            pygame.draw.line(
                surf, WHITE,
                (caret_x, caret_top),
                (caret_x, caret_top + _button_font.get_height()),
                3,
            )
        remaining = _lockout_remaining(password_slot)
        warning = (
            f"Too many failed attempts. Try again in {remaining} seconds."
            if remaining else
            password_error
            or "Passwords cannot be recovered. Keep yours somewhere safe."
        )
        warn_color = (
            (255, 125, 125)
            if password_error or remaining else (180, 180, 190)
        )
        warn = _small.render(warning, True, warn_color)
        surf.blit(warn, warn.get_rect(center=(password_rect.centerx, password_rect.top + 230)))
        for rect, label in ((password_ok, "CONTINUE"), (password_cancel, "CANCEL")):
            pygame.draw.rect(surf, STONE_MID, rect, border_radius=4)
            pygame.draw.rect(surf, STONE_LIGHT, rect, 2, border_radius=4)
            text = _button_font.render(label, True, WHITE)
            surf.blit(text, text.get_rect(center=rect.center))

    def _resume_menu_music():
        pygame.mixer.music.load("assets/audios/mainMenuBgm.mp3")
        apply_music_volume()
        pygame.mixer.music.play(-1)

    def _run_new(slot_num, state):
        pygame.mixer.music.stop()
        tutorial_result = tutorial_screen(screen, show_loading=True)
        if tutorial_result != "completed":
            # Do not create an unfinished save or overwrite an existing one
            # when the player returns from the tutorial. This also prevents
            # Escape from falling through into gameplay.
            _resume_menu_music()
            return "tutorial_cancelled"
        save_manager.save_slot(slot_num, state)
        result = game_screen(screen, slot_num=slot_num, save_state=state)
        _resume_menu_music()
        return result

    def _run_loaded(slot_num, state):
        pygame.mixer.music.stop()
        result = game_screen(screen, slot_num=slot_num, save_state=state)
        _resume_menu_music()
        return result

    def _open_password(action, slot_num):
        nonlocal password_action, password_stage, password_slot
        nonlocal password_text, first_password, password_error
        password_action = action
        password_stage = "enter"
        password_slot = slot_num
        password_text = first_password = password_error = ""
        pygame.key.start_text_input()

    def _close_password():
        nonlocal password_action, password_text, first_password, password_error
        password_action = None
        password_text = first_password = password_error = ""
        pygame.key.stop_text_input()

    def _submit_password():
        nonlocal password_stage, password_text, first_password, password_error
        state = save_manager.load_slot(password_slot)
        if password_action in ("load_unlock", "overwrite_unlock"):
            remaining = _lockout_remaining(password_slot)
            if remaining:
                password_error = (
                    f"Too many failed attempts. Try again in {remaining} seconds."
                )
                password_text = ""
                return None
            if not save_manager.verify_password(state, password_text):
                failures = _password_failures.get(password_slot, 0) + 1
                if failures >= PASSWORD_MAX_ATTEMPTS:
                    _password_failures[password_slot] = 0
                    _password_locked_until[password_slot] = (
                        time.monotonic() + PASSWORD_LOCKOUT_SECONDS
                    )
                    password_error = (
                        "Too many failed attempts. Access is temporarily locked."
                    )
                else:
                    _password_failures[password_slot] = failures
                    attempts_left = PASSWORD_MAX_ATTEMPTS - failures
                    password_error = (
                        f"Incorrect password. {attempts_left} "
                        f"attempt{'s' if attempts_left != 1 else ''} remaining."
                    )
                password_text = ""
                return None
            _password_failures.pop(password_slot, None)
            _password_locked_until.pop(password_slot, None)
            security = state.get("_security")
            action = password_action
            slot = password_slot
            _close_password()
            if action == "load_unlock":
                return _run_loaded(slot, state)
            fresh = save_manager.new_game_state()
            fresh["_security"] = security
            return _run_new(slot, fresh)

        if password_stage == "enter":
            if len(password_text) < save_manager.PASSWORD_MIN_LENGTH:
                password_error = f"Use at least {save_manager.PASSWORD_MIN_LENGTH} characters."
                return None
            first_password = password_text
            password_text = ""
            password_error = ""
            password_stage = "confirm"
            return None
        if password_text != first_password:
            password_error = "Passwords do not match. Try the confirmation again."
            password_text = ""
            return None
        action = password_action
        slot = password_slot
        password = first_password
        if action == "new_create":
            state = save_manager.protect_state(save_manager.new_game_state(), password)
            _close_password()
            return _run_new(slot, state)
        state = save_manager.protect_state(state, password)
        save_manager.save_slot(slot, state)
        _close_password()
        return _run_loaded(slot, state)

    def _transition_to_main_menu(t):
        from src.ui.transitions import crumble_transition
        from src.screens.main_menu import (
            MM_LABELS, compute_menu_layout, render_main_menu_buttons,
        )
        old_source = screen.copy()
        main_rects, *_ = compute_menu_layout(width, height, len(MM_LABELS))
        new_source = background.copy()
        render_main_menu_buttons(new_source, main_rects, t)
        crumble_transition(screen, background, old_source, rects,
                            new_source, main_rects, seed=101,
                            burst_duration=0.52, assemble_duration=0.56,
                            paint_backdrop=paint_menu_backdrop)

    clock = pygame.time.Clock()
    while True:
        dt = clock.tick(60) / 1000.0
        t = pygame.time.get_ticks() / 1000.0
        mouse = pygame.mouse.get_pos()
        hovers = [rect.collidepoint(mouse) for rect in rects]
        _update_icon_anims(dict(zip(icons, hovers)), dt)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if handle_music_shortcut(event):
                continue
            if password_action is not None:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        _close_password()
                    elif (_lockout_remaining(password_slot) == 0
                          and event.key == pygame.K_BACKSPACE):
                        password_text = password_text[:-1]
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if _submit_password() == "main_menu":
                            return
                    elif (_lockout_remaining(password_slot) == 0
                          and event.unicode
                          and event.unicode.isprintable()
                          and len(password_text) < 32):
                        password_text += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if password_cancel.collidepoint(event.pos):
                        _close_password()
                    elif password_ok.collidepoint(event.pos):
                        if _submit_password() == "main_menu":
                            return
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if confirm_slot is not None:
                    confirm_slot = None
                elif show_slot_panel is not None:
                    show_slot_panel = None
                else:
                    _transition_to_main_menu(t)
                    return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if confirm_slot is not None:
                    if confirm_yes.collidepoint(event.pos):
                        existing = save_manager.load_slot(confirm_slot)
                        if save_manager.is_protected(existing):
                            _open_password("overwrite_unlock", confirm_slot)
                        else:
                            _open_password("new_create", confirm_slot)
                        confirm_slot = None
                    elif confirm_no.collidepoint(event.pos):
                        confirm_slot = None
                    continue
                if show_slot_panel is not None:
                    if back_rect.collidepoint(event.pos):
                        show_slot_panel = None
                        continue
                    for i, rect in enumerate(slot_rects):
                        if not rect.collidepoint(event.pos):
                            continue
                        slot = i + 1
                        filled = save_manager.slot_exists(slot)
                        if show_slot_panel == "new":
                            if filled:
                                confirm_slot = slot
                            else:
                                _open_password("new_create", slot)
                        elif show_slot_panel == "load" and filled:
                            state = save_manager.load_slot(slot)
                            _open_password("load_unlock" if save_manager.is_protected(state)
                                           else "legacy_create", slot)
                    continue
                if rects[0].collidepoint(event.pos):
                    show_slot_panel = "new"
                elif rects[1].collidepoint(event.pos):
                    show_slot_panel = "load"
                elif rects[2].collidepoint(event.pos):
                    _transition_to_main_menu(t)
                    return

        paint_menu_backdrop(screen, t)
        for rect, label, icon, hovered, seed, tier in zip(
            rects, labels, icons, hovers, seeds, tiers
        ):
            _draw_stone_button(screen, rect, label, icon, hovered, seed, t, tier)
        hint = _small.render(music_shortcut_label(), True, (160, 165, 180))
        screen.blit(hint, (16, height - hint.get_height() - 12))
        if show_slot_panel is not None:
            _draw_slot_panel(screen, show_slot_panel)
        if confirm_slot is not None:
            _draw_confirm(screen, confirm_slot)
        if password_action is not None:
            _draw_password(screen)
        pygame.display.flip()
