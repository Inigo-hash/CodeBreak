"""Behavioral coverage for Tagama's September 7-13 task list."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame
from src import display
from src.data.challenges import CHALLENGES
from src.data.stages import get_stage, stage_world
from src.entities.enemy import Enemy
from src.screens.game import nearest_interactable
from src.systems import save_manager
from src.systems.combat import (
    PlayerCombat, move_rect, PLAYER_TORCH_HP_REGEN,
    PLAYER_ATTACK_COOLDOWN, PLAYER_INVULNERABILITY,
)
from src.systems.encounter_progress import newly_cleared_encounter_ids
from src.systems.stage_gate import evaluate_stage_gate, required_topic_ids
from src.systems.stage_handoff import advance_save_state
from src.systems.stage_progress import StageProgress
from src.ui.code_editor import CodeEditor
from test_learning_challenges import VALID_SOLUTIONS


class TagamaTasks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1920, 1080))

    def test_run_and_submit_every_campaign_challenge(self):
        for challenge_id, code in VALID_SOLUTIONS.items():
            with self.subTest(challenge=challenge_id):
                editor = CodeEditor(self.screen, CHALLENGES[challenge_id], self.screen.copy())
                editor.text_buffer.lines = code.splitlines()
                editor.run_code()
                self.assertFalse(editor.solved, "RUN must not complete a lesson")
                editor.submit_code()
                self.assertTrue(editor.solved, editor.output_panel.messages)

    def test_unexecuted_or_overwritten_answers_do_not_complete(self):
        cases = (
            ("print_001", 'if False:\n    print("Hello, World!")'),
            ("variables_001", "age = 18\nage = 19"),
            ("data_types_001", VALID_SOLUTIONS["data_types_001"] + "\nis_ready = 1"),
            ("type_casting_001", VALID_SOLUTIONS["type_casting_001"] + '\nage = "18"'),
            ("input_lesson_001", 'name = input("Enter your name: ")\nname = "Alex"'),
            ("formatted_output_001", 'name = "Alex"\nif False:\n    print(f"Welcome, {name}!")'),
        )
        for challenge_id, code in cases:
            with self.subTest(challenge=challenge_id):
                editor = CodeEditor(self.screen, CHALLENGES[challenge_id], self.screen.copy())
                editor.text_buffer.lines = code.splitlines()
                editor.submit_code()
                self.assertFalse(editor.solved)

    def test_enemies_require_clear_sight_and_return_after_disengaging(self):
        for species in ("manananggal", "tikbalang", "tiyanak_sinta"):
            with self.subTest(species=species):
                enemy = Enemy(self.screen, 1000, 1000, 200, 200, enemy_id=species)
                player = pygame.Rect(295, 190, 20, 20)
                wall = pygame.Rect(250, 150, 10, 100)
                enemy.update(0.01, player, [wall], 1000, 1000)
                self.assertEqual(enemy.state, "idle")
                enemy.update(0.01, player, [], 1000, 1000)
                self.assertEqual(enemy.state, "alert")
                enemy.update(0.2, player, [], 1000, 1000)
                self.assertEqual(enemy.state, "chase")
                player.center = (950, 950)
                enemy.update(0.01, player, [], 1000, 1000)
                self.assertEqual(enemy.state, "return")
                enemy.update(0.01, player, [], 1000, 1000)
                self.assertEqual(enemy.state, "idle")

    def test_each_enemy_attack_connects_once_and_respects_cooldown(self):
        for species in ("manananggal", "tikbalang", "tiyanak_sinta"):
            with self.subTest(species=species):
                enemy = Enemy(self.screen, 1000, 1000, 200, 200, enemy_id=species)
                player = pygame.Rect(230, 190, 20, 20)
                enemy.state = "chase"
                enemy.update(0.001, player, [player], 1000, 1000, navigation_rects=[])
                self.assertEqual(enemy.state, "attack")
                damage = [enemy.update(0.01, player, [player], 1000, 1000, navigation_rects=[])
                          for _ in range(80)]
                self.assertEqual(sum(damage), enemy.stats.attack_damage)

    def test_player_dodge_damage_grace_and_attack_cooldown(self):
        combat = PlayerCombat()
        self.assertTrue(combat.start_dodge())
        self.assertFalse(combat.take_damage(10))
        combat.update(0.25)
        self.assertTrue(combat.take_damage(10))
        self.assertFalse(combat.take_damage(10))
        combat.update(PLAYER_INVULNERABILITY + 0.01)
        self.assertTrue(combat.start_attack())
        self.assertFalse(combat.start_attack())
        combat.update(PLAYER_ATTACK_COOLDOWN)
        self.assertTrue(combat.start_attack())

    def test_movement_preserves_fractional_speed_and_cannot_skip_walls(self):
        bounds = pygame.Rect(0, 0, 500, 500)
        rect = pygame.Rect(10, 10, 10, 10)
        x, y = 10.0, 10.0
        for _ in range(10):
            x, y = move_rect(rect, x, y, 0.2, 0, [], bounds)
        self.assertEqual(rect.x, 12)
        wall = pygame.Rect(50, 0, 2, 500)
        move_rect(rect, x, y, 150, 0, [wall], bounds)
        self.assertEqual(rect.right, wall.left)

    def test_interactions_cannot_pass_through_walls_but_allow_prop_art(self):
        player = pygame.Rect(0, 20, 10, 10)
        prop = {"rect": pygame.Rect(30, 20, 16, 16)}
        wall = pygame.Rect(20, 0, 2, 100)
        self.assertIsNone(nearest_interactable(player, [prop], blockers=[wall]))
        self.assertIs(nearest_interactable(player, [prop], blockers=[prop["rect"]]), prop)

    def test_healing_only_uses_time_after_the_damage_delay(self):
        combat = PlayerCombat()
        combat.take_damage(80)
        combat.update(2.5, hp_regen=PLAYER_TORCH_HP_REGEN)
        self.assertEqual(combat.hp, 20 + int(0.5 * PLAYER_TORCH_HP_REGEN))

    def test_save_write_failure_preserves_previous_progress(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(save_manager, "SAVE_DIR", folder):
            original = save_manager.new_game_state()
            save_manager.save_slot(1, original)
            with self.assertRaises(TypeError):
                save_manager.save_slot(1, {"not_json": object()})
            self.assertEqual(save_manager.load_slot(1), original)
            with patch.object(save_manager.os, "replace", side_effect=OSError("interrupted")):
                with self.assertRaises(OSError):
                    save_manager.save_slot(1, {"keys": 3})
            self.assertEqual(save_manager.load_slot(1), original)
            self.assertEqual([p.name for p in Path(folder).iterdir()], ["slot_1.json"])

    def test_campaign_progress_round_trip_through_all_encounters_and_gate(self):
        stage = get_stage("island")
        state = save_manager.new_game_state()
        progress = StageProgress()
        encounters = stage_world(stage)["encounters"]
        ids = [encounter["id"] for encounter in encounters]
        enemies = [SimpleNamespace(group_id=group, state="chase") for group in ids]
        with tempfile.TemporaryDirectory() as folder, patch.object(save_manager, "SAVE_DIR", folder):
            for enemy in enemies:
                enemy.state = "defeated"
                cleared = newly_cleared_encounter_ids(enemies, ids, progress.cleared_encounters)
                for group in cleared:
                    progress.clear_encounter(group)
                    state["keys"] += 1
                state["stage_progress"] = progress.to_dict()
                save_manager.save_slot(1, state)
                state = save_manager.load_slot(1)
                progress = StageProgress.from_dict(state["stage_progress"])
                self.assertFalse(newly_cleared_encounter_ids(enemies, ids, progress.cleared_encounters))
            self.assertEqual(state["keys"], len(ids))
            self.assertFalse(evaluate_stage_gate(stage, state["keys"], []).unlocked)
            state["challenges_passed"] = list(required_topic_ids(stage))
            self.assertFalse(evaluate_stage_gate(stage, state["keys"], state["challenges_passed"]).unlocked)
            boss = stage["completion"]["required_boss"]
            self.assertTrue(evaluate_stage_gate(stage, state["keys"], state["challenges_passed"], [boss]).unlocked)
            transitioned = advance_save_state(state, stage, get_stage("castle"))
            save_manager.save_slot(1, transitioned)
            self.assertEqual(save_manager.load_slot(1), transitioned)
            self.assertEqual(transitioned["keys"], 0)
            self.assertEqual(transitioned["challenges_passed"], state["challenges_passed"])

    def test_laptop_desktop_letterboxing_and_mouse_drag_coordinates(self):
        for size in ((1280, 720), (1366, 768), (1920, 1080), (2560, 1440), (1280, 1024), (2560, 1080)):
            with self.subTest(size=size), patch.object(display, "_window", pygame.Surface(size)):
                scale, offset, scaled = display._viewport(size)
                self.assertLessEqual(scaled[0], size[0])
                self.assertLessEqual(scaled[1], size[1])
                center = (offset[0] + scaled[0] // 2, offset[1] + scaled[1] // 2)
                virtual = display.window_to_virtual(center)
                self.assertLessEqual(abs(virtual[0] - 960), 1)
                self.assertLessEqual(abs(virtual[1] - 540), 1)
                event = pygame.event.Event(pygame.MOUSEMOTION, pos=center, rel=(20, 10), buttons=(1, 0, 0))
                with patch.object(display, "_original_event_get", return_value=[event]):
                    converted = display._events()[0]
                self.assertEqual(converted.rel, (20 / scale, 10 / scale))
                if any(offset):
                    self.assertEqual(display.window_to_virtual((0, 0)), (-1, -1))


if __name__ == "__main__":
    unittest.main()
