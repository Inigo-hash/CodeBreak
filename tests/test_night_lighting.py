"""Regression tests for night, torch, fog, and function-key tools."""

import os
from pathlib import Path
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.ui.night_lighting import (
    WORLD_IS_NIGHT,
    build_torch_overlay,
    draw_night_and_torch,
    torch_screen_position,
)
from src.ui.fog import build_fog_texture, draw_fog


class NightLightingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def test_world_starts_at_night(self):
        self.assertTrue(WORLD_IS_NIGHT)

    def test_torch_overlay_is_bright_near_flame_and_dark_far_away(self):
        overlay = build_torch_overlay((800, 600), (400, 300), 0.25, radius=180)

        center_alpha = overlay.get_at((400, 300)).a
        middle_alpha = overlay.get_at((490, 300)).a
        corner_alpha = overlay.get_at((0, 0)).a

        self.assertLess(center_alpha, middle_alpha)
        self.assertLess(middle_alpha, corner_alpha)

    def test_torch_changes_sides_with_player_facing(self):
        center = (400, 300)
        left = torch_screen_position(center, "left", 0)
        right = torch_screen_position(center, "right", 0)

        self.assertLess(left[0], center[0])
        self.assertGreater(right[0], center[0])

    def test_lighting_renders_repeatedly_at_supported_sizes(self):
        for size in ((800, 600), (1280, 720), (1920, 1080)):
            surface = pygame.Surface(size)
            center = (size[0] // 2, size[1] // 2)
            for frame in range(30):
                surface.fill((145, 160, 125))
                draw_night_and_torch(
                    surface, center, "right", frame / 60.0
                )

            flame = torch_screen_position(center, "right", 29 / 60.0)
            near = surface.get_at((round(flame[0]), round(flame[1])))
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
