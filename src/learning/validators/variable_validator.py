import ast


class VariableValidator:

    """
    Validates variable assignment challenges.
    """

    def validate(self, challenge, tree):

        expected = challenge["expected"]

        expected_name = expected["name"]

        expected_value = expected["value"]

        for node in ast.walk(tree):

            if not isinstance(node, ast.Assign):

                continue

            if len(node.targets) != 1:

                continue

            target = node.targets[0]

            if not isinstance(target, ast.Name):

                continue

            if target.id != expected_name:

                continue

            if not isinstance(node.value, ast.Constant):

                continue

            if node.value.value != expected_value:

                return False, (
                    f"'{expected_name}' has the wrong value."
                )

            return True, "Correct!"

        return False, (
            f"Expected:\n\n{expected_name} = {expected_value}"
        )