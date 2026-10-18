"""Castle's remaining eight topics, behavioral cases, and mastery bundles.

Examples deliberately use different stories from the graded challenges.
Function scaffolding is supplied before Functions is assessed in the Throne.
"""
from copy import deepcopy
from src.data.castle_lists import LIST_CHALLENGE_IDS

CASTLE_TOPICS = {}
CASTLE_CHALLENGES = {}


def _topic(key, title, requirements, lesson, tasks):
    topic_id = 'castle_' + key
    ids = []
    for suffix, name, parameters, title_, contract, hints, cases in tasks:
        cid = f'{topic_id}_{suffix}_001'
        ids.append(cid)
        CASTLE_CHALLENGES[cid] = {
            'id': cid, 'title': title_, 'difficulty': 'Intermediate', 'type': 'function',
            'function_name': name, 'preserve_args': True, 'requirements': requirements,
            'problem': f'Write {name}({parameters}). {contract} Leave supplied collections unchanged.',
            'objective': contract,
            'starter_code': f'def {name}({parameters}):\n    # Return the requested value; do not just print it.\n    pass',
            'hints': hints,
            'function_cases': [{'args': args, 'expected': expected} for args, expected in cases],
        }
    CASTLE_TOPICS[topic_id] = {
        'id': topic_id, 'title': title, 'difficulty': 'Intermediate',
        'requirements': requirements, 'challenge_id': ids[0], 'challenge_ids': tuple(ids),
        'lesson': lesson + '\n\nMASTERY\nPass both challenges. Read each function contract and return the requested value.\nReplays and practice award no extra keys. Keys are earned for complete topic bundles.',
    }


_topic('tuples', 'Tuples', ['castle_lists'], '''TUPLES: ORDERED AND IMMUTABLE
A tuple groups related values: position = (4, 7). Indexing begins at zero;
position[0] is 4, position[-1] is 7, and len(position) is 2.
A one-item tuple needs a comma: (4,). () is empty. Check length before indexing.
Tuples cannot replace, append or remove items. position[0] = 9 raises TypeError.
Create a new tuple when you need a changed record. A tuple may contain a mutable
list, so immutable structure does not imply everything inside it is immutable.
Unpacking assigns a known number of fields: x, y = position.

WORKED EXAMPLE: A WEATHER RECORD
weather = ("Manila", 29)
city, temperature = weather
warmer = (city, temperature + 1)
# weather is still ("Manila", 29); warmer is ("Manila", 30).
For each challenge, the checker calls your supplied function with several records.''', [
    ('inspect', 'inspect_record', 'record', 'Archive Record Endpoints',
     'Return (first, last, count) for a tuple. For () return (None, None, 0).',
     ['Tuples have order but may be empty.', 'Handle () before indexing; use len().',
      'if not record: return (..., ..., ...)\n# otherwise use endpoints', 'A single field is both first and last.'],
     [([()], (None,None,0)), ([("seal",)], ('seal','seal',1)), ([(0,False,9)], (0,9,3)), ([("a","b")], ('a','b',2))]),
    ('replace', 'replace_quantity', 'record, quantity', 'Create an Updated Archive Record',
     'record is a two-field (item, old_quantity) tuple. Return a NEW (item, quantity) tuple.',
     ['Create a new tuple instead of changing record.', 'Keep the first field and replace the second.',
      'return (record[...], ...)', 'The return type must be tuple; a list is a different type.'],
     [([('ink',3),8], ('ink',8)), ([('paper',0),0], ('paper',0)), ([('',1),-2], ('',-2))]),
])

_topic('dictionaries', 'Dictionaries', ['castle_tuples'], '''DICTIONARIES: KEYS AND VALUES
stock = {"apple": 3, "pear": 2} associates unique keys with values.
stock["apple"] reads 3; stock["apple"] = 4 updates it. Assigning a new key adds it.
Reading a missing key with [] raises KeyError. stock.get("plum", 0) returns 0.
Use if key in stock: to test membership. len(stock) counts keys.
for key in stock: visits keys; for key, value in stock.items(): visits pairs.
A dict keeps insertion order, but our challenge comparisons ignore key order.
Copy with dict(stock) before changing a supplied dictionary.

WORKED EXAMPLE: VOTES
votes = {"blue": 2}
for color in ["blue", "red", "blue"]:
    votes[color] = votes.get(color, 0) + 1
# {"blue": 4, "red": 1}
for color, count in votes.items():
    print(color, count)
The for statement is introduced here; its full lesson follows in the Dungeon.''', [
    ('lookup', 'lookup_stock', 'stock, item', 'Read the Archive Stock',
     'Return the quantity for item, or 0 when item is missing. Preserve actual stored zero or negative values.',
     ['A missing key and a stored zero are different cases.', 'Use get with a default or test membership.',
      'return stock.get(..., ...)', 'Do not use a default that replaces an existing negative value.'],
     [([{},'ink'],0), ([{'ink':0},'ink'],0), ([{'ink':-2},'ink'],-2), ([{'ink':4},'paper'],0), ([{'ink':4},'ink'],4)]),
    ('count', 'count_items', 'items', 'Count Repeated Archive Items',
     'Return a dictionary mapping each string in items to its occurrence count. [] returns {}.',
     ['Repeated names must increase the same counter.', 'Start with {}, visit each item, add one to its previous count.',
      'counts = {}\nfor item in items:\n    counts[item] = ...\nreturn counts', 'Use get(item, 0) to start new counters.'],
     [([[]],{}), ([['ink']],{'ink':1}), ([['ink','paper','ink']],{'ink':2,'paper':1}), ([['','']],{'':2})]),
])

_topic('for_loops', 'For Loops', ['castle_dictionaries'], '''FOR LOOPS: VISIT EACH VALUE
for value in collection: repeats an indented body once for each value.
range(stop) produces 0 through stop-1. range(start, stop, step) supports steps.
An empty collection runs the body zero times. Initialize results before the loop.
An accumulator keeps a running result. Do not reset it inside the body.

WORKED EXAMPLE: TRAVEL COST
costs = [12, 8, 5]
total = 0
for cost in costs:
    total = total + cost
# total is 25
labels = []
for number in range(1, 4):
    labels.append(number * 10)
# labels is [10, 20, 30]. The stop 4 is excluded.''', [
    ('total', 'total_supplies', 'quantities', 'Total Cell Supplies',
     'Return the sum of the integers in quantities, including negative adjustments. [] returns 0.',
     ['Keep a running total.', 'Initialize total to zero before traversal.', 'total = 0\nfor quantity in quantities:\n    total += ...\nreturn total', 'Do not skip negative quantities.'],
     [([[]],0), ([[7]],7), ([[4,-3,2]],3), ([[0,0]],0)]),
    ('labels', 'cell_labels', 'count', 'Number the Cells',
     'Return a list of integers from 1 through count inclusive. count is a nonnegative integer; 0 returns [].',
     ['The first cell is 1, not 0.', 'range excludes its stop.', 'labels = []\nfor number in range(..., ...):\n    labels.append(...)\nreturn labels', 'Include count itself.'],
     [([0],[]), ([1],[1]), ([4],[1,2,3,4]), ([7],[1,2,3,4,5,6,7])]),
])

_topic('while_loops', 'While Loops', ['castle_for_loops'], '''WHILE LOOPS: REPEAT WHILE A CONDITION IS TRUE
A while loop checks its condition before every iteration. It may run zero times.
The body must change something that can eventually make the condition false.
Otherwise the sandbox reports that your code took too long.

WORKED EXAMPLE: SAVING COINS
coins = 2
days = 0
while coins < 11:
    coins += 3
    days += 1
# coins is 11 and days is 3.
Use < when reaching the target is enough; <= would perform an extra iteration.
Be careful with zero or negative increments: they may prevent termination.''', [
    ('charge', 'charge_steps', 'current, target, step', 'Charge the Cell Switch',
     'step is a positive integer. Return how many additions of step are needed for current >= target. Return 0 if already there.',
     ['Count additions until the target is met.', 'Use a counter and update current each time.', 'steps = 0\nwhile current < target:\n    current += ...\n    steps += ...\nreturn steps', 'Overshooting the target still counts as reaching it.'],
     [([0,0,2],0), ([9,4,2],0), ([0,7,3],3), ([-3,3,2],3), ([2,11,3],3)]),
    ('countdown', 'countdown', 'start', 'Countdown for the Cell Door',
     'start is nonnegative. Return [start, start-1, ..., 1]. For 0 return []. Do not include 0.',
     ['Stop before zero.', 'Append the current number then decrease it.', 'result = []\nwhile start > ...:\n    ...\nreturn result', 'Without decrementing start the loop never ends.'],
     [([0],[]), ([1],[1]), ([4],[4,3,2,1]), ([6],[6,5,4,3,2,1])]),
])

_topic('nested_loops', 'Nested Loops', ['castle_while_loops'], '''NESTED LOOPS: TRAVERSE ROWS AND THEIR VALUES
An inner loop runs completely for each iteration of its outer loop.
A list of rows can have unequal lengths or empty rows. Visit the actual values
rather than assuming every row has the length of the first one.

WORKED EXAMPLE: CLASSROOM SEATS
seats = []
for row in range(2):
    for column in range(3):
        seats.append((row, column))
# [(0,0), (0,1), (0,2), (1,0), (1,1), (1,2)]
For R rows and C columns, this body runs R*C times. A zero dimension gives no pairs.
For a list of lists, use for row in rows: then for value in row:.''', [
    ('flatten', 'flatten_cells', 'rows', 'Read Every Cell Row',
     'Return one list containing every value of rows in row order. Preserve duplicates; empty rows add nothing.',
     ['Each outer value is another list.', 'Append each inner value to one result.', 'result = []\nfor row in rows:\n    for value in row:\n        ...\nreturn result', 'Do not return the nested rows unchanged.'],
     [([[]],[]), ([[[],[]]],[]), ([[[1,2],[],[3]]],[1,2,3]), ([[['a'],['a','b']]],['a','a','b'])]),
    ('coordinates', 'cell_coordinates', 'rows, columns', 'Map the Cell Coordinates',
     'Return (row, column) tuples in row-major order, using zero-based indices. Both dimensions are nonnegative.',
     ['Visit all columns for each row.', 'Use nested ranges and append a tuple.', 'for row in range(rows):\n    for column in range(columns):\n        ...', 'One zero dimension means an empty result.'],
     [([0,3],[]), ([2,0],[]), ([1,1],[(0,0)]), ([2,3],[(0,0),(0,1),(0,2),(1,0),(1,1),(1,2)])]),
])

_topic('loop_control', 'Break and Continue', ['castle_nested_loops'], '''BREAK AND CONTINUE
break exits the nearest loop immediately. Values after a stop signal are not processed.
continue skips the rest of the current iteration and starts the next one.
In a while loop, make needed updates before continue so the loop can terminate.
In nested loops, break exits only the inner loop that contains it.

WORKED EXAMPLE: SENSOR READINGS
accepted = []
for reading in [3, -2, 5, 0, 9]:
    if reading == 0:
        break
    if reading < 0:
        continue
    accepted.append(reading)
# accepted is [3, 5]; the reading 9 is after the stop signal.''', [
    ('stop', 'before_stop', 'items, stop', 'Obey the Prison Stop Signal',
     'Return a list of all items before the FIRST item equal to stop. Exclude stop and everything after it. If absent return a copy of all items.',
     ['The first stop ends traversal.', 'Check the sentinel before appending.', 'for item in items:\n    if item == stop:\n        break\n    ...', 'Stop may be the first item or may never occur.'],
     [([[],0],[]), ([[0,1],0],[]), ([[1,2,0,3,0],0],[1,2]), ([[1,2],9],[1,2])]),
    ('skip', 'positive_before_stop', 'numbers', 'Skip Invalid Cell Readings',
     'Visit integers until the first 0. Skip negative values and return only positive values before that 0. If there is no 0, process every value.',
     ['Zero stops; negatives only skip.', 'Check zero first, then negatives.', 'if number == 0:\n    break\nif number < 0:\n    continue', 'A negative number must not end the whole loop.'],
     [([[]],[]), ([[0,5]],[]), ([[-2,4,-1,7,0,9]],[4,7]), ([[-2,-1]],[]), ([[3,4]],[3,4])]),
])

_topic('functions', 'Functions', ['castle_loop_control'], '''FUNCTIONS: PARAMETERS AND RETURN VALUES
def names a reusable block. Parameters receive arguments each time it is called.
Indent the function body. return sends a result to its caller and ends the call.
Without return a function returns None. print displays text; it does not return it.
Variables created inside a function are local to that call. Avoid hidden global state.
A helper function can be called from another function to reuse a calculation.

WORKED EXAMPLE: DELIVERY COST
def delivery_cost(distance, rate):
    return distance * rate

def trip_cost(distances, rate):
    total = 0
    for distance in distances:
        total += delivery_cost(distance, rate)
    return total

# trip_cost([2, 3], 4) returns 20.
A function should work for different inputs, including empty collections.''', [
    ('price', 'supply_cost', 'quantity, price', 'Price the Throne Supplies',
     'Return quantity multiplied by price. Both inputs are nonnegative integers; zero is valid.',
     ['Use the parameters rather than fixed numbers.', 'Return the product, do not only print it.', 'def supply_cost(quantity, price):\n    return ...', 'The checker calls the same function with different inputs.'],
     [([0,8],0), ([4,0],0), ([3,7],21), ([1,9],9)]),
    ('invoice', 'invoice_total', 'quantities, price', 'Build the Throne Invoice',
     'Return the total cost of all nonnegative quantities at the shared price. Define and CALL a helper named line_cost(quantity, price) for each quantity. Empty quantities returns 0.',
     ['Use a helper for one line, then accumulate lines.', 'Define line_cost separately and call it from invoice_total.', 'def line_cost(quantity, price):\n    ...\ndef invoice_total(quantities, price):\n    ...', 'Return the accumulated total after visiting all quantities.'],
     [([[],5],0), ([[2],4],8), ([[2,0,3],5],25), ([[1,4],0],0)]),
])

_topic('exceptions', 'Try and Except', ['castle_functions'], '''ERROR HANDLING: TRY AND EXCEPT
int("12") returns 12; int("twelve") raises ValueError. Some invalid types raise TypeError.
A try block contains the operation that may fail. except ValueError: handles
that error without stopping the program. except (ValueError, TypeError): handles both.
Keep the try block narrow. Avoid bare except: because it hides unrelated mistakes.
After an exception the rest of that try block is skipped; execution resumes after its handler.

WORKED EXAMPLE: TICKET COUNTS
total = 0
for text in ["4", "bad", "6"]:
    try:
        count = int(text)
    except ValueError:
        continue
    total += count
# total is 10. The invalid text was skipped, not treated as a fatal error.
Boundary cases include empty text, surrounding spaces, negative values, and None.''', [
    ('parse', 'parse_quantity', 'raw', 'Read a Safe Supply Quantity',
     'raw is a string or None. Return int(raw) when conversion succeeds; return 0 for ValueError or TypeError. Keep valid negative values.',
     ['Conversion can fail; guard it.', 'Catch both ValueError and TypeError.', 'try:\n    return int(...)\nexcept (..., ...):\n    return ...', 'None and empty text are invalid; " 7 " is valid.'],
     [(['12'],12), (['bad'],0), ([''],0), ([None],0), (['-3'],-3), ([' 7 '],7)]),
    ('total', 'valid_quantity_total', 'values', 'Total Only Valid Quantities',
     'values contains strings or None. Convert each with int(), skip ValueError/TypeError, and sum valid integers (including negatives). [] returns 0.',
     ['One invalid item must not discard the entire list.', 'Put try/except inside the loop.', 'for raw in values:\n    try:\n        ...\n    except (ValueError, TypeError):\n        continue', 'Initialize total outside the loop and return after it.'],
     [([[]],0), ([['2','bad','3']],5), ([[None,'','-4',' 6 ']],2), ([['x']],0)]),
])

# Deliberate syntax targets supplement behavioral checks only for the lessons
# explicitly teaching those constructs. Other equivalent implementations pass.
for _key in ('for_loops', 'while_loops', 'nested_loops', 'loop_control', 'exceptions'):
    for _cid in CASTLE_TOPICS['castle_' + _key]['challenge_ids']:
        CASTLE_CHALLENGES[_cid]['learning_construct'] = _key
CASTLE_CHALLENGES['castle_functions_invoice_001']['required_helper'] = 'line_cost'

CASTLE_TOPIC_ORDER = ('castle_lists', *CASTLE_TOPICS)
CASTLE_CHALLENGE_IDS = (*LIST_CHALLENGE_IDS, *CASTLE_CHALLENGES)
CASTLE_BUNDLES = {
    'castle_lists_key_1': {'topics': ['castle_lists'], 'challenges': LIST_CHALLENGE_IDS, 'keys': 1},
}
for _number, _keys in enumerate((('tuples','dictionaries'), ('for_loops','while_loops'),
                                ('nested_loops','loop_control'), ('functions','exceptions')), 2):
    _topics = ['castle_' + key for key in _keys]
    CASTLE_BUNDLES[f'castle_bundle_key_{_number}'] = {
        'topics': _topics, 'challenges': tuple(cid for tid in _topics for cid in CASTLE_TOPICS[tid]['challenge_ids']), 'keys': 1,
    }


def castle_practice(challenge_id):
    """Separate identity and extra cases; practice never writes campaign rewards."""
    result = deepcopy(CASTLE_CHALLENGES[challenge_id])
    result.update(id='practice_' + challenge_id, practice_only=True,
                  title=result['title'] + ' - Practice (no rewards)')
    result['function_cases'].reverse()
    return result
