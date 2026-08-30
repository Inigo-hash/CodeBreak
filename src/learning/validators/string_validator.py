"""Validate beginner string construction and concatenation."""

import ast


def _string_parts(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _string_parts(node.left)
        right = _string_parts(node.right)
        return left + right if left is not None and right is not None else None
    return None


class StringValidator:
    """Require quoted string pieces joined with the + operator."""

    def validate(self, challenge, tree):
        expected = challenge.get("expected", {})
        target_name = expected.get("target")
        expected_parts = list(expected.get("parts", ()))

        for node in ast.walk(tree):
            if (not isinstance(node, ast.Assign) or len(node.targets) != 1
                    or not isinstance(node.targets[0], ast.Name)
                    or node.targets[0].id != target_name):
                continue
            parts = _string_parts(node.value)
            if parts is None or not isinstance(node.value, ast.BinOp):
                return False, "Join the quoted string pieces with the + operator."
            if parts != expected_parts:
                return False, "Check the words, spaces, and punctuation in each string."
            if "".join(parts) != expected.get("value"):
                return False, f"{target_name} does not form the requested text."
            return True, "Great job! You joined the strings correctly."

        return False, f"Create the string variable {target_name}."
