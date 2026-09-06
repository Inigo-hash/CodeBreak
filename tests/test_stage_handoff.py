"""Regression tests for the stage 1 -> stage 2 handoff.

Three seams are covered: what stages.py says follows what, what a save
carries across the gate, and the loop in start_game_menu that re-enters
gameplay on the stage the gate handed over to.
"""

import os
from collections import deque
from pathlib import Path
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from pytmx.util_pygame import load_pygame

from src.data.stages import get_stage, stage_world
from src.data.zones import get_zone_at
from src.screens import start_game_menu
from src.systems import save_manager
from src.systems.stage_handoff import (
    FULL_HEARTS, advance_save_state, has_playable_next_stage, next_stage,
    next_stage_id, stage_is_enterable,
)
from src.ui.gameplay_hud import MAX_HEARTS


def island_state(**overrides):
    """A save sitting at the Island's exit gate with the stage finished."""

    state = {
        "stage": "Island",
        "hearts": 1,
        "keys": 9,
        "topics_discovered": ["variables"],
        "topics_completed": ["variables"],
        "bonus_time": 42,
        "challenges_passed": ["variables_001", "strings_lesson_001"],
        "completed_stages": [],
        "map_layout_version": 2,
        "map_position": [1234.0, 567.0],
        "stored_topics": ["variables"],
        "weapon_obtained": True,
        "weapon_equipped": True,
        "stage_progress": {
            "discovered_items": ["barrel"],
            "defeated_enemies": ["corrupted_core_kapre"],
            "objectives_done": ["island_variables"],
            "opened_interactables": ["1504"],
        },
    }
    state.update(overrides)
    return state


class StageOrderTests(unittest.TestCase):
    def test_the_island_leads_to_the_castle(self):
        island = get_stage("island")
        self.assertEqual(next_stage_id(island), "castle")
        self.assertEqual(next_stage(island)["id"], "castle")

    def test_the_castle_is_enterable_so_the_gate_hands_over(self):
        self.assertTrue(stage_is_enterable(get_stage("castle")))
        self.assertTrue(has_playable_next_stage(get_stage("island")))

    def test_the_last_authored_stage_ends_the_run(self):
        castle = get_stage("castle")
        self.assertIsNone(next_stage(castle))
        self.assertFalse(has_playable_next_stage(castle))

    def test_an_unknown_next_stage_does_not_restart_the_run_on_stage_one(self):
        # get_stage() falls back to the Island for an id it does not know,
        # which would quietly send a finished player back to the beginning.
        self.assertIsNone(next_stage({"id": "island", "next_stage": "atlantis"}))
        self.assertFalse(has_playable_next_stage({"next_stage": "atlantis"}))

    def test_a_stage_without_a_map_is_not_enterable(self):
        self.assertFalse(stage_is_enterable({"world": {"map": None}}))
        self.assertFalse(stage_is_enterable(None))


class AdvanceSaveStateTests(unittest.TestCase):
    def setUp(self):
        self.island = get_stage("island")
        self.castle = get_stage("castle")
        self.original = island_state()
        self.advanced = advance_save_state(
            self.original, self.island, self.castle
        )

    def test_the_advanced_save_reopens_in_the_next_stage(self):
        self.assertEqual(get_stage(self.advanced["stage"])["id"], "castle")

    def test_what_the_player_learned_travels_with_them(self):
        for field in ("challenges_passed", "topics_discovered",
                      "topics_completed", "stored_topics", "bonus_time",
                      "weapon_obtained", "weapon_equipped"):
            self.assertEqual(self.advanced[field], self.original[field], field)

    def test_the_finished_stage_is_recorded_as_complete(self):
        self.assertEqual(self.advanced["completed_stages"], ["island"])

    def test_a_stage_is_never_recorded_twice(self):
        again = advance_save_state(
            island_state(completed_stages=["island"]), self.island, self.castle
        )
        self.assertEqual(again["completed_stages"], ["island"])

    def test_stage_scoped_progress_is_left_behind(self):
        self.assertEqual(self.advanced["keys"], 0)
        self.assertIsNone(self.advanced["map_position"])
        self.assertEqual(self.advanced["stage_progress"], {})
        self.assertEqual(
            self.advanced["map_layout_version"],
            stage_world(self.castle)["map_layout_version"],
        )

    def test_hearts_are_refilled_for_the_new_stage(self):
        self.assertEqual(self.advanced["hearts"], FULL_HEARTS)

    def test_a_full_heart_row_means_the_same_everywhere(self):
        self.assertEqual(FULL_HEARTS, MAX_HEARTS)
        self.assertEqual(save_manager.new_game_state()["hearts"], FULL_HEARTS)

    def test_the_save_handed_in_is_not_mutated(self):
        self.assertEqual(self.original["keys"], 9)
        self.assertEqual(self.original["stage"], "Island")
        self.assertEqual(self.original["completed_stages"], [])

    def test_a_password_protected_save_stays_protected(self):
        protected = save_manager.protect_state(island_state(), "hunter2")
        advanced = advance_save_state(protected, self.island, self.castle)
        self.assertTrue(save_manager.is_protected(advanced))


class StageChainTests(unittest.TestCase):
    """The loop that re-enters gameplay once a stage hands over."""

    def setUp(self):
        self.runs = []
        self.slots = {}

    def _install(self, results):
        """Patch gameplay and slot loading with scripted stand-ins."""

        outcomes = list(results)

        def fake_game_screen(screen, slot_num=None, save_state=None):
            self.runs.append((save_state or {}).get("stage"))
            return outcomes.pop(0)

        self.addCleanup(
            setattr, start_game_menu, "game_screen",
            start_game_menu.game_screen,
        )
        start_game_menu.game_screen = fake_game_screen

        self.addCleanup(
            setattr, save_manager, "load_slot", save_manager.load_slot
        )
        save_manager.load_slot = lambda slot: self.slots.get(slot)

    def test_a_handoff_reloads_the_slot_and_enters_the_next_stage(self):
        self._install(["next_stage", "main_menu"])
        self.slots[1] = {"stage": "Castle"}

        result = start_game_menu.run_stage_chain(None, 1, {"stage": "Island"})

        self.assertEqual(result, "main_menu")
        self.assertEqual(self.runs, ["Island", "Castle"])

    def test_an_ordinary_exit_never_reloads_the_slot(self):
        self._install(["main_menu"])

        self.assertEqual(
            start_game_menu.run_stage_chain(None, 1, {"stage": "Island"}),
            "main_menu",
        )
        self.assertEqual(self.runs, ["Island"])

    def test_a_slot_that_will_not_reload_does_not_replay_the_finished_stage(self):
        self._install(["next_stage"])

        self.assertEqual(
            start_game_menu.run_stage_chain(None, 1, {"stage": "Island"}),
            "main_menu",
        )
        self.assertEqual(self.runs, ["Island"])


class CastleMapTests(unittest.TestCase):
    """The castle has to load, and its spawn has to be somewhere standable."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.stage = get_stage("castle")
        cls.world = stage_world(cls.stage)
        cls.tmx = load_pygame(
            str(Path(__file__).parents[1] / cls.world["map"])
        )
        cls.tile = cls.tmx.tilewidth
        cls.blocked = set()
        for layer in cls.tmx.visible_layers:
            if not hasattr(layer, "data"):
                continue
            for x, y, gid in layer:
                properties = (
                    cls.tmx.get_tile_properties_by_gid(gid) if gid else None
                )
                if properties and properties.get("collidable"):
                    cls.blocked.add((x, y))

    def spawn_cell(self):
        fraction_x, fraction_y = self.world["spawn"]
        return (
            int(fraction_x * self.tmx.width),
            int(fraction_y * self.tmx.height),
        )

    def test_the_map_the_stage_names_exists(self):
        self.assertTrue(
            (Path(__file__).parents[1] / self.world["map"]).is_file()
        )

    def test_the_spawn_is_inside_the_map_and_not_inside_a_wall(self):
        x, y = self.spawn_cell()
        self.assertTrue(0 <= x < self.tmx.width and 0 <= y < self.tmx.height)
        self.assertNotIn((x, y), self.blocked)

    def reachable_cells(self):
        """Every tile the player can walk to from the authored spawn."""

        spawn = self.spawn_cell()
        frontier = deque([spawn])
        reachable = {spawn}
        while frontier:
            x, y = frontier.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                cell = (x + dx, y + dy)
                if (cell in reachable or cell in self.blocked
                        or not 0 <= cell[0] < self.tmx.width
                        or not 0 <= cell[1] < self.tmx.height):
                    continue
                reachable.add(cell)
                frontier.append(cell)
        return reachable

    def test_the_lobby_hall_can_be_walked_to_from_the_spawn(self):
        map_width = self.tmx.width * self.tile
        map_height = self.tmx.height * self.tile
        hall = [
            cell for cell in self.reachable_cells()
            if get_zone_at(
                cell[0] * self.tile, cell[1] * self.tile,
                map_width, map_height, self.world["zones"],
            ) == "The Lobby Hall"
        ]
        self.assertTrue(hall, "the spawn is walled off from the lobby hall")

    def test_every_explore_objective_names_a_zone_that_can_be_reached(self):
        reachable_zones = {
            get_zone_at(
                cell[0] * self.tile, cell[1] * self.tile,
                self.tmx.width * self.tile, self.tmx.height * self.tile,
                self.world["zones"],
            )
            for cell in self.reachable_cells()
        }
        for objective in self.stage["objectives"]:
            if objective.get("kind") != "explore":
                continue
            self.assertIn(objective["target"], reachable_zones, objective["id"])

    def test_the_spawn_is_somewhere_the_hud_can_name(self):
        x, y = self.spawn_cell()
        zone = get_zone_at(
            x * self.tile, y * self.tile,
            self.tmx.width * self.tile, self.tmx.height * self.tile,
            self.world["zones"],
        )
        self.assertNotEqual(zone, "Wilderness")

    def test_an_interior_stage_is_not_lit_by_the_island_night(self):
        # No dirt path means no torches, and night here would be a black
        # screen rather than an atmosphere.
        self.assertFalse(self.world["night"])
        self.assertTrue(stage_world(get_stage("island"))["night"])


if __name__ == "__main__":
    unittest.main()
