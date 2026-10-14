"""Regression tests for the beginner-facing code submission workflow."""

import os
import unittest
from unittest.mock import patch

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

    def test_tutor_shortcut_opens_without_changing_code(self):
        original = list(self.editor.text_buffer.lines)
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h, mod=pygame.KMOD_CTRL))
        with patch('src.ui.code_editor.open_mang_tahimik') as tutor:
            self.editor.handle_events()
        tutor.assert_called_once()
        self.assertEqual(self.editor.text_buffer.lines, original)

    def test_tutor_button_click_opens_chat(self):
        from src.screens.mang_tahimik import tutor_helper_rect
        rect = tutor_helper_rect(self.screen, self.editor.renderer.panel_rect)
        self.assertTrue(self.screen.get_rect().contains(rect))
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))
        with patch('src.ui.code_editor.open_mang_tahimik') as tutor:
            self.editor.handle_events()
        tutor.assert_called_once()

    def test_feedback_labels_fit_inside_buttons(self):
        from src.ui.text_layout import fit_text
        from src.ui.editor_theme import BUTTON_FONT, BUTTON_TEXT_COLOR
        self.editor._show_submission_feedback(True, 'Complete', 'Done', 'Correct')
        primary, secondary, _ = self.editor._feedback_layout()
        for rect, label in ((primary, 'CONTINUE'), (secondary, 'REVIEW CODE')):
            rendered = fit_text(BUTTON_FONT, label, BUTTON_TEXT_COLOR, (rect.w - 24, rect.h - 12))
            self.assertTrue(rect.contains(rendered.get_rect(center=rect.center)))

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

    def test_dismissing_feedback_does_not_type_the_acknowledgement(self):
        for key, text in ((pygame.K_e, 'e'), (pygame.K_SPACE, ' ')):
            self.editor._show_submission_feedback(False, 'Try again', 'Keep going', 'Expected:\n\nprint("Hello")')
            original = list(self.editor.text_buffer.lines)
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=text))
            pygame.event.post(pygame.event.Event(pygame.TEXTINPUT, text=text))
            self.editor.handle_events()
            self.assertIsNone(self.editor.submission_feedback)
            self.assertEqual(self.editor.text_buffer.lines, original)
        # Typing on the next event batch works normally.
        pygame.event.post(pygame.event.Event(pygame.TEXTINPUT, text='x'))
        self.editor.handle_events()
        self.assertNotEqual(self.editor.text_buffer.lines, original)

    def test_expected_answer_is_not_truncated_at_blank_lines(self):
        detail = 'Expected:\n\nprint("Hello, World!")'
        self.editor._show_submission_feedback(False, 'Try again', 'Keep going', detail)
        with patch('src.ui.code_editor.draw_text_block') as draw:
            self.editor.draw_submission_feedback()
        self.assertEqual(draw.call_args.args[1], detail)
        self.assertGreater(draw.call_args.args[4].height, 0)

    def test_four_progressive_hints_unlock_on_repeated_failures(self):
        panel = self.editor.renderer.problem_panel
        self.assertEqual(panel.hint_level, 0)
        self.assertEqual(len(panel.hint_steps()), 4)

        for expected_level in (1, 2, 3, 4, 4):
            self.editor.text_buffer.lines = ['print("Wrong")']
            self.editor.submit_code()
            self.assertEqual(panel.hint_level, expected_level)
            self.editor.submission_feedback = None

        # Rows are (text, font, color, height) - each line carries the
        # vertical space it needs so the panel can mix three faces.
        rows = panel._build_rows(300)
        self.assertTrue(
            any(text == "HINT 4 OF 4" for text, _font, _color, _height in rows)
        )
        self.assertTrue(all(height > 0 for _t, _f, _c, height in rows))

    def test_every_hint_row_is_wrapped_to_the_pane_width(self):
        # The locked-hint notice used to be appended unwrapped, so it ran
        # straight off the side of a narrowed objective pane.
        panel = self.editor.renderer.problem_panel

        for _ in range(2):
            width = 150
            for text, font, _color, _height in panel._build_rows(width):
                self.assertLessEqual(font.size(text)[0], width)
            panel.record_failure()

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
