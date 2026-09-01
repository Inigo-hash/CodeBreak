"""Searchable props stay shut until the camp standing over them is cleared."""

import os
from pathlib import Path
from types import SimpleNamespace
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.systems.guards import (
    GUARD_RADIUS, assign_guards, is_guarded, remaining_guards,
)


def enemy_at(center, state="idle"):
    """A stand-in enemy that lives (spawns) at ``center``."""

    return SimpleNamespace(
        rect=pygame.Rect(0, 0, 20, 20), spawn=center, state=state
    )


def prop_at(center):
    rect = pygame.Rect(0, 0, 32, 32)
    rect.center = center
    return {"rect": rect, "guards": []}


class GuardedPropTests(unittest.TestCase):
    def test_only_props_with_a_camp_around_them_are_guarded(self):
        inside = prop_at((500, 500))
        outside = prop_at((5000, 5000))
        camp = enemy_at((520, 480))

        assign_guards([inside, outside], [camp])

        self.assertEqual(inside["guards"], [camp])
        self.assertEqual(outside["guards"], [])
        self.assertTrue(is_guarded(inside))
        self.assertFalse(is_guarded(outside))

    def test_every_camp_member_around_the_prop_guards_it(self):
        prop = prop_at((500, 500))
        pack = [enemy_at((500 + offset, 500)) for offset in (-60, 0, 60)]
        far = enemy_at((4000, 4000))

        assign_guards([prop], pack + [far])

        self.assertEqual(len(prop["guards"]), 3)
        self.assertNotIn(far, prop["guards"])

    def test_prop_opens_only_once_every_guard_is_defeated(self):
        prop = prop_at((500, 500))
        first, second = enemy_at((480, 500)), enemy_at((520, 500))
        assign_guards([prop], [first, second])

        first.state = "defeated"
        self.assertEqual(remaining_guards(prop), [second])
        self.assertTrue(is_guarded(prop))

        second.state = "defeated"
        self.assertFalse(is_guarded(prop))

    def test_luring_a_camp_away_does_not_unlock_its_prop(self):
        prop = prop_at((500, 500))
        guard = enemy_at((500, 500))
        assign_guards([prop], [guard])

        # The chase carries it across the map; it is still alive, so the
        # prop must stay shut rather than opening because nobody is nearby.
        guard.rect.center = (4000, 4000)
        guard.state = "chase"
        self.assertTrue(is_guarded(prop))

    def test_a_dying_guard_stops_holding_the_prop_shut(self):
        prop = prop_at((500, 500))
        guard = enemy_at((500, 500), state="defeated")
        assign_guards([prop], [guard])

        # "defeated" covers the death animation, before the enemy is
        # deactivated, so the prop opens the moment the fight is over.
        self.assertFalse(is_guarded(prop))

    def test_guards_revived_after_a_player_death_lock_the_prop_again(self):
        prop = prop_at((500, 500))
        guard = enemy_at((500, 500), state="defeated")
        assign_guards([prop], [guard])
        self.assertFalse(is_guarded(prop))

        guard.state = "idle"          # Enemy.reset() on player death
        self.assertTrue(is_guarded(prop))

    def test_a_camp_just_beyond_the_radius_does_not_guard_the_prop(self):
        prop = prop_at((500, 500))
        just_inside = enemy_at((500 + GUARD_RADIUS - 5, 500))
        just_outside = enemy_at((500 + GUARD_RADIUS + 5, 500))

        assign_guards([prop], [just_inside, just_outside])

        self.assertEqual(prop["guards"], [just_inside])

    def test_props_with_no_camp_need_no_fight(self):
        prop = prop_at((500, 500))
        assign_guards([prop], [])
        self.assertFalse(is_guarded(prop))
        self.assertEqual(remaining_guards(prop), [])

    def test_gameplay_loop_assigns_camps_and_blocks_the_hold(self):
        source = (
            Path(__file__).resolve().parents[1] / "src" / "screens" / "game.py"
        ).read_text(encoding="utf-8")
        self.assertIn("assign_guards(interactables, enemies)", source)
        self.assertIn("blocking_guards = remaining_guards(near_interactable)", source)


if __name__ == "__main__":
    unittest.main()
