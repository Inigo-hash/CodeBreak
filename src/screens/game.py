from pytmx.util_pygame import load_pygame
import pygame
import sys
import random
from src.config import DEBUG
from src.settings_state import settings_state as _settings_state
from src.screens.settings import SettingsPanel
from src.entities.player import MainCharacter
from src.entities.enemy import Enemy
from src.ui.code_editor import CodeEditor
from src.screens.game_over import game_over_screen
from src.screens.profile import profile_screen
from src.screens.inventory import PlayerInventory, Toolbar, open_inventory
from src.screens.stage_info import open_stage_info
from src.screens.world_map import open_world_map
from src.systems import save_manager
from src.systems.stage_progress import StageProgress
from src.ui.stage_panel import StagePanel
from src.ui.gameplay_hud import (
    GameplayHUD, MINIMAP_FRAME, build_minimap_frame, build_view_vignette,
)
from src.ui.chart import (
    BOSS_INK, INK, build_chart_texture, build_night_veil, build_sea_tile,
    chart_sea_color, draw_marker, fill_sea, ink_text,
)
from src.systems.combat import (
    COMBAT_DEBUG, DEBUG_ENEMY_AI, FACING_VECTORS, PLAYER_DODGE_SPEED,
    PlayerCombat, attack_hitbox, attack_path_blocked, move_rect,
    selected_weapon_damage,
)
from src.systems.audio import CombatAudio
from src.data.zones import ZONES, get_zone_at
from src.data.stages import get_stage
from src.screens.topic_found import open_topic_found
from src.data.topics import get_topic
from src.data.challenges import get_challenge
from src.screens.topic_lesson import open_topic_lesson
from src.data.encounters import BEGINNER_PATH_GIDS, BEGINNER_STAGE_ENCOUNTERS
from src.systems.enemy_spawns import resolve_encounter_spawns
from src.ui.theme import UI_COLORS, body_font, draw_button, draw_panel, title_font

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

    # Pytmx assigns its own runtime IDs to authored TMX gids. Convert the
    # known dirt-path IDs before comparing them with layer iteration values.
    runtime_path_gids = {
        runtime_gid
        for authored_gid in BEGINNER_PATH_GIDS
        for runtime_gid, _flags in tmx_data.map_gid(authored_gid)
    }

    # --- Build collision rects from tile custom properties ---
    collision_rects = []
    path_cells = set()
    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'data'):
            for x, y, gid in layer:
                if gid == 0:
                    continue
                if layer.name == "Ground Layer 1" and gid in runtime_path_gids:
                    path_cells.add((x, y))
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

    # --- Load interactive objects from all object layers ---
    interactables = []

    for layer in tmx_data.visible_layers:

        # Tile layers have "data", object layers do not
        if hasattr(layer, 'data'):
            continue

        for obj in layer:

            if obj.properties.get('types') != 'interactive':
                continue

            interactables.append({
                'rect': pygame.Rect(
                    int(obj.x),
                    int(obj.y),
                    int(obj.width),
                    int(obj.height)
                ),

                'actions': obj.properties.get('actions'),
                'topic_id': obj.properties.get('topic_id'),

                'inspecting': False,
                'inspect_progress': 0.0,

                'topic_handled': False
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
    stage_spawn = player_rect.topleft
    player_speed = 2.50

    # --- Restore from a save slot, if one was passed in ---
    # (map_position only for now - hearts/keys/topics/challenges are
    # carried through so they round-trip on save/load, but nothing in
    # this loop drains hearts or grants keys yet; inventory items aren't
    # restored either, since Item icons aren't currently serializable.)
    gameplay_state = {
        "hearts": 5, "keys": 0, "topics_completed": [], "bonus_time": 0,
    }
    save_stage = "Island"
    save_challenges_passed = []
    save_stage_progress = None

    if save_state:
        gameplay_state["hearts"] = save_state.get("hearts", gameplay_state["hearts"])
        gameplay_state["keys"] = save_state.get("keys", gameplay_state["keys"])
        save_stage = save_state.get("stage", save_stage)
        gameplay_state["topics_completed"] = list(save_state.get("topics_completed", []))
        gameplay_state["bonus_time"] = save_state.get("bonus_time", 0)
        save_challenges_passed = save_state.get("challenges_passed", [])
        save_stage_progress = save_state.get("stage_progress")

        map_position = save_state.get("map_position")
        if map_position:
            player_x, player_y = float(map_position[0]), float(map_position[1])
            player_rect.x, player_rect.y = int(player_x), int(player_y)
            player_rect.clamp_ip(pygame.Rect(0, 0, map_width, map_height))
            player_x, player_y = float(player_rect.x), float(player_rect.y)

    # --- Stage information (right-hand HUD panel) ---
    # `stage` is the static description of this stage - its manual, enemy
    # and item lists, and objectives. `stage_progress` is what this player
    # has found so far, and is what decides whether the panel prints a
    # real entry or a "???" placeholder.
    stage = get_stage(save_stage)
    stage_progress = StageProgress.from_dict(save_stage_progress)
    # Catches up on anything already satisfied by an older save (e.g. a
    # challenge passed before objectives existed).
    stage_progress.sync_objectives(stage, save_challenges_passed)

    def build_save_state():
        return {
            "stage": save_stage,
            "hearts": gameplay_state["hearts"],
            "keys": gameplay_state["keys"],
            "topics_completed": gameplay_state["topics_completed"],
            "bonus_time": gameplay_state["bonus_time"],
            "challenges_passed": save_challenges_passed,
            "map_position": [player_x, player_y],
            "inventory": [],
            "weapon_obtained": player_inventory.weapon_obtained,
            "weapon_equipped": player_inventory.weapon_equipped,
            "stage_progress": stage_progress.to_dict(),
        }

    # Feedback message shown briefly after SAVE is pressed. Frame-based
    # (this loop doesn't track dt / delta-time), so this counts down once
    # per rendered frame rather than in real seconds.
    save_message_frames = 0

    # --- Fonts ---
    font = body_font(18)
    inspect_font = body_font(20)
    pause_title_font = title_font(max(28, int(SCREEN_H * 0.045)))
    pause_button_font = title_font(24)
    INSPECT_TIME = 2.0  # seconds to hold E

    # --- Gameplay HUD (top-left live counters) ---
    profile_name = "Bobiles the explorer the great"
    # --- Inventory system ---
    # One PlayerInventory object holds every item the player owns. The Toolbar
    # (bottom-centre hotbar) and the B-key bag screen both read from it, so
    # they can never fall out of sync. Equipment is intentionally limited to
    # the game's single sword; discovered topics still use the bag.
    player_inventory = PlayerInventory()
    # Existing saves predate these flags and already began with the sword, so
    # they migrate as obtained/equipped. New-game state supplies them too.
    player_inventory.set_weapon_state(
        True if save_state is None else save_state.get("weapon_obtained", True),
        True if save_state is None else save_state.get("weapon_equipped", True),
    )
    toolbar = Toolbar(screen, player_inventory)
    gameplay_hud = GameplayHUD(
        screen, gameplay_state, stage, player_inventory,
        completed_stage_topics=save_challenges_passed,
    )

    # Objectives tracker + the rail of buttons that opens the full Stage
    # Information screen. Holds `stage` and `stage_progress` by reference,
    # so the tracker updates itself as objectives complete.
    stage_panel = StagePanel(screen, stage, stage_progress)

    def open_topic_flow(
        topic_id,
        background
    ):
        """
        Open a topic lesson and, if requested,
        launch its coding challenge.

        Used by both:
            - newly discovered world topics
            - stored inventory topics
        """

        topic = get_topic(
            topic_id
        )

        if topic is None:

            print(
                f"Unknown topic id: {topic_id}"
            )

            return "close"

        # -----------------------------------------------------
        # Topic Lesson
        # -----------------------------------------------------

        lesson_result = open_topic_lesson(
            screen,
            topic,
            background
        )

        if lesson_result != "challenge":

            return "close"

        # -----------------------------------------------------
        # Find challenge belonging to topic
        # -----------------------------------------------------

        challenge_id = topic.get(
            "challenge_id"
        )

        challenge = get_challenge(
            challenge_id
        )

        if challenge is None:

            print(
                f"Challenge not found: {challenge_id}"
            )

            return "close"

        # -----------------------------------------------------
        # Coding Environment
        # -----------------------------------------------------

        editor_background = screen.copy()

        editor = CodeEditor(
            screen,
            challenge,
            editor_background
        )

        editor.run()

        # -----------------------------------------------------
        # Challenge completion
        # -----------------------------------------------------

        if editor.solved:

            first_completion = (
                challenge_id
                not in save_challenges_passed
            )

            if first_completion:

                save_challenges_passed.append(
                    challenge_id
                )

                gameplay_state["keys"] = min(
                    5,
                    gameplay_state["keys"] + 1
                )

            if (
                topic_id
                not in gameplay_state["topics_completed"]
            ):

                gameplay_state[
                    "topics_completed"
                ].append(
                    topic_id
                )

            stage_progress.sync_objectives(
                stage,
                save_challenges_passed
            )

        return "editor_closed"

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
    #
    # What gets baked is the *chart*, not the world art: parchment and
    # sepia ink, from the same builder the paper map uses (ui/chart.py).
    # The minimap is a piece of the map the character is carrying, so it
    # should no more look like the ground than a real map does.
    MINIMAP_SIZE = max(150, min(220, int(SCREEN_H * 0.22)))
    MINIMAP_MARGIN = 14
    # The carved frame eats into the panel rather than growing it, so the
    # minimap keeps the screen footprint it always had.
    MINIMAP_VIEW = MINIMAP_SIZE - MINIMAP_FRAME * 2
    MINIMAP_SPAN_FACTOR = 1.5  # how much wider the minimap's view is than the player's own screen view
    # Scaled against the viewport, not the panel, so the frame costs
    # resolution rather than changing how much world is on show.
    minimap_px_per_unit = MINIMAP_VIEW / ((max(SCREEN_W, SCREEN_H) / ZOOM) * MINIMAP_SPAN_FACTOR)

    # Object layers containing trees, props, etc. are drawn per-frame
    # as depth-sorted dynamic props rather than baked into raw_map_surface.
    # dynamic_props rather than baked into raw_map_surface, so on its own
    # raw_map_surface is missing those objects. Bake them into a separate
    # copy just for the minimap texture so the main game's map_surface
    # (which is derived from raw_map_surface) doesn't end up with a
    # duplicate, non-depth-sorted copy of every tree.
    minimap_base_surface = raw_map_surface.copy()

    for layer in tmx_data.visible_layers:
        # Skip tile layers; we only want object layers here
        if hasattr(layer, 'data'):
            continue

        for obj in layer:
            gid = getattr(obj, 'gid', None)

            # Ignore objects that don't have a tile image
            if not gid:
                continue

            tile_image = tmx_data.get_tile_image_by_gid(gid)

            if tile_image:
                minimap_base_surface.blit(
                    tile_image,
                    (obj.x, obj.y - obj.height)
                )

    # No torn edge or margins on this one, unlike the sheet M opens: the
    # minimap crops a window out of it, and a paper edge inside the stone
    # frame would read as a gap rather than as a worn map.
    minimap_texture = build_chart_texture(
        minimap_base_surface,
        (
            max(1, int(map_width * minimap_px_per_unit)),
            max(1, int(map_height * minimap_px_per_unit)),
        )
    )

    # Wherever the crop runs past the coast, the chart's own water
    # carries on - the sea tone taken from the chart itself, hatched with
    # the wave dashes an old map would use, so the paper appears to
    # continue past the island instead of stopping at a panel colour.
    minimap_sea_tile = build_sea_tile(chart_sea_color(minimap_texture))

    # Player marker: a GTA-style arrowhead, in the map's red ink so it
    # matches the one on the paper sheet. It takes a heading vector
    # straight off the movement input rather than the character's `facing`,
    # which only tracks the four cardinals it has sprite sets for — that way
    # the arrow covers the diagonals (NE/NW/SE/SW) as well.
    MINIMAP_ARROW_SIZE = 8

    # Chrome that never changes: the carved surround and the vignette that
    # beds the terrain into it. Built here, blitted per frame. The vignette
    # is warmed to a burnt brown, since it is now shading paper rather
    # than the cold terrain art it was tuned against.
    minimap_frame = build_minimap_frame((MINIMAP_SIZE, MINIMAP_SIZE))
    minimap_vignette = build_view_vignette(
        (MINIMAP_VIEW, MINIMAP_VIEW), color=(48, 30, 14), strength=110
    )

    # Nightfall on the minimap: the same even wash the paper map uses, so
    # the two agree about how dark it is.
    minimap_night_veil = build_night_veil((MINIMAP_VIEW, MINIMAP_VIEW))

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

    zone_label_font = title_font(11, bold=False)

    def draw_minimap(surf, player_rect, heading, night=False):
        panel_rect = pygame.Rect(
            MINIMAP_MARGIN,
            SCREEN_H - MINIMAP_MARGIN - MINIMAP_SIZE,
            MINIMAP_SIZE,
            MINIMAP_SIZE
        )
        # The terrain lives inside the frame; everything that used to be
        # measured against the panel is measured against this instead.
        view_rect = panel_rect.inflate(-MINIMAP_FRAME * 2, -MINIMAP_FRAME * 2)

        # The minimap-texture pixel the player is standing on, cropped so
        # that pixel lands dead-center in the panel — this is what makes
        # the minimap pan while keeping the player marker fixed in place.
        mm_x = player_rect.centerx * minimap_px_per_unit
        mm_y = player_rect.centery * minimap_px_per_unit
        src_left = mm_x - MINIMAP_VIEW / 2
        src_top = mm_y - MINIMAP_VIEW / 2

        # Open water first, wherever the crop runs past the coast (e.g.
        # the player standing near the map border). Phased by the same
        # crop offset as the chart, so the waves stay pinned to the world
        # and hold still while the map pans over them.
        fill_sea(surf, view_rect, minimap_sea_tile, (src_left, src_top))

        prev_clip = surf.get_clip()
        surf.set_clip(view_rect)
        surf.blit(minimap_texture, (view_rect.left - src_left, view_rect.top - src_top))
        surf.set_clip(prev_clip)

        # ----------------------------------
        # Zone Name Labels
        # ----------------------------------
        # Reuses the same crop math as the map texture above, so a
        # zone's label lines up with the terrain it's naming even
        # as the minimap pans with the player.

        surf.set_clip(view_rect)

        # Terrain first, then the vignette, then the names: a label drawn
        # under the vignette would be dimmed by it right where the crop is
        # busiest, which is the opposite of what it is there for. Night
        # comes after all three — it is the light the whole chart is being
        # read in, names included, not a filter on the terrain alone.
        surf.blit(minimap_vignette, view_rect.topleft)

        for zone in zone_pixel_rects:

            zone_center_x = zone["rect"].centerx * minimap_px_per_unit
            zone_center_y = zone["rect"].centery * minimap_px_per_unit

            label_x = view_rect.left - src_left + zone_center_x
            label_y = view_rect.top - src_top + zone_center_y

            # Same ink hand as the paper map: a parchment halo carrying
            # brown ink, boss ground in red. The halo is tighter and
            # thinner than the sheet's - at this size a full one covers
            # most of the zone it is naming.
            ink_text(
                surf, zone_label_font, zone["name"], (label_x, label_y),
                BOSS_INK if zone["is_boss_zone"] else INK,
                halo_alpha=120, halo_pad=(8, 4)
            )

        if night:
            surf.blit(minimap_night_veil, view_rect.topleft)

        surf.set_clip(prev_clip)

        # Player marker — always dead-center, since the crop above keeps
        # the player's world position pinned to the middle of the panel.
        # Drawn by the shared chart code, so it is the same arrowhead,
        # pointing the same way, as the one on the paper map — and drawn
        # over the night, since where you are has to stay findable after
        # dark.
        draw_marker(surf, view_rect.center, heading, MINIMAP_ARROW_SIZE)

        # The surround goes on last: it is the thing the terrain is
        # clipped into, so it has to cover the crop's edges.
        surf.blit(minimap_frame, panel_rect.topleft)

    # --- Dynamic props ---
    dynamic_props = []

    for layer in tmx_data.visible_layers:

        if hasattr(layer, 'data'):
            continue

        for obj in layer:
            gid = getattr(obj, 'gid', None)

            if not gid:
                continue

            tile_image = tmx_data.get_tile_image_by_gid(gid)

            if not tile_image:
                continue

            dynamic_props.append({
                'image': pygame.transform.scale(
                    tile_image,
                    (int(obj.width * ZOOM), int(obj.height * ZOOM))
                ),
                'x': obj.x * ZOOM,
                'y': (obj.y - obj.height) * ZOOM,
                'sort_y': obj.y
            })

    # --- Pause menu setup ---
    paused = False
    # The frame the world was on when the player paused, already blurred.
    # The menu is drawn over this rather than over a freshly rendered
    # scene - see the note in the paused branch of the loop below.
    pause_snapshot = None
    show_pause_settings = False
    # Debug day/night preview.
    night_mode = False

    night_overlay = pygame.Surface(
        (SCREEN_W, SCREEN_H),
        pygame.SRCALPHA
    )

    night_overlay.fill(
        (8, 15, 40, 200)
    )

    # ---------------------------------------------------------
    # Debug fog preview
    # ---------------------------------------------------------

    fog_mode = False

    # Fog movement through the world.
    fog_drift_x = 0.0
    fog_drift_y = 0.0

    # Pixels per second.
    fog_speed_x = 18.0
    fog_speed_y = 4.0

    def create_fog_texture(width, height, seed=7):
        """
        Creates a smoother, softer fog texture.

        Uses two low-contrast noise layers and smoothscales them
        multiple times so the fog looks more cloudy and less blotchy.
        """

        def build_layer(small_w, small_h, max_alpha, layer_seed):
            rng = random.Random(layer_seed)

            small = pygame.Surface(
                (small_w, small_h),
                pygame.SRCALPHA
            )

            for y in range(small_h):
                for x in range(small_w):

                    # Lower contrast = smoother fog
                    alpha = rng.randint(0, max_alpha)

                    small.set_at(
                        (x, y),
                        (205, 215, 220, alpha)
                    )

            # First upscale
            layer = pygame.transform.smoothscale(
                small,
                (width, height)
            )

            # Smooth it even more by shrinking and enlarging again
            layer = pygame.transform.smoothscale(
                pygame.transform.smoothscale(
                    layer,
                    (
                        max(1, width // 2),
                        max(1, height // 2)
                    )
                ),
                (width, height)
            )

            return layer

        # Large soft fog shapes
        base_layer = build_layer(
            28,   # smaller = softer / broader fog
            20,
            26,   # lower alpha = smoother
            seed
        )

        # Light secondary detail so it doesn't look too flat
        detail_layer = build_layer(
            52,
            36,
            14,
            seed + 99
        )

        # Blend them together
        base_layer.blit(
            detail_layer,
            (0, 0),
            special_flags=pygame.BLEND_RGBA_ADD
        )

        # -----------------------------------------------------
        # Create mirrored seamless texture
        # -----------------------------------------------------

        fog = pygame.Surface(
            (width * 2, height * 2),
            pygame.SRCALPHA
        )

        fog.blit(
            base_layer,
            (0, 0)
        )

        fog.blit(
            pygame.transform.flip(
                base_layer,
                True,
                False
            ),
            (width, 0)
        )

        fog.blit(
            pygame.transform.flip(
                base_layer,
                False,
                True
            ),
            (0, height)
        )

        fog.blit(
            pygame.transform.flip(
                base_layer,
                True,
                True
            ),
            (width, height)
        )

        return fog

    # Create the fog texture once at startup.
    fog_texture = create_fog_texture(
        1100,
        750
    )
    settings_panel = SettingsPanel(screen)
    settings_panel.close()

    PAUSE_MENU_OPTIONS = [
        ("RESUME", "resume"),
        ("SAVE GAME", "save"),
        ("SETTINGS", "settings"),
        ("RETURN TO MAIN MENU", "main_menu"),
    ]
    # Wide enough for the longest label with margin to spare, so "RETURN TO
    # MAIN MENU" never ends up touching the button's rim on a small screen.
    PAUSE_BTN_WIDTH = max(
        int(SCREEN_W * 0.25),
        max(pause_button_font.size(label)[0] for label, _ in PAUSE_MENU_OPTIONS)
        + int(SCREEN_W * 0.05),
    )
    PAUSE_BTN_HEIGHT = int(SCREEN_H * 0.07)
    PAUSE_BTN_GAP = int(SCREEN_H * 0.02)
    total_height = (
        len(PAUSE_MENU_OPTIONS) * PAUSE_BTN_HEIGHT
        + (len(PAUSE_MENU_OPTIONS) - 1) * PAUSE_BTN_GAP
    )

    # The panel is built around its contents rather than sized independently:
    # title, then the button block, then room for the save message. Centring
    # the panel and the buttons separately is what used to slide the first
    # button up over the title.
    pause_title_surface = pause_title_font.render("PAUSED", True, UI_COLORS["gold"])
    PAUSE_PAD_TOP = int(SCREEN_H * 0.045)
    PAUSE_TITLE_GAP = int(SCREEN_H * 0.035)
    PAUSE_PAD_SIDE = int(SCREEN_W * 0.035)
    # Bottom padding also has to clear the "Game saved." line, which draws
    # 34px up from the panel floor.
    PAUSE_PAD_BOTTOM = max(int(SCREEN_H * 0.05), font.get_height() + 26)

    pause_panel = pygame.Rect(0, 0,
        max(PAUSE_BTN_WIDTH, pause_title_surface.get_width()) + PAUSE_PAD_SIDE * 2,
        PAUSE_PAD_TOP + pause_title_surface.get_height() + PAUSE_TITLE_GAP
        + total_height + PAUSE_PAD_BOTTOM)
    pause_panel.center = (SCREEN_W // 2, SCREEN_H // 2)

    pause_title_pos = (
        pause_panel.centerx - pause_title_surface.get_width() // 2,
        pause_panel.top + PAUSE_PAD_TOP,
    )

    pause_by0 = (pause_panel.top + PAUSE_PAD_TOP
                 + pause_title_surface.get_height() + PAUSE_TITLE_GAP)
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

    def draw_pause_button(surf, rect, label, hovered):
        draw_button(surf, rect, label, pause_button_font, hovered=hovered)

    def blur_frame(surf):
        """
        The given frame, softened - the backdrop the pause menu sits on.

        Taken once when the player pauses, not every frame: the scene
        behind a pause menu never changes, and two full-screen rescales
        per frame to reproduce the same image is work for nothing.
        """

        small = pygame.transform.smoothscale(
            surf,
            (SCREEN_W // 8, SCREEN_H // 8)
        )
        return pygame.transform.smoothscale(small, (SCREEN_W, SCREEN_H))

    def draw_pause_menu(surf, mouse_pos):
        # The blurred scene is already on `surf` - the caller blits the
        # snapshot taken at the moment of pausing.

        # ----- Dark transparent overlay -----
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surf.blit(overlay, (0, 0))

        # ----- Center panel -----
        panel = pause_panel
        draw_panel(surf, panel, radius=10)

        # ----- Title -----
        surf.blit(pause_title_surface, pause_title_pos)

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

    running = True
    # Matches MainCharacter's own starting facing, so the arrow agrees with
    # the sprite before the player has moved at all.
    minimap_heading = (1, 0)
    # How close (in unscaled world pixels) the player has to get before an
    # enemy is written into the bestiary. Roughly "you have clearly seen it".
    ENEMY_SIGHT_RANGE = 180
    main_character = MainCharacter(screen, map_width, map_height)
    enemy_spawns = resolve_encounter_spawns(
        BEGINNER_STAGE_ENCOUNTERS, map_width, map_height,
        collision_rects, path_cells, TILE_SIZE,
        (stage_spawn[0] + player_size // 2, stage_spawn[1] + player_size),
    )
    enemies = [
        Enemy(screen, map_width, map_height,
              world_x=spawn["position"][0], world_y=spawn["position"][1],
              enemy_id=spawn["enemy_id"], zone_size=spawn["zone_size"],
              zone_name=spawn["zone_name"], zone_rect=spawn["zone_rect"],
              group_id=spawn["encounter_id"],
              detection_range=spawn["detection_range"],
              chase_range=spawn["chase_range"],
              disengage_range=spawn["disengage_range"],
              return_tolerance=spawn["return_tolerance"])
        for spawn in enemy_spawns
    ]
    player_combat = PlayerCombat()
    combat_audio = CombatAudio()
    attack_key_ready = True
    death_animation_complete = False
    near_interactable = None
    engaged = False
    while running:
        dt = clock.tick(60) / 1000.0
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

            # The stage panel does not open its own screen - it reports
            # which tab the player asked for (button click or I/J/K/O) and
            # leaves the decision here, the same way the F5 editor and the
            # B inventory are opened from this loop.
            if not paused:
                requested_tab = stage_panel.handle_event(event)
                if requested_tab:
                    background_snapshot = screen.copy()
                    open_stage_info(
                        screen, stage, stage_progress,
                        background=background_snapshot,
                        tab=requested_tab
                    )
                    continue

            # The pause settings panel takes every key while it is open,
            # not just Escape - it is arrow-key operable now, and a key
            # meant for it must never reach the gameplay bindings below.
            if event.type == pygame.KEYDOWN and show_pause_settings:
                settings_panel.handle_event(event)
                show_pause_settings = settings_panel.is_open
                continue

            if event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_e and attack_key_ready and not paused
                        and (near_interactable is None or engaged)):
                    attack_key_ready = False
                    if (player_inventory.weapon_equipped
                            and player_combat.start_attack()):
                        combat_audio.play("sword_swing")
                elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT) and not paused:
                    if player_combat.start_dodge():
                        combat_audio.play("dodge")
                elif event.key == pygame.K_b and not paused:

                    # Keep the original game frame behind the inventory.
                    inventory_background = screen.copy()

                    while True:

                        selected_topic_id = open_inventory(
                            screen,
                            player_inventory,
                            inventory_background
                        )

                        # Inventory was closed normally with B / ESC.
                        if selected_topic_id is None:
                            break

                        # -------------------------------------------------
                        # Stored topic clicked
                        # -------------------------------------------------

                        # The inventory is currently visible on screen,
                        # so use it as the lesson's background.
                        lesson_background = screen.copy()

                        open_topic_flow(
                            selected_topic_id,
                            lesson_background
                        )

                        # When the lesson/editor closes, this loop opens
                        # the inventory again.

                elif event.key == pygame.K_F1 and not paused and DEBUG:

                    night_mode = not night_mode

                    print(
                        "Night mode ON"
                        if night_mode
                        else "Night mode OFF"
                    )

                elif event.key == pygame.K_F2 and not paused and DEBUG:

                    fog_mode = not fog_mode

                    print(
                        "Fog mode ON"
                        if fog_mode
                        else "Fog mode OFF"
                    )

                elif event.key == pygame.K_m and not paused:
                    # M opens the full paper chart. It is handed the same
                    # baked texture and zone rects the minimap draws from,
                    # so the two can never name or place anything
                    # differently - the map is just the uncropped view.
                    background_snapshot = screen.copy()
                    # Returns whether night was left on: F1 keeps working
                    # while the sheet is open, so the world and the map
                    # cannot end up disagreeing about the time of day.
                    night_mode = open_world_map(
                        screen,
                        minimap_base_surface,
                        player_rect,
                        map_width,
                        map_height,
                        zone_pixel_rects,
                        heading=minimap_heading,
                        background=background_snapshot,
                        title=f"Map of the {stage.get('name', 'Island')}",
                        subtitle="YOU ARE IN " + get_zone_at(
                            player_rect.centerx, player_rect.centery,
                            map_width, map_height
                        ).upper(),
                        night=night_mode,
                    )

                elif event.key == pygame.K_ESCAPE:
                    # Settings-panel Escape is handled by the guard at the
                    # top of this loop, so by here the panel is closed.
                    if paused:
                        paused = False
                    else:
                        paused = True
                        # `screen` still holds the last completed frame at
                        # this point - events are pumped before anything
                        # is drawn - so this is exactly what the player
                        # was looking at when they hit pause.
                        pause_snapshot = blur_frame(screen)

                elif event.key == pygame.K_F5 and DEBUG:
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

                elif event.key == pygame.K_F6 and DEBUG:
                    # Debug: prints the player's position as a
                    # fraction of the map, for placing zone rects
                    # in zones.py accurately.
                    frac_x = player_rect.centerx / map_width
                    frac_y = player_rect.centery / map_height
                    print(f"Zone debug position: ({frac_x:.2f}, {frac_y:.2f})")
                    
                elif event.key == pygame.K_F8 and DEBUG:
                    # Dev-only preview: press F8 to see the Game Over screen,
                    # F8 again (or Esc/Enter/R/M/click) to leave it and resume
                    # gameplay right where you were.
                    background_snapshot = screen.copy()
                    game_over_screen(screen, background=background_snapshot)

            # Left button only - see the note in main_menu.py: the wheel
            # and the right button raise this event as well, which had
            # the pause menu firing on a scroll.
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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
                                settings_panel.open()
                            elif btn["action"] == "main_menu":
                                pygame.mixer.music.stop()
                                return "main_menu"
                elif paused and show_pause_settings:
                    settings_panel.handle_event(event)
                    show_pause_settings = settings_panel.is_open
                elif not paused:
                    if gameplay_hud.profile_rect.collidepoint(event.pos):
                        background_snapshot = screen.copy()
                        profile_screen(
                            screen,
                            background=background_snapshot,
                            name=profile_name,
                            hp=player_combat.hp, max_hp=player_combat.max_hp,
                            pp=0, max_pp=0,
                            hearts=gameplay_state["hearts"],
                        )

            if event.type == pygame.MOUSEBUTTONUP:
                if show_pause_settings:
                    settings_panel.handle_event(event)

            if event.type == pygame.KEYUP and event.key == pygame.K_e:
                attack_key_ready = True

            if show_pause_settings and event.type == pygame.MOUSEMOTION:
                settings_panel.handle_event(event)

        if paused:
            # Show the frame the player paused on, and nothing else.
            #
            # This used to re-render the scene from scratch here - the
            # base map, the character, the hotbar and the stage panel -
            # which quietly dropped everything that draw pass did not
            # know about: the trees and other props, the enemies, the
            # profile HUD, the minimap, and the night and fog overlays.
            # That is why pausing wiped the world back to bare ground and
            # turned night into day. Anything added to the main draw pass
            # in future would have gone the same way; a snapshot cannot
            # fall behind like that, because it *is* the finished frame.
            if pause_snapshot is None:
                pause_snapshot = blur_frame(screen)
            screen.blit(pause_snapshot, (0, 0))

            if show_pause_settings:
                settings_panel.draw()
            else:
                draw_pause_menu(screen, mouse_pos)
                if save_message_frames > 0:
                    save_message_frames -= 1
            pygame.display.flip()
            continue
        # --- Movement / combat action state ---
        player_combat.update(dt)
        main_character.set_combat_state(player_combat.state)
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

        if player_combat.state in ("attacking", "flinch", "defeated"):
            dx = dy = 0
        elif player_combat.state == "dodging":
            dodge_dx, dodge_dy = FACING_VECTORS.get(main_character.facing, (1, 0))
            dx, dy = dodge_dx * PLAYER_DODGE_SPEED, dodge_dy * PLAYER_DODGE_SPEED
        else:
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

        # --- Independent enemy AI and combat resolution ---
        engaged = False
        for enemy in enemies:
            enemy_blockers = collision_rects + [
                other.rect for other in enemies
                if other is not enemy and other.active
                and other.state != "defeated"
            ]
            incoming_damage = enemy.update(
                dt, player_rect, enemy_blockers, map_width, map_height,
                navigation_rects=collision_rects,
            )
            if enemy.just_started_attack:
                combat_audio.play("enemy_attack")
            engaged = engaged or enemy.engaged
            if incoming_damage:
                if player_combat.take_damage(incoming_damage):
                    combat_audio.play(
                        "player_death" if player_combat.hp == 0 else "player_hurt"
                    )

            enemy_dx = enemy.center_x - player_rect.centerx
            enemy_dy = enemy.center_y - player_rect.centery
            if enemy_dx * enemy_dx + enemy_dy * enemy_dy <= ENEMY_SIGHT_RANGE ** 2:
                if stage_progress.discover_enemy(enemy.enemy_id):
                    stage_progress.sync_objectives(stage, save_challenges_passed)

        if player_combat.attack_active:
            hitbox = attack_hitbox(player_rect, main_character.facing)
            damage = selected_weapon_damage(player_inventory)
            for enemy in enemies:
                already_hit = getattr(enemy, "last_player_attack", -1) == player_combat.attack_id
                path_blocked = attack_path_blocked(
                    player_rect, enemy.rect, collision_rects
                )
                if damage and enemy.active and not already_hit and not path_blocked and hitbox.colliderect(enemy.rect):
                    enemy.last_player_attack = player_combat.attack_id
                    if enemy.receive_damage(damage):
                        combat_audio.play("sword_hit")
                        combat_audio.play(
                            "enemy_death" if enemy.hp == 0 else "enemy_hurt"
                        )

        for enemy in enemies:
            if enemy.state == "defeated" and not getattr(enemy, "rewarded", False):
                enemy.rewarded = True
                gameplay_state["bonus_time"] += enemy.stats.reward_time
                stage_progress.defeat_enemy(enemy.enemy_id)

        if player_combat.hp == 0 and death_animation_complete:
            gameplay_state["hearts"] = max(0, gameplay_state["hearts"] - 1)
            result = game_over_screen(screen, background=screen.copy())
            if result == "main_menu":
                pygame.mixer.music.stop()
                return "main_menu"
            if gameplay_state["hearts"] == 0:
                gameplay_state["hearts"] = 5
            player_combat.reset()
            death_animation_complete = False
            player_rect.topleft = stage_spawn
            player_x, player_y = map(float, stage_spawn)
            for enemy in enemies:
                enemy.reset()
                enemy.rewarded = False

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

        # Combat takes input priority over environmental hold interactions.
        if engaged:
            near_interactable = None

        # --- Handle E key hold ---
        if near_interactable:
            if keys[pygame.K_e]:
                near_interactable['inspect_progress'] += 1 / 60 / INSPECT_TIME
                near_interactable['inspect_progress'] = min(near_interactable['inspect_progress'], 1.0)
                if near_interactable['inspect_progress'] >= 1.0:
                    near_interactable['inspecting'] = True

                    topic_id = near_interactable.get('topic_id')

                    if (
                        topic_id
                        and not near_interactable['topic_handled']
                    ):

                        # Prevent this barrel from opening the discovery popup
                        # repeatedly.
                        near_interactable['topic_handled'] = True

                        background_snapshot = screen.copy()

                        decision = open_topic_found(
                            screen,
                            topic_id,
                            background_snapshot
                        )

                        if decision == "start":

                            open_topic_flow(
                                topic_id,
                                background_snapshot
                            )

                        elif decision == "store":

                            topic = get_topic(topic_id)

                            if topic is None:

                                print(
                                    f"Unknown topic id: {topic_id}"
                                )

                            else:

                                stored = player_inventory.add_topic(
                                    topic_id,
                                    topic["title"]
                                )

                                if stored:

                                    print(
                                        f"Stored topic: {topic['title']}"
                                    )

                                else:

                                    print(
                                        f"Topic already stored or bag is full: "
                                        f"{topic['title']}"
                                    )

                            # NEXT STEP:
                            # player_inventory.add_topic(...)
                            
                    # Finishing a search is what counts as discovering the
                    # object, so it fills in its entry in the Items tab.
                    # The action string ("search_vase") is the join between
                    # the Tiled object and items.py.
                    if stage_progress.discover_by_action(
                        near_interactable.get('actions', '')
                    ):
                        stage_progress.sync_objectives(
                            stage, save_challenges_passed
                        )
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

        # game.py already resolved movement/collision above; only synchronize
        # the renderer here so the player is not moved a second time.
        main_character.pos_x = player_x
        main_character.pos_y = player_y
        main_character.center_x, main_character.center_y = player_rect.center
        main_character.update_frames(keys)

        # --- Depth-sorted draw pass (painter's algorithm) ---
        draw_list = [('prop', p['sort_y'], p) for p in dynamic_props]
        draw_list.append(('player', player_rect.bottom, None))
        for enemy in enemies:
            if enemy.active:
                draw_list.append(('enemy', enemy.center_y, enemy))
        draw_list.sort(key=lambda entry: entry[1])

        for kind, _, prop in draw_list:
            if kind == 'prop':
                screen.blit(prop['image'], (prop['x'] - camera_x, prop['y'] - camera_y))
            elif kind == 'player':
                main_character.draw_frames(ZOOM, camera_x, camera_y, dt=dt)
            elif kind == 'enemy':
                prop.draw_frames(ZOOM, camera_x, camera_y)

        # ---------------------------------------------------------
        # Night Mode
        # ---------------------------------------------------------
        # F1 toggles a simple dark blue overlay over the world.
        # UI is drawn afterwards, so it stays clearly visible.

        if night_mode:
            screen.blit(
                night_overlay,
                (0, 0)
            )

        # ---------------------------------------------------------
        # Fog
        # ---------------------------------------------------------

        if fog_mode:

            # Move fog independently through the world.
            fog_drift_x += fog_speed_x * dt
            fog_drift_y += fog_speed_y * dt

            fog_w = fog_texture.get_width()
            fog_h = fog_texture.get_height()

            # World position + independent fog movement.
            offset_x = int(
                camera_x - fog_drift_x
            )

            offset_y = int(
                camera_y - fog_drift_y
            )

            start_x = -(
                offset_x % fog_w
            )

            start_y = -(
                offset_y % fog_h
            )

            # Repeat fog across visible screen.
            for fog_y in range(
                start_y - fog_h,
                SCREEN_H + fog_h,
                fog_h
            ):

                for fog_x in range(
                    start_x - fog_w,
                    SCREEN_W + fog_w,
                    fog_w
                ):

                    screen.blit(
                        fog_texture,
                        (fog_x, fog_y)
                    )

        # --- Draw interaction UI ---
        if near_interactable:
            # Scale the interactable position to match the zoomed map
            cam_x = near_interactable['rect'].x * ZOOM - camera_x
            cam_y = near_interactable['rect'].y * ZOOM - camera_y - 30

            if not near_interactable['inspecting']:
                # Keep progress anchored to the object; the contextual action
                # text itself is rendered once by GameplayHUD at bottom-centre.
                bar_w = 80
                pygame.draw.rect(screen, (50, 50, 50),
                                 (cam_x, cam_y, bar_w, 8))
                # Progress bar fill
                pygame.draw.rect(screen, (255, 220, 50),
                                 (cam_x, cam_y,
                                  int(bar_w * near_interactable['inspect_progress']), 8))
            else:
                # Show message based on object type
                action = near_interactable.get('actions', '')
                topic_id = near_interactable.get('topic_id')

                if topic_id:
                    message = ""
                else:
                    object_name = (
                        action
                        .removeprefix("search_")
                        .replace("_", " ")
                    )

                    if object_name:
                        message = f"The {object_name} is empty."
                    else:
                        message = "Nothing here."

                # Only draw the message box if there is actually a message
                if message:
                    msg = inspect_font.render(
                        message,
                        True,
                        (255, 255, 255)
                    )

                    box = pygame.Rect(
                        SCREEN_W // 2 - msg.get_width() // 2 - 10,
                        SCREEN_H // 2 - msg.get_height() // 2 - 10,
                        msg.get_width() + 20,
                        msg.get_height() + 20
                    )

                    pygame.draw.rect(
                        screen,
                        (20, 20, 20),
                        box,
                        border_radius=6
                    )

                    pygame.draw.rect(
                        screen,
                        (200, 200, 100),
                        box,
                        2,
                        border_radius=6
                    )

                    screen.blit(
                        msg,
                        (
                            SCREEN_W // 2 - msg.get_width() // 2,
                            SCREEN_H // 2 - msg.get_height() // 2
                        )
                    )

                    close_hint = font.render(
                        "Release E to close",
                        True,
                        (255, 0, 0)
                    )

                    screen.blit(
                        close_hint,
                        (
                            SCREEN_W // 2 - close_hint.get_width() // 2,
                            SCREEN_H // 2 + msg.get_height()
                        )
                    )

                # Keep this OUTSIDE "if message"
                if not keys[pygame.K_e]:
                    near_interactable['inspecting'] = False
                    near_interactable['inspect_progress'] = 0.0

        interaction_prompt = None
        if near_interactable and not near_interactable["inspecting"]:
            action = near_interactable.get("actions", "")
            if near_interactable.get("topic_id"):
                interaction_prompt = "Read Topic"
            elif action.startswith("search_"):
                target = action.removeprefix("search_").replace("_", " ").title()
                interaction_prompt = f"Search {target}" if target else "Interact"
            else:
                interaction_prompt = "Interact"

        # HUD consumes existing state and nearby-interactable detection.
        gameplay_hud.draw(
            interaction_prompt=interaction_prompt,
            in_combat=engaged,
            current_hp=player_combat.hp,
            max_hp=player_combat.max_hp,
            bonus_time=gameplay_state["bonus_time"],
        )

        if COMBAT_DEBUG:
            world_hitbox = attack_hitbox(player_rect, main_character.facing)
            debug_hitbox = pygame.Rect(
                world_hitbox.x * ZOOM - camera_x,
                world_hitbox.y * ZOOM - camera_y,
                world_hitbox.width * ZOOM,
                world_hitbox.height * ZOOM,
            )
            pygame.draw.rect(screen, (255, 220, 40), debug_hitbox, 2)
            for enemy in enemies:
                enemy_debug_rect = pygame.Rect(
                    enemy.rect.x * ZOOM - camera_x,
                    enemy.rect.y * ZOOM - camera_y,
                    enemy.rect.width * ZOOM,
                    enemy.rect.height * ZOOM,
                )
                pygame.draw.rect(screen, (255, 80, 80), enemy_debug_rect, 1)

        if DEBUG_ENEMY_AI:
            ai_font = body_font(12, bold=True)
            for enemy in enemies:
                if not enemy.active:
                    continue
                center = (
                    round(enemy.rect.centerx * ZOOM - camera_x),
                    round(enemy.rect.centery * ZOOM - camera_y),
                )
                home = (
                    round(enemy.spawn[0] * ZOOM - camera_x),
                    round(enemy.spawn[1] * ZOOM - camera_y),
                )
                zone = pygame.Rect(
                    enemy.zone.x * ZOOM - camera_x,
                    enemy.zone.y * ZOOM - camera_y,
                    enemy.zone.width * ZOOM,
                    enemy.zone.height * ZOOM,
                )
                pygame.draw.rect(screen, (80, 180, 255), zone, 2)
                pygame.draw.circle(screen, (255, 80, 80), center,
                                   round(enemy.stats.attack_range * ZOOM), 1)
                pygame.draw.circle(screen, (255, 220, 70), center,
                                   round(enemy.awareness_radius * ZOOM), 1)
                pygame.draw.circle(screen, (80, 230, 120), center,
                                   round(enemy.detection_range * ZOOM), 2)
                pygame.draw.circle(screen, (210, 100, 255), home,
                                   round(enemy.chase_range * ZOOM), 1)
                pygame.draw.circle(screen, (255, 255, 255), home, 4)
                label = ai_font.render(
                    f"{enemy.state.upper()} | {enemy.zone_name} | {enemy.group_id}",
                    True, (255, 255, 255),
                )
                screen.blit(label, (center[0] + 10, center[1] - 24))
        # Minimap (bottom-left)
        draw_minimap(screen, player_rect, minimap_heading, night_mode)

        # Hotbar (bottom-centre). Drawn after the world and the HUD so it
        # always sits on top of everything else in the scene.
        toolbar.draw(mouse_pos)

        # Objectives tracker + stage info rail (right side)
        stage_panel.draw(mouse_pos)

        # Key hints (top-right, out of the way of the profile HUD)
        hint = font.render(
            "ESC = Pause    B = Inventory    M = Map    F1 = Night    F2 = Fog",
            True,
            (255, 255, 255)
        )
        screen.blit(hint, (SCREEN_W - hint.get_width() - 10, 10))

        pygame.display.flip()
        if player_combat.state == "defeated" and player_combat.action_time == 0:
            # The final defeated frame has now actually been presented. The
            # next loop may safely deduct a heart and open Game Over.
            death_animation_complete = True
