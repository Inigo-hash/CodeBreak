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
from src.learning.validators.conditional_validator import ConditionalValidator
from src.learning.validators.boolean_logic_validator import BooleanLogicValidator
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

            "conditional":
                ConditionalValidator(),

            "boolean_logic":
                BooleanLogicValidator(),

            "control_flow":
                ControlFlowValidator()
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
