"""Minimal Stage 3 map entry.

Stage 3 is intentionally an exploration-only map for now. Its learning
curriculum, challenge definitions, boss arena, and encounter data were
removed; they can be authored again when the team is ready.
"""
from src.data.stage_music import STAGE_MUSIC


CITADEL_STAGE = {
    'id': 'citadel',
    'name': 'Citadel',
    'subtitle': 'Stage 3',
    'area_name': '',
    'next_stage': None,
    'playable': True,
    'progress': {'enabled': False},
    'world': {
        'map': 'assets/map/tmx/map3.tmx',
        **STAGE_MUSIC['citadel'],
        'night': False,
        # The red-X arrival point in map3.tmx (player top-left at tile 66, 72).
        'spawn': (66/80, 72/80),
        'resume_position': False,
        'zoom': 2.5,
        'follow_edges': True,
        'zones': (),
        'encounters': (),
        'map_layout_version': 2,
    },
    'manual': {
        'summary': '',
        'controls': {},
        'topics': (),
        'mechanics': [],
        'tips': [],
    },
    'enemies': [],
    'items': [],
    'completion': {
        'content_ready': False,
        'required_keys': 0,
    },
    'objectives': [],
}
