"""
type_casting_validator.py

Validates challenges involving Python type casting.
"""

import ast


class TypeCastingValidator:

    def validate(self, challenge, tree):

        expected = challenge.get(
            "expected",
            {}
        )

        source_name = expected.get(
            "source"
        )

        source_value = expected.get(
            "source_value"
        )

        target_name = expected.get(
            "target"
        )

        casting_function = expected.get(
            "function"
        )

        source_found = False
        casting_found = False

        for node in ast.walk(tree):

            if not isinstance(node, ast.Assign):
                continue

            if len(node.targets) != 1:
                continue

            target = node.targets[0]

            if not isinstance(target, ast.Name):
                continue

            # -----------------------------------------
            # Check:
            #
            # age_text = "18"
            # -----------------------------------------

            if target.id == source_name:

                try:
                    value = ast.literal_eval(
                        node.value
                    )

                except (ValueError, TypeError):
                    value = None

                if value == source_value:
                    source_found = True

            # -----------------------------------------
            # Check:
            #
            # age = int(age_text)
            # -----------------------------------------

            if target.id == target_name:

                value = node.value

                if not isinstance(
                    value,
                    ast.Call
                ):
                    continue

                if not isinstance(
                    value.func,
                    ast.Name
                ):
                    continue

                # Must use int()
                if (
                    value.func.id
                    != casting_function
                ):
                    continue

                # int() should receive exactly one value.
                if len(value.args) != 1:
                    continue

                argument = value.args[0]

                # Must specifically cast age_text.
                if (
                    isinstance(argument, ast.Name)
                    and argument.id == source_name
                ):
                    casting_found = True

        if not source_found:

            return (
                False,
                f'Create {source_name} = "{source_value}" first.'
            )

        if not casting_found:

            return (
                False,
                f"Convert {source_name} using "
                f"{casting_function}() and store it in {target_name}."
            )

        return (
            True,
            "Great job! You used type casting correctly."
        )