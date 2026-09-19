"""Atlas interaction, campaign unlocks, checkpoints and screen transforms."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import copy
import tempfile
import unittest
from unittest.mock import patch
import pygame

from src import display
from src.data.stages import STAGES, get_stage
from src.data.stage_map import STAGE_MAP_NODES
from src.screens.stage_select import (
    ART_SIZE, _original_art, draw_stage_select, hotspot_at, map_to_screen,
    open_stage_select, screen_to_map, stage_select_layout,
)
from src.systems import save_manager
from src.systems.stage_handoff import advance_save_state, STAGE_SCOPED_KEYS
from src.systems.stage_selection import select_stage, stage_available, stage_status, stage_unlocked

SIZES = ((1280, 720), (1366, 768), (1920, 1080), (2560, 1440), (1280, 1024), (2560, 1080))


class StageSelectionRules(unittest.TestCase):
    def test_new_save_unlocks_only_existing_stage_one(self):
        state = save_manager.new_game_state()
        self.assertTrue(stage_available("island", state))
        self.assertEqual(stage_status("island", state), "CURRENT")
        for target in ("castle", "citadel"):
            self.assertEqual(stage_status(target, state), "LOCKED")
            with self.assertRaises(ValueError):
                select_stage(state, target)
        self.assertFalse(stage_available("unknown", state, True))

    def test_completion_unlocks_next_landmark_but_requires_a_playable_map(self):
        state = save_manager.new_game_state()
        state["completed_stages"] = ["island"]
        self.assertEqual(stage_status("island", state), "COMPLETED")
        self.assertTrue(stage_available("island", state))
        self.assertTrue(stage_available("castle", state))
        self.assertFalse(stage_unlocked("citadel", state))
        state["completed_stages"].append("castle")
        self.assertTrue(stage_unlocked("citadel", state))
        self.assertEqual(stage_status("citadel", state), "COMING SOON")
        self.assertFalse(stage_available("citadel", state))
        with patch.dict(STAGES, {"citadel": {"id": "citadel", "name": "Citadel", "world": {"map": "future.tmx"}}}):
            self.assertTrue(stage_available("citadel", state))
            self.assertEqual(select_stage(state, "citadel")["stage"], "Citadel")

    def test_developer_bypass_does_not_complete_any_stage_or_enable_missing_map(self):
        state = save_manager.new_game_state()
        selected = select_stage(state, "castle", developer_access=True)
        self.assertEqual(selected["completed_stages"], [])
        self.assertEqual(selected["challenges_passed"], [])
        self.assertFalse(stage_available("citadel", state, developer_access=True))
        self.assertNotIn("developer_mode", selected)

    def test_old_castle_saves_remain_accessible(self):
        state = {"stage": "Castle", "keys": 0}
        self.assertTrue(stage_available("castle", state))
        self.assertEqual(select_stage(state, "castle"), state)
        island = select_stage(state, "island")
        self.assertEqual(island["stage_progress"], {})
        self.assertIsNotNone(island["map_layout_version"])

    def test_checkpoint_switch_round_trip_preserves_campaign_and_security(self):
        state = save_manager.new_game_state()
        state.update(completed_stages=["island"], keys=9, map_position=[400, 500], map_layout_version=2,
                     stage_progress={"defeated_enemies": ["corrupted_core_kapre"], "opened_interactables": ["1504"]},
                     challenges_passed=["stage1_final_001"], stored_topics=["variables"],
                     weapon_equipped=False, _security={"test": "preserved"})
        original = copy.deepcopy(state)
        castle = select_stage(state, "castle")
        castle["map_position"] = [600, 700]
        castle["stage_progress"] = {"visited_zones": ["Lobby"]}
        with tempfile.TemporaryDirectory() as directory, patch.object(save_manager, "SAVE_DIR", directory):
            save_manager.save_slot(1, castle)
            restored = select_stage(save_manager.load_slot(1), "island")
            for key in STAGE_SCOPED_KEYS:
                self.assertEqual(restored.get(key), original.get(key), key)
            for key in ("completed_stages", "challenges_passed", "stored_topics", "weapon_equipped", "_security"):
                self.assertEqual(restored[key], original[key], key)
            save_manager.save_slot(1, restored)
            back = select_stage(save_manager.load_slot(1), "castle")
            self.assertEqual(back["map_position"], [600, 700])
            self.assertEqual(back["stage_progress"], castle["stage_progress"])
        self.assertEqual(state, original)

    def test_campaign_exit_keeps_finished_map_checkpoint_for_return(self):
        state = save_manager.new_game_state()
        state.update(keys=9, map_position=[100, 200], stage_progress={"defeated_enemies": ["corrupted_core_kapre"]})
        advanced = advance_save_state(state, get_stage("island"), get_stage("castle"))
        returned = select_stage(advanced, "island")
        self.assertEqual(returned["stage_progress"], state["stage_progress"])
        self.assertEqual(returned["map_position"], state["map_position"])
        self.assertEqual(returned["keys"], 9)


class StageSelectionUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def test_full_image_and_hotspots_at_all_supported_resolutions(self):
        self.assertEqual(_original_art().get_size(), ART_SIZE)
        for size in SIZES:
            with self.subTest(size=size):
                screen = pygame.Surface(size)
                layout = draw_stage_select(screen, save_manager.new_game_state())
                self.assertTrue(screen.get_rect().contains(layout["map"]))
                self.assertTrue(screen.get_rect().contains(layout["panel"]))
                self.assertTrue(layout["panel"].contains(layout["enter"]))
                self.assertAlmostEqual(layout["map"].w / layout["map"].h, ART_SIZE[0] / ART_SIZE[1], places=2)
                for index, node in enumerate(STAGE_MAP_NODES):
                    self.assertEqual(hotspot_at(layout["plaques"][index].center, layout), index)
                    self.assertEqual(hotspot_at(layout["markers"][index], layout), index)
                    self.assertEqual(hotspot_at(map_to_screen(node["marker"], layout["map"]), layout), index)
                    point = map_to_screen(node["marker"], layout["map"])
                    normal = screen_to_map(point, layout["map"])
                    self.assertAlmostEqual(normal[0], node["marker"][0], places=2)
                    self.assertFalse(layout["panel"].colliderect(layout["plaques"][index]))
                self.assertIsNone(hotspot_at(layout["panel"].center, layout))
                self.assertIsNone(hotspot_at((0, 0), layout))

    def test_display_mouse_transform_and_landmark_transform_compose(self):
        for size in SIZES:
            canvas = pygame.Surface(display.canvas_size_for_window(size))
            layout = stage_select_layout(canvas.get_size())
            with patch.object(display, "_canvas", canvas), patch.object(display, "_window", pygame.Surface(size)):
                scale, offset, _ = display._viewport(size)
                for index, plaque in enumerate(layout["plaques"]):
                    physical = tuple(round(value*scale+origin) for value, origin in zip(plaque.center, offset))
                    self.assertEqual(hotspot_at(display.window_to_virtual(physical), layout), index)

    def test_hover_and_click_stage_one_then_enter(self):
        layout = stage_select_layout(self.screen.get_size())
        position = map_to_screen((.32, .76), layout["map"])
        self.assertEqual(hotspot_at(position, layout), 0)
        events = [pygame.event.Event(pygame.MOUSEMOTION, pos=position),
                  pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position),
                  pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=layout["enter"].center)]
        with patch("pygame.event.get", return_value=events):
            self.assertEqual(open_stage_select(self.screen, save_manager.new_game_state()), "island")

    def test_locked_landmarks_never_enter(self):
        layout = stage_select_layout(self.screen.get_size())
        for index in (1, 2):
            events = [pygame.event.Event(pygame.MOUSEMOTION, pos=layout["plaques"][index].center),
                      pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=layout["enter"].center),
                      pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN),
                      pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]
            with patch("pygame.event.get", return_value=events):
                self.assertIsNone(open_stage_select(self.screen, save_manager.new_game_state()))

    def test_completed_stage_keyboard_selection_and_cancellation(self):
        state = save_manager.new_game_state()
        state.update(stage="Castle", completed_stages=["island"])
        with patch("pygame.event.get", return_value=[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN),
                                                    pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]):
            self.assertEqual(open_stage_select(self.screen, state), "island")
        with patch("pygame.event.get", return_value=[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]):
            self.assertIsNone(open_stage_select(self.screen, state))

    def test_launch_selects_existing_game_map_and_cancellation_does_not_save(self):
        from src.screens import start_game_menu as menu
        state = save_manager.new_game_state()
        with tempfile.TemporaryDirectory() as directory, patch.object(save_manager, "SAVE_DIR", directory), patch.object(
            menu, "open_stage_select", return_value="island"
        ), patch.object(menu, "game_screen", return_value="main_menu") as game:
            self.assertEqual(menu.launch_selected_stage(self.screen, 1, state), "main_menu")
            self.assertEqual(game.call_args.kwargs["save_state"]["stage"], "Island")
            self.assertEqual(save_manager.load_slot(1)["stage"], "Island")
            with patch.object(menu, "open_stage_select", return_value=None), patch.object(save_manager, "save_slot") as write:
                self.assertEqual(menu.launch_selected_stage(self.screen, 1, state), "stage_selection_cancelled")
                write.assert_not_called()

    def test_selected_island_boots_and_gameplay_preserves_other_map_checkpoint(self):
        from test_stage1_ending_regressions import Stage1EndingRegressions
        fixture = Stage1EndingRegressions()
        fixture.screen = self.screen
        state = save_manager.new_game_state()
        state.update(stage="Castle", completed_stages=["island"], map_position=[600, 700],
                     stage_progress={"visited_zones": ["Lobby"]})
        selected = select_stage(state, "island")
        saved, intros, _, _ = fixture.run_frames(selected, doorway=False)
        self.assertEqual(saved["stage"], "Island")
        self.assertEqual(saved["stage_checkpoints"]["castle"]["map_position"], [600, 700])
        self.assertEqual(saved["stage_checkpoints"]["castle"]["stage_progress"], state["stage_progress"])
        self.assertEqual(intros, 0)

    def test_g_shortcut_saves_live_progress_before_travelling(self):
        from test_stage1_ending_regressions import Stage1EndingRegressions
        from src.screens import game
        fixture = Stage1EndingRegressions()
        fixture.screen = self.screen
        state = save_manager.new_game_state()
        state.update(completed_stages=["island"], keys=9, stored_topics=["variables"])
        def events(frame, live):
            return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_g)]
        with patch.object(game, "open_stage_select", return_value="castle") as atlas:
            saved, _, _, _ = fixture.run_frames(state, events=events, doorway=False, expect_next=True)
        atlas.assert_called_once()
        self.assertEqual(saved["stage"], "Castle")
        self.assertEqual(saved["stage_checkpoints"]["island"]["keys"], 9)
        self.assertIsNotNone(saved["stage_checkpoints"]["island"]["map_position"])
        self.assertEqual(saved["stored_topics"], ["variables"])
        self.assertEqual(saved["completed_stages"], ["island"])

    def test_g_shortcut_from_pause_can_cancel_without_reloading(self):
        from test_stage1_ending_regressions import Stage1EndingRegressions, gameplay_locals
        from src.screens import game
        fixture = Stage1EndingRegressions()
        fixture.screen = self.screen
        def events(frame, live):
            return [pygame.event.Event(pygame.KEYDOWN, key=key) for key in
                    (pygame.K_ESCAPE, pygame.K_g, pygame.K_ESCAPE)] if frame == 0 else []
        def cancel(*args):
            self.assertTrue(gameplay_locals()["paused"])
            return None
        with patch.object(game, "open_stage_select", side_effect=cancel) as atlas:
            saved, _, _, _ = fixture.run_frames(save_manager.new_game_state(), events=events, doorway=False)
        atlas.assert_called_once()
        self.assertEqual(saved["stage"], "Island")
        self.assertEqual(saved["completed_stages"], [])

    def test_g_current_stage_keeps_live_boss_instance(self):
        from test_stage1_ending_regressions import Stage1EndingRegressions
        from src.screens import game
        fixture = Stage1EndingRegressions()
        fixture.screen = self.screen
        bosses = []
        def events(frame, live):
            return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_g)] if frame == 1 else []
        def check(frame, live):
            bosses.append(live["boss_enemy"])
        with patch.object(game, "open_stage_select", return_value="island") as atlas:
            _, intros, _, _ = fixture.run_frames(save_manager.new_game_state(), developer=True, events=events, check=check)
        atlas.assert_called_once()
        self.assertEqual(intros, 1)
        self.assertIsNotNone(bosses[0])
        self.assertTrue(all(boss is bosses[0] for boss in bosses))
