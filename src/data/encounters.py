"""Adjustable encounter layout for the Beginner/Island stage.

Anchors are normalized map coordinates copied from the marked reference map.
The spawn resolver moves each member to nearby walkable ground at runtime.
"""

# Castle rooms use the same persistent encounter groups as the Island.
# Patrol rectangles are in tile units, converted by rooms.py for each map.
CASTLE_ROOM_CAMPS = {
    'lobby': (
        ('castle_lobby_west_01', 'West Hall Guards', (2, 18, 10, 5)),
        ('castle_lobby_east_01', 'East Hall Guards', (34, 18, 10, 5)),
    ),
    'dining': (
        ('castle_dining_duwende_01', 'Dining Supply Camp', (25, 14, 11, 12)),
        ('castle_dining_north_01', 'Dining North Guards', (3, 11, 13, 9)),
    ),
    'throne': (
        ('castle_throne_north_01', 'Throne West Guards', (3, 23, 12, 5)),
        ('castle_throne_east_01', 'Throne East Guards', (24, 23, 12, 5)),
    ),
    'library': (
        ('castle_library_north_01', 'Library Upper Aisle Guards', (3, 11, 13, 7)),
        ('castle_library_east_01', 'Library Lower Aisle Guards', (24, 27, 12, 7)),
    ),
    'dungeon': (
        ('castle_dungeon_west_01', 'Dungeon West Guards', (3, 10, 8, 8)),
        ('castle_dungeon_inner_01', 'Dungeon Inner Hall Guards', (12, 10, 8, 8)),
    ),
}


def castle_room_encounters(room_id, width=40, height=40):
    encounters = []
    for camp_id, name, (x, y, w, h) in CASTLE_ROOM_CAMPS[room_id]:
        encounters.append({
            'id': camp_id, 'anchor': ((x + w / 2) / width, (y + h / 2) / height),
            'zone_size': (w * 16, h * 16), 'spawn_margin': 8,
            'require_path': False, 'enemies': (
                ('duwende_mandurug', 'kapre_usikan') if room_id in ('lobby', 'dining', 'dungeon')
                else ('white_lady', 'kapre_usikan')),
            'detection_range': 144, 'chase_range': 240, 'disengage_range': 208,
            'return_tolerance': 6,
        })
    # Retain the original Dining camp's authored formation and saved IDs.
    if room_id == 'dining':
        encounters[0].update(anchor=(0.8, 0.425), spawn_margin=16)
    return tuple(encounters)


def castle_room_zones(room_id, room_name, width=40, height=40):
    return [{'name': name, 'rect': (x / width, y / height, w / width, h / height)}
            for _, name, (x, y, w, h) in CASTLE_ROOM_CAMPS[room_id]] + [
                {'name': room_name, 'rect': (0, 0, 1, 1)}]


CASTLE_DINING_ENCOUNTERS = castle_room_encounters('dining')

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

# Core dirt tiles from Ground Layer 1 in map1.tmx.
# walkable for the player, so collision properties cannot identify paths.
BEGINNER_PATH_GIDS = frozenset((20, 21, 38, 39))
