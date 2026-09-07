"""Developer gate bypass and visible low-health feedback."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
import inspect
import tempfile
import xml.etree.ElementTree as ET
from unittest.mock import patch
import pygame
from src.data.stages import get_stage
from src.data.stages import stage_world
from src.screens import game
from src.systems import save_manager
from src.systems.developer_mode import developer_mode
from src.screens.stage_gate import open_stage_gate
from src.systems.stage_gate import evaluate_stage_gate
from src.systems.stage_handoff import advance_save_state
from src.systems.save_manager import new_game_state
from src.systems.developer_mode import DeveloperMode
from src.ui.gameplay_hud import draw_low_health_warning


class DeveloperExplorationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def test_f4_state_can_be_toggled_back_off(self):
        mode = DeveloperMode()
        self.assertFalse(mode.enabled)
        self.assertTrue(mode.toggle())
        self.assertFalse(mode.toggle())

    def test_zero_progress_can_exit_only_with_developer_access(self):
        stage = get_stage("island")
        status = evaluate_stage_gate(stage, 0, [])
        self.assertFalse(status.unlocked)
        for enabled, expected in ((True, "exit"), (False, "stay")):
            event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
            with patch("pygame.event.get", side_effect=[[], [event]]):
                self.assertEqual(open_stage_gate(
                    self.screen, status, next_stage_name="Castle", developer_access=enabled
                ), expected)
        self.assertEqual(status.keys, 0)
        self.assertEqual(status.completed_topics, 0)
        self.assertFalse(status.boss_defeated)

    def test_developer_handoff_does_not_fabricate_campaign_completion(self):
        state = new_game_state()
        advanced = advance_save_state(state, get_stage("island"), get_stage("castle"), mark_complete=False)
        self.assertEqual(advanced["stage"], "Castle")
        self.assertEqual(advanced["challenges_passed"], [])
        self.assertEqual(advanced["completed_stages"], [])
        self.assertEqual(advanced["keys"], 0)
        self.assertNotIn("developer_mode", advanced)

    def test_actual_f4_then_gate_enters_castle_with_no_keys_or_topics(self):
        stage = get_stage("island")
        world = stage_world(stage)
        root = ET.parse(world["map"]).getroot()
        width = int(root.get("width")) * int(root.get("tilewidth"))
        height = int(root.get("height")) * int(root.get("tileheight"))
        x, y, w, h = stage["completion"]["exit_rect"]
        state = new_game_state()
        state["map_layout_version"] = world["map_layout_version"]
        state["map_position"] = [round((x + w / 2) * width), round((y + h / 2) * height)]
        sent = False
        def events():
            nonlocal sent
            callers = [frame.function for frame in inspect.stack()]
            if "_pump_events" in callers:
                return []
            if "open_stage_gate" in callers:
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]
            if "game_screen" in callers and not sent:
                sent = True
                return [pygame.event.Event(pygame.KEYDOWN, key=key) for key in (pygame.K_F4, pygame.K_e)]
            raise AssertionError("The F4 gate transition did not finish on the first gameplay frame")
        with tempfile.TemporaryDirectory() as folder, patch.object(save_manager, "SAVE_DIR", folder), patch.object(
            developer_mode, "enabled", False
        ), patch.object(game, "DEBUG_MODE", True), patch(
            "pygame.event.get", side_effect=events
        ), patch.object(game.StageLoadingScreen, "finish", lambda self: None):
            result = game.game_screen(self.screen, slot_num=1, save_state=state)
            self.assertEqual(result, "next_stage")
            self.assertTrue(developer_mode.enabled)
            saved = save_manager.load_slot(1)
            self.assertEqual(saved["stage"], "Castle")
            self.assertEqual(saved["keys"], 0)
            self.assertEqual(saved["challenges_passed"], [])
            self.assertEqual(saved["completed_stages"], [])

    def test_low_health_glow_is_visible_on_edges_with_clear_center(self):
        surface = pygame.Surface((1280, 720))
        surface.fill((20, 20, 20))
        self.assertTrue(draw_low_health_warning(surface, 26, 100, 0))
        edge = surface.get_at((640, 2))
        self.assertGreater(edge.r - edge.g, 70)
        self.assertEqual(surface.get_at((640, 360))[:3], (20, 20, 20))

    def test_healthy_or_dead_player_has_no_warning(self):
        for hp in (31, 100, 0):
            surface = pygame.Surface((1280, 720))
            surface.fill((20, 20, 20))
            self.assertFalse(draw_low_health_warning(surface, hp, 100))
            self.assertEqual(surface.get_at((640, 2))[:3], (20, 20, 20))
