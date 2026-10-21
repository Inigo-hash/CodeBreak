"""The redesigned defeat modal keeps every exit reachable."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import unittest
from unittest.mock import patch

import pygame
from src.screens.game_over import game_over_screen, _game_over_layout


class GameOverDesignTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720))

    def choose(self, events):
        with patch('pygame.event.get', return_value=events), \
             patch('pygame.time.get_ticks', side_effect=[0] + [1000] * 20):
            return game_over_screen(self.screen)

    def test_keyboard_navigation_selects_the_focused_action(self):
        for key, expected in ((pygame.K_DOWN, 'review'), (pygame.K_UP, 'main_menu')):
            with self.subTest(expected=expected):
                self.assertEqual(self.choose([
                    pygame.event.Event(pygame.KEYDOWN, key=key),
                    pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN),
                ]), expected)

    def test_existing_keyboard_shortcuts_remain_available(self):
        for key, expected in ((pygame.K_RETURN, 'retry'), (pygame.K_ESCAPE, 'retry'),
                              (pygame.K_r, 'review'), (pygame.K_m, 'main_menu')):
            with self.subTest(expected=expected, key=key):
                self.assertEqual(self.choose([
                    pygame.event.Event(pygame.KEYDOWN, key=key)
                ]), expected)

    def test_each_button_is_clickable(self):
        for rect, expected in zip(_game_over_layout(self.screen.get_size())['buttons'],
                                  ('retry', 'review', 'main_menu')):
            with self.subTest(expected=expected):
                self.assertEqual(self.choose([
                    pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)
                ]), expected)

    def test_input_that_opened_modal_cannot_click_through(self):
        with patch('pygame.event.get', side_effect=[
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)],
        ]), patch('pygame.time.get_ticks', side_effect=[0, 100, 300]):
            self.assertEqual(game_over_screen(self.screen), 'retry')
