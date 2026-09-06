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
    night               True for the night veil and torch lighting, False
                        for a stage lit by its own tiles. An interior has
                        no dirt path to hang torches along, so inheriting
                        the Island's night would leave it pitch black.
    spawn               where the player starts, as (x, y) fractions of
                        the map like zone rects and encounter anchors
    zones               the stage's list from zones.py
    encounters          the stage's table from encounters.py
    path_layer          tile layer whose dirt tiles are walkable ground
    path_gids           authored gids in that layer counting as path
    map_layout_version  bumped when a map is re-cut, so old saves in
                        this stage can have their position migrated
    legacy_shift_tiles  (x, y) tiles an older save must move by

Stage order
-----------
`next_stage` names the stage this one leads to when its exit gate opens.
A stage that names none - or names one with no map - ends the run at the
main menu instead, which is what the Island did before the Castle had a
map. src/systems/stage_handoff.py reads it, so game.py still never names
a stage itself.

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
from src.data.zones import CASTLE_ZONES, ISLAND_ZONES


# Filled in for any stage that leaves a world setting out. A stage with no
# map is data-only: menus and saves can name it, but it cannot be entered.
WORLD_DEFAULTS = {
    "map": None,
    "music": None,
    "boss_music": None,
    "night": True,
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

        # Clearing the Corrupted Core gate now walks into stage 2 instead
        # of ending the run. See systems/stage_handoff.py.
        "next_stage": "castle",

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
        # if the TMX dimensions change. Nine keys alone are not sufficient:
        # every lesson listed in manual.topics must also be completed.
        "completion": {
            "required_keys": 9,
            "required_boss": "corrupted_core_kapre",
            "exit_name": "Corrupted Core Gate",
            "exit_rect": (0.544255, 0.231250, 0.023830, 0.028125),
            # Nine beginner lessons award one key each. Keeping rewards
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
                "text": "Repair the Operators terminal.",
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
                "id": "island_control_flow",
                "text": "Repair the Control Flow terminal.",
                "kind": "challenge",
                "target": "control_flow_lesson_001",
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

    # Stage 2. The lobby map is authored, so the Island's exit gate can
    # hand a finished run over to it. Everything else is still being
    # written: no lessons, no enemies, no boss, and no exit rect, which
    # means the Castle can be walked but not yet completed. Each of those
    # is a data addition here rather than a change to game.py.
    "castle": {

        "id": "castle",

        "name": "Castle",

        "subtitle": "Stage 2 - Intermediate",

        "playable": True,

        # The last authored stage: its gate, once it has one, ends the run
        # at the main menu the way the Island's used to.
        "next_stage": None,

        "world": {

            "map": "assets/map/tmx/map2_castle_lobby.tmx",

            # Placeholder until a castle theme is recorded - silence reads
            # as a broken build rather than as atmosphere.
            "music": "assets/audios/gameStage1Bgm.mp3",

            "boss_music": None,

            # An interior lights itself. The night veil hangs its torches
            # off the walkable dirt path, and a marble floor has none, so
            # inheriting the Island's night would black the lobby out.
            "night": False,

            # The foot of the grand staircase, dead centre, facing up into
            # the hall: where someone entering the castle would arrive.
            "spawn": (0.525, 0.425),

            "zones": CASTLE_ZONES,

            # No camps authored yet. Enemies arrive with the lesson route.
            "encounters": (),

            "path_layer": None,

            "path_gids": frozenset(),

            "map_layout_version": 1,

        },

        "manual": {

            "summary":
                "Past the Corrupted Core's gate the island's corruption "
                "gives way to stone. The castle lobby still stands, its "
                "stairs climbing into the dark, and its machinery runs on "
                "intermediate Python. Its lesson route is still being "
                "charted - for now, the way in is the way out.",

            "mechanics": [
                "The lobby is walkable; its lessons, enemies and boss are "
                "still being authored.",
                "Everything you learned on the island travels with you. "
                "Keys do not - the castle's gate wants its own.",
            ],

            "controls": WORLD_CONTROLS,

            "topics": [],

            "tips": [
                "Nothing in the lobby can hurt you yet. Use it to get your "
                "bearings.",
            ],
        },

        "enemies": [],

        "items": [],

        # No exit_rect: without one game.py builds no gate, which is the
        # honest state of a stage that cannot yet be finished.
        "completion": {
            "required_keys": 0,
            "required_boss": None,
            "exit_name": "Castle Exit",
            "topic_key_rewards": {},
        },

        "objectives": [
            # Provisional, and the only thing the Castle can currently ask
            # for: somewhere to walk that is not where the player lands.
            # It goes when the lesson terminals arrive.
            {
                "id": "castle_reach_lower_landings",
                "text": "Follow the stair down to the lower landings.",
                "kind": "explore",
                "target": "The Lower Landings",
                "optional": False,
            },
        ],
    },

}


def get_stage(stage_id):
    """
    Look up a stage record by id, falling back to the default stage.

    The lookup is case-insensitive because save files store the stage as
    a display name ("Island") while the keys here are lowercase ids
    ("island"). Display names are matched too, so a stage whose name is
    not simply its id capitalised cannot make its own saves reopen on the
    Island. Falling back rather than raising means an old save naming a
    stage that no longer exists still loads.
    """

    if stage_id:
        wanted = str(stage_id).strip().lower()
        stage = STAGES.get(wanted)
        if stage:
            return stage
        for stage in STAGES.values():
            if str(stage.get("name", "")).strip().lower() == wanted:
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
