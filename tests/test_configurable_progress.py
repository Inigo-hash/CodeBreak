"""Shared progression rules work for authored stages and future stage IDs."""
import copy
import tempfile
import unittest
from unittest.mock import patch
from src.data.stages import get_stage
from src.systems.learning_progress import progress_snapshot, learning_progress_enabled
from src.systems import save_manager


class ConfigurableProgressTests(unittest.TestCase):
    def test_progress_is_available_for_any_stage_with_lessons_and_can_be_disabled(self):
        for stage_id in ('island', 'castle'):
            self.assertTrue(learning_progress_enabled(get_stage(stage_id)))
        future = {'id': 'future', 'manual': {'topics': ['new_lesson']}}
        self.assertTrue(learning_progress_enabled(future))
        future['progress'] = {'enabled': False}
        self.assertFalse(learning_progress_enabled(future))
        self.assertFalse(learning_progress_enabled({'id': 'empty'}))

    def test_slot_and_in_game_percentages_agree_through_stage_milestones(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(save_manager, 'SAVE_DIR', folder):
            for stage_id in ('island', 'castle'):
                stage = get_stage(stage_id)
                topics = stage['manual']['topics']
                for count in (0, 1, len(topics)):
                    state = save_manager.new_game_state()
                    state.update(stage=stage['name'], challenges_passed=list(topics[:count]))
                    save_manager.save_slot(1, state)
                    loaded = save_manager.load_slot(1)
                    self.assertEqual(save_manager.slot_progress(1), progress_snapshot(stage, loaded)['percent'])
                state.update(keys=stage['completion']['required_keys'])
                state['stage_progress'] = {'defeated_enemies': [stage['completion']['required_boss']]}
                save_manager.save_slot(1, state)
                self.assertLess(save_manager.slot_progress(1), 100)
                state['challenges_passed'].append(stage['completion']['required_final_challenge'])
                save_manager.save_slot(1, state)
                self.assertEqual(save_manager.slot_progress(1), 100)

    def test_boss_victory_in_another_room_counts_but_stale_active_room_does_not(self):
        stage = get_stage('castle')
        state = {'room_id': 'lobby', 'keys': 5, 'challenges_passed': list(stage['manual']['topics']),
                 'room_checkpoints': {'throne': {'stage_progress': {'defeated_enemies': ['zombie_aktan']}}}}
        self.assertTrue(progress_snapshot(stage, state)['gate'].boss_defeated)
        state['room_id'] = 'throne'
        self.assertFalse(progress_snapshot(stage, state)['gate'].boss_defeated)

    def test_unfinished_stage_uses_authored_guidance_or_generic_fallback(self):
        stage = {'id': 'future', 'manual': {'topics': []},
                 'completion': {'content_ready': False, 'required_keys': 0},
                 'progress': {'unfinished_content_message': 'The observatory is still being built.'}}
        before = copy.deepcopy(stage)
        self.assertEqual(progress_snapshot(stage, {})['next'], stage['progress']['unfinished_content_message'])
        self.assertEqual(stage, before)
        del stage['progress']
        message = progress_snapshot(stage, {})['next']
        self.assertNotIn('Dining', message)
        self.assertNotIn('Castle', message)
        self.assertLess(progress_snapshot(stage, {})['percent'], 100)

    def test_completed_stage_marker_is_case_insensitive_and_missing_slot_is_zero(self):
        self.assertEqual(progress_snapshot(get_stage('castle'), {'completed_stages': ['CASTLE']})['percent'], 100)
        with patch.object(save_manager, 'load_slot', return_value=None):
            self.assertEqual(save_manager.slot_progress(1), 0)

    def test_real_game_opens_progress_and_guidance_in_both_stages(self):
        import pygame
        import test_stage1_ending_regressions as gameplay_helpers
        pygame.init()
        helper = gameplay_helpers.Stage1EndingRegressions()
        helper.screen = pygame.display.set_mode((1280, 720))
        for stage_id in ('island', 'castle'):
            state = save_manager.new_game_state()
            state['stage'] = get_stage(stage_id)['name']
            def events(frame, live):
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r if frame == 0 else pygame.K_t)] if frame < 2 else []
            def check(frame, live):
                self.assertTrue(live['stage_panel'].learning_progress)
                self.assertIn('progress', live['stage_panel'].button_rects)
                self.assertIn('topic_guidance', live['stage_panel'].button_rects)
            with patch('src.screens.game.open_learning_progress') as panel:
                helper.run_frames(state, doorway=False, events=events, check=check)
                self.assertEqual(panel.call_count, 2)
                self.assertEqual(panel.call_args_list[0].args[1]['id'], stage_id)
                self.assertFalse(panel.call_args_list[0].kwargs['topics_only'])
                self.assertTrue(panel.call_args_list[1].kwargs['topics_only'])
