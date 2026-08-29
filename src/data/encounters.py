"""Adjustable encounter layout for the Beginner/Island stage.

Anchors are normalized map coordinates copied from the marked reference map.
The spawn resolver moves each member to nearby walkable ground at runtime.
"""

BEGINNER_STAGE_ENCOUNTERS = (
    {
        "id": "bottom_right_lower",
        "anchor": (0.751915, 0.756250),
        "zone_size": (360, 300),
        "enemies": ("tiyanak_sinta",) * 5
    },

    {
        "id": "bottom_left",
        "anchor": (0.227660, 0.750000),
        "zone_size": (360, 300),
        "enemies": ("tiyanak_sinta",) * 5
    },

    {
        "id": "bottom_right_upper",
        "anchor": (0.697447, 0.731250),
        "zone_size": (360, 300),
        "enemies": ("manananggal",) * 4
    },

    {
        "id": "middle_right",
        "anchor": (0.622553, 0.556250),
        "zone_size": (400, 340),
        "enemies": ("manananggal", "tiyanak_sinta") * 4
    },

    {
        "id": "left_middle",
        "anchor": (0.296221, 0.484750),
        "zone_size": (400, 340),
        "spawn_margin": 56,
        "enemies": ("tikbalang",) * 3
    },

    {
        "id": "far_right_middle",
        "anchor": (0.792766, 0.550000),
        "zone_size": (360, 340),
        "enemies": ("tikbalang", "tiyanak_sinta") * 3
    },

    {
        "id": "upper_right_center",
        "anchor": (0.724681, 0.450000),
        "zone_size": (400, 340),
        "enemies": ("manananggal", "tikbalang") * 3
    },

    {
        "id": "top_right",
        "anchor": (0.772340, 0.256250),
        "zone_size": (380, 320),
        "enemies": (
            "manananggal",
            "manananggal",
            "tiyanak_sinta"
        ) * 3
    },

    {
        "id": "top_left",
        "anchor": (0.302553, 0.281250),
        "zone_size": (420, 340),
        "enemies": (
            "tikbalang",
            "manananggal",
            "tiyanak_sinta"
        ) * 3
    },
)

# Core dirt tiles from Ground Layer 1 in basic.tmx. Grass is intentionally
# walkable for the player, so collision properties cannot identify paths.
BEGINNER_PATH_GIDS = frozenset((20, 21, 38, 39))
