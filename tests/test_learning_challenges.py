"""End-to-end checks for every coding challenge shipped with the game."""

import unittest

from src.data.challenges import CHALLENGES
from src.data.practice_templates import generate_practice_challenge
from src.learning.challenge_manager import ChallengeManager
from src.learning.sandbox import run_user_code


VALID_SOLUTIONS = {
    'iterative_structure_lesson_for_001': (
        'def sum_training_points(limit):\n'
        '    total = 0\n'
        '    for number in range(1, limit + 1):\n'
        '        total += number\n'
        '    return total'
    ),
    'iterative_structure_lesson_nested_001': (
        'def count_training_tiles(rows, columns):\n'
        '    count = 0\n'
        '    for row in range(rows):\n'
        '        for column in range(columns):\n'
        '            count += 1\n'
        '    return count'
    ),
    'iterative_structure_lesson_control_001': (
        'def count_launch_numbers(start):\n'
        '    count = 0\n'
        '    number = start\n'
        '    while number > 0:\n'
        '        count += 1\n'
        '        number -= 1\n'
        '    return count'
    ),
    'lists_lesson_report_001': (
        'def list_report(items):\n'
        '    if not items:\n'
        '        return (None, 0)\n'
        '    return (items[0], len(items))'
    ),
    'lists_lesson_update_001': (
        'def add_inventory_item(items, new_item):\n'
        '    result = list(items)\n'
        '    result.append(new_item)\n'
        '    return result'
    ),
    'functions_lesson_greet_001': (
        'def greet_explorer(name):\n'
        '    return "Hello, " + name'
    ),
    'functions_lesson_total_001': (
        'def add_supplies(first, second):\n'
        '    return first + second'
    ),
    'tuples_lesson_coordinates_001': (
        'def make_coordinates(x, y):\n'
        '    return (x, y)'
    ),
    'tuples_lesson_distance_001': (
        'def get_x_coordinate(point):\n'
        '    return point[0]'
    ),
    'error_handling_lesson_safe_int_001': (
        'def safe_number(text):\n'
        '    try:\n'
        '        return int(text)\n'
        '    except ValueError:\n'
        '        return None'
    ),
    'error_handling_lesson_safe_divide_001': (
        'def safe_divide(first, second):\n'
        '    try:\n'
        '        return first / second\n'
        '    except ZeroDivisionError:\n'
        '        return None'
    ),
}


from castle_solutions import CASTLE_SOLUTIONS
VALID_SOLUTIONS.update(CASTLE_SOLUTIONS)
from island_solutions import ISLAND_SOLUTIONS
from citadel_solutions import CITADEL_SOLUTIONS
from test_stage2_dining import SOLUTIONS as LEGACY_LIST_SOLUTIONS
VALID_SOLUTIONS.update(ISLAND_SOLUTIONS)
VALID_SOLUTIONS.update(LEGACY_LIST_SOLUTIONS)
VALID_SOLUTIONS.update(CITADEL_SOLUTIONS)


class LearningChallengeTests(unittest.TestCase):
    def test_formatted_output_accepts_empty_suffix(self):
        challenge = generate_practice_challenge("formatted_output_d")
        expected = challenge["expected"]
        code = (
            expected["variable"]
            + " = "
            + repr(expected["value"])
            + "\nprint(f\""
            + expected["prefix"]
            + "{"
            + expected["variable"]
            + "}"
            + expected["suffix"]
            + '\")'
        )
        manager = ChallengeManager()

        passed, feedback = manager.validate(challenge, code)

        self.assertTrue(passed, feedback)

    def test_every_challenge_has_a_runnable_valid_solution(self):
        graded = {cid: challenge for cid, challenge in CHALLENGES.items() if challenge.get('type')}
        self.assertEqual(set(graded), set(VALID_SOLUTIONS))
        manager = ChallengeManager()

        for challenge_id, challenge in graded.items():
            with self.subTest(challenge=challenge_id):
                code = VALID_SOLUTIONS[challenge_id]
                execution = run_user_code(
                    code, input_values=challenge.get("test_inputs", [])
                )
                self.assertTrue(execution["success"], execution.get("error"))

                passed, feedback = manager.validate(
                    challenge,
                    code,
                    variables=execution.get("variables", {}),
                    output=execution.get("output", ""),
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
                'message = "Welcome to\n" + game_name\n'
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
