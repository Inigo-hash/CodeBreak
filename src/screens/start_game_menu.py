import sys
import pygame
from src.settings_state import settings_state as _settings_state
from src.systems import save_manager
from src.screens.game import game_screen
from src.screens.tutorial import tutorial_screen

SG_ICONS = ["play", "chest", "quit"]
SG_LABELS = ["START NEW GAME", "LOAD SAVE DATA", "RETURN TO MAIN MENU"]
SG_SEEDS = [55, 66, 77]


def render_start_menu_buttons(surface, rects, t=0.0):
    """Draw the start-game menu's buttons onto an OFFSCREEN surface —
    used by main_menu.py to build the crumble-transition target."""
    from src.screens.main_menu import _draw_stone_button
    for rect, label, icon, seed in zip(rects, SG_LABELS, SG_ICONS, SG_SEEDS):
        _draw_stone_button(surface, rect, label, icon, False, seed, t)


def start_game_menu(screen, clean_backdrop=None):
    from src.screens.main_menu import (
        STONE_DARK, STONE_MID, STONE_LIGHT, METAL_FRAME, BLUE_GLOW, WHITE,
        _button_font, _small, _draw_stone_button, _update_icon_anims,
        compute_menu_layout,
    )
    

    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    # The caller already owns a background+logo surface with no buttons.
    # Re-capturing `screen` here would bake the assembled Start Game buttons
    # into the backdrop and make them show beneath the return transition.
    background = clean_backdrop.copy() if clean_backdrop is not None else screen.copy()

    rects, bw, bh, gap, center_x, by0 = compute_menu_layout(SCREEN_WIDTH, SCREEN_HEIGHT, 3)
    icons, labels, seeds = SG_ICONS, SG_LABELS, SG_SEEDS

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
        tutorial_screen(screen)
        result = game_screen(screen, slot_num=slot_num, save_state=state)
        _resume_menu_music()
        return result

    def _load_game_from_slot(slot_num):
        state = save_manager.load_slot(slot_num)
        pygame.mixer.music.stop()
        result = game_screen(screen, slot_num=slot_num, save_state=state)
        _resume_menu_music()
        return result
    
    def _transition_to_main_menu():
        from src.ui.transitions import crumble_transition
        from src.screens.main_menu import compute_menu_layout, render_main_menu_buttons

        old_source = screen.copy()  # current frame, start-game buttons already on it

        main_menu_rects, *_ = compute_menu_layout(SCREEN_WIDTH, SCREEN_HEIGHT, 4)
        new_source = background.copy()  # clean main-menu backdrop, no buttons
        render_main_menu_buttons(new_source, main_menu_rects, t)

        crumble_transition(screen, background, old_source, rects,
                            new_source, main_menu_rects, seed=101,
                            burst_duration=0.52, assemble_duration=0.56)

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
                    _transition_to_main_menu()
                    return

            # Left button only - see the note in main_menu.py: the wheel
            # and the right button raise this event as well.
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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
                    _transition_to_main_menu()
                    return

        # ---------------- DRAW ----------------
        screen.blit(background, (0, 0))

        for rect, label, icon, h, seed in zip(rects, labels, icons, hovers, seeds):
            _draw_stone_button(screen, rect, label, icon, h, seed, t)

        if show_slot_panel is not None:
            _draw_slot_panel(screen, show_slot_panel)
        if confirm_slot is not None:
            _draw_confirm(screen, confirm_slot)

        pygame.display.flip()
