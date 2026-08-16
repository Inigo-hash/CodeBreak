from pytmx.util_pygame import load_pygame
import pygame
import sys
from src.settings_state import (
    settings_state as _settings_state,
    current_theme_name,
    cycle_theme,
    swatch_color,
)
from src.entities.player import MainCharacter
from src.entities.enemy import Enemy
from src.ui.code_editor import CodeEditor
from src.screens.game_over import game_over_screen
from src.screens.profile import profile_screen
from src.screens.inventory import PlayerInventory, Toolbar, open_inventory
from src.systems import save_manager
from src.data.zones import ZONES

def game_screen(screen, slot_num=None, save_state=None):
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
    # Float position to avoid integer truncation causing uneven movement
    player_rect.clamp_ip(pygame.Rect(0, 0, map_width, map_height))
    player_x = float(player_rect.x)
    player_y = float(player_rect.y)
    player_speed = 2.50

    # --- Restore from a save slot, if one was passed in ---
    # (map_position only for now - hearts/keys/topics/challenges are
    # carried through so they round-trip on save/load, but nothing in
    # this loop drains hearts or grants keys yet; inventory items aren't
    # restored either, since Item icons aren't currently serializable.)
    save_hearts = 5
    save_keys = 0
    save_stage = "Island"
    save_topics_completed = []
    save_challenges_passed = []

    if save_state:
        save_hearts = save_state.get("hearts", save_hearts)
        save_keys = save_state.get("keys", save_keys)
        save_stage = save_state.get("stage", save_stage)
        save_topics_completed = save_state.get("topics_completed", [])
        save_challenges_passed = save_state.get("challenges_passed", [])

        map_position = save_state.get("map_position")
        if map_position:
            player_x, player_y = float(map_position[0]), float(map_position[1])
            player_rect.x, player_rect.y = int(player_x), int(player_y)
            player_rect.clamp_ip(pygame.Rect(0, 0, map_width, map_height))
            player_x, player_y = float(player_rect.x), float(player_rect.y)

    def build_save_state():
        return {
            "stage": save_stage,
            "hearts": save_hearts,
            "keys": save_keys,
            "topics_completed": save_topics_completed,
            "challenges_passed": save_challenges_passed,
            "map_position": [player_x, player_y],
            "inventory": [],
        }

    # Feedback message shown briefly after SAVE is pressed. Frame-based
    # (this loop doesn't track dt / delta-time), so this counts down once
    # per rendered frame rather than in real seconds.
    save_message_frames = 0

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

    # Every dimension of the profile HUD is derived from this one factor, so
    # the whole panel can be resized from a single line. 1 is the original
    # size the layout numbers below were picked at.
    HUD_SCALE = 1.5

    def hud_px(value):
        # Rounded because pygame needs whole pixels — font sizes, smoothscale
        # dimensions and border radii all reject floats, so a fractional
        # HUD_SCALE would otherwise blow up here.
        return round(value * HUD_SCALE)

    hud_font_name = pygame.font.SysFont("consolas", hud_px(16), bold=True)
    hud_font_bar = pygame.font.SysFont("consolas", hud_px(12), bold=True)

    minimap_compass_font = pygame.font.SysFont("consolas", 14, bold=True)

    HUD_MARGIN = 14
    HUD_PORTRAIT_SIZE = hud_px(56)
    HUD_FRAME_PAD = hud_px(6)
    HUD_EDGE_WIDTH = hud_px(2)
    HUD_RADIUS = hud_px(4)
    hud_portrait = pygame.image.load("assets/images/logos/codebreakLogo.png").convert_alpha()
    hud_portrait = pygame.transform.smoothscale(hud_portrait, (HUD_PORTRAIT_SIZE, HUD_PORTRAIT_SIZE))
    hud_portrait_rect = pygame.Rect(HUD_MARGIN, HUD_MARGIN, HUD_PORTRAIT_SIZE, HUD_PORTRAIT_SIZE)

    HUD_BAR_WIDTH = hud_px(180)
    HUD_BAR_HEIGHT = hud_px(16)
    hud_bars_left = hud_portrait_rect.right + hud_px(10)
    hud_hp_rect = pygame.Rect(hud_bars_left, hud_portrait_rect.top + hud_px(22), HUD_BAR_WIDTH, HUD_BAR_HEIGHT)
    hud_pp_rect = pygame.Rect(hud_bars_left, hud_hp_rect.bottom + hud_px(6), HUD_BAR_WIDTH, HUD_BAR_HEIGHT)

    def draw_hud_bar(surf, rect, value, max_value, fill_color, edge_color):
        pygame.draw.rect(surf, (20, 22, 28), rect, border_radius=HUD_RADIUS)
        ratio = 0 if max_value <= 0 else max(0.0, min(1.0, value / max_value))
        fill_rect = pygame.Rect(rect.left, rect.top, int(rect.width * ratio), rect.height)
        if fill_rect.width > 0:
            pygame.draw.rect(surf, fill_color, fill_rect, border_radius=HUD_RADIUS)
        pygame.draw.rect(surf, edge_color, rect, HUD_EDGE_WIDTH, border_radius=HUD_RADIUS)
        label = hud_font_bar.render(f"{value}/{max_value}", True, (255, 255, 255))
        surf.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

    def draw_profile_hud(surf, mouse_pos):
        frame_rect = hud_portrait_rect.inflate(HUD_FRAME_PAD, HUD_FRAME_PAD)
        pygame.draw.rect(surf, (20, 20, 26), frame_rect, border_radius=HUD_RADIUS)
        surf.blit(hud_portrait, hud_portrait_rect)
        hovered = hud_portrait_rect.collidepoint(mouse_pos)
        frame_color = (255, 220, 120) if hovered else (90, 94, 110)
        pygame.draw.rect(surf, frame_color, frame_rect, HUD_EDGE_WIDTH, border_radius=HUD_RADIUS)

        name_surf = hud_font_name.render(profile_name, True, (240, 240, 240))
        surf.blit(name_surf, (hud_bars_left, hud_portrait_rect.top))

        draw_hud_bar(surf, hud_hp_rect, player_hp, player_max_hp, (200, 40, 40), (255, 90, 90))
        draw_hud_bar(surf, hud_pp_rect, player_pp, player_max_pp, (210, 175, 40), (255, 220, 120))

    # --- Inventory system ---
    # One PlayerInventory object holds every item the player owns. The Toolbar
    # (bottom-centre hotbar) and the B-key bag screen both read from it, so
    # they can never fall out of sync. It starts empty for now; drop items in
    # later with player_inventory.add_item(Item("Name")).
    player_inventory = PlayerInventory()
    toolbar = Toolbar(screen, player_inventory)

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
        return surf

    raw_map_surface = render_map_surface()
    # Scale the pre-rendered map once at startup based on ZOOM level (e.g. ZOOM=2 doubles the size)
    # This avoids rescaling every frame which would slow down the game
    map_surface = pygame.transform.scale(raw_map_surface, (map_width * ZOOM, map_height * ZOOM))

    # --- Minimap ---
    # Pre-bake the whole map once at minimap resolution (same idea as
    # map_surface above) so drawing it per-frame is just a cheap clipped
    # blit rather than a rescale. The camera never rotates — it's the
    # same fixed birds-eye view as the main game — so "panning" is just
    # a straight crop centered on the player, no texture rotation needed.
    MINIMAP_SIZE = max(150, min(220, int(SCREEN_H * 0.22)))
    MINIMAP_MARGIN = 14
    # Taken from the map's own water tiles, so the area past the map edge
    # blends into the real coastline instead of reading as a flat backdrop.
    MINIMAP_SEA_COLOR = (44, 232, 244)
    MINIMAP_SPAN_FACTOR = 1.5  # how much wider the minimap's view is than the player's own screen view
    minimap_px_per_unit = MINIMAP_SIZE / ((max(SCREEN_W, SCREEN_H) / ZOOM) * MINIMAP_SPAN_FACTOR)

    # Object Layer 1 (trees, etc.) is drawn per-frame as depth-sorted
    # dynamic_props rather than baked into raw_map_surface, so on its own
    # raw_map_surface is missing those objects. Bake them into a separate
    # copy just for the minimap texture so the main game's map_surface
    # (which is derived from raw_map_surface) doesn't end up with a
    # duplicate, non-depth-sorted copy of every tree.
    minimap_base_surface = raw_map_surface.copy()
    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'name') and layer.name == "Object Layer 1":
            for obj in layer:
                gid = getattr(obj, 'gid', None)
                if not gid:
                    continue
                tile_image = tmx_data.get_tile_image_by_gid(gid)
                if tile_image:
                    minimap_base_surface.blit(tile_image, (obj.x, obj.y - obj.height))

    minimap_texture = pygame.transform.smoothscale(
        minimap_base_surface,
        (
            max(1, int(map_width * minimap_px_per_unit)),
            max(1, int(map_height * minimap_px_per_unit)),
        )
    )

    # Player marker: a GTA-style white arrowhead. It takes a heading vector
    # straight off the movement input rather than the character's `facing`,
    # which only tracks the four cardinals it has sprite sets for — that way
    # the arrow covers the diagonals (NE/NW/SE/SW) as well.
    MINIMAP_ARROW_SIZE = 8

    # --- Zone Labels ---
    # Converts each zone's fractional rect (from zones.py) into a
    # real pixel rect once, using this map's actual dimensions.
    zone_pixel_rects = []
    for zone in ZONES:
        frac_x, frac_y, frac_w, frac_h = zone["rect"]
        zone_pixel_rects.append({
            "name": zone["name"],
            "is_boss_zone": zone.get("is_boss_zone", False),
            "rect": pygame.Rect(
                frac_x * map_width,
                frac_y * map_height,
                frac_w * map_width,
                frac_h * map_height
            )
        })

    zone_label_font = pygame.font.SysFont("consolas", 11, bold=True)

    def draw_minimap(surf, player_rect, heading):
        panel_rect = pygame.Rect(
            MINIMAP_MARGIN,
            SCREEN_H - MINIMAP_MARGIN - MINIMAP_SIZE,
            MINIMAP_SIZE,
            MINIMAP_SIZE
        )

        # Background shows through wherever the crop runs past the edge
        # of the map (e.g. the player standing near the map border).
        # Sampled straight from the map's own water tiles so the
        # out-of-bounds area reads as the sea continuing past the edge
        # instead of an obvious flat panel behind the map.
        pygame.draw.rect(surf, MINIMAP_SEA_COLOR, panel_rect)

        # The minimap-texture pixel the player is standing on, cropped so
        # that pixel lands dead-center in the panel — this is what makes
        # the minimap pan while keeping the player marker fixed in place.
        mm_x = player_rect.centerx * minimap_px_per_unit
        mm_y = player_rect.centery * minimap_px_per_unit
        src_left = mm_x - MINIMAP_SIZE / 2
        src_top = mm_y - MINIMAP_SIZE / 2

        prev_clip = surf.get_clip()
        surf.set_clip(panel_rect)
        surf.blit(minimap_texture, (panel_rect.left - src_left, panel_rect.top - src_top))
        surf.set_clip(prev_clip)

        # ----------------------------------
        # Zone Name Labels
        # ----------------------------------
        # Reuses the same crop math as the map texture above, so a
        # zone's label lines up with the terrain it's naming even
        # as the minimap pans with the player.

        surf.set_clip(panel_rect)

        for zone in zone_pixel_rects:

            zone_center_x = zone["rect"].centerx * minimap_px_per_unit
            zone_center_y = zone["rect"].centery * minimap_px_per_unit

            label_x = panel_rect.left - src_left + zone_center_x
            label_y = panel_rect.top - src_top + zone_center_y

            label_color = (
                (255, 210, 90) if zone["is_boss_zone"] else (230, 230, 230)
            )

            shadow = zone_label_font.render(zone["name"], True, (0, 0, 0))
            label = zone_label_font.render(zone["name"], True, label_color)

            surf.blit(
                shadow,
                (label_x - label.get_width() // 2 + 1, label_y - label.get_height() // 2 + 1)
            )
            surf.blit(
                label,
                (label_x - label.get_width() // 2, label_y - label.get_height() // 2)
            )

        surf.set_clip(prev_clip)

        # Compass letters fixed to the panel edges — the view never
        # rotates, so N is always "up" here just like on the main screen.
        for label, (lx, ly) in (
            ("N", (panel_rect.centerx, panel_rect.top + 11)),
            ("S", (panel_rect.centerx, panel_rect.bottom - 11)),
            ("W", (panel_rect.left + 11, panel_rect.centery)),
            ("E", (panel_rect.right - 11, panel_rect.centery)),
        ):
            shadow = minimap_compass_font.render(label, True, (0, 0, 0))
            txt = minimap_compass_font.render(label, True, (235, 220, 180))
            surf.blit(shadow, (lx - txt.get_width() // 2 + 1, ly - txt.get_height() // 2 + 1))
            surf.blit(txt, (lx - txt.get_width() // 2, ly - txt.get_height() // 2))

        # Player marker — always dead-center, since the crop above keeps
        # the player's world position pinned to the middle of the panel.
        # Points are laid out along the heading vector (how far forward)
        # and across it (how far out to the side): a long tip against a
        # narrow tail, with a notch cut into the back so the pointed end
        # is unmistakable. Turns with the character's facing.
        hx, hy = heading
        px, py = -hy, hx  # perpendicular to the heading
        cx, cy = panel_rect.center

        def arrow_point(along, across):
            return (cx + (hx * along + px * across) * MINIMAP_ARROW_SIZE,
                    cy + (hy * along + py * across) * MINIMAP_ARROW_SIZE)

        arrow = (
            arrow_point(1.15, 0),      # tip
            arrow_point(-0.7, 0.62),   # back corner
            arrow_point(-0.42, 0),     # notch, pulled forward between them
            arrow_point(-0.7, -0.62),  # back corner
        )
        pygame.draw.polygon(surf, (255, 255, 255), arrow)
        pygame.draw.polygon(surf, (30, 30, 30), arrow, 1)

        pygame.draw.rect(surf, (90, 94, 110), panel_rect, 3)

    # --- Dynamic props (tile objects requiring per-frame depth sorting) ---
    dynamic_props = []
    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'name') and layer.name == "Object Layer 1":
            for obj in layer:
                gid = getattr(obj, 'gid', None)
                if not gid:
                    continue
                tile_image = tmx_data.get_tile_image_by_gid(gid)
                if not tile_image:
                    continue
                dynamic_props.append({
                    'image': pygame.transform.scale(
                        tile_image, (int(obj.width * ZOOM), int(obj.height * ZOOM))
                    ),
                    'x': obj.x * ZOOM,
                    'y': (obj.y - obj.height) * ZOOM,
                    'sort_y': obj.y
                })

    # --- Pause menu setup ---
    paused = False
    show_pause_settings = False

    PAUSE_MENU_OPTIONS = [
        ("RESUME", "resume"),
        ("SAVE GAME", "save"),
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
    # Taller than the old two-slider panel so the COLOR THEME row below
    # has room to sit between SFX and the BACK button.
    panel_height = min(430, int(SCREEN_H * 0.58))

    settings_panel_rect = pygame.Rect(
        (SCREEN_W - panel_width) // 2,
        (SCREEN_H - panel_height) // 2,
        panel_width,
        panel_height
    )
    padding = 30

    music_bar = pygame.Rect(
        settings_panel_rect.left + padding,
        settings_panel_rect.top + int(settings_panel_rect.height * 0.28),
        settings_panel_rect.width - padding * 2,
        14
    )

    sfx_bar = pygame.Rect(
        settings_panel_rect.left + padding,
        settings_panel_rect.top + int(settings_panel_rect.height * 0.46),
        settings_panel_rect.width - padding * 2,
        14
    )

    # COLOR THEME row: a pair of arrows with the current theme's name
    # between them, matching the picker in the main menu's settings.
    theme_arrow_y = settings_panel_rect.top + int(settings_panel_rect.height * 0.66)

    theme_left_rect = pygame.Rect(
        settings_panel_rect.left + padding, theme_arrow_y, 40, 28
    )

    theme_right_rect = pygame.Rect(
        settings_panel_rect.right - padding - 40, theme_arrow_y, 40, 28
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
        # ----- Buttons -----
        for btn in pause_buttons:
            hovered = btn["rect"].collidepoint(mouse_pos)
            draw_pause_button(surf, btn["rect"], btn["label"], hovered)

        # ----- Save feedback -----
        if save_message_frames > 0:
            if slot_num is not None:
                msg, color = "Game saved.", (120, 220, 140)
            else:
                msg, color = "No save slot active - can't save here.", (230, 120, 120)
            msg_surf = font.render(msg, True, color)
            surf.blit(
                msg_surf,
                (panel.centerx - msg_surf.get_width() // 2, panel.bottom - 34)
            )

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

        # --- COLOR THEME (restyles the coding environment only) ---
        surf.blit(
            font.render("COLOR THEME", True, (200, 200, 210)),
            (theme_left_rect.left, theme_arrow_y - 26)
        )

        for rect in (theme_left_rect, theme_right_rect):
            hovered = rect.collidepoint(mouse_pos)
            pygame.draw.rect(
                surf,
                (60, 90, 130) if hovered else (50, 55, 70),
                rect,
                border_radius=4
            )

        arrow_left = [
            (theme_left_rect.right - 8, theme_left_rect.top + 6),
            (theme_left_rect.right - 8, theme_left_rect.bottom - 6),
            (theme_left_rect.left + 6, theme_left_rect.centery),
        ]
        arrow_right = [
            (theme_right_rect.left + 8, theme_right_rect.top + 6),
            (theme_right_rect.left + 8, theme_right_rect.bottom - 6),
            (theme_right_rect.right - 6, theme_right_rect.centery),
        ]
        pygame.draw.polygon(surf, (80, 180, 255), arrow_left)
        pygame.draw.polygon(surf, (80, 180, 255), arrow_right)

        theme_name = current_theme_name()
        theme_label = font.render(theme_name, True, swatch_color(theme_name))
        surf.blit(
            theme_label,
            (
                settings_panel_rect.centerx - theme_label.get_width() // 2,
                theme_arrow_y + 14 - theme_label.get_height() // 2
            )
        )

        back_hovered = settings_back_rect.collidepoint(mouse_pos)
        draw_pause_button(surf, settings_back_rect, "BACK", back_hovered)

    running = True
    # Matches MainCharacter's own starting facing, so the arrow agrees with
    # the sprite before the player has moved at all.
    minimap_heading = (1, 0)
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

            # Let the hotbar claim its own input first (number keys 1-5, mouse
            # wheel and clicks on a slot). Only while actually playing - the
            # pause menu should not have its clicks stolen. handle_event()
            # returns True when it used the event, so we skip the rest below.
            if not paused and toolbar.handle_event(event):
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b and not paused:
                    # B opens the bag. Freeze the current frame and hand that
                    # snapshot to the inventory screen so it has something to
                    # blur while it slides up.
                    background_snapshot = screen.copy()
                    open_inventory(screen, player_inventory, background_snapshot)

                elif event.key == pygame.K_ESCAPE:
                    if show_pause_settings:
                        show_pause_settings = False
                    elif paused:
                        paused = False
                    else:
                        paused = True

                elif event.key == pygame.K_F5:
                    sample_challenge = {
                        "title": "Variables",
                        "objective": "Create a variable called age and assign the value 18.",
                        "type": "variable",
                        "expected": {
                            "name": "age",
                            "value": 18
                        }
                    }
                    background_snapshot = screen.copy()
                    editor = CodeEditor(screen, sample_challenge, background_snapshot)
                    editor.run()

                elif event.key == pygame.K_F6:
                    # Debug: prints the player's position as a
                    # fraction of the map, for placing zone rects
                    # in zones.py accurately.
                    frac_x = player_rect.centerx / map_width
                    frac_y = player_rect.centery / map_height
                    print(f"Zone debug position: ({frac_x:.2f}, {frac_y:.2f})")
                    
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
                            elif btn["action"] == "save":
                                if slot_num is not None:
                                    save_manager.save_slot(slot_num, build_save_state())
                                save_message_frames = 96  # ~1.6s at 60fps
                            elif btn["action"] == "settings":
                                show_pause_settings = True
                            elif btn["action"] == "main_menu":
                                pygame.mixer.music.stop()
                                return "main_menu"
                elif paused and show_pause_settings:
                    if music_bar.collidepoint(event.pos):
                        dragging_music = True
                    if sfx_bar.collidepoint(event.pos):
                        dragging_sfx = True
                    # Shared with the main menu's picker, so both panels
                    # always agree on the selected theme.
                    if theme_left_rect.collidepoint(event.pos):
                        cycle_theme(-1)
                    if theme_right_rect.collidepoint(event.pos):
                        cycle_theme(1)
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
            if paused:
                screen.blit(map_surface, (-camera_x, -camera_y))
                main_character.draw_frames(ZOOM, camera_x, camera_y)
                # Draw the hotbar before the pause overlay so it gets blurred
                # along with the rest of the scene instead of vanishing.
                toolbar.draw()
                if show_pause_settings:
                    draw_pause_settings(screen, mouse_pos)
                else:
                    draw_pause_menu(screen, mouse_pos)
                    if save_message_frames > 0:
                        save_message_frames -= 1
                pygame.display.flip()
                continue
        # --- Movement ---
        keys = pygame.key.get_pressed()

        up = keys[pygame.K_w] or keys[pygame.K_UP]
        down = keys[pygame.K_s] or keys[pygame.K_DOWN]
        left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        right = keys[pygame.K_d] or keys[pygame.K_RIGHT]

        if up and down:
            up = down = False
        if left and right:
            left = right = False

        dx, dy = 0, 0
        if up:
            dy = -1
        if down:
            dy = 1
        if left:
            dx = -1
        if right:
            dx = 1
            
        
        # Normalize diagonal movement so it's the same speed as cardinal directions
        if dx != 0 and dy != 0:
            dx *= 0.7071 # 1/sqrt(2)
            dy *= 0.7071

        # Feed the minimap arrow off the movement input, which already covers
        # all eight directions. It's a unit vector at this point (the diagonal
        # normalization above is exactly what makes it one), so the arrow comes
        # out the same length whichever way it points. Held over when standing
        # still so the marker keeps the last direction walked.
        if dx or dy:
            minimap_heading = (dx, dy)

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

        main_character.update_position(dx, dy, player_rect, player_x, player_y, collision_rects, map_width, map_height)   
        main_character.update_frames(keys)

        # --- Depth-sorted draw pass (painter's algorithm) ---
        draw_list = [('prop', p['sort_y'], p) for p in dynamic_props]
        draw_list.append(('player', player_rect.bottom, None))
        draw_list.append(('enemy', enemy.center_y, None))
        draw_list.sort(key=lambda entry: entry[1])

        for kind, _, prop in draw_list:
            if kind == 'prop':
                screen.blit(prop['image'], (prop['x'] - camera_x, prop['y'] - camera_y))
            elif kind == 'player':
                main_character.draw_frames(ZOOM, camera_x, camera_y)
            elif kind == 'enemy':
                enemy.draw_frames(ZOOM, camera_x, camera_y)

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
                elif action == 'search_crate':
                    message = 'The crate is empty.'
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

        # Minimap (bottom-left)
        draw_minimap(screen, player_rect, minimap_heading)

        # Hotbar (bottom-centre). Drawn after the world and the HUD so it
        # always sits on top of everything else in the scene.
        toolbar.draw(mouse_pos)

        # Key hints (top-right, out of the way of the profile HUD)
        hint = font.render("ESC = Pause    B = Inventory", True, (255, 255, 255))
        screen.blit(hint, (SCREEN_W - hint.get_width() - 10, 10))

        pygame.display.flip()

        