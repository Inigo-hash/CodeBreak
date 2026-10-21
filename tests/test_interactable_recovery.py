"""Exercise lesson recovery and one-shot searches through the gameplay loop."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

from collections import defaultdict
from copy import deepcopy
import inspect
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame

from src.data.stages import get_stage
from src.screens import game
from src.systems import save_manager
from src.systems.topic_mastery import complete_topic_challenge


class EndFrames(Exception):
    pass


def live_game():
    frame = inspect.currentframe()
    while frame:
        if frame.f_code is game.game_screen.__code__ and 'dt' in frame.f_locals:
            return frame.f_locals
        frame = frame.f_back
    return None


class InteractableRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def make_item(self, action='search_barrel', topic_id='python_syntax_basics', **props):
        properties = {'actions': action, 'persistent_id': 'recovery_prop', **props}
        if topic_id:
            properties['topic_id'] = topic_id
        obj = SimpleNamespace(id=1, x=0, y=0, width=24, height=24,
                              properties=properties)
        return game.load_interactables(SimpleNamespace(visible_layers=[[obj]]))[0]

    def run_search(self, state, item, *, decision='close', editor_solved=False, frames=2):
        rendered = 0
        saved = None

        def events():
            live = live_game()
            if live:
                item['rect'] = live['player_rect'].copy()
                item['inspect_progress'] = 1.0
            return []

        def present():
            nonlocal rendered, saved
            live = live_game()
            if live and 'previous_player_position' in live:
                rendered += 1
                if rendered >= frames:
                    saved = deepcopy(live['build_save_state']())
                    raise EndFrames

        class Editor:
            solved = editor_solved
            def __init__(self, *args, **kwargs):
                pass
            def run(self):
                pass

        with tempfile.TemporaryDirectory() as folder, \
                patch.object(save_manager, 'SAVE_DIR', folder), \
                patch.object(game, 'load_interactables', return_value=[item]), \
                patch.object(game.StageLoadingScreen, 'finish'), \
                patch.object(pygame.event, 'get', side_effect=events), \
                patch.object(pygame.display, 'flip', side_effect=present), \
                patch.object(pygame.key, 'get_pressed', return_value=defaultdict(bool, {pygame.K_e: True})), \
                patch.object(game, 'open_topic_found', return_value=decision) as found, \
                patch.object(game, 'open_topic_lesson', return_value='challenge'), \
                patch.object(game, 'CodeEditor', Editor):
            with self.assertRaises(EndFrames):
                game.game_screen(self.screen, slot_num=1, save_state=deepcopy(state))
            return saved, found.call_count

    def test_cancelled_discovery_can_be_reopened_in_game_and_after_reload(self):
        state, visits = self.run_search(save_manager.new_game_state(), self.make_item())
        self.assertEqual(visits, 2)
        self.assertIn('python_syntax_basics', state['topics_discovered'])
        self.assertFalse(state['topics_completed'])
        _, visits = self.run_search(state, self.make_item(), frames=1)
        self.assertEqual(visits, 1)

    def test_unsolved_editor_does_not_consume_a_required_lesson(self):
        state, visits = self.run_search(save_manager.new_game_state(), self.make_item(), decision='start')
        self.assertEqual(visits, 2)
        self.assertFalse(state['challenges_passed'])
        self.assertEqual(state['keys'], 0)
        _, visits = self.run_search(state, self.make_item(), decision='start', frames=1)
        self.assertEqual(visits, 1)

    def test_solving_a_lesson_awards_its_key_immediately_and_once(self):
        state, visits = self.run_search(
            save_manager.new_game_state(), self.make_item(), decision='start', editor_solved=True,
        )
        self.assertEqual(visits, 1)
        self.assertEqual(state['keys'], 1)
        self.assertEqual(state['challenges_passed'], ['python_syntax_basics_001'])
        replay = complete_topic_challenge(state, get_stage('island'),
                                          'python_syntax_basics', 'python_syntax_basics_001')
        self.assertEqual(replay['keys'], 1)

    def test_independent_crate_rewards_once_across_reload(self):
        def crate():
            return self.make_item('search_crate', None, independent_search=True, reward_seconds=15)
        state, _ = self.run_search(save_manager.new_game_state(), crate())
        self.assertEqual(state['bonus_time'], 15)
        self.assertIn('recovery_prop', state['stage_progress']['opened_interactables'])
        state, _ = self.run_search(state, crate())
        self.assertEqual(state['bonus_time'], 15)

    def test_empty_untagged_chest_has_no_reward_or_placeholder_lesson(self):
        item = self.make_item('search_chest', None)
        state, visits = self.run_search(save_manager.new_game_state(), item)
        self.assertEqual(state['bonus_time'], 0)
        self.assertEqual(visits, 0)
        self.assertEqual(item['interaction_message'], 'The chest is empty.')


if __name__ == '__main__':
    unittest.main()
