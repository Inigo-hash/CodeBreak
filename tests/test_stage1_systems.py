"""Coverage for Stage 1 chests, exploration, debug gating, and Stage 2 data."""

import os
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.data.items import item_id_for_action
from src.data.stages import get_stage, stage_challenges
from src.entities.chest import Chest
from src.systems.stage_progress import StageProgress


class ChestTests(unittest.TestCase):
    def test_reward_and_trap_resolve_only_once(self):
        reward = Chest((0, 0, 32, 32), reward_seconds=30)
        self.assertEqual(reward.open(10)[0], 40)
        self.assertEqual(reward.open(40)[0], 40)

        trap = Chest((0, 0, 32, 32), trap_seconds=15)
        self.assertEqual(trap.open(20)[0], 5)
        self.assertEqual(trap.open(5)[0], 5)

    def test_map_authors_one_reward_chest_and_one_trapped_chest(self):
        root = ET.parse(Path("assets/map/tmx/basic.tmx")).getroot()
        chest_objects = []
        for obj in root.findall(".//object"):
            properties = {
                prop.get("name"): prop.get("value")
                for prop in obj.findall("./properties/property")
            }
            if properties.get("actions") == "search_chest":
                chest_objects.append(properties)
        self.assertEqual(len(chest_objects), 2)
        self.assertTrue(any("reward_seconds" in item for item in chest_objects))
        self.assertTrue(any("trap_seconds" in item for item in chest_objects))
        self.assertEqual(item_id_for_action("search_chest"), "chest")


class StageProgressCompletionTests(unittest.TestCase):
    def test_exploration_and_opened_chests_round_trip(self):
        progress = StageProgress()
        self.assertTrue(progress.visit_zone("Amber Hollow"))
        self.assertTrue(progress.open_interactable("1504"))
        self.assertFalse(progress.open_interactable("1504"))

        restored = StageProgress.from_dict(progress.to_dict())
        self.assertTrue(restored.knows_zone("Amber Hollow"))
        self.assertTrue(restored.has_opened_interactable("1504"))

    def test_explore_and_chest_objectives_complete(self):
        stage = get_stage("island")
        progress = StageProgress(discovered_items=("chest",))
        progress.visit_zone("Amber Hollow")
        progress.sync_objectives(stage)
        self.assertTrue(progress.is_objective_done("island_open_chest"))
        self.assertTrue(progress.is_objective_done("island_explore_amber_hollow"))


class StageScaffoldAndDebugTests(unittest.TestCase):
    def test_castle_scaffold_is_distinct_and_has_empty_topic_list(self):
        castle = get_stage("castle")
        self.assertEqual(castle["id"], "castle")
        self.assertFalse(castle["playable"])
        self.assertEqual(castle["manual"]["topics"], [])
        self.assertEqual(stage_challenges(castle), [])

    def test_preview_hotkeys_are_guarded_by_debug_mode(self):
        for path in (
            Path("src/screens/game.py"),
            Path("src/screens/world_map.py"),
            Path("src/screens/game_over.py"),
        ):
            source = path.read_text(encoding="utf-8")
            for line in source.splitlines():
                if any(key in line for key in (
                    "pygame.K_F1", "pygame.K_F2", "pygame.K_F5",
                    "pygame.K_F6", "pygame.K_F8",
                )):
                    self.assertIn("DEBUG_MODE", line, f"unguarded debug key: {line}")


if __name__ == "__main__":
    unittest.main()
