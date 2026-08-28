"""
input_validator.py

Validates beginner challenges using input().
"""

import ast


class InputValidator:

    def validate(
        self,
        challenge,
        tree
    ):

        expected = challenge.get(
            "expected",
            {}
        )

        target_name = expected.get(
            "target"
        )

        expected_prompt = expected.get(
            "prompt"
        )

        input_found = False

        # -----------------------------------------------------
        # Look for something like:
        #
        # name = input("Enter your name: ")
        #
        # Also supports future nested forms such as:
        #
        # age = int(input("Enter your age: "))
        # -----------------------------------------------------

        for node in ast.walk(tree):

            if not isinstance(
                node,
                ast.Assign
            ):
                continue

            if len(node.targets) != 1:
                continue

            target = node.targets[0]

            if not isinstance(
                target,
                ast.Name
            ):
                continue

            if target.id != target_name:
                continue

            # Search the assigned value for input().
            for child in ast.walk(
                node.value
            ):

                if not isinstance(
                    child,
                    ast.Call
                ):
                    continue

                if not isinstance(
                    child.func,
                    ast.Name
                ):
                    continue

                if child.func.id != "input":
                    continue

                input_found = True

                # -----------------------------------------
                # Validate the prompt
                # -----------------------------------------

                if expected_prompt is not None:

                    if len(child.args) != 1:

                        return (
                            False,
                            "Give input() the required prompt."
                        )

                    prompt = child.args[0]

                    if (
                        not isinstance(
                            prompt,
                            ast.Constant
                        )
                        or prompt.value
                        != expected_prompt
                    ):

                        return (
                            False,
                            f'Use the prompt:\n\n'
                            f'input("{expected_prompt}")'
                        )

                return (
                    True,
                    "Great job! You used input() correctly."
                )

        if not input_found:

            return (
                False,
                f"Use input() and store the result "
                f"inside {target_name}."
            )

        return (
            False,
            "The input() statement is not correct yet."
        )