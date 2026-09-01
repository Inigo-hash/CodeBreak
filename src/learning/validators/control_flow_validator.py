"""Validate beginner control-flow challenges."""

import ast


_COMPARISONS = {
    "gte": ast.GtE,
    "gt": ast.Gt,
    "lte": ast.LtE,
    "lt": ast.Lt,
    "eq": ast.Eq,
    "neq": ast.NotEq,
}


def _literal_assignment(statements, target_name):
    """Find a simple literal assignment such as score = 85."""

    for statement in statements:
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == target_name
        ):
            try:
                return ast.literal_eval(statement.value)
            except (ValueError, TypeError):
                return None

    return None


def _matches_compare(test, source_name, operator_name, value):
    """Check a comparison such as score >= 75."""

    operator_type = _COMPARISONS.get(
        str(operator_name).lower()
    )

    if operator_type is None:
        return False

    if not isinstance(test, ast.Compare):
        return False

    if len(test.ops) != 1:
        return False

    if len(test.comparators) != 1:
        return False

    if not isinstance(test.left, ast.Name):
        return False

    if test.left.id != source_name:
        return False

    if not isinstance(test.ops[0], operator_type):
        return False

    try:
        comparison_value = ast.literal_eval(
            test.comparators[0]
        )
    except (ValueError, TypeError):
        return False

    return comparison_value == value


class ControlFlowValidator:
    """
    Validate if/elif/else and boolean logic.

    Expected solution example:

        score = 85
        has_key = True

        if score >= 90:
            rank = "Gold"
        elif score >= 75:
            rank = "Silver"
        else:
            rank = "Bronze"

        can_enter = has_key and score >= 75
    """

    def validate(self, challenge, tree):
        expected = challenge.get("expected", {})

        score_target = expected.get("score_target")
        score_value = expected.get("score_value")

        key_target = expected.get("key_target")
        key_value = expected.get("key_value")

        rank_target = expected.get("rank_target")
        branches = expected.get("branches", [])
        else_result = expected.get("else_result")

        boolean_target = expected.get("boolean_target")
        boolean_variable = expected.get("boolean_variable")
        boolean_operator = expected.get("boolean_operator")

        comparison_operator = expected.get(
            "comparison_operator"
        )

        comparison_value = expected.get(
            "comparison_value"
        )

        # =====================================================
        # 1. Check starting variables
        # =====================================================

        if (
            _literal_assignment(tree.body, score_target)
            != score_value
        ):
            return False, (
                f"Create {score_target} with the value "
                f"{score_value}."
            )

        if (
            _literal_assignment(tree.body, key_target)
            is not key_value
        ):
            return False, (
                f"Set {key_target} to {key_value}."
            )

        # =====================================================
        # 2. Find if / elif / else
        # =====================================================

        chain = next(
            (
                node
                for node in tree.body
                if isinstance(node, ast.If)
            ),
            None
        )

        if chain is None:
            return False, (
                "Create an if/elif/else statement."
            )

        current = chain

        # =====================================================
        # 3. Validate if and elif branches
        # =====================================================

        for index, branch in enumerate(branches):

            if not _matches_compare(
                current.test,
                score_target,
                branch.get("operator"),
                branch.get("value")
            ):
                label = "if" if index == 0 else "elif"

                return False, (
                    f"Check the {label} condition."
                )

            branch_result = _literal_assignment(
                current.body,
                rank_target
            )

            if branch_result != branch.get("result"):
                return False, (
                    f"Set {rank_target} to "
                    f'"{branch.get("result")}" '
                    f"in branch {index + 1}."
                )

            if index < len(branches) - 1:

                if (
                    len(current.orelse) != 1
                    or not isinstance(
                        current.orelse[0],
                        ast.If
                    )
                ):
                    return False, (
                        "Add the required elif branch."
                    )

                current = current.orelse[0]

        # =====================================================
        # 4. Validate else
        # =====================================================

        if (
            not current.orelse
            or isinstance(current.orelse[0], ast.If)
        ):
            return False, (
                "Finish the decision with an else branch."
            )

        final_result = _literal_assignment(
            current.orelse,
            rank_target
        )

        if final_result != else_result:
            return False, (
                f'Set {rank_target} to "{else_result}" '
                f"in the else branch."
            )

        # =====================================================
        # 5. Find boolean expression
        #
        # can_enter = has_key and score >= 75
        # =====================================================

        boolean_expression = None

        for node in tree.body:

            if not isinstance(node, ast.Assign):
                continue

            if len(node.targets) != 1:
                continue

            if not isinstance(node.targets[0], ast.Name):
                continue

            if node.targets[0].id != boolean_target:
                continue

            boolean_expression = node.value
            break

        if boolean_expression is None:
            return False, (
                f"Create {boolean_target}."
            )

        # =====================================================
        # 6. Require AND
        # =====================================================

        if boolean_operator == "and":

            if (
                not isinstance(
                    boolean_expression,
                    ast.BoolOp
                )
                or not isinstance(
                    boolean_expression.op,
                    ast.And
                )
            ):
                return False, (
                    f"Build {boolean_target} "
                    f"using the and operator."
                )

        else:
            return False, (
                f"Unsupported boolean operator: "
                f"{boolean_operator}."
            )

        # =====================================================
        # 7. Require has_key
        # =====================================================

        has_boolean_variable = any(
            isinstance(value, ast.Name)
            and value.id == boolean_variable
            for value in boolean_expression.values
        )

        if not has_boolean_variable:
            return False, (
                f"Use {boolean_variable} in "
                f"{boolean_target}."
            )

        # =====================================================
        # 8. Require score >= 75
        # =====================================================

        has_comparison = any(
            _matches_compare(
                value,
                score_target,
                comparison_operator,
                comparison_value
            )
            for value in boolean_expression.values
        )

        if not has_comparison:
            return False, (
                f"Compare {score_target} with "
                f"{comparison_value} inside "
                f"{boolean_target}."
            )

        # =====================================================
        # Everything passed
        # =====================================================

        return True, (
            "Great job! You used control flow and "
            "boolean logic correctly."
        )