"""Dedicated AST checks for Stage 2 list challenges."""
import ast


class ListsValidator:
    """Check list operations and safe list access before behavioral tests run."""

    def validate(self, challenge, function_node):
        nodes = list(ast.walk(function_node))
        required = challenge.get("required_list_operations", [])
        calls = {
            node.func.id for node in nodes
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        attributes = {
            node.func.attr for node in nodes
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        available = calls | attributes
        for operation in required:
            if operation not in available:
                return False, f"Use {operation} as required by this list challenge."
        if challenge.get("id", "").endswith("report_001"):
            if not any(isinstance(node, ast.If) for node in nodes):
                return False, "Check whether the list is empty before indexing it."
        if challenge.get("id", "").endswith("update_001"):
            if not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                       and node.func.id == "list" for node in nodes):
                return False, "Copy the input list with list(items) before modifying it."
            if ('remove' in required or challenge.get('require_membership_check')) and not any(
                    isinstance(node, ast.Compare) for node in nodes):
                return False, "Check whether the requested value exists before removing it."
        return True, "Required list operations found."
