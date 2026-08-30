"""Validate beginner boolean values and logical operators."""

import ast


class BooleanLogicValidator:
    """Require named booleans combined with ``and`` and ``not``."""

    def validate(self, challenge, tree):
        expected = challenge.get("expected", {})
        required_values = expected.get("variables", {})
        target_name = expected.get("target")
        found_values = {}
        target_value = None

        for node in tree.body:
            if (not isinstance(node, ast.Assign) or len(node.targets) != 1
                    or not isinstance(node.targets[0], ast.Name)):
                continue
            name = node.targets[0].id
            if name in required_values:
                try:
                    found_values[name] = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    pass
            if name == target_name:
                target_value = node.value

        for name, value in required_values.items():
            if found_values.get(name) is not value:
                return False, f"Set {name} to the requested boolean value."

        if not isinstance(target_value, ast.BoolOp) or not isinstance(target_value.op, ast.And):
            return False, f"Build {target_name} with the and operator."

        plain_name = expected.get("plain")
        negated_name = expected.get("negated")
        has_plain = any(
            isinstance(value, ast.Name) and value.id == plain_name
            for value in target_value.values
        )
        has_negated = any(
            isinstance(value, ast.UnaryOp) and isinstance(value.op, ast.Not)
            and isinstance(value.operand, ast.Name)
            and value.operand.id == negated_name
            for value in target_value.values
        )
        if not has_plain or not has_negated:
            return False, f"Combine {plain_name} and not {negated_name}."
        return True, "Great job! You combined the boolean conditions correctly."
