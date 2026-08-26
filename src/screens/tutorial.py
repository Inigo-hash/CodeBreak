import pygame
import sys
from src.settings_state import revealed_characters
from src.entities.player import MainCharacter
from src.entities.enemy import Enemy
from src.systems.combat import PlayerCombat, attack_hitbox
from src.systems.audio import CombatAudio, apply_music_volume, handle_music_shortcut
from src.ui.code_editor import CodeEditor
from src.data.challenges import CHALLENGES
from src.screens.how_to_play import (
    draw_manual_columns,
    manual_layout,
    STONE_DARK,
    STONE_LIGHT,
)
from src.ui.theme import body_font, title_font


def tutorial_screen(screen, play_music=True):
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

    # --- Palette (stone/gold theme, matches main menu & game UI) ---
    STONE_MID = (42, 46, 58)
    METAL_FRAME = (90, 94, 110)
    YELLOW_GLOW = (255, 220, 120)
    GREEN_OK = (80, 220, 120)
    WHITE = (255, 255, 255)
    DIM_TEXT = (180, 180, 190)
    BG_FLOOR = (34, 36, 44)

    # --- Fonts ---
    name_font = title_font(26)
    dialogue_font = body_font(28)
    hint_font = body_font(20)
    prompt_font = title_font(18, bold=False)
    manual_title_font = title_font(30)
    manual_header_font = title_font(20, bold=False)
    manual_key_font = body_font(17, bold=True)
    manual_line_font = body_font(17)
    manual_note_font = body_font(15)
    manual_btn_font = title_font(22)
    exit_title_font = title_font(26)

    # Rows of dialogue the textbox reserves room for. Every tutorial line
    # fits well inside this at the current width; the cap only exists so an
    # over-long line cannot grow the box off the bottom of the screen.
    MAX_DIALOGUE_LINES = 3
    PORTRAIT_SIDE = 190

    # --- Music: reuse the main menu theme for the tutorial ---
    if play_music:
        pygame.mixer.music.load("assets/audios/tutorial_background_music.mp3")
        apply_music_volume()
        pygame.mixer.music.play(-1)

    def _stop_tutorial_music():
        pygame.mixer.music.stop()

    # --- Mang Tahimik portrait (falls back to a drawn placeholder if the path is wrong) ---
    # NOTE: adjust this path to wherever his portrait actually lives in your assets folder
    portrait = None
    try:
        portrait = pygame.image.load("assets/images/characters/mang_tahimik/portrait.png").convert_alpha()
    except Exception:
        portrait = None

    # The textbox sizes itself from its fonts, so the portrait is scaled to
    # whatever square it ends up asking for rather than to a fixed size here.
    _portrait_cache = {}

    def _portrait_at(size):
        if size not in _portrait_cache:
            _portrait_cache[size] = pygame.transform.smoothscale(portrait, (size, size))
        return _portrait_cache[size]

    def draw_portrait(surf, rect):
        if portrait:
            surf.blit(_portrait_at(rect.width), rect.topleft)
            pygame.draw.rect(surf, METAL_FRAME, rect, 3, border_radius=6)
        else:
            pygame.draw.rect(surf, (60, 70, 60), rect, border_radius=6)
            pygame.draw.rect(surf, METAL_FRAME, rect, 3, border_radius=6)
            cx, cy = rect.center
            pygame.draw.circle(surf, (220, 230, 220), (cx, cy - 20), 34)
            pygame.draw.rect(surf, (220, 230, 220), (rect.left + 24, cy, rect.width - 48, 50), border_radius=10)
            pygame.draw.circle(surf, (30, 30, 38), (cx - 12, cy - 24), 4)
            pygame.draw.circle(surf, (30, 30, 38), (cx + 12, cy - 24), 4)

    # ------------------------------------------------------------------
    # Dialogue system: one consistent key. A beginner should not have to
    # remember three equivalent inputs while also learning the game.
    # ------------------------------------------------------------------
    class DialogueBox:
        """
        Mang Tahimik's textbox.

        Lines type themselves out one character at a time, at whatever
        pace the TEXT SPEED setting asks for - the setting used to be a
        label in the settings panel with nothing behind it, and this is
        what it now drives. On INSTANT the whole line is there on the
        first frame and the typing never happens at all.
        """

        def __init__(self, lines, on_finish=None):
            self.lines = lines
            self.index = 0
            self.on_finish = on_finish
            self.active = True
            self.started_at = pygame.time.get_ticks()
            # Set when the player asks to see the rest of the line now.
            self.skipped = False

            # The box is as tall as its longest line needs and no taller,
            # measured once here rather than per frame: a box that resized
            # itself as the text typed out would jump on every character.
            self.text_width = (SCREEN_WIDTH - 120 - PORTRAIT_SIDE - 24) - 36
            self.rows = max(
                (len(self.wrap_text(line, dialogue_font, self.text_width))
                 for line in lines),
                default=1
            )
            self.rows = max(1, min(MAX_DIALOGUE_LINES, self.rows))

        def visible_count(self):
            """How many characters of the current line are on screen."""

            if self.skipped:
                return len(self.lines[self.index])

            return revealed_characters(
                len(self.lines[self.index]),
                pygame.time.get_ticks() - self.started_at,
            )

        def line_complete(self):
            return self.visible_count() >= len(self.lines[self.index])

        def advance(self):
            # One press finishes the line, the next moves on. Anything
            # else punishes a fast reader for pressing early by eating
            # the line they had not finished reading.
            if not self.line_complete():
                self.skipped = True
                return

            self.index += 1
            self.started_at = pygame.time.get_ticks()
            self.skipped = False

            if self.index >= len(self.lines):
                self.active = False
                if self.on_finish:
                    self.on_finish()

        def handle_event(self, event):
            if not self.active:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                self.advance()

        def wrap_text(self, text, font, max_width):
            words = text.split(" ")
            lines, current = [], ""
            for word in words:
                test = (current + " " + word).strip()
                if font.size(test)[0] <= max_width:
                    current = test
                else:
                    lines.append(current)
                    current = word
            if current:
                lines.append(current)
            return lines

        def draw(self, surf):
            if not self.active:
                return

            # The box is measured from the fonts rather than given a fixed
            # height, so bumping a font size up for readability cannot push
            # the last line of dialogue out under the hint.
            line_height = dialogue_font.get_height() + 6
            box_h = (18 + name_font.get_height() + 10
                     + self.rows * line_height
                     + 10 + hint_font.get_height() + 14)
            box = pygame.Rect(60, SCREEN_HEIGHT - box_h - 40, SCREEN_WIDTH - 120, box_h)

            # Bottom-aligned with the box, so a short box means more of him
            # standing above it rather than a portrait hanging below it.
            portrait_rect = pygame.Rect(box.left, box.bottom - PORTRAIT_SIDE,
                                        PORTRAIT_SIDE, PORTRAIT_SIDE)
            draw_portrait(surf, portrait_rect)

            text_rect = pygame.Rect(portrait_rect.right + 24, box.top,
                                    self.text_width + 36, box.height)
            pygame.draw.rect(surf, STONE_MID, text_rect, border_radius=8)
            pygame.draw.rect(surf, METAL_FRAME, text_rect, 3, border_radius=8)

            name_tag = name_font.render("Mang Tahimik", True, YELLOW_GLOW)
            surf.blit(name_tag, (text_rect.left + 18, text_rect.top + 14))

            # Wrap the whole line first and reveal characters through the
            # finished layout, rather than wrapping what is visible so
            # far: wrapping a growing string makes words jump between
            # rows as they appear.
            wrapped = self.wrap_text(self.lines[self.index], dialogue_font,
                                     self.text_width)
            text_top = text_rect.top + 18 + name_font.get_height() + 10
            budget = self.visible_count()
            for i, line in enumerate(wrapped[:MAX_DIALOGUE_LINES]):
                if budget <= 0:
                    break
                txt = dialogue_font.render(line[:budget], True, WHITE)
                surf.blit(txt, (text_rect.left + 18, text_top + i * line_height))
                # +1 for the space the wrapper dropped at the line break,
                # so the reveal runs at an even pace across rows.
                budget -= len(line) + 1

            hint_text = ("Press E to continue" if self.line_complete()
                         else "Press E to show the full line")
            hint = hint_font.render(hint_text, True, DIM_TEXT)
            surf.blit(hint, (text_rect.right - hint.get_width() - 16, text_rect.bottom - hint.get_height() - 10))

    # ------------------------------------------------------------------
    # Movement & Combat practice area
    # ------------------------------------------------------------------
    # Treat the whole tutorial screen as a single "room" with no camera
    # scrolling, so MainCharacter's map bounds == the screen bounds.
    ZOOM = 1
    camera_x, camera_y = 0, 0

    main_character = MainCharacter(screen, SCREEN_WIDTH, SCREEN_HEIGHT)
    player_size = 40
    player_rect = pygame.Rect(
        SCREEN_WIDTH // 2 - player_size // 2,
        SCREEN_HEIGHT // 2 - player_size // 2,
        player_size, player_size,
    )
    player_rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
    player_x = float(player_rect.x)
    player_y = float(player_rect.y)
    player_speed = 2.5
    main_character.center_x, main_character.center_y = player_rect.centerx, player_rect.centery

    training_enemy = Enemy(
        screen, SCREEN_WIDTH, SCREEN_HEIGHT,
        world_x=SCREEN_WIDTH // 2 + 220,
        world_y=SCREEN_HEIGHT // 2,
        enemy_id="tiyanak_sinta",
    )
    player_combat = PlayerCombat()
    combat_audio = CombatAudio()
    attack_has_hit = False

    has_moved = {"up": False, "down": False, "left": False, "right": False}
    has_attacked = False
    has_solved = False

    def gate_complete():
        """Movement & Combat gate only - the coding challenge is its
        own separate gate later in the state machine."""
        return all(has_moved.values()) and has_attacked

    # ------------------------------------------------------------------
    # Tutorial state machine
    # ------------------------------------------------------------------
    # "intro_dialogue" -> "practice" (movement + attack)
    #   -> "movement_complete_dialogue" -> "code_editor_intro_dialogue"
    #   -> [CodeEditor opens] -> "challenge_complete_dialogue" (on pass)
    #      or "retry_dialogue" -> [CodeEditor opens again] (on fail)
    #   -> "stage_manual" -> "done"
    state = "intro_dialogue"

    intro_lines = [
        "Ah, a new soul in CodeBreak... I am Mang Tahimik, and I will guide you through these halls.",
        "Use W, A, S, D to move. Try walking in every direction so your legs remember the way.",
        "When you're ready, face the training Tiyanak and press E to strike it. Combat will save your life down here.",
    ]
    movement_complete_lines = [
        "Good. Your body knows how to move, and your blade knows how to strike.",
        "But steel alone won't get you far down here. Let me show you something else...",
    ]
    code_intro_lines = [
        "This is the Code Editor. Type your code on the left, press RUN to test it, then SUBMIT when you're ready.",
        "Your first lesson is simple: make the dummy hear you. Use print() to say... Hello, World!",
    ]
    retry_lines = [
        "Not yet, but the dungeon is patient. Try again.",
    ]
    challenge_complete_lines = [
        "Correct! Your mind now speaks the language of code, same as your blade speaks steel.",
        "One more thing before you descend - take a moment with the stage manual. It won't bite.",
    ]

    def finish_intro():
        nonlocal state
        state = "practice"

    def start_code_editor_intro():
        nonlocal state, dialogue
        dialogue = DialogueBox(code_intro_lines, on_finish=open_code_editor)
        state = "code_editor_intro_dialogue"

    def open_code_editor():
        """Opens the CodeEditor as a blocking sub-loop, then folds the
        result back into the tutorial's own state
        machine depending on whether the player actually solved it."""
        nonlocal state, dialogue, has_solved

        challenge = CHALLENGES["print_001"]
        background_snapshot = screen.copy()

        editor = CodeEditor(screen, challenge, background_snapshot)
        editor.run()

        if editor.solved:
            has_solved = True
            dialogue = DialogueBox(challenge_complete_lines, on_finish=finish_challenge_complete)
            state = "challenge_complete_dialogue"
        else:
            dialogue = DialogueBox(retry_lines, on_finish=open_code_editor)
            state = "retry_dialogue"

    def finish_challenge_complete():
        nonlocal state
        state = "stage_manual"

    dialogue = DialogueBox(intro_lines, on_finish=finish_intro)

    # --- Stage manual layout (reuses the How To Play content so the
    # two stay in sync) ---
    # Same panel, same columns, same content as the How To Play screen -
    # manual_layout() and draw_manual_columns() are shared so the sheet a
    # player reads here and the one they open from the menu cannot say
    # two different things.
    manual_panel_rect, manual_left_col, manual_right_col, manual_footer = (
        manual_layout(SCREEN_WIDTH, SCREEN_HEIGHT)
    )
    manual_begin_rect = pygame.Rect(
        manual_panel_rect.centerx - 110, manual_panel_rect.bottom - 56, 220, 40
    )

    # Escape opens a decision instead of silently skipping into gameplay.
    # Keeping the destructive/navigation choice mouse-only means repeated
    # Escape presses can only open/close this box; they cannot confirm it.
    show_exit_confirm = False
    exit_rect = pygame.Rect(0, 0, min(620, SCREEN_WIDTH - 60), 280)
    exit_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    keep_learning_rect = pygame.Rect(exit_rect.left + 48, exit_rect.bottom - 76, 220, 46)
    return_menu_rect = pygame.Rect(exit_rect.right - 268, exit_rect.bottom - 76, 220, 46)

    def draw_exit_confirmation(surf):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        surf.blit(overlay, (0, 0))
        pygame.draw.rect(surf, STONE_MID, exit_rect, border_radius=10)
        pygame.draw.rect(surf, METAL_FRAME, exit_rect, 3, border_radius=10)
        heading = exit_title_font.render("LEAVE THE TUTORIAL?", True, YELLOW_GLOW)
        surf.blit(heading, heading.get_rect(center=(exit_rect.centerx, exit_rect.top + 48)))
        copy = hint_font.render("Your new adventure will not start until the tutorial is completed.", True, WHITE)
        surf.blit(copy, copy.get_rect(center=(exit_rect.centerx, exit_rect.top + 105)))
        note = prompt_font.render("Press ESC to keep learning, or choose an option below.", True, DIM_TEXT)
        surf.blit(note, note.get_rect(center=(exit_rect.centerx, exit_rect.top + 145)))
        mouse = pygame.mouse.get_pos()
        for rect, label, color in (
            (keep_learning_rect, "KEEP LEARNING", GREEN_OK),
            (return_menu_rect, "RETURN TO MENU", (115, 75, 75)),
        ):
            fill = tuple(min(255, channel + 20) for channel in color) if rect.collidepoint(mouse) else color
            pygame.draw.rect(surf, fill, rect, border_radius=5)
            pygame.draw.rect(surf, STONE_LIGHT, rect, 2, border_radius=5)
            rendered = prompt_font.render(label, True, WHITE)
            surf.blit(rendered, rendered.get_rect(center=rect.center))

    def draw_stage_manual(surf, mouse_pos):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surf.blit(overlay, (0, 0))

        pygame.draw.rect(surf, (36, 38, 48), manual_panel_rect, border_radius=8)
        pygame.draw.rect(surf, METAL_FRAME, manual_panel_rect, 4, border_radius=8)
        pygame.draw.rect(surf, STONE_DARK, manual_panel_rect.inflate(-24, -24), border_radius=6)

        title = manual_title_font.render("STAGE MANUAL", True, WHITE)
        surf.blit(title, (manual_panel_rect.centerx - title.get_width() // 2, manual_panel_rect.top + 24))
        pygame.draw.line(
            surf, YELLOW_GLOW,
            (manual_panel_rect.left + 40, manual_panel_rect.top + 70),
            (manual_panel_rect.right - 40, manual_panel_rect.top + 70), 1
        )

        draw_manual_columns(
            surf, manual_left_col, manual_right_col, manual_footer,
            manual_header_font, manual_key_font, manual_line_font,
            manual_note_font,
        )

        begin_hovered = manual_begin_rect.collidepoint(mouse_pos)
        pygame.draw.rect(surf, (70, 140, 70) if begin_hovered else GREEN_OK, manual_begin_rect, border_radius=4)
        pygame.draw.rect(surf, STONE_LIGHT, manual_begin_rect, 2, border_radius=4)
        bt = manual_btn_font.render("BEGIN ADVENTURE", True, (20, 30, 20) if not begin_hovered else WHITE)
        surf.blit(bt, (manual_begin_rect.centerx - bt.get_width() // 2, manual_begin_rect.centery - bt.get_height() // 2))

        hint = hint_font.render("Click / E / SPACE / ENTER to begin", True, DIM_TEXT)
        surf.blit(hint, (manual_panel_rect.centerx - hint.get_width() // 2, manual_begin_rect.bottom + 10))

    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if handle_music_shortcut(event):
                continue

            if show_exit_confirm:
                if event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_ESCAPE, pygame.K_e, pygame.K_RETURN, pygame.K_KP_ENTER
                ):
                    show_exit_confirm = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if keep_learning_rect.collidepoint(event.pos):
                        show_exit_confirm = False
                    elif return_menu_rect.collidepoint(event.pos):
                        _stop_tutorial_music()
                        return "cancelled"
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                show_exit_confirm = True
                continue

            if state in (
                "intro_dialogue",
                "movement_complete_dialogue",
                "code_editor_intro_dialogue",
                "challenge_complete_dialogue",
                "retry_dialogue",
            ):
                dialogue.handle_event(event)

            if state == "practice" and event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                if player_combat.start_attack():
                    attack_has_hit = False
                    combat_audio.play("sword_swing")

            if state == "stage_manual":
                begin_pressed = (
                    event.type == pygame.KEYDOWN
                    and event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN)
                ) or (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and manual_begin_rect.collidepoint(event.pos)
                )
                if begin_pressed:
                    state = "done"

        keys = pygame.key.get_pressed()

        if state == "practice" and not show_exit_confirm:
            player_combat.update(dt)
            dx = dy = 0
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dy = -1; has_moved["up"] = True
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dy = 1; has_moved["down"] = True
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                dx = -1; has_moved["left"] = True
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                dx = 1; has_moved["right"] = True

            if dx and dy:
                dx *= 0.7071
                dy *= 0.7071

            if player_combat.locked:
                dx = dy = 0
            else:
                dx *= player_speed
                dy *= player_speed

            # No obstacles in the tutorial room, just screen-bound clamping,
            # handled inside update_position via map_width/map_height.
            main_character.update_position(
                dx, dy, player_rect, player_x, player_y, [], SCREEN_WIDTH, SCREEN_HEIGHT
            )
            player_x, player_y = main_character.pos_x, main_character.pos_y

            # Use the real enemy state machine and animations. Tutorial
            # damage is intentionally ignored so no campaign hearts are lost.
            training_enemy.update(
                dt, player_rect, [], SCREEN_WIDTH, SCREEN_HEIGHT
            )

            if player_combat.attack_active and not attack_has_hit:
                sword_box = attack_hitbox(player_rect, main_character.facing)
                if sword_box.colliderect(training_enemy.rect):
                    attack_has_hit = True
                    training_enemy.receive_damage(20)
                    combat_audio.play("sword_hit")
                    if training_enemy.hp == 0:
                        has_attacked = True
                        combat_audio.play("enemy_death")
                    else:
                        combat_audio.play("enemy_hurt")

            if (gate_complete() and not training_enemy.active
                    and player_combat.state != "attacking"):
                dialogue = DialogueBox(movement_complete_lines, on_finish=start_code_editor_intro)
                state = "movement_complete_dialogue"

            main_character.set_combat_state(player_combat.state)
            main_character.update_frames(keys)

        if state == "done":
            _stop_tutorial_music()
            return "completed"  # Full tutorial gate cleared.

        # --- draw ---
        mouse_pos = pygame.mouse.get_pos()

        screen.fill(BG_FLOOR)
        for gx in range(0, SCREEN_WIDTH, 64):
            pygame.draw.line(screen, (40, 42, 52), (gx, 0), (gx, SCREEN_HEIGHT), 1)
        for gy in range(0, SCREEN_HEIGHT, 64):
            pygame.draw.line(screen, (40, 42, 52), (0, gy), (SCREEN_WIDTH, gy), 1)

        training_enemy.draw_frames(ZOOM, camera_x, camera_y)

        main_character.draw_frames(ZOOM, camera_x, camera_y)

        if state == "practice":
            checklist = [
                ("Move UP (W)", has_moved["up"]),
                ("Move DOWN (S)", has_moved["down"]),
                ("Move LEFT (A)", has_moved["left"]),
                ("Move RIGHT (D)", has_moved["right"]),
                ("Defeat the Tiyanak (E)", has_attacked),
            ]
            panel = pygame.Rect(20, 20, 260, 30 + len(checklist) * 26)
            pygame.draw.rect(screen, STONE_MID, panel, border_radius=8)
            pygame.draw.rect(screen, METAL_FRAME, panel, 2, border_radius=8)
            title = prompt_font.render("Movement & Combat", True, YELLOW_GLOW)
            screen.blit(title, (panel.left + 14, panel.top + 8))
            for i, (label, done) in enumerate(checklist):
                color = GREEN_OK if done else DIM_TEXT
                mark = "[x]" if done else "[ ]"
                line = hint_font.render(f"{mark} {label}", True, color)
                screen.blit(line, (panel.left + 14, panel.top + 38 + i * 24))

            sword_box = attack_hitbox(player_rect, main_character.facing)
            if not sword_box.colliderect(training_enemy.rect):
                hint = hint_font.render("Face the Tiyanak, move closer, and press E", True, DIM_TEXT)
                screen.blit(hint, (
                    training_enemy.rect.centerx - hint.get_width() // 2,
                    training_enemy.rect.top - 36,
                ))

        if state == "stage_manual":
            draw_stage_manual(screen, mouse_pos)
        else:
            esc_hint = hint_font.render("ESC = Tutorial options", True, DIM_TEXT)
            screen.blit(esc_hint, (SCREEN_WIDTH - esc_hint.get_width() - 16, 16))
            dialogue.draw(screen)

        if show_exit_confirm:
            draw_exit_confirmation(screen)

        pygame.display.flip()
