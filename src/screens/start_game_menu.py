import sys
import pygame
from src.settings_state import settings_state as _settings_state
from src.systems import save_manager


def start_game_menu(screen):
    from src.screens.main_menu import (
        STONE_DARK, STONE_MID, STONE_LIGHT, METAL_FRAME, BLUE_GLOW, WHITE,
        _button_font, _small, _draw_stone_button, _update_icon_anims,
    )
    from src.screens.game import game_screen

    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    background = screen.copy()   # snapshot the main menu behind this screen

    bw, bh = 380, 64
    by0 = SCREEN_HEIGHT // 2 - 100
    gap = 16
    center_x = SCREEN_WIDTH // 2 - bw // 2

    rects = [
        pygame.Rect(center_x, by0 + 0 * (bh + gap), bw, bh),  # START NEW GAME
        pygame.Rect(center_x, by0 + 1 * (bh + gap), bw, bh),  # LOAD SAVE DATA
        pygame.Rect(center_x, by0 + 2 * (bh + gap), bw, bh),  # RETURN TO MAIN MENU
    ]
    icons = ["play", "chest", "quit"]
    labels = ["START NEW GAME", "LOAD SAVE DATA", "RETURN TO MAIN MENU"]
    seeds = [55, 66, 77]

    show_slot_panel = None   # None | "new" | "load"
    confirm_slot = None      # slot number pending overwrite confirmation

    panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 260, SCREEN_HEIGHT // 2 - 220, 520, 440)
    slot_rects = [
        pygame.Rect(panel_rect.left + 40, panel_rect.top + 90 + i * 100, panel_rect.width - 80, 80)
        for i in range(save_manager.NUM_SLOTS)
    ]
    back_rect = pygame.Rect(panel_rect.centerx - 70, panel_rect.bottom - 56, 140, 36)

    confirm_rect = pygame.Rect(SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 - 90, 440, 180)
    confirm_yes = pygame.Rect(confirm_rect.centerx - 150, confirm_rect.bottom - 56, 130, 40)
    confirm_no = pygame.Rect(confirm_rect.centerx + 20, confirm_rect.bottom - 56, 130, 40)

    def _draw_slot_panel(surf, mode):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))

        pygame.draw.rect(surf, (36, 38, 48), panel_rect, border_radius=6)
        pygame.draw.rect(surf, METAL_FRAME, panel_rect, 4, border_radius=6)

        title_text = "SELECT SLOT TO START" if mode == "new" else "SELECT SLOT TO LOAD"
        title = _button_font.render(title_text, True, WHITE)
        surf.blit(title, (panel_rect.centerx - title.get_width() // 2, panel_rect.top + 24))

        mouse_pos = pygame.mouse.get_pos()
        for i, r in enumerate(slot_rects):
            slot_num = i + 1
            filled = save_manager.slot_exists(slot_num)
            hovered = r.collidepoint(mouse_pos)
            clickable = filled or mode == "new"

            pygame.draw.rect(surf, STONE_MID if clickable else STONE_DARK, r, border_radius=4)
            if hovered and clickable:
                hi = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
                hi.fill((*BLUE_GLOW[:3], 35))
                surf.blit(hi, r.topleft)
            pygame.draw.rect(surf, STONE_LIGHT if clickable else (60, 60, 65), r, 2, border_radius=4)

            name = _button_font.render(f"SLOT {slot_num}", True, WHITE if clickable else (110, 110, 115))
            surf.blit(name, (r.left + 16, r.top + 12))

            summary_color = (200, 200, 210) if filled else (120, 120, 125)
            sm = _small.render(save_manager.slot_summary(slot_num), True, summary_color)
            surf.blit(sm, (r.left + 16, r.top + 44))

        pygame.draw.rect(surf, STONE_MID, back_rect, border_radius=4)
        pygame.draw.rect(surf, STONE_LIGHT, back_rect, 2, border_radius=4)
        bt = _button_font.render("BACK", True, WHITE)
        surf.blit(bt, (back_rect.centerx - bt.get_width() // 2, back_rect.centery - bt.get_height() // 2))

    def _draw_confirm(surf, slot_num):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surf.blit(overlay, (0, 0))

        pygame.draw.rect(surf, (36, 38, 48), confirm_rect, border_radius=6)
        pygame.draw.rect(surf, (200, 90, 90), confirm_rect, 3, border_radius=6)

        msg1 = _button_font.render("OVERWRITE THIS SAVE?", True, WHITE)
        surf.blit(msg1, (confirm_rect.centerx - msg1.get_width() // 2, confirm_rect.top + 24))
        msg2 = _small.render(f"Slot {slot_num} already has progress saved.", True, (200, 200, 210))
        surf.blit(msg2, (confirm_rect.centerx - msg2.get_width() // 2, confirm_rect.top + 64))

        pygame.draw.rect(surf, (70, 140, 70), confirm_yes, border_radius=4)
        yes_t = _button_font.render("YES", True, WHITE)
        surf.blit(yes_t, (confirm_yes.centerx - yes_t.get_width() // 2, confirm_yes.centery - yes_t.get_height() // 2))

        pygame.draw.rect(surf, (140, 70, 70), confirm_no, border_radius=4)
        no_t = _button_font.render("NO", True, WHITE)
        surf.blit(no_t, (confirm_no.centerx - no_t.get_width() // 2, confirm_no.centery - no_t.get_height() // 2))

    def _resume_menu_music():
        pygame.mixer.music.load("assets/audios/mainMenuBgm.mp3")
        pygame.mixer.music.set_volume(_settings_state["music_vol"])
        pygame.mixer.music.play(-1)

    def _start_game_with_slot(slot_num):
        state = save_manager.new_game_state()
        save_manager.save_slot(slot_num, state)
        pygame.mixer.music.stop()
        result = game_screen(screen)
        _resume_menu_music()
        return result

    def _load_game_from_slot(slot_num):
        state = save_manager.load_slot(slot_num)
        pygame.mixer.music.stop()
        result = game_screen(screen)
        _resume_menu_music()
        return result

    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        t = pygame.time.get_ticks() / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        hovers = [r.collidepoint(mouse_pos) for r in rects]
        _update_icon_anims(dict(zip(icons, hovers)), dt)

        # ---------------- EVENTS ----------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if confirm_slot is not None:
                    confirm_slot = None
                elif show_slot_panel is not None:
                    show_slot_panel = None
                else:
                    return

            if event.type == pygame.MOUSEBUTTONDOWN:
                if confirm_slot is not None:
                    if confirm_yes.collidepoint(event.pos):
                        result = _start_game_with_slot(confirm_slot)
                        confirm_slot = None
                        show_slot_panel = None
                        if result == "main_menu":
                            return
                    elif confirm_no.collidepoint(event.pos):
                        confirm_slot = None
                    continue

                if show_slot_panel is not None:
                    if back_rect.collidepoint(event.pos):
                        show_slot_panel = None
                        continue
                    for i, r in enumerate(slot_rects):
                        if r.collidepoint(event.pos):
                            slot_num = i + 1
                            filled = save_manager.slot_exists(slot_num)
                            if show_slot_panel == "new":
                                if filled:
                                    confirm_slot = slot_num
                                else:
                                    result = _start_game_with_slot(slot_num)
                                    show_slot_panel = None
                                    if result == "main_menu":
                                        return
                            elif show_slot_panel == "load" and filled:
                                result = _load_game_from_slot(slot_num)
                                show_slot_panel = None
                                if result == "main_menu":
                                    return
                    continue

                if rects[0].collidepoint(event.pos):
                    show_slot_panel = "new"
                if rects[1].collidepoint(event.pos):
                    show_slot_panel = "load"
                if rects[2].collidepoint(event.pos):
                    return

        # ---------------- DRAW ----------------
        screen.blit(background, (0, 0))
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 170))
        screen.blit(dim, (0, 0))

        title = _button_font.render("START GAME", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, by0 - 100))

        for rect, label, icon, h, seed in zip(rects, labels, icons, hovers, seeds):
            _draw_stone_button(screen, rect, label, icon, h, seed, t)

        if show_slot_panel is not None:
            _draw_slot_panel(screen, show_slot_panel)
        if confirm_slot is not None:
            _draw_confirm(screen, confirm_slot)

        pygame.display.flip()