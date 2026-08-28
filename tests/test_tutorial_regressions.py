"""Regression tests for tutorial input, escape flow, and menu SFX."""

import os
import tempfile
import threading
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame


class TutorialRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def setUp(self):
        # Importing main_menu creates the production display at module scope.
        # Restore a predictable test surface before every case so one modal's
        # display setup cannot leak into the next stress scenario.
        self.screen = pygame.display.set_mode((1280, 720))
        pygame.event.clear()

    def test_editor_accepts_text_after_another_modal_stops_text_input(self):
        from src.data.challenges import CHALLENGES
        from src.ui.code_editor import CodeEditor

        # Reproduce the password-modal handoff that originally disabled all
        # printable input in the tutorial editor.
        pygame.key.stop_text_input()
        editor = CodeEditor(
            self.screen, CHALLENGES["print_001"], self.screen.copy()
        )
        pygame.event.post(pygame.event.Event(pygame.TEXTINPUT, text='print("Hello, World!")'))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        editor.run()

        self.assertEqual(editor.text_buffer.lines, ['print("Hello, World!")'])

    def test_escape_spam_cannot_complete_or_skip_the_tutorial(self):
        from src.screens.tutorial import tutorial_screen

        # An odd number leaves the confirmation open. Only the explicit
        # Return to Menu click may exit, and its result must not mean success.
        for _ in range(101):
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        width, height = self.screen.get_size()
        exit_rect = pygame.Rect(0, 0, min(620, width - 60), 280)
        exit_rect.center = (width // 2, height // 2)
        return_menu = pygame.Rect(exit_rect.right - 268,
                                  exit_rect.bottom - 76, 220, 46)
        # Post the explicit click after the first event batch. This exercises
        # repeated Escape across the actual modal frame boundary rather than
        # relying on every synthetic event being consumed in one pump.
        timer = threading.Timer(
            0.15,
            lambda: pygame.event.post(pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, button=1, pos=return_menu.center
            )),
        )
        timer.start()
        try:
            self.assertEqual(tutorial_screen(self.screen, play_music=False), "cancelled")
        finally:
            timer.cancel()

    def test_z_cancelled_tutorial_neither_saves_nor_launches_gameplay(self):
        import src.screens.start_game_menu as start_menu
        from src.screens.main_menu import compute_menu_layout
        from src.systems import save_manager

        original_dir = save_manager.SAVE_DIR
        original_tutorial = start_menu.tutorial_screen
        original_game = start_menu.game_screen
        game_calls = []

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                save_manager.SAVE_DIR = temp_dir
                start_menu.tutorial_screen = (
                    lambda _screen, **_kwargs: "cancelled"
                )
                start_menu.game_screen = lambda *_args, **_kwargs: game_calls.append(True)

                width, height = self.screen.get_size()
                menu_rects, *_ = compute_menu_layout(width, height, 3)
                panel = pygame.Rect(0, 0, min(650, width - 60),
                                    min(520, height - 70))
                panel.center = (width // 2, height // 2)
                slot_one = pygame.Rect(panel.left + 40, panel.top + 92,
                                       panel.width - 80, 84)

                pygame.event.post(pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN, button=1, pos=menu_rects[0].center
                ))
                pygame.event.post(pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN, button=1, pos=slot_one.center
                ))
                for text in ("pass", "pass"):
                    for char in text:
                        pygame.event.post(pygame.event.Event(
                            pygame.KEYDOWN, key=ord(char), unicode=char
                        ))
                    pygame.event.post(pygame.event.Event(
                        pygame.KEYDOWN, key=pygame.K_RETURN, unicode=""
                    ))
                # Close slot selection, then return from the start menu.
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))

                start_menu.start_game_menu(self.screen, self.screen.copy())

                self.assertFalse(save_manager.slot_exists(1))
                self.assertEqual(game_calls, [])
            finally:
                save_manager.SAVE_DIR = original_dir
                start_menu.tutorial_screen = original_tutorial
                start_menu.game_screen = original_game

    def test_crumble_has_separate_break_and_rubble_settle_layers(self):
        from src.systems.audio import _build_crumble_sound

        breaking = _build_crumble_sound("break")
        settling = _build_crumble_sound("settle")
        self.assertIsNotNone(breaking)
        self.assertIsNotNone(settling)
        self.assertGreater(breaking.get_length(), 0.65)
        self.assertGreater(settling.get_length(), 0.40)
        self.assertGreater(breaking.get_length(), settling.get_length())


if __name__ == "__main__":
    unittest.main()
