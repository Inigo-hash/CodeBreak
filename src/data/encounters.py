"""Adjustable encounter layout for the Beginner/Island stage.

Anchors are normalized map coordinates copied from the marked reference map.
The spawn resolver moves each member to nearby walkable ground at runtime.
"""

BEGINNER_STAGE_ENCOUNTERS = (
    {"id": "bottom_right_lower", "anchor": (0.87, 0.91),
     "enemies": ("tiyanak_sinta",) * 4},
    {"id": "bottom_left", "anchor": (0.10, 0.90),
     "enemies": ("tiyanak_sinta",) * 4},
    {"id": "bottom_right_upper", "anchor": (0.79, 0.87),
     "enemies": ("manananggal",) * 2},
    {"id": "middle_right", "anchor": (0.68, 0.59),
     "enemies": ("manananggal", "tiyanak_sinta") * 2},
    {"id": "left_middle", "anchor": (0.22, 0.53),
     "enemies": ("tikbalang",) * 2},
    {"id": "far_right_middle", "anchor": (0.93, 0.58),
     "enemies": ("tikbalang", "tiyanak_sinta") * 2},
    {"id": "upper_right_center", "anchor": (0.83, 0.42),
     "enemies": ("manananggal", "tikbalang") * 2},
    {"id": "top_right", "anchor": (0.90, 0.11),
     "enemies": ("manananggal", "manananggal", "tiyanak_sinta") * 2},
    {"id": "top_left", "anchor": (0.21, 0.15),
     "enemies": ("tikbalang", "manananggal", "tiyanak_sinta") * 2},
)

# Core dirt tiles from Ground Layer 1 in basic.tmx. Grass is intentionally
# walkable for the player, so collision properties cannot identify paths.
BEGINNER_PATH_GIDS = frozenset((20, 21, 38, 39))
