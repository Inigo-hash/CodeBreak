"""Stage 1 final assessment pool. Limits are starting values for playtesting."""
from copy import deepcopy

FINAL_COMPLETION_ID = 'stage1_final_001'
ASSESSMENT_IDS = ('stage1_final_001', 'stage1_supply_final', 'stage1_energy_final', 'stage1_bridge_final')


def _case(name, amount, operation, top, middle, labels, subject):
    value = operation(amount)
    status = labels[0] if value >= top else labels[1] if value >= middle else labels[2]
    message = f'{name} - {subject}: {value} - {status}'
    return {
        'input_values': [name, str(amount)],
        'runtime_expected': {'name': name, 'amount_text': str(amount), 'amount': amount,
                             'total': value, 'status': status, 'ready': value >= middle,
                             'message': message, 'final_message': message.upper()},
        'expected_output_last_line': message.upper(),
    }


def _build(key, title, story, calculation, operation, top, middle, labels, subject, values, limit):
    cases = [_case(name, amount, operation, top, middle, labels, subject)
             for name, amount in zip(('Alex', 'Mika', 'Luna', 'Kai', 'Robin', 'Sam'), values)]
    sample = cases[0]
    return {
        'id': key, 'title': title, 'difficulty': 'Beginner Final',
        'type': 'stage1_integrated', 'time_limit': limit,
        'objective': 'Apply the Stage 1 Python topics to complete the final assessment.',
        'problem': f'''{story}

Read two inputs in this order:
1. Store the explorer name in name.
2. Store the number (as text) in amount_text.
Convert amount_text with int() and store it in amount.

{calculation}
Store the calculated integer in total.

Use if / elif / else to set status:
- {labels[0]} if total >= {top}
- {labels[1]} if total >= {middle}
- {labels[2]} otherwise

Set ready to the Boolean result of total >= {middle}.
Build message using an f-string in exactly this format:
{{name}} - {subject}: {{total}} - {{status}}
Use message.upper() to create final_message.
Print final_message.

Example inputs: {sample['input_values'][0]}, {sample['input_values'][1]}
Expected final printed line:
{sample['expected_output_last_line']}

Your program is also checked with other names and numbers.
You may fix and resubmit until time runs out.''',
        'test_inputs': sample['input_values'],
        'runtime_expected': sample['runtime_expected'],
        'expected_output_last_line': sample['expected_output_last_line'],
        'hidden_tests': cases[1:],
        'hints': [
            'Read the two inputs in order. input() returns text.',
            'Convert amount_text with int() before calculating total.',
            'Check the highest threshold first, then the middle threshold, then else.',
            'Use the calculated total and status in your f-string, then uppercase and print it.',
        ],
    }


NEW_ASSESSMENTS = {
    'stage1_supply_final': _build(
        'stage1_supply_final', 'Supply Station Report',
        'The island camp needs a report showing the supplies you recovered.',
        'Each crate contains 4 supplies. Multiply amount by 4, then add 6 bonus supplies.',
        lambda n: n * 4 + 6, 46, 26, ('Stocked', 'Ready', 'Low'), 'Supplies',
        (5, 10, 9, 4, 0, 20), 480),
    'stage1_energy_final': _build(
        'stage1_energy_final', 'Gate Energy Check',
        'The final gate spends energy on repairs before it can open.',
        'Start with amount energy. Subtract 15 for repairs, then multiply the remainder by 2.',
        lambda n: (n - 15) * 2, 100, 50, ('Stable', 'Charging', 'Weak'), 'Energy',
        (40, 65, 64, 39, 15, 80), 600),
    'stage1_bridge_final': _build(
        'stage1_bridge_final', 'Bridge Repair Budget',
        'A broken bridge needs a budget report before the expedition can cross.',
        'Each recovered token is worth 5 coins. Multiply amount by 5, then subtract 20 for tools.',
        lambda n: n * 5 - 20, 100, 50, ('Complete', 'Partial', 'Insufficient'), 'Budget',
        (14, 24, 23, 13, 4, 30), 600),
}


def get_final_assessment(challenge_id):
    # Import only when requested: the original authored challenge stays intact.
    from src.data.challenges import CHALLENGES
    source = CHALLENGES.get(challenge_id) if challenge_id == FINAL_COMPLETION_ID else NEW_ASSESSMENTS.get(challenge_id)
    if source is None:
        return None
    challenge = deepcopy(source)
    challenge.setdefault('time_limit', 480)
    if challenge_id == FINAL_COMPLETION_ID:
        for name, raw, rank in [('Rin', 80, 'Gold'), ('Ari', 79, 'Silver'), ('Lee', 64, 'Bronze')]:
            message = f'{name} - {rank}'
            challenge['hidden_tests'].append({
                'input_values': [name, str(raw)],
                'runtime_expected': {'score': raw + 10, 'rank': rank, 'message': message,
                                     'final_message': message.upper()},
                'expected_output_last_line': message.upper(),
            })
    for case in challenge.get('hidden_tests', []):
        case.setdefault('expected_output_last_line', case.get('runtime_expected', {}).get('final_message'))
    return challenge
