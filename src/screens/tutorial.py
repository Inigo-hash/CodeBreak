import pygame
import sys
from src.settings_state import settings_state as _settings_state
from src.entities.player import MainCharacter


def tutorial_screen(screen):
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

    # --- Palette (stone/gold theme, matches main menu & game UI) ---
    STONE_MID = (42, 46, 58)
    METAL_FRAME = (90, 94, 110)
    YELLOW_GLOW = (255, 220, 120)
    GREEN_OK = (80, 220, 120)
    WHITE = (255, 255, 255)
    DIM_TEXT = (180, 180, 190)
    BG_FLOOR = (34, 36, 44)
    DUMMY_FALLBACK_COLOR = (140, 90, 60)
    DUMMY_HIT_TINT = (255, 140, 60)

    # --- Fonts ---
    name_font = pygame.font.SysFont("consolas", 22, bold=True)
    dialogue_font = pygame.font.SysFont("consolas", 20)
    hint_font = pygame.font.SysFont("consolas", 16)
    prompt_font = pygame.font.SysFont("consolas", 18, bold=True)

    # --- Music: reuse the main menu theme for the tutorial ---
    pygame.mixer.music.load("assets/audios/mainMenuBgm.mp3")
    pygame.mixer.music.set_volume(_settings_state["music_vol"])
    pygame.mixer.music.play(-1)

    def _stop_tutorial_music():
        pygame.mixer.music.stop()

    # --- Mang Tahimik portrait (falls back to a drawn placeholder if the path is wrong) ---
    # NOTE: adjust this path to wherever his portrait actually lives in your assets folder
    portrait = None
    try:
        portrait = pygame.image.load("assets/images/characters/mang_tahimik/portrait.png").convert_alpha()
        portrait = pygame.transform.scale(portrait, (160, 160))
    except Exception:
        portrait = None

    def draw_portrait(surf, rect):
        if portrait:
            surf.blit(portrait, rect.topleft)
            pygame.draw.rect(surf, METAL_FRAME, rect, 3, border_radius=6)
        else:
            pygame.draw.rect(surf, (60, 70, 60), rect, border_radius=6)
            pygame.draw.rect(surf, METAL_FRAME, rect, 3, border_radius=6)
            cx, cy = rect.center
            pygame.draw.circle(surf, (220, 230, 220), (cx, cy - 20), 34)
            pygame.draw.rect(surf, (220, 230, 220), (rect.left + 24, cy, rect.width - 48, 50), border_radius=10)
            pygame.draw.circle(surf, (30, 30, 38), (cx - 12, cy - 24), 4)
            pygame.draw.circle(surf, (30, 30, 38), (cx + 12, cy - 24), 4)

    # --- Training dummy sprite: reuse the static enemy asset (yuunp) as a stand-in ---
    # NOTE: I don't know the exact filename in your project — adjust this path.
    # Falls back to the old brown placeholder box if it doesn't load.
    DUMMY_SIZE = (64, 64)
    dummy_sprite = None
    try:
        dummy_sprite = pygame.image.load("assets/images/enemies/static_enemy.png").convert_alpha()
        dummy_sprite = pygame.transform.scale(dummy_sprite, DUMMY_SIZE)
    except Exception:
        dummy_sprite = None

    def draw_dummy(surf, rect, hit):
        if dummy_sprite:
            surf.blit(dummy_sprite, rect.topleft)
            if hit:
                tint = pygame.Surface(rect.size, pygame.SRCALPHA)
                tint.fill((*DUMMY_HIT_TINT, 120))
                surf.blit(tint, rect.topleft)
        else:
            color = DUMMY_HIT_TINT if hit else DUMMY_FALLBACK_COLOR
            pygame.draw.rect(surf, color, rect, border_radius=4)
            pygame.draw.rect(surf, METAL_FRAME, rect, 2, border_radius=4)

    # ------------------------------------------------------------------
    # Dialogue system: portrait + textbox, advance on click / E / SPACE
    # ------------------------------------------------------------------
    class DialogueBox:
        def __init__(self, lines, on_finish=None):
            self.lines = lines
            self.index = 0
            self.on_finish = on_finish
            self.active = True

        def advance(self):
            self.index += 1
            if self.index >= len(self.lines):
                self.active = False
                if self.on_finish:
                    self.on_finish()

        def handle_event(self, event):
            if not self.active:
                return
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                self.advance()
            elif event.type == pygame.MOUSEBUTTONDOWN:
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
            box_h = 170
            box = pygame.Rect(60, SCREEN_HEIGHT - box_h - 40, SCREEN_WIDTH - 120, box_h)

            portrait_rect = pygame.Rect(box.left, box.top - 20, 160, 160)
            draw_portrait(surf, portrait_rect)

            text_rect = pygame.Rect(portrait_rect.right + 24, box.top, box.width - 160 - 24, box.height)
            pygame.draw.rect(surf, STONE_MID, text_rect, border_radius=8)
            pygame.draw.rect(surf, METAL_FRAME, text_rect, 3, border_radius=8)

            name_tag = name_font.render("Mang Tahimik", True, YELLOW_GLOW)
            surf.blit(name_tag, (text_rect.left + 18, text_rect.top + 14))

            wrapped = self.wrap_text(self.lines[self.index], dialogue_font, text_rect.width - 36)
            for i, line in enumerate(wrapped[:3]):
                txt = dialogue_font.render(line, True, WHITE)
                surf.blit(txt, (text_rect.left + 18, text_rect.top + 50 + i * 26))

            hint = hint_font.render("Click / E / SPACE to continue", True, DIM_TEXT)
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

    dummy_rect = pygame.Rect(SCREEN_WIDTH // 2 + 220, SCREEN_HEIGHT // 2 - 32, *DUMMY_SIZE)
    dummy_flash_timer = 0.0

    has_moved = {"up": False, "down": False, "left": False, "right": False}
    has_attacked = False

    def gate_complete():
        return all(has_moved.values()) and has_attacked

    # ------------------------------------------------------------------
    # Tutorial state machine
    # ------------------------------------------------------------------
    state = "intro_dialogue"  # -> "practice" -> "gate_complete_dialogue" -> "done"

    intro_lines = [
        "Ah, a new soul in CodeBreak... I am Mang Tahimik, and I will guide you through these halls.",
        "Use W, A, S, D to move. Try walking in every direction so your legs remember the way.",
        "When you're ready, press E near the training dummy to strike it. Combat will save your life down here.",
    ]
    complete_lines = [
        "Good. Your body knows how to move, and your blade knows how to strike.",
        "That is all you need for now. The dungeon does not wait for the hesitant.",
    ]

    def finish_intro():
        nonlocal state
        state = "practice"

    def finish_complete_dialogue():
        nonlocal state
        state = "done"

    dialogue = DialogueBox(intro_lines, on_finish=finish_intro)

    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                _stop_tutorial_music()
                return  # bail back to caller at any point

            if state in ("intro_dialogue", "gate_complete_dialogue"):
                dialogue.handle_event(event)

            if state == "practice" and event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                if player_rect.colliderect(dummy_rect.inflate(30, 30)):
                    has_attacked = True
                    dummy_flash_timer = 0.15

        keys = pygame.key.get_pressed()

        if state == "practice":
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

            dx *= player_speed
            dy *= player_speed

            # No obstacles in the tutorial room, just screen-bound clamping,
            # handled inside update_position via map_width/map_height.
            main_character.update_position(
                dx, dy, player_rect, player_x, player_y, [], SCREEN_WIDTH, SCREEN_HEIGHT
            )
            player_x, player_y = main_character.pos_x, main_character.pos_y

            if dummy_flash_timer > 0:
                dummy_flash_timer -= dt

            if gate_complete():
                dialogue = DialogueBox(complete_lines, on_finish=finish_complete_dialogue)
                state = "gate_complete_dialogue"

            main_character.update_frames(keys)

        if state == "done":
            _stop_tutorial_music()
            return  # Movement & Combat gate cleared, hand control back to caller

        # --- draw ---
        screen.fill(BG_FLOOR)
        for gx in range(0, SCREEN_WIDTH, 64):
            pygame.draw.line(screen, (40, 42, 52), (gx, 0), (gx, SCREEN_HEIGHT), 1)
        for gy in range(0, SCREEN_HEIGHT, 64):
            pygame.draw.line(screen, (40, 42, 52), (0, gy), (SCREEN_WIDTH, gy), 1)

        draw_dummy(screen, dummy_rect, dummy_flash_timer > 0)

        main_character.draw_frames(ZOOM, camera_x, camera_y)

        if state == "practice":
            checklist = [
                ("Move UP (W)", has_moved["up"]),
                ("Move DOWN (S)", has_moved["down"]),
                ("Move LEFT (A)", has_moved["left"]),
                ("Move RIGHT (D)", has_moved["right"]),
                ("Attack dummy (E)", has_attacked),
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

            if not player_rect.colliderect(dummy_rect.inflate(30, 30)):
                hint = hint_font.render("Walk up to the dummy and press E to attack", True, DIM_TEXT)
                screen.blit(hint, (dummy_rect.centerx - hint.get_width() // 2, dummy_rect.top - 26))

        esc_hint = hint_font.render("ESC = Skip tutorial for now", True, DIM_TEXT)
        screen.blit(esc_hint, (SCREEN_WIDTH - esc_hint.get_width() - 16, 16))

        dialogue.draw(screen)
        pygame.display.flip()