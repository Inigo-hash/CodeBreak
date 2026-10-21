"""Dedicated AST checks for Stage 2 iterative-structure challenges."""
import ast


class IterativeStructureValidator:
    """Require the loop constructs explicitly taught by the current challenge."""

    def validate(self, challenge, function_node):
        nodes = list(ast.walk(function_node))
        constructs = challenge.get("learning_constructs", [])
        checks = {
            "for": ast.For,
            "while": ast.While,
            "break": ast.Break,
            "continue": ast.Continue,
        }
        for construct in constructs:
            if construct == "nested_for":
                outer_loops = [node for node in nodes if isinstance(node, ast.For)]
                if not any(
                    any(isinstance(child, ast.For)
                        for statement in outer.body for child in ast.walk(statement))
                    for outer in outer_loops
                ):
                    return False, "Use an inner for loop inside an outer for loop."
                continue
            node_type = checks.get(construct)
            if node_type is None or not any(isinstance(node, node_type) for node in nodes):
                return False, f"This challenge requires a {construct} statement in your function."
        return True, "Required loop structures found."
