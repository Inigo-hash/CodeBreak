"""
stages.py

One record per stage, tying together everything the Stage Information
panel shows: the manual, the enemy list, the item list and the
objectives. Pure data, like zones.py and challenges.py.

Enemies and items are referenced by id (into enemies.py / items.py)
rather than described here, so an enemy that shows up in three stages is
still written up exactly once.

Objectives
----------
Each objective is a dict:

    id        unique string, also what gets stored in the save file
    text      the line shown to the player
    kind      "interact" | "challenge" | "explore"
    target    what completes it, read according to `kind`:
                interact  -> an item id from items.py
                challenge -> a challenge id from challenges.py
                explore   -> a zone name from zones.py
    optional  True for side objectives (shown but not counted as required)

Only "interact" and "challenge" complete themselves right now, through
StageProgress.sync_objectives(). "explore" objectives are recognised by
the panel but nothing marks them done yet - the zone-entry hook is not
wired up.
"""

from src.data.challenges import CHALLENGES


DEFAULT_STAGE_ID = "island"


STAGES = {

    "island": {

        "id": "island",

        "name": "Island",

        "subtitle": "Stage 1",

        "manual": {

            "summary":
                "You wake up on an island that runs on broken code. The "
                "terminals scattered across it still work, and every one "
                "you repair pushes the corruption back a little further. "
                "Explore, search what you find, and fix what you can.",

            "mechanics": [
                "Searching is a hold, not a tap - stay put until the bar "
                "fills or you get nothing.",
                "Code terminals open the editor. Your solution has to "
                "actually run, not just look right.",
                "Enemies you have met are recorded in the Enemies tab, "
                "along with what they are weak to.",
                "Anything you discover is kept in your save, so a "
                "reloaded game remembers what you already found.",
            ],

            "controls": [
                ("W A S D / Arrows", "Move"),
                ("E (hold)", "Search an object"),
                ("B", "Open your bag"),
                ("1 - 5 / Wheel", "Pick a hotbar slot"),
                ("M", "Open the island map"),
                ("I / J / K / O", "Manual, Enemies, Items, Objectives"),
                ("ESC", "Pause"),
            ],

            # Challenge ids from challenges.py. The panel prints each
            # one's real title and difficulty, so this list never falls
            # out of step with the challenges themselves.
            "topics": [
                "variables_001",
                "print_001",
            ],

            "tips": [
                "Duwende give up the chase quickly - distance is a real "
                "option.",
                "Read the lesson panel before the problem panel. It "
                "usually contains the exact line you need.",
            ],
        },

        "enemies": [
            "duwende_mandurug",
        ],

        "items": [
            "barrel",
            "burrow",
            "crate",
            "hay",
            "vase",
            "mang_tahimik",
        ],

        "objectives": [
            {
                "id": "island_search_first",
                "text": "Search anything you can find on the island.",
                "kind": "interact",
                "target": "barrel",
                "optional": False,
            },
            {
                "id": "island_variables",
                "text": "Repair a terminal with the Variables challenge.",
                "kind": "challenge",
                "target": "variables_001",
                "optional": False,
            },
            {
                "id": "island_print",
                "text": "Repair a terminal with the Say Hello challenge.",
                "kind": "challenge",
                "target": "print_001",
                "optional": False,
            },
            {
                "id": "island_burrow",
                "text": "Search a duwende burrow.",
                "kind": "interact",
                "target": "burrow",
                "optional": True,
            },
        ],
    },

}


def get_stage(stage_id):
    """
    Look up a stage record by id, falling back to the default stage.

    The lookup is case-insensitive because save files store the stage as
    a display name ("Island") while the keys here are lowercase ids
    ("island"). Falling back rather than raising means an old save
    naming a stage that no longer exists still loads.
    """

    if stage_id:
        stage = STAGES.get(str(stage_id).strip().lower())
        if stage:
            return stage

    return STAGES[DEFAULT_STAGE_ID]


def stage_challenges(stage):
    """
    The challenge records named by a stage's manual, skipping any id
    that challenges.py does not define.

    Returns a list of (challenge_id, challenge_dict) pairs, in the order
    the stage lists them.
    """

    pairs = []

    for challenge_id in stage.get("manual", {}).get("topics", []):
        challenge = CHALLENGES.get(challenge_id)
        if challenge:
            pairs.append((challenge_id, challenge))

    return pairs
