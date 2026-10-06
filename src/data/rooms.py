"""Stage room routes. Coordinates are tile units (16 px in these maps).

Rectangles are walkable approach zones, not the painted door arches.
Spawns use the player's top-left collision corner. Add a room and its
routes here without adding room-specific branches to the gameplay loop.
"""
ROOM_STAGES = {
    'castle': {
        'default': 'lobby',
        'zoom': 2.5,
        'follow_edges': True,
        'hold_seconds': 1.0,
        'rooms': {
            'lobby': {
                'name': 'Castle Lobby',
                'map': 'assets/map/tmx/map2_castle_lobby.tmx',
                'spawn': (23, 36),
                'routes': [
                    {'id': 'dining', 'rect': (6, 13, 5, 3), 'target': 'dining', 'arrival': 'entry', 'label': 'Enter Dining Area'},
                    {'id': 'throne', 'rect': (20, 9, 7, 3), 'target': 'throne', 'arrival': 'entry', 'label': 'Enter Throne Room'},
                    {'id': 'library', 'rect': (36, 13, 5, 3), 'target': 'library', 'arrival': 'entry', 'label': 'Enter Library'},
                    {'id': 'dungeon', 'rect': (5, 35, 5, 3), 'target': 'dungeon', 'arrival': 'entry', 'label': 'Enter Dungeon Prison'},
                ],
                'arrivals': {'dining': (8, 15), 'throne': (23, 11), 'library': (38, 15), 'dungeon': (7, 37)},
            },
            'dining': {
                'name': 'Dining Area', 'map': 'assets/map/tmx/map2_dining_area.tmx',
                'spawn': (19.5, 34), 'arrivals': {'entry': (19.5, 34)},
                'routes': [{'id': 'lobby', 'rect': (17.5, 33, 5, 3), 'target': 'lobby', 'arrival': 'dining', 'label': 'Go back to Castle Lobby'}],
            },
            'throne': {
                'name': 'Throne Room', 'map': 'assets/map/tmx/map2_throne_room.tmx',
                'spawn': (20, 33), 'arrivals': {'entry': (20, 33)},
                'routes': [{'id': 'lobby', 'rect': (17.5, 32, 5, 4), 'target': 'lobby', 'arrival': 'throne', 'label': 'Go back to Castle Lobby'}],
            },
            'library': {
                'name': 'Library', 'map': 'assets/map/tmx/map2_library.tmx',
                'spawn': (20, 37), 'arrivals': {'entry': (20, 37)},
                'routes': [{'id': 'lobby', 'rect': (17.5, 36, 5, 3), 'target': 'lobby', 'arrival': 'library', 'label': 'Go back to Castle Lobby'}],
            },
            'dungeon': {
                'name': 'Dungeon Prison', 'map': 'assets/map/tmx/map3_dungeon_prison.tmx',
                'spawn': (9, 35), 'arrivals': {'entry': (9, 35)},
                'routes': [{'id': 'lobby', 'rect': (7, 34, 5, 3), 'target': 'lobby', 'arrival': 'dungeon', 'label': 'Go back to Castle Lobby'}],
            },
        },
    },
}
