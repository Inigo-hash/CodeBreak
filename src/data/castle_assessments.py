"""Intermediate final rotation: only concepts taught in Castle.

Limits are generous initial values for learner playtesting, not measured norms.
"""
CASTLE_FINAL_ID = 'castle_supply_final'
CASTLE_ASSESSMENT_IDS = ('castle_supply_final', 'castle_rooms_final', 'castle_manifest_final')


def _assessment(cid, title, name, parameters, problem, cases):
    return {
        'id': cid, 'title': title, 'difficulty': 'Intermediate Final',
        'type': 'function', 'function_name': name, 'preserve_args': True,
        'time_limit': 900, 'objective': 'Combine Castle collections, loops, functions and error handling.',
        'problem': problem + ' Leave input collections unchanged. Return your answer; printing is not enough.',
        'starter_code': f'def {name}({parameters}):\n    pass',
        'hints': ['Build the answer one record at a time.',
                  'Convert a quantity inside try/except; skip invalid values.',
                  'Use a dictionary accumulator and return after the loop.',
                  'Test empty input, duplicates and boundary quantities.'],
        'function_cases': [{'args': args, 'expected': expected} for args, expected in cases],
    }


CASTLE_ASSESSMENTS = {
    CASTLE_FINAL_ID: _assessment(CASTLE_FINAL_ID, 'Castle Supply Report', 'build_supply_report', 'records, minimum',
        'Write build_supply_report(records, minimum). records is a list of (item, raw_quantity) tuples. '
        'raw_quantity is a string or None. Convert it with int(); skip ValueError and TypeError. '
        'Keep quantities >= minimum, then total quantities by item in a dictionary. '
        'minimum is a nonnegative integer. Example: ([("ink", "3"), ("ink", "4"), ("paper", "bad")], 2) returns {"ink": 7}.',
        [([[],0],{}), ([[('ink','3'),('ink','4'),('paper','bad')],2],{'ink':7}),
         ([[('a',None),('a',''),('b','-1'),('c','0')],0],{'c':0}),
         ([[('a','2'),('b','3'),('a',' 5 ')],3],{'b':3,'a':5}),
         ([[('a','4')],4],{'a':4}), ([[('a','4')],5],{})]),
    'castle_rooms_final': _assessment('castle_rooms_final', 'Room Supply Audit', 'audit_rooms', 'rooms',
        'Write audit_rooms(rooms). rooms is a list of lists of (item, raw_quantity) tuples. '
        'Visit all rooms and records. Convert each string or None quantity with int(); skip ValueError/TypeError and negative quantities. '
        'Return a dictionary of totals by item, keeping valid zero quantities. '
        'Example: [[("key", "2")], [("key", "3"), ("ink", "bad")]] returns {"key": 5}.',
        [([[]],{}), ([[[],[]]],{}), ([[[('key','2')],[('key','3'),('ink','bad')]]],{'key':5}),
         ([[[('a',None),('b','-2')],[],[('b','0'),('a',' 7 ')]]],{'b':0,'a':7}),
         ([[[('a','1'),('b','2')],[('a','4')]]],{'a':5,'b':2})]),
    'castle_manifest_final': _assessment('castle_manifest_final', 'Sealed Manifest Report', 'read_manifest', 'records, stop',
        'Write read_manifest(records, stop). records is a list of (item, raw_quantity) tuples. '
        'Stop at the FIRST record whose item equals stop; exclude that record and everything after it. '
        'Before the stop, convert string or None quantities with int(); skip ValueError/TypeError and negative values. '
        'Return totals by item in a dictionary, keeping valid zero quantities. '
        'Example: ([("ink", "2"), ("END", "x"), ("ink", "9")], "END") returns {"ink": 2}.',
        [([[],'END'],{}), ([[('END','2'),('a','9')],'END'],{}),
         ([[('ink','2'),('END','x'),('ink','9')],'END'],{'ink':2}),
         ([[('a',None),('b','-3'),('b','0'),('a','4')],'STOP'],{'b':0,'a':4}),
         ([[('a','2'),('a','3'),('z','bad')],'END'],{'a':5})]),
}
