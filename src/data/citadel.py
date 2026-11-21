"""Stage 3 Citadel map and learning progression.

Learning terminals are active; the previous cleanup remains in force:
no enemies, boss arena, encounters, or boss/assessment sequence is configured.
"""
from src.data.stage_music import STAGE_MUSIC
from src.data.controls import WORLD_CONTROLS
from src.data.stage3_topics import (
    CITADEL_TOPICS, CITADEL_CHALLENGES, CITADEL_TOPIC_ORDER,
    CITADEL_CHALLENGE_IDS, CITADEL_BUNDLES,
)

CITADEL_STAGE = {
    "id": "citadel",
    "name": "Citadel",
    "subtitle": "Stage 3 - Advanced",
    "area_name": "Lava Chamber",
    "next_stage": None,
    "playable": True,
    "progress": {"enabled": True},
    "world": {
        "map": "assets/map/tmx/map3.tmx",
        **STAGE_MUSIC["citadel"],
        "night": False,
        # Keep the established safe-floor arrival point.
        "spawn": (86/120, 92/120),
        "resume_position": False,
        "zoom": 2.5,
        "follow_edges": True,
        "zones": (),
        "encounters": (),
        "map_layout_version": 3,
    },
    "manual": {
        "summary": "Study five advanced programming topics in the Citadel. Complete all 14 coding problems to earn five mastery keys.",
        "controls": WORLD_CONTROLS,
        "topics": CITADEL_CHALLENGE_IDS,
        "mechanics": [
            "Complete every problem at a topic terminal to earn that topic's mastery key once.",
            "Practice attempts and repeated submissions do not grant extra keys.",
            "File-handling challenges use in-memory text/JSON because the game editor cannot access real files.",
            "Only the five mapped learning terminals are active. No enemies, boss arena, or encounters are configured.",
        ],
        "tips": [
            "Read the topic lesson before opening its challenge list.",
            "Use empty inputs and boundary cases to check your solutions.",
            "Developer mode can load the matching reference solution with F7 while a challenge editor is open.",
        ],
    },
    "enemies": [],
    "items": [],
    "completion": {
        "content_ready": True,
        "required_keys": 5,
        "mastery_bundles": CITADEL_BUNDLES,
        "topic_key_rewards": {cid: 0 for cid in CITADEL_CHALLENGE_IDS},
        "encounter_key_reward": 0,
    },
    "objectives": [
        {"id": tid + "_mastery", "text": "Master " + CITADEL_TOPICS[tid]["title"] + ".", "kind": "topic", "target": tid, "optional": False}
        for tid in CITADEL_TOPIC_ORDER
    ],
}
