"""Enemy markers are detection indicators, not permanent map radar."""

import unittest
from types import SimpleNamespace

import pygame

from src.screens.world_map import (
    enemy_is_tracking_player, enemy_marker_positions,
)


class MapEnemyVisibilityTests(unittest.TestCase):
    @staticmethod
    def enemy(state, resume="chase", active=True):
        return SimpleNamespace(
            state=state,
            _resume_state=resume,
            active=active,
            rect=pygame.Rect(90, 190, 20, 20),
        )

    def test_idle_and_returning_enemies_are_hidden(self):
        for state in ("idle", "return", "defeated"):
            with self.subTest(state=state):
                self.assertFalse(enemy_is_tracking_player(self.enemy(state)))

    def test_acquired_enemy_states_are_visible(self):
        for state in ("alert", "chase", "attack"):
            with self.subTest(state=state):
                self.assertTrue(enemy_is_tracking_player(self.enemy(state)))

    def test_flinch_preserves_the_state_that_will_resume(self):
        self.assertTrue(enemy_is_tracking_player(self.enemy("flinch", "chase")))
        self.assertFalse(enemy_is_tracking_player(self.enemy("flinch", "return")))

    def test_full_map_positions_exclude_unaware_and_inactive_enemies(self):
        enemies = [
            self.enemy("idle"),
            self.enemy("chase"),
            self.enemy("attack", active=False),
        ]
        positions = enemy_marker_positions(
            enemies, (10, 20), pygame.Rect(5, 7, 500, 500), 0.5
        )
        self.assertEqual(positions, [(65, 127)])


if __name__ == "__main__":
    unittest.main()
