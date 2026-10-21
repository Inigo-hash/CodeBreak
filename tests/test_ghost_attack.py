"""Attack lighting follows combat timing and stops outside attacks."""
import math
import unittest
from types import SimpleNamespace

import pygame

from src.ui.ghost_attack import ghost_attack_pose, draw_ghost_attack


class GhostAttackTests(unittest.TestCase):
    def enemy(self, **changes):
        fields = dict(active=True, enemy_id='white_lady', state='attack',
                      action_timer=1.0, stats=SimpleNamespace(attack_duration=1.0),
                      rect=pygame.Rect(100, 100, 24, 24), facing='east', attack_range=95)
        fields.update(changes)
        return SimpleNamespace(**fields)

    def test_light_peaks_at_damage_time_and_tracks_camera(self):
        windup = ghost_attack_pose(self.enemy(), 2, 20, 30)
        impact = ghost_attack_pose(self.enemy(action_timer=.48), 2, 20, 30)
        recovery = ghost_attack_pose(self.enemy(action_timer=0), 2, 20, 30)
        self.assertGreater(impact[2], windup[2])
        self.assertGreater(impact[2], recovery[2])
        self.assertEqual(impact[0], (204, 160))

    def test_only_active_attacking_ghosts_emit_light(self):
        for changes in ({'active': False}, {'state': 'idle'}, {'state': 'flinch'},
                        {'state': 'defeated'}, {'enemy_id': 'kapre_usikan'}):
            self.assertIsNone(ghost_attack_pose(self.enemy(**changes), 1, 0, 0))

    def test_light_follows_committed_diagonal_aim(self):
        direction = (1 / math.sqrt(2), -1 / math.sqrt(2))
        pose = ghost_attack_pose(self.enemy(attack_direction=direction), 1, 0, 0)
        self.assertAlmostEqual(pose[3], -math.pi / 4)

    def test_light_is_visible_in_every_attack_direction(self):
        for facing in ('north', 'south', 'east', 'west'):
            surface = pygame.Surface((400, 400))
            pose = ghost_attack_pose(self.enemy(facing=facing, action_timer=.48), 1, 0, 0)
            draw_ghost_attack(surface, pose)
            self.assertGreater(sum(surface.get_at(pose[0])[:3]), 0)
            before = pygame.image.tostring(surface, 'RGB')
            draw_ghost_attack(surface, None)
            self.assertEqual(pygame.image.tostring(surface, 'RGB'), before)
