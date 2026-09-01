"""Validate beginner string handling, escape sequences, and string methods."""

import ast

class StringValidator:
    """
    Validate the Strings challenge.

    Expected solution:

        game_name = "CodeBreak"
        message = "Welcome to\\n" + game_name
        result = message.upper()
    """

    def validate(self, challenge, tree):
        expected = challenge.get("expected", {})

        name_target = expected.get("name_target")
        name_value = expected.get("name_value")

        message_target = expected.get("message_target")
        prefix = expected.get("prefix")

        result_target = expected.get("result_target")
        method_name = expected.get("method")
        expected_result = expected.get("result")

        # =====================================================
        # 1. Check the starting string
        #
        # game_name = "CodeBreak"
        # =====================================================

        found_name = False

        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue

            if len(node.targets) != 1:
                continue

            target = node.targets[0]

            if not isinstance(target, ast.Name):
                continue

            if target.id != name_target:
                continue

            if not isinstance(node.value, ast.Constant):
                continue

            if not isinstance(node.value.value, str):
                continue

            if node.value.value != name_value:
                return False, (
                    f'Set {name_target} to "{name_value}".'
                )

            found_name = True
            break

        if not found_name:
            return False, (
                f'Create {name_target} and set it to "{name_value}".'
            )

        # =====================================================
        # 2. Check string joining and escape sequence
        #
        # message = "Welcome to\n" + game_name
        # =====================================================

        found_message = False

        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue

            if len(node.targets) != 1:
                continue

            target = node.targets[0]

            if not isinstance(target, ast.Name):
                continue

            if target.id != message_target:
                continue

            if not isinstance(node.value, ast.BinOp):
                return False, (
                    f"Build {message_target} by joining the string "
                    f"and {name_target} with +."
                )

            if not isinstance(node.value.op, ast.Add):
                return False, (
                    "Use the + operator to join the strings."
                )

            left = node.value.left
            right = node.value.right

            if (
                not isinstance(left, ast.Constant)
                or not isinstance(left.value, str)
            ):
                return False, (
                    f"Start {message_target} with the required text."
                )

            if left.value != prefix:
                return False, (
                    "Check the text and the \\n escape sequence."
                )

            if (
                not isinstance(right, ast.Name)
                or right.id != name_target
            ):
                return False, (
                    f"Join the text with {name_target}."
                )

            found_message = True
            break

        if not found_message:
            return False, (
                f"Create {message_target} using the required "
                f"string and {name_target}."
            )

        # =====================================================
        # 3. Check the string method
        #
        # result = message.upper()
        # =====================================================

        found_method = False

        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue

            if len(node.targets) != 1:
                continue

            target = node.targets[0]

            if not isinstance(target, ast.Name):
                continue

            if target.id != result_target:
                continue

            if not isinstance(node.value, ast.Call):
                return False, (
                    f"Create {result_target} using "
                    f"{message_target}.{method_name}()."
                )

            call = node.value

            if not isinstance(call.func, ast.Attribute):
                return False, (
                    f"Use the .{method_name}() string method."
                )

            if call.func.attr != method_name:
                return False, (
                    f"Use the .{method_name}() string method."
                )

            if (
                not isinstance(call.func.value, ast.Name)
                or call.func.value.id != message_target
            ):
                return False, (
                    f"Call .{method_name}() on {message_target}."
                )

            if call.args or call.keywords:
                return False, (
                    f".{method_name}() does not need any arguments here."
                )

            found_method = True
            break

        if not found_method:
            return False, (
                f"Create {result_target} using "
                f"{message_target}.{method_name}()."
            )

        # =====================================================
        # Verify the expected final result
        # =====================================================

        try:
            combined = prefix + name_value

            if method_name == "upper":
                calculated_result = combined.upper()
            elif method_name == "lower":
                calculated_result = combined.lower()
            elif method_name == "strip":
                calculated_result = combined.strip()
            else:
                return False, (
                    f"Unsupported string method: {method_name}."
                )

        except (TypeError, AttributeError):
            return False, "The string result could not be calculated."

        if calculated_result != expected_result:
            return False, (
                f"{result_target} does not produce the expected text."
            )

        return True, (
            "Great job! You used string joining, an escape "
            "sequence, and a string method correctly."
        )