"""Structure checks for the three new Stage 1 assessment variants.

Runtime values and printed output are checked separately for every test case.
"""
import ast


class IntegratedFinalValidator:
    def validate(self, challenge, tree):
        nodes = list(ast.walk(tree))
        assigned = {node.id for node in nodes if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)}
        required = set(challenge.get('runtime_expected', {}))
        if required - assigned:
            return False, 'Create the required variables: ' + ', '.join(sorted(required - assigned)) + '.'
        inputs = set()
        for node in nodes:
            if isinstance(node, ast.Assign) and any(
                isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == 'input'
                for child in ast.walk(node.value)
            ):
                inputs.update(target.id for target in node.targets if isinstance(target, ast.Name))
        if not {'name', 'amount_text'} <= inputs:
            return False, 'Read name and amount_text using input().'
        if not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id == 'int' and node.args
                   and isinstance(node.args[0], ast.Name) and node.args[0].id == 'amount_text' for node in nodes):
            return False, 'Convert amount_text using int().'
        if not any(isinstance(node, (ast.BinOp, ast.AugAssign)) for node in nodes):
            return False, 'Calculate total with the arithmetic operators in the instructions.'
        if not any(isinstance(node, ast.If) and len(node.orelse) == 1
                   and isinstance(node.orelse[0], ast.If) and node.orelse[0].orelse for node in nodes):
            return False, 'Use if / elif / else to select status.'
        if not any(isinstance(node, ast.JoinedStr) for node in nodes):
            return False, 'Build message with an f-string.'
        if not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                   and node.func.attr == 'upper' for node in nodes):
            return False, 'Use message.upper() to create final_message.'
        if not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id == 'print' for node in nodes):
            return False, 'Print final_message.'
        return True, 'All required concepts and test cases are correct.'
