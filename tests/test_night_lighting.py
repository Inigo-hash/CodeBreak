"""Regression tests for night, torch, fog, and function-key tools."""

import os
from pathlib import Path
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.ui.night_lighting import (
    WORLD_IS_NIGHT,
    draw_night_and_map_torches,
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


if __name__ == "__main__":
    unittest.main()
