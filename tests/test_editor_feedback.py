"""Regression tests for the beginner-facing code submission workflow."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.data.challenges import CHALLENGES
from src.ui.code_editor import CodeEditor


class EditorFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def setUp(self):
        self.screen = pygame.display.set_mode((1280, 720))
        pygame.event.clear()
        self.editor = CodeEditor(
            self.screen,
            CHALLENGES["print_001"],
            self.screen.copy(),
        )
        self.editor.running = True

    def test_correct_submission_shows_completion_message_and_continues(self):
        self.editor.text_buffer.lines = ['print("Hello, World!")']

        self.editor.submit_code()

        self.assertTrue(self.editor.solved)
        self.assertEqual(self.editor.submission_attempts, 1)
        self.assertTrue(self.editor.submission_feedback["passed"])
        self.assertEqual(
            self.editor.submission_feedback["title"],
            "CHALLENGE COMPLETE!",
        )
        self.assertTrue(any(
            "Challenge complete" in message
            for message, _color in self.editor.output_panel.messages
        ))

        # The result must also render outside the small output pane.
        self.editor.renderer.draw()
        self.editor.draw_submission_feedback()

        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_e, unicode="e"
        ))
        self.editor.handle_events()

        self.assertFalse(self.editor.running)
        self.assertIsNone(self.editor.submission_feedback)

    def test_wrong_submission_blocks_click_spam_until_acknowledged(self):
        self.editor.text_buffer.lines = ['print("Wrong")']
        self.editor.submit_code()

        self.assertFalse(self.editor.solved)
        self.assertEqual(self.editor.submission_attempts, 1)
        self.assertEqual(
            self.editor.submission_feedback["title"],
            "NOT COMPLETE YET",
        )

        # Click where Submit sits many times. The modal owns focus, so none
        # of these events may trigger another validation attempt underneath.
        submit_position = self.editor.submit_button.rect.center
        original_lines = list(self.editor.text_buffer.lines)
        for _ in range(100):
            pygame.event.post(pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=1,
                pos=submit_position,
            ))
        pygame.event.post(pygame.event.Event(
            pygame.TEXTINPUT, text="should_not_reach_editor"
        ))
        self.editor.handle_events()

        self.assertEqual(self.editor.submission_attempts, 1)
        self.assertEqual(self.editor.text_buffer.lines, original_lines)
        self.assertIsNotNone(self.editor.submission_feedback)

        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_RETURN, unicode=""
        ))
        self.editor.handle_events()
        self.assertTrue(self.editor.running)
        self.assertIsNone(self.editor.submission_feedback)

    def test_broken_code_explains_that_submission_did_not_complete(self):
        self.editor.text_buffer.lines = ["print("]

        self.editor.submit_code()

        self.assertFalse(self.editor.solved)
        self.assertEqual(
            self.editor.submission_feedback["title"],
            "CODE COULD NOT RUN",
        )
        self.assertIn(
            "not submitted",
            self.editor.submission_feedback["message"],
        )
        self.assertIn("Syntax error", self.editor.submission_feedback["detail"])

    def test_four_progressive_hints_unlock_on_repeated_failures(self):
        panel = self.editor.renderer.problem_panel
        self.assertEqual(panel.hint_level, 0)
        self.assertEqual(len(panel.hint_steps()), 4)

        for expected_level in (1, 2, 3, 4, 4):
            self.editor.text_buffer.lines = ['print("Wrong")']
            self.editor.submit_code()
            self.assertEqual(panel.hint_level, expected_level)
            self.editor.submission_feedback = None

        rows = panel._build_rows(300)
        self.assertTrue(any(text == "HINT 4 OF 4" for text, _font, _color in rows))

    def test_feedback_layout_renders_at_supported_window_sizes(self):
        for size in ((800, 600), (1280, 720), (1920, 1080)):
            self.screen = pygame.display.set_mode(size)
            editor = CodeEditor(
                self.screen,
                CHALLENGES["print_001"],
                self.screen.copy(),
            )
            editor.text_buffer.lines = ['print("Hello, World!")']
            editor.submit_code()
            editor.renderer.draw()
            editor.draw_submission_feedback()

            _primary, _secondary, panel = editor._feedback_layout()
            self.assertTrue(self.screen.get_rect().contains(panel))


if __name__ == "__main__":
    unittest.main()
