"""Real gameplay doorway and ending checkpoints, using temporary saves only."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import inspect
import tempfile
import copy
import xml.etree.ElementTree as ET
import unittest
from unittest.mock import patch

import pygame

from src.data.stages import get_stage, stage_world
from src.screens import game
from src.systems import save_manager
from src.systems.developer_mode import developer_mode
from src.systems.stage_gate import required_topic_ids


class FinishedFrames(Exception):
    pass


def gameplay_locals():
    frame = inspect.currentframe()
    while frame:
        if frame.f_code is game.game_screen.__code__:
            return frame.f_locals
        frame = frame.f_back
    return None


class Stage1EndingRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def run_frames(self, state, *, developer=False, debug=True, events=None,
                   check=None, doorway=True, expect_next=False):
        frames = 0
        saved = None
        state = copy.deepcopy(state)
        if doorway:
            world = stage_world(get_stage("island"))
            root = ET.parse(world["map"]).getroot()
            width = int(root.get("width")) * int(root.get("tilewidth"))
            height = int(root.get("height")) * int(root.get("tileheight"))
            zone = next(zone for zone in world["zones"] if zone.get("is_boss_zone"))
            x, y, w, h = zone["rect"]
            state["map_layout_version"] = world["map_layout_version"]
            state["map_position"] = [round((x + w / 2) * width), round((y + h) * height) - 40]

        def get_events():
            live = gameplay_locals()
            if live is None or "dt" not in live:
                return []
            return events(frames, live) if events else []

        def present():
            nonlocal frames, saved
            live = gameplay_locals()
            if live is None or "previous_player_position" not in live:
                return
            frames += 1
            if check:
                check(frames, live)
            if frames >= 3:
                save_manager.save_slot(1, live["build_save_state"]())
                saved = save_manager.load_slot(1)
                raise FinishedFrames()

        with tempfile.TemporaryDirectory() as folder, patch.object(
            save_manager, "SAVE_DIR", folder
        ), patch.object(developer_mode, "enabled", developer), patch.object(
            game, "DEBUG_MODE", debug
        ), patch.object(game.StageLoadingScreen, "finish", lambda self: None), patch(
            "pygame.event.get", side_effect=get_events
        ), patch("pygame.display.flip", side_effect=present), patch.object(
            game, "open_boss_intro", return_value="fight"
        ) as intro, patch.object(game, "open_stage_gate", side_effect=lambda screen, status, **kwargs:
            "exit" if expect_next and status.unlocked else "stay"), patch.object(
            game, "open_boss_result", return_value="continue"
        ) as result, patch.object(game, "open_final_challenge_warning", return_value="later") as warning:
            if expect_next:
                self.assertEqual(game.game_screen(self.screen, slot_num=1, save_state=state), "next_stage")
                saved = save_manager.load_slot(1)
            else:
                with self.assertRaises(FinishedFrames):
                    game.game_screen(self.screen, slot_num=1, save_state=state)
            return saved, intro.call_count, result.call_count, warning.call_count

    def test_doorway_access_matrix_and_no_fabricated_progress(self):
        stage = get_stage("island")
        for developer, earned, expected in ((True, False, 1), (False, False, 0), (False, True, 1)):
            with self.subTest(developer=developer, earned=earned):
                state = save_manager.new_game_state()
                if earned:
                    state["keys"] = 9
                    state["challenges_passed"] = list(required_topic_ids(stage))
                def check(frame, live):
                    self.assertEqual(live["boss_enemy"] is not None, bool(expected))
                    if expected:
                        self.assertIn(live["boss_enemy"], live["enemies"])
                saved, intros, _, _ = self.run_frames(state, developer=developer, check=check)
                self.assertEqual(intros, expected)
                self.assertEqual(saved["keys"], state["keys"])
                self.assertEqual(saved["challenges_passed"], state["challenges_passed"])
                self.assertEqual(saved["completed_stages"], [])
                self.assertNotIn("developer_mode", saved)

    def test_enabling_f4_after_locked_approach_rearms_doorway(self):
        def events(frame, live):
            return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F4)] if frame == 1 else []
        _, intros, _, _ = self.run_frames(save_manager.new_game_state(), events=events)
        self.assertEqual(intros, 1)

    def test_developer_mode_does_not_spawn_boss_outside_doorway(self):
        _, intros, _, _ = self.run_frames(save_manager.new_game_state(), developer=True, doorway=False)
        self.assertEqual(intros, 0)

    def test_boss_defeat_checkpoint_is_once_and_reload_reveals_final(self):
        def defeat(frame, live):
            if frame == 1:
                live["boss_enemy"].state = "defeated"
                live["boss_enemy"].active = False
            elif frame == 2:
                checkpoint = save_manager.load_slot(1)
                self.assertIn(live["boss_id"], checkpoint["stage_progress"]["defeated_enemies"])
        saved, intros, results, warnings = self.run_frames(
            save_manager.new_game_state(), developer=True, check=defeat)
        self.assertEqual((intros, results, warnings), (1, 1, 1))
        boss = get_stage("island")["completion"]["required_boss"]
        self.assertIn(boss, saved["stage_progress"]["defeated_enemies"])
        def restored(frame, live):
            self.assertIsNone(live["boss_enemy"])
            self.assertTrue(live["final_challenge_revealed"])
        _, intros, results, warnings = self.run_frames(saved, developer=True, check=restored)
        self.assertEqual((intros, results, warnings), (0, 0, 0))

    def test_release_f6_cannot_open_final_challenge_preview(self):
        def events(frame, live):
            return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F6)] if frame == 0 else []
        with patch.object(game, "CodeEditor") as editor:
            self.run_frames(save_manager.new_game_state(), debug=False, events=events, doorway=False)
        editor.assert_not_called()

    def test_boss_phase_waves_do_not_overlap_or_relocate_existing_bodies(self):
        def check(frame, live):
            if frame != 1:
                return
            boss = live["boss_enemy"]
            for phase in live["boss_phases"]["phases"]:
                existing = [enemy for enemy in live["enemies"] if enemy.active]
                positions = [enemy.rect.copy() for enemy in existing]
                with patch.object(game.random, "choice", return_value="tikbalang"):
                    live["trigger_boss_phase"](phase.threshold)
                for enemy, position in zip(existing, positions):
                    self.assertEqual(enemy.rect, position)
                summons = [enemy for enemy in live["enemies"] if enemy not in existing]
                self.assertTrue(summons)
                for summon in summons:
                    self.assertEqual(summon.rect.collidelist(positions + [live["player_rect"]]), -1)
                # Free the bounded wave slots to exercise the next phase.
                for enemy in summons:
                    enemy.active = False
            self.assertEqual(boss.phase_thresholds_triggered, {750, 500, 250})
        self.run_frames(save_manager.new_game_state(), developer=True, check=check)

    def test_final_submit_at_exit_saves_and_hands_off_to_castle(self):
        stage = get_stage("island")
        state = save_manager.new_game_state()
        state["keys"] = 9
        state["challenges_passed"] = list(required_topic_ids(stage))
        state["stage_progress"] = {"defeated_enemies": [stage["completion"]["required_boss"]]}
        world = stage_world(stage)
        root = ET.parse(world["map"]).getroot()
        width = int(root.get("width")) * int(root.get("tilewidth"))
        height = int(root.get("height")) * int(root.get("tileheight"))
        x, y, w, h = stage["completion"]["exit_rect"]
        state["map_layout_version"] = world["map_layout_version"]
        state["map_position"] = [round((x + w / 2) * width), round((y + h / 2) * height)]

        def events(frame, live):
            if frame == 1:
                self.assertIn("stage1_final_001", save_manager.load_slot(1)["challenges_passed"])
            return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)]

        # The validator is exercised with real code in test_tagama_tasks.
        # Here the editor supplies the solved outcome to exercise the game save path.
        with patch.object(game, "CodeEditor") as editor:
            editor.return_value.solved = True
            # Dismiss the gate so we can reload the final-completion checkpoint.
            saved, _, _, _ = self.run_frames(state, events=events, doorway=False)
        self.assertEqual(saved["challenges_passed"].count("stage1_final_001"), 1)
        self.assertEqual(editor.call_count, 1)
        self.assertEqual(saved["completed_stages"], [])

        def gate_events(frame, live):
            return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)]

        # Gate authorization is checked by the helper's gate callback.
        with patch.object(game, "CodeEditor") as editor:
            saved, _, _, _ = self.run_frames(saved, events=gate_events, doorway=False, expect_next=True)
        editor.assert_not_called()
        self.assertEqual(saved["stage"], "Castle")
        self.assertEqual(saved["completed_stages"], ["island"])
        self.assertIn("stage1_final_001", saved["challenges_passed"])
