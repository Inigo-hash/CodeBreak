"""Exercise keyboard-only learning and tutor recovery with real Pygame events."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
from unittest.mock import patch
import pygame
from src.data.topics import TOPICS, topic_challenge_ids
from src.screens.topic_challenges import open_topic_challenges
from src.screens.topic_lesson import TopicLessonScreen
from src.screens.mang_tahimik import MangTahimikChat
from src.screens.settings import SettingsPanel
from src.settings_state import ROWS, settings_state
from src.ui.theme import clear_font_cache


def key(code, mod=0):
    return pygame.event.Event(pygame.KEYDOWN, key=code, mod=mod)


class NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((960, 640))

    def test_challenge_picker_resumes_unfinished_and_cycles(self):
        topic = TOPICS['castle_lists']
        ids = topic_challenge_ids(topic)
        with patch('pygame.event.get', return_value=[key(pygame.K_RETURN)]):
            self.assertEqual(open_topic_challenges(self.screen, topic, {ids[0]}), ids[1])
        with patch('pygame.event.get', return_value=[key(pygame.K_TAB, pygame.KMOD_SHIFT), key(pygame.K_RETURN)]):
            self.assertEqual(open_topic_challenges(self.screen, topic, {ids[0]}), ids[0])

    def test_lesson_scroll_and_confirmation_without_mouse(self):
        lesson = TopicLessonScreen(self.screen, TOPICS['castle_lists'])
        with patch('pygame.event.get', return_value=[key(pygame.K_END), key(pygame.K_RETURN), key(pygame.K_RETURN)]):
            self.assertEqual(lesson.run(), 'challenge')
        self.assertEqual(lesson.scroll_offset, lesson.max_scroll())

    def test_escape_cancels_confirmation_before_leaving_lesson(self):
        lesson = TopicLessonScreen(self.screen, TOPICS['castle_lists'])
        with patch('pygame.event.get', return_value=[key(pygame.K_RETURN), key(pygame.K_ESCAPE), key(pygame.K_ESCAPE)]):
            self.assertEqual(lesson.run(), 'close')
        self.assertFalse(lesson.show_confirmation)

    def test_settings_tab_and_shift_tab_show_focus(self):
        panel = SettingsPanel(self.screen)
        panel._handle_key(key(pygame.K_TAB))
        self.assertEqual(panel.focus, 1)
        self.assertTrue(panel.keyboard_focus)
        panel._handle_key(key(pygame.K_TAB, pygame.KMOD_SHIFT))
        self.assertEqual(panel.focus, 0)

    def test_tutor_controls_fit_small_window_with_large_text(self):
        for size in ((640, 480), (960, 640), (1280, 720)):
            with patch.dict(settings_state, font_size=28):
                clear_font_cache()
                chat = MangTahimikChat(pygame.Surface(size))
                chat.session.pending = True
                chat.messages.append(('Mang Tahimik', 'Python reference. ' * 80))
                chat.draw()
                for rect in (chat.guide_rect, chat.back_rect, chat.send_rect, chat.scroll_track):
                    self.assertTrue(chat.screen.get_rect().contains(rect))
                self.assertFalse(chat.guide_rect.colliderect(chat.back_rect))
                chat.handle_key(key(pygame.K_PAGEUP))
                self.assertGreater(chat.scroll, 0)
        clear_font_cache()

    def test_empty_submit_explains_how_to_recover(self):
        chat = MangTahimikChat(self.screen)
        chat.submit()
        self.assertEqual(chat.feedback, 'Type a question first.')
