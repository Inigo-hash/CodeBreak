"""Regression tests for the 10-key, all-topics stage exit gate."""

import os
from collections import deque
from pathlib import Path
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from pytmx.util_pygame import load_pygame

from src.data.challenges import CHALLENGES
from src.data.stages import get_stage, stage_world
from src.data.topics import TOPICS
from src.screens.stage_gate import open_stage_gate
from src.systems.stage_gate import (
    award_topic_keys, earned_topic_keys, evaluate_boss_access,
    evaluate_stage_gate,
    migrate_key_count, required_topic_ids,
)


class StageGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def setUp(self):
        self.stage = get_stage("island")
        self.world = stage_world(self.stage)
        self.required_topics = required_topic_ids(self.stage)
        self.defeated_boss = (self.stage["completion"]["required_boss"],)

    def test_island_has_ten_real_required_topics_and_ten_keys(self):
        self.assertEqual(len(self.required_topics), 10)
        self.assertTrue(all(topic in CHALLENGES for topic in self.required_topics))
        self.assertEqual(earned_topic_keys(self.stage, self.required_topics), 10)

    def test_every_required_topic_is_reachable_from_an_authored_map_object(self):
        map_path = Path(__file__).parents[1] / self.world["map"]
        root = ET.parse(map_path).getroot()
        mapped_topic_ids = {
            prop.get("value")
            for prop in root.findall(".//object/properties/property")
            if prop.get("name") == "topic_id" and prop.get("value")
        }
        mapped_challenges = {
            TOPICS[topic_id]["challenge_id"]
            for topic_id in mapped_topic_ids
            if topic_id in TOPICS
        }
        self.assertTrue(set(self.required_topics).issubset(mapped_challenges))

        tmx = load_pygame(str(map_path))
        tile_size = tmx.tilewidth
        blocked = set()
        for layer in tmx.visible_layers:
            if not hasattr(layer, "data"):
                continue
            for x, y, gid in layer:
                properties = tmx.get_tile_properties_by_gid(gid) if gid else None
                if properties and properties.get("collidable"):
                    blocked.add((x, y))

        map_width = tmx.width * tile_size
        map_height = tmx.height * tile_size
        spawn = self._spawn_cell(map_width, map_height, tile_size)
        frontier = deque([spawn])
        reachable_cells = {spawn}
        while frontier:
            x, y = frontier.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (x + dx, y + dy)
                if (
                    neighbor not in reachable_cells
                    and neighbor not in blocked
                    and 0 <= neighbor[0] < tmx.width
                    and 0 <= neighbor[1] < tmx.height
                ):
                    reachable_cells.add(neighbor)
                    frontier.append(neighbor)

        reachable_challenges = set()
        for obj in root.findall(".//object"):
            properties = {
                prop.get("name"): prop.get("value")
                for prop in obj.findall("./properties/property")
            }
            topic = TOPICS.get(properties.get("topic_id"))
            if not topic:
                continue
            rect = pygame.Rect(
                round(float(obj.get("x", 0))),
                round(float(obj.get("y", 0))),
                max(1, round(float(obj.get("width", 1)))),
                max(1, round(float(obj.get("height", 1)))),
            )
            nearby = {
                (x, y)
                for x in range(max(0, rect.left // tile_size - 2),
                               min(tmx.width - 1, rect.right // tile_size + 2) + 1)
                for y in range(max(0, rect.top // tile_size - 2),
                               min(tmx.height - 1, rect.bottom // tile_size + 2) + 1)
            }
            if nearby & reachable_cells:
                reachable_challenges.add(topic["challenge_id"])

        self.assertTrue(
            set(self.required_topics).issubset(reachable_challenges),
            "At least one required Stage 1 lesson cannot be reached from spawn",
        )

    def _spawn_cell(self, map_width, map_height, tile_size):
        """The authored spawn from stages.py, as a tile coordinate."""

        spawn_x, spawn_y = self.world["spawn"]
        return (
            round(spawn_x * map_width) // tile_size,
            round(spawn_y * map_height) // tile_size,
        )

    def test_castle_exit_trigger_is_reachable_from_player_spawn(self):
        map_path = Path(__file__).parents[1] / self.world["map"]
        tmx = load_pygame(str(map_path))
        tile_size = tmx.tilewidth
        blocked = set()
        for layer in tmx.visible_layers:
            if not hasattr(layer, "data"):
                continue
            for x, y, gid in layer:
                properties = tmx.get_tile_properties_by_gid(gid) if gid else None
                if properties and properties.get("collidable"):
                    blocked.add((x, y))

        map_width = tmx.width * tile_size
        map_height = tmx.height * tile_size
        exit_x, exit_y, exit_width, exit_height = self.stage["completion"]["exit_rect"]
        exit_detection = pygame.Rect(
            round(exit_x * map_width),
            round(exit_y * map_height),
            round(exit_width * map_width),
            round(exit_height * map_height),
        ).inflate(tile_size * 4, tile_size * 4)

        spawn = self._spawn_cell(map_width, map_height, tile_size)

        frontier = deque([spawn])
        visited = {spawn}
        reached = False
        while frontier:
            cell = frontier.popleft()
            cell_rect = pygame.Rect(
                cell[0] * tile_size, cell[1] * tile_size,
                tile_size, tile_size,
            )
            if cell_rect.colliderect(exit_detection):
                reached = True
                break
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (cell[0] + dx, cell[1] + dy)
                if (
                    neighbor not in visited
                    and neighbor not in blocked
                    and 0 <= neighbor[0] < tmx.width
                    and 0 <= neighbor[1] < tmx.height
                ):
                    visited.add(neighbor)
                    frontier.append(neighbor)

        self.assertTrue(reached, "The authored castle exit cannot be reached from spawn")

    def test_ten_keys_cannot_bypass_a_missing_topic(self):
        status = evaluate_stage_gate(
            self.stage, 10, self.required_topics[:-1], self.defeated_boss
        )
        self.assertFalse(status.unlocked)
        self.assertEqual(status.completed_topics, len(self.required_topics) - 1)
        self.assertEqual(status.missing_topic_ids, (self.required_topics[-1],))

    def test_all_topics_cannot_bypass_missing_keys(self):
        status = evaluate_stage_gate(
            self.stage, 9, self.required_topics, self.defeated_boss
        )
        self.assertFalse(status.unlocked)
        self.assertEqual(status.keys, 9)
        self.assertFalse(status.missing_topic_ids)

    def test_ten_keys_and_every_topic_unlock_the_exit(self):
        status = evaluate_stage_gate(
            self.stage, 10, self.required_topics, self.defeated_boss
        )
        self.assertTrue(status.unlocked)
        self.assertEqual(status.completed_topics, status.required_topics)

    def test_keys_and_topics_cannot_bypass_required_boss(self):
        status = evaluate_stage_gate(
            self.stage, 10, self.required_topics, defeated_enemies=()
        )
        self.assertFalse(status.unlocked)
        self.assertFalse(status.boss_defeated)
        self.assertEqual(
            status.required_boss_id,
            self.stage["completion"]["required_boss"],
        )

    def test_boss_access_does_not_report_an_unfought_boss_as_defeated(self):
        locked = evaluate_boss_access(self.stage, 0, ())
        self.assertFalse(locked.unlocked)
        self.assertFalse(locked.boss_defeated)

        ready = evaluate_boss_access(self.stage, 10, self.required_topics)
        self.assertTrue(ready.unlocked)
        self.assertFalse(ready.boss_defeated)

    def test_first_completion_rewards_cap_at_ten(self):
        keys = 0
        for challenge_id in self.required_topics:
            keys = award_topic_keys(keys, self.stage, challenge_id)
        self.assertEqual(keys, 10)
        self.assertEqual(
            award_topic_keys(keys, self.stage, self.required_topics[0]), 10
        )

    def test_old_save_recovers_keys_for_completed_required_topics(self):
        completed = self.required_topics[:3]
        expected = earned_topic_keys(self.stage, completed)
        self.assertGreater(expected, 0)
        self.assertEqual(
            migrate_key_count(0, self.stage, completed), expected
        )
        # A legitimate larger saved total is preserved, while bad overflow
        # can never exceed the authored stage maximum.
        self.assertEqual(migrate_key_count(8, self.stage, completed), 8)
        self.assertEqual(migrate_key_count(999, self.stage, completed), 10)


class StageGateModalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))
        cls.stage = get_stage("island")
        cls.topics = required_topic_ids(cls.stage)
        cls.defeated_boss = (cls.stage["completion"]["required_boss"],)

    def setUp(self):
        pygame.event.clear()

    def test_confirm_key_cannot_exit_while_requirements_are_missing(self):
        locked = evaluate_stage_gate(
            self.stage, 10, self.topics[:-1], self.defeated_boss
        )
        confirm_event = pygame.event.Event(
            pygame.KEYDOWN, {"key": pygame.K_e, "unicode": "e"}
        )
        # The empty first frame exercises the complete render path before the
        # confirmation event proves a locked gate cannot return "exit".
        with patch("pygame.event.get", side_effect=[[], [confirm_event]]):
            self.assertEqual(open_stage_gate(self.screen, locked), "stay")

    def test_confirm_key_exits_only_after_both_requirements_pass(self):
        unlocked = evaluate_stage_gate(
            self.stage, 10, self.topics, self.defeated_boss
        )
        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN, {"key": pygame.K_RETURN, "unicode": "\r"}
        ))
        self.assertEqual(open_stage_gate(self.screen, unlocked), "exit")

    def test_escape_keeps_player_in_stage_even_when_gate_is_open(self):
        unlocked = evaluate_stage_gate(
            self.stage, 10, self.topics, self.defeated_boss
        )
        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN, {"key": pygame.K_ESCAPE, "unicode": ""}
        ))
        self.assertEqual(open_stage_gate(self.screen, unlocked), "stay")


if __name__ == "__main__":
    unittest.main()
