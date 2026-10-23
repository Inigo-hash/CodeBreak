"""Dedicated Stage 2 lessons and challenges.

This module is authored for the Intermediate stage and intentionally does not
import or modify the earlier third-party-authored Castle curriculum files.
Challenge data stays separate from validation logic.
"""

ITERATIVE_CHALLENGE_IDS = (
    "iterative_structure_lesson_for_001",
    "iterative_structure_lesson_nested_001",
    "iterative_structure_lesson_control_001",
)
LISTS_CHALLENGE_IDS = (
    "lists_lesson_report_001",
    "lists_lesson_update_001",
)

ITERATIVE_STRUCTURE_TOPIC = {
    "id": "iterative_structure_lesson",
    "title": "Iterative Structures (Loops)",
    "difficulty": "Intermediate",
    "requirements": ["control_flow_lesson"],
    "challenge_id": ITERATIVE_CHALLENGE_IDS[0],
    "challenge_ids": ITERATIVE_CHALLENGE_IDS,
    "lesson": """ITERATIVE STRUCTURES (LOOPS) — BEGINNER

Loops repeat code so you do not need to write the same instruction many times.
These examples use Stage 1 skills: variables, numbers, operators, and if.

FOR LOOPS: repeat over a range.
    for number in range(1, 4):
        print(number)  # prints 1, 2, 3
The ending value of range is not included.

ACCUMULATORS: set a total before the loop and update it inside.
    total = 0
    for number in range(1, 5):
        total = total + number
    print(total)  # 10

WHILE LOOPS: repeat while a condition is True. Update the counter.
    number = 3
    while number > 0:
        print(number)
        number = number - 1

NESTED LOOPS: an inner loop completes for each outer-loop repetition.
    for row in range(2):
        for column in range(3):
            print("*", end="")
        print()
This prints two rows of three stars.

BREAK: immediately ends the nearest loop.
    for number in range(1, 6):
        if number == 4:
            break
        print(number)  # 1, 2, 3

CONTINUE: skips the current repetition and moves to the next.
    for number in range(1, 6):
        if number % 2 == 0:
            continue
        print(number)  # 1, 3, 5

COMMON MISTAKES
- Set totals before the loop.
- Keep indentation consistent.
- range(1, 4) stops before 4.
- Change the counter in a while loop.
- break ends the loop; continue skips one repetition.
Run the examples to see their output.""",
}""",
}

LISTS_STAGE2_TOPIC = {
    "id": "lists_lesson",
    "title": "Lists",
    "difficulty": "Intermediate",
    "requirements": ["iterative_structure_lesson"],
    "challenge_id": LISTS_CHALLENGE_IDS[0],
    "challenge_ids": LISTS_CHALLENGE_IDS,
    "lesson": """LISTS — BEGINNER

A list stores multiple values in order. Lists can be changed after creation.

CREATING A LIST
    inventory = ["sword", "key", "potion"]
    empty_inventory = []

ACCESSING ITEMS: indexes start at 0; negative indexes count from the end.
    inventory = ["sword", "key", "potion"]
    print(inventory[0])   # sword
    print(inventory[-1])  # potion
Check the list is not empty before indexing.

FINDING LENGTH
    inventory = ["sword", "key", "potion"]
    print(len(inventory))  # 3

ADDING WITH append(): adds one item to the end.
    inventory = ["sword", "key"]
    inventory.append("shield")
    print(inventory)  # ['sword', 'key', 'shield']

REMOVING WITH remove(): removes the first matching value.
    inventory = ["key", "potion", "key"]
    if "key" in inventory:
        inventory.remove("key")
    print(inventory)  # ['potion', 'key']
Check membership if the value might be missing.

REMOVING AND GETTING WITH pop(): removes and returns the last item.
    inventory = ["sword", "potion"]
    item = inventory.pop()
    print(item)       # potion
    print(inventory)  # ['sword']
Only call pop() when the list is not empty.

LOOPING THROUGH A LIST
    inventory = ["sword", "key", "potion"]
    for item in inventory:
        print(item)

COPYING A LIST: make a copy before changing it if the original must stay same.
    original = ["sword", "key"]
    updated = list(original)
    updated.append("shield")
    print(original)  # ['sword', 'key']
    print(updated)   # ['sword', 'key', 'shield']

REMEMBER
- items[0] is the first item; items[-1] is the last.
- len(items) counts items.
- append(), remove(), and pop() change a list.
- remove() removes one match; pop() returns the removed item.
- Check for empty lists or missing values when needed.
- Returning a value is different from printing it.""",
}""",
}

ITERATIVE_CHALLENGES = {
    ITERATIVE_CHALLENGE_IDS[0]: {
        "id": ITERATIVE_CHALLENGE_IDS[0],
        "title": "Add the Training Points",
        "difficulty": "Beginner",
        "type": "iterative_structure",
        "function_name": "sum_training_points",
        "learning_constructs": ["for"],
        "problem": "Write sum_training_points(limit). Return the sum of whole numbers from 1 through limit. If limit is 0 or negative, return 0. Example: sum_training_points(4) returns 10.",
        "objective": "Use range(), a for loop, and a running total.",
        "starter_code": "def sum_training_points(limit):\\n    total = 0\\n    # Loop from 1 through limit and add each number.\\n    # Return total.\\n    pass",
        "hints": ["Start with total = 0.", "Use range(1, limit + 1).", "Add each number to total inside the loop.", "Return total after the loop."],
        "function_cases": [{"args": [0], "expected": 0}, {"args": [-3], "expected": 0}, {"args": [1], "expected": 1}, {"args": [4], "expected": 10}, {"args": [5], "expected": 15}]
    },
    ITERATIVE_CHALLENGE_IDS[1]: {
        "id": ITERATIVE_CHALLENGE_IDS[1],
        "title": "Build the Training Grid",
        "difficulty": "Beginner",
        "type": "iterative_structure",
        "function_name": "count_training_tiles",
        "learning_constructs": ["nested_for"],
        "problem": "Write count_training_tiles(rows, columns). Return the number of tiles in a grid with these dimensions. If either number is 0 or negative, return 0. Example: count_training_tiles(2, 3) returns 6. Use nested loops, not multiplication.",
        "objective": "Use one for loop inside another to count each grid tile.",
        "starter_code": "def count_training_tiles(rows, columns):\\n    count = 0\\n    # Loop through each row and each column.\\n    # Add 1 for each tile, then return count.\\n    pass",
        "hints": ["Set count = 0 before either loop.", "Use range(rows) for the outer loop.", "Inside it, use range(columns).", "Add 1 inside the inner loop."],
        "function_cases": [{"args": [0, 3], "expected": 0}, {"args": [2, 0], "expected": 0}, {"args": [1, 1], "expected": 1}, {"args": [2, 3], "expected": 6}, {"args": [3, 2], "expected": 6}]
    },
    ITERATIVE_CHALLENGE_IDS[2]: {
        "id": ITERATIVE_CHALLENGE_IDS[2],
        "title": "Count Down to Launch",
        "difficulty": "Beginner",
        "type": "iterative_structure",
        "function_name": "count_launch_numbers",
        "learning_constructs": ["while"],
        "problem": "Write count_launch_numbers(start). Return how many positive whole numbers are counted down from start to 1. If start is 0 or negative, return 0. Example: count_launch_numbers(3) returns 3. Use a while loop.",
        "objective": "Use a while loop and update the counter so the loop eventually stops.",
        "starter_code": "def count_launch_numbers(start):\\n    count = 0\\n    number = start\\n    # While number is positive, count it and subtract 1.\\n    pass",
        "hints": ["Use while number > 0.", "Increase count by 1 during each repetition.", "Decrease number by 1 during each repetition.", "Return count after the loop."],
        "function_cases": [{"args": [0], "expected": 0}, {"args": [-2], "expected": 0}, {"args": [1], "expected": 1}, {"args": [3], "expected": 3}, {"args": [5], "expected": 5}]
    },
}

LISTS_STAGE2_CHALLENGES = {
    LISTS_CHALLENGE_IDS[0]: {
        "id": LISTS_CHALLENGE_IDS[0],
        "title": "Read the Inventory",
        "difficulty": "Beginner",
        "type": "lists",
        "function_name": "list_report",
        "required_list_operations": ["len"],
        "problem": "Write list_report(items). Return (first, count). If items is empty, return (None, 0). Do not modify items. Example: list_report(['key', 'potion']) returns ('key', 2).",
        "objective": "Check for an empty list, then use index 0 and len().",
        "starter_code": "def list_report(items):\\n    # If items is empty, return (None, 0).\\n    # Otherwise return the first item and list length.\\n    pass",
        "hints": ["Check if not items before indexing.", "Use items[0] for the first item.", "Use len(items) for the count.", "Return both values in a tuple."],
        "function_cases": [{"args": [[]], "expected": (None, 0)}, {"args": [["key"]], "expected": ("key", 1)}, {"args": [["key", "potion"]], "expected": ("key", 2)}, {"args": [[1, 2, 3]], "expected": (1, 3)}],
        "preserve_args": True
    LISTS_CHALLENGE_IDS[1]: {
        "id": LISTS_CHALLENGE_IDS[1],
        "title": "Add an Item to the Inventory",
        "difficulty": "Beginner",
        "type": "lists",
        "function_name": "add_inventory_item",
        "required_list_operations": ["append"],
        "problem": "Write add_inventory_item(items, new_item). Make a copy of items, add new_item to the end of the copy, and return the copy. Do not change items. Example: add_inventory_item(['key'], 'potion') returns ['key', 'potion'].",
        "objective": "Copy a list, use append(), and return the updated copy.",
        "starter_code": "def add_inventory_item(items, new_item):\\n    # Make a copy with list(items).\\n    # Append new_item to the copy.\\n    # Return the copy, leaving items unchanged.\\n    pass",
        "hints": ["Create result = list(items).", "Use result.append(new_item).", "Return result.", "Do not append directly to items."],
        "function_cases": [{"args": [[], "key"], "expected": ["key"]}, {"args": [["key"], "potion"], "expected": ["key", "potion"]}, {"args": [["key", "map"], "shield"], "expected": ["key", "map", "shield"]}],
        "preserve_args": True

}
