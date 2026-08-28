"""Regression tests for the reusable stage-loading presentation."""

import os
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.screens.loading import (
    BEGINNER_TIPS, STAGE_TIPS, StageLoadingScreen, loading_layout,
)


class LoadingScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_required_resolutions_remain_inside_safe_area(self):
        for size in ((1920, 1080), (1600, 900), (1366, 768), (1280, 720)):
            with self.subTest(size=size):
                layout = loading_layout(size)
                safe = layout["safe"]
                self.assertTrue(safe.contains(layout["note"]))
                self.assertTrue(safe.contains(layout["bar"].inflate(10, 10)))
                self.assertLess(layout["note"].bottom, layout["status_y"])
                self.assertLess(layout["status_y"], layout["bar"].top)

    def test_cover_scaling_preserves_aspect_ratio_without_empty_edges(self):
        source = pygame.Surface((1600, 900))
        for size in ((1920, 1080), (1366, 768), (1280, 720)):
            result = StageLoadingScreen._cover_scale(source, size)
            self.assertEqual(result.get_size(), size)

    def test_beginner_tip_records_are_short_and_have_code(self):
        self.assertGreaterEqual(len(BEGINNER_TIPS), 10)
        for tip in BEGINNER_TIPS:
            self.assertTrue(tip["text"])
            self.assertTrue(tip["code"])
            self.assertLessEqual(len(tip["text"]), 80)

        self.assertTrue(any("input(" in tip["code"] for tip in BEGINNER_TIPS))

    def test_tutorial_has_beginner_specific_loading_tips(self):
        tutorial_tips = STAGE_TIPS["tutorial"]
        self.assertGreaterEqual(len(tutorial_tips), 4)
        self.assertTrue(any("RUN" in tip["code"] for tip in tutorial_tips))

    def test_reported_progress_never_moves_backwards(self):
        screen = pygame.display.set_mode((1280, 720))
        background = pygame.Surface(screen.get_size())
        with patch.object(StageLoadingScreen, "_fade_from_previous"):
            loading = StageLoadingScreen(
                screen,
                stage_id="tutorial",
                background=background,
                previous_frame=background,
                seed=1,
            )
        loading.update(65, "Loading characters...")
        loading.update(20, "Older update")
        self.assertEqual(loading.progress, 65)

    def test_new_game_requests_the_tutorial_loading_transition(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "screens" / "start_game_menu.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("tutorial_screen(screen, show_loading=True)", source)


if __name__ == "__main__":
    unittest.main()

