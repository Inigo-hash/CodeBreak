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
from src.screens.game import load_interactables, nearest_interactable
from src.screens.intro import PAGES
from src.screens.settings import HELP_COPY
from src.settings_state import settings_state
from src.ui.ambient_particles import AmbientParticles


class MapAndInteractionRegressionTests(unittest.TestCase):
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

    def test_editor_keeps_numbered_workflow_and_line_numbers(self):
        source = Path("src/ui/editor_renderer.py").read_text(encoding="utf-8")
        self.assertIn('"2  RUN"', source)
        self.assertIn('"3  SUBMIT"', source)
        self.assertIn("line_number =", source)

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
