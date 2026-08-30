"""
topics.py

Learning topic data for CodeBreak.

Tiled stores a topic_id on searchable objects.
That topic_id must exactly match one of the keys in TOPICS.
"""


TOPICS = {

    # =========================================================
    # Python Syntax Basics
    # =========================================================

    "python_syntax_basics": {

        "id": "python_syntax_basics",

        "title": "Python Syntax Basics",

        "difficulty": "Beginner",

        "lesson": """
WHAT IS PYTHON SYNTAX?

Syntax refers to the rules used when writing Python code.

Just like sentences have rules for how words are arranged,
programming languages also have rules that must be followed.


WRITING PYTHON CODE

Python instructions are normally written one statement at a time.

Example:

    print("Hello!")

Python reads this instruction and executes it.


CASE SENSITIVITY

Python is case-sensitive.

This means:

    name

and:

    Name

are treated as different names.


QUOTATION MARKS

Text values must be surrounded by quotation marks.

Correct:

    "Hello"

Incorrect:

    Hello


PARENTHESES

Some Python functions use parentheses.

Example:

    print("Hello")

The value being given to the function is placed inside
the parentheses.


INDENTATION

Python uses indentation to organize blocks of code.

Example:

    if True:
        print("Hello")

The indented line belongs to the if statement.


COMMENTS

Comments are notes written inside code.

They begin with:

    #

Example:

    # This is a comment

Python ignores comments when running the program.


REMEMBER

Python syntax means following the rules for writing valid
Python code.
""",

        "challenge_id": "python_syntax_basics_001"
    },


    # =========================================================
    # Variables
    # =========================================================

    "variables": {

        "id": "variables",

        "title": "Variables",

        "difficulty": "Beginner",

        "lesson": """
WHAT ARE VARIABLES?

Variables are used to store information that can be used later
in a program.

Think of a variable like a labeled container.

Example:

    age = 18

Here:

    age

is the name of the variable.

The equals sign:

    =

assigns a value to the variable.

And:

    18

is the value stored inside it.


VARIABLE SYNTAX

The basic syntax is:

    variable_name = value

Examples:

    score = 100

    player_name = "John"

    health = 50


VARIABLE NAMES

Variable names should describe what the stored value represents.

Examples:

    player_health = 100

    score = 50


STRINGS AND NUMBERS

Variables can store different types of values.

Number:

    age = 18

Text:

    name = "John"


REMEMBER

Creating a variable usually follows:

    name = value
""",

        "challenge_id": "variables_001"
    },


    # =========================================================
    # Data Types
    # =========================================================

    "data_types": {

        "id": "data_types",

        "title": "Data Types",

        "difficulty": "Beginner",

        "lesson": """
WHAT ARE DATA TYPES?

Data types describe the kind of value stored in a program.

Python contains several common data types.


INTEGER - int

Integers are whole numbers.

Examples:

    age = 18

    score = 100


FLOAT - float

Floats are numbers containing decimal points.

Examples:

    height = 1.75

    price = 99.50


STRING - str

Strings are used to store text.

Examples:

    name = "John"

    message = "Hello!"


BOOLEAN - bool

A Boolean has only two possible values:

    True

or:

    False

Examples:

    has_key = True

    game_over = False


CHECKING A DATA TYPE

Python provides the type() function.

Example:

    age = 18

    print(type(age))


REMEMBER

Common Python data types include:

    int
    float
    str
    bool
""",

        "challenge_id": "data_types_001"
    },


    # =========================================================
    # Type Casting
    # =========================================================

    "type_casting": {

        "id": "type_casting",

        "title": "Type Casting",

        "difficulty": "Beginner",

        "lesson": """
WHAT IS TYPE CASTING?

Type casting means converting a value from one data type
into another data type.

Python provides functions that can perform these conversions.


CONVERTING TO AN INTEGER

Use:

    int()

Example:

    number = "18"

    age = int(number)

The string "18" becomes the integer 18.


CONVERTING TO A FLOAT

Use:

    float()

Example:

    number = "10.5"

    price = float(number)


CONVERTING TO A STRING

Use:

    str()

Example:

    score = 100

    text_score = str(score)


CONVERTING TO A BOOLEAN

Use:

    bool()

Example:

    value = bool(1)


WHY TYPE CASTING IS USEFUL

Sometimes data is stored in one type but needs to be used
as another type.

For example:

    age = "18"

cannot be treated like a normal number until it is converted:

    age = int(age)


REMEMBER

Common type casting functions are:

    int()
    float()
    str()
    bool()
""",

        "challenge_id": "type_casting_001"
    },
    # =========================================================
    # Input
    # =========================================================

    "input_lesson": {

        "id": "input_lesson",

        "title": "Input",

        "difficulty": "Beginner",

        "lesson": """
WHAT IS INPUT?

Input allows a program to receive information from the user.

Python uses the input() function for this.


USING INPUT()

The basic syntax is:

    input("Message")

The message inside the parentheses is shown to the user.

Example:

    input("Enter your name: ")


STORING INPUT

The value entered by the user should usually be stored
inside a variable.

Example:

    name = input("Enter your name: ")

Here:

    name

stores whatever the user enters.


INPUT RETURNS A STRING

The input() function normally returns text.

Example:

    age = input("Enter your age: ")

Even if the user enters:

    18

Python initially treats it as a string.


INPUT WITH TYPE CASTING

If you need a number, input can be combined with
type casting.

Example:

    age = int(input("Enter your age: "))


DISPLAYING USER INPUT

You can use the stored value later in the program.

Example:

    name = input("Enter your name: ")

    print(name)


REMEMBER

The basic pattern is:

    variable = input("Prompt: ")
""",

        "challenge_id": "input_lesson_001"
    },


    # =========================================================
    # Formatted Output
    # =========================================================

    "formatted_output": {

        "id": "formatted_output",

        "title": "Formatted Output",

        "difficulty": "Beginner",

        "lesson": """
WHAT IS FORMATTED OUTPUT?

Formatted output allows values stored in variables to be
placed inside text.

This makes output easier to read and understand.


F-STRINGS

A common way to create formatted output in Python is
using an f-string.

Place the letter:

    f

before the quotation marks.

Example:

    name = "Alex"

    print(f"Hello, {name}!")


USING CURLY BRACES

Variables are placed inside curly braces:

    { }

Example:

    score = 100

    print(f"Score: {score}")

Python replaces:

    {score}

with the value stored inside the score variable.


MULTIPLE VALUES

An f-string can contain more than one value.

Example:

    name = "Alex"

    score = 100

    print(f"{name} has {score} points.")


PLACEHOLDER FORMATTING

Python can also use placeholders with the percent symbol.

Example:

    score = 100

    print("Score: %d" % score)

Some common placeholders are:

    %s    text

    %d    integer


WHY FORMATTED OUTPUT IS USEFUL

Instead of writing separate pieces of output, formatted
strings combine text and values into one readable message.


REMEMBER

A basic f-string looks like:

    print(f"Text {variable}")
""",

        "challenge_id": "formatted_output_001"
    },


    # =========================================================
    # Arithmetic Operators
    # =========================================================

    "operators": {
        "id": "operators",
        "title": "Arithmetic Operators",
        "difficulty": "Beginner",
        "lesson": """
OPERATORS

Operators tell Python to calculate with values.

    +   addition
    -   subtraction
    *   multiplication
    /   division

An expression can be stored in a variable:

    total = 12 + 8

Python calculates the right side first, then stores the result.
""",
        "challenge_id": "operators_001",
    },


    # =========================================================
    # String Basics
    # =========================================================

    "string_basics": {
        "id": "string_basics",
        "title": "String Basics",
        "difficulty": "Beginner",
        "lesson": """
STRING BASICS

A string is text surrounded by quotation marks.

    name = "Alex"

The + operator joins strings. This is called concatenation.

    title = "Code" + " Breaker"

Spaces inside quotation marks are part of the resulting text.
""",
        "challenge_id": "string_basics_001",
    },


    # =========================================================
    # If / Elif / Else
    # =========================================================

    "conditionals": {
        "id": "conditionals",
        "title": "If, Elif, and Else",
        "difficulty": "Beginner",
        "lesson": """
MAKING DECISIONS

An if statement runs a block when its condition is true.
elif checks another condition. else handles everything remaining.

    if score >= 90:
        rank = "Gold"
    elif score >= 75:
        rank = "Silver"
    else:
        rank = "Bronze"

Each heading ends with a colon, and each body is indented.
""",
        "challenge_id": "conditionals_001",
    },


    # =========================================================
    # Boolean Logic
    # =========================================================

    "boolean_logic": {
        "id": "boolean_logic",
        "title": "Boolean Logic",
        "difficulty": "Beginner",
        "lesson": """
BOOLEAN LOGIC

Booleans have only two values: True and False.

Use and when both conditions must be true. Use not to reverse a value.

    can_enter = has_key and not gate_locked

This is true only when the player has a key and the gate is not locked.
""",
        "challenge_id": "boolean_logic_001",
    },

}


def get_topic(topic_id):
    """
    Return a topic by id.

    Returns None when the id does not exist.
    """

    return TOPICS.get(topic_id)
