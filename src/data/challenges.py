#challenges.py
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

        "problem": """
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

        "problem": """
Use print() to display the message

Hello, World!
        """,

        "objective": "Use print() to display: Hello, World!",

        "requirements": [],

        "expected": {
            "value": "Hello, World!"
        }
    }

}


def get_challenge(challenge_id):
    """
    Return a coding challenge by id.

    Returns None if the challenge does not exist.
    """

    return CHALLENGES.get(challenge_id)