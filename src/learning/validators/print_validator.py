#print_validator.py
import ast


class PrintValidator:

    """
    Validates challenges that ask the player to print a specific
    message, e.g. print("Hello, World!").

    Like VariableValidator, this checks the parsed AST rather than
    captured stdout, so it stays consistent with how ChallengeManager
    calls every validator (challenge dict + parsed source tree).
    """

    def validate(self, challenge, tree):

        expected_value = challenge["expected"]["value"]

        for node in ast.walk(tree):

            if not isinstance(node, ast.Call):
                continue

            if not isinstance(node.func, ast.Name) or node.func.id != "print":
                continue

            if len(node.args) != 1:
                continue

            arg = node.args[0]

            if not isinstance(arg, ast.Constant):
                continue

            if arg.value != expected_value:
                return False, (
                    f"Not quite. Try:\n\nprint(\"{expected_value}\")"
                )

            return True, "Correct! You printed it perfectly."

        return False, (
            f"Expected:\n\nprint(\"{expected_value}\")"
        )
