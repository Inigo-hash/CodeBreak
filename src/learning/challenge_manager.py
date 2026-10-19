#challenge_manager.py
import ast
from src.learning.sandbox import run_function_tests
from src.learning.validators.structure_validator import missing_construct
from src.learning.validators.integrated_final_validator import IntegratedFinalValidator

from src.learning.validators.variable_validator import VariableValidator
from src.learning.validators.print_validator import PrintValidator
from src.learning.validators.data_type_validator import DataTypeValidator
from src.learning.validators.type_casting_validator import TypeCastingValidator
from src.learning.validators.formatted_output_validator import FormattedOutputValidator
from src.learning.validators.input_validator import InputValidator
from src.learning.validators.operator_validator import OperatorValidator
from src.learning.validators.string_validator import StringValidator
from src.learning.validators.control_flow_validator import ControlFlowValidator
from src.learning.validators.stage1_final_validator import (
    Stage1FinalValidator,
)

class ChallengeManager:

    """
    Routes challenges to the correct validator.
    """

    def __init__(self):

        self.validators = {
            "stage1_integrated": IntegratedFinalValidator(),

            "variable":
                VariableValidator(),

            "print":
                PrintValidator(),

            "data_type":
                DataTypeValidator(),

            "type_casting":
                TypeCastingValidator(),

            "formatted_output":
                FormattedOutputValidator(),

            "input":
                InputValidator(),

            "operator":
                OperatorValidator(),

            "string":
                StringValidator(),

            "control_flow":
                ControlFlowValidator(),

            "stage1_final":
                Stage1FinalValidator(),
        }

    def validate_runtime(
        self,
        runtime_expected,
        variables,
    ):
        """Check final variable values from one sandbox execution."""

        for name, expected_value in runtime_expected.items():

            if name not in variables:
                return False, (
                    f"Create the variable {name}."
                )

            actual_value = variables[name]

            if type(actual_value) is not type(expected_value) or actual_value != expected_value:
                return False, (
                    f"{name} has the wrong final value."
                )

        return True, "Runtime values are correct."

    def validate(
        self,
        challenge,
        code,
        variables=None,
        output=None,
    ):

        if challenge.get('type') == 'function':
            try:
                tree = ast.parse(code)
            except SyntaxError as error:
                return False, f'Syntax error on line {error.lineno}: {error.msg}'
            target = next((node for node in tree.body if isinstance(node, ast.FunctionDef)
                           and node.name == challenge['function_name']), None)
            if target is None:
                return False, f"Define the required function {challenge['function_name']}."
            nodes = list(ast.walk(target))
            construct = challenge.get('learning_construct')
            required = {'for_loops': ast.For, 'while_loops': ast.While,
                        'nested_loops': ast.For, 'loop_control': ast.Break,
                        'exceptions': ast.Try}.get(construct)
            if required and not any(isinstance(node, required) for node in nodes):
                return False, f'This lesson asks you to use {construct.replace("_", " ")} inside your function.'
            if construct == 'nested_loops' and not any(
                isinstance(node, ast.For) and any(isinstance(inner, ast.For)
                    for statement in node.body for inner in ast.walk(statement)) for node in nodes):
                return False, 'Use an inner for loop inside an outer for loop.'
            missing = missing_construct(nodes, challenge.get('required_constructs', ()))
            if missing:
                return False, f'Use {missing} inside your function as required by this challenge.'
            helper = challenge.get('required_helper')
            if helper and (not any(isinstance(node, ast.FunctionDef) and node.name == helper for node in ast.walk(tree))
                           or not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                                      and node.func.id == helper for node in nodes)):
                return False, f'Define and call the helper {helper}.'
            return run_function_tests(code, challenge['function_name'], challenge['function_cases'],
                                      challenge.get('timeout', 3.0), challenge.get('preserve_args', False))

        try:
            tree = ast.parse(code)

        except SyntaxError as error:
            return False, error.msg

        validator = self.validators.get(
            challenge["type"]
        )

        if validator is None:
            return (
                False,
                "No validator exists for this challenge."
            )

        # ---------------------------------------------------------
        # 1. Check the required code structure.
        # ---------------------------------------------------------

        passed, feedback = validator.validate(
            challenge,
            tree
        )

        if not passed:
            return False, feedback

        # ---------------------------------------------------------
        # 2. Check runtime values when the challenge defines them.
        # ---------------------------------------------------------

        runtime_expected = challenge.get(
            "runtime_expected",
            {}
        )

        if runtime_expected:

            if variables is None:
                return False, (
                    "The code ran, but its final values "
                    "could not be checked."
                )

            runtime_passed, runtime_feedback = self.validate_runtime(
                runtime_expected,
                variables,
            )

            if not runtime_passed:
                return False, runtime_feedback

        if "expected_output" in challenge:
            if output is None or output.rstrip("\n") != challenge["expected_output"]:
                return False, "Your printed output does not match the objective."

        # Input prompts are echoed by the sandbox; check the final result
        # independently of how the learner spaces those prompts.
        if "expected_output_last_line" in challenge:
            lines = (output or "").splitlines()
            if not lines or lines[-1] != challenge["expected_output_last_line"]:
                return False, "Print the required final message after reading the inputs."

        return True, feedback
