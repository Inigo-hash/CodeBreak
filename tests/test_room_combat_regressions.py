"""Door placement and camp assistance from the Throne Room report."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
from unittest.mock import patch
import pygame
from src.entities.enemy import Enemy
from src.systems.enemy_alerts import alert_camp
from src.data.rooms import ROOM_STAGES
from src.ui.gameplay_hud import GameplayHUD


class RoomCombatRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((960, 640))

    def pair(self):
        return [Enemy(self.screen, 640, 640, x, 400, enemy_id=species,
                      group_id='castle_test', combat_scale=.4, combat_tier=2)
                for x, species in ((350, 'white_lady'), (430, 'kapre_usikan'))]

    def test_hit_alerts_nearby_kapre_and_it_moves_toward_player(self):
        ghost, kapre = self.pair()
        ghost.receive_damage(10)
        alert_camp(ghost, [ghost, kapre], [])
        self.assertEqual(kapre.state, 'alert')
        player = pygame.Rect(310, 400, 16, 16)
        start = kapre.rect.centerx
        for _ in range(30):
            kapre.update(.05, player, [ghost.rect, player], 640, 640, navigation_rects=[])
        self.assertLess(kapre.rect.centerx, start)

    def test_alert_does_not_cross_walls_groups_or_revive_defeated_enemies(self):
        for mode in ('wall', 'group', 'defeated', 'distance'):
            ghost, kapre = self.pair()
            terrain = [pygame.Rect(385, 0, 16, 640)] if mode == 'wall' else []
            if mode == 'group': kapre.group_id = 'another_camp'
            if mode == 'defeated': kapre.state = 'defeated'
            if mode == 'distance': kapre.rect.x = 600
            before = kapre.state
            alert_camp(ghost, [ghost, kapre], terrain)
            self.assertEqual(kapre.state, before, mode)

    def test_throne_return_requires_walking_to_south_threshold(self):
        room = ROOM_STAGES['castle']['rooms']['throne']
        door = pygame.Rect(*(round(v*16) for v in room['routes'][0]['rect']))
        arrival = pygame.Rect(*(round(v*16) for v in room['spawn']), 16, 16)
        self.assertFalse(door.colliderect(arrival))
        self.assertFalse(door.colliderect(pygame.Rect(320, 35*16, 16, 16)))
        self.assertTrue(door.colliderect(pygame.Rect(320, 38*16, 16, 16)))

    def test_hold_prompt_has_no_duplicate_key_but_tap_prompt_keeps_key(self):
        hud = object.__new__(GameplayHUD)
        hud.screen = self.screen
        hud.bold = pygame.font.Font(None, 24)
        hud._panel = lambda *args, **kwargs: None
        from src.ui.gameplay_hud import fit_text
        with patch('src.ui.gameplay_hud.fit_text', wraps=fit_text) as fitted:
            hud.draw_interaction_prompt('Hold E to go back to Castle Lobby', 960, 640)
            self.assertEqual(fitted.call_args.args[1], 'Hold E to go back to Castle Lobby')
            hud.draw_interaction_prompt('Read Sign', 960, 640)
            self.assertEqual(fitted.call_args.args[1], '[E] Read Sign')
