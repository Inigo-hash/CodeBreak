"""Regression tests for the reusable stage-loading presentation."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.screens.loading import (
    BEGINNER_TIPS, StageLoadingScreen, loading_layout,
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


if __name__ == "__main__":
    unittest.main()

