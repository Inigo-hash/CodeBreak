#challenge_manager.py
import ast

from src.learning.validators.variable_validator import VariableValidator
from src.learning.validators.print_validator import PrintValidator


class ChallengeManager:

    """
    Routes challenges to the correct validator.
    """

    def __init__(self):

        self.validators = {

            "variable": VariableValidator(),

            "print": PrintValidator()

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