#challenges.py
"""
All coding challenges for the game.

Each challenge is pure data.

No validation logic belongs here.
"""


CHALLENGES = {

    # =========================================================
    # Variables
    # =========================================================

    "variables_001": {

        "id": "variables_001",

        "title": "Variables",

        "difficulty": "Beginner",

        "type": "variable",

        "problem": """
Create a variable named age
and assign the value 18.
        """,

        "objective":
            "Create a variable named age and assign it the value 18.",

        "requirements": [],

        "expected": {
            "name": "age",
            "value": 18
        }
    },


    # =========================================================
    # Print
    # =========================================================

    "print_001": {

        "id": "print_001",

        "title": "Say Hello",

        "difficulty": "Beginner",

        "type": "print",

        "problem": """
Use print() to display:

Hello, World!
        """,

        "objective":
            "Use print() to display: Hello, World!",

        "requirements": [],

        "expected": {
            "value": "Hello, World!"
        }
    },


    # =========================================================
    # Python Syntax Basics
    # =========================================================

    "python_syntax_basics_001": {

        "id": "python_syntax_basics_001",

        "title": "Python Syntax Basics",

        "difficulty": "Beginner",

        # We can reuse your existing PrintValidator.
        "type": "print",

        "problem": """
Use Python's print() function to display:

Hello, Explorer!
        """,

        "objective":
            'Display the message "Hello, Explorer!" using print().',

        "requirements": [],

        "expected": {
            "value": "Hello, Explorer!"
        }
    },


    # =========================================================
    # Data Types
    # =========================================================

    "data_types_001": {

        "id": "data_types_001",

        "title": "Data Types",

        "difficulty": "Beginner",

        "type": "data_type",

        "problem": """
Create these four variables:

age = 18

height = 1.75

name = "Alex"

is_ready = True
        """,

        "objective":
            "Create variables containing an int, float, string, and boolean.",

        "requirements": [],

        "expected": {

            "age": {
                "type": "int",
                "value": 18
            },

            "height": {
                "type": "float",
                "value": 1.75
            },

            "name": {
                "type": "str",
                "value": "Alex"
            },

            "is_ready": {
                "type": "bool",
                "value": True
            }
        }
    },


    # =========================================================
    # Type Casting
    # =========================================================

    "type_casting_001": {

        "id": "type_casting_001",

        "title": "Type Casting",

        "difficulty": "Beginner",

        "type": "type_casting",

        "problem": """
Create a variable:

age_text = "18"

Then convert age_text into an integer
and store the result inside a variable named:

age
        """,

        "objective":
            "Convert age_text into an integer using int() and store it in age.",

        "requirements": [],

        "expected": {
            "source": "age_text",
            "source_value": "18",
            "target": "age",
            "function": "int"
        }
    },
    # =========================================================
    # Input
    # =========================================================

    "input_lesson_001": {

        "id": "input_lesson_001",

        "title": "User Input",

        "difficulty": "Beginner",

        "type": "input",

        "problem": """
Use input() to ask the user:

Enter your name:

Store the user's answer inside
a variable named:

name

The coding environment will use:

Alex

as the test input.
        """,

        "objective":
            "Use input() to store the user's name inside a variable named name.",

        "requirements": [],

        "test_inputs": [
            "Alex"
        ],

        "expected": {
            "target": "name",
            "prompt": "Enter your name: "
        }
    },


    # =========================================================
    # Formatted Output
    # =========================================================

    "formatted_output_001": {

        "id": "formatted_output_001",

        "title": "Formatted Output",

        "difficulty": "Beginner",

        "type": "formatted_output",

        "problem": """
Create this variable:

name = "Alex"

Then use an f-string to display:

Welcome, Alex!
        """,

        "objective":
            'Use an f-string to display "Welcome, Alex!" using the name variable.',

        "requirements": [],

        "expected": {
            "variable": "name",
            "value": "Alex",
            "prefix": "Welcome, ",
            "suffix": "!"
        }
    },


    # =========================================================
    # Operators
    # =========================================================

    "operators_001": {
        "id": "operators_001",
        "title": "Arithmetic Operators",
        "difficulty": "Beginner",
        "type": "operator",
        "problem": "Store the result of 12 + 8 inside a variable named total.",
        "objective": "Create total using the + operator with 12 and 8.",
        "requirements": [],
        "expected": {
            "target": "total", "operator": "add",
            "left": 12, "right": 8, "value": 20,
        },
    },


    # =========================================================
    # String Basics
    # =========================================================

    "string_basics_001": {
        "id": "string_basics_001",
        "title": "String Basics",
        "difficulty": "Beginner",
        "type": "string",
        "problem": (
            'Join "Code" and " Breaker" with + and store the result '
            "inside a variable named title."
        ),
        "objective": "Create title by joining the two quoted strings.",
        "requirements": [],
        "expected": {
            "target": "title",
            "parts": ["Code", " Breaker"],
            "value": "Code Breaker",
        },
    },


    # =========================================================
    # If / Elif / Else
    # =========================================================

    "conditionals_001": {
        "id": "conditionals_001",
        "title": "If, Elif, and Else",
        "difficulty": "Beginner",
        "type": "conditional",
        "problem": (
            "Set score to 85. Set rank to 'Gold' when score >= 90, "
            "'Silver' when score >= 75, and 'Bronze' otherwise."
        ),
        "objective": "Use a complete if/elif/else chain to assign rank.",
        "requirements": [],
        "expected": {
            "source": "score",
            "source_value": 85,
            "target": "rank",
            "branches": [
                {"operator": "gte", "value": 90, "result": "Gold"},
                {"operator": "gte", "value": 75, "result": "Silver"},
            ],
            "else_result": "Bronze",
        },
    },


    # =========================================================
    # Boolean Logic
    # =========================================================

    "boolean_logic_001": {
        "id": "boolean_logic_001",
        "title": "Boolean Logic",
        "difficulty": "Beginner",
        "type": "boolean_logic",
        "problem": (
            "Set has_key to True and gate_locked to False. Then create "
            "can_enter using has_key and not gate_locked."
        ),
        "objective": "Combine boolean variables using and and not.",
        "requirements": [],
        "expected": {
            "variables": {"has_key": True, "gate_locked": False},
            "target": "can_enter",
            "plain": "has_key",
            "negated": "gate_locked",
        },
    },

}


def get_challenge(challenge_id):
    """
    Return a coding challenge by id.

    Returns None if the challenge does not exist.
    """

    return CHALLENGES.get(challenge_id)
