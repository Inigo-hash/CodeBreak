"""Stage 3 Citadel map, patrol encounters, and learning progression."""
from src.data.stage_music import STAGE_MUSIC
from src.data.controls import WORLD_CONTROLS
from src.data.citadel_assessments import CITADEL_ASSESSMENT_IDS
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
        "zones": (
            {
                "name": "The Lapu-Lapu Arena",
                "map_label": False,
                "rect": (0.635, 0.405, 0.105, 0.105),
                "is_boss_zone": True,
                "entrance_rect": (0.655, 0.485, 0.065, 0.035),
                "movement_rect": (0.275, 0.055, 0.515, 0.435),
            },
        ),
        "path_layer": "ground",
        # GID 2275 is the solid land ground tile; GID 3912 is the surrounding lava.
        "path_gids": frozenset({2275}),
        # Keep the currently established 23-enemy layout; any later authored
        # patrol entries are intentionally not instantiated.
        "max_enemies": 23,
        # The arena is compact; leave room for the boss body and its escape
        # route instead of shrinking the spawn area by four tiles per side.
        "boss_spawn_margin": 16,
        # The altar is north of the player-facing approach; place the boss at
        # the marked X on the south side of the arena rather than its center.
        "boss_spawn_anchor": (0.68, 0.502),
        # Exact world-pixel position (body center) where Zombie Lapu-Lapu
        # appears. It sits a little south of the spot at world_xy
        # (1056, 625). If a wall is in the way, the nearest clear spot is used.
        "boss_spawn_position": (1064, 681),
        # Dying during the boss fight ends the fight, removes the boss and
        # respawns the player at the statue checkpoint. Use Fight Boss at the
        # yellow marker again to start a fresh encounter.
        "boss_loss_respawn_at_checkpoint": True,
        # The fight only ever starts from the yellow marker's FIGHT BOSS
        # button. It is never saved, so quitting and reloading removes the
        # boss, and walking through the arena doorway does not start it.
        "boss_fight_via_gate_only": True,
        "encounters": (
            # Six optional patrol camps at the marked circle locations.
            # Anchors are normalized to the 120x120 map, estimated from the
            # user's screenshot; collision-safe resolver chooses final positions.
            {
                "id": "citadel_patrol_northwest",
                "anchor": (20/120, 35/120),
                "zone_size": (320, 280),
                "spawn_margin": 32,
                "require_path": True,
                "enemies": ("zombie_aktan",) * 4,
            },
            {
                "id": "citadel_patrol_west_center",
                "anchor": (45/120, 43/120),
                "zone_size": (320, 280),
                "spawn_margin": 32,
                "require_path": True,
                "enemies": ("zombie_aktan", "white_lady") * 2,
            },
            {
                "id": "citadel_patrol_east",
                "anchor": (94/120, 47/120),
                "zone_size": (320, 280),
                "spawn_margin": 32,
                "require_path": True,
                "enemies": ("white_lady", "zombie_aktan") * 2,
            },
            {
                "id": "citadel_patrol_midwest",
                "anchor": (22/120, 56/120),
                "zone_size": (320, 280),
                "spawn_margin": 32,
                "require_path": True,
                "enemies": ("white_lady",) * 4,
            },
            {
                "id": "citadel_patrol_mid_south",
                "anchor": (57/120, 62/120),
                "zone_size": (320, 280),
                "spawn_margin": 32,
                "require_path": True,
                "enemies": ("zombie_aktan", "white_lady") * 2,
            },
            {
                "id": "citadel_patrol_statue_south",
                "anchor": (27/120, 75/120),
                "zone_size": (320, 280),
                "spawn_margin": 32,
                "require_path": True,
                # Keep the zombies on the wider clear land to the right of
                # the two ghosts; default lower offsets overlap blocked tiles.
                "spawn_offsets": ((-42, -22), (42, -22), (80, 0), (112, 0)),
                "enemies": ("white_lady",) * 2 + ("zombie_aktan",) * 2,
            },
            {
                "id": "citadel_patrol_southwest",
                "anchor": (20/120, 72/120),
                "zone_size": (320, 280),
                "spawn_margin": 32,
                "require_path": True,
                "enemies": ("zombie_aktan",) * 4,
            },
        ),
        "map_layout_version": 3,
    },
    "manual": {
        "summary": "Study six advanced programming topics in the Citadel. Complete all 15 coding problems to earn six mastery keys, defeat Zombie Lapu-Lapu, and pass the final assessment.",
        "controls": WORLD_CONTROLS,
        "topics": CITADEL_CHALLENGE_IDS,
        "mechanics": [
            "Complete every problem at a topic terminal to earn that topic's mastery key once.",
            "Practice attempts and repeated submissions do not grant extra keys.",
            "Complete all six topics and collect all six mastery keys before entering the Lapu-Lapu Arena.",
            "Defeat Zombie Lapu-Lapu to unlock the Citadel final assessment. Passing it completes the stage.",
            "File-handling challenges use in-memory text/JSON because the game editor cannot access real files.",
            "Six optional patrol camps are spread across the Citadel. Clear them for combat practice while completing the mapped lessons.",
        ],
        "tips": [
            "Read the topic lesson before opening its challenge list.",
            "Use empty inputs and boundary cases to check your solutions.",
            "Developer mode can load the matching reference solution with F7 while a challenge editor is open.",
        ],
    },
    "enemies": ["white_lady", "zombie_aktan", "zombie_lapu_lapu"],
    "items": [],
    "completion": {
        "content_ready": True,
        "required_keys": 6,
        "required_boss": "zombie_lapu_lapu",
        "required_final_challenge": "citadel_expedition_final",
        # Six different problems with their own timers; see
        # citadel_assessments.py.
        "final_assessment_ids": CITADEL_ASSESSMENT_IDS,
        "practice_after_failure": True,
        "mastery_bundles": CITADEL_BUNDLES,
        "topic_key_rewards": {cid: 0 for cid in CITADEL_CHALLENGE_IDS},
        "encounter_key_reward": 0,
    },
    "objectives": [
        {"id": tid + "_mastery", "text": "Master " + CITADEL_TOPICS[tid]["title"] + ".", "kind": "topic", "target": tid, "optional": False}
        for tid in CITADEL_TOPIC_ORDER
    ] + [
        {"id": "citadel_lapu_lapu", "text": "Defeat Zombie Lapu-Lapu in the Citadel arena.", "kind": "defeat", "target": "zombie_lapu_lapu", "optional": False},
        {"id": "citadel_final", "text": "Pass the Citadel final coding assessment.", "kind": "challenge", "target": "citadel_expedition_final", "optional": False},
    ],
}