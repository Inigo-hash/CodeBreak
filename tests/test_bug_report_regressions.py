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
from src.systems.combat import ENEMY_STATS
from src.systems.enemy_spawns import resolve_encounter_spawns
from src.screens.game import load_interactables, nearest_interactable
from src.screens.world_map import enemy_marker_positions
from src.screens.intro import PAGES
from src.screens.settings import HELP_COPY, SettingsPanel
from src.settings_state import settings_state
from src.ui.ambient_particles import AmbientParticles


class MapAndInteractionRegressionTests(unittest.TestCase):
    def test_world_map_marks_only_living_active_enemies(self):
        alive = SimpleNamespace(
            active=True, state="idle", rect=pygame.Rect(90, 40, 20, 20)
        )
        defeated = SimpleNamespace(
            active=True, state="defeated", rect=pygame.Rect(10, 10, 20, 20)
        )
        positions = enemy_marker_positions(
            (alive, defeated), (100, 50), pygame.Rect(20, 30, 300, 200), 0.5
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

    def test_default_text_is_larger_than_the_old_baseline(self):
        self.assertGreater(settings_state["font_size"], 18)

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
