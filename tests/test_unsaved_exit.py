import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
from unittest.mock import Mock, patch
import pygame
from src.systems.exit_guard import EventExitGuard, has_unsaved_progress
from src.screens.unsaved_exit import confirm_unsaved_exit


class UnsavedExitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((960, 640))

    def key(self, key):
        return pygame.event.Event(pygame.KEYDOWN, key=key)

    def test_dirty_state_compares_progress_not_password_metadata(self):
        self.assertFalse(has_unsaved_progress({'keys': 1, '_security': 'a'}, {'keys': 1, '_security': 'b'}))
        self.assertTrue(has_unsaved_progress({'keys': 2}, {'keys': 1}))
        self.assertTrue(has_unsaved_progress({'keys': 0}, None))

    @patch('pygame.display.flip')
    def test_enter_defaults_to_keep_playing(self, flip):
        save = Mock()
        with patch('pygame.event.get', return_value=[self.key(pygame.K_RETURN)]):
            self.assertFalse(confirm_unsaved_exit(self.screen, save))
        save.assert_not_called()

    @patch('pygame.display.flip')
    def test_save_and_leave_writes_before_leaving(self, flip):
        save = Mock()
        with patch('pygame.event.get', return_value=[self.key(pygame.K_TAB), self.key(pygame.K_RETURN)]):
            self.assertTrue(confirm_unsaved_exit(self.screen, save))
        save.assert_called_once()

    @patch('pygame.display.flip')
    def test_discard_requires_explicit_choice_and_does_not_save(self, flip):
        save = Mock()
        with patch('pygame.event.get', return_value=[self.key(pygame.K_LEFT), self.key(pygame.K_RETURN)]):
            self.assertTrue(confirm_unsaved_exit(self.screen, save))
        save.assert_not_called()

    @patch('pygame.display.flip')
    def test_save_failure_keeps_game_open(self, flip):
        save = Mock(side_effect=OSError('disk full'))
        with patch('pygame.event.get', side_effect=[
            [self.key(pygame.K_TAB), self.key(pygame.K_RETURN)], [self.key(pygame.K_ESCAPE)]
        ]):
            self.assertFalse(confirm_unsaved_exit(self.screen, save))
        save.assert_called_once()

    @patch('pygame.display.flip')
    def test_second_window_close_cancels_warning(self, flip):
        with patch('pygame.event.get', return_value=[pygame.event.Event(pygame.QUIT)]):
            self.assertFalse(confirm_unsaved_exit(self.screen))

    def test_guard_intercepts_close_from_nested_overlay(self):
        confirm = Mock(return_value=False)
        guard = EventExitGuard(lambda: [pygame.event.Event(pygame.QUIT)], confirm,
                               self.test_guard_intercepts_close_from_nested_overlay.__code__)
        def overlay():
            return guard()
        self.assertEqual(overlay(), [])
        confirm.assert_called_once_with('exit the game')

    def test_guard_passes_close_only_after_approval(self):
        guard = EventExitGuard(lambda: [pygame.event.Event(pygame.QUIT)], lambda _: True,
                               self.test_guard_passes_close_only_after_approval.__code__)
        self.assertEqual(guard()[0].type, pygame.QUIT)
