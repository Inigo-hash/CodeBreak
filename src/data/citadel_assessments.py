"""Citadel post-boss final assessment rotation.

These integrated assessment problems are deliberately separate from the topic
challenge set. They are registered in CHALLENGES so the existing editor,
function validator, progress screen and assessment shuffle bag can reuse them.
"""
CITADEL_ASSESSMENT_IDS = (
    "citadel_expedition_final",
    "citadel_json_final",
    "citadel_route_final",
)

CITADEL_ASSESSMENTS = {
    "citadel_expedition_final": {
        "id": "citadel_expedition_final",
        "title": "Expedition Readiness Report",
        "difficulty": "Advanced Final",
        "type": "function",
        "function_name": "build_expedition_report",
        "preserve_args": True,
        "time_limit": 1080,
        "objective": "Combine classes, properties, methods and exception handling to build a readiness report.",
        "problem": """Write build_expedition_report(records). records is a list of (name, raw_health) tuples. Define an Explorer class inside the function. Its constructor stores name and health; expose health through a @property; and add a status() method returning 'Ready' when health is at least 50, otherwise 'Recover'. Convert raw_health to int inside try/except ValueError. Skip invalid values and negative health. Return a list of dictionaries in the original order, each containing name, health, and status. Zero health is valid.""",
        "starter_code": "def build_expedition_report(records):\n    # Define Explorer, convert health safely, and build the report.\n    pass",
        "hints": [
            "Define class Explorer inside the function and assign name and _health in __init__.",
            "Use @property above health(self) to return _health.",
            "Add status(self) that checks self.health >= 50.",
            "Convert each raw_health with int() inside try/except ValueError; skip negative values.",
            "Append dictionaries containing name, health, and status to a report list.",
        ],
        "function_cases": [
            {"args": [[["Mira", "80"], ["Bato", "35"], ["Dara", "bad"], ["Eli", "0"], ["Yen", "-3"]]], "expected": [
                {"name": "Mira", "health": 80, "status": "Ready"},
                {"name": "Bato", "health": 35, "status": "Recover"},
                {"name": "Eli", "health": 0, "status": "Recover"},
            ]},
            {"args": [[["Rin", "50"], ["Kai", "49"]]], "expected": [
                {"name": "Rin", "health": 50, "status": "Ready"},
                {"name": "Kai", "health": 49, "status": "Recover"},
            ]},
            {"args": [[]], "expected": []},
        ],
    },
    "citadel_json_final": {
        "id": "citadel_json_final",
        "title": "Supply JSON Audit",
        "difficulty": "Advanced Final",
        "type": "function",
        "function_name": "summarize_json_supplies",
        "preserve_args": True,
        "time_limit": 720,
        "objective": "Use json imports, nested data, safe conversions and exceptions to summarize supply records.",
        "problem": """Write summarize_json_supplies(json_text). Import json and decode the text. The JSON contains a 'supplies' list of dictionaries with 'name' and 'quantity'. Convert quantity to int; skip malformed quantities and negative values; keep zero quantities. Return {'total': total_quantity, 'items': [(name, quantity), ...]} in the original order. If the JSON is malformed or 'supplies' is missing/not a list, return {'total': 0, 'items': []}. Do not access real files.""",
        "starter_code": "def summarize_json_supplies(json_text):\n    # Parse the supplied JSON text and safely summarize its records.\n    pass",
        "hints": [
            "Import json and wrap json.loads(json_text) in try/except json.JSONDecodeError.",
            "Check that data.get('supplies', []) is a list before looping.",
            "Convert each quantity with int() and skip ValueError or negative quantities.",
            "Keep zero quantities and append (name, quantity) tuples.",
            "Return the total and items using the exact dictionary keys requested.",
        ],
        "function_cases": [
            {"args": ['{"supplies":[{"name":"Potion","quantity":"3"},{"name":"Torch","quantity":4},{"name":"Map","quantity":"bad"},{"name":"Coin","quantity":0},{"name":"Trap","quantity":-2}]}'], "expected": {"total": 7, "items": [("Potion", 3), ("Torch", 4), ("Coin", 0)]}},
            {"args": ['{"supplies":[]}'], "expected": {"total": 0, "items": []}},
            {"args": ['{"other":3}'], "expected": {"total": 0, "items": []}},
            {"args": ["not json"], "expected": {"total": 0, "items": []}},
        ],
    },
    "citadel_route_final": {
        "id": "citadel_route_final",
        "title": "Route Validation Summary",
        "difficulty": "Advanced Final",
        "type": "function",
        "function_name": "summarize_routes",
        "preserve_args": True,
        "time_limit": 900,
        "objective": "Apply nested collections, list comprehensions and conditional filtering to validate routes.",
        "problem": """Write summarize_routes(routes, minimum). routes is a list of dictionaries containing 'name' and 'checkpoints'. Each checkpoint is a dictionary with 'name' and Boolean 'passed'. Include only routes that have at least minimum passed checkpoints. Return a dictionary mapping each included route name to a list of the names of its passed checkpoints, preserving route and checkpoint order. Use a list comprehension for each checkpoint list. Return an empty dictionary when none qualify.""",
        "starter_code": "def summarize_routes(routes, minimum):\n    # Filter routes and build each list of passed checkpoint names.\n    pass",
        "hints": [
            "Loop through each route and count its passed checkpoints.",
            "Skip routes whose passed checkpoint count is below minimum.",
            "Build the checkpoint names with a list comprehension and an if checkpoint['passed'] filter.",
            "Store the list under route['name'] in a result dictionary.",
        ],
        "function_cases": [
            {"args": [[{"name":"North","checkpoints":[{"name":"Gate","passed":True},{"name":"Bridge","passed":False},{"name":"Tower","passed":True}]},{"name":"South","checkpoints":[{"name":"Cave","passed":False}]}], 2], "expected": {"North": ["Gate", "Tower"]}},
            {"args": [[{"name":"West","checkpoints":[{"name":"Dock","passed":True}]}], 2], "expected": {}},
            {"args": [[{"name":"East","checkpoints":[{"name":"A","passed":True},{"name":"B","passed":True}]}], 2], "expected": {"East": ["A", "B"]}},
            {"args": [[], 0], "expected": {}},
        ],
    },
}


# ---------------------------------------------------------------------------
# Additional final problems. Together with the three above, the Citadel has
# six different problems. Timers scale with difficulty:
#   Explorer Leaderboard 10:00 < Supply JSON Audit 12:00 < Mission Log Reader
#   14:00 < Route Validation 15:00 < Expedition Readiness 18:00 < Supply
#   Request Handler 20:00.
# ---------------------------------------------------------------------------
CITADEL_ASSESSMENTS.update({
    "citadel_log_final": {
        "id": "citadel_log_final",
        "title": "Mission Log Reader",
        "difficulty": "Advanced Final",
        "type": "function",
        "function_name": "read_mission_log",
        "preserve_args": True,
        "time_limit": 840,
        "objective": "Use in-memory file text, string methods and safe conversions to read a mission log.",
        "problem": """Write read_mission_log(log_text). log_text is the text of a log file; the game cannot open real files, so treat the text as the file contents and go through it one line at a time with splitlines(). Each useful line looks like 'name,distance'. Strip whitespace from every line and from each part. Ignore blank lines and lines starting with '#'. Skip lines that do not have exactly two comma-separated parts, lines whose distance is not an integer (use try/except ValueError), and negative distances. Return {'entries': [(name, distance), ...], 'total': sum_of_distances, 'farthest': name_with_the_largest_distance}. Entries keep their original order. If several entries tie for the largest distance, farthest is the first of them. If there are no entries, farthest is None and total is 0.""",
        "starter_code": "def read_mission_log(log_text):\n    # Read log_text line by line with splitlines() and collect valid entries.\n    pass",
        "hints": [
            "Loop over log_text.splitlines() as if each item were one line read from a file.",
            "Call line.strip() and skip blank or '#' lines with continue.",
            "Use line.split(',') and check that there are exactly two parts before converting.",
            "Wrap int(distance_text) in try/except ValueError and skip negative values.",
            "Track the largest distance with a > comparison so the first tie wins.",
        ],
        "function_cases": [
            {"args": ["# mission log\nMira, 40\nBato,15\n\nbad line\nDara,x\nEli,-5\nYen,40\n"], "expected": {
                "entries": [("Mira", 40), ("Bato", 15), ("Yen", 40)], "total": 95, "farthest": "Mira"}},
            {"args": [""], "expected": {"entries": [], "total": 0, "farthest": None}},
            {"args": ["Kai,0"], "expected": {"entries": [("Kai", 0)], "total": 0, "farthest": "Kai"}},
            {"args": ["# only a comment\n   \nA,1,2\n"], "expected": {"entries": [], "total": 0, "farthest": None}},
        ],
    },
    "citadel_supply_final": {
        "id": "citadel_supply_final",
        "title": "Supply Request Handler",
        "difficulty": "Advanced Final",
        "type": "function",
        "function_name": "process_supply_requests",
        "preserve_args": True,
        "time_limit": 1200,
        "objective": "Define a custom exception and combine try/except/finally with dictionaries to process supply requests.",
        "problem": """Write process_supply_requests(stock, requests). stock is a dictionary of item -> quantity and requests is a list of (item, raw_amount) tuples. Define class SupplyError(Exception) inside the function. Work on a copy of stock; never change the dictionary that was passed in. Handle every request in order inside try/except/finally: convert raw_amount with int() (a ValueError means the request is 'invalid'); raise SupplyError('unknown') when the item is not in stock; raise SupplyError('invalid') when the amount is zero or negative; raise SupplyError('short') when the amount is larger than the quantity in stock; otherwise subtract the amount. Record each failed request as (item, reason) in order. The finally block must count every request as an attempt. Return {'stock': updated_copy, 'errors': [(item, reason), ...], 'attempts': number_of_requests}.""",
        "starter_code": "def process_supply_requests(stock, requests):\n    # Define SupplyError, copy stock, and handle each request safely.\n    pass",
        "hints": [
            "Define class SupplyError(Exception): pass inside the function, then make remaining = dict(stock).",
            "Put int(raw_amount) first in the try block so a bad value raises ValueError.",
            "Check unknown first, then amount <= 0, then amount > remaining[item], raising SupplyError with the reason text.",
            "Use except SupplyError as error: and append (item, str(error)); use a second except ValueError: for 'invalid'.",
            "Add 1 to attempts in a finally block so every request is counted.",
        ],
        "function_cases": [
            {"args": [{"potion": 5, "torch": 2}, [["potion", "2"], ["map", "1"], ["torch", "3"], ["potion", "bad"], ["torch", "0"], ["potion", "3"]]],
             "expected": {"stock": {"potion": 0, "torch": 2},
                          "errors": [("map", "unknown"), ("torch", "short"), ("potion", "invalid"), ("torch", "invalid")],
                          "attempts": 6}},
            {"args": [{}, []], "expected": {"stock": {}, "errors": [], "attempts": 0}},
            {"args": [{"rope": 1}, [["rope", "1"], ["rope", "1"]]],
             "expected": {"stock": {"rope": 0}, "errors": [("rope", "short")], "attempts": 2}},
        ],
    },
    "citadel_leaderboard_final": {
        "id": "citadel_leaderboard_final",
        "title": "Explorer Leaderboard",
        "difficulty": "Advanced Final",
        "type": "function",
        "function_name": "rank_explorers",
        "preserve_args": True,
        "time_limit": 600,
        "objective": "Use dictionaries, sorted() with a key function and slicing to build a leaderboard.",
        "problem": """Write rank_explorers(scores). scores is a list of (name, points) tuples and a name can appear more than once. Keep only each explorer's highest points. Return {'players': alphabetical list of unique names, 'best': {name: highest_points}, 'top': up to three names ordered by highest points from largest to smallest, with ties broken alphabetically}. Use sorted() with a key function for the ranking. Return empty collections when scores is empty.""",
        "starter_code": "def rank_explorers(scores):\n    # Track each explorer's best points, then rank the names.\n    pass",
        "hints": [
            "Build best = {} and update best[name] only when the name is new or points is higher.",
            "sorted(best) gives the alphabetical list of unique names.",
            "Use sorted(best, key=lambda name: (-best[name], name)) for points high to low, then name.",
            "Slice the ranked list with [:3] to keep at most three names.",
        ],
        "function_cases": [
            {"args": [[["Mira", 50], ["Bato", 70], ["Mira", 90], ["Dara", 70], ["Eli", 10]]],
             "expected": {"players": ["Bato", "Dara", "Eli", "Mira"],
                          "best": {"Mira": 90, "Bato": 70, "Dara": 70, "Eli": 10},
                          "top": ["Mira", "Bato", "Dara"]}},
            {"args": [[]], "expected": {"players": [], "best": {}, "top": []}},
            {"args": [[["Zed", 5]]], "expected": {"players": ["Zed"], "best": {"Zed": 5}, "top": ["Zed"]}},
            {"args": [[["A", -5], ["A", -9], ["B", -7]]],
             "expected": {"players": ["A", "B"], "best": {"A": -5, "B": -7}, "top": ["A", "B"]}},
        ],
    },
})

# Every problem in the rotation. The expedition report stays first because it
# is the stage's recorded completion challenge.
CITADEL_ASSESSMENT_IDS = tuple(CITADEL_ASSESSMENTS)