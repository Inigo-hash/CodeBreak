"""Playable Citadel content: lessons, behavioral cases and the Lava Chamber.

Only authored data lives here. Examples use different stories from the graded
tasks; reference solutions belong in tests, never in the tutor's knowledge.
"""
from copy import deepcopy
from src.data.controls import WORLD_CONTROLS
from src.data.stage_music import STAGE_MUSIC

CITADEL_TOPICS = {}
CITADEL_CHALLENGES = {}


def _topic(key, title, lesson, tasks):
    tid = 'citadel_' + key
    previous = list(CITADEL_TOPICS)[-1:]
    ids = []
    for suffix, name, parameters, task_title, contract, hints, cases in tasks:
        cid = tid + '_' + suffix + '_001'
        ids.append(cid)
        CITADEL_CHALLENGES[cid] = {
            'id': cid, 'title': task_title, 'difficulty': 'Advanced',
            'type': 'function', 'function_name': name, 'preserve_args': True,
            'requirements': previous,
            'objective': contract,
            'problem': f'Write {name}({parameters}). {contract} '
                       'Leave every input collection unchanged. Return the result; printing is not enough.',
            'starter_code': f'def {name}({parameters}):\n    # Build and return the requested result.\n    pass',
            'hints': hints,
            'function_cases': [{'args': args, 'expected': expected} for args, expected in cases],
        }
    CITADEL_TOPICS[tid] = {
        'id': tid, 'title': title, 'difficulty': 'Advanced',
        'requirements': previous, 'challenge_id': ids[0], 'challenge_ids': tuple(ids),
        'lesson': lesson + '\n\nMASTERY\nPass both challenges for this topic to earn one Citadel key, once. '
                          'Practice and repeat submissions grant no additional keys. '
                          'Supplied def/return scaffolding follows the Castle Functions lesson.',
    }


_topic('comprehensions', 'List Comprehensions', '''BUILD A NEW LIST
A list comprehension combines a transformation, a loop and an optional filter:
[expression for value in values if condition]
Read the loop and condition first, then the expression. The filter decides
which original values to keep; the expression transforms each kept value.
An empty input or a filter that keeps nothing produces []. Order and duplicate
values are preserved. The original list is unchanged unless you mutate it.

WORKED EXAMPLE: BUS FARES
fares = [8, 0, 12, 8]
discounted = [fare - 2 for fare in fares if fare > 0]
# discounted is [6, 10, 6]; fares is still [8, 0, 12, 8].
This is equivalent to creating [], looping, checking fare > 0, then appending.
Use the longer loop when it is easier to understand; short code is not always clearer.

STRINGS IN COLLECTIONS
text.strip() removes surrounding whitespace, not internal spaces.
text.lower() returns a lowercase copy. Neither method changes the original string.
labels = ["  Rain ", " ", "SUN"]
clean = [label.strip().lower() for label in labels if label.strip()]
# clean is ["rain", "sun"]. Empty text is false in a condition.''', [
    ('squares', 'positive_squares', 'numbers', 'Filter the Ember Readings',
     'numbers is a list of integers. Return the squares of strictly positive values in original order, including duplicates. Zero and negatives are excluded.',
     ['Choose positive values before transforming them.', 'For each number > 0, calculate number * number.',
      'return [ ... for number in numbers if ... ]', '[] and a list containing only nonpositive values both produce [].'],
     [([[]], []), ([[0,-2]], []), ([[3,-1,2,3,0]], [9,4,9]), ([[1]], [1]), ([[-4,5]], [25])]),
    ('labels', 'clean_labels', 'labels', 'Restore the Chamber Labels',
     'labels is a list of strings. Strip surrounding whitespace, discard empty results, and lowercase each remaining string. Preserve order and duplicates.',
     ['Clean text before deciding whether it is blank.', 'Use strip(), skip empty results, then lower().',
      'cleaned = label.strip()\n# only add a nonempty cleaned value', 'Whitespace-only strings disappear; internal spaces and repeated labels remain.'],
     [([[]], []), ([[' ', '\t', '']], []), ([['  FIRE ', 'Ash', ' FIRE ', 'two WORDS']], ['fire','ash','fire','two words']),
      ([['x']], ['x']), ([['  0  ']], ['0'])]),
])

_topic('sets', 'Sets and Unique Values', '''SETS REMOVE DUPLICATES
A set stores distinct hashable values. set(["red", "blue", "red"]) contains
"red" and "blue" once each. set() is empty; {} is an empty dictionary.
A set has no positional indexing and its iteration order is not a contract.
Use sorted(a_set) when your answer must be an ordered LIST.
Our challenges use strings, so their values can be stored in sets.

WORKED EXAMPLE: CLUB MEMBERS
music = {"Ana", "Ben"}
art = {"Ben", "Cara"}
shared = music & art       # {"Ben"}: intersection
everyone = music | art    # all three distinct names: union
music_only = music - art  # {"Ana"}: difference
print(sorted(everyone))   # ['Ana', 'Ben', 'Cara']
The & and | operations create new sets. Avoid difference_update or other
mutating methods on a supplied set. Membership uses value equality.
String comparisons are case-sensitive: "Ash" and "ash" are distinct.''', [
    ('unique', 'unique_runes', 'runes', 'Catalog Unique Runes',
     'runes is a list of strings. Return a sorted list of its distinct strings, using ordinary Python alphabetical ordering. Comparison is case-sensitive.',
     ['Remove duplicates, then establish an order.', 'set(runes) keeps unique values; sorted(...) returns a list.',
      'unique = set(...)\nreturn sorted(...)', 'Do not return a set. Empty strings are valid rune values.'],
     [([[]], []), ([['b','a','b']], ['a','b']), ([['Ash','ash','Ash']], ['Ash','ash']), ([['','a','']], ['','a']), ([['z']], ['z'])]),
    ('shared', 'shared_runes', 'left, right', 'Match the Two Rune Seals',
     'left and right are lists of strings. Return a sorted list of distinct strings present in BOTH lists. Comparison is case-sensitive.',
     ['This asks for intersection, not union.', 'Convert each input to a set, intersect them, then sort.',
      'common = set(left) & ...\nreturn sorted(...)', 'If either input is empty or they share nothing, return [].'],
     [([[],[]], []), ([['a'],[]], []), ([['b','a','b'],['b','c','b']], ['b']),
      ([['c','a','b'],['a','c']], ['a','c']), ([['Ash'],['ash']], []), ([[''],['','']], [''])]),
])

_topic('sorting', 'Sorting and Key Functions', '''SORT A COPY WITH A KEY
sorted(records) creates a new list. list.sort() changes the list in place and
returns None. Use sorted when you must preserve input collections.
A key function selects what to compare. lambda record: record[1] is a short
function taking one record and returning its second field.

WORKED EXAMPLE: RUNNERS
runners = [("Mia", 14), ("Ana", 12), ("Ben", 12)]
by_time = sorted(runners, key=lambda record: record[1])
# [('Ana', 12), ('Ben', 12), ('Mia', 14)]
Sorting is stable: equal keys keep their original relative order.
A tuple key compares its first field, then its next field on a tie.
by_name_then_time = sorted(runners, key=lambda record: (record[0], record[1]))

For a higher-is-better numeric score with alphabetical tie-breaking, a key
(-record[1], record[0]) negates ONLY the score. reverse=True reverses all key
fields, which would also reverse alphabetical order on a tie.
Return the records themselves, not their keys or just their scores.''', [
    ('rank', 'rank_seals', 'records', 'Rank the Power Seals',
     'records contains (name, integer_score) tuples. Return a new list sorted by descending score, then ascending name for ties. Keep duplicate records.',
     ['There are two ordering rules.', 'Use a tuple key: negative score first, name second.',
      'return sorted(records, key=lambda record: (..., ...))', 'A tie must use ascending names; negative and zero scores are valid.'],
     [([[]], []), ([[('z',2)]], [('z',2)]), ([[('b',5),('a',5),('c',7)]], [('c',7),('a',5),('b',5)]),
      ([[('b',-1),('a',0),('b',-1)]], [('a',0),('b',-1),('b',-1)])]),
    ('stable', 'order_crates', 'records', 'Schedule the Supply Crates',
     'records contains (name, integer_weight) tuples. Return a new list in ascending weight order. Equal-weight records must keep their original relative order; do not sort ties by name.',
     ['Only weight is a sort key.', 'Python sorted is stable when keys are equal.',
      'return sorted(records, key=lambda record: record[...])', 'Test two different names with the same weight in deliberately reversed alphabetical order.'],
     [([[]], []), ([[('z',2),('a',2),('m',1)]], [('m',1),('z',2),('a',2)]),
      ([[('a',-1),('b',0),('c',-1)]], [('a',-1),('c',-1),('b',0)]), ([[('x',4)]], [('x',4)])]),
])

_topic('algorithms', 'Search and Aggregation', '''CHOOSE AN ALGORITHM FOR THE CONTRACT
A linear search visits records from left to right and returns on the first
match. If no match is found, return None after the loop. Do not confuse a
missing record with a stored zero. At most n records are inspected for n inputs.

WORKED EXAMPLE: LOOK UP A BOOK
def first_book(books, wanted):
    for title, pages in books:
        if title == wanted:
            return (title, pages)
    return None
# first_book([('Sea', 90), ('Sky', 120), ('Sea', 80)], 'Sea') -> ('Sea', 90)

GROUP TOTALS WITH A DICTIONARY
A dictionary maps unique keys to values: counts = {"tea": 2}.
counts["tea"] reads 2; counts["tea"] = 3 updates it. {} creates an empty dictionary.
counts.get("cake", 0) returns 0 when "cake" is absent; it preserves a stored zero.
Repeatedly scanning the whole list for every name performs unnecessary work.
Maintain one accumulator per name while visiting each record once.
sales = [('tea', '2'), ('tea', '3'), ('cake', 'bad')]
totals = {}
for name, raw in sales:
    try:
        amount = int(raw)
    except (ValueError, TypeError):
        continue
    totals[name] = totals.get(name, 0) + amount
# totals is {'tea': 5}; conversion failures do not discard valid records.
When excluding negatives, check amount after conversion. A valid zero should
still establish its name in the result. Return {} for no valid records.''', [
    ('search', 'find_first_seal', 'records, wanted', 'Find the First Matching Seal',
     'records contains (name, integer_power) tuples. Return the FIRST tuple whose name equals wanted, or None if absent. Names are case-sensitive and zero power is valid.',
     ['Search in input order.', 'Return the record immediately on a name match.',
      'for record in records:\n    if record[0] == wanted:\n        ...\n# handle no match after the loop', 'Do not return the last duplicate or treat a zero-power record as absent.'],
     [([[],'x'], None), ([[('x',0)],'x'], ('x',0)), ([[('x',3),('x',9)],'x'], ('x',3)),
      ([[('Ash',2)],'ash'], None), ([[('a',1),('b',2)],'z'], None)]),
    ('group', 'total_readings', 'records', 'Aggregate Valid Reactor Readings',
     'records contains (name, raw_power) tuples; raw_power is a string or None. Convert with int(), skip ValueError/TypeError and negative powers, and return totals by exact name as a dictionary. Keep valid zero-power names.',
     ['Convert and validate one record at a time.', 'Use try/except inside the loop, then add to totals.get(name, 0).',
      'totals = {}\nfor name, raw in records:\n    # convert, validate, then update this name\nreturn totals', 'None, invalid text and negatives are skipped; repeated names add together and zero stays valid.'],
     [([[]], {}), ([[('a','2'),('a','3'),('b','bad')]], {'a':5}),
      ([[('x',None),('x','-2'),('y','0'),('a',' 4 ')]], {'y':0,'a':4}),
      ([[('Ash','1'),('ash','2')]], {'Ash':1,'ash':2})]),
])

CITADEL_TOPIC_ORDER = tuple(CITADEL_TOPICS)
CITADEL_CHALLENGE_IDS = tuple(CITADEL_CHALLENGES)
CITADEL_BUNDLES = {
    tid + '_key': {'topics': [tid], 'challenges': topic['challenge_ids'], 'keys': 1}
    for tid, topic in CITADEL_TOPICS.items()
}


def citadel_practice(challenge_id):
    challenge = deepcopy(CITADEL_CHALLENGES[challenge_id])
    challenge.update(id='practice_' + challenge_id, practice_only=True,
                     title=challenge['title'] + ' - Practice (no rewards)')
    challenge['function_cases'].reverse()
    return challenge


CITADEL_FINAL_ID = 'citadel_restoration_final'
CITADEL_FINAL = {
    'id': CITADEL_FINAL_ID, 'title': 'Restore the Citadel Reactor', 'difficulty': 'Advanced Final',
    'type': 'function', 'function_name': 'restore_reactor', 'preserve_args': True,
    'time_limit': 1200,
    'objective': 'Normalize records, validate quantities, aggregate by name and rank the results.',
    'problem': '''Write restore_reactor(records, minimum).
records contains (name, raw_power) tuples. name is a string; raw_power is a string or None.
minimum is a nonnegative integer.
1. Strip and lowercase each name. Skip names that become empty.
2. Convert raw_power with int(). Skip ValueError/TypeError and negative powers.
3. Keep individual records whose converted power is >= minimum.
4. Sum kept powers by normalized name.
5. Return a LIST of (name, total) TUPLES, sorted by descending total, then ascending name for ties.
Preserve every input collection. Return [] if no records qualify. Keep a valid zero total when minimum is 0.
Filter individual records BEFORE grouping; several below-minimum records must not combine to qualify.
Example: ([(' FIRE ', '3'), ('fire', '4'), ('ash', 'bad'), ('water', '7')], 2)
returns [('fire', 7), ('water', 7)]. Names break the tie in ascending order.
Use only built-in Python; no imports or file access are needed.''',
    'starter_code': 'def restore_reactor(records, minimum):\n    # Normalize, validate, filter, aggregate, then sort.\n    pass',
    'hints': ['Plan the five steps separately.', 'Normalize a name before grouping; catch conversion failures per record.',
              'Use a dictionary for totals after applying the minimum filter.',
              'Return sorted dictionary items with descending totals and ascending name ties. Test empty input and zeros.'],
    'function_cases': [
        {'args': [[],0], 'expected': []},
        {'args': [[(' FIRE ','3'),('fire','4'),('ash','bad'),('water','7')],2], 'expected': [('fire',7),('water',7)]},
        {'args': [[('x','1'),('x','1'),('y','2')],2], 'expected': [('y',2)]},
        {'args': [[(' ', '9'),('x',None),('x','-1'),('Y','0')],0], 'expected': [('y',0)]},
        {'args': [[('B',' 5 '),('a','5'),('a','0')],0], 'expected': [('a',5),('b',5)]},
        {'args': [[('x','4')],5], 'expected': []},
        {'args': [[('x','4')],4], 'expected': [('x',4)]},
    ],
}

CITADEL_ZONES = (
    {'name': 'Reactor Arena', 'rect': (15/40,15/40,10/40,10/40), 'is_boss_zone': True,
     'gate_all_edges': True, 'movement_rect': (15/40,15/40,10/40,10/40)},
    {'name': 'West Ash Patrol', 'rect': (3/40,12/40,7/40,6/40)},
    {'name': 'East Ember Patrol', 'rect': (30/40,12/40,7/40,6/40)},
    {'name': 'Lava Chamber', 'rect': (0,0,1,1)},
)
CITADEL_ENCOUNTERS = tuple({
    'id': 'citadel_' + side + '_patrol', 'anchor': (x/40,15/40),
    'zone_size': (112,96), 'spawn_margin': 4, 'require_path': False,
    'enemies': enemies, 'detection_range': 128, 'chase_range': 192,
    'disengage_range': 176, 'return_tolerance': 6,
} for side, x, enemies in (
    ('west',6.5,('tikbalang','kapre_usikan')),
    ('east',33.5,('white_lady','kapre_usikan')),
))

CITADEL_STAGE = {
    'id': 'citadel', 'name': 'Citadel', 'subtitle': 'Stage 3 - Advanced', 'area_name': 'Lava Chamber',
    'next_stage': None, 'playable': True, 'progress': {'enabled': True},
    'world': {
        'map': 'assets/map/tmx/map3_lava_chamber.tmx', **STAGE_MUSIC['citadel'],
        'night': False, 'spawn': (19.5/40,36/40), 'zoom': 2.5, 'follow_edges': True,
        'combat_tier': 3, 'boss_spawn_margin': 8, 'zones': CITADEL_ZONES,
        'encounters': CITADEL_ENCOUNTERS, 'map_layout_version': 1,
    },
    'manual': {
        'summary': 'The Corrupted Citadel is the final chapter. Explore the Lava Chamber perimeter: '
                   'Comprehensions southwest, Sets west, Sorting east, then Search and Aggregation southeast. '
                   'Master eight challenges for four keys. Defeat the Flame Warden on the central reactor platform, '
                   'pass the restoration assessment, and use the northern seal to finish the campaign.',
        'controls': WORLD_CONTROLS, 'topics': CITADEL_CHALLENGE_IDS,
        'mechanics': [
            'Two challenges master each topic and grant one key once. Follow the terminal prerequisite order.',
            'Citadel keys are separate from Castle keys. Lessons, inventory and unspent bonus time carry over.',
            'Bright molten lava is solid terrain: use the stone bridges. Orange cracked stone is walkable.',
            'Optional patrols award bonus time, never keys. Cleared groups and opened supplies stay cleared in your save.',
            'All bridge approaches to the reactor are sealed until all four keys and eight challenges are complete.',
            'The Flame Warden uses a Kapre-based appearance, alternates normal and ultimate attacks, and grows more aggressive below 900 and 450 HP.',
            'Boss victory reveals a 20-minute final assessment. Up to 300 earned bonus seconds extend an attempt. '
            'Failed/interrupted attempts require untimed practice before retaking; boss victory remains saved.',
            'After passing, press E at the northern reactor seal. Your completed Citadel is saved before returning to the main menu.',
        ],
        'tips': ['The southern arrival and lower terminals are away from patrols.',
                 'Citadel attacks commit to their direction. Dodge sideways, wait for recovery, then counter.',
                 'Lit interiors do not provide fixed-torch healing. Retreat before committing to a fight; a stage handoff refills lives.'],
    },
    'enemies': ['tikbalang','white_lady','kapre_usikan','citadel_flame_warden'],
    'items': ['crate','mang_tahimik'],
    'completion': {
        'content_ready': True, 'required_keys': 4, 'required_boss': 'citadel_flame_warden',
        'required_final_challenge': CITADEL_FINAL_ID, 'final_assessment_ids': (CITADEL_FINAL_ID,),
        'practice_after_failure': True, 'mastery_bundles': CITADEL_BUNDLES,
        'topic_key_rewards': {cid: 0 for cid in CITADEL_CHALLENGE_IDS}, 'encounter_key_reward': 0,
        'exit_name': 'Citadel Restoration Seal', 'exit_rect': (19/40,12/40,2/40,2/40),
    },
    'objectives': [
        {'id': tid + '_mastery', 'text': 'Master ' + topic['title'] + '.', 'kind': 'topic', 'target': tid, 'optional': False}
        for tid, topic in CITADEL_TOPICS.items()
    ] + [
        {'id': 'citadel_warden', 'text': 'Defeat the Flame Warden on the reactor platform.', 'kind': 'defeat', 'target': 'citadel_flame_warden', 'optional': False},
        {'id': 'citadel_final', 'text': 'Pass the Citadel restoration assessment.', 'kind': 'challenge', 'target': CITADEL_FINAL_ID, 'optional': False},
    ] + [
        {'id': camp['id'], 'text': 'Clear the ' + side + ' patrol for bonus time.', 'kind': 'encounter', 'target': camp['id'], 'optional': True}
        for side, camp in zip(('west','east'), CITADEL_ENCOUNTERS)
    ],
}
