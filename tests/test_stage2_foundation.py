"""Room isolation and stage-authored assessment contracts."""
import copy
import random
import unittest
from unittest.mock import patch
from src.data.rooms import ROOM_STAGES
from src.data.stages import get_stage
from src.data.final_assessments import ASSESSMENT_IDS, assessment_ids_for_stage, get_final_assessment
from src.data.challenges import CHALLENGES
from src.systems.rooms import world_for_room, transition_room, stage_defeated_enemies
from src.systems.final_assessment import peek_assessment, start_attempt, finish_attempt


class Stage2FoundationTests(unittest.TestCase):
    def test_room_encounters_can_be_authored_without_leaking_lobby(self):
        world = {'encounters': ({'id': 'lobby_camp'},), 'zones': [], 'map': 'lobby'}
        dining = ROOM_STAGES['castle']['rooms']['dining']
        content = {'encounters': [{'id': 'castle_dining_guard'}], 'zones': [{'name': 'Tables'}]}
        with patch.dict(dining, world=content):
            selected = world_for_room('castle', world, {'room_id': 'dining'})
            self.assertEqual(selected['encounters'][0]['id'], 'castle_dining_guard')
            selected['encounters'][0]['id'] = 'changed'
            self.assertEqual(content['encounters'][0]['id'], 'castle_dining_guard')
        self.assertTrue(all(e['id'].startswith('castle_library_') for e in world_for_room('castle', world, {'room_id': 'library'})['encounters']))
        self.assertEqual(world['encounters'][0]['id'], 'lobby_camp')

    def test_transitions_keep_global_rewards_and_each_room_checkpoint(self):
        state = {'room_id': 'dining', 'keys': 1, 'challenges_passed': ['lists'],
                 'stage_progress': {'cleared_encounters': ['dining_guard'], 'opened_interactables': ['table']},
                 'map_position': [100, 100]}
        before = copy.deepcopy(state)
        lobby = transition_room(state, 'castle', 'lobby')
        returned = transition_room(lobby, 'castle', 'dining')
        self.assertEqual(returned['keys'], 1)
        self.assertEqual(returned['challenges_passed'], ['lists'])
        self.assertEqual(returned['stage_progress'], state['stage_progress'])
        self.assertEqual(returned['map_position'], [19.5 * 16, 34 * 16])
        self.assertEqual(state, before)

    def test_gate_sees_other_room_boss_but_ignores_stale_active_checkpoint(self):
        state = {'room_id': 'lobby', 'stage_progress': {'defeated_enemies': ['guard']},
                 'room_checkpoints': {
                     'throne': {'stage_progress': {'defeated_enemies': ['warden']}},
                     'lobby': {'stage_progress': {'defeated_enemies': ['stale']}}}}
        self.assertEqual(stage_defeated_enemies(state), {'guard', 'warden'})

    def test_stage1_rotation_remains_and_empty_castle_is_not_completed(self):
        self.assertEqual(assessment_ids_for_stage(get_stage('island')), ASSESSMENT_IDS)
        self.assertEqual(assessment_ids_for_stage(get_stage('castle')), ())
        self.assertIsNone(peek_assessment({}, assessment_ids=()))

    def test_stage2_pool_isolated_and_attempt_records_persist(self):
        authored = {'id': 'stage2_final', 'title': 'Castle Report', 'time_limit': 600}
        stage = {'id': 'castle', 'completion': {'required_final_challenge': 'stage2_final'}}
        session = {'remaining': ['stage1_final_001']}
        with patch.dict(CHALLENGES, stage2_final=authored):
            challenge = peek_assessment(session, random.Random(4), assessment_ids_for_stage(stage))
            self.assertEqual(challenge['id'], 'stage2_final')
            active = start_attempt(session, challenge, now=100)
            self.assertEqual(active['deadline'], 700)
            finish_attempt(session, 'passed', now=120)
            self.assertEqual(session['history'][0]['challenge_id'], 'stage2_final')
            self.assertIsNone(session.get('active'))
            self.assertEqual(peek_assessment(session, assessment_ids=('stage2_final',))['id'], 'stage2_final')
            challenge['title'] = 'mutated'
            self.assertEqual(CHALLENGES['stage2_final']['title'], 'Castle Report')

    def test_stage2_assessment_screen_marks_stage2_completion(self):
        from src.screens.final_assessment import open_final_assessment
        stage = {'id': 'castle', 'name': 'Castle', 'manual': {'topics': ['lists']},
                 'completion': {'required_keys': 1, 'required_boss': 'warden',
                                'required_final_challenge': 'stage2_final'}}
        state = {'keys': 1, 'challenges_passed': ['lists'], 'room_id': 'lobby',
                 'room_checkpoints': {'throne': {'stage_progress': {'defeated_enemies': ['warden']}}}}
        class Screen:
            def copy(self):
                return self
        class Editor:
            timed_out = False
            solved = False
            def __init__(self, *args, **kwargs):
                self.commit = kwargs['on_assessment_pass']
            def run(self):
                self.solved = True
                self.commit()
        sessions = {}
        passed = []
        with patch.dict(CHALLENGES, stage2_final={'id': 'stage2_final', 'title': 'Report', 'time_limit': 600}), \
                patch('src.screens.final_assessment.assessment_dialog', return_value=True), \
                patch('src.screens.final_assessment.CodeEditor', Editor):
            self.assertTrue(open_final_assessment(Screen(), stage, state, sessions,
                                                  lambda: None, lambda: passed.append('stage2_final')))
        self.assertEqual(passed, ['stage2_final'])
        self.assertNotIn('island', sessions)
        self.assertEqual(sessions['castle']['history'][0]['result'], 'passed')


if __name__ == '__main__':
    unittest.main()
