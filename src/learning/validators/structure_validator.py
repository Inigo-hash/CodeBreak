"""Check authored Python structure rules without knowing any lesson or stage IDs.

Rules live on challenges under ``structure_requirements``. Runtime values and
behavioral test cases remain the responsibility of ChallengeManager/sandbox.
"""
import ast


CONSTRUCT_NODES = {
    'for': ast.For, 'while': ast.While, 'break': ast.Break,
    'continue': ast.Continue, 'try': ast.Try,
}


def missing_construct(nodes, requirements):
    """Return the first absent (or unknown) authored construct, if any."""
    for name in requirements:
        node_type = CONSTRUCT_NODES.get(name)
        if node_type is None or not any(isinstance(node, node_type) for node in nodes):
            return name
    return None


def _name(node, value):
    return isinstance(node, ast.Name) and node.id == value


def _call(node, name):
    return isinstance(node, ast.Call) and _name(node.func, name)


def _assignment(node, target):
    return (isinstance(node, ast.Assign) and len(node.targets) == 1
            and _name(node.targets[0], target))


def _matches(rule, tree, nodes):
    kind = rule['kind']
    if kind == 'variables':
        if rule.get('include_all_stores'):
            assigned = {n.id for n in nodes if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
        else:
            assigned = {target.id for n in nodes if isinstance(n, ast.Assign)
                        for target in n.targets if isinstance(target, ast.Name)}
            assigned.update(n.target.id for n in nodes if isinstance(n, ast.AugAssign)
                            and isinstance(n.target, ast.Name))
        return set(rule['names']).issubset(assigned)
    if kind == 'input':
        return any(isinstance(n, ast.Assign)
                   and (not rule.get('single_target') or len(n.targets) == 1)
                   and any(_name(target, rule['target']) for target in n.targets)
                   and any(_call(child, 'input') for child in ast.walk(n.value)) for n in nodes)
    if kind == 'cast':
        candidates = [n.value for n in nodes if _assignment(n, rule['target'])] if rule.get('target') else nodes
        return any(_call(n, rule['function']) and n.args
                   and _name(n.args[0], rule['source'])
                   and (not rule.get('exactly_one_arg') or len(n.args) == 1) for n in candidates)
    if kind == 'aug_assign':
        operator = getattr(ast, rule['operator'], None)
        return operator is not None and any(
            isinstance(n, ast.AugAssign) and _name(n.target, rule['target'])
            and isinstance(n.op, operator) and isinstance(n.value, ast.Constant)
            and n.value.value == rule['value'] for n in nodes)
    if kind == 'arithmetic':
        return any(isinstance(n, (ast.BinOp, ast.AugAssign)) for n in nodes)
    if kind == 'if_elif_else':
        candidates = nodes
        if rule.get('first_top_level'):
            first = next((n for n in tree.body if isinstance(n, ast.If)), None)
            candidates = [first]
        return any(isinstance(n, ast.If) and len(n.orelse) == 1
                   and isinstance(n.orelse[0], ast.If) and n.orelse[0].orelse for n in candidates)
    if kind == 'f_string':
        candidates = [n.value for n in nodes if _assignment(n, rule['target'])] if rule.get('target') else nodes
        return any(isinstance(n, ast.JoinedStr) for n in candidates)
    if kind == 'method':
        candidates = [n.value for n in nodes if _assignment(n, rule['target'])] if rule.get('target') else nodes
        return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr == rule['method']
                   and (not rule.get('source') or _name(n.func.value, rule['source'])) for n in candidates)
    if kind == 'print':
        return any(_call(n, 'print') and (not rule.get('source')
                   or (len(n.args) == 1 and _name(n.args[0], rule['source']))) for n in nodes)
    return False


class StructureValidator:
    """Missing or invalid rule configuration must never silently pass."""
    def validate(self, challenge, tree):
        rules = challenge.get('structure_requirements')
        if not isinstance(rules, (tuple, list)) or not rules:
            return False, 'This challenge has no configured structure requirements.'
        nodes = list(ast.walk(tree))
        for rule in rules:
            try:
                matched = _matches(rule, tree, nodes)
            except (KeyError, TypeError, AttributeError):
                return False, 'This challenge has an invalid structure requirement.'
            if not matched:
                return False, rule.get('feedback', 'Include the required ' + str(rule.get('kind', 'code structure')) + '.')
        return True, challenge.get('structure_success', 'All required concepts and test cases are correct.')
