#challenge_manager.py
import ast

from src.learning.validators.variable_validator import VariableValidator
from src.learning.validators.print_validator import PrintValidator
from src.learning.validators.data_type_validator import DataTypeValidator
from src.learning.validators.type_casting_validator import TypeCastingValidator
from src.learning.validators.formatted_output_validator import FormattedOutputValidator
from src.learning.validators.input_validator import InputValidator
from src.learning.validators.operator_validator import OperatorValidator
from src.learning.validators.string_validator import StringValidator
from src.learning.validators.control_flow_validator import ControlFlowValidator

class ChallengeManager:

    """
    Routes challenges to the correct validator.
    """

    def __init__(self):

        self.validators = {

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

            if actual_value != expected_value:
                return False, (
                    f"{name} has the wrong final value."
                )

        return True, "Runtime values are correct."

    def validate(
        self,
        challenge,
        code,
        variables=None
    ):

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

        return True, feedback
