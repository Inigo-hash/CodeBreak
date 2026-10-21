"""Small, labelled reference answers; never executes or solves player code.

Only whole, recognized questions match. Everything else stays on the AI path.
Keep game facts tied to authored controls rather than an independent key list.
"""
import re

GUIDE_LABEL = 'Built-in guide: '


def built_in_answer(question):
    text = re.sub(r'\s+', ' ', question.strip().lower()).strip(' ?!.')
    definitions = {
        'python': 'Python is a programming language used to write instructions for a computer. CodeBreak teaches it through coding challenges. For example, print("Hello") displays Hello.',
        'a variable': 'A variable is a name that refers to a value. For example, score = 10 stores the value 10 under the name score.',
        'a list': 'A list is an ordered collection you can change. For example, items = ["key", "torch"]. Index 0 selects the first item; index -1 selects the last.',
        'a for loop': 'A for loop repeats code for each item in a collection. For example, for item in items: visits each item. Indent the code you want repeated.',
        'a while loop': 'A while loop repeats while its condition is true. Make sure something changes so the condition can eventually become false.',
        'a function': 'A function is a reusable block defined with def. Parameters receive inputs, and return sends a result back to the caller.',
        'a dictionary': 'A dictionary stores key-value pairs. For example, supplies = {"torches": 3}; supplies["torches"] reads the value 3.',
        'a tuple': 'A tuple is an ordered collection whose entries cannot be changed after creation. For example, position = (2, 4). You can read its entries with indexing.',
    }
    if text in ('who is python', 'ano ang python', 'ano yung python'):
        return GUIDE_LABEL + definitions['python']
    for subject, answer in definitions.items():
        if text in (f'what is {subject}', f"what's {subject}"):
            return GUIDE_LABEL + answer
    if text in ('what is codebreak', "what's codebreak"):
        return GUIDE_LABEL + 'CodeBreak is a desktop game for learning Python through exploration, coding challenges and combat with Filipino folklore creatures. Read lessons, solve challenges and follow your stage objectives.'
    if text in ('how to play the game', 'how do i play the game', 'how to play codebreak', 'how do i play codebreak'):
        return GUIDE_LABEL + ('Explore, search objects, read lessons and solve coding challenges. Open I for the stage manual and O for objectives. Open B, drag the sword to a hotbar slot and select it before fighting. Save from the pause menu.')
    if text in ('what are the controls', 'what are the game controls', 'how do i move', 'how to move'):
        from src.data.controls import CONTROL_SECTIONS
        movement = next(rows for title, rows in CONTROL_SECTIONS if title == 'MOVING AND FIGHTING')
        return GUIDE_LABEL + '; '.join(f'{key}: {action}' for key, action in movement) + '. Open I for the stage manual and full controls.'
    if text in ('how do i equip the sword', 'how to equip the sword', 'how do i attack'):
        from src.data.controls import CONTROL_NOTES
        return GUIDE_LABEL + ' '.join(CONTROL_NOTES[:2])
    if text in ('how do i save', 'how to save the game'):
        return GUIDE_LABEL + 'Press Escape to pause, then choose Save Game. Use the same save slot when you continue your adventure.'
    return None
