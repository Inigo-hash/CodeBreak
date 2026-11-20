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
        # Map 3 expanded from 80x80 to 120x120, adding 20 tiles on each
        # top/left side. The original red-X spawn therefore moved to tile (86, 92).
        'spawn': (86/120, 92/120),
        'resume_position': False,
        'zoom': 2.5,
        'follow_edges': True,
        'zones': (),
        'encounters': (),
        'map_layout_version': 3,
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
