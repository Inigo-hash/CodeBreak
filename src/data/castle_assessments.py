"""Final rotation using the five currently mapped Castle topic groups.

No dictionaries, sets or sorting are needed until the Citadel teaches them.
Limits are generous starting values for learner playtesting.
"""
CASTLE_FINAL_ID = 'castle_supply_final'
CASTLE_ASSESSMENT_IDS = ('castle_supply_final', 'castle_rooms_final', 'castle_manifest_final')


def _assessment(cid, title, name, parameters, problem, cases):
    return {
        'id': cid, 'title': title, 'difficulty': 'Intermediate Final',
        'type': 'function', 'function_name': name, 'preserve_args': True,
        'time_limit': 900, 'objective': 'Combine Castle loops, lists, functions, tuples and error handling.',
        'problem': problem + ' Leave input collections unchanged. Return your answer; printing is not enough.',
        'starter_code': f'def {name}({parameters}):\n    pass',
        'hints': ['Visit each record in order.',
                  'Convert a quantity inside try/except ValueError; skip invalid text.',
                  'Keep your totals or result list outside the loop; return after processing.',
                  'Test empty input, duplicate names, invalid text and boundary quantities.'],
        'function_cases': [{'args': args, 'expected': expected} for args, expected in cases],
    }


CASTLE_ASSESSMENTS = {
    CASTLE_FINAL_ID: _assessment(CASTLE_FINAL_ID, 'Castle Supply Report', 'build_supply_report', 'records, minimum',
        'Write build_supply_report(records, minimum). records is a list of (item, raw_quantity) tuples. '
        'raw_quantity is always a string. Convert it with int(); skip ValueError. '
        'minimum is a nonnegative integer. Keep individual quantities >= minimum. '
        'Return a (total_quantity, valid_record_count) tuple for the kept records. Count repeated names as separate records. '
        'Example: ([("ink", "3"), ("ink", "4"), ("paper", "bad")], 2) returns (7, 2).',
        [([[],0],(0,0)), ([[('ink','3'),('ink','4'),('paper','bad')],2],(7,2)),
         ([[('a',''),('b','-1'),('c','0')],0],(0,1)),
         ([[('a','2'),('b','3'),('a',' 5 ')],3],(8,2)),
         ([[('a','4')],4],(4,1)), ([[('a','4')],5],(0,0))]),
    'castle_rooms_final': _assessment('castle_rooms_final', 'Room Supply Audit', 'audit_rooms', 'rooms',
        'Write audit_rooms(rooms). rooms is a list of lists of (item, raw_quantity) tuples. '
        'raw_quantity is always a string. For each room, convert with int(), skip ValueError and negative quantities, '
        'and calculate its total. Return one total per room in a list, in original room order. Empty rooms contribute 0. '
        'Example: [[("key", "2")], [("key", "3"), ("ink", "bad")]] returns [2, 3].',
        [([[]],[]), ([[[],[]]],[0,0]), ([[[('key','2')],[('key','3'),('ink','bad')]]],[2,3]),
         ([[[('a',''),('b','-2')],[],[('b','0'),('a',' 7 ')]]],[0,0,7]),
         ([[[('a','1'),('b','2')],[('a','4')]]],[3,4])]),
    'castle_manifest_final': _assessment('castle_manifest_final', 'Sealed Manifest Report', 'read_manifest', 'records, stop',
        'Write read_manifest(records, stop). records is a list of (item, raw_quantity) tuples. raw_quantity is a string. '
        'Stop at the FIRST record whose item equals stop; exclude it and everything after it. '
        'Before the stop, convert with int(); skip ValueError and negative quantities. '
        'Return a list of (item, converted_quantity) tuples in original order, keeping duplicates and zero. '
        'Example: ([("ink", "2"), ("END", "x"), ("ink", "9")], "END") returns [("ink", 2)].',
        [([[],'END'],[]), ([[('END','2'),('a','9')],'END'],[]),
         ([[('ink','2'),('END','x'),('ink','9')],'END'],[('ink',2)]),
         ([[('a','bad'),('b','-3'),('b','0'),('a','4')],'STOP'],[('b',0),('a',4)]),
         ([[('a','2'),('a','3'),('z','bad')],'END'],[('a',2),('a',3)])]),
}
