from pytmx.util_pygame import load_pygame
import pygame
import sys
from src.settings_state import settings_state as _settings_state
from src.entities.player import MainCharacter
from src.entities.enemy import Enemy
from src.ui.code_editor import CodeEditor
from src.screens.game_over import game_over_screen
from src.screens.profile import profile_screen

def game_screen(screen):
    clock = pygame.time.Clock()

    pygame.mixer.music.load("assets/audios/gameStage1Bgm.mp3")  
    pygame.mixer.music.set_volume(_settings_state["music_vol"])  # ← use saved volume                  
    pygame.mixer.music.play(-1)

    # --- Load Map ---
    tmx_data = load_pygame("assets/map/tmx/basic.tmx")
    TILE_SIZE = tmx_data.tilewidth

    map_width  = tmx_data.width  * TILE_SIZE
    map_height = tmx_data.height * TILE_SIZE

    # --- Build collision rects from tile custom properties ---
    collision_rects = []
    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'data'):
            for x, y, gid in layer:
                if gid == 0:
                    continue
                props = tmx_data.get_tile_properties_by_gid(gid)
                if props and props.get('collidable'):
                    collision_rects.append(
                        pygame.Rect(
                            x * TILE_SIZE,
                            y * TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE
                        )
                    )

    # --- Load interactive objects from Object Layer ---
    interactables = []
    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'name') and layer.name == "Object Layer 1":
            for obj in layer:
                if obj.properties.get('types') == 'interactive':
                    interactables.append({
                        'rect': pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height)),
                        'actions': obj.properties.get('actions'),
                        'inspecting': False,
                        'inspect_progress': 0.0
                    })

    # --- Player Setup ---
    SCREEN_W, SCREEN_H = screen.get_size()
    player_size = TILE_SIZE

    spawn_margin = TILE_SIZE * 6
    spawn_offset_x = TILE_SIZE * 7  # how far right of center — tweak this number
    player_rect = pygame.Rect(
        map_width // 2 - player_size // 2 + spawn_offset_x,
        map_height - spawn_margin,
        player_size,
        player_size
    )

    # Float position to avoid integer truncation causing uneven movement
    player_rect.clamp_ip(pygame.Rect(0, 0, map_width, map_height))
    player_x = float(player_rect.x)
    player_y = float(player_rect.y)
    player_speed = 2.50
    player_color = (255, 50, 50)

    # --- Fonts ---
    font = pygame.font.SysFont("consolas", 18)
    inspect_font = pygame.font.SysFont("consolas", 20)
    pause_title_font = pygame.font.SysFont("consolas", 40, bold=True)
    pause_button_font = pygame.font.SysFont("consolas", 24, bold=True)
    INSPECT_TIME = 2.0  # seconds to hold E

    # --- Profile HUD (top-left portrait + HP/PP bars) ---
    # Draft values — not wired to real damage/energy systems yet.
    profile_name = "Bobiles the explorer the great"
    player_hp, player_max_hp = 100, 100
    player_pp, player_max_pp = 100, 100

    hud_font_name = pygame.font.SysFont("consolas", 16, bold=True)
    hud_font_bar = pygame.font.SysFont("consolas", 12, bold=True)

    HUD_MARGIN = 14
    HUD_PORTRAIT_SIZE = 56
    hud_portrait = pygame.image.load("assets/images/logos/codebreakLogo.png").convert_alpha()
    hud_portrait = pygame.transform.smoothscale(hud_portrait, (HUD_PORTRAIT_SIZE, HUD_PORTRAIT_SIZE))
    hud_portrait_rect = pygame.Rect(HUD_MARGIN, HUD_MARGIN, HUD_PORTRAIT_SIZE, HUD_PORTRAIT_SIZE)

    HUD_BAR_WIDTH = 180
    HUD_BAR_HEIGHT = 16
    hud_bars_left = hud_portrait_rect.right + 10
    hud_hp_rect = pygame.Rect(hud_bars_left, hud_portrait_rect.top + 22, HUD_BAR_WIDTH, HUD_BAR_HEIGHT)
    hud_pp_rect = pygame.Rect(hud_bars_left, hud_hp_rect.bottom + 6, HUD_BAR_WIDTH, HUD_BAR_HEIGHT)

    def draw_hud_bar(surf, rect, value, max_value, fill_color, edge_color):
        pygame.draw.rect(surf, (20, 22, 28), rect, border_radius=4)
        ratio = 0 if max_value <= 0 else max(0.0, min(1.0, value / max_value))
        fill_rect = pygame.Rect(rect.left, rect.top, int(rect.width * ratio), rect.height)
        if fill_rect.width > 0:
            pygame.draw.rect(surf, fill_color, fill_rect, border_radius=4)
        pygame.draw.rect(surf, edge_color, rect, 2, border_radius=4)
        label = hud_font_bar.render(f"{value}/{max_value}", True, (255, 255, 255))
        surf.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

    def draw_profile_hud(surf, mouse_pos):
        pygame.draw.rect(surf, (20, 20, 26), hud_portrait_rect.inflate(6, 6), border_radius=4)
        surf.blit(hud_portrait, hud_portrait_rect)
        hovered = hud_portrait_rect.collidepoint(mouse_pos)
        frame_color = (255, 220, 120) if hovered else (90, 94, 110)
        pygame.draw.rect(surf, frame_color, hud_portrait_rect.inflate(6, 6), 2, border_radius=4)

        name_surf = hud_font_name.render(profile_name, True, (240, 240, 240))
        surf.blit(name_surf, (hud_bars_left, hud_portrait_rect.top))

        draw_hud_bar(surf, hud_hp_rect, player_hp, player_max_hp, (200, 40, 40), (255, 90, 90))
        draw_hud_bar(surf, hud_pp_rect, player_pp, player_max_pp, (210, 175, 40), (255, 220, 120))

    # --- Camera with zoom ---
    camera_x = 0
    camera_y = 0

    ZOOM = 2 # increase this to zoom in more (ex. 2, 3, or 4)

    def update_camera():
        cx = player_rect.centerx * ZOOM - SCREEN_W // 2
        cy = player_rect.centery * ZOOM - SCREEN_H // 2
        cx = max(0, min(cx, map_width * ZOOM - SCREEN_W))
        cy = max(0, min(cy, map_height * ZOOM - SCREEN_H))
        return cx, cy

    # --- Pre-render map ---
    def render_map_surface():
        surf = pygame.Surface((map_width, map_height))
        for layer in tmx_data.visible_layers:
            if hasattr(layer, 'data'):
                for x, y, gid in layer:
                    if gid == 0:
                        continue
                    tile = tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        surf.blit(tile, (x * TILE_SIZE, y * TILE_SIZE))
            elif hasattr(layer, 'name') and layer.name == "Object Layer 1":
                # Draw tile objects (e.g. the big tree) placed on the object layer
                for obj in layer:
                    gid = getattr(obj, 'gid', None)
                    if not gid:
                        continue  # skip non-tile objects (interactables, shapes, etc.)
                    tile_image = tmx_data.get_tile_image_by_gid(gid)
                    if not tile_image:
                        continue
                    # Scale to whatever size you resized the object to in Tiled
                    scaled = pygame.transform.scale(tile_image, (int(obj.width), int(obj.height)))
                    # Tiled anchors tile objects at bottom-left, so shift y up by height
                    surf.blit(scaled, (obj.x, obj.y - obj.height))
        return surf

    map_surface = render_map_surface()
    # Scale the pre-rendered map once at startup based on ZOOM level (e.g. ZOOM=2 doubles the size)
    # This avoids rescaling every frame which would slow down the game
    map_surface = pygame.transform.scale(map_surface, (map_width * ZOOM, map_height * ZOOM))

    # --- Pause menu setup ---
    paused = False
    show_pause_settings = False

    PAUSE_MENU_OPTIONS = [
        ("RESUME", "resume"),
        ("SETTINGS", "settings"),
        ("RETURN TO MAIN MENU", "main_menu"),
    ]
    PAUSE_BTN_WIDTH = int(SCREEN_W * 0.25)
    PAUSE_BTN_HEIGHT = int(SCREEN_H * 0.07)
    PAUSE_BTN_GAP = int(SCREEN_H * 0.02)
    total_height = (
        len(PAUSE_MENU_OPTIONS) * PAUSE_BTN_HEIGHT
        + (len(PAUSE_MENU_OPTIONS) - 1) * PAUSE_BTN_GAP
    )

    pause_by0 = (SCREEN_H - total_height) // 2
    pause_center_x = SCREEN_W // 2 - PAUSE_BTN_WIDTH // 2

    pause_buttons = []
    for i, (label, action) in enumerate(PAUSE_MENU_OPTIONS):
        pause_buttons.append({
            "label": label,
            "action": action,
            "rect": pygame.Rect(
                pause_center_x,
                pause_by0 + i * (PAUSE_BTN_HEIGHT + PAUSE_BTN_GAP),
                PAUSE_BTN_WIDTH,
                PAUSE_BTN_HEIGHT
            )
        })

    panel_width = min(500, int(SCREEN_W * 0.40))
    panel_height = min(360, int(SCREEN_H * 0.50))

    settings_panel_rect = pygame.Rect(
        (SCREEN_W - panel_width) // 2,
        (SCREEN_H - panel_height) // 2,
        panel_width,
        panel_height
    )
    padding = 30

    music_bar = pygame.Rect(
        settings_panel_rect.left + padding,
        settings_panel_rect.top + int(settings_panel_rect.height * 0.35),
        settings_panel_rect.width - padding * 2,
        14
    )

    sfx_bar = pygame.Rect(
        settings_panel_rect.left + padding,
        settings_panel_rect.top + int(settings_panel_rect.height * 0.58),
        settings_panel_rect.width - padding * 2,
        14
    )

    settings_back_rect = pygame.Rect(settings_panel_rect.centerx - 70, settings_panel_rect.bottom - 56, 140, 36)
    dragging_music = False
    dragging_sfx = False

    def draw_pause_button(surf, rect, label, hovered):
        color = (60, 90, 130) if hovered else (40, 42, 54)
        border_color = (120, 180, 230) if hovered else (90, 94, 110)
        pygame.draw.rect(surf, color, rect, border_radius=6)
        pygame.draw.rect(surf, border_color, rect, 2, border_radius=6)
        txt = pause_button_font.render(label, True, (255, 255, 255))
        surf.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

    def draw_pause_menu(surf, mouse_pos):
        # ----- Blur the current game screen -----
        small = pygame.transform.smoothscale(
            surf,
            (SCREEN_W // 8, SCREEN_H // 8)
        )
        blurred = pygame.transform.smoothscale(
            small,
            (SCREEN_W, SCREEN_H)
        )
        surf.blit(blurred, (0, 0))

        # ----- Dark transparent overlay -----
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surf.blit(overlay, (0, 0))

        # ----- Center panel -----
        panel_width = min(520, int(SCREEN_W * 0.42))
        panel_height = min(420, int(SCREEN_H * 0.60))

        panel = pygame.Rect(
            (SCREEN_W - panel_width) // 2,
            (SCREEN_H - panel_height) // 2,
            panel_width,
            panel_height
        )

        pygame.draw.rect(surf, (36, 38, 48), panel, border_radius=10)
        pygame.draw.rect(surf, (90, 94, 110), panel, 3, border_radius=10)

        # ----- Title -----
        title = pause_title_font.render("PAUSED", True, (255, 255, 255))
        surf.blit(
            title,
            (
                panel.centerx - title.get_width() // 2,
                panel.top + 30
            )
        )

        # ----- Buttons -----
        for btn in pause_buttons:
            hovered = btn["rect"].collidepoint(mouse_pos)
            draw_pause_button(surf, btn["rect"], btn["label"], hovered)

    def draw_pause_settings(surf, mouse_pos):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))
        pygame.draw.rect(surf, (36, 38, 48), settings_panel_rect, border_radius=8)
        pygame.draw.rect(surf, (90, 94, 110), settings_panel_rect, 3, border_radius=8)
        title = pause_button_font.render("SETTINGS", True, (255, 255, 255))
        surf.blit(title, (settings_panel_rect.centerx - title.get_width() // 2, settings_panel_rect.top + 20))

        surf.blit(font.render("MUSIC", True, (200, 200, 210)), (music_bar.left, music_bar.top - 26))
        pygame.draw.rect(surf, (20, 22, 30), music_bar, border_radius=4)
        mx = music_bar.left + int((music_bar.width - 16) * _settings_state["music_vol"])
        pygame.draw.rect(surf, (255, 220, 120), (mx, music_bar.top - 2, 16, 18), border_radius=3)

        surf.blit(font.render("SFX", True, (200, 200, 210)), (sfx_bar.left, sfx_bar.top - 26))
        pygame.draw.rect(surf, (20, 22, 30), sfx_bar, border_radius=4)
        sx = sfx_bar.left + int((sfx_bar.width - 16) * _settings_state["sfx_vol"])
        pygame.draw.rect(surf, (255, 220, 120), (sx, sfx_bar.top - 2, 16, 18), border_radius=3)

        back_hovered = settings_back_rect.collidepoint(mouse_pos)
        draw_pause_button(surf, settings_back_rect, "BACK", back_hovered)

    running = True
    main_character = MainCharacter(screen, map_width, map_height)
    # simple enemy instance for visual testing/animation
    enemy = Enemy(screen, map_width, map_height)
    while running:
        clock.tick(60)
        mouse_pos = pygame.mouse.get_pos()

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if show_pause_settings:
                        show_pause_settings = False
                    elif paused:
                        paused = False
                    else:
                        paused = True
                elif event.key == pygame.K_F5:
                    sample_challenge = {
                        "title": "Variables",
                        "objective": "Create a variable called age and assign the value 18."
                    }
                    background_snapshot = screen.copy()
                    editor = CodeEditor(screen, sample_challenge, background_snapshot)
                    editor.run()
                elif event.key == pygame.K_F8:
                    # Dev-only preview: press F8 to see the Game Over screen,
                    # F8 again (or Esc/Enter/R/M/click) to leave it and resume
                    # gameplay right where you were.
                    background_snapshot = screen.copy()
                    game_over_screen(screen, background=background_snapshot)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if paused and not show_pause_settings:
                    for btn in pause_buttons:
                        if btn["rect"].collidepoint(event.pos):
                            if btn["action"] == "resume":
                                paused = False
                            elif btn["action"] == "settings":
                                show_pause_settings = True
                            elif btn["action"] == "main_menu":
                                pygame.mixer.music.stop()
                                return
                elif paused and show_pause_settings:
                    if music_bar.collidepoint(event.pos):
                        dragging_music = True
                    if sfx_bar.collidepoint(event.pos):
                        dragging_sfx = True
                    if settings_back_rect.collidepoint(event.pos):
                        show_pause_settings = False
                elif not paused:
                    if hud_portrait_rect.collidepoint(event.pos):
                        background_snapshot = screen.copy()
                        profile_screen(
                            screen,
                            background=background_snapshot,
                            name=profile_name,
                            hp=player_hp, max_hp=player_max_hp,
                            pp=player_pp, max_pp=player_max_pp,
                        )

            if event.type == pygame.MOUSEBUTTONUP:
                dragging_music = False
                dragging_sfx = False

        if dragging_music:
            _settings_state["music_vol"] = max(0.0, min(1.0, (mouse_pos[0] - music_bar.left) / music_bar.width))
            pygame.mixer.music.set_volume(_settings_state["music_vol"])
        if dragging_sfx:
            _settings_state["sfx_vol"] = max(0.0, min(1.0, (mouse_pos[0] - sfx_bar.left) / sfx_bar.width))

        if paused:
            screen.blit(map_surface, (-camera_x, -camera_y))
            main_character.draw_frames(ZOOM, camera_x, camera_y)
            if show_pause_settings:
                draw_pause_settings(screen, mouse_pos)
            else:
                draw_pause_menu(screen, mouse_pos)
            pygame.display.flip()
            continue
        # --- Movement ---
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy =  1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx =  1
            
        
        # Normalize diagonal movement so it's the same speed as cardinal directions
        if dx != 0 and dy != 0:
            dx *= 0.7071 # 1/sqrt(2)
            dy *= 0.7071

        dx *= player_speed
        dy *= player_speed

        # --- Collision (horizontal) ---
        player_x += dx
        player_rect.x = round(player_x)
        for rect in collision_rects:
            if player_rect.colliderect(rect):
                if dx > 0:
                    player_rect.right = rect.left
                elif dx < 0:
                    player_rect.left = rect.right
                # Only resync the float when a collision actually adjusted the rect.
                # Resyncing unconditionally every frame discards the leftover
                # sub-pixel fraction (e.g. the .5 in speed 2.5), which is what
                # was causing the inconsistent / direction-dependent speed.
                player_x = float(player_rect.x)

        # --- Collision (vertical) ---
        player_y += dy
        player_rect.y = round(player_y)
        for rect in collision_rects:
            if player_rect.colliderect(rect):
                if dy > 0:
                    player_rect.bottom = rect.top
                elif dy < 0:
                    player_rect.top = rect.bottom
                player_y = float(player_rect.y)

        # --- Keep player inside map bounds ---
        player_rect.clamp_ip(pygame.Rect(0, 0, map_width, map_height))
        player_x = float(player_rect.x)
        player_y = float(player_rect.y)

        # --- Camera ---
        camera_x, camera_y = update_camera()

        # --- Check if player is near an interactable ---
        near_interactable = None
        for item in interactables:
            # player_rect is in UNSCALED world coordinates (ZOOM is only
            # applied when drawing to the screen), so the detection rect
            # must stay unscaled too to match it.
            detection_rect = item['rect'].inflate(20, 20)

            if player_rect.colliderect(detection_rect):
                near_interactable = item
                break

        # --- Handle E key hold ---
        if near_interactable:
            if keys[pygame.K_e]:
                near_interactable['inspect_progress'] += 1 / 60 / INSPECT_TIME
                near_interactable['inspect_progress'] = min(near_interactable['inspect_progress'], 1.0)
                if near_interactable['inspect_progress'] >= 1.0:
                    near_interactable['inspecting'] = True
            else:
                near_interactable['inspect_progress'] = max(
                    0, near_interactable['inspect_progress'] - 1 / 60 / INSPECT_TIME
                )
                if not near_interactable['inspecting']:
                    near_interactable['inspect_progress'] = 0.0
        else:
            for item in interactables:
                item['inspect_progress'] = 0.0
                item['inspecting'] = False

        # --- Draw ---
        screen.blit(map_surface, (-camera_x, -camera_y))

        # Draw player (scaled position)
        # (removed red placeholder rect — sprite is drawn below via main_character.draw_frames)

        # --- Draw interaction UI ---
        if near_interactable:
            # Scale the interactable position to match the zoomed map
            cam_x = near_interactable['rect'].x * ZOOM - camera_x
            cam_y = near_interactable['rect'].y * ZOOM - camera_y - 30

            if not near_interactable['inspecting']:
                # "Hold E" prompt
                prompt = inspect_font.render("Hold E to search", True, (255, 255, 255))
                screen.blit(prompt, (cam_x, cam_y))

                # Progress bar background
                bar_w = 80
                pygame.draw.rect(screen, (50, 50, 50),
                                 (cam_x, cam_y + 22, bar_w, 8))
                # Progress bar fill
                pygame.draw.rect(screen, (255, 220, 50),
                                 (cam_x, cam_y + 22,
                                  int(bar_w * near_interactable['inspect_progress']), 8))
            else:
                # Show message based on object type
                action = near_interactable.get('actions', '')
                if action == 'search_barrel':
                    message = 'The barrel is empty.'
                elif action == 'search_burrow':
                    message = 'The burrow is empty.'
                elif action == 'search_vase':
                    message = 'The vase is empty.'
                elif action == 'search_hay':
                    message = 'The hay is empty.'
                else:
                    message = "Nothing here."
                msg = inspect_font.render(message, True, (255, 255, 255))
                box = pygame.Rect(
                    SCREEN_W // 2 - msg.get_width() // 2 - 10,
                    SCREEN_H // 2 - msg.get_height() // 2 - 10,
                    msg.get_width() + 20,
                    msg.get_height() + 20
                )
                pygame.draw.rect(screen, (20, 20, 20), box, border_radius=6)
                pygame.draw.rect(screen, (200, 200, 100), box, 2, border_radius=6)
                screen.blit(msg, (SCREEN_W // 2 - msg.get_width() // 2,
                                  SCREEN_H // 2 - msg.get_height() // 2))

                close_hint = font.render("Release E to close", True, (255, 0, 0))
                screen.blit(close_hint, (SCREEN_W // 2 - close_hint.get_width() // 2,
                                         SCREEN_H // 2 + msg.get_height()))

                if not keys[pygame.K_e]:
                    near_interactable['inspecting'] = False
                    near_interactable['inspect_progress'] = 0.0

        # Profile HUD (top-left)
        draw_profile_hud(screen, mouse_pos)

        # ESC hint (top-right, out of the way of the profile HUD)
        hint = font.render("ESC = Pause", True, (255, 255, 255))
        screen.blit(hint, (SCREEN_W - hint.get_width() - 10, 10))

        main_character.update_position(dx, dy, player_rect, player_x, player_y, collision_rects, map_width, map_height)   
        main_character.update_frames(keys)
        main_character.draw_frames(ZOOM, camera_x, camera_y)

        # Draw the enemy (animated)
        enemy.draw_frames(ZOOM, camera_x, camera_y)
        
        
        pygame.display.flip()

        