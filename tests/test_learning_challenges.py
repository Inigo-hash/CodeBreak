"""End-to-end checks for every coding challenge shipped with the game."""

import unittest

from src.data.challenges import CHALLENGES
from src.data.practice_templates import generate_practice_challenge
from src.learning.challenge_manager import ChallengeManager
from src.learning.sandbox import run_user_code


VALID_SOLUTIONS = {
    'iterative_structure_lesson_for_001': (
        'def sum_usable_supplies(amounts):\n'
        '    total = 0\n'
        '    for amount in amounts:\n'
        '        if amount > 0:\n            total += amount\n'
        '    return total'
    ),
    'iterative_structure_lesson_nested_001': (
        'def count_grid_relics(grid):\n'
        '    count = 0\n'
        '    for row in grid:\n'
        '        for value in row:\n'
        '            if value != 0:\n                count += 1\n'
        '    return count'
    ),
    'iterative_structure_lesson_control_001': (
        'def accepted_order_total(orders):\n'
        '    total = 0\n    index = 0\n'
        '    while index < len(orders):\n'
        '        value = orders[index]\n        index += 1\n'
        '        if value is None:\n            break\n'
        '        if value <= 0:\n            continue\n'
        '        total += value\n'
        '    return total'
    ),
    'lists_lesson_report_001': (
        'def list_report(items):\n'
        '    if not items:\n        return (None, None, 0)\n'
        '    return (items[0], items[-1], len(items))'
    ),
    'lists_lesson_update_001': (
        'def update_archive(items, added, removed):\n'
        '    result = list(items)\n    result.append(added)\n'
        '    if removed in result:\n        result.remove(removed)\n'
        '    popped = result.pop() if result else None\n'
        '    return (result, popped)'
    ),
    'castle_lists_inspect_001': (
        'def describe_items(items):\n'
        '    return (items[0], items[-1], len(items)) if items else (None, None, 0)'
    ),
    'castle_lists_update_001': (
        'def update_items(items, added, removed):\n'
        '    result = list(items)\n    result.append(added)\n'
        '    if removed in result:\n        result.remove(removed)\n'
        '    popped = result.pop() if result else None\n'
        '    return (result, popped)'
    ),
    "stage1_final_001": (
        'name = input("Enter explorer name: ")\n'
        'score_text = input("Enter score: ")\n'
        'score = int(score_text)\nscore += 10\n'
        'if score >= 90:\n    rank = "Gold"\n'
        'elif score >= 75:\n    rank = "Silver"\n'
        'else:\n    rank = "Bronze"\n'
        'message = f"{name} - {rank}"\n'
        'final_message = message.upper()\nprint(final_message)'
    ),
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


from castle_solutions import CASTLE_SOLUTIONS
VALID_SOLUTIONS.update(CASTLE_SOLUTIONS)


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
