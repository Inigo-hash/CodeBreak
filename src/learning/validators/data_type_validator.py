"""
data_type_validator.py

Validates challenges involving basic Python data types.
"""

import ast


class DataTypeValidator:

    def validate(self, challenge, tree):

        expected = challenge.get(
            "expected",
            {}
        )

        found_variables = {}

        # Search through the player's code for assignments.
        #
        # Example:
        #
        # age = 18
        # name = "Alex"
        #
        for node in ast.walk(tree):

            if not isinstance(node, ast.Assign):
                continue

            # Only support simple assignments for this challenge.
            #
            # age = 18
            #
            # not:
            #
            # a = b = 18
            #
            if len(node.targets) != 1:
                continue

            target = node.targets[0]

            if not isinstance(target, ast.Name):
                continue

            # Safely get literal values such as:
            #
            # 18
            # 1.75
            # "Alex"
            # True
            #
            try:
                value = ast.literal_eval(
                    node.value
                )

            except (ValueError, TypeError):
                continue

            found_variables[
                target.id
            ] = value

        # Check every required variable.
        for variable_name, requirement in expected.items():

            if variable_name not in found_variables:

                return (
                    False,
                    f"Missing variable: {variable_name}"
                )

            actual_value = (
                found_variables[variable_name]
            )

            expected_type = requirement.get(
                "type"
            )

            expected_value = requirement.get(
                "value"
            )

            actual_type = type(
                actual_value
            ).__name__

            # Check the data type.
            if actual_type != expected_type:

                return (
                    False,
                    f"{variable_name} should be "
                    f"{expected_type}, not {actual_type}."
                )

            # Check the value.
            if actual_value != expected_value:

                return (
                    False,
                    f"{variable_name} has the wrong value."
                )

        return (
            True,
            "Great job! You used the correct data types."
        )