"""
stages.py

One record per stage, tying together everything the Stage Information
panel shows: the manual, the enemy list, the item list and the
objectives. Pure data, like zones.py and challenges.py.

Enemies and items are referenced by id (into enemies.py / items.py)
rather than described here, so an enemy that shows up in three stages is
still written up exactly once.

World
-----
Each stage's `world` dict is everything game.py needs to actually load
it, so the gameplay screen reads the stage record instead of naming the
Island's files itself:

    map                 TMX path; a stage without one cannot be entered
    music               background track, or None for silence
    boss_music          track for this stage's boss fight, or None to
                        keep the ordinary stage music playing
    spawn               where the player starts, as (x, y) fractions of
                        the map like zone rects and encounter anchors
    zones               the stage's list from zones.py
    encounters          the stage's table from encounters.py
    path_layer          tile layer whose dirt tiles are walkable ground
    path_gids           authored gids in that layer counting as path
    map_layout_version  bumped when a map is re-cut, so old saves in
                        this stage can have their position migrated
    legacy_shift_tiles  (x, y) tiles an older save must move by

Objectives
----------
Each objective is a dict:

    id        unique string, also what gets stored in the save file
    text      the line shown to the player
    kind      "interact" | "challenge" | "defeat" | "explore"
    target    what completes it, read according to `kind`:
                interact  -> an item id from items.py
                challenge -> a challenge id from challenges.py
                defeat    -> an enemy id from enemies.py
                explore   -> a zone name from zones.py
    optional  True for side objectives (shown but not counted as required)

Interact, challenge, defeat, and explore objectives complete through
StageProgress.sync_objectives(); game.py records discoveries, victories,
and named-zone entry as the player moves through the stage.
"""

from src.data.challenges import CHALLENGES
from src.data.controls import WORLD_CONTROLS
from src.data.encounters import BEGINNER_PATH_GIDS, BEGINNER_STAGE_ENCOUNTERS
from src.data.zones import ISLAND_ZONES


# Filled in for any stage that leaves a world setting out. A stage with no
# map is data-only: menus and saves can name it, but it cannot be entered.
WORLD_DEFAULTS = {
    "map": None,
    "music": None,
    "boss_music": None,
    "spawn": (0.5, 0.5),
    "zones": (),
    "encounters": (),
    "path_layer": None,
    "path_gids": frozenset(),
    "map_layout_version": 1,
    "legacy_shift_tiles": (0, 0),
}


DEFAULT_STAGE_ID = "island"


STAGES = {

    "island": {

        "id": "island",

        "name": "Island",

        "subtitle": "Stage 1",

        "world": {

            "map": "assets/map/tmx/map1.tmx",

            "music": "assets/audios/gameStage1Bgm.mp3",

            "boss_music": (
                "assets/audios/bgm/boss_fight/easy/Boss_fight_easy_sound_01.mp3"
            ),

            # The original spawn: bottom-centre of the island, seven tiles
            # right of the middle and six tiles in from the ocean border.
            "spawn": (0.534574, 0.775),

            "zones": ISLAND_ZONES,

            "encounters": BEGINNER_STAGE_ENCOUNTERS,

            "path_layer": "Ground Layer 1",

            "path_gids": BEGINNER_PATH_GIDS,

            # Version 2 is the resized Island map: the original island was
            # shifted 30 tiles right and down when ocean space was added
            # around all four sides.
            "map_layout_version": 2,

            "legacy_shift_tiles": (30, 30),

        },

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
                "Entering the Corrupted Core starts its boss encounter. "
                "Victory is required before the castle exit can open.",
                "If the boss defeats you, choose safe combat practice or "
                "retry the encounter immediately.",
            ],

            # Shared with How To Play and the tutorial rather than
            # retyped: this list used to be missing Attack and Dodge
            # entirely. A stage that really does need its own set can
            # still write one out here instead.
            "controls": WORLD_CONTROLS,

            # Challenge ids from challenges.py. The panel prints each
            # one's real title and difficulty, so this list never falls
            # out of step with the challenges themselves.
            "topics": [
                "python_syntax_basics_001",
                "variables_001",
                "data_types_001",
                "type_casting_001",
                "input_lesson_001",
                "formatted_output_001",
                "operators_lesson_001",
                "strings_lesson_001",
                "control_flow_lesson_001",
                "boolean_logic_001",
            ],

            "tips": [
                "Duwende give up the chase quickly - distance is a real "
                "option.",
                "Read the lesson panel before the problem panel. It "
                "usually contains the exact line you need.",
                "The Core warden telegraphs its swing. Dodge first, then "
                "answer with one or two attacks.",
            ],
        },

        "enemies": [
            "tiyanak_sinta",
            "manananggal",
            "tikbalang",
            "corrupted_core_kapre",
        ],

        "items": [
            "barrel",
            "burrow",
            "crate",
            "chest",
            "hay",
            "vase",
            "mang_tahimik",
        ],

        # The castle doorway in the Corrupted Core is the stage exit. Its
        # rectangle is fractional, like zone rectangles, so it stays aligned
        # if the TMX dimensions change. Ten keys alone are not sufficient:
        # every lesson listed in manual.topics must also be completed.
        "completion": {
            "required_keys": 10,
            "required_boss": "corrupted_core_kapre",
            "exit_name": "Corrupted Core Gate",
            "exit_rect": (0.544255, 0.231250, 0.023830, 0.028125),
            # Ten beginner lessons award one key each. Keeping rewards
            # authored here makes save migration deterministic.
            "topic_key_rewards": {
                "python_syntax_basics_001": 1,
                "variables_001": 1,
                "data_types_001": 1,
                "type_casting_001": 1,
                "input_lesson_001": 1,
                "formatted_output_001": 1,
                "operators_lesson_001": 1,
                "strings_lesson_001": 1,
                "control_flow_lesson_001": 1,
                "boolean_logic_001": 1,
            },
        },

        "objectives": [
            {
                "id": "island_search_first",
                "text": "Search anything you can find on the island.",
                "kind": "interact",
                "target": "barrel",
                "optional": False,
            },
            {
                "id": "island_python_syntax",
                "text": "Repair the Python Syntax Basics terminal.",
                "kind": "challenge",
                "target": "python_syntax_basics_001",
                "optional": False,
            },
            {
                "id": "island_variables",
                "text": "Repair the Variables terminal.",
                "kind": "challenge",
                "target": "variables_001",
                "optional": False,
            },
            {
                "id": "island_data_types",
                "text": "Repair the Data Types terminal.",
                "kind": "challenge",
                "target": "data_types_001",
                "optional": False,
            },
            {
                "id": "island_type_casting",
                "text": "Repair the Type Casting terminal.",
                "kind": "challenge",
                "target": "type_casting_001",
                "optional": False,
            },
            {
                "id": "island_input",
                "text": "Repair the User Input terminal.",
                "kind": "challenge",
                "target": "input_lesson_001",
                "optional": False,
            },
            {
                "id": "island_formatted_output",
                "text": "Repair the Formatted Output terminal.",
                "kind": "challenge",
                "target": "formatted_output_001",
                "optional": False,
            },
            {
                "id": "island_core_boss",
                "text": "Defeat the warden of the Corrupted Core.",
                "kind": "defeat",
                "target": "corrupted_core_kapre",
                "optional": False,
            },
            {
                "id": "island_operators",
                "text": "Repair the Arithmetic Operators terminal.",
                "kind": "challenge",
                "target": "operators_lesson_001",
                "optional": False,
            },
            {
                "id": "island_strings",
                "text": "Repair the Strings terminal.",
                "kind": "challenge",
                "target": "strings_lesson_001",
                "optional": False,
            },
            {
                "id": "island_conditionals",
                "text": "Repair the Control Flow terminal.",
                "kind": "challenge",
                "target": "control_flow_lesson_001",
                "optional": False,
            },
            {
                "id": "island_boolean_logic",
                "text": "Repair the Boolean Logic terminal.",
                "kind": "challenge",
                "target": "boolean_logic_001",
                "optional": False,
            },
            {
                "id": "island_burrow",
                "text": "Search a duwende burrow.",
                "kind": "interact",
                "target": "burrow",
                "optional": True,
            },
            {
                "id": "island_explore_amber_hollow",
                "text": "Reach Amber Hollow in the island's southeast.",
                "kind": "explore",
                "target": "Amber Hollow",
                "optional": True,
            },
            {
                "id": "island_open_chest",
                "text": "Open one of the island's timer chests.",
                "kind": "interact",
                "target": "chest",
                "optional": True,
            },
        ],
    },

    # Stage 2 content buffer. The record is intentionally non-playable until
    # its own map, encounters, topics, and completion gate are authored; it is
    # nevertheless valid stage data, so menus and save migrations can refer to
    # the Castle without falling back to the Island.
    "castle": {
        "id": "castle",
        "name": "Castle",
        "subtitle": "Stage 2 - Intermediate",
        "playable": False,
        # No map yet, which is exactly what keeps the Castle unenterable:
        # game.py refuses to load a stage whose world names no TMX file.
        "world": {
            "map": None,
            "music": None,
            "boss_music": None,
        },
        "manual": {
            "summary": (
                "Beyond the Corrupted Core stands a castle whose machinery "
                "depends on intermediate Python. Its lesson route is still "
                "being charted."
            ),
            "mechanics": [
                "The Castle is an intermediate-code stage scaffold.",
                "Its map, encounters, and lesson terminals will be added here.",
            ],
            "controls": WORLD_CONTROLS,
            "topics": [],
            "tips": [
                "Finish every Island lesson and defeat the Core warden first."
            ],
        },
        "enemies": [],
        "items": [],
        "completion": {
            "required_keys": 0,
            "required_boss": None,
            "exit_name": "Castle Exit",
            "topic_key_rewards": {},
        },
        "objectives": [],
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


def stage_world(stage):
    """
    Return a stage's world settings with every missing key defaulted.

    game.py reads this rather than the raw record so a stage that leaves
    a setting unwritten loads with a sane value instead of raising.
    """

    world = dict(WORLD_DEFAULTS)
    world.update(stage.get("world", {}))
    return world


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
