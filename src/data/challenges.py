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

        "runtime_expected": {"age": 18},

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
            "value": 18,
        },
    },

    # =========================================================
    # Print
    # =========================================================

    "print_001": {

        "expected_output": "Hello, World!",

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
            "value": "Hello, World!",
        },
    },

    # =========================================================
    # Python Syntax Basics
    # =========================================================

    "python_syntax_basics_001": {

        "expected_output": "Hello, Explorer!",

        "id": "python_syntax_basics_001",

        "title": "Python Syntax Basics",

        "difficulty": "Beginner",

        # Reuses the existing PrintValidator.
        "type": "print",

        "problem": """
Use Python's print() function to display:

Hello, Explorer!
        """,

        "objective":
            'Display the message "Hello, Explorer!" using print().',

        "requirements": [],

        "expected": {
            "value": "Hello, Explorer!",
        },
    },

    # =========================================================
    # Data Types
    # =========================================================

    "data_types_001": {

        "runtime_expected": {
            "age": 18,
            "height": 1.75,
            "name": "Alex",
            "is_ready": True,
        },

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
                "value": 18,
            },

            "height": {
                "type": "float",
                "value": 1.75,
            },

            "name": {
                "type": "str",
                "value": "Alex",
            },

            "is_ready": {
                "type": "bool",
                "value": True,
            },
        },
    },

    # =========================================================
    # Type Casting
    # =========================================================

    "type_casting_001": {

        "runtime_expected": {
            "age_text": "18",
            "age": 18,
        },

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
            "function": "int",
        },
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
            "Alex",
        ],

        "hidden_tests": [
            {
                "input_values": ["Maria"],
                "runtime_expected": {
                    "name": "Maria",
                },
            },
            {
                "input_values": ["John"],
                "runtime_expected": {
                    "name": "John",
                },
            },
            {
                "input_values": ["CodeBreaker"],
                "runtime_expected": {
                    "name": "CodeBreaker",
                },
            },
        ],

        "expected": {
            "target": "name",
            "prompt": "Enter your name: ",
        },
    },

    # =========================================================
    # Formatted Output
    # =========================================================

    "formatted_output_001": {

        "runtime_expected": {
            "name": "Alex",
        },

        "expected_output": "Welcome, Alex!",

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
            "suffix": "!",
        },
    },

    # =========================================================
    # Operators
    # =========================================================

    "operators_lesson_001": {

        "id": "operators_lesson_001",

        "title": "Operators",

        "difficulty": "Beginner",

        "type": "operator",

        "problem": (
            "Create a variable named score with the value 5. "
            "Use += to add 3 to score. Then create passed by checking "
            "if score is greater than or equal to 8."
        ),

        "objective": (
            "Use an assignment operator and a comparison operator."
        ),

        "requirements": [],

        "hints": [
            "Start by creating score and assigning it the value 5.",
            "Use += to increase the current value of score by 3.",
            "Create a Boolean variable named passed by comparing score with 8.",
            "Use this shape: passed = score >= 8.",
        ],

        "expected": {
            "target": "score",
            "start_value": 5,
            "operator": "add_assign",
            "update_value": 3,
            "final_value": 8,
            "comparison_target": "passed",
            "comparison_operator": "gte",
            "comparison_value": 8,
            "comparison_result": True,
        },

        "runtime_expected": {
            "score": 8,
            "passed": True,
        },
    },

    # =========================================================
    # Strings
    # =========================================================

    "strings_lesson_001": {

        "id": "strings_lesson_001",

        "title": "Strings",

        "difficulty": "Beginner",

        "type": "string",

        "problem": (
            'Create a variable named game_name with the value "CodeBreak". '
            'Create message using "Welcome to\\n" + game_name. '
            'Then create result by converting message to uppercase '
            'using .upper().'
        ),

        "objective": (
            "Use string handling, a newline escape sequence, "
            "and the .upper() string method."
        ),

        "requirements": [],

        "hints": [
            'Start by creating game_name with the value "CodeBreak".',
            r'Use "Welcome to\n" + game_name to create message.',
            "Call the .upper() method on message.",
            "Store the uppercase result using: result = message.upper().",
        ],

        "expected": {
            "name_target": "game_name",
            "name_value": "CodeBreak",
            "message_target": "message",
            "prefix": "Welcome to\n",
            "result_target": "result",
            "method": "upper",
            "result": "WELCOME TO\nCODEBREAK",
        },

        "runtime_expected": {
            "game_name": "CodeBreak",
            "message": "Welcome to\nCodeBreak",
            "result": "WELCOME TO\nCODEBREAK",
        },
    },

    # =========================================================
    # Control Flow
    # =========================================================

    "control_flow_lesson_001": {

        "id": "control_flow_lesson_001",

        "title": "Control Flow",

        "difficulty": "Beginner",

        "type": "control_flow",

        "problem": (
            "Set score to 85 and has_key to True. "
            "Create rank using an if/elif/else statement: "
            "'Gold' when score >= 90, 'Silver' when score >= 75, "
            "and 'Bronze' otherwise. Then create can_enter using "
            "has_key and score >= 75."
        ),

        "objective": (
            "Use if/elif/else and boolean logic."
        ),

        "requirements": [],

        "hints": [
            "Create score = 85 and has_key = True first.",
            "Use if, elif, and else to assign Gold, Silver, or Bronze to rank.",
            "The first condition checks score >= 90 and the elif checks score >= 75.",
            "After the decision, create can_enter using: has_key and score >= 75.",
        ],

        "expected": {
            "score_target": "score",
            "score_value": 85,
            "key_target": "has_key",
            "key_value": True,
            "rank_target": "rank",

            "branches": [
                {
                    "operator": "gte",
                    "value": 90,
                    "result": "Gold",
                },
                {
                    "operator": "gte",
                    "value": 75,
                    "result": "Silver",
                },
            ],

            "else_result": "Bronze",

            "boolean_target": "can_enter",
            "boolean_variable": "has_key",
            "boolean_operator": "and",
            "comparison_operator": "gte",
            "comparison_value": 75,
            "boolean_result": True,
        },

        "runtime_expected": {
            "score": 85,
            "has_key": True,
            "rank": "Silver",
            "can_enter": True,
        },
    },

    # =========================================================
    # Stage 1 Final Challenge
    # =========================================================

    "stage1_final_001": {

        "id": "stage1_final_001",

        "title": "Corrupted Core Final Challenge",

        "difficulty": "Beginner Final",

        "type": "stage1_final",

        "problem": """
The Corrupted Core has been defeated,
but the castle gate still needs one final program.

1. Ask the player:

Enter explorer name:

Store the answer in:

name

2. Ask:

Enter score:

Store the text in:

score_text

3. Convert score_text to an integer
and store it in:

score

4. Add 10 to score using +=

5. Create rank using:

Gold if score >= 90
Silver if score >= 75
Bronze otherwise

6. Create this formatted message:

{name} - {rank}

Store it in:

message

7. Convert message to uppercase
and store it in:

final_message

8. Print final_message.
        """,

        "objective":
            "Use all Stage 1 concepts to unlock the castle gate.",

        "requirements": [],

        "test_inputs": [
            "Alex",
            "70",
        ],

        "hidden_tests": [
            {
                "input_values": ["Mika", "85"],
                "runtime_expected": {
                    "score": 95,
                    "rank": "Gold",
                    "message": "Mika - Gold",
                    "final_message": "MIKA - GOLD",
                },
            },
            {
                "input_values": ["Luna", "65"],
                "runtime_expected": {
                    "score": 75,
                    "rank": "Silver",
                    "message": "Luna - Silver",
                    "final_message": "LUNA - SILVER",
                },
            },
            {
                "input_values": ["Kai", "40"],
                "runtime_expected": {
                    "score": 50,
                    "rank": "Bronze",
                    "message": "Kai - Bronze",
                    "final_message": "KAI - BRONZE",
                },
            },
        ],
    },
}


def get_challenge(challenge_id):
    """
    Return a coding challenge by id.

    Returns None if the challenge does not exist.
    """

    return CHALLENGES.get(challenge_id)