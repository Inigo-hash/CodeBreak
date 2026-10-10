import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
from unittest.mock import patch
import pygame
from src.screens.mang_tahimik import MangTahimikChat, wrap_lines
from src.systems.ai_tutor import TutorSession


class ChatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((960, 640))

    def test_wrapping_preserves_indentation_and_long_tokens_fit(self):
        font = pygame.font.Font(None, 20)
        lines = wrap_lines('    print(x)\n' + 'x' * 200, font, 120)
        self.assertTrue(lines[0].startswith('    '))
        self.assertTrue(all(font.size(line)[0] <= 120 for line in lines))

    def test_draw_clamps_scroll_and_escape_closes_pending_request(self):
        chat = MangTahimikChat(self.screen)
        chat.session.pending = True
        chat.scroll = 100000
        chat.draw()
        self.assertEqual(chat.scroll, 0)
        with patch('pygame.event.get', return_value=[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]):
            chat.run()
        self.assertTrue(chat.session.pending)

    def test_input_submission_and_failed_send_keep_text(self):
        chat = MangTahimikChat(self.screen, session=TutorSession(lambda *args: 'hint'))
        chat.question = 'what is a list?'
        chat.submit()
        self.assertEqual(chat.messages[-1], ('You', 'what is a list?'))
        self.assertEqual(chat.question, '')
        chat.question = 'second question'
        chat.submit()
        self.assertEqual(chat.question, 'second question')

    def test_small_window_draw(self):
        chat = MangTahimikChat(pygame.Surface((640, 480)))
        chat.messages.append(('Mang Tahimik', 'word ' * 500))
        chat.question = 'x' * 1000
        chat.draw()
