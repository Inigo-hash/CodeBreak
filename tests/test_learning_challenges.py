"""End-to-end checks for every coding challenge shipped with the game."""

import unittest

from src.data.challenges import CHALLENGES
from src.learning.challenge_manager import ChallengeManager
from src.learning.sandbox import run_user_code


VALID_SOLUTIONS = {
    "variables_001": "age = 18",
    "print_001": 'print("Hello, World!")',
    "python_syntax_basics_001": 'print("Hello, Explorer!")',
    "data_types_001": (
        'age = 18\nheight = 1.75\nname = "Alex"\nis_ready = True'
    ),
    "type_casting_001": 'age_text = "18"\nage = int(age_text)',
    "input_lesson_001": 'name = input("Enter your name: ")',
    "formatted_output_001": (
        'name = "Alex"\nprint(f"Welcome, {name}!")'
    ),
    "operators_lesson_001": (
        "score = 5\nscore += 3\npassed = score >= 8"
    ),
    "strings_lesson_001": (
        'game_name = "CodeBreak"\n'
        'message = "Welcome to\\n" + game_name\n'
        "result = message.upper()"
    ),
    "control_flow_lesson_001": (
        'score = 85\n'
        'has_key = True\n'
        'if score >= 90:\n    rank = "Gold"\n'
        'elif score >= 75:\n    rank = "Silver"\n'
        'else:\n    rank = "Bronze"\n'
        'can_enter = has_key and score >= 75'
    ),
    "boolean_logic_001": (
        "has_key = True\ngate_locked = False\n"
        "can_enter = has_key and not gate_locked"
    ),
}


class LearningChallengeTests(unittest.TestCase):
    def test_every_challenge_has_a_runnable_valid_solution(self):
        self.assertEqual(set(CHALLENGES), set(VALID_SOLUTIONS))
        manager = ChallengeManager()

        for challenge_id, challenge in CHALLENGES.items():
            with self.subTest(challenge=challenge_id):
                code = VALID_SOLUTIONS[challenge_id]
                execution = run_user_code(
                    code, input_values=challenge.get("test_inputs", [])
                )
                self.assertTrue(execution["success"], execution.get("error"))

                passed, feedback = manager.validate(challenge, code)
                self.assertTrue(passed, feedback)
                self.assertTrue(feedback.strip())

    def test_invalid_answers_return_actionable_feedback(self):
        manager = ChallengeManager()
        invalid_solutions = {
            "variables_001": "age = 17",
            "print_001": 'print("Goodbye")',
            "python_syntax_basics_001": 'print("Wrong")',
            "data_types_001": 'age = "18"',
            "type_casting_001": 'age_text = "18"\nage = age_text',
            "input_lesson_001": 'name = "Alex"',
            "formatted_output_001": (
                'name = "Alex"\nprint("Welcome, Alex!")'
            ),
            "operators_lesson_001": (
                "score = 5\nscore += 2\npassed = score >= 8"
            ),
            "strings_lesson_001": (
                'game_name = "CodeBreak"\n'
                'message = "Welcome to " + game_name\n'
                "result = message.lower()"
            ),
            "control_flow_lesson_001": (
                'score = 85\nhas_key = True\n'
                'if score >= 75:\n    rank = "Silver"'
            ),
            "boolean_logic_001": (
                "has_key = True\ngate_locked = False\n"
                "can_enter = has_key or gate_locked"
            ),
        }

        for challenge_id, code in invalid_solutions.items():
            with self.subTest(challenge=challenge_id):
                passed, feedback = manager.validate(
                    CHALLENGES[challenge_id], code
                )
                self.assertFalse(passed)
                self.assertGreater(len(feedback.strip()), 5)


if __name__ == "__main__":
    unittest.main()
