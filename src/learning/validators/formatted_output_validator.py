"""
formatted_output_validator.py

Validates beginner formatted-output challenges using f-strings.
"""

import ast


class FormattedOutputValidator:

    def validate(self, challenge, tree):

        expected = challenge.get(
            "expected",
            {}
        )

        variable_name = expected.get(
            "variable"
        )

        variable_value = expected.get(
            "value"
        )

        prefix = expected.get(
            "prefix",
            ""
        )

        suffix = expected.get(
            "suffix",
            ""
        )

        variable_found = False
        formatted_print_found = False

        # -----------------------------------------------------
        # Find:
        #
        # name = "Alex"
        # -----------------------------------------------------

        for node in ast.walk(tree):

            if not isinstance(node, ast.Assign):
                continue

            if len(node.targets) != 1:
                continue

            target = node.targets[0]

            if not isinstance(target, ast.Name):
                continue

            if target.id != variable_name:
                continue

            try:
                value = ast.literal_eval(
                    node.value
                )

            except (ValueError, TypeError):
                continue

            if value == variable_value:
                variable_found = True

        # -----------------------------------------------------
        # Find:
        #
        # print(f"Welcome, {name}!")
        # -----------------------------------------------------

        for node in ast.walk(tree):

            if not isinstance(node, ast.Call):
                continue

            if not isinstance(node.func, ast.Name):
                continue

            if node.func.id != "print":
                continue

            if len(node.args) != 1:
                continue

            argument = node.args[0]

            # An f-string is represented as JoinedStr in the AST.
            if not isinstance(argument, ast.JoinedStr):
                continue

            values = argument.values

            if len(values) != 3:
                continue

            first = values[0]
            middle = values[1]
            last = values[2]

            # Check:
            #
            # "Welcome, "
            if (
                not isinstance(first, ast.Constant)
                or first.value != prefix
            ):
                continue

            # Check:
            #
            # {name}
            if not isinstance(
                middle,
                ast.FormattedValue
            ):
                continue

            if not isinstance(
                middle.value,
                ast.Name
            ):
                continue

            if middle.value.id != variable_name:
                continue

            # Check:
            #
            # "!"
            if (
                not isinstance(last, ast.Constant)
                or last.value != suffix
            ):
                continue

            formatted_print_found = True

        # -----------------------------------------------------
        # Feedback
        # -----------------------------------------------------

        if not variable_found:

            return (
                False,
                f'Create {variable_name} = "{variable_value}" first.'
            )

        if not formatted_print_found:

            return (
                False,
                f'Use an f-string like:\n\n'
                f'print(f"{prefix}{{{variable_name}}}{suffix}")'
            )

        return (
            True,
            "Great job! You used formatted output correctly."
        )