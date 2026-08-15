"""
All coding challenges for the game.

Each challenge is pure data.

No validation logic belongs here.
"""

CHALLENGES = { 

    "variables_001": {

        "id": "variables_001",

        "title": "Variables",

        "difficulty": "Beginner",

        "type": "variable",

        "lesson":

        """
Variables are used to store information.

Examples

score = 100

name = "John"

age = 18
        """,

        "problem":

        """
Create a variable named

age

and assign the value

18
        """,

        "objective": "Create a variable named age and assign it the value 18.",

        "requirements": [],

        "expected": {

            "name": "age",

            "value": 18

        }

    },

    "print_001": {

        "id": "print_001",

        "title": "Say Hello",

        "difficulty": "Beginner",

        "type": "print",

        "lesson":

        """
print() displays text on the screen.

Example

print("I am a warrior")
        """,

        "problem":

        """
Use print() to display the message

Hello, World!
        """,

        "objective": 'Use print() to display: Hello, World!',

        "requirements": [],

        "expected": {

            "value": "Hello, World!"

        }

    }

}