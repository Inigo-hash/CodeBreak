import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import tempfile
import unittest
from unittest.mock import patch
import pygame
from src.entities.player import MainCharacter
from src.screens.character_select import (character_select_layout, open_character_select,
                                          draw_character_selection, character_preview)
from src.data.characters import CHARACTERS
from src.systems import save_manager
from src.systems.rooms import transition_room


class CharacterSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((960, 640))

    def test_layout_and_descriptions_fit_supported_screens(self):
        previews = {key: character_preview(key) for key in CHARACTERS}
        for size in ((640, 480), (800, 600), (1280, 720), (1920, 1080)):
            screen = pygame.Surface(size)
            panel, cards, confirm, back = character_select_layout(size)
            self.assertTrue(screen.get_rect().contains(panel))
            for rect in [*cards, confirm, back]:
                self.assertTrue(panel.contains(rect))
            self.assertFalse(cards[0].colliderect(cards[1]))
            self.assertFalse(confirm.colliderect(back))
            draw_character_selection(screen, screen.copy(), 'woman', previews)

    def test_keyboard_choice_and_cancellation(self):
        with patch('pygame.event.get', return_value=[
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT),
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN),
        ]):
            self.assertEqual(open_character_select(self.screen), 'woman')
        with patch('pygame.event.get', return_value=[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]):
            self.assertIsNone(open_character_select(self.screen))

    def test_mouse_card_selection_then_confirmation(self):
        _, cards, confirm, _ = character_select_layout(self.screen.get_size())
        with patch('pygame.event.get', return_value=[
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=cards[1].center),
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=confirm.center),
        ]):
            self.assertEqual(open_character_select(self.screen), 'woman')

    def test_woman_has_visible_frames_in_every_state_and_direction(self):
        character = MainCharacter(self.screen, 960, 640, character_id='woman')
        for group in (character.scaled, character.sword_walk_frames, character.sword_idle_frames,
                      character.attack_frames, character.flinch_frames, character.unarmed_flinch_frames,
                      character.dodge_frames, character.unarmed_dodge_frames, character.death_frames,
                      character.unarmed_death_frames):
            for frames in group.values():
                self.assertTrue(frames)
                self.assertTrue(all(frame.get_bounding_rect().height > 0 for frame in frames))
        character.weapon_equipped = True
        character.update_frames({key: False for key in
                                (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d,
                                 pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)})
        self.assertIs(character.current_frames, character.sword_idle_frames['right'])

    def test_legacy_or_invalid_character_defaults_to_man(self):
        self.assertEqual(MainCharacter(self.screen, 960, 640).character_id, 'man')
        self.assertEqual(MainCharacter(self.screen, 960, 640, character_id='unknown').character_id, 'man')

    def test_character_is_saved_and_survives_room_changes(self):
        state = save_manager.new_game_state()
        state['character_id'] = 'woman'
        with tempfile.TemporaryDirectory() as directory, patch.object(save_manager, 'SAVE_DIR', directory):
            save_manager.save_slot(1, state)
            loaded = save_manager.load_slot(1)
            self.assertEqual(loaded['character_id'], 'woman')
        loaded['room_id'] = 'lobby'
        self.assertEqual(transition_room(loaded, 'castle', 'dining')['character_id'], 'woman')

    def test_tutorial_normalizes_player_and_enemy_visible_sizes(self):
        from src.screens.tutorial import tutorial_sprite_scales
        from src.entities.enemy import Enemy
        enemies = [Enemy(self.screen, 1920, 1080, enemy_id=identity)
                   for identity in ('tiyanak_sinta', 'manananggal', 'tikbalang')]
        for identity in ('man', 'woman'):
            character = MainCharacter(self.screen, 1920, 1080, character_id=identity)
            player_scale, scales = tutorial_sprite_scales(character, enemies, 1080)
            height = max(f.get_bounding_rect(min_alpha=8).height for key, frames in character.scaled.items()
                         if key.startswith('idle_') for f in frames)
            player_height = height * player_scale / 2
            self.assertGreaterEqual(player_height, 110)
            self.assertLessEqual(player_height, 120)
            for enemy, proportion in zip(enemies, (.55, 1.15, 1.35)):
                tallest = max(f.get_bounding_rect(min_alpha=8).height
                              for frames in enemy.frames['walking'].values() for f in frames)
                self.assertAlmostEqual(tallest*scales[enemy.enemy_id], player_height*proportion)
