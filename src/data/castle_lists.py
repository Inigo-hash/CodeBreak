"""Authored Dining lesson and return-value challenges. No runtime rules."""
from copy import deepcopy

LIST_CHALLENGE_IDS = ('castle_lists_inspect_001', 'castle_lists_update_001')
LISTS_TOPIC = {
    'id': 'castle_lists', 'title': 'Lists', 'difficulty': 'Intermediate',
    'challenge_id': LIST_CHALLENGE_IDS[0], 'challenge_ids': LIST_CHALLENGE_IDS,
    'requirements': [],
    'lesson': '''LISTS: ORDERED, CHANGEABLE COLLECTIONS
A list stores values in order: songs = ["Rain", "Sun", "Moon"].
Indexing starts at zero: songs[0] is "Rain". Negative indices count from
the end: songs[-1] is "Moon". len(songs) is 3.
Reading songs[0] or songs[-1] on [] raises IndexError. Check if songs:
or len(songs) > 0 before accessing an endpoint.

ADDING AND REMOVING
songs.append("Wind") adds one item at the end. It changes songs and returns
None: do not write songs = songs.append("Wind").
songs.remove("Sun") removes only the FIRST matching value. Missing values
raise ValueError, so check if "Sun" in songs: before removing it.
songs.pop() removes AND RETURNS the last item. pop(0) removes the first.
pop() raises IndexError if the list is empty BEFORE the call. Popping the
only item still returns that item even though the remaining list is [].
Lists can contain duplicates. Removing one does not remove all of them.

WORKED EXAMPLE: A MUSIC PLAYLIST
original = ["Rain", "Sun", "Rain"]
playlist = list(original)    # copy; original stays unchanged
print(playlist[0])          # Rain
print(playlist[-1])         # Rain
print(len(playlist))        # 3
playlist.append("Moon")    # ["Rain", "Sun", "Rain", "Moon"]
playlist.remove("Rain")    # ["Sun", "Rain", "Moon"]
encore = playlist.pop()     # "Moon"; playlist is ["Sun", "Rain"]

FUNCTION STARTER GUIDE
The challenges provide def and return scaffolding. Parameters are the
input names inside the function. Indent your steps under def. return
sends a value to the checker; printing alone does not return an answer.
return (first, last, count) groups three values in a tuple.
Functions will have their own full lesson later in the Castle.

DINING MASTERY
Pass BOTH Dining challenges to master Lists and earn Castle Key 1 once.
The first inspects a list; the second changes a COPY in a specified order.
Completed challenges can be replayed as practice with no extra keys.
The other four Castle key bundles and stage completion are not ready yet.
''',
}

LISTS_CHALLENGES = {
    LIST_CHALLENGE_IDS[0]: {
        'id': LIST_CHALLENGE_IDS[0], 'title': 'Dining Inventory Report',
        'difficulty': 'Intermediate', 'type': 'function',
        'function_name': 'describe_items', 'preserve_args': True,
        'problem': 'Write describe_items(items). Return (first, last, count). '
                   'For an empty list return (None, None, 0). Leave items unchanged. '
                   'Example: ["plate", "cup"] returns ("plate", "cup", 2).',
        'objective': 'Return the first item, last item, and length for any supplied list.',
        'starter_code': 'def describe_items(items):\n    # Check for an empty list before indexing.\n    # Return (first, last, count), not printed output.\n    pass',
        'hints': [
            'An empty list has no first or last item. Nonempty lists keep their order.',
            'Check the empty case first. Then use the first index, the last index, and len().',
            'def describe_items(items):\n    if not items:\n        return (..., ..., ...)\n    return (items[...], items[...], len(...))',
            'Use None for empty endpoints. A single item is both first and last; duplicates still count.',
        ],
        'function_cases': [
            {'args': [[]], 'expected': (None, None, 0)},
            {'args': [['plate']], 'expected': ('plate', 'plate', 1)},
            {'args': [['']], 'expected': ('', '', 1)},
            {'args': [[None, 0]], 'expected': (None, 0, 2)},
            {'args': [['plate', 'cup']], 'expected': ('plate', 'cup', 2)},
            {'args': [['cup', 'plate', 'cup']], 'expected': ('cup', 'cup', 3)},
            {'args': [[0, -1, 8, 0]], 'expected': (0, 0, 4)},
        ],
    },
    LIST_CHALLENGE_IDS[1]: {
        'id': LIST_CHALLENGE_IDS[1], 'title': 'Update the Dining Supplies',
        'difficulty': 'Intermediate', 'type': 'function',
        'function_name': 'update_items', 'preserve_args': True,
        'problem': 'Write update_items(items, added, removed). Copy items, append added, '
                   'remove the first matching removed if present, then pop the last item '
                   'if the copy is nonempty. Return (remaining_items, popped_item). '
                   'Use None only if empty BEFORE popping. Leave items unchanged. '
                   'Example: (["plate", "cup"], "bowl", "plate") returns (["cup"], "bowl").',
        'objective': 'Copy, append, remove the first matching value, pop safely, and return both results.',
        'starter_code': 'def update_items(items, added, removed):\n    # Work on a copy. Follow the requested order.\n    # Return (remaining_items, popped_item).\n    pass',
        'hints': [
            'Work on a copy so the caller keeps its original supplies. remove() affects one match.',
            'Copy, append, conditionally remove, then conditionally pop. Keep the popped value separately.',
            'def update_items(items, added, removed):\n    remaining = list(...)\n    remaining.append(...)\n    if ... in remaining:\n        ...\n    popped = None\n    if remaining:\n        ...\n    return (remaining, popped)',
            'If append adds the only item and remove removes it, skip pop. Otherwise even a one-item pop returns the item.',
        ],
        'function_cases': [
            {'args': [[], 'cup', 'missing'], 'expected': ([], 'cup')},
            {'args': [[], 'cup', 'cup'], 'expected': ([], None)},
            {'args': [['plate'], 'cup', 'plate'], 'expected': ([], 'cup')},
            {'args': [['plate'], 'cup', 'missing'], 'expected': (['plate'], 'cup')},
            {'args': [['cup', 'plate', 'cup'], 'bowl', 'cup'], 'expected': (['plate', 'cup'], 'bowl')},
            {'args': [['plate', 'cup'], 'bowl', 'bowl'], 'expected': (['plate'], 'cup')},
            {'args': [['plate', 'cup'], 'bowl', 'cup'], 'expected': (['plate'], 'bowl')},
        ],
    },
}


def lists_practice(challenge_id):
    result = deepcopy(LISTS_CHALLENGES[challenge_id])
    result['id'] = challenge_id.replace('castle_lists_', 'practice_lists_')
    result['title'] += ' - Practice (no rewards)'
    result['practice_only'] = True
    result['problem'] = result['problem'].replace('plate', 'book').replace('cup', 'scroll').replace('bowl', 'map')
    def replace(value):
        if isinstance(value, str):
            return {'plate': 'book', 'cup': 'scroll', 'bowl': 'map'}.get(value, value)
        if isinstance(value, list):
            return [replace(item) for item in value]
        if isinstance(value, tuple):
            return tuple(replace(item) for item in value)
        return value
    result['function_cases'] = [{'args': replace(case['args']), 'expected': replace(case['expected'])}
                                for case in result['function_cases']]
    return result
