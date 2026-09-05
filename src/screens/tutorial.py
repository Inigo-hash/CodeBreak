import math
import pygame
import sys
from src.settings_state import revealed_characters
from src.entities.player import MainCharacter
from src.entities.enemy import Enemy
from src.systems.combat import (
    FACING_VECTORS, PLAYER_DODGE_SPEED, PlayerCombat, attack_hitbox,
)
from src.systems.audio import CombatAudio, apply_music_volume, handle_music_shortcut
from src.ui.code_editor import CodeEditor
from src.data.challenges import CHALLENGES
from src.screens.how_to_play import (
    draw_manual_columns,
    manual_layout,
)
from src.ui.theme import UI_COLORS, body_font, title_font
from src.ui.gameplay_hud import draw_stat_bar
from src.screens.loading import StageLoadingScreen

# The manual's own colours, read straight from the shared palette rather
# than imported from how_to_play.py. Borrowing them from another screen
# meant this file restyled itself whenever that one changed.
STONE_DARK = UI_COLORS["modal_inner"]
STONE_LIGHT = UI_COLORS["modal_button_edge"]


def tutorial_screen(screen, play_music=True, show_loading=False,
                    practice_only=False):
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

    loading = None
    if show_loading:
        loading = StageLoadingScreen(
            screen,
            stage_id="tutorial",
            stage_name="Training Grounds",
            stage_label="Tutorial",
            previous_frame=screen,
        )
        loading.update(8, "Preparing your first lesson...")

    # --- Palette (stone/gold theme, matches main menu & game UI) ---
    STONE_MID = UI_COLORS["modal_button"]
    METAL_FRAME = UI_COLORS["modal_frame"]
    YELLOW_GLOW = UI_COLORS["modal_accent"]
    GREEN_OK = (80, 220, 120)
    WHITE = UI_COLORS["modal_text"]
    DIM_TEXT = UI_COLORS["modal_text_dim"]
    BG_FLOOR = (34, 36, 44)

    practice_background = None
    practice_collision_rects = []
    practice_arena_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
    if practice_only:
        try:
            source_background = pygame.image.load(
                "assets/images/backgrounds/practice_training_ground.png"
            ).convert()
            # Cover the screen without stretching the artwork, then crop the
            # excess from the centre for non-16:9 displays.
            scale = max(
                SCREEN_WIDTH / source_background.get_width(),
                SCREEN_HEIGHT / source_background.get_height(),
            )
            scaled_size = (
                round(source_background.get_width() * scale),
                round(source_background.get_height() * scale),
            )
            scaled_background = pygame.transform.smoothscale(
                source_background, scaled_size
            )
            crop = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
            crop.center = scaled_background.get_rect().center
            practice_background = scaled_background.subsurface(crop).copy()
            readability_shade = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
            )
            readability_shade.fill((8, 12, 20, 82))
            practice_background.blit(readability_shade, (0, 0))
        except (pygame.error, FileNotFoundError):
            practice_background = None

        # The generated arena keeps every prop around the perimeter. Match
        # its clear dirt floor with invisible solid bands so combatants feel
        # grounded inside the scene instead of walking over fences, targets,
        # braziers, banners, or the foreground gate.
        practice_arena_rect = pygame.Rect(
            # Leave sprite-sized clearance inside the visible fence. Enemy
            # collision bodies are intentionally much narrower than their
            # artwork (especially Tikbalang), so aligning the body boundary
            # directly to the props still lets the rendered sprite overlap.
            round(SCREEN_WIDTH * 0.12),
            round(SCREEN_HEIGHT * 0.21),
            round(SCREEN_WIDTH * 0.76),
            round(SCREEN_HEIGHT * 0.67),
        )
        practice_collision_rects = [
            pygame.Rect(0, 0, SCREEN_WIDTH, practice_arena_rect.top),
            pygame.Rect(
                0, practice_arena_rect.bottom, SCREEN_WIDTH,
                SCREEN_HEIGHT - practice_arena_rect.bottom,
            ),
            pygame.Rect(
                0, practice_arena_rect.top, practice_arena_rect.left,
                practice_arena_rect.height,
            ),
            pygame.Rect(
                practice_arena_rect.right, practice_arena_rect.top,
                SCREEN_WIDTH - practice_arena_rect.right,
                practice_arena_rect.height,
            ),
        ]

    def clamp_to_practice_oval(rect, padding_x=0, padding_y=0):
        """Project a combat body back onto the arena's elliptical floor."""
        if not practice_only:
            return False
        radius_x = max(1.0, practice_arena_rect.width / 2 - padding_x)
        radius_y = max(1.0, practice_arena_rect.height / 2 - padding_y)
        center_x, center_y = practice_arena_rect.center
        offset_x = rect.centerx - center_x
        offset_y = rect.centery - center_y
        normalized = (
            (offset_x / radius_x) ** 2
            + (offset_y / radius_y) ** 2
        )
        if normalized <= 1.0:
            return False
        correction = 1.0 / math.sqrt(normalized)
        rect.center = (
            round(center_x + offset_x * correction),
            round(center_y + offset_y * correction),
        )
        return True

    # --- Fonts ---
    name_font = title_font(26)
    dialogue_font = body_font(28)
    hint_font = body_font(20)
    prompt_font = title_font(18, bold=False)
    manual_title_font = title_font(30)
    manual_header_font = title_font(18, bold=False)
    manual_key_font = body_font(14, bold=True)
    manual_line_font = body_font(14)
    manual_note_font = body_font(12)
    manual_btn_font = title_font(22)
    exit_title_font = title_font(26)
    if loading:
        loading.update(24, "Preparing tutorial instructions...")

    # Rows of dialogue the textbox reserves room for. Every tutorial line
    # fits well inside this at the current width; the cap only exists so an
    # over-long line cannot grow the box off the bottom of the screen.
    MAX_DIALOGUE_LINES = 3
    PORTRAIT_SIDE = 190

    # --- Music: reuse the main menu theme for the tutorial ---
    tutorial_owns_music = play_music or practice_only
    if tutorial_owns_music:
        music_path = (
            "assets/audios/bgm/boss_fight/advanced/"
            "Boss_fight_advanced_sound_01.mp3"
            if practice_only
            else "assets/audios/tutorial_background_music.mp3"
        )
        pygame.mixer.music.load(music_path)
        apply_music_volume()
        pygame.mixer.music.play(-1)
    if loading:
        loading.update(38, "Loading Mang Tahimik...")

    def _stop_tutorial_music():
        if tutorial_owns_music:
            pygame.mixer.music.stop()

    # --- Mang Tahimik portrait (falls back to a drawn placeholder if the path is wrong) ---
    # NOTE: adjust this path to wherever his portrait actually lives in your assets folder
    portrait = None
    try:
        portrait = pygame.image.load("assets/images/characters/mang_tahimik/portrait.png").convert_alpha()
    except Exception:
        portrait = None
    if loading:
        loading.update(52, "Preparing the training room...")

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
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
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

            hint_text = ("Press SPACE to continue" if self.line_complete()
                         else "Press SPACE to show the full line")
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
    if loading:
        loading.update(72, "Equipping your explorer...")
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

    practice_waves = (
        ("TIYANAK TRIAL", ("tiyanak_sinta",) * 3),
        ("MANANANGGAL TRIAL", ("manananggal",) * 3),
        ("TIKBALANG TRIAL", ("tikbalang",) * 3),
    )
    practice_wave_index = 0

    def build_training_wave(enemy_ids):
        offsets = ((220, 0), (-260, -150), (250, 170))
        result = []
        for enemy_id, (offset_x, offset_y) in zip(enemy_ids, offsets):
            result.append(Enemy(
                screen, SCREEN_WIDTH, SCREEN_HEIGHT,
                world_x=SCREEN_WIDTH // 2 + offset_x,
                world_y=SCREEN_HEIGHT // 2 + offset_y,
                enemy_id=enemy_id,
                zone_rect=practice_arena_rect,
                detection_range=float("inf"), chase_range=float("inf"),
                disengage_range=float("inf"),
            ))
        return result

    initial_enemy_ids = (
        practice_waves[0][1] if practice_only else ("tiyanak_sinta",) * 3
    )
    training_enemies = build_training_wave(initial_enemy_ids)
    if loading:
        loading.update(88, "Summoning the training creature...")
    player_combat = PlayerCombat()
    combat_audio = CombatAudio()
    attack_has_hit = False

    has_moved = {"up": False, "down": False, "left": False, "right": False}
    has_attacked = False
    has_dodged = False
    death_count = 0
    has_solved = False

    def gate_complete():
        """Movement & Combat gate only - the coding challenge is its
        own separate gate later in the state machine."""
        if practice_only:
            return has_attacked
        return (
            all(has_moved.values())
            and has_attacked
            and has_dodged
        )

    # ------------------------------------------------------------------
    # Tutorial state machine
    # ------------------------------------------------------------------
    # "intro_dialogue" -> "practice" (movement + attack)
    #   -> "movement_complete_dialogue" -> "code_editor_intro_dialogue"
    #   -> [CodeEditor opens] -> "challenge_complete_dialogue" (on pass)
    #      or "retry_dialogue" -> [CodeEditor opens again] (on fail)
    #   -> "stage_manual" -> "done"
    state = "practice" if practice_only else "intro_dialogue"

    intro_lines = [
        "Ah, a new soul in CodeBreak... I am Mang Tahimik, and I will guide you through these halls.",
        "Use W, A, S, D to move. Try walking in every direction so your legs remember the way.",
        "The red HP bar is your health. If it empties, you fall, but this training ground will revive you so you can try again.",
        "The gold Energy bar powers your Left Shift dash. Each dash costs 25 energy, and energy slowly refills on its own.",
        "Dash out of danger and press E while facing the Tiyanak to strike back.",
    ]
    death_lesson_lines = [
        "You have fallen, but this training ground gives you another chance. In the adventure, defeat costs one of your hearts.",
        "Keep an eye on the red HP bar. Retreat and use a healing item from your hotbar before HP reaches zero.",
        "The gold Energy bar is your dash reserve. A dash costs 25 energy, briefly protects you from damage, and energy regenerates over time.",
        "Try again now: move, dash through an attack, face each Tiyanak, and press E to defeat all three.",
    ]
    repeat_death_advice = (
        (
            "The Tiyanak caught you again. Watch their attack animation and dash just before the strike lands.",
            "Your Energy refills slowly, so leave enough for an emergency dash. I will restore you now.",
        ),
        (
            "Another fall. Do not stay surrounded: keep moving and draw one Tiyanak away from the others.",
            "Check your HP often, create distance when it is low, and strike only when you have a safe opening.",
        ),
        (
            "You fell once more, but every attempt teaches timing. Face your target before pressing E so the blade connects.",
            "Dash through danger, wait for Energy to recover, then return to the fight. Up you get.",
        ),
    )

    def death_dialogue_for(attempt):
        if attempt == 1:
            return death_lesson_lines
        advice = repeat_death_advice[(attempt - 2) % len(repeat_death_advice)]
        return [
            f"Defeat #{attempt}. Do not lose heart; this training ground will revive you every time.",
            *advice,
            ("Try again. Your HP, Energy, position, and the current practice wave have been reset."
             if practice_only else
             "Try again. Your HP, Energy, position, and all three training Tiyanak have been reset."),
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

    def restart_after_death_lesson():
        nonlocal state, player_x, player_y, attack_has_hit, has_attacked
        player_combat.reset()
        player_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        player_x, player_y = map(float, player_rect.topleft)
        main_character.pos_x, main_character.pos_y = player_x, player_y
        main_character.center_x, main_character.center_y = player_rect.center
        for enemy in training_enemies:
            enemy.reset()
        attack_has_hit = False
        has_attacked = False
        state = "practice"

    def start_next_practice_wave():
        nonlocal practice_wave_index, training_enemies
        nonlocal player_x, player_y, attack_has_hit, has_attacked
        practice_wave_index += 1
        training_enemies = build_training_wave(
            practice_waves[practice_wave_index][1]
        )
        player_combat.reset()
        player_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        player_x, player_y = map(float, player_rect.topleft)
        main_character.pos_x, main_character.pos_y = player_x, player_y
        main_character.center_x, main_character.center_y = player_rect.center
        attack_has_hit = False
        has_attacked = False

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
    if loading:
        loading.update(96, "Opening the training grounds...")

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
        heading_text = (
            "LEAVE TRAINING GROUNDS?"
            if practice_only else "LEAVE THE TUTORIAL?"
        )
        heading = exit_title_font.render(heading_text, True, YELLOW_GLOW)
        surf.blit(heading, heading.get_rect(center=(exit_rect.centerx, exit_rect.top + 48)))
        copy_text = (
            "Leaving ends this training run. Press P on the island whenever you want to return."
            if practice_only
            else "Your new adventure will not start until the tutorial is completed."
        )
        def draw_centered_wrapped(text, font, color, top, max_width):
            words = text.split()
            lines, current = [], ""
            for word in words:
                candidate = f"{current} {word}".strip()
                if not current or font.size(candidate)[0] <= max_width:
                    current = candidate
                else:
                    lines.append(current)
                    current = word
            if current:
                lines.append(current)
            for index, line_text in enumerate(lines):
                rendered = font.render(line_text, True, color)
                surf.blit(rendered, rendered.get_rect(
                    center=(exit_rect.centerx,
                            top + index * (font.get_height() + 2))
                ))

        draw_centered_wrapped(
            copy_text, hint_font, WHITE, exit_rect.top + 98,
            exit_rect.width - 64,
        )
        draw_centered_wrapped(
            ("Press ESC to resume training, or choose an option below."
             if practice_only else
             "Press ESC to keep learning, or choose an option below."),
            prompt_font, DIM_TEXT, exit_rect.top + 150,
            exit_rect.width - 64,
        )
        mouse = pygame.mouse.get_pos()
        for rect, label, color in (
            (keep_learning_rect, (
                "RESUME TRAINING" if practice_only else "KEEP LEARNING"
            ), GREEN_OK),
            (return_menu_rect, (
                "EXIT TRAINING"
                if practice_only else "RETURN TO MENU"
            ), (115, 75, 75)),
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

        hint = hint_font.render("Press SPACE or click BEGIN ADVENTURE", True, DIM_TEXT)
        surf.blit(hint, (manual_panel_rect.centerx - hint.get_width() // 2, manual_begin_rect.bottom + 10))

    if loading:
        loading.finish()

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
                        return "practice_cancelled" if practice_only else "cancelled"
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
                "death_lesson_dialogue",
            ):
                dialogue.handle_event(event)

            if (state == "practice"
                    and event.type == pygame.KEYDOWN and event.key == pygame.K_e):
                if player_combat.start_attack():
                    attack_has_hit = False
                    combat_audio.play("sword_swing")

            if (state == "practice" and event.type == pygame.KEYDOWN
                    and event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT)):
                if player_combat.start_dodge():
                    has_dodged = True
                    combat_audio.play("dodge")

            if state == "stage_manual":
                begin_pressed = (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_SPACE
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

            if player_combat.state == "dodging":
                dodge_dx, dodge_dy = FACING_VECTORS.get(
                    main_character.facing, (1, 0)
                )
                dx = dodge_dx * PLAYER_DODGE_SPEED
                dy = dodge_dy * PLAYER_DODGE_SPEED
            elif player_combat.locked:
                dx = dy = 0
            else:
                dx *= player_speed
                dy *= player_speed

            # No obstacles in the tutorial room, just screen-bound clamping,
            # handled inside update_position via map_width/map_height.
            main_character.update_position(
                dx, dy, player_rect, player_x, player_y,
                practice_collision_rects, SCREEN_WIDTH, SCREEN_HEIGHT
            )
            player_x, player_y = main_character.pos_x, main_character.pos_y
            if clamp_to_practice_oval(
                    player_rect, padding_x=24, padding_y=18):
                player_x, player_y = map(float, player_rect.topleft)
                main_character.pos_x = player_x
                main_character.pos_y = player_y
                main_character.center_x, main_character.center_y = (
                    player_rect.center
                )

            # Training enemies pursue with the real state machine, but their
            # damage cannot cost campaign hearts during the lesson.
            for training_enemy in training_enemies:
                incoming_damage = training_enemy.update(
                    dt, player_rect,
                    [other.rect for other in training_enemies
                     if other is not training_enemy and other.active]
                    + practice_collision_rects,
                    SCREEN_WIDTH, SCREEN_HEIGHT,
                )
                if incoming_damage and player_combat.take_damage(incoming_damage):
                    combat_audio.play(
                        "player_death" if player_combat.hp == 0 else "player_hurt"
                    )
                if clamp_to_practice_oval(
                        training_enemy.rect, padding_x=56, padding_y=24):
                    training_enemy.x = float(training_enemy.rect.x)
                    training_enemy.y = float(training_enemy.rect.y)
                    training_enemy.center_x, training_enemy.center_y = (
                        training_enemy.rect.center
                    )
                    training_enemy.chase_path.clear()
                    training_enemy.chase_goal = None

            if player_combat.attack_active and not attack_has_hit:
                sword_box = attack_hitbox(player_rect, main_character.facing)
                for training_enemy in training_enemies:
                    if (training_enemy.active
                            and sword_box.colliderect(training_enemy.rect)):
                        attack_has_hit = True
                        training_enemy.receive_damage(20)
                        combat_audio.play("sword_hit")
                        combat_audio.play(
                            "enemy_death" if training_enemy.hp == 0
                            else "enemy_hurt"
                        )
                        break

            has_attacked = all(not enemy.active for enemy in training_enemies)

            if player_combat.hp == 0 and player_combat.action_time == 0:
                death_count += 1
                if practice_only:
                    restart_after_death_lesson()
                else:
                    dialogue = DialogueBox(
                        death_dialogue_for(death_count),
                        on_finish=restart_after_death_lesson,
                    )
                    state = "death_lesson_dialogue"

            if (state == "practice" and gate_complete()
                    and player_combat.state != "attacking"):
                if practice_only:
                    if practice_wave_index + 1 < len(practice_waves):
                        start_next_practice_wave()
                    else:
                        _stop_tutorial_music()
                        return "practice_complete"
                else:
                    dialogue = DialogueBox(
                        movement_complete_lines,
                        on_finish=start_code_editor_intro,
                    )
                    state = "movement_complete_dialogue"

            main_character.set_combat_state(player_combat.state)
            main_character.update_frames(keys)

        if state == "done":
            _stop_tutorial_music()
            return "practice_complete" if practice_only else "completed"

        # --- draw ---
        mouse_pos = pygame.mouse.get_pos()

        if practice_background is not None:
            screen.blit(practice_background, (0, 0))
        else:
            screen.fill(BG_FLOOR)
            for gx in range(0, SCREEN_WIDTH, 64):
                pygame.draw.line(
                    screen, (40, 42, 52),
                    (gx, 0), (gx, SCREEN_HEIGHT), 1,
                )
            for gy in range(0, SCREEN_HEIGHT, 64):
                pygame.draw.line(
                    screen, (40, 42, 52),
                    (0, gy), (SCREEN_WIDTH, gy), 1,
                )

        for training_enemy in training_enemies:
            training_enemy.draw_frames(ZOOM, camera_x, camera_y)

        main_character.draw_frames(ZOOM, camera_x, camera_y)

        if state == "practice":
            if practice_only:
                practice_title = (
                    f"WAVE {practice_wave_index + 1}/3  "
                    f"{practice_waves[practice_wave_index][0]}"
                )
                remaining = sum(enemy.active for enemy in training_enemies)
                title_surface = prompt_font.render(
                    practice_title, True, YELLOW_GLOW
                )
                remaining_surface = hint_font.render(
                    f"Enemies remaining: {remaining}", True, WHITE
                )
                panel = pygame.Rect(
                    20, 20,
                    max(title_surface.get_width(),
                        remaining_surface.get_width()) + 28,
                    title_surface.get_height()
                    + remaining_surface.get_height() + 30,
                )
                pygame.draw.rect(screen, STONE_MID, panel, border_radius=8)
                pygame.draw.rect(screen, METAL_FRAME, panel, 2,
                                 border_radius=8)
                screen.blit(title_surface, (panel.left + 14, panel.top + 8))
                screen.blit(remaining_surface, (
                    panel.left + 14,
                    panel.top + title_surface.get_height() + 14,
                ))
            else:
                checklist = [
                    ("Move UP (W)", has_moved["up"]),
                    ("Move DOWN (S)", has_moved["down"]),
                    ("Move LEFT (A)", has_moved["left"]),
                    ("Move RIGHT (D)", has_moved["right"]),
                    ("Dash (Left Shift)", has_dodged),
                    ("Defeat all 3 Tiyanak (E)", has_attacked),
                ]
                line_width = max(
                    hint_font.size(f"[ ] {label}")[0]
                    for label, _ in checklist
                )
                practice_title = "Movement & Combat"
                panel_width = min(
                    SCREEN_WIDTH - 40,
                    max(line_width,
                        prompt_font.size(practice_title)[0]) + 28,
                )
                row_height = max(26, hint_font.get_height() + 6)
                header_height = max(44, prompt_font.get_height() + 22)
                panel = pygame.Rect(
                    20, 20, panel_width,
                    header_height + len(checklist) * row_height + 10,
                )
                pygame.draw.rect(screen, STONE_MID, panel, border_radius=8)
                pygame.draw.rect(screen, METAL_FRAME, panel, 2,
                                 border_radius=8)
                title = prompt_font.render(
                    practice_title, True, YELLOW_GLOW
                )
                screen.blit(title, (panel.left + 14, panel.top + 8))
                for i, (label, done) in enumerate(checklist):
                    color = GREEN_OK if done else DIM_TEXT
                    mark = "[x]" if done else "[ ]"
                    line = hint_font.render(
                        f"{mark} {label}", True, color
                    )
                    screen.blit(line, (
                        panel.left + 14,
                        panel.top + header_height + i * row_height,
                    ))

            sword_box = attack_hitbox(player_rect, main_character.facing)
            nearest_enemy = min(
                (enemy for enemy in training_enemies if enemy.active),
                key=lambda enemy: math.dist(player_rect.center, enemy.rect.center),
                default=None,
            )
            if (not practice_only and nearest_enemy
                    and not sword_box.colliderect(nearest_enemy.rect)):
                hint_text = "Face a Tiyanak, move closer, and press E"
                hint = hint_font.render(hint_text, True, DIM_TEXT)
                screen.blit(hint, (
                    nearest_enemy.rect.centerx - hint.get_width() // 2,
                    nearest_enemy.rect.top - 36,
                ))

        if state in ("practice", "death_lesson_dialogue"):
            stat_font = body_font(15, bold=True)
            stat_width = min(330, SCREEN_WIDTH // 3)
            stat_x = SCREEN_WIDTH - stat_width - 20
            stat_y = 58
            stats_panel = pygame.Rect(stat_x - 12, stat_y - 12,
                                      stat_width + 24, 66)
            pygame.draw.rect(screen, STONE_MID, stats_panel, border_radius=8)
            pygame.draw.rect(screen, METAL_FRAME, stats_panel, 2,
                             border_radius=8)
            draw_stat_bar(
                screen, stat_font, stat_x, stat_y, stat_width, "HP",
                player_combat.hp, player_combat.max_hp, label_width=132,
            )
            draw_stat_bar(
                screen, stat_font, stat_x, stat_y + 27, stat_width, "ENERGY",
                round(player_combat.energy), player_combat.max_energy,
                fill_color=YELLOW_GLOW, label_width=132,
            )

        if state == "stage_manual":
            draw_stage_manual(screen, mouse_pos)
        else:
            esc_label = (
                "ESC = Exit training"
                if practice_only else "ESC = Tutorial options"
            )
            esc_hint = hint_font.render(esc_label, True, DIM_TEXT)
            screen.blit(esc_hint, (SCREEN_WIDTH - esc_hint.get_width() - 16, 16))
            # practice_only deliberately starts in "practice" and must not
            # leak the normal tutorial's already-created introduction over
            # the boss training arena.
            if state.endswith("_dialogue"):
                dialogue.draw(screen)

        if show_exit_confirm:
            draw_exit_confirmation(screen)

        pygame.display.flip()
