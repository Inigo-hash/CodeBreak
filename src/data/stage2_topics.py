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
}


FUNCTIONS_CHALLENGE_IDS = (
    "functions_lesson_greet_001",
    "functions_lesson_total_001",
)
TUPLES_CHALLENGE_IDS = (
    "tuples_lesson_coordinates_001",
    "tuples_lesson_distance_001",
)
ERROR_HANDLING_CHALLENGE_IDS = (
    "error_handling_lesson_safe_int_001",
    "error_handling_lesson_safe_divide_001",
)

FUNCTIONS_TOPIC = {
    "id": "functions_lesson",
    "title": "Functions",
    "difficulty": "Beginner",
    "requirements": ["lists_lesson"],
    "challenge_id": FUNCTIONS_CHALLENGE_IDS[0],
    "challenge_ids": FUNCTIONS_CHALLENGE_IDS,
    "lesson": """FUNCTIONS — BEGINNER

A function is a named block of code you can call when you need it.
Use def to define a function. Indent its body.

1. DEFINE AND CALL A FUNCTION
    def greet():
        print("Hello!")

    greet()  # prints Hello!

2. PARAMETERS: give a function information to use.
    def greet_person(name):
        print("Hello, " + name)

    greet_person("Alex")  # prints Hello, Alex

3. RETURN VALUES: send a result back to the code that called the function.
    def add(a, b):
        return a + b

    result = add(3, 4)
    print(result)  # 7

4. PARAMETERS CAN BE NUMBERS OR TEXT
    def double(number):
        return number * 2

    print(double(5))  # 10

5. RETURN VS PRINT
- print() displays something on screen.
- return gives a value back so other code can use it.
- Code after return in that function does not run.

COMMON MISTAKES
- Remember the colon after the def line.
- Indent the function body.
- Use parentheses when calling a function.
- Return a value when the task asks for a result.""",
}

TUPLES_TOPIC = {
    "id": "tuples_lesson",
    "title": "Tuples",
    "difficulty": "Beginner",
    "requirements": ["functions_lesson"],
    "challenge_id": TUPLES_CHALLENGE_IDS[0],
    "challenge_ids": TUPLES_CHALLENGE_IDS,
    "lesson": """TUPLES — BEGINNER

A tuple stores multiple values in order. Unlike a list, a tuple cannot be changed after it is created.

1. CREATE A TUPLE
    coordinates = (10, 20)
    point = ("north", 5)

2. ACCESS ITEMS: indexes start at 0.
    coordinates = (10, 20)
    print(coordinates[0])  # 10
    print(coordinates[1])  # 20

3. UNPACK A TUPLE: assign its values to separate variables.
    coordinates = (10, 20)
    x, y = coordinates
    print(x)  # 10
    print(y)  # 20

4. RETURN A TUPLE FROM A FUNCTION
    def make_point(x, y):
        return (x, y)

    point = make_point(3, 7)
    print(point)  # (3, 7)

5. ONE-ITEM TUPLES need a comma.
    single_value = (5,)

REMEMBER
- Tuples keep their order.
- Use parentheses to create a tuple.
- Indexing starts at 0.
- You can read tuple items, but cannot assign a new value to an index.
- A function can return several related values in one tuple.""",
}

ERROR_HANDLING_TOPIC = {
    "id": "error_handling_lesson",
    "title": "Error Handling",
    "difficulty": "Beginner",
    "requirements": ["tuples_lesson"],
    "challenge_id": ERROR_HANDLING_CHALLENGE_IDS[0],
    "challenge_ids": ERROR_HANDLING_CHALLENGE_IDS,
    "lesson": """ERROR HANDLING — BEGINNER

An error can happen while a program runs. try/except lets the program respond instead of stopping unexpectedly.

1. HANDLE INVALID NUMBER INPUT
    text = "12"
    try:
        number = int(text)
        print(number)
    except ValueError:
        print("Please enter a whole number")

2. TRY RUNS CODE THAT MAY FAIL
Put the risky operation inside the try block.

    text = "hello"
    try:
        number = int(text)
    except ValueError:
        number = 0
    print(number)  # 0

3. HANDLE DIVISION BY ZERO
    try:
        answer = 10 / 0
    except ZeroDivisionError:
        answer = None
    print(answer)  # None

4. KEEP EXCEPTIONS SPECIFIC
- ValueError can happen when text cannot be converted to a number.
- ZeroDivisionError happens when dividing by zero.
- Put except after the matching try block.
- Indent the code inside try and except.

REMEMBER
Handle only errors you expect. A useful except block gives the program a clear fallback result.""",
}

FUNCTIONS_CHALLENGES = {
    FUNCTIONS_CHALLENGE_IDS[0]: {
        "id": FUNCTIONS_CHALLENGE_IDS[0],
        "title": "Greet the Explorer",
        "difficulty": "Beginner",
        "type": "function",
        "function_name": "greet_explorer",
        "problem": "Write greet_explorer(name). Return the text \"Hello, \" followed by name. Example: greet_explorer(\"Alex\") returns \"Hello, Alex\".",
        "objective": "Define a function with one parameter and return a string.",
        "starter_code": "def greet_explorer(name):\n    # Return a greeting that includes name.\n    pass",
        "hints": ["The parameter name contains the text to greet.", "Join strings with +.", "Return the result instead of printing it."],
        "function_cases": [{"args": ["Alex"], "expected": "Hello, Alex"}, {"args": ["Sam"], "expected": "Hello, Sam"}, {"args": [""], "expected": "Hello, "}]
    },
    FUNCTIONS_CHALLENGE_IDS[1]: {
        "id": FUNCTIONS_CHALLENGE_IDS[1],
        "title": "Add Two Supplies",
        "difficulty": "Beginner",
        "type": "function",
        "function_name": "add_supplies",
        "problem": "Write add_supplies(first, second). Return the sum of the two numbers. Example: add_supplies(3, 4) returns 7.",
        "objective": "Use two parameters and return their sum.",
        "starter_code": "def add_supplies(first, second):\n    # Add the two values and return the result.\n    pass",
        "hints": ["The values are provided through first and second.", "Use the + operator.", "Return first + second."],
        "function_cases": [{"args": [0, 0], "expected": 0}, {"args": [3, 4], "expected": 7}, {"args": [-2, 5], "expected": 3}]
    }
}

TUPLES_CHALLENGES = {
    TUPLES_CHALLENGE_IDS[0]: {
        "id": TUPLES_CHALLENGE_IDS[0],
        "title": "Pack a Coordinate",
        "difficulty": "Beginner",
        "type": "function",
        "function_name": "make_coordinates",
        "problem": "Write make_coordinates(x, y). Return both values together as a tuple (x, y). Example: make_coordinates(3, 7) returns (3, 7).",
        "objective": "Return two related values together in a tuple.",
        "starter_code": "def make_coordinates(x, y):\n    # Return x and y together as a tuple.\n    pass",
        "hints": ["Tuples use parentheses.", "Put x first and y second.", "Return (x, y)."],
        "function_cases": [{"args": [0, 0], "expected": (0, 0)}, {"args": [3, 7], "expected": (3, 7)}, {"args": [-1, 4], "expected": (-1, 4)}]
    },
    TUPLES_CHALLENGE_IDS[1]: {
        "id": TUPLES_CHALLENGE_IDS[1],
        "title": "Read a Coordinate",
        "difficulty": "Beginner",
        "type": "function",
        "function_name": "get_x_coordinate",
        "problem": "Write get_x_coordinate(point). The point is a two-item tuple. Return its first value. Example: get_x_coordinate((8, 2)) returns 8.",
        "objective": "Read a tuple item using index 0.",
        "starter_code": "def get_x_coordinate(point):\n    # Return the first item in point.\n    pass",
        "hints": ["Tuple indexes start at 0.", "Use point[0].", "Return that value."],
        "function_cases": [{"args": [[0, 0]], "expected": 0}, {"args": [[8, 2]], "expected": 8}, {"args": [[-3, 9]], "expected": -3}]
    }
}

ERROR_HANDLING_CHALLENGES = {
    ERROR_HANDLING_CHALLENGE_IDS[0]: {
        "id": ERROR_HANDLING_CHALLENGE_IDS[0],
        "title": "Read a Safe Number",
        "difficulty": "Beginner",
        "type": "function",
        "learning_construct": "exceptions",
        "function_name": "safe_number",
        "problem": "Write safe_number(text). Try converting text to an integer. Return the number if it works, or None if a ValueError happens. Example: safe_number(\"12\") returns 12 and safe_number(\"oops\") returns None.",
        "objective": "Use try/except ValueError to handle invalid number text.",
        "starter_code": "def safe_number(text):\n    try:\n        # Try converting text to an integer.\n        pass\n    except ValueError:\n        # Return None if conversion fails.\n        pass",
        "hints": ["Put int(text) inside try.", "Return the converted number inside try.", "In except ValueError, return None."],
        "function_cases": [{"args": ["12"], "expected": 12}, {"args": ["0"], "expected": 0}, {"args": ["oops"], "expected": None}, {"args": [""], "expected": None}]
    },
    ERROR_HANDLING_CHALLENGE_IDS[1]: {
        "id": ERROR_HANDLING_CHALLENGE_IDS[1],
        "title": "Divide Safely",
        "difficulty": "Beginner",
        "type": "function",
        "learning_construct": "exceptions",
        "function_name": "safe_divide",
        "problem": "Write safe_divide(first, second). Return first / second. If second is 0, catch ZeroDivisionError and return None. Example: safe_divide(8, 2) returns 4.0 and safe_divide(8, 0) returns None.",
        "objective": "Handle division by zero with try/except.",
        "starter_code": "def safe_divide(first, second):\n    try:\n        # Return first divided by second.\n        pass\n    except ZeroDivisionError:\n        # Return None when second is zero.\n        pass",
        "hints": ["Put first / second inside try.", "Return the division result.", "Catch ZeroDivisionError and return None."],
        "function_cases": [{"args": [8, 2], "expected": 4.0}, {"args": [9, 3], "expected": 3.0}, {"args": [8, 0], "expected": None}, {"args": [-6, 2], "expected": -3.0}]
    }
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
        "starter_code": "def sum_training_points(limit):\n    total = 0\n    # Loop from 1 through limit and add each number.\n    # Return total.\n    pass",
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
        "starter_code": "def count_training_tiles(rows, columns):\n    count = 0\n    # Loop through each row and each column.\n    # Add 1 for each tile, then return count.\n    pass",
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
        "starter_code": "def count_launch_numbers(start):\n    count = 0\n    number = start\n    # While number is positive, count it and subtract 1.\n    pass",
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
        "starter_code": "def list_report(items):\n    # If items is empty, return (None, 0).\n    # Otherwise return the first item and list length.\n    pass",
        "hints": ["Check if not items before indexing.", "Use items[0] for the first item.", "Use len(items) for the count.", "Return both values in a tuple."],
        "function_cases": [{"args": [[]], "expected": (None, 0)}, {"args": [["key"]], "expected": ("key", 1)}, {"args": [["key", "potion"]], "expected": ("key", 2)}, {"args": [[1, 2, 3]], "expected": (1, 3)}],
        "preserve_args": True
    },
    LISTS_CHALLENGE_IDS[1]: {
        "id": LISTS_CHALLENGE_IDS[1],
        "title": "Add an Item to the Inventory",
        "difficulty": "Beginner",
        "type": "lists",
        "function_name": "add_inventory_item",
        "required_list_operations": ["append"],
        "problem": "Write add_inventory_item(items, new_item). Make a copy of items, add new_item to the end of the copy, and return the copy. Do not change items. Example: add_inventory_item(['key'], 'potion') returns ['key', 'potion'].",
        "objective": "Copy a list, use append(), and return the updated copy.",
        "starter_code": "def add_inventory_item(items, new_item):\n    # Make a copy with list(items).\n    # Append new_item to the copy.\n    # Return the copy, leaving items unchanged.\n    pass",
        "hints": ["Create result = list(items).", "Use result.append(new_item).", "Return result.", "Do not append directly to items."],
        "function_cases": [{"args": [[], "key"], "expected": ["key"]}, {"args": [["key"], "potion"], "expected": ["key", "potion"]}, {"args": [["key", "map"], "shield"], "expected": ["key", "map", "shield"]}],
        "preserve_args": True
    },
}
