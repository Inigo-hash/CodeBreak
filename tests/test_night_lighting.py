"""Regression tests for night, torch, fog, and function-key tools."""

import os
from pathlib import Path
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.systems.combat import (
    PLAYER_ENERGY_REGEN, PLAYER_TORCH_ENERGY_REGEN, PLAYER_TORCH_HP_REGEN,
    PlayerCombat,
)
from src.ui.night_lighting import (
    LIGHT_CENTER_LIFT,
    LIT_RADIUS_SCALE,
    WORLD_IS_NIGHT,
    draw_night_and_map_torches,
    in_torch_light,
    place_path_torches,
)
from src.ui.fog import build_fog_texture, draw_fog


class NightLightingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def test_world_starts_at_night(self):
        self.assertTrue(WORLD_IS_NIGHT)

    def test_fixed_torches_are_limited_and_stay_off_the_path(self):
        tile_size = 16
        radius = 84
        path_cells = {(x, y) for x in range(40) for y in range(3)}
        torches = place_path_torches(
            path_cells, tile_size, radius, max_torches=4
        )

        torch_cells = {(x // tile_size, y // tile_size) for x, y in torches}
        self.assertTrue(torch_cells.isdisjoint(path_cells))
        self.assertGreater(len(torches), 0)
        self.assertLessEqual(len(torches), 4)

    def test_lighting_renders_repeatedly_at_supported_sizes(self):
        for size in ((800, 600), (1280, 720), (1920, 1080)):
            surface = pygame.Surface(size)
            torches = [(size[0] // 3, size[1] // 2),
                       (size[0] * 2 // 3, size[1] // 2)]
            for frame in range(30):
                surface.fill((145, 160, 125))
                draw_night_and_map_torches(surface, torches, frame / 60.0)

            near = surface.get_at(torches[0])
            far = surface.get_at((5, 5))
            self.assertGreater(sum(near[:3]), sum(far[:3]))

    def test_previous_function_key_bindings_are_restored(self):
        root = Path(__file__).resolve().parents[1]
        game_source = (root / "src" / "screens" / "game.py").read_text(
            encoding="utf-8"
        )
        for key in ("K_F1", "K_F2", "K_F5", "K_F6", "K_F8"):
            self.assertIn(f"pygame.{key}", game_source)

        audio_source = (root / "src" / "systems" / "audio.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("pygame.K_F10", audio_source)

    def test_fog_texture_tiles_over_the_viewport(self):
        surface = pygame.Surface((800, 600))
        surface.fill((30, 40, 50))
        fog = build_fog_texture(220, 150)
        before = surface.copy()

        draw_fog(surface, fog, 120, 80, 13.5, 4.0)

        self.assertNotEqual(
            pygame.image.tobytes(surface, "RGBA"),
            pygame.image.tobytes(before, "RGBA"),
        )


class TorchWarmthTests(unittest.TestCase):
    """Standing in a lit pool refills the dodge budget far faster."""

    RADIUS = 60
    TORCH = (100, 100)

    def test_light_membership_follows_the_visible_pool_not_the_radius(self):
        lit_center = (self.TORCH[0], self.TORCH[1] - LIGHT_CENTER_LIFT)
        visible_edge = self.RADIUS * LIT_RADIUS_SCALE

        self.assertTrue(in_torch_light(
            lit_center, [self.TORCH], self.RADIUS, LIGHT_CENTER_LIFT
        ))
        inside = (lit_center[0] + visible_edge - 5, lit_center[1])
        self.assertTrue(in_torch_light(
            inside, [self.TORCH], self.RADIUS, LIGHT_CENTER_LIFT
        ))

        # Past the drawn contour but still inside the nominal radius: the
        # player can see they are out of the light, so it must not count.
        beyond_contour = (lit_center[0] + visible_edge + 4, lit_center[1])
        self.assertLess(beyond_contour[0] - lit_center[0], self.RADIUS)
        self.assertFalse(in_torch_light(
            beyond_contour, [self.TORCH], self.RADIUS, LIGHT_CENTER_LIFT
        ))

    def test_open_ground_and_unlit_maps_are_never_warmed(self):
        self.assertFalse(in_torch_light((900, 900), [self.TORCH], self.RADIUS))
        self.assertFalse(in_torch_light(self.TORCH, [], self.RADIUS))

    def test_any_torch_in_range_warms_the_player(self):
        torches = [(1000, 1000), self.TORCH, (2000, 40)]
        self.assertTrue(in_torch_light(
            self.TORCH, torches, self.RADIUS, LIGHT_CENTER_LIFT
        ))

    def test_torchlight_regenerates_four_times_the_open_ground_rate(self):
        combat = PlayerCombat()

        combat.energy = 5.0
        combat.update(1.0)
        self.assertAlmostEqual(combat.energy, 5.0 + PLAYER_ENERGY_REGEN)

        combat.energy = 5.0
        combat.update(1.0, PLAYER_TORCH_ENERGY_REGEN)
        self.assertAlmostEqual(
            combat.energy, 5.0 + PLAYER_TORCH_ENERGY_REGEN
        )
        self.assertEqual(PLAYER_TORCH_ENERGY_REGEN, PLAYER_ENERGY_REGEN * 4)

    def test_boosted_regen_still_stops_at_full_energy(self):
        combat = PlayerCombat()
        combat.energy = combat.max_energy - 5
        combat.update(1.0, PLAYER_TORCH_ENERGY_REGEN)
        self.assertEqual(combat.energy, float(combat.max_energy))

    def test_torchlight_heals_at_the_authored_rate(self):
        combat = PlayerCombat()
        combat.take_damage(40)
        self.assertEqual(combat.hp, 60)

        combat.update(1.0, PLAYER_ENERGY_REGEN, PLAYER_TORCH_HP_REGEN)
        self.assertEqual(combat.hp, 60 + int(PLAYER_TORCH_HP_REGEN))

    def test_healing_banks_fractions_across_frames(self):
        """A rate below one point per frame still heals over time."""

        combat = PlayerCombat()
        combat.take_damage(80)                   # low enough to heal freely
        for _ in range(120):                     # two seconds at 60fps
            combat.update(1 / 60, PLAYER_ENERGY_REGEN, PLAYER_TORCH_HP_REGEN)

        self.assertIsInstance(combat.hp, int)
        self.assertLessEqual(combat.hp, 20 + 2 * PLAYER_TORCH_HP_REGEN)
        self.assertGreaterEqual(combat.hp, 20 + 2 * PLAYER_TORCH_HP_REGEN - 1)

    def test_healing_stops_at_full_health(self):
        combat = PlayerCombat()
        combat.take_damage(3)
        for _ in range(600):
            combat.update(1 / 60, PLAYER_ENERGY_REGEN, PLAYER_TORCH_HP_REGEN)

        self.assertEqual(combat.hp, combat.max_hp)

    def test_torchlight_does_not_revive_a_downed_player(self):
        combat = PlayerCombat()
        combat.take_damage(combat.max_hp)
        self.assertEqual(combat.state, "defeated")

        for _ in range(300):
            combat.update(1 / 60, PLAYER_ENERGY_REGEN, PLAYER_TORCH_HP_REGEN)

        self.assertEqual(combat.hp, 0)

    def test_open_ground_heals_nothing(self):
        combat = PlayerCombat()
        combat.take_damage(30)
        for _ in range(600):                     # ten seconds away from light
            combat.update(1 / 60)

        self.assertEqual(combat.hp, 70)

    def test_gameplay_loop_feeds_the_boost_from_torch_positions(self):
        source = (
            Path(__file__).resolve().parents[1] / "src" / "screens" / "game.py"
        ).read_text(encoding="utf-8")
        self.assertIn("in_torch_light(", source)
        self.assertIn("PLAYER_TORCH_ENERGY_REGEN", source)
        self.assertIn("PLAYER_TORCH_HP_REGEN", source)


if __name__ == "__main__":
    unittest.main()
