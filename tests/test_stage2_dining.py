"""Dining vertical slice: real maps, sandbox, reward transactions and slots."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from collections import deque, defaultdict
from copy import deepcopy
import inspect
import tempfile
import time
import unittest
from unittest.mock import patch
import pygame
from pytmx.util_pygame import load_pygame
from src.data.castle_lists import LIST_CHALLENGE_IDS, LISTS_CHALLENGES, lists_practice
from src.data.stages import get_stage, stage_world
from src.data.rooms import ROOM_STAGES
from src.learning.challenge_manager import ChallengeManager
from src.learning.sandbox import run_user_code, run_function_tests
from src.systems.topic_mastery import complete_topic_challenge, reconcile_mastery
from src.systems.rooms import transition_room, world_for_room, aggregate_stage_progress
from src.systems.stage_gate import evaluate_stage_gate
from src.systems.enemy_spawns import resolve_encounter_spawns
from src.systems import save_manager
from src.screens import game
from src.ui.code_editor import CodeEditor

INSPECT = '''def describe_items(items):
    if not items:
        return (None, None, 0)
    return (items[0], items[-1], len(items))'''
UPDATE = '''def update_items(items, added, removed):
    result = list(items)
    result.append(added)
    if removed in result:
        result.remove(removed)
    popped = None
    if result:
        popped = result.pop()
    return (result, popped)'''
SOLUTIONS = dict(zip(LIST_CHALLENGE_IDS, (INSPECT, UPDATE)))


class FunctionValidationTests(unittest.TestCase):
    def setUp(self):
        self.manager = ChallengeManager()

    def test_all_authored_cases_and_practice_pass(self):
        for cid in LIST_CHALLENGE_IDS:
            for challenge in (LISTS_CHALLENGES[cid], lists_practice(cid)):
                with self.subTest(cid=challenge['id']):
                    self.assertTrue(self.manager.validate(challenge, SOLUTIONS[cid])[0])

    def test_alternative_implementations(self):
        alternative = '''def describe_items(items):
    count = len(items)
    return (items[0], items[count - 1], count) if count else (None, None, 0)'''
        self.assertTrue(self.manager.validate(LISTS_CHALLENGES[LIST_CHALLENGE_IDS[0]], alternative)[0])
        self.assertTrue(self.manager.validate(LISTS_CHALLENGES[LIST_CHALLENGE_IDS[1]], UPDATE.replace('list(items)', 'items[:]'))[0])

    def test_failure_feedback_contains_input_actual_expected(self):
        passed, feedback = self.manager.validate(LISTS_CHALLENGES[LIST_CHALLENGE_IDS[0]], 'def describe_items(items):\n    return 0')
        self.assertFalse(passed)
        for label in ('Input:', 'Actual:', 'Expected:'):
            self.assertIn(label, feedback)

    def test_missing_function_and_runtime_error(self):
        for code, message in [('x = 1', 'Define the required function'),
                              ('def describe_items(items):\n    return items[0]', 'IndexError')]:
            passed, feedback = self.manager.validate(LISTS_CHALLENGES[LIST_CHALLENGE_IDS[0]], code)
            self.assertFalse(passed)
            self.assertIn(message, feedback)

    def test_infinite_loop_inside_function_times_out(self):
        started = time.monotonic()
        passed, feedback = run_function_tests('def forever(items):\n    while True:\n        pass',
                                              'forever', [{'args': [[]], 'expected': None}], timeout=0.05)
        self.assertFalse(passed)
        self.assertIn('too long', feedback)
        self.assertLess(time.monotonic() - started, 1)

    def test_fresh_globals_and_mutable_inputs_per_case(self):
        cases = [{'args': [[1]], 'expected': [1, 2]}] * 2
        original = deepcopy(cases)
        code = 'seen = []\ndef add(items):\n    seen.append(1)\n    items.append(1 + len(seen))\n    return items'
        self.assertTrue(run_function_tests(code, 'add', cases)[0])
        self.assertEqual(cases, original)

    def test_original_list_must_not_be_modified(self):
        passed, feedback = self.manager.validate(LISTS_CHALLENGES[LIST_CHALLENGE_IDS[1]], UPDATE.replace('list(items)', 'items'))
        self.assertFalse(passed)
        self.assertIn('unchanged', feedback)

    def test_single_item_pop_returns_item_not_none(self):
        result = run_user_code(UPDATE, function_call={'name': 'update_items', 'args': [[], 'cup', 'missing']})
        self.assertEqual(result['return_value'], ([], 'cup'))
        result = run_user_code(UPDATE, function_call={'name': 'update_items', 'args': [[], 'cup', 'cup']})
        self.assertEqual(result['return_value'], ([], None))


    def test_custom_return_callbacks_never_run_after_sandbox(self):
        code = """def forever(self, other=None):
    while True:
        pass
def describe_items(items):
    custom = type('Custom', (), {'__eq__': forever, '__repr__': forever})
    return (custom(), None, 0)
"""
        passed, feedback = run_function_tests(code, 'describe_items',
            [{'args': [[]], 'expected': (None, None, 0)}], timeout=.1)
        self.assertFalse(passed)
        self.assertIn('plain values', feedback)

    def test_cyclic_return_is_reported_without_recursing_in_checker(self):
        passed, feedback = run_function_tests(
            'def describe_items(items):\n    result = []\n    result.append(result)\n    return result',
            'describe_items', [{'args': [[]], 'expected': (None, None, 0)}])
        self.assertFalse(passed)
        self.assertIn('non-cyclic', feedback)


class MasteryTests(unittest.TestCase):
    def setUp(self):
        # Keep regression coverage for the older saved-note curriculum.
        # Current map/gate integration is exercised in test_citadel.py.
        from src.data.castle_curriculum import CASTLE_BUNDLES, CASTLE_CHALLENGE_IDS, CASTLE_TOPIC_ORDER
        self.stage = deepcopy(get_stage('castle'))
        self.stage['manual']['topics'] = list(CASTLE_CHALLENGE_IDS)
        self.stage['completion']['mastery_bundles'] = CASTLE_BUNDLES
        self.stage['completion'].pop('challenge_migrations', None)
        self.stage['objectives'] = [
            {'id': tid + '_mastery', 'kind': 'topic', 'target': tid}
            for tid in CASTLE_TOPIC_ORDER]
        self.state = {'stage': 'Castle', 'keys': 0, 'challenges_passed': [], 'topics_completed': []}

    def test_all_challenges_required_in_either_order(self):
        for ids in (LIST_CHALLENGE_IDS, LIST_CHALLENGE_IDS[::-1]):
            state = complete_topic_challenge(self.state, self.stage, 'castle_lists', ids[0])
            self.assertEqual(state['keys'], 0)
            self.assertNotIn('castle_lists', state['topics_completed'])
            state = complete_topic_challenge(state, self.stage, 'castle_lists', ids[1])
            self.assertEqual(state['keys'], 1)
            self.assertIn('castle_lists', state['topics_completed'])
            self.assertEqual(state['mastery_reward_claims'], ['castle_lists_key_1'])
            self.assertEqual(self.state['challenges_passed'], [])

    def mastered(self):
        state = self.state
        for cid in LIST_CHALLENGE_IDS:
            state = complete_topic_challenge(state, self.stage, 'castle_lists', cid)
        return state

    def test_replay_practice_and_load_are_idempotent(self):
        state = self.mastered()
        for cid in LIST_CHALLENGE_IDS:
            self.assertEqual(complete_topic_challenge(state, self.stage, 'castle_lists', cid), state)
            self.assertEqual(complete_topic_challenge(state, self.stage, 'castle_lists', cid, practice=True), state)
        self.assertEqual(reconcile_mastery(state, self.stage), state)
        self.assertEqual(complete_topic_challenge(self.state, self.stage, 'castle_lists', 'practice_lists_inspect_001'), self.state)

    def test_legacy_mastery_reconciles_without_double_reward(self):
        state = self.mastered()
        state.pop('mastery_reward_claims')
        self.assertEqual(reconcile_mastery(state, self.stage)['keys'], 1)

    def test_stage_switch_keeps_castle_claim_in_its_own_checkpoint(self):
        from src.systems.stage_selection import select_stage
        state = self.mastered()
        state['completed_stages'] = ['island']
        island = select_stage(state, 'island')
        self.assertEqual(island['keys'], 0)
        self.assertEqual(island['mastery_reward_claims'], [])
        returned = select_stage(island, 'castle')
        self.assertEqual(returned['keys'], 1)
        self.assertEqual(returned['mastery_reward_claims'], ['castle_lists_key_1'])

    def test_unfinished_castle_never_unlocks(self):
        state = self.mastered()
        self.assertEqual(self.stage['completion']['required_keys'], 5)
        self.assertFalse(evaluate_stage_gate(self.stage, 5, state['challenges_passed']).unlocked)
        self.assertEqual(get_stage('island')['completion']['required_keys'], 9)

    def test_progress_guides_from_dining_to_library(self):
        from src.systems.learning_progress import progress_snapshot
        snapshot = progress_snapshot(self.stage, self.mastered())
        self.assertEqual(snapshot['percent'], 10)
        self.assertIn('Archive Record', snapshot['next'])

    def test_atomic_interruption_keeps_old_snapshot_and_retry_claims_once(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(save_manager, 'SAVE_DIR', tmp):
            first = complete_topic_challenge(self.state, self.stage, 'castle_lists', LIST_CHALLENGE_IDS[0])
            save_manager.save_slot(1, first)
            candidate = complete_topic_challenge(first, self.stage, 'castle_lists', LIST_CHALLENGE_IDS[1])
            with patch.object(save_manager.os, 'replace', side_effect=OSError('interrupted')):
                with self.assertRaises(OSError):
                    save_manager.save_slot(1, candidate)
            self.assertEqual(save_manager.load_slot(1), first)
            save_manager.save_slot(1, candidate)
            # Loading the completed old note credits its current replacement.
            self.assertEqual(save_manager.load_slot(1), reconcile_mastery(candidate, get_stage('castle')))
            self.assertEqual(reconcile_mastery(save_manager.load_slot(1), self.stage)['keys'], 1)


class DiningMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))
        cls.world = world_for_room('castle', stage_world(get_stage('castle')), {'room_id': 'dining'})
        cls.tmx = load_pygame(cls.world['map'])
        cls.blockers = game.object_collision_rects(cls.tmx)
        cls.blockers += [pygame.Rect(x*16, y*16, 16, 16)
                         for layer in cls.tmx.visible_layers if hasattr(layer, 'data')
                         for x, y, gid in layer if gid and (cls.tmx.get_tile_properties_by_gid(gid) or {}).get('collidable')]
        cls.objects = game.load_interactables(cls.tmx)
        cls.spawns = resolve_encounter_spawns(cls.world['encounters'], 640, 640, cls.blockers, set(), 16, (320, 560), zones=cls.world['zones'])

    def reachable(self):
        start = (312, 544)
        seen = {start}
        frontier = deque([start])
        while frontier:
            x, y = frontier.popleft()
            for dx, dy in ((8, 0), (-8, 0), (0, 8), (0, -8)):
                point = (x+dx, y+dy)
                body = pygame.Rect(*point, 16, 16)
                if point in seen or not pygame.Rect(0, 0, 640, 640).contains(body) or body.collidelist(self.blockers) >= 0:
                    continue
                seen.add(point)
                frontier.append(point)
        return seen

    def test_player_sized_reachability_and_interaction_line_of_sight(self):
        bodies = [pygame.Rect(x, y, 16, 16) for x, y in self.reachable()]
        # The current Dining map deliberately has no required lessons;
        # the five mapped groups live in the other Castle rooms.
        self.assertEqual(len(self.objects), 0)
        self.assertGreater(len(bodies), 0)
        for item in self.objects:
            with self.subTest(id=item['interaction_id']):
                self.assertTrue(any(game.nearest_interactable(body, [item], reach=32, blockers=self.blockers) for body in bodies))
                self.assertTrue(item['interaction_id'].startswith('castle_dining_'))

    def test_exact_encounter_size_safe_spawn_and_patrol_area(self):
        self.assertEqual(len(self.spawns), 4)
        camp = pygame.Rect(400, 224, 176, 192)
        arrival = pygame.Rect(312,544,16,16)
        for spawn in self.spawns:
            from src.systems.combat import ENEMY_BODY_SIZES
            body = pygame.Rect(0, 0, *ENEMY_BODY_SIZES[spawn['enemy_id']])
            body.center = spawn['position']
            self.assertTrue(pygame.Rect(spawn['zone_rect']).contains(body))
            self.assertEqual(body.collidelist(self.blockers), -1)
            self.assertGreater(pygame.Vector2(body.center).distance_to(arrival.center), 140)
        self.assertFalse(camp.colliderect(pygame.Rect(312, 544, 16, 16)))

    def test_room_world_isolated_and_searches_independent(self):
        self.assertTrue(all(e['id'].startswith('castle_library_') for e in world_for_room('castle', stage_world(get_stage('castle')), {'room_id': 'library'})['encounters']))
        for item in self.objects:
            if item['actions'].startswith('search_'):
                self.assertIsNone(item['topic_id'])
                self.assertTrue(item['independent_search'])

    def test_guards_stay_inside_chase_bounds_when_lured(self):
        from src.entities.enemy import Enemy
        for spawn in self.spawns:
            enemy = Enemy(self.screen, 640, 640, *spawn['position'],
                          enemy_id=spawn['enemy_id'], zone_rect=spawn['zone_rect'])
            enemy.state = 'chase'
            player = pygame.Rect(520, 430, 16, 16)
            for _ in range(100):
                enemy.update(0.05, player, self.blockers + [player], 640, 640, navigation_rects=self.blockers)
                self.assertTrue(enemy.chase_bounds.contains(enemy.rect))

    def test_full_room_save_roundtrip_and_aggregate_objectives(self):
        state = {'stage': 'Castle', 'room_id': 'lobby', 'keys': 0, 'stage_progress': {}, 'challenges_passed': [], 'topics_completed': []}
        state = transition_room(state, 'castle', 'dining')
        for cid in LIST_CHALLENGE_IDS:
            self.assertTrue(ChallengeManager().validate(LISTS_CHALLENGES[cid], SOLUTIONS[cid])[0])
            state = complete_topic_challenge(state, get_stage('castle'), 'castle_lists', cid)
        progress = game.StageProgress.from_dict(state['stage_progress'])
        for item in self.objects:
            if item['actions'].startswith('search_'):
                progress.open_interactable(item['interaction_id'])
        progress.clear_encounter('castle_dining_duwende_01')
        state['stage_progress'] = progress.to_dict()
        lobby = transition_room(state, 'castle', 'lobby')
        self.assertEqual(aggregate_stage_progress(lobby, get_stage('castle')).objective_counts(get_stage('castle')), (1, 7))
        returned = transition_room(lobby, 'castle', 'dining')
        with tempfile.TemporaryDirectory() as tmp, patch.object(save_manager, 'SAVE_DIR', tmp):
            save_manager.save_slot(1, returned)
            restored = save_manager.load_slot(1)
        self.assertEqual(restored['keys'], 1)
        self.assertEqual(restored['mastery_reward_claims'], ['castle_mapped_lists_lesson'])
        self.assertEqual(restored['stage_progress'], state['stage_progress'])
        self.assertEqual(set(restored['topics_completed']), {'castle_lists','lists_lesson'})


class EndFrames(Exception):
    pass


class DiningGameplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def run_frames(self, state, action=None, held_e=False):
        frames = 0
        saved = None
        acted = False
        def live_game():
            frame = inspect.currentframe()
            while frame:
                if frame.f_code is game.game_screen.__code__ and 'dt' in frame.f_locals:
                    return frame.f_locals
                frame = frame.f_back
            return None
        def events():
            nonlocal acted
            live = live_game()
            if live and not acted:
                acted = True
                if action:
                    action(live)
            return []
        def present():
            nonlocal frames, saved
            live = live_game()
            if live:
                frames += 1
                if frames == 3:
                    saved = deepcopy(live['build_save_state']())
                    self.assertEqual(len([e for e in live['enemies'] if e.active]),
                                     sum(len(camp['enemies']) for camp in live['world']['encounters'] if camp['id'] not in saved['stage_progress']['cleared_encounters']))
                    raise EndFrames
        keys = defaultdict(bool, {pygame.K_e: held_e})
        with patch.object(pygame.event, 'get', side_effect=events), \
                patch.object(pygame.display, 'flip', side_effect=present), \
                patch.object(game.StageLoadingScreen, 'finish'), \
                patch.object(pygame.key, 'get_pressed', return_value=keys):
            with self.assertRaises(EndFrames):
                game.game_screen(self.screen, slot_num=1, save_state=deepcopy(state))
        return saved

    def test_real_game_lessons_encounter_return_search_and_reload(self):
        state = save_manager.new_game_state()
        state.update(stage='Castle', room_id='lobby', weapon_obtained=True, weapon_equipped=True)
        state = transition_room(state, 'castle', 'dining')
        class SolvingEditor(CodeEditor):
            def run(self):
                self.text_buffer.lines = SOLUTIONS[self.challenge['id']].split('\n')
                self.submit_code()
        def complete_and_clear(live):
            self.assertEqual(live['open_topic_flow']('castle_lists', self.screen.copy()), 'solved')
            for enemy in live['enemies']:
                enemy.state = 'defeated'
                enemy.active = False
                enemy.hp = 0
        with tempfile.TemporaryDirectory() as tmp, patch.object(save_manager, 'SAVE_DIR', tmp), \
                patch.object(game, 'open_topic_lesson', return_value='challenge'), \
                patch.object(game, 'open_topic_challenges', side_effect=[*LIST_CHALLENGE_IDS, None]), \
                patch.object(game, 'CodeEditor', SolvingEditor):
            state = self.run_frames(state, complete_and_clear)
            self.assertEqual(state['keys'], 1)
            self.assertEqual(save_manager.load_slot(1)['keys'], 1)
            self.assertEqual(set(state['topics_completed']), {'castle_lists','lists_lesson'})
            self.assertEqual(set(state['stage_progress']['cleared_encounters']), {'castle_dining_duwende_01', 'castle_dining_north_01'})
            state = transition_room(state, 'castle', 'lobby')
            state = transition_room(state, 'castle', 'dining')
            # Dining's removed props must not reappear. Camp clears and a
            # migrated saved Lists note still survive the room round trip.
            before_reload = state['bonus_time']
            save_manager.save_slot(1,state)
            state = self.run_frames(save_manager.load_slot(1))
            self.assertEqual(state['bonus_time'],before_reload)
            self.assertEqual(state['keys'],1)
            self.assertEqual(state['mastery_reward_claims'],['castle_mapped_lists_lesson'])
            self.assertEqual(set(state['stage_progress']['cleared_encounters']),
                             {'castle_dining_duwende_01','castle_dining_north_01'})


if __name__ == '__main__':
    unittest.main()
