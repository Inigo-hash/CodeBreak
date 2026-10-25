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

    def test_conversation_wraps_at_word_boundaries(self):
        font = pygame.font.Font(None, 20)
        text = 'Python makes learning enjoyable for everyone.'
        lines = wrap_lines(text, font, font.size('Python makes lea')[0])
        self.assertEqual(''.join(lines), text)
        self.assertEqual(' '.join(lines).split(), text.split())
        self.assertTrue(all(font.size(line)[0] <= font.size('Python makes lea')[0] for line in lines))

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

    def test_reopening_chat_keeps_history_and_the_pending_reply(self):
        import threading
        entered, release = threading.Event(), threading.Event()
        def ask(*args):
            entered.set()
            release.wait(2)
            return 'A live follow-up.'
        session = TutorSession(ask)
        session.history = [{'role': 'user', 'content': 'previous question'},
                           {'role': 'assistant', 'content': 'previous answer'}]
        try:
            first = MangTahimikChat(self.screen, session=session)
            first.question = 'give another example'
            first.submit()
            self.assertTrue(entered.wait(1))
            reopened = MangTahimikChat(self.screen, session=session)
            self.assertIn(('You', 'previous question'), reopened.messages)
            self.assertIn(('Mang Tahimik', 'previous answer'), reopened.messages)
            self.assertEqual(reopened.messages[-1], ('You', 'give another example'))
            self.assertTrue(reopened.session.pending)
            reopened.draw()
        finally:
            release.set()
            session._worker.join(2)
        self.assertEqual(reopened.session.poll(), 'A live follow-up.')

    def test_selection_replace_undo_redo_and_navigation(self):
        chat = MangTahimikChat(self.screen)
        def key(code, mod=0):
            chat.handle_key(pygame.event.Event(pygame.KEYDOWN, key=code, mod=mod))
        chat.replace_selection('hello world')
        key(pygame.K_a, pygame.KMOD_CTRL)
        self.assertEqual((chat.anchor, chat.cursor), (0, 11))
        chat.replace_selection('Python')
        self.assertEqual(chat.question, 'Python')
        key(pygame.K_z, pygame.KMOD_CTRL)
        self.assertEqual(chat.question, 'hello world')
        key(pygame.K_y, pygame.KMOD_CTRL)
        self.assertEqual(chat.question, 'Python')
        key(pygame.K_HOME)
        key(pygame.K_RIGHT, pygame.KMOD_SHIFT)
        key(pygame.K_DELETE)
        self.assertEqual(chat.question, 'ython')

    def test_clipboard_copy_cut_and_paste_limit(self):
        chat = MangTahimikChat(self.screen)
        chat.replace_selection('hello')
        chat.handle_key(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, mod=pygame.KMOD_CTRL))
        with patch('pygame.scrap.get_init', return_value=True), patch('pygame.scrap.put') as put:
            chat.handle_key(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c, mod=pygame.KMOD_CTRL))
            put.assert_called_with(pygame.SCRAP_TEXT, b'hello\x00')
            self.assertEqual(chat.question, 'hello')
            chat.handle_key(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x, mod=pygame.KMOD_CTRL))
            self.assertEqual(chat.question, '')
        with patch('pygame.scrap.get_init', return_value=True), patch('pygame.scrap.get', return_value=b'x' * 1500 + b'\x00'):
            chat.handle_key(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_v, mod=pygame.KMOD_CTRL))
        self.assertEqual(len(chat.question), 1000)
        chat.draw()

    def test_scrollbar_drag_reaches_both_ends(self):
        chat = MangTahimikChat(self.screen)
        chat.messages.append(('Mang Tahimik', 'word ' * 500))
        chat.draw()
        self.assertGreater(chat.max_scroll, 0)
        self.assertEqual(chat.scroll_thumb.bottom, chat.scroll_track.bottom)
        chat.drag_scroll = 0
        chat.drag_scroll_to(chat.scroll_track.top)
        self.assertEqual(chat.scroll, chat.max_scroll)
        chat.draw()
        self.assertEqual(chat.scroll_thumb.top, chat.scroll_track.top)
        chat.drag_scroll_to(chat.scroll_track.bottom)
        self.assertEqual(chat.scroll, 0)
