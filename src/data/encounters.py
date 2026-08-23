"""Adjustable encounter layout for the Beginner/Island stage.

Anchors are normalized map coordinates copied from the marked reference map.
The spawn resolver moves each member to nearby walkable ground at runtime.
"""

BEGINNER_STAGE_ENCOUNTERS = (
    {"id": "bottom_right_lower", "anchor": (0.87, 0.91), "zone_size": (360, 300),
     "enemies": ("tiyanak_sinta",) * 4},
    {"id": "bottom_left", "anchor": (0.10, 0.90), "zone_size": (360, 300),
     "enemies": ("tiyanak_sinta",) * 4},
    {"id": "bottom_right_upper", "anchor": (0.79, 0.87), "zone_size": (360, 300),
     "enemies": ("manananggal",) * 2},
    {"id": "middle_right", "anchor": (0.68, 0.59), "zone_size": (400, 340),
     "enemies": ("manananggal", "tiyanak_sinta") * 2},
    # Centered within Ferngate Clearing. The previous 0.22/0.53 anchor sat
    # only 32px from its southern leash, clipping detection to melee distance.
    {"id": "left_middle", "anchor": (0.2007, 0.4756), "zone_size": (400, 340),
     "spawn_margin": 56,
     "enemies": ("tikbalang",) * 2},
    {"id": "far_right_middle", "anchor": (0.93, 0.58), "zone_size": (360, 340),
     "enemies": ("tikbalang", "tiyanak_sinta") * 2},
    {"id": "upper_right_center", "anchor": (0.83, 0.42), "zone_size": (400, 340),
     "enemies": ("manananggal", "tikbalang") * 2},
    {"id": "top_right", "anchor": (0.90, 0.11), "zone_size": (380, 320),
     "enemies": ("manananggal", "manananggal", "tiyanak_sinta") * 2},
    {"id": "top_left", "anchor": (0.21, 0.15), "zone_size": (420, 340),
     "enemies": ("tikbalang", "manananggal", "tiyanak_sinta") * 2},
)

# Core dirt tiles from Ground Layer 1 in basic.tmx. Grass is intentionally
# walkable for the player, so collision properties cannot identify paths.
BEGINNER_PATH_GIDS = frozenset((20, 21, 38, 39))
