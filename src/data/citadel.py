"""Stage 3 Citadel map, patrol encounters, and learning progression."""
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
        "path_layer": "ground",
        # GID 2275 is the solid land ground tile; GID 3912 is the surrounding lava.
        "path_gids": frozenset({2275}),
        "encounters": (
            # Six optional patrol camps at the marked circle locations.
            # Anchors are normalized to the 120x120 map, estimated from the
            # user's screenshot; collision-safe resolver chooses final positions.
            {
                "id": "citadel_patrol_northwest",
                "anchor": (20/120, 32/120),
                "zone_size": (320, 280),
                "spawn_margin": 32,
                "require_path": True,
                "enemies": ("zombie_aktan",) * 4,
            },
            {
                "id": "citadel_patrol_west_center",
                "anchor": (45/120, 38/120),
                "zone_size": (320, 280),
                "spawn_margin": 32,
                "require_path": False,
                "enemies": ("zombie_aktan", "white_lady") * 2,
            },
            {
                "id": "citadel_patrol_east",
                "anchor": (94/120, 41/120),
                "zone_size": (320, 280),
                "spawn_margin": 32,
                "require_path": False,
                "enemies": ("white_lady",) * 4,
            },
            {
                "id": "citadel_patrol_midwest",
                "anchor": (22/120, 56/120),
                "zone_size": (320, 280),
                "spawn_margin": 32,
                "require_path": False,
                "enemies": ("white_lady",) * 4,
            },
            {
                "id": "citadel_patrol_mid_south",
                "anchor": (57/120, 62/120),
                "zone_size": (320, 280),
                "spawn_margin": 32,
                "require_path": False,
                "enemies": ("zombie_aktan", "white_lady") * 2,
            },
            {
                "id": "citadel_patrol_southwest",
                "anchor": (20/120, 72/120),
                "zone_size": (320, 280),
                "spawn_margin": 32,
                "require_path": False,
                "enemies": ("zombie_aktan",) * 4,
            },
        ),
        "map_layout_version": 3,
    },
    "manual": {
        "summary": "Study six advanced programming topics in the Citadel. Complete all 15 coding problems to earn six mastery keys.",
        "controls": WORLD_CONTROLS,
        "topics": CITADEL_CHALLENGE_IDS,
        "mechanics": [
            "Complete every problem at a topic terminal to earn that topic's mastery key once.",
            "Practice attempts and repeated submissions do not grant extra keys.",
            "File-handling challenges use in-memory text/JSON because the game editor cannot access real files.",
            "Six optional patrol camps are spread across the Citadel. Clear them for combat practice while completing the mapped lessons.",
        ],
        "tips": [
            "Read the topic lesson before opening its challenge list.",
            "Use empty inputs and boundary cases to check your solutions.",
            "Developer mode can load the matching reference solution with F7 while a challenge editor is open.",
        ],
    },
    "enemies": ["white_lady", "zombie_aktan"],
    "items": [],
    "completion": {
        "content_ready": True,
        "required_keys": 6,
        "mastery_bundles": CITADEL_BUNDLES,
        "topic_key_rewards": {cid: 0 for cid in CITADEL_CHALLENGE_IDS},
        "encounter_key_reward": 0,
    },
    "objectives": [
        {"id": tid + "_mastery", "text": "Master " + CITADEL_TOPICS[tid]["title"] + ".", "kind": "topic", "target": tid, "optional": False}
        for tid in CITADEL_TOPIC_ORDER
    ],
}
