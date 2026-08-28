#challenge_manager.py
import ast

from src.learning.validators.variable_validator import VariableValidator
from src.learning.validators.print_validator import PrintValidator
from src.learning.validators.data_type_validator import DataTypeValidator
from src.learning.validators.type_casting_validator import TypeCastingValidator
from src.learning.validators.formatted_output_validator import FormattedOutputValidator
from src.learning.validators.input_validator import InputValidator


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
                InputValidator()

        }

    def validate(self, challenge, code):

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

        return validator.validate(
            challenge,
            tree
        )