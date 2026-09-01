"""Regression coverage for the supplied August 31 bug report."""

import os
from pathlib import Path
from types import SimpleNamespace
import unittest
import xml.etree.ElementTree as ET

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.entities.enemy import Enemy
from src.systems.combat import ENEMY_STATS, attack_hitbox
from src.systems.enemy_spawns import resolve_encounter_spawns
from src.screens.game import (
    coalesced_collision_rects, load_interactables,
    load_object_collision_rects, nearest_interactable,
)
from src.screens.inventory import PlayerInventory
from src.screens.world_map import enemy_marker_positions
from src.screens.intro import PAGES
from src.screens.settings import HELP_COPY, SettingsPanel
from src.settings_state import settings_state
from src.systems import save_manager
from src.systems.onboarding import (
    _reset_walkthrough_for_tests, opening_walkthrough_needed,
)
from src.display import _viewport
from src.ui.ambient_particles import AmbientParticles


class MapAndInteractionRegressionTests(unittest.TestCase):
    def test_world_map_marks_only_active_enemies_tracking_the_player(self):
        alive = SimpleNamespace(
            active=True, state="chase", rect=pygame.Rect(90, 40, 20, 20)
        )
        unaware = SimpleNamespace(
            active=True, state="idle", rect=pygame.Rect(50, 40, 20, 20)
        )
        defeated = SimpleNamespace(
            active=True, state="defeated", rect=pygame.Rect(10, 10, 20, 20)
        )
        positions = enemy_marker_positions(
            (alive, unaware, defeated), (100, 50),
            pygame.Rect(20, 30, 300, 200), 0.5
        )
        self.assertEqual(positions, [(170, 105)])

    def test_impossible_dirt_spawn_is_skipped_without_crashing(self):
        spawns = resolve_encounter_spawns(
            ({
                "id": "no_dirt",
                "anchor": (0.5, 0.5),
                "enemies": ("tiyanak_sinta",),
            },),
            320, 240, [], set(), 16, (160, 220),
            zones=(),
        )
        self.assertEqual(spawns, [])

    def test_sword_reaches_past_the_body_without_out_ranging_enemies(self):
        """The blade has to cover both a closed-in target and a step of gap."""

        player = pygame.Rect(0, 0, 16, 16)
        player.center = (100, 100)

        for facing in ("right", "left", "forward", "backward"):
            with self.subTest(facing=facing):
                box = attack_hitbox(player, facing)
                # An enemy that has walked into the player is still hittable.
                self.assertTrue(box.collidepoint(player.center))

                furthest = max(
                    abs(box.left - player.centerx),
                    abs(box.right - player.centerx),
                    abs(box.top - player.centery),
                    abs(box.bottom - player.centery),
                )
                self.assertGreaterEqual(furthest, 60)
                # Enemies keep the range advantage: a tiyanak strikes from 72.
                self.assertLess(
                    furthest, ENEMY_STATS["tiyanak_sinta"].attack_range
                )

    def test_wilderness_enemy_reach_matches_visible_sprite_distance(self):
        self.assertGreaterEqual(ENEMY_STATS["tiyanak_sinta"].attack_range, 72)
        self.assertGreaterEqual(ENEMY_STATS["manananggal"].attack_range, 96)
        self.assertGreaterEqual(ENEMY_STATS["tikbalang"].attack_range, 104)

    def test_enemy_body_cannot_move_from_dirt_onto_grass(self):
        enemy = Enemy.__new__(Enemy)
        enemy.rect = pygame.Rect(16, 16, 12, 12)
        enemy.x, enemy.y = float(enemy.rect.x), float(enemy.rect.y)
        enemy.spawn = enemy.rect.center
        enemy.allowed_ground_cells = {(1, 1)}
        enemy.ground_tile_size = 16
        enemy.detour_time = 0.0
        enemy.detour_direction = (0, 0)
        enemy.facing = "south"
        enemy.stuck_time = 0.0
        enemy.center_x, enemy.center_y = enemy.rect.center

        enemy._move((1, 0), 20, 1.0, [], 128, 128, allow_detour=False)

        self.assertEqual(enemy.rect.topleft, (16, 16))

    def test_every_authored_collision_property_uses_the_loader_spelling(self):
        root = ET.parse(
            Path("assets/map/tsx/Enviroment-Forest.tsx")
        ).getroot()
        names = [node.get("name") for node in root.findall(".//property")]
        self.assertNotIn("collidible", names)
        self.assertGreaterEqual(names.count("collidable"), 16)

    def test_ocean_tile_is_solid_at_every_shoreline(self):
        root = ET.parse(
            Path("assets/map/tsx/Enviroment-Forest.tsx")
        ).getroot()
        water = root.find("./tile[@id='109']")
        self.assertIsNotNone(water)
        properties = {
            prop.get("name"): prop.get("value")
            for prop in water.findall("./properties/property")
        }
        self.assertEqual(properties.get("collidable"), "true")

    def test_ocean_collision_cells_are_coalesced_into_row_runs(self):
        cells = {(0, 0), (1, 0), (2, 0), (5, 0), (0, 1)}
        rects = coalesced_collision_rects(cells, 16)
        self.assertEqual(
            {(rect.x, rect.y, rect.width, rect.height) for rect in rects},
            {(0, 0, 48, 16), (80, 0, 16, 16), (0, 16, 16, 16)},
        )

    def test_sign_and_monument_have_authored_collision_boxes(self):
        root = ET.parse(Path("assets/map/tmx/map1.tmx")).getroot()
        objects = {obj.get("name"): obj for obj in root.findall(".//object")}
        for name in ("Trail Sign", "Monument Collision"):
            self.assertIn(name, objects)
            properties = {
                prop.get("name"): prop.get("value")
                for prop in objects[name].findall("./properties/property")
            }
            self.assertEqual(properties.get("collidable"), "true")

        self.assertEqual(objects["Monument Collision"].get("width"), "160")
        self.assertEqual(objects["Monument Collision"].get("height"), "96")

    def test_object_collision_loader_uses_precise_authored_bounds(self):
        obj = SimpleNamespace(
            x=12.4, y=18.6, width=40.2, height=22.8,
            properties={"collidable": True},
        )
        tiled_map = SimpleNamespace(visible_layers=[[obj]])
        self.assertEqual(
            load_object_collision_rects(tiled_map),
            [pygame.Rect(12, 19, 40, 23)],
        )

    def test_action_only_map_objects_remain_interactable(self):
        obj = SimpleNamespace(
            x=100, y=80, width=28, height=30, type="",
            properties={"actions": "search_crate"},
        )
        layer = [obj]
        tiled_map = SimpleNamespace(visible_layers=[layer])

        items = load_interactables(tiled_map)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["actions"], "search_crate")

    def test_authored_sign_opens_its_text_message(self):
        root = ET.parse(Path("assets/map/tmx/map1.tmx")).getroot()
        sign = next(
            obj for obj in root.findall(".//object")
            if obj.get("name") == "Trail Sign"
        )
        properties = {
            prop.get("name"): prop.get("value")
            for prop in sign.findall("./properties/property")
        }
        self.assertEqual(properties.get("actions"), "read_sign")
        self.assertIn("Python keys", properties.get("message", ""))

        obj = SimpleNamespace(
            id=sign.get("id"), x=1552, y=1872, width=32, height=16,
            type="", properties=properties,
        )
        items = load_interactables(SimpleNamespace(visible_layers=[[obj]]))
        self.assertEqual(items[0]["message"], properties["message"])

    def test_every_chest_and_barrel_has_a_specific_coding_topic(self):
        root = ET.parse(Path("assets/map/tmx/map1.tmx")).getroot()
        checked = 0
        for obj in root.findall(".//object"):
            properties = {
                prop.get("name"): prop.get("value")
                for prop in obj.findall("./properties/property")
            }
            if properties.get("actions") not in (
                "search_chest", "search_barrel"
            ):
                continue
            checked += 1
            self.assertTrue(properties.get("topic_id"), obj.get("id"))
        self.assertGreaterEqual(checked, 7)

    def test_nearest_reachable_object_wins_over_map_file_order(self):
        player = pygame.Rect(100, 100, 16, 16)
        farther = {"rect": pygame.Rect(130, 100, 16, 16)}
        nearer = {"rect": pygame.Rect(112, 100, 16, 16)}

        self.assertIs(
            nearest_interactable(player, [farther, nearer], reach=32),
            nearer,
        )


class EnemyNavigationRegressionTests(unittest.TestCase):
    def test_large_enemy_can_route_around_a_tree_wall(self):
        enemy = Enemy.__new__(Enemy)
        enemy.rect = pygame.Rect(0, 0, 36, 38)
        enemy.rect.center = (40, 48)
        enemy.spawn = enemy.rect.center
        blockers = [pygame.Rect(88, 0, 24, 112)]
        bounds = pygame.Rect(0, 0, 220, 180)

        path = enemy._find_path_to(
            (180, 48), blockers, bounds.width, bounds.height, bounds
        )

        self.assertTrue(path)
        self.assertTrue(any(y > blockers[0].bottom for _x, y in path))
        for point in path[:-1]:
            probe = enemy.rect.copy()
            probe.center = point
            self.assertEqual(probe.collidelist(blockers), -1)


class OnboardingAndSettingsRegressionTests(unittest.TestCase):
    def test_intro_uses_clear_action_wording(self):
        all_copy = " ".join(
            [part for page in PAGES for part in (page[0], page[1], *page[2])]
        ).lower()
        self.assertNotIn("handles monsters", all_copy)
        self.assertIn("defeats monsters", all_copy)

    def test_default_text_uses_the_reported_recommended_size(self):
        self.assertEqual(settings_state["font_size"], 25)

    def test_every_settings_help_tip_explains_what_how_and_effect(self):
        for topic, copy in HELP_COPY.items():
            with self.subTest(topic=topic):
                self.assertIn("controls", copy.lower())
                self.assertGreaterEqual(copy.count("."), 3)

    def test_slider_help_explains_mouse_and_button_controls(self):
        for topic in ("music", "sfx"):
            copy = HELP_COPY[topic].lower()
            self.assertIn("slider", copy)
            self.assertIn("- / +", copy)
            self.assertTrue("drag" in copy or "click" in copy)

    def test_editor_action_row_is_unnumbered_and_keeps_line_numbers(self):
        # The step numbers were dropped from the button labels; the header
        # still spells the workflow out, and the gutter still numbers lines.
        source = Path("src/ui/editor_renderer.py").read_text(encoding="utf-8")
        self.assertIn('"RUN"', source)
        self.assertIn('"SUBMIT"', source)
        self.assertNotIn('"2  RUN"', source)
        self.assertNotIn('"3  SUBMIT"', source)
        self.assertIn("TYPE CODE", source)
        self.assertIn("line_number =", source)

    def test_exit_sits_in_the_title_bar_not_beside_submit(self):
        # Unsaved code makes a LEAVE button next to SUBMIT a misclick away
        # from losing everything, so leaving lives up by the settings wheel.
        source = Path("src/ui/editor_renderer.py").read_text(encoding="utf-8")
        self.assertIn("self.exit_button", source)
        self.assertNotIn("self.leave_button", source)
        self.assertIn("self.settings_gear_rect.left - EXIT_BUTTON_GAP", source)

    def test_focus_ring_is_keyboard_only_in_both_settings_panels(self):
        # The blue ring tells a keyboard player which row the arrow keys
        # will change. A mouse user can see that from the pointer, so a
        # click has to put the ring away again.
        from src.ui.editor_settings import EditorSettingsPanel

        screen = pygame.display.set_mode((1280, 720))

        for panel in (SettingsPanel(screen), EditorSettingsPanel(screen)):
            panel.open()
            with self.subTest(panel=type(panel).__name__):
                self.assertFalse(panel.keyboard_focus)

                panel.handle_event(pygame.event.Event(
                    pygame.KEYDOWN, key=pygame.K_DOWN, unicode="", mod=0
                ))
                self.assertTrue(panel.keyboard_focus)

                panel.handle_event(pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN, button=1, pos=(1, 1)
                ))
                self.assertFalse(panel.keyboard_focus)

    def test_main_menu_still_launches_the_walkthrough(self):
        source = Path("src/screens/main_menu.py").read_text(encoding="utf-8")
        self.assertIn("opening_walkthrough(screen)", source)

    def test_walkthrough_is_automatic_only_for_a_new_session(self):
        _reset_walkthrough_for_tests()
        self.assertTrue(opening_walkthrough_needed(lambda _slot: False, 3))
        self.assertFalse(opening_walkthrough_needed(lambda _slot: False, 3))

        _reset_walkthrough_for_tests()
        self.assertFalse(opening_walkthrough_needed(lambda slot: slot == 2, 3))

    def test_intro_teaches_menu_navigation_and_top_right_help(self):
        all_copy = " ".join(
            [part for page in PAGES for part in (page[0], page[1], *page[2])]
        ).lower()
        self.assertIn("start game", all_copy)
        self.assertIn("how to play", all_copy)
        self.assertIn("top-right", all_copy)
        self.assertIn("hover over or select any ?", all_copy)

    def test_non_widescreen_windows_have_no_letterbox_viewport(self):
        for size in ((1280, 800), (1024, 768), (2560, 1080)):
            with self.subTest(size=size):
                scales, offset, scaled = _viewport(size)
                self.assertEqual(offset, (0, 0))
                self.assertEqual(scaled, size)
                self.assertAlmostEqual(scales[0], size[0] / 1920)
                self.assertAlmostEqual(scales[1], size[1] / 1080)

    def test_new_players_carry_but_do_not_auto_equip_the_sword(self):
        state = save_manager.new_game_state()
        self.assertTrue(state["weapon_obtained"])
        self.assertFalse(state["weapon_equipped"])

        inventory = PlayerInventory()
        inventory.set_weapon_state(
            state["weapon_obtained"], state["weapon_equipped"]
        )
        self.assertFalse(inventory.weapon_equipped)
        self.assertTrue(any(
            item is not None and item.kind == "weapon"
            for item in inventory.bag
        ))

    def test_gameplay_exposes_settings_and_clears_combat_corners(self):
        source = Path("src/screens/game.py").read_text(encoding="utf-8")
        self.assertIn("settings_gear_rect", source)
        self.assertIn("draw_gear_medallion", source)
        self.assertIn("if engaged:\n            draw_low_health_warning", source)

    def test_settings_modal_suppresses_underlying_menu_hover(self):
        source = Path("src/screens/main_menu.py").read_text(encoding="utf-8")
        self.assertIn("(not show_settings) and rect.collidepoint", source)

    def test_painted_fireflies_and_blue_motes_are_animated(self):
        background = pygame.transform.smoothscale(
            pygame.image.load("assets/images/backgrounds/mainMenuBg1.png"),
            (1280, 720),
        )
        ambient = AmbientParticles(1280, 720, background=background)

        self.assertTrue(ambient._specks)
        self.assertTrue(ambient._motes)
        self.assertTrue(ambient._fireflies)
        self.assertNotEqual(ambient._specks[0].delta(0),
                            ambient._specks[0].delta(2))
        self.assertNotEqual(ambient._motes[0].level(0),
                            ambient._motes[0].level(2))
        self.assertNotEqual(ambient._fireflies[0].position(0),
                            ambient._fireflies[0].position(2))


if __name__ == "__main__":
    unittest.main()
