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
        "score = 5\n"
        "score += 3\n"
        "passed = score >= 8"
    ),

    "strings_lesson_001": (
        'game_name = "CodeBreak"\n'
        'message = "Welcome to\\n" + game_name\n'
        'result = message.upper()'
    ),

    "control_flow_lesson_001": (
        "score = 85\n"
        "has_key = True\n"
        "if score >= 90:\n"
        '    rank = "Gold"\n'
        "elif score >= 75:\n"
        '    rank = "Silver"\n'
        "else:\n"
        '    rank = "Bronze"\n'
        "can_enter = has_key and score >= 75"
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

                passed, feedback = manager.validate(
                    challenge,
                    code,
                    variables=execution.get("variables", {})
                )
                self.assertTrue(passed, feedback)
                self.assertTrue(feedback.strip())

                for hidden_test in challenge.get("hidden_tests", []):

                    hidden_execution = run_user_code(
                        code,
                        input_values=hidden_test.get(
                            "input_values",
                            []
                        ),
                    )

                    self.assertTrue(
                        hidden_execution["success"],
                        hidden_execution.get("error"),
                    )

                    runtime_passed, runtime_feedback = (
                        manager.validate_runtime(
                            hidden_test.get(
                                "runtime_expected",
                                {}
                            ),
                            hidden_execution.get(
                                "variables",
                                {}
                            ),
                        )
                    )

                    self.assertTrue(
                        runtime_passed,
                        runtime_feedback,
                    )

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
                "score = 5\n"
                "score -= 3\n"
                "passed = score >= 8"
            ),

            "strings_lesson_001": (
                'game_name = "CodeBreak"\n'
                'message = "Welcome to\\n" + game_name\n'
                'result = message.lower()'
            ),

            "control_flow_lesson_001": (
                "score = 85\n"
                "has_key = True\n"
                "if score >= 90:\n"
                '    rank = "Gold"\n'
                "elif score >= 75:\n"
                '    rank = "Silver"\n'
                "else:\n"
                '    rank = "Bronze"\n'
                "can_enter = has_key or score >= 75"
            ),
        }

        for challenge_id, code in invalid_solutions.items():
            with self.subTest(challenge=challenge_id):
                challenge = CHALLENGES[challenge_id]

                execution = run_user_code(
                    code,
                    input_values=challenge.get("test_inputs", [])
                )

                variables = (
                    execution.get("variables", {})
                    if execution["success"]
                    else {}
                )

                passed, feedback = manager.validate(
                    challenge,
                    code,
                    variables=variables
                )

                self.assertFalse(passed)
                self.assertGreater(len(feedback.strip()), 5)


if __name__ == "__main__":
    unittest.main()
