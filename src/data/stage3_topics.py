"""Stage 3 lessons and coding challenges matching the five topic IDs in map3.tmx."""
def _challenge(cid, title, name, params, objective, starter, hints, cases):
    return {"id": cid, "title": title, "difficulty": "Advanced", "type": "function",
            "function_name": name, "preserve_args": True, "objective": objective,
            "problem": f"Write {name}({params}). {objective}",
            "starter_code": starter, "hints": hints,
            "function_cases": [{"args": a, "expected": e} for a, e in cases]}

def _topic(tid, title, lesson, challenges, requirements=()):
    ids = tuple(challenges)
    return {"id": tid, "title": title, "difficulty": "Advanced", "requirements": list(requirements),
            "challenge_id": ids[0], "challenge_ids": ids,
            "lesson": lesson.strip() + "\n\nMASTERY\nComplete every problem in this topic to earn one Stage 3 mastery key. Practice attempts do not award keys."}

OOP_IDS = tuple(f"object_oriented_programming_lesson_{part}_001" for part in
                ("classes", "constructors", "encapsulation", "inheritance", "polymorphism", "overriding"))
MODULE_IDS = ("modules_imports_lesson_math_001", "modules_imports_lesson_helpers_001")
FILE_IDS = ("file_handling_lesson_text_001", "file_handling_lesson_json_001")
ERROR_IDS = ("advance_error_handling_lesson_multiple_001",)
DATA_IDS = tuple(f"advance_data_structure_lesson_{part}_001" for part in
                 ("nested", "list_comp", "dict_comp"))
VALIDATION_ID = "advance_data_structure_lesson_validation_001"

OOP_LESSON = """
CLASSES & OBJECTS: A class is a blueprint; an object is an instance created from it.
    class Player: pass
    explorer = Player()

CONSTRUCTORS (__init__): Python calls __init__ when an object is created.
    class Player:
        def __init__(self, name, hp):
            self.name = name
            self.hp = hp

ENCAPSULATION: Keep data and methods together. A leading underscore marks an
internal attribute; a property can expose controlled read access.
    class Player:
        def __init__(self, hp): self._hp = hp
        @property
        def hp(self): return self._hp

INHERITANCE: A child class inherits attributes and methods from a parent.
    class Warrior(Player): pass

POLYMORPHISM: Different classes can share a method name but implement it
differently. Calling the same method on different objects selects each object's behavior.

METHOD OVERRIDING: A child class can replace an inherited method by defining
a method with the same name. The child implementation is used for its instances.
"""
OOP_CHALLENGES = {
 OOP_IDS[0]: _challenge(OOP_IDS[0],"Create a Player Class","describe_player","name","Define Player inside the function, create an object, assign its name, and return {'class': 'Player', 'name': player.name}.","def describe_player(name):\n    # Define Player, create an object, and return its details.\n    pass",["Define class Player inside the function.","Create player = Player().","Set player.name = name and return the requested dictionary."],[([ "Mira" ],{"class":"Player","name":"Mira"}),([""],{"class":"Player","name":""})]),
 OOP_IDS[1]: _challenge(OOP_IDS[1],"Initialize Explorer Attributes","create_explorer","name, hp","Define Explorer with __init__(self, name, hp), instantiate it, and return a dictionary with its name and hp.","def create_explorer(name, hp):\n    # Define Explorer with a constructor.\n    pass",["Store both values on self in __init__.","Create Explorer(name, hp).","Return the instance attributes."],[(["Ada",100],{"name":"Ada","hp":100}),(["Kai",45],{"name":"Kai","hp":45})]),
 OOP_IDS[2]: _challenge(OOP_IDS[2],"Protect Player Health","read_player_health","hp","Define Player with internal _hp and a read-only @property hp. Return Player(hp).hp.","def read_player_health(hp):\n    # Define Player with _hp and a property.\n    pass",["Assign self._hp in __init__.","Use @property above def hp(self).","Return the property value."],[([100],100),([0],0),([37],37)]),
 OOP_IDS[3]: _challenge(OOP_IDS[3],"Inherit Explorer Skills","describe_warrior","name","Define Explorer with a name and travel() returning 'travel'. Define Warrior(Explorer) without replacing travel. Return its name and inherited skill result.","def describe_warrior(name):\n    # Define Explorer and its Warrior child.\n    pass",["Define __init__ and travel() on Explorer.","Declare class Warrior(Explorer).","Create Warrior(name) and call travel()."],[(["Rin"],{"name":"Rin","skill":"travel"}),(["Sol"],{"name":"Sol","skill":"travel"})]),
 OOP_IDS[4]: _challenge(OOP_IDS[4],"Use Polymorphic Attacks","run_attacks","power","Define Sword.attack() returning power and Staff.attack() returning power * 2. Return both attack results in a list.","def run_attacks(power):\n    # Define Sword and Staff with attack().\n    pass",["Both classes define attack(self).","Store power on each object.","Call attack() on both objects."],[([10],[10,20]),([0],[0,0]),([7],[7,14])]),
 OOP_IDS[5]: _challenge(OOP_IDS[5],"Override a Parent Method","boss_greeting","name","Define Explorer.greet() returning 'Hello, ' + name. Define Boss(Explorer) overriding greet() to return 'Fear me, ' + name. Return Boss(name).greet().","def boss_greeting(name):\n    # Define Explorer and override greet() in Boss.\n    pass",["Define greet() on Explorer.","Make Boss inherit from Explorer.","Define greet() again on Boss."],[(["Kapre"],"Fear me, Kapre"),(["Warden"],"Fear me, Warden")])
}

MODULE_LESSON = """
MODULES & IMPORTS: A module is a Python file containing reusable code.
    import math
    math.sqrt(16)  # 4.0
Import a specific name with: from math import sqrt. Then call sqrt(25).

MULTI-FILE PROGRAMS: Split a project into focused files. A helper module can
define functions and the main file imports and calls them.
    # helpers.py: def double(value): return value * 2
    # main.py: from helpers import double
    result = double(6)
"""
MODULE_CHALLENGES = {
 MODULE_IDS[0]: _challenge(MODULE_IDS[0],"Use a Module Function","circle_area","radius","Import math and return math.pi * math.pow(radius, 2).","def circle_area(radius):\n    # Import math and calculate the circle area.\n    pass",["Write import math inside the function.","Use math.pi and math.pow().","Return the calculated area."],[([1],3.141592653589793),([2],12.566370614359172),([0],0.0)]),
 MODULE_IDS[1]: _challenge(MODULE_IDS[1],"Import a Specific Function","double_with_math","value","Import sqrt directly from the math module, then return the square root of (value squared plus 9).","def double_with_math(value):\n    # Import sqrt directly from math, then return sqrt(value * value + 9).\n    pass",["Write: from math import sqrt.","Calculate value * value + 9 inside the function.","Return sqrt(value * value + 9)."],[([0],3.0),([4],5.0),([12],12.36931687685298)])
}

FILE_LESSON = """
READING & WRITING TEXT FILES: Real Python programs can open, read and write
text files. The game editor runs in a restricted environment, so challenges
use supplied text as in-memory file contents rather than accessing your device.
    text = "level=3"
    lines = text.splitlines()
    updated = text + "\\nstatus=ready"

JSON HANDLING: JSON represents structured data as text. json.dumps() encodes
Python data; json.loads() decodes JSON text.
    json.dumps({"level": 3})
    json.loads('{"level": 3}')
"""
FILE_CHALLENGES = {
 FILE_IDS[0]: _challenge(FILE_IDS[0],"Read and Update a Text Record","update_text_record","text","Treat text as file contents, append 'status=ready', and return the updated text joined with newline characters.","def update_text_record(text):\n    # Read the supplied text and append a status line.\n    pass",["Use text.splitlines().","Append 'status=ready'.","Return '\\n'.join(lines)."],[ (["level=3"],"level=3\nstatus=ready"),([""],"status=ready"),(["level=3\nname=Alex"],"level=3\nname=Alex\nstatus=ready") ]),
 FILE_IDS[1]: _challenge(FILE_IDS[1],"Parse JSON Text","read_json_profile","json_text","Import json, decode json_text, and return the 'level' value or 0 when the key is missing.","def read_json_profile(json_text):\n    # Import json, decode the text, and read level safely.\n    pass",["Use import json.","Decode with json.loads(json_text).","Return profile.get('level', 0)."],[(['{"level":3}'],3),(['{"name":"Alex"}'],0),(['{"level":0}'],0)])
}

ERROR_LESSON = """
MULTIPLE EXCEPTION TYPES: Follow one try block with specific except clauses.
    try:
        number = int(value)
        result = 100 / number
    except ValueError:
        result = "invalid number"
    except ZeroDivisionError:
        result = "cannot divide by zero"
Use finally for cleanup that must always happen. Keep each handler specific
so invalid text and division by zero produce different responses.
"""
ERROR_CHALLENGES = {
 ERROR_IDS[0]: _challenge(ERROR_IDS[0],"Handle Multiple Exceptions","safe_ratio","text","Convert text to an integer and return 100 divided by it. Return 'invalid number' for ValueError and 'cannot divide by zero' for ZeroDivisionError.","def safe_ratio(text):\n    # Convert, divide, and handle both exception types.\n    pass",["Put conversion and division inside try.","Catch ValueError separately.","Catch ZeroDivisionError separately."],[ (["4"],25.0),(["0"],"cannot divide by zero"),(["abc"],"invalid number"),(["-2"],-50.0) ])
}

DATA_LESSON = """
NESTED DATA STRUCTURES: A collection can contain other collections, such as
a list of dictionaries. Access nested values one level at a time:
    stages = [{"name":"Easy", "topics":["variables","if"]}]
    stages[0]["topics"][0]

LIST COMPREHENSIONS: [expression for value in values if condition]
    squares = [n * n for n in range(10) if n % 2 == 0]

DICTIONARY COMPREHENSIONS: {key: value for item in items if condition}
    positive = {k: v for k, v in stock.items() if v > 0}

"""
DATA_CHALLENGES = {
 DATA_IDS[0]: _challenge(DATA_IDS[0],"Read a Nested Stage Record","read_stage_record","stages, stage_name","Find the first stage dictionary with a matching name and return its topics list, or [] if absent.","def read_stage_record(stages, stage_name):\n    # Search the nested list of dictionaries.\n    pass",["Loop over each stage.","Compare stage.get('name') with stage_name.","Return stage.get('topics', []) or [] after the loop."],[([[], "Easy"],[]),([[{"name":"Easy","topics":["variables","if"]}],"Easy"],["variables","if"]),([[{"name":"Hard","topics":["oop"]}],"Easy"],[])]),
 DATA_IDS[1]: _challenge(DATA_IDS[1],"Filter with a List Comprehension","positive_squares","numbers","Return the squares of positive numbers using a list comprehension. Preserve order and duplicates.","def positive_squares(numbers):\n    # Use a list comprehension.\n    pass",["Use number * number as the expression.","Loop with for number in numbers.","Filter with if number > 0."],[([[]],[]),([[0,-2]],[]),([[2,-1,3,2]],[4,9,4])]),
 DATA_IDS[2]: _challenge(DATA_IDS[2],"Build a Dictionary Comprehension","positive_stock","stock","Return a new dictionary containing only pairs with quantity greater than zero. Do not change stock.","def positive_stock(stock):\n    # Use a dictionary comprehension.\n    pass",["Use {key: value for key, value in stock.items() if condition}.","Keep the original key and quantity.","Filter with quantity > 0."],[([{}],{}),([{"key":2,"potion":0,"map":-1}],{"key":2}),([{"a":1,"b":3}],{"a":1,"b":3})]),
 VALIDATION_ID: _challenge(VALIDATION_ID,"Validate a Calculation","validate_total","values, expected","Return True only when sum(values) equals expected; otherwise return False.","def validate_total(values, expected):\n    # Compare the calculated total with expected.\n    pass",["Calculate sum(values).","Compare it with expected using ==.","Return the comparison result."],[([[2,3],5],True),([[2,3],6],False),([[],0],True)])
}

CITADEL_TOPICS = {
 "object_oriented_programming_lesson": _topic("object_oriented_programming_lesson","Object-Oriented Programming (OOP)",OOP_LESSON,OOP_CHALLENGES),
 "modules_imports_lesson": _topic("modules_imports_lesson","Modules & Imports",MODULE_LESSON,MODULE_CHALLENGES, ("object_oriented_programming_lesson",)),
 "file_handling_lesson": _topic("file_handling_lesson","File Handling",FILE_LESSON,FILE_CHALLENGES, ("modules_imports_lesson",)),
 "advance_error_handling_lesson": _topic("advance_error_handling_lesson","Advanced Error Handling",ERROR_LESSON,ERROR_CHALLENGES, ("file_handling_lesson",)),
 "advance_data_structure_lesson": _topic("advance_data_structure_lesson","Advanced Data Structures",DATA_LESSON,
     {cid: DATA_CHALLENGES[cid] for cid in DATA_IDS}, ("advance_error_handling_lesson",)),
}
CITADEL_CHALLENGES = {**OOP_CHALLENGES, **MODULE_CHALLENGES, **FILE_CHALLENGES,
                      **ERROR_CHALLENGES, **{cid: DATA_CHALLENGES[cid] for cid in DATA_IDS}}
CITADEL_TOPIC_ORDER = tuple(CITADEL_TOPICS)
CITADEL_CHALLENGE_IDS = tuple(CITADEL_CHALLENGES)
CITADEL_BUNDLES = {tid + "_key": {"topics":[tid], "challenges":topic["challenge_ids"], "keys":1}
                   for tid,topic in CITADEL_TOPICS.items()}
