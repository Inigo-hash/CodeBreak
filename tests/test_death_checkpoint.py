"""Ordinary campaign deaths must survive leaving the game-over screen."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import pygame
from src.screens import game
from src.systems import save_manager


class DeathCheckpointTests(unittest.TestCase):
    def test_game_over_checkpoints_penalty_and_safe_position_before_menu(self):
        pygame.init()
        screen = pygame.display.set_mode((1280, 720))
        for hearts, expected in ((5, 4), (1, 5)):
            with self.subTest(hearts=hearts), tempfile.TemporaryDirectory() as folder:
                state = save_manager.new_game_state()
                state.update(hearts=hearts, bonus_time=42)
                live_state = {}

                def present():
                    frame = sys._getframe(1)
                    if frame.f_code.co_name != "game_screen":
                        return
                    live_state.update(frame.f_locals)
                    combat = frame.f_locals["player_combat"]
                    combat.hp = 0
                    combat.state = "defeated"
                    combat.action_time = 0

                def game_over(*args, **kwargs):
                    self.assertIsNone(kwargs.get('failed_snippet'))
                    saved = save_manager.load_slot(1)
                    self.assertEqual(saved["hearts"], expected)
                    self.assertEqual(saved["map_position"], list(live_state["stage_spawn"]))
                    self.assertEqual(saved["bonus_time"], 42)
                    self.assertEqual(saved["challenges_passed"], [])
                    return "main_menu"

                with patch.object(save_manager, "SAVE_DIR", folder), \
                     patch.object(game.StageLoadingScreen, "finish", lambda self: None), \
                     patch.object(game, "game_over_screen", game_over), \
                     patch.object(pygame.display, "flip", present), \
                     patch.object(pygame.event, "get", return_value=[]):
                    save_manager.save_slot(1, state)
                    self.assertEqual(game.game_screen(screen, slot_num=1, save_state=state), "main_menu")

    def test_lethal_coding_trap_passes_failed_code_to_game_over(self):
        from src.data.challenges import CHALLENGES
        from src.entities.trap import Trap

        pygame.init()
        screen = pygame.display.set_mode((1280, 720))
        trap = Trap('test_coding_death', (0, 0, 100000, 100000), damage=100)
        editor = SimpleNamespace(
            solved=False, run=lambda: None,
            text_buffer=SimpleNamespace(lines=['print("unfinished")']),
        )

        def finish_death_animation():
            frame = sys._getframe(1)
            if frame.f_code.co_name == 'game_screen':
                combat = frame.f_locals['player_combat']
                if combat.hp == 0:
                    combat.action_time = 0

        with patch.object(game, 'load_traps', return_value=[trap]), \
             patch.object(game, 'build_trap_challenge', return_value=CHALLENGES['print_001']), \
             patch.object(game, 'open_trap_alert'), \
             patch.object(game, 'CodeEditor', return_value=editor), \
             patch.object(game, 'game_over_screen', return_value='main_menu') as modal, \
             patch.object(game.StageLoadingScreen, 'finish', lambda self: None), \
             patch.object(pygame.display, 'flip', finish_death_animation), \
             patch.object(pygame.event, 'get', return_value=[]):
            self.assertEqual(game.game_screen(screen, save_state=save_manager.new_game_state()), 'main_menu')
        self.assertEqual(modal.call_args.kwargs['failed_snippet'], 'print("unfinished")')
