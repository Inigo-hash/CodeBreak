"""Adjustable encounter layout for the Beginner/Island stage.

Anchors are normalized map coordinates copied from the marked reference map.
The spawn resolver moves each member to nearby walkable ground at runtime.
"""

BEGINNER_STAGE_ENCOUNTERS = (
    {
        "id": "bottom_right_lower",
        "anchor": (0.751915, 0.756250),
        "topic_id": "python_syntax_basics",
        "zone_size": (360, 300),
        "enemies": ("tiyanak_sinta",) * 5
    },

    {
        "id": "bottom_left",
        "anchor": (0.227660, 0.750000),
        "topic_id": "variables",
        "zone_size": (360, 300),
        "enemies": ("tiyanak_sinta",) * 5
    },

    {
        "id": "bottom_right_upper",
        "anchor": (0.697447, 0.731250),
        "topic_id": "data_types",
        "zone_size": (360, 300),
        "enemies": ("manananggal",) * 4
    },

    {
        "id": "middle_right",
        "anchor": (0.622553, 0.556250),
        "topic_id": "type_casting",
        "zone_size": (400, 340),
        "enemies": ("manananggal", "tiyanak_sinta") * 4
    },

    {
        "id": "left_middle",
        "anchor": (0.296221, 0.484750),
        "topic_id": "input_lesson",
        "zone_size": (400, 340),
        "enemies": ("tikbalang",) * 3
    },

    {
        "id": "far_right_middle",
        "anchor": (0.792766, 0.550000),
        "topic_id": "boolean_logic",
        "zone_size": (360, 340),
        "enemies": ("tikbalang", "tiyanak_sinta") * 3
    },

    {
        "id": "upper_right_center",
        "anchor": (0.724681, 0.450000),
        "topic_id": "operators_lesson",
        "zone_size": (400, 340),
        "enemies": ("manananggal", "tikbalang") * 3
    },

    {
        "id": "top_right",
        "anchor": (0.772340, 0.256250),
        "topic_id": "strings_lesson",
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
        "topic_id": "control_flow_lesson",
        "zone_size": (420, 340),
        "enemies": (
            "tikbalang",
            "manananggal",
            "tiyanak_sinta"
        ) * 3
    },

    # Two small camps close the unguarded gaps called out in the playtest:
    # the bottom-centre chest/barrel pair and the west-centre barrel now have
    # enemies visibly standing over their code locks.
    {
        "id": "bottom_center_cache",
        "anchor": (0.547872, 0.775000),
        "topic_id": "formatted_output",
        "zone_size": (300, 260),
        "enemies": ("tiyanak_sinta", "manananggal"),
    },

    {
        "id": "west_center_cache",
        "anchor": (0.207447, 0.412500),
        "topic_id": "strings_lesson",
        "zone_size": (280, 260),
        "enemies": ("tiyanak_sinta", "tikbalang"),
    },
)

# Core dirt tiles from Ground Layer 1 in basic.tmx. Grass is intentionally
# walkable for the player, so collision properties cannot identify paths.
BEGINNER_PATH_GIDS = frozenset((20, 21, 38, 39))
