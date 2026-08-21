"""
enemies.py

The bestiary - one entry per enemy the player can meet, written as pure
data in the same spirit as zones.py and challenges.py. Nothing here draws
anything or knows about pygame; the Enemies tab of the stage info panel
(src/screens/stage_info.py) reads these entries and renders them.

An entry is only shown in full once the player has actually met that enemy
(see src/systems/stage_progress.py). Until then the panel prints "???" in
its place, so the bestiary doubles as a record of what you have survived
rather than a spoiler list.

``portrait`` points at a single existing animation frame rather than a
purpose-made portrait image. That keeps this file working with the art
that is already in the repo; swap in a proper portrait later and only this
line changes. A missing file is tolerated - the panel falls back to a
placeholder box instead of crashing.

Which enemies belong to which stage is NOT decided here. stages.py holds
that list, so the same enemy can appear in several stages without its
description being duplicated.
"""

ENEMIES = {

    "tiyanak_sinta": {
        "id": "tiyanak_sinta",
        "name": "Tiyanak",
        "family": "Tiyanak",
        "threat": "Low",
        "portrait": "assets/images/frames/tiyanak_sinta/walking/south/frame_0.png",
        "description": "A quick, common creature found along the island's outer paths.",
        "behavior": "Closes in when approached and strikes at short range.",
        "weakness": "Low endurance makes a clean sword combo effective.",
        "drops": ["Small scraps"],
    },

    "manananggal": {
        "id": "manananggal",
        "name": "Manananggal",
        "family": "Manananggal",
        "threat": "Moderate",
        "portrait": "assets/images/frames/manananggal/flying/south/frame_0.png",
        "description": "A flying hunter that guards the island's deeper routes.",
        "behavior": "Detects intruders from farther away and attacks aggressively.",
        "weakness": "Dodge its committed strike, then counter during recovery.",
        "drops": ["Corrupted fragments"],
    },

    "tikbalang": {
        "id": "tikbalang",
        "name": "Tikbalang",
        "family": "Tikbalang",
        "threat": "High",
        "portrait": "assets/images/frames/tikbalang/walking/south/frame_0.png",
        "description": "A powerful guardian encountered far from the island entrance.",
        "behavior": "Pursues over a wide area and delivers heavy close-range blows.",
        "weakness": "Its deliberate approach leaves room to reposition before attacking.",
        "drops": ["Large corrupted fragments"],
    },

    "duwende_mandurug": {

        "id": "duwende_mandurug",

        "name": "Duwende (Mandurug)",

        "family": "Duwende",

        # Free-text so it can read as a word rather than a number:
        # Low / Moderate / High / Boss.
        "threat": "Low",

        "portrait":
            "assets/images/frames/duwende_mandurug/walking/"
            "walking_forward/frame_0.png",

        "description":
            "A small earth-dweller that keeps to the mounds and burrows "
            "of the island. It is territorial rather than cruel, and it "
            "guards whatever it has dragged underground.",

        "behavior":
            "Patrols a short loop near its burrow and closes in once you "
            "step inside it. It gives up quickly if you back away.",

        "weakness":
            "Slow to turn. Circling around it buys you enough time to "
            "get past or to strike from behind.",

        "drops": [
            "Scraps of buried loot",
        ],
    },

}


def get_enemy(enemy_id):
    """
    Look up one bestiary entry, or None when the id is unknown.

    Returning None (instead of raising) means a stage can reference an
    enemy that has not been written up yet without taking the game down
    with it - the panel simply skips the entry.
    """

    return ENEMIES.get(enemy_id)
