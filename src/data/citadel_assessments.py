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
        "time_limit": 900,
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
        "time_limit": 900,
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
