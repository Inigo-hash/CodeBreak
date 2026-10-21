"""Playable appearances. Character choice never changes combat statistics."""
CHARACTERS = {
    'man': {
        'title': 'MALE EXPLORER', 'label': 'MAN',
        'description': 'A wandering adventurer ready to explore forgotten paths. Face folklore creatures and unlock new routes through Python.',
        'short_description': 'Explore forgotten paths.\nLearn Python as you fight.',
        'preview': 'assets/images/frames/main_character/idle/no_sword/idle_backward/frame_1.png',
    },
    'woman': {
        'title': 'FEMALE EXPLORER', 'label': 'WOMAN',
        'description': 'A determined adventurer setting out into the unknown. Explore the castle, master coding challenges, and forge your own path.',
        'short_description': 'Brave the unknown.\nSolve puzzles and explore.',
        'preview': 'assets/images/frames/girl_main_character/walking/south/frame_0.png',
    },
}


def character_id(value):
    return value if isinstance(value, str) and value in CHARACTERS else 'man'


def character_title(value):
    return CHARACTERS[character_id(value)]['title']
