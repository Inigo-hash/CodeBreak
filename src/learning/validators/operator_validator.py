"""Validate beginner arithmetic-expression challenges."""

import ast


_OPERATORS = {
    "add": ast.Add,
    "subtract": ast.Sub,
    "multiply": ast.Mult,
    "divide": ast.Div,
}

_EVALUATE = {
    "add": lambda left, right: left + right,
    "subtract": lambda left, right: left - right,
    "multiply": lambda left, right: left * right,
    "divide": lambda left, right: left / right,
}


class OperatorValidator:
    """Require the authored binary operator, operands, and target name."""

    def validate(self, challenge, tree):
        expected = challenge.get("expected", {})
        target_name = expected.get("target")
        operator_name = str(expected.get("operator", "add")).lower()
        operator_type = _OPERATORS.get(operator_name)

        if operator_type is None:
            return False, f"Unknown operator requirement: {operator_name}."

        for node in ast.walk(tree):
            if (not isinstance(node, ast.Assign) or len(node.targets) != 1
                    or not isinstance(node.targets[0], ast.Name)
                    or node.targets[0].id != target_name):
                continue
            if not isinstance(node.value, ast.BinOp):
                return False, f"Build {target_name} with an arithmetic expression."
            if not isinstance(node.value.op, operator_type):
                return False, f"Use the {operator_name} operator in {target_name}."
            try:
                left = ast.literal_eval(node.value.left)
                right = ast.literal_eval(node.value.right)
            except (ValueError, TypeError, ZeroDivisionError):
                return False, "Use literal values on both sides of the operator."
            if left != expected.get("left") or right != expected.get("right"):
                return False, "Use the two values shown in the objective, in order."
            try:
                result = _EVALUATE[operator_name](left, right)
            except (TypeError, ZeroDivisionError):
                return False, "The two values cannot be used with that operator."
            if result != expected.get("value"):
                return False, f"{target_name} does not produce the expected value."
            return True, "Great job! You built the arithmetic expression correctly."

        return False, f"Store the arithmetic expression in {target_name}."
