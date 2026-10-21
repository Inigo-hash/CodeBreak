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
    "lesson": """ITERATIVE STRUCTURES (LOOPS) — INTERMEDIATE

Loops repeat work without duplicating code. For each problem, implement the
named function and RETURN the requested result. Do not print the answer.
The checker calls your function with several inputs, including edge cases.

FOR LOOPS AND ACCUMULATORS
Use for to visit each item in a sequence. Initialize the accumulator before
the loop. An empty sequence should return the correct starting value.

NESTED LOOPS
The inner loop runs once for each item in the current outer-loop item. For a
grid represented as a list of rows, process every value in every row. Rows may
be empty, and negative values still count as values.

WHILE, BREAK, AND CONTINUE
A while loop repeats while its condition is true. Update the loop state so it
can finish. break exits the nearest loop; continue skips only the current
iteration. Check a stop marker before adding it to the result.

INTERMEDIATE CHECKLIST
- Handle empty input and empty rows.
- Put accumulator updates at the correct indentation level.
- Preserve the supplied input collections.
- Do not confuse skipping an item with ending the loop.
""",
}

LISTS_STAGE2_TOPIC = {
    "id": "lists_lesson",
    "title": "Lists",
    "difficulty": "Intermediate",
    "requirements": ["control_flow_lesson"],
    "challenge_id": LISTS_CHALLENGE_IDS[0],
    "challenge_ids": LISTS_CHALLENGE_IDS,
    "lesson": """LISTS — INTERMEDIATE

Lists are ordered, mutable collections. Indexing starts at zero, and negative
indices count from the end. An empty list has no first or last element, so
check it before indexing.

MUTATION AND RETURN VALUES
append(value) changes the list and returns None. remove(value) removes only
the first matching value and raises ValueError if the value is absent. pop()
removes and returns the final item; it raises IndexError if the list is empty.

SAFE COLLECTION PROCESSING
Copy a supplied list with list(items) when the task asks you to modify a copy.
Duplicates are meaningful: remove() removes one matching occurrence, not all.
Follow the exact requested operation order and return the specified tuple.

INTERMEDIATE CHECKLIST
- Handle empty lists, duplicates, and missing values.
- Preserve the caller's original list.
- Distinguish a popped value from the remaining list.
- Return data rather than printing it.
""",
}

ITERATIVE_CHALLENGES = {
    ITERATIVE_CHALLENGE_IDS[0]: {
        "id": ITERATIVE_CHALLENGE_IDS[0],
        "title": "Audit the Supply Shipment",
        "difficulty": "Intermediate",
        "type": "iterative_structure",
        "function_name": "sum_usable_supplies",
        "learning_constructs": ["for"],
        "problem": "Write sum_usable_supplies(amounts). Return the sum of all positive integer amounts. Ignore zero and negative amounts. Return 0 for an empty list. Example: [4, 0, -3, 7] returns 11. Do not change amounts.",
        "objective": "Use a for loop and an accumulator to sum only positive amounts.",
        "starter_code": "def sum_usable_supplies(amounts):\n    # Start a total before the loop.\n    # Add only positive amounts, then return the total.\n    pass",
        "hints": ["Initialize total to 0 before the loop.", "Visit each amount with for.", "Only add an amount when it is greater than zero.", "Return total after the loop."],
        "function_cases": [
            {"args": [[]], "expected": 0},
            {"args": [[4, 0, -3, 7]], "expected": 11},
            {"args": [[-8, -1, 0]], "expected": 0},
            {"args": [[5, 5, 2]], "expected": 12},
            {"args": [[1]], "expected": 1},
        ],
        "preserve_args": True,
    },
    ITERATIVE_CHALLENGE_IDS[1]: {
        "id": ITERATIVE_CHALLENGE_IDS[1],
        "title": "Count Relics Across the Grid",
        "difficulty": "Intermediate",
        "type": "iterative_structure",
        "function_name": "count_grid_relics",
        "learning_constructs": ["nested_for"],
        "problem": "Write count_grid_relics(grid). grid is a list of rows. Return how many values across all rows are nonzero. Empty grids and empty rows are allowed. Example: [[1, 0], [], [-2, 3]] returns 3. Do not change grid.",
        "objective": "Use nested for loops to inspect every cell and count nonzero values.",
        "starter_code": "def count_grid_relics(grid):\n    # Visit each row, then each value in that row.\n    # Count nonzero values and return the count.\n    pass",
        "hints": ["Initialize count before both loops.", "The outer loop visits rows; the inner loop visits values.", "Increment only when a value is not zero.", "Return count after both loops finish."],
        "function_cases": [
            {"args": [[]], "expected": 0},
            {"args": [[[], []]], "expected": 0},
            {"args": [[[1, 0], [], [-2, 3]]], "expected": 3},
            {"args": [[[0, 0], [0]]], "expected": 0},
            {"args": [[[4, -4, 2]]], "expected": 3},
        ],
        "preserve_args": True,
    },
    ITERATIVE_CHALLENGE_IDS[2]: {
        "id": ITERATIVE_CHALLENGE_IDS[2],
        "title": "Process Orders Until Cancelled",
        "difficulty": "Intermediate",
        "type": "iterative_structure",
        "function_name": "accepted_order_total",
        "learning_constructs": ["while", "break", "continue"],
        "problem": "Write accepted_order_total(orders). Process values from left to right. Stop immediately at the first value None. Skip zero and negative values. Return the sum of positive values before the stop marker. If None is first or orders is empty, return 0. Example: [5, 0, 3, None, 9] returns 8.",
        "objective": "Use while, continue to skip nonpositive values, and break at the None stop marker.",
        "starter_code": "def accepted_order_total(orders):\n    # Track the current index and total.\n    # Break at None; continue past nonpositive values.\n    pass",
        "hints": ["Use an index and a while condition that checks the list length.", "Read the current value before changing the index.", "If the value is None, break before adding it.", "For zero or negative values, advance the index before continue."],
        "function_cases": [
            {"args": [[]], "expected": 0},
            {"args": [[None, 4]], "expected": 0},
            {"args": [[5, 0, 3, None, 9]], "expected": 8},
            {"args": [[-2, 6, -1, 4]], "expected": 10},
            {"args": [[1, 2, 3]], "expected": 6},
        ],
        "preserve_args": True,
    },
}

LISTS_STAGE2_CHALLENGES = {
    LISTS_CHALLENGE_IDS[0]: {
        "id": LISTS_CHALLENGE_IDS[0],
        "title": "Report the Archive List",
        "difficulty": "Intermediate",
        "type": "lists",
        "function_name": "list_report",
        "required_list_operations": ["len"],
        "problem": "Write list_report(items). Return (first, last, count). If items is empty, return (None, None, 0). Do not modify items. Example: ['ink', 'paper', 'ink'] returns ('ink', 'ink', 3).",
        "objective": "Safely report both endpoints and the list length.",
        "starter_code": "def list_report(items):\n    # Handle an empty list before indexing.\n    # Return (first, last, count).\n    pass",
        "hints": ["Check if not items before using an index.", "For a nonempty list, use items[0] and items[-1].", "Use len(items) for count.", "Return a tuple containing all three values."],
        "function_cases": [
            {"args": [[]], "expected": (None, None, 0)},
            {"args": [["seal"]], "expected": ("seal", "seal", 1)},
            {"args": [["ink", "paper", "ink"]], "expected": ("ink", "ink", 3)},
            {"args": [[0, False, 0]], "expected": (0, 0, 3)},
            {"args": [[""]], "expected": ("", "", 1)},
        ],
        "preserve_args": True,
    },
    LISTS_CHALLENGE_IDS[1]: {
        "id": LISTS_CHALLENGE_IDS[1],
        "title": "Update the Archive Inventory",
        "difficulty": "Intermediate",
        "type": "lists",
        "function_name": "update_archive",
        "required_list_operations": ["append", "remove", "pop"],
        "problem": "Write update_archive(items, added, removed). Copy items, append added, remove the first occurrence of removed only if it exists, then pop the last item if the copy is nonempty. Return (remaining_items, popped_item). Use None for popped_item only when the copy is empty before pop. Leave items unchanged. Example: (['map', 'key'], 'scroll', 'map') returns (['key'], 'scroll').",
        "objective": "Copy a list, append, conditionally remove one matching value, and pop safely in the required order.",
        "starter_code": "def update_archive(items, added, removed):\n    # Work on a copy, not items.\n    # Follow the operation order in the instructions.\n    # Return (remaining_items, popped_item).\n    pass",
        "hints": ["Make a copy with list(items).", "Append added before checking for removed.", "Check membership before remove() so a missing value is safe.", "Set popped_item to None, then pop only if the copied list is nonempty."],
        "function_cases": [
            {"args": [[], "key", "missing"], "expected": ([], "key")},
            {"args": [[], "key", "key"], "expected": ([], None)},
            {"args": [["map", "key"], "scroll", "map"], "expected": (["key"], "scroll")},
            {"args": [["key"], "scroll", "missing"], "expected": (["key"], "scroll")},
            {"args": [["key", "map", "key"], "scroll", "key"], "expected": (["map", "key"], "scroll")},
            {"args": [["map", "key"], "scroll", "scroll"], "expected": (["map"], "key")},
        ],
        "preserve_args": True,
    },
}
