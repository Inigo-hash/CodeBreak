"""Assessment contracts remain strict and reusable without scenario names."""
import ast
import copy
import unittest
from src.data.challenges import CHALLENGES
from src.data.final_assessments import ASSESSMENT_IDS, get_final_assessment
from src.learning.challenge_manager import ChallengeManager
from src.learning.sandbox import run_user_code
from src.learning.validators.structure_validator import StructureValidator
from test_learning_challenges import VALID_SOLUTIONS


class ConfigurableAssessmentTests(unittest.TestCase):
    def test_all_island_assessments_pass_sample_and_hidden_runtime_cases(self):
        specifications = {
            'stage1_supply_final': ('amount * 4 + 6', 46, 26, ('Stocked', 'Ready', 'Low'), 'Supplies'),
            'stage1_energy_final': ('(amount - 15) * 2', 100, 50, ('Stable', 'Charging', 'Weak'), 'Energy'),
            'stage1_bridge_final': ('amount * 5 - 20', 100, 50, ('Complete', 'Partial', 'Insufficient'), 'Budget'),
        }
        manager = ChallengeManager()
        for cid in ASSESSMENT_IDS:
            challenge = get_final_assessment(cid)
            if cid in specifications:
                calc, top, middle, labels, subject = specifications[cid]
                code = (f'name = input()\namount_text = input()\namount = int(amount_text)\ntotal = {calc}\n'
                        f'if total >= {top}:\n    status = {labels[0]!r}\n'
                        f'elif total >= {middle}:\n    status = {labels[1]!r}\nelse:\n    status = {labels[2]!r}\n'
                        f'ready = total >= {middle}\nmessage = f"{{name}} - {subject}: {{total}} - {{status}}"\n'
                        'final_message = message.upper()\nprint(final_message)')
            else:
                code = VALID_SOLUTIONS[cid]
            for case in [dict(input_values=challenge['test_inputs'], runtime_expected=challenge['runtime_expected'],
                              expected_output_last_line=challenge['expected_output_last_line'])] + challenge['hidden_tests']:
                with self.subTest(challenge=cid, inputs=case['input_values']):
                    run = run_user_code(code, input_values=case['input_values'])
                    self.assertTrue(run['success'], run.get('error'))
                    evaluated = dict(challenge, runtime_expected=case['runtime_expected'],
                                     expected_output_last_line=case['expected_output_last_line'])
                    passed, feedback = manager.validate(evaluated, code, run['variables'], run['output'])
                    self.assertTrue(passed, feedback)

    def test_original_structure_requirements_still_reject_each_missing_concept(self):
        challenge = CHALLENGES['stage1_final_001']
        code = VALID_SOLUTIONS[challenge['id']]
        replacements = [('name = input("Enter explorer name: ")', 'name = "Alex"'),
                        ('score = int(score_text)', 'score = 70'), ('score += 10', 'score = score + 10'),
                        ('message = f"{name} - {rank}"', 'message = name + " - " + rank'),
                        ('final_message = message.upper()', 'final_message = message'),
                        ('print(final_message)', 'print("ALEX - SILVER")')]
        validator = StructureValidator()
        for old, new in replacements:
            with self.subTest(concept=old):
                self.assertIn(old, code)
                self.assertFalse(validator.validate(challenge, ast.parse(code.replace(old, new)))[0])

    def test_new_variable_names_and_operations_are_controlled_by_data(self):
        challenge = {'structure_requirements': [
            {'kind': 'variables', 'names': ['entry', 'energy']},
            {'kind': 'input', 'target': 'entry'},
            {'kind': 'cast', 'function': 'float', 'source': 'entry', 'target': 'energy'},
            {'kind': 'aug_assign', 'target': 'energy', 'operator': 'Mult', 'value': 2},
            {'kind': 'print', 'source': 'energy'}]}
        before = copy.deepcopy(challenge)
        self.assertTrue(StructureValidator().validate(challenge, ast.parse('entry = input()\nenergy = float(entry)\nenergy *= 2\nprint(energy)'))[0])
        self.assertFalse(StructureValidator().validate(challenge, ast.parse('entry = input()\nenergy = float(entry)\nenergy += 2\nprint(energy)'))[0])
        self.assertEqual(challenge, before)
        for rules in (None, [], [{'kind': 'unknown'}], [{'kind': 'cast'}]):
            self.assertFalse(StructureValidator().validate({'structure_requirements': rules}, ast.parse('pass'))[0])

    def test_renamed_function_still_requires_continue_when_authored(self):
        challenge = copy.deepcopy(CHALLENGES['castle_loop_control_skip_001'])
        code = VALID_SOLUTIONS[challenge['id']]
        challenge['function_name'] = 'filter_readings'
        code = code.replace('positive_before_stop', 'filter_readings')
        manager = ChallengeManager()
        self.assertTrue(manager.validate(challenge, code)[0])
        without_continue = ('def filter_readings(numbers):\n    result = []\n    for value in numbers:\n'
                            '        if value == 0:\n            break\n        if value > 0:\n            result.append(value)\n    return result')
        self.assertFalse(manager.validate(challenge, without_continue)[0])
        challenge['required_constructs'] = ['break']
        self.assertTrue(manager.validate(challenge, without_continue)[0])
