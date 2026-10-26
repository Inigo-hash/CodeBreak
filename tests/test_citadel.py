"""Stage 3 teaching, physical placement, combat and real-editor campaign flow."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from collections import deque, defaultdict
from copy import deepcopy
import inspect
import tempfile
import unittest
from unittest.mock import patch
import pygame
from pytmx.util_pygame import load_pygame
from src.data.citadel import (
    CITADEL_TOPICS, CITADEL_CHALLENGES, CITADEL_TOPIC_ORDER,
    CITADEL_CHALLENGE_IDS, CITADEL_FINAL_ID, CITADEL_FINAL,
)
from src.data.castle_progression import CASTLE_MAPPED_TOPICS, CASTLE_MAPPED_CHALLENGES
from src.data.castle_curriculum import CASTLE_CHALLENGE_IDS
from src.data.challenges import CHALLENGES
from src.data.topics import TOPICS
from src.data.stages import get_stage, stage_world
from src.data.practice_templates import generate_practice_challenge, get_topic_template_ids
from src.learning.challenge_manager import ChallengeManager
from src.systems.topic_mastery import complete_topic_challenge, reconcile_mastery
from src.systems.stage_gate import evaluate_stage_gate, evaluate_boss_access
from src.systems.stage_handoff import advance_save_state, next_stage
from src.systems.stage_selection import stage_available, select_stage
from src.systems.stage_progress import StageProgress
from src.systems.rooms import transition_room
from src.systems.enemy_spawns import resolve_encounter_spawns
from src.systems.combat import ENEMY_BODY_SIZES, enemy_stats_for_tier, boss_phase_table
from src.systems.boss_trigger import BossEntranceTrigger, boss_arena_exit_at
from src.systems.final_assessment import peek_assessment, start_attempt, settle_interrupted
from src.systems import save_manager
from src.screens import game
from src.screens.final_assessment import open_final_assessment
from src.ui.code_editor import CodeEditor
from citadel_solutions import CITADEL_SOLUTIONS
from mapped_castle_solutions import MAPPED_CASTLE_SOLUTIONS
from castle_solutions import CASTLE_SOLUTIONS


def mastered(stage_id='citadel'):
    stage = get_stage(stage_id)
    state = save_manager.new_game_state()
    state.update(stage=stage['name'], completed_stages=['island','castle'] if stage_id == 'citadel' else ['island'],
                 topics_completed=['control_flow_lesson'])
    topics = CITADEL_TOPICS.values() if stage_id == 'citadel' else CASTLE_MAPPED_TOPICS
    for topic in topics:
        for cid in topic['challenge_ids']:
            state = complete_topic_challenge(state,stage,topic['id'],cid)
    return state


class CitadelLearningTests(unittest.TestCase):
    def test_all_authored_solutions_practice_boundary_cases_and_wrong_returns(self):
        manager = ChallengeManager()
        for cid, challenge in {**CITADEL_CHALLENGES, CITADEL_FINAL_ID:CITADEL_FINAL}.items():
            with self.subTest(challenge=cid):
                passed, feedback = manager.validate(challenge,CITADEL_SOLUTIONS[cid])
                self.assertTrue(passed,feedback)
                self.assertFalse(manager.validate(challenge,f"def {challenge['function_name']}(*args):\n    return None")[0])
                if cid != CITADEL_FINAL_ID:
                    practice = generate_practice_challenge(cid)
                    self.assertTrue(practice['practice_only'])
                    self.assertNotIn(practice['id'], CITADEL_CHALLENGE_IDS)
                    self.assertTrue(manager.validate(practice,CITADEL_SOLUTIONS[cid])[0])
        for tid, topic in CITADEL_TOPICS.items():
            self.assertEqual(get_topic_template_ids(tid), list(topic['challenge_ids']))

    def test_equivalent_implementation_mutation_missing_function_errors_and_timeout(self):
        challenge = CITADEL_CHALLENGES['citadel_comprehensions_squares_001']
        alternate = 'def positive_squares(numbers):\n    answer = []\n    for n in numbers:\n        if n > 0:\n            answer.append(n ** 2)\n    return answer'
        manager = ChallengeManager()
        self.assertTrue(manager.validate(challenge,alternate)[0])
        for code in ('def other(numbers):\n    return []',
                     'def positive_squares(numbers):\n    return 1 / 0',
                     'def positive_squares(numbers):\n    result = [n*n for n in numbers if n > 0]\n    numbers.append(999)\n    return result'):
            self.assertFalse(manager.validate(challenge,code)[0])
        fast = dict(challenge,timeout=.02)
        self.assertFalse(manager.validate(fast,'def positive_squares(numbers):\n    while True:\n        pass')[0])

    def test_partial_completion_both_orders_practice_and_rewards_round_trip(self):
        stage = get_stage('citadel')
        for reverse in (False,True):
            state = save_manager.new_game_state()
            state['stage'] = 'Citadel'
            for index,(tid,topic) in enumerate(CITADEL_TOPICS.items()):
                ids = topic['challenge_ids'][::-1] if reverse else topic['challenge_ids']
                partial = complete_topic_challenge(state,stage,tid,ids[0])
                self.assertEqual(partial['keys'], index)
                self.assertNotIn(tid,partial['topics_completed'])
                self.assertEqual(complete_topic_challenge(partial,stage,tid,ids[1],practice=True),partial)
                with tempfile.TemporaryDirectory() as tmp, patch.object(save_manager,'SAVE_DIR',tmp):
                    save_manager.save_slot(1,partial)
                    partial = save_manager.load_slot(1)
                state = complete_topic_challenge(partial,stage,tid,ids[1])
                self.assertEqual(state['keys'],index+1)
                self.assertIn(tid,state['topics_completed'])
                self.assertEqual(complete_topic_challenge(state,stage,tid,ids[1]),state)
                self.assertEqual(reconcile_mastery(state,stage),state)
            self.assertEqual(len(state['mastery_reward_claims']),4)

    def test_gate_requires_all_lessons_keys_boss_and_final(self):
        stage = get_stage('citadel'); state = mastered()
        self.assertTrue(evaluate_boss_access(stage,4,state['challenges_passed']).unlocked)
        self.assertFalse(evaluate_boss_access(stage,4,state['challenges_passed'][:-1]).unlocked)
        for keys,passed,bosses in ((3,state['challenges_passed'],['citadel_flame_warden']),
                                  (4,state['challenges_passed'],[]),
                                  (4,state['challenges_passed'],['citadel_flame_warden'])):
            self.assertFalse(evaluate_stage_gate(stage,keys,passed,bosses).unlocked)
        state['challenges_passed'].append(CITADEL_FINAL_ID)
        self.assertTrue(evaluate_stage_gate(stage,4,state['challenges_passed'],['citadel_flame_warden']).unlocked)

    def test_interrupted_final_keeps_deadline_bonus_and_practice_requirement(self):
        session={}; challenge=peek_assessment(session,assessment_ids=(CITADEL_FINAL_ID,))
        attempt=start_attempt(session,challenge,now=100,bonus_time=500)
        self.assertEqual(attempt['deadline'],1600)
        self.assertEqual(attempt['bonus_time'],300)
        self.assertTrue(settle_interrupted(session,now=101))
        self.assertTrue(session['practice_required'])
        self.assertEqual(session['history'][0]['result'],'interrupted')

    def test_failed_final_requires_solved_practice_and_keeps_boss_victory(self):
        stage=get_stage('citadel');state=mastered();state['bonus_time']=100
        state['stage_progress']={'defeated_enemies':['citadel_flame_warden']}
        class Screen:
            def copy(self):return self
        answers=iter((False,False,True,True));modes=[]
        class Editor:
            timed_out=False
            def __init__(self,*args,**kwargs):
                self.solved=next(answers);self.commit=kwargs.get('on_assessment_pass');modes.append(kwargs['mode'])
            def run(self):
                if self.solved and self.commit:self.commit()
        sessions={};spent=[]
        def consume(n):spent.append(n);state['bonus_time']-=n
        def passed():state['challenges_passed'].append(CITADEL_FINAL_ID)
        with patch('src.screens.final_assessment.assessment_dialog',return_value=True),patch('src.screens.final_assessment.CodeEditor',Editor):
            self.assertFalse(open_final_assessment(Screen(),stage,state,sessions,lambda:None,passed,consume))
            self.assertFalse(open_final_assessment(Screen(),stage,state,sessions,lambda:None,passed,consume))
            self.assertTrue(open_final_assessment(Screen(),stage,state,sessions,lambda:None,passed,consume))
        self.assertEqual(modes,['assessment','practice','practice','assessment'])
        self.assertEqual(spent,[100,0])
        self.assertEqual(state['keys'],4)
        self.assertEqual(state['stage_progress']['defeated_enemies'],['citadel_flame_warden'])
        self.assertIn(CITADEL_FINAL_ID,state['challenges_passed'])

    def test_castle_maps_and_gate_use_current_five_and_migrate_legacy_mastery(self):
        stage = get_stage('castle')
        self.assertEqual(tuple(stage['manual']['topics']),CASTLE_MAPPED_CHALLENGES)
        self.assertEqual(len(CASTLE_MAPPED_TOPICS),5)
        state = mastered('castle')
        self.assertEqual(state['keys'],5)
        self.assertTrue(evaluate_boss_access(stage,5,state['challenges_passed']).unlocked)
        old = save_manager.new_game_state()
        old.update(stage='Castle',challenges_passed=list(CASTLE_CHALLENGE_IDS),keys=5)
        migrated = reconcile_mastery(old,stage)
        self.assertTrue(set(CASTLE_MAPPED_CHALLENGES).issubset(migrated['challenges_passed']))
        self.assertEqual(migrated['keys'],5)
        self.assertEqual(reconcile_mastery(migrated,stage),migrated)
        self.assertEqual(old['challenges_passed'],list(CASTLE_CHALLENGE_IDS))
        manager=ChallengeManager()
        for cid in CASTLE_MAPPED_CHALLENGES:
            self.assertTrue(manager.validate(CHALLENGES[cid],MAPPED_CASTLE_SOLUTIONS[cid])[0],cid)
            self.assertTrue(manager.validate(generate_practice_challenge(cid),MAPPED_CASTLE_SOLUTIONS[cid])[0],cid)

    def test_castle_handoff_atlas_and_independent_checkpoints(self):
        castle=get_stage('castle'); citadel=get_stage('citadel')
        self.assertEqual(next_stage(castle)['id'],'citadel')
        self.assertIsNone(next_stage(citadel))
        original=mastered('castle'); original['completed_stages']=['island']
        original.update(room_id='throne',bonus_time=73,character_id='woman')
        moved=advance_save_state(original,castle,citadel)
        self.assertEqual(moved['stage'],'Citadel'); self.assertEqual(moved['keys'],0)
        self.assertEqual(moved['bonus_time'],73); self.assertEqual(moved['character_id'],'woman')
        self.assertEqual(moved['completed_stages'],['island','castle'])
        self.assertTrue(stage_available('citadel',moved))
        self.assertFalse(stage_available('citadel',save_manager.new_game_state()))
        moved=complete_topic_challenge(moved,citadel,CITADEL_TOPIC_ORDER[0],CITADEL_CHALLENGE_IDS[0])
        returned=select_stage(select_stage(moved,'castle'),'citadel')
        self.assertEqual(returned['keys'],0)
        self.assertIn(CITADEL_CHALLENGE_IDS[0],returned['challenges_passed'])


class CitadelMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init(); cls.screen=pygame.display.set_mode((1280,720))
        cls.stage=get_stage('citadel'); cls.world=stage_world(cls.stage)
        cls.tmx=load_pygame(cls.world['map'])
        cls.blockers=game.object_collision_rects(cls.tmx)+[
            pygame.Rect(x*16,y*16,16,16) for layer in cls.tmx.visible_layers if hasattr(layer,'data')
            for x,y,gid in layer if gid and (cls.tmx.get_tile_properties_by_gid(gid) or {}).get('collidable')]
        cls.objects=game.load_interactables(cls.tmx)
        cls.spawns=resolve_encounter_spawns(cls.world['encounters'],640,640,cls.blockers,set(),16,(320,584),zones=cls.world['zones'])

    def reachable(self):
        start=(312,576); seen={start}; queue=deque([start]); bounds=pygame.Rect(0,0,640,640)
        self.assertEqual(pygame.Rect(*start,16,16).collidelist(self.blockers),-1)
        while queue:
            x,y=queue.popleft()
            for dx,dy in ((8,0),(-8,0),(0,8),(0,-8)):
                point=(x+dx,y+dy); body=pygame.Rect(*point,16,16)
                if point not in seen and bounds.contains(body) and body.collidelist(self.blockers)<0:
                    seen.add(point); queue.append(point)
        return [pygame.Rect(*point,16,16) for point in seen]

    def test_all_terminals_crate_and_exit_reachable_with_real_body_and_line_of_sight(self):
        bodies=self.reachable()
        self.assertEqual({o['topic_id'] for o in self.objects if o['topic_id']},set(CITADEL_TOPIC_ORDER))
        self.assertEqual(len({o['interaction_id'] for o in self.objects}),len(self.objects))
        for obj in self.objects:
            self.assertTrue(obj['terminal_visual'] or obj['entity_visual'])
            self.assertTrue(obj['interaction_id'].startswith('citadel_'))
            self.assertEqual(obj['rect'].collidelist(self.blockers),-1,obj['interaction_id'])
            self.assertTrue(any(game.nearest_interactable(body,[obj],reach=32,blockers=self.blockers) for body in bodies),obj['interaction_id'])
        exit_rect=pygame.Rect(*(round(v*640) for v in self.stage['completion']['exit_rect']))
        self.assertTrue(any(body.colliderect(exit_rect) for body in bodies))
        self.assertTrue(any(body.center == (320,320) for body in bodies))

    def test_molten_lava_is_blocked_and_all_three_bridges_stay_open(self):
        for tile in ((12,12),(13,16),(26,25),(14,10)):
            self.assertNotEqual(pygame.Rect(tile[0]*16,tile[1]*16,16,16).collidelist(self.blockers),-1)
        for tile in ((19,27),(13,19),(26,19),(19,13),(19,20)):
            self.assertEqual(pygame.Rect(tile[0]*16,tile[1]*16,16,16).collidelist(self.blockers),-1,tile)

    def test_exact_camps_valid_bodies_safe_arrival_and_boss_assets(self):
        self.assertEqual(len(self.spawns),4)
        for spawn in self.spawns:
            body=pygame.Rect(0,0,*ENEMY_BODY_SIZES[spawn['enemy_id']]);body.center=spawn['position']
            self.assertEqual(body.collidelist(self.blockers),-1)
            self.assertTrue(pygame.Rect(spawn['zone_rect']).contains(body))
            self.assertGreater(pygame.Vector2(body.center).distance_to((320,584)),250)
            self.assertGreater(enemy_stats_for_tier(spawn['enemy_id'],3).max_hp,
                               enemy_stats_for_tier(spawn['enemy_id'],2).max_hp)
        from src.entities.enemy import Enemy
        boss=Enemy(self.screen,640,640,320,320,enemy_id='citadel_flame_warden',combat_tier=3,is_boss=True)
        self.assertEqual(boss.hp,1550)
        self.assertEqual(boss.rect.collidelist(self.blockers),-1)
        for direction in ('north','south','east','west'):
            for group in ('walking','attack','ultimate','flinch'):
                self.assertTrue(boss.frames[group][direction])
        self.assertEqual([p.threshold for p in boss_phase_table(boss.enemy_id)['phases']],[900,450])

    def test_boss_access_and_retreat_cover_side_bridges_too(self):
        zone={'rect':pygame.Rect(240,240,160,160),'is_boss_zone':True,'gate_all_edges':True}
        for outside,inside in (((200,320),(240,320)),((440,320),(399,320)),((320,200),(320,240)),((320,440),(320,399))):
            trigger=BossEntranceTrigger()
            self.assertFalse(trigger.update(zone,outside))
            self.assertTrue(trigger.update(zone,inside))
            self.assertFalse(trigger.update(zone,inside))
            self.assertTrue(boss_arena_exit_at(zone,((outside[0]+inside[0])//2,(outside[1]+inside[1])//2)))


class StopFrames(Exception):
    pass


class CitadelGameplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init(); cls.screen=pygame.display.set_mode((1280,720))

    def frames(self,state,action=None,held_e=False,after=None):
        count=0; saved=None; acted=False
        def locals_():
            frame=inspect.currentframe()
            while frame:
                if frame.f_code is game.game_screen.__code__ and 'dt' in frame.f_locals:return frame.f_locals
                frame=frame.f_back
        def events():
            nonlocal acted
            live=locals_()
            if live and not acted:
                acted=True
                if action:action(live)
            return []
        def present():
            nonlocal count,saved
            live=locals_()
            if live:
                count+=1
                if count==3:
                    if after:after(live)
                    saved=deepcopy(live['build_save_state']());raise StopFrames
        with patch.object(pygame.event,'get',side_effect=events),patch.object(pygame.display,'flip',side_effect=present), \
             patch.object(game.StageLoadingScreen,'finish'),patch.object(pygame.key,'get_pressed',return_value=defaultdict(bool,{pygame.K_e:held_e})):
            with self.assertRaises(StopFrames):game.game_screen(self.screen,slot_num=1,save_state=deepcopy(state))
        return saved

    def test_real_editors_all_topics_partial_save_camps_cache_assessment_and_final_exit(self):
        state=save_manager.new_game_state();state.update(stage='Citadel',completed_stages=['island','castle'],weapon_obtained=True,weapon_equipped=True)
        solutions=CITADEL_SOLUTIONS
        class Editor(CodeEditor):
            def run(editor):
                editor.text_buffer.lines=solutions[editor.challenge['id'].removeprefix('practice_')].split('\n')
                editor.submit_code()
                self.assertTrue(editor.solved,editor.submission_feedback)
        import src.screens.final_assessment as final_screen
        with tempfile.TemporaryDirectory() as tmp,patch.object(save_manager,'SAVE_DIR',tmp), \
             patch.object(game,'open_topic_lesson',return_value='challenge'),patch.object(game,'open_topic_requirements',return_value='continue'), \
             patch.object(game,'CodeEditor',Editor),patch.object(final_screen,'CodeEditor',Editor),patch.object(final_screen,'assessment_dialog',return_value=True):
            tid=CITADEL_TOPIC_ORDER[0]; ids=TOPICS[tid]['challenge_ids']
            with patch.object(game,'open_topic_challenges',side_effect=[ids[0],None]):
                state=self.frames(state,lambda live:self.assertEqual(live['open_topic_flow'](tid,self.screen.copy()),'editor_closed'))
            self.assertEqual(state['keys'],0);self.assertIn(ids[0],save_manager.load_slot(1)['challenges_passed'])
            selections=[cid for topic in CITADEL_TOPICS.values() for cid in (*topic['challenge_ids'],None)]
            def learn(live):
                for topic_id in CITADEL_TOPIC_ORDER:
                    self.assertEqual(live['open_topic_flow'](topic_id,self.screen.copy()),'solved')
            with patch.object(game,'open_topic_challenges',side_effect=selections):state=self.frames(state,learn)
            self.assertEqual(state['keys'],4)
            def clear(live):
                for enemy in live['enemies']:enemy.hp=0;enemy.active=False;enemy.state='defeated'
            state=self.frames(state,clear)
            self.assertEqual(len(state['stage_progress']['cleared_encounters']),2)
            bonus=state['bonus_time']
            state['map_position']=[336,528]
            def search(live):
                crate=next(o for o in live['interactables'] if o['actions']=='search_crate')
                crate['inspect_progress']=1.0
            state=self.frames(state,search,held_e=True)
            self.assertIn('citadel_supply_cache',state['stage_progress']['opened_interactables'])
            self.assertEqual(state['bonus_time'],bonus+30)
            state=self.frames(save_manager.load_slot(1),search,held_e=True)
            self.assertEqual(state['bonus_time'],bonus+30)
            # Defeat is seeded here: actual boss attacks/assets/access are
            # exercised separately, rather than pretending combat was played.
            state['stage_progress']['defeated_enemies'].append('citadel_flame_warden')
            state=self.frames(state,lambda live:self.assertTrue(live['run_final_assessment']()))
            self.assertIn(CITADEL_FINAL_ID,state['challenges_passed'])
            state['map_position']=[304,208]
            event=pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e,unicode='e')
            with patch.object(game,'open_stage_gate',return_value='exit'),patch.object(game.StageLoadingScreen,'finish'), \
                 patch.object(pygame.event,'get',return_value=[event]):
                self.assertEqual(game.game_screen(self.screen,slot_num=1,save_state=state),'main_menu')
            restored=save_manager.load_slot(1)
            self.assertIn('citadel',restored['completed_stages'])
            self.assertEqual(restored['keys'],4)
            self.assertIn(CITADEL_FINAL_ID,restored['challenges_passed'])

    def test_real_castle_editors_follow_existing_map_topics_then_handoff(self):
        state=save_manager.new_game_state();state.update(stage='Castle',room_id='lobby',topics_completed=['control_flow_lesson'],completed_stages=['island'])
        solutions={**MAPPED_CASTLE_SOLUTIONS,**CASTLE_SOLUTIONS}
        class Editor(CodeEditor):
            def run(editor):
                editor.text_buffer.lines=solutions[editor.challenge['id']].split('\n');editor.submit_code()
                self.assertTrue(editor.solved,editor.submission_feedback)
        import src.screens.final_assessment as final_screen
        rooms=(('lobby',('iterative_structure_lesson',)),('library',('lists_lesson',)),
               ('dungeon',('functions_lesson',)),('dungeon_east',('tuples_lesson',)),
               ('throne',('error_handling_lesson',)))
        with tempfile.TemporaryDirectory() as tmp,patch.object(save_manager,'SAVE_DIR',tmp), \
             patch.object(game,'open_topic_lesson',return_value='challenge'),patch.object(game,'open_topic_requirements',return_value='continue'), \
             patch.object(game,'CodeEditor',Editor),patch.object(final_screen,'CodeEditor',Editor),patch.object(final_screen,'assessment_dialog',return_value=True):
            for room_id,tids in rooms:
                if room_id!='lobby':state=transition_room(state,'castle',room_id)
                picks=[cid for tid in tids for cid in (*TOPICS[tid]['challenge_ids'],None)]
                def learn(live):
                    mapped={item['topic_id'] for item in live['interactables'] if item.get('topic_id')}
                    for tid in tids:
                        self.assertIn(tid,mapped)
                        self.assertEqual(live['open_topic_flow'](tid,self.screen.copy()),'solved')
                with patch.object(game,'open_topic_challenges',side_effect=picks):state=self.frames(state,learn)
                if room_id!='lobby':state=transition_room(state,'castle','lobby')
            self.assertEqual(state['keys'],5)
            state=transition_room(state,'castle','throne')
            state['stage_progress']['defeated_enemies']=['zombie_aktan']
            state=self.frames(state,lambda live:self.assertTrue(live['run_final_assessment']()))
            state['map_position']=[304,192]
            event=pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e,unicode='e')
            with patch.object(game,'open_stage_gate',return_value='exit'),patch.object(game.StageLoadingScreen,'finish'),patch.object(pygame.event,'get',return_value=[event]):
                self.assertEqual(game.game_screen(self.screen,slot_num=1,save_state=state),'next_stage')
            moved=save_manager.load_slot(1)
            self.assertEqual(moved['stage'],'Citadel');self.assertEqual(moved['keys'],0)
            self.assertIn('castle',moved['completed_stages'])
            self.assertEqual(self.frames(moved)['stage'],'Citadel')

    def test_missing_requirements_block_each_real_boss_bridge_approach(self):
        for position in ((240,312),(376,312),(312,240),(312,376)):
            state=save_manager.new_game_state();state.update(stage='Citadel',map_position=list(position))
            def check(live):
                self.assertIsNone(live['boss_enemy'])
                self.assertFalse(live['boss_zone']['rect'].collidepoint(live['player_rect'].center))
            with patch.object(game,'open_stage_gate',return_value='close'):
                self.frames(state,after=check)
