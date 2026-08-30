"""Validate a beginner if/elif/else decision chain."""

import ast


_COMPARISONS = {
    "gte": ast.GtE,
    "gt": ast.Gt,
    "lte": ast.LtE,
    "lt": ast.Lt,
    "eq": ast.Eq,
}


def _literal_assignment(statements, target_name):
    for statement in statements:
        if (isinstance(statement, ast.Assign) and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
                and statement.targets[0].id == target_name):
            try:
                return ast.literal_eval(statement.value)
            except (ValueError, TypeError):
                return None
    return None


def _matches_compare(test, source_name, operator_name, value):
    operator_type = _COMPARISONS.get(str(operator_name).lower())
    if (operator_type is None or not isinstance(test, ast.Compare)
            or len(test.ops) != 1 or len(test.comparators) != 1
            or not isinstance(test.left, ast.Name)
            or test.left.id != source_name
            or not isinstance(test.ops[0], operator_type)):
        return False
    try:
        return ast.literal_eval(test.comparators[0]) == value
    except (ValueError, TypeError):
        return False


class ConditionalValidator:
    """Require the authored source and complete if/elif/else structure."""

    def validate(self, challenge, tree):
        expected = challenge.get("expected", {})
        source = expected.get("source")
        target = expected.get("target")
        branches = expected.get("branches", ())

        if _literal_assignment(tree.body, source) != expected.get("source_value"):
            return False, f"Create {source} with the requested starting value."

        chain = next((node for node in tree.body if isinstance(node, ast.If)), None)
        if chain is None:
            return False, "Add an if/elif/else decision."

        current = chain
        for index, branch in enumerate(branches):
            if not _matches_compare(
                current.test, source, branch.get("operator"), branch.get("value")
            ):
                label = "if" if index == 0 else "elif"
                return False, f"Check the {label} condition and comparison value."
            if _literal_assignment(current.body, target) != branch.get("result"):
                return False, f"Assign the requested {target} inside branch {index + 1}."
            if index < len(branches) - 1:
                if len(current.orelse) != 1 or not isinstance(current.orelse[0], ast.If):
                    return False, "Add the required elif branch after the if branch."
                current = current.orelse[0]

        if not current.orelse or isinstance(current.orelse[0], ast.If):
            return False, "Finish the decision with an else branch."
        if _literal_assignment(current.orelse, target) != expected.get("else_result"):
            return False, f"Assign the requested {target} inside the else branch."
        return True, "Great job! Your if/elif/else chain is complete."
