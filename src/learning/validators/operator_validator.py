#operator_validator.py
"""Validate beginner operator challenges."""

import ast


# =========================================================
# Assignment Operators
# =========================================================

_ASSIGNMENT_OPERATORS = {
    "add_assign": ast.Add,
    "subtract_assign": ast.Sub,
    "multiply_assign": ast.Mult,
    "divide_assign": ast.Div,
}

_ASSIGNMENT_EVALUATE = {
    "add_assign": lambda left, right: left + right,
    "subtract_assign": lambda left, right: left - right,
    "multiply_assign": lambda left, right: left * right,
    "divide_assign": lambda left, right: left / right,
}


# =========================================================
# Comparison Operators
# =========================================================

_COMPARISON_OPERATORS = {
    "eq": ast.Eq,
    "neq": ast.NotEq,
    "gt": ast.Gt,
    "lt": ast.Lt,
    "gte": ast.GtE,
    "lte": ast.LtE,
}

_COMPARISON_EVALUATE = {
    "eq": lambda left, right: left == right,
    "neq": lambda left, right: left != right,
    "gt": lambda left, right: left > right,
    "lt": lambda left, right: left < right,
    "gte": lambda left, right: left >= right,
    "lte": lambda left, right: left <= right,
}


class OperatorValidator:
    """
    Validate the Operators challenge.

    Expected solution example:

        score = 5
        score += 3
        passed = score >= 8
    """

    def validate(self, challenge, tree):
        expected = challenge.get("expected", {})

        target = expected.get("target")
        start_value = expected.get("start_value")

        operator_name = expected.get("operator")
        update_value = expected.get("update_value")
        final_value = expected.get("final_value")

        comparison_target = expected.get("comparison_target")
        comparison_operator = expected.get("comparison_operator")
        comparison_value = expected.get("comparison_value")
        comparison_result = expected.get("comparison_result")

        # -----------------------------------------------------
        # Check supported operators
        # -----------------------------------------------------

        assignment_operator_type = _ASSIGNMENT_OPERATORS.get(
            operator_name
        )

        if assignment_operator_type is None:
            return False, (
                f"Unknown assignment operator requirement: "
                f"{operator_name}."
            )

        comparison_operator_type = _COMPARISON_OPERATORS.get(
            comparison_operator
        )

        if comparison_operator_type is None:
            return False, (
                f"Unknown comparison operator requirement: "
                f"{comparison_operator}."
            )

        # -----------------------------------------------------
        # 1. Check starting assignment
        #
        # score = 5
        # -----------------------------------------------------

        found_start = False

        for node in ast.walk(tree):

            if not isinstance(node, ast.Assign):
                continue

            if len(node.targets) != 1:
                continue

            target_node = node.targets[0]

            if not isinstance(target_node, ast.Name):
                continue

            if target_node.id != target:
                continue

            try:
                value = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue

            if value == start_value:
                found_start = True
                break

        if not found_start:
            return False, (
                f"Start by creating {target} "
                f"with the value {start_value}."
            )

        # -----------------------------------------------------
        # 2. Check assignment operator
        #
        # score += 3
        # -----------------------------------------------------

        found_assignment_operator = False

        for node in ast.walk(tree):

            if not isinstance(node, ast.AugAssign):
                continue

            if not isinstance(node.target, ast.Name):
                continue

            if node.target.id != target:
                continue

            if not isinstance(node.op, assignment_operator_type):
                continue

            try:
                value = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue

            if value != update_value:
                continue

            found_assignment_operator = True
            break

        if not found_assignment_operator:
            return False, (
                f"Use the required assignment operator on "
                f"{target} with the value {update_value}."
            )

        # -----------------------------------------------------
        # Check resulting value
        # -----------------------------------------------------

        try:
            calculated_final = _ASSIGNMENT_EVALUATE[
                operator_name
            ](
                start_value,
                update_value
            )
        except (TypeError, ZeroDivisionError):
            return False, (
                "The assignment operation could not be calculated."
            )

        if calculated_final != final_value:
            return False, (
                f"{target} does not produce the expected final value."
            )

        # -----------------------------------------------------
        # 3. Check comparison
        #
        # passed = score >= 8
        # -----------------------------------------------------

        found_comparison = False

        for node in ast.walk(tree):

            if not isinstance(node, ast.Assign):
                continue

            if len(node.targets) != 1:
                continue

            target_node = node.targets[0]

            if not isinstance(target_node, ast.Name):
                continue

            if target_node.id != comparison_target:
                continue

            if not isinstance(node.value, ast.Compare):
                continue

            comparison = node.value

            if len(comparison.ops) != 1:
                continue

            if len(comparison.comparators) != 1:
                continue

            if not isinstance(
                comparison.left,
                ast.Name
            ):
                continue

            if comparison.left.id != target:
                continue

            if not isinstance(
                comparison.ops[0],
                comparison_operator_type
            ):
                continue

            try:
                right_value = ast.literal_eval(
                    comparison.comparators[0]
                )
            except (ValueError, TypeError):
                continue

            if right_value != comparison_value:
                continue

            found_comparison = True
            break

        if not found_comparison:
            return False, (
                f"Create {comparison_target} by comparing "
                f"{target} with {comparison_value}."
            )

        # -----------------------------------------------------
        # Check expected comparison result
        # -----------------------------------------------------

        try:
            calculated_result = _COMPARISON_EVALUATE[
                comparison_operator
            ](
                final_value,
                comparison_value
            )
        except TypeError:
            return False, (
                "The comparison could not be calculated."
            )

        if calculated_result != comparison_result:
            return False, (
                f"{comparison_target} does not produce "
                f"the expected result."
            )

        # -----------------------------------------------------
        # Everything passed
        # -----------------------------------------------------

        return True, (
            "Great job! You used assignment and "
            "comparison operators correctly."
        )