"""Castle completion follows the five lesson groups actually on its maps.

Equivalent completed legacy groups credit the replacement challenges on load.
Partial legacy groups never receive an unearned mastery key.
"""
from src.data.stage2_topics import (
    ITERATIVE_STRUCTURE_TOPIC, LISTS_STAGE2_TOPIC, FUNCTIONS_TOPIC,
    TUPLES_TOPIC, ERROR_HANDLING_TOPIC,
)
from src.data.castle_curriculum import CASTLE_TOPICS, CASTLE_TOPIC_ORDER
from src.data.castle_lists import LIST_CHALLENGE_IDS

CASTLE_MAPPED_TOPICS = (ITERATIVE_STRUCTURE_TOPIC, LISTS_STAGE2_TOPIC,
                        FUNCTIONS_TOPIC, TUPLES_TOPIC, ERROR_HANDLING_TOPIC)
CASTLE_MAPPED_ORDER = tuple(topic['id'] for topic in CASTLE_MAPPED_TOPICS)
CASTLE_MAPPED_CHALLENGES = tuple(cid for topic in CASTLE_MAPPED_TOPICS for cid in topic['challenge_ids'])
CASTLE_MAPPED_BUNDLES = {
    'castle_mapped_' + topic['id']: {
        'topics': [topic['id']], 'challenges': topic['challenge_ids'], 'keys': 1,
    } for topic in CASTLE_MAPPED_TOPICS
}
_old_loops = tuple(cid for tid in CASTLE_TOPIC_ORDER if tid in (
    'castle_for_loops','castle_while_loops','castle_nested_loops','castle_loop_control')
    for cid in CASTLE_TOPICS[tid]['challenge_ids'])
CASTLE_CHALLENGE_MIGRATIONS = tuple(
    {'requires': old, 'grants': topic['challenge_ids']}
    for old, topic in zip((
        _old_loops, LIST_CHALLENGE_IDS,
        CASTLE_TOPICS['castle_functions']['challenge_ids'],
        CASTLE_TOPICS['castle_tuples']['challenge_ids'],
        CASTLE_TOPICS['castle_exceptions']['challenge_ids'],
    ), CASTLE_MAPPED_TOPICS)
)
