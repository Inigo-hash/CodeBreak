"""Behavioral regressions for bugs or smth.pdf (September 10)."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame
import pytmx

from src import display, settings_state as settings
from src.screens.game import load_interactables, object_collision_rects
from src.systems.enemy_spawns import _has_escape_route
from src.ui.damage_numbers import DamageNumbers


class SeptemberReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.map = pytmx.load_pygame("assets/map/tmx/map1.tmx")

    def test_tile_object_collision_uses_bottom_origin(self):
        objects = [SimpleNamespace(x=30, y=80, width=20, height=40, gid=1,
                                   properties={"collidable": True}),
                   SimpleNamespace(x=90, y=80, width=20, height=40, gid=0,
                                   properties={"collidable": True})]
        rects = object_collision_rects(SimpleNamespace(visible_layers=[objects]))
        self.assertEqual(rects, [pygame.Rect(30, 40, 20, 40), pygame.Rect(90, 80, 20, 40)])

    def test_statue_base_is_solid(self):
        rects = object_collision_rects(self.map)
        self.assertTrue(any(r.collidepoint(2208, 2024) for r in rects))

    def test_new_player_must_equip_the_starter_sword(self):
        from src.systems.save_manager import new_game_state
        from src.screens.inventory import PlayerInventory
        state = new_game_state()
        inventory = PlayerInventory()
        inventory.set_weapon_state(state["weapon_obtained"], state["weapon_equipped"])
        self.assertFalse(inventory.weapon_equipped)
        self.assertTrue(any(item is not None and item.kind == "weapon" for item in inventory.bag))

    def test_existing_sign_tiles_have_readable_interactions(self):
        signs = [i for i in load_interactables(self.map) if i["actions"] == "read_sign"]
        self.assertGreaterEqual(len(signs), 2)
        self.assertTrue(all(i["interaction_message"] for i in signs))
        self.assertTrue(any(i["rect"].collidepoint(1558, 1878) for i in signs))

    def test_every_chest_and_barrel_is_linked_to_a_real_lesson(self):
        from src.data.topics import TOPICS
        caches = [i for i in load_interactables(self.map)
                  if i["actions"] in ("search_chest", "search_barrel")]
        self.assertGreater(len(caches), 2)
        self.assertTrue(all(i["topic_id"] in TOPICS for i in caches))

    def test_spawn_rejects_a_pocket_but_accepts_an_open_route(self):
        body = pygame.Rect(90, 90, 20, 20)
        bounds = pygame.Rect(0, 0, 300, 300)
        walls = [pygame.Rect(70, 70, 60, 10), pygame.Rect(70, 120, 60, 10),
                 pygame.Rect(70, 70, 10, 60), pygame.Rect(120, 70, 10, 60)]
        self.assertFalse(_has_escape_route(body, bounds, walls, set(), 16, None, False))
        self.assertTrue(_has_escape_route(body, bounds, walls[:-1], set(), 16, None, False))

    def test_damage_numbers_draw_and_expire(self):
        effects = DamageNumbers()
        effects.add((100, 100), 20)
        effects.add((100, 100), 0)
        self.assertEqual(len(effects.hits), 1)
        surface = pygame.Surface((300, 300))
        effects.draw(surface, 1, 0, 0)
        self.assertGreater(pygame.surfarray.array3d(surface).sum(), 0)
        effects.update(0.86)
        self.assertFalse(effects.hits)

    def test_monitor_aspects_fill_without_stretching_or_cropping(self):
        for size in ((1366, 768), (1280, 1024), (2560, 1080), (1920, 1200)):
            canvas = pygame.Surface(display.canvas_size_for_window(size))
            with self.subTest(size=size), patch.object(display, "_canvas", canvas):
                scale, offset, scaled = display._viewport(size)
                self.assertEqual(offset, (0, 0))
                self.assertLessEqual(abs(scaled[0] - size[0]), 1)
                self.assertLessEqual(abs(scaled[1] - size[1]), 1)
                self.assertAlmostEqual(canvas.get_width() * scale, size[0], delta=1)

    def test_walkthrough_seen_persists_without_changing_player_settings(self):
        with TemporaryDirectory() as temp, patch.object(settings, "SETTINGS_PATH", str(Path(temp) / "settings.json")), patch.dict(settings.settings_state):
            settings.settings_state["walkthrough_seen"] = True
            self.assertTrue(settings.save_settings())
            settings.settings_state["walkthrough_seen"] = False
            self.assertTrue(settings.load_settings())
            self.assertTrue(settings.settings_state["walkthrough_seen"])


if __name__ == "__main__":
    unittest.main()
