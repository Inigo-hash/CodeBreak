"""Castle curriculum, real-map reachability, persistence, assessment retakes."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from collections import deque
from copy import deepcopy
import tempfile
import unittest
from unittest.mock import patch
import pygame
from pytmx.util_pygame import load_pygame
from castle_solutions import CASTLE_SOLUTIONS
from test_stage2_dining import SOLUTIONS
from src.data.castle_curriculum import CASTLE_TOPICS, CASTLE_CHALLENGES, CASTLE_TOPIC_ORDER
from src.data.castle_assessments import CASTLE_ASSESSMENTS, CASTLE_ASSESSMENT_IDS, CASTLE_FINAL_ID
from src.data.stages import get_stage
from src.data.topics import TOPICS
from src.data.rooms import ROOM_STAGES
from src.learning.challenge_manager import ChallengeManager
from src.data.practice_templates import PRACTICE_TEMPLATE_IDS, generate_practice_challenge
from src.systems.topic_mastery import complete_topic_challenge, reconcile_mastery
from src.systems.stage_gate import evaluate_stage_gate, evaluate_boss_access
from src.systems.rooms import transition_room
from src.systems.final_assessment import start_attempt, finish_attempt, settle_interrupted
from src.systems import save_manager
from src.screens import game
from src.screens.final_assessment import open_final_assessment


class CastleCurriculumTests(unittest.TestCase):
    def test_all_solutions_practice_and_wrong_returns(self):
        manager = ChallengeManager()
        for cid, challenge in {**CASTLE_CHALLENGES, **CASTLE_ASSESSMENTS}.items():
            with self.subTest(cid=cid):
                self.assertTrue(manager.validate(challenge, CASTLE_SOLUTIONS[cid])[0])
                wrong = f"def {challenge['function_name']}(*args):\n    return None"
                self.assertFalse(manager.validate(challenge, wrong)[0])
        for tid, topic in CASTLE_TOPICS.items():
            self.assertEqual(len(PRACTICE_TEMPLATE_IDS[tid]), 2)
            for cid in topic['challenge_ids']:
                challenge = generate_practice_challenge(cid)
                self.assertTrue(challenge['practice_only'])
                self.assertTrue(manager.validate(challenge, CASTLE_SOLUTIONS[cid])[0])

    def test_mastery_is_per_topic_while_keys_require_whole_bundle(self):
        stage = get_stage('castle')
        state = {'stage': 'Castle', 'keys': 0, 'challenges_passed': [], 'topics_completed': []}
        for index, tid in enumerate(CASTLE_TOPIC_ORDER):
            for required in TOPICS[tid]['requirements']:
                self.assertIn(required, state['topics_completed'])
            for cid in TOPICS[tid]['challenge_ids']:
                state = complete_topic_challenge(state, stage, tid, cid)
            self.assertIn(tid, state['topics_completed'])
            self.assertEqual(state['keys'], (index + 2) // 2)
            self.assertEqual(reconcile_mastery(state, stage), state)
        self.assertEqual(state['keys'], 5)
        self.assertEqual(len(state['mastery_reward_claims']), 5)
        self.assertTrue(evaluate_boss_access(stage, 5, state['challenges_passed']).unlocked)
        self.assertFalse(evaluate_stage_gate(stage, 5, state['challenges_passed'], ['zombie_aktan']).unlocked)
        state['challenges_passed'].append(CASTLE_FINAL_ID)
        self.assertFalse(evaluate_stage_gate(stage, 5, state['challenges_passed']).unlocked)
        self.assertTrue(evaluate_stage_gate(stage, 5, state['challenges_passed'], ['zombie_aktan']).unlocked)
        state.update(room_id='throne', stage_progress={'defeated_enemies':['zombie_aktan']})
        lobby = transition_room(state, 'castle', 'lobby')
        restored = transition_room(lobby, 'castle', 'throne')
        with tempfile.TemporaryDirectory() as tmp, patch.object(save_manager, 'SAVE_DIR', tmp):
            save_manager.save_slot(1, restored)
            self.assertEqual(save_manager.load_slot(1), restored)
        self.assertEqual(restored['stage_progress']['defeated_enemies'], ['zombie_aktan'])
        self.assertEqual(reconcile_mastery(restored, stage), restored)

    def test_syntax_requirements_are_not_substituted_for_return_checks(self):
        manager = ChallengeManager()
        challenge = CASTLE_CHALLENGES['castle_while_loops_charge_001']
        self.assertFalse(manager.validate(challenge, 'def charge_steps(current, target, step):\n    while False:\n        pass\n    return 0')[0])
        challenge = CASTLE_CHALLENGES['castle_functions_invoice_001']
        self.assertFalse(manager.validate(challenge, 'def invoice_total(quantities, price):\n    return sum(quantities) * price')[0])


class CastleMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280,720))

    def test_every_topic_terminal_and_throne_exit_are_reachable(self):
        found = set()
        room_topics = {
            'lobby': set(),
            'dining': {'castle_lists'},
            'library': {'castle_tuples', 'castle_dictionaries'},
            'dungeon': {'castle_for_loops', 'castle_while_loops',
                        'castle_nested_loops', 'castle_loop_control'},
            'throne': {'castle_functions', 'castle_exceptions'},
        }
        terminal_ids = set()
        for rid, room in ROOM_STAGES['castle']['rooms'].items():
            tmx = load_pygame(room['map'])
            blockers = game.object_collision_rects(tmx) + [pygame.Rect(x*16,y*16,16,16)
                for layer in tmx.visible_layers if hasattr(layer,'data') for x,y,gid in layer
                if gid and (tmx.get_tile_properties_by_gid(gid) or {}).get('collidable')]
            start = tuple(round(value*16) for value in room['spawn'])
            seen = {start}; queue = deque([start])
            bounds = pygame.Rect(0,0,tmx.width*16,tmx.height*16)
            while queue:
                x,y = queue.popleft()
                for dx,dy in ((8,0),(-8,0),(0,8),(0,-8)):
                    point = (x+dx,y+dy); body = pygame.Rect(*point,16,16)
                    if point not in seen and bounds.contains(body) and body.collidelist(blockers)<0:
                        seen.add(point); queue.append(point)
            bodies = [pygame.Rect(*point,16,16) for point in seen]
            interactables = game.load_interactables(tmx)
            self.assertEqual({item['topic_id'] for item in interactables if item.get('topic_id')},
                             room_topics[rid], rid)
            for item in interactables:
                if item.get('topic_id'):
                    self.assertNotIn(item['topic_id'], found, (rid, item['topic_id']))
                    found.add(item['topic_id'])
                    self.assertTrue(item['terminal_visual'], (rid, item['topic_id']))
                    self.assertNotIn(item['interaction_id'], terminal_ids)
                    terminal_ids.add(item['interaction_id'])
                    self.assertTrue(item['interaction_id'].startswith('castle_' + rid + '_'))
                    self.assertEqual(item['rect'].collidelist(blockers), -1,
                                     (rid, item['topic_id'], 'terminal is hidden in solid artwork'))
                    self.assertTrue(any(game.nearest_interactable(body,[item],reach=32,blockers=blockers)
                                        for body in bodies), (rid,item['topic_id']))
            if rid == 'throne':
                x,y,w,h = get_stage('castle')['completion']['exit_rect']
                exit_rect = pygame.Rect(x*bounds.w,y*bounds.h,w*bounds.w,h*bounds.h)
                self.assertTrue(any(body.colliderect(exit_rect) for body in bodies))
        self.assertEqual(found, set(CASTLE_TOPIC_ORDER))

    def test_white_lady_has_all_floating_frames_and_scaled_portraits_are_cached(self):
        from src.entities.enemy import Enemy
        enemy = Enemy(self.screen,640,640,320,320,enemy_id='white_lady')
        for direction in ('north','south','east','west'):
            self.assertEqual(len(enemy.frames['walking'][direction]),9)
            self.assertEqual(len(enemy.frames['attack'][direction]),9)
        from src.screens.mang_tahimik import _scaled_helper_portrait
        _scaled_helper_portrait.cache_clear()
        self.assertIs(_scaled_helper_portrait(64), _scaled_helper_portrait(64))
        self.assertEqual(_scaled_helper_portrait.cache_info().misses,1)


class CastleAssessmentTests(unittest.TestCase):
    def test_bonus_is_capped_and_interruption_requires_practice(self):
        challenge = CASTLE_ASSESSMENTS[CASTLE_FINAL_ID]
        session = {'remaining':[CASTLE_FINAL_ID]}
        active = start_attempt(session,challenge,now=10,bonus_time=500)
        self.assertEqual(active['deadline'],1210)
        self.assertEqual(active['bonus_time'],300)
        settle_interrupted(session,now=20)
        self.assertTrue(session['practice_required'])
        self.assertEqual(session['history'][0]['result'],'interrupted')

    def test_failed_attempt_then_unsolved_and_solved_practice_then_pass(self):
        stage = get_stage('castle')
        state = {'keys':5,'challenges_passed':list(stage['manual']['topics']), 'bonus_time':100,
                 'stage_progress':{'defeated_enemies':['zombie_aktan']}}
        class Screen:
            def copy(self): return self
        solved = iter([False,False,True,True])
        modes = []
        class Editor:
            timed_out = False
            def __init__(self,*args,**kwargs):
                self.solved = next(solved); self.commit = kwargs.get('on_assessment_pass')
                modes.append(kwargs['mode'])
            def run(self):
                if self.solved and self.commit: self.commit()
        sessions = {}; consumed = []; passes = []
        def consume(n):
            consumed.append(n); state['bonus_time'] -= n
        with patch('src.screens.final_assessment.assessment_dialog',return_value=True), \
                patch('src.screens.final_assessment.CodeEditor',Editor):
            self.assertFalse(open_final_assessment(Screen(),stage,state,sessions,lambda:None,lambda:passes.append(1),consume))
            self.assertTrue(sessions['castle']['practice_required'])
            self.assertFalse(open_final_assessment(Screen(),stage,state,sessions,lambda:None,lambda:passes.append(1),consume))
            self.assertTrue(open_final_assessment(Screen(),stage,state,sessions,lambda:None,lambda:passes.append(1),consume))
        self.assertEqual(modes,['assessment','practice','practice','assessment'])
        self.assertEqual(consumed,[100,0])
        self.assertEqual(passes,[1])
        self.assertEqual(sessions['castle']['practice_completed'],1)


class CastleGameplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280,720))

    def run_frames(self, *args, **kwargs):
        import test_stage2_dining as dining
        return dining.DiningGameplayTests.run_frames(self, *args, **kwargs)

    def test_real_editors_all_rooms_assessment_bonus_and_exit_save(self):
        from src.ui.code_editor import CodeEditor
        import src.screens.final_assessment as assessment_screen
        solutions = {**SOLUTIONS, **CASTLE_SOLUTIONS}
        class SolvingEditor(CodeEditor):
            def run(editor):
                editor.text_buffer.lines = solutions[editor.challenge['id']].split('\n')
                editor.submit_code()
                self.assertTrue(editor.solved, editor.submission_feedback)
        state = save_manager.new_game_state()
        state.update(stage='Castle',room_id='lobby')
        room_topics = {'dining':('castle_lists',), 'library':('castle_tuples','castle_dictionaries'),
                       'dungeon':('castle_for_loops','castle_while_loops','castle_nested_loops','castle_loop_control'),
                       'throne':('castle_functions','castle_exceptions')}
        def requirements(screen, tid, completed, background):
            self.assertTrue(set(TOPICS[tid]['requirements']).issubset(completed))
            return 'continue'
        with tempfile.TemporaryDirectory() as tmp, patch.object(save_manager,'SAVE_DIR',tmp), \
                patch.object(game,'open_topic_lesson',return_value='challenge'), \
                patch.object(game,'open_topic_requirements',side_effect=requirements), \
                patch.object(game,'CodeEditor',SolvingEditor), \
                patch.object(assessment_screen,'CodeEditor',SolvingEditor), \
                patch.object(assessment_screen,'assessment_dialog',return_value=True):
            for rid, tids in room_topics.items():
                state = transition_room(state,'castle',rid)
                selections = [cid for tid in tids for cid in (*TOPICS[tid]['challenge_ids'],None)]
                def learn(live):
                    for tid in tids:
                        self.assertEqual(live['open_topic_flow'](tid,self.screen.copy()),'solved')
                with patch.object(game,'open_topic_challenges',side_effect=selections):
                    state = self.run_frames(state,learn)
                self.assertEqual(save_manager.load_slot(1)['keys'],state['keys'])
                if rid != 'throne':
                    state = transition_room(state,'castle','lobby')
            self.assertEqual(state['keys'],5)
            self.assertEqual(len(state['topics_completed']),9)
            # Keep this an integration of the teaching/save/exit path: combat is
            # independently covered by the enemy suites, not simulated as played.
            state['stage_progress']['defeated_enemies'] = ['zombie_aktan']
            state['bonus_time'] = 400
            def assess(live):
                self.assertTrue(live['run_final_assessment']())
            state = self.run_frames(state,assess)
            self.assertEqual(state['bonus_time'],100)
            self.assertIn(CASTLE_FINAL_ID,state['challenges_passed'])
            self.assertEqual(state['final_assessments']['castle']['history'][-1]['bonus_time'],300)
            state['map_position'] = [304,192]
            def exit_gate(screen,status,**kwargs):
                self.assertTrue(status.unlocked)
                self.assertFalse(kwargs['developer_access'])
                return 'exit'
            event = pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e,unicode='e')
            with patch.object(game,'open_stage_gate',side_effect=exit_gate), \
                    patch.object(game.StageLoadingScreen,'finish'), \
                    patch.object(pygame.event,'get',return_value=[event]):
                self.assertEqual(game.game_screen(self.screen,slot_num=1,save_state=state),'main_menu')
            restored = save_manager.load_slot(1)
            self.assertIn('castle',restored['completed_stages'])
            self.assertEqual(restored['keys'],5)
            self.assertEqual(restored['bonus_time'],100)
