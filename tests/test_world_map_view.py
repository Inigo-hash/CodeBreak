"""Zooming and panning the sheet opened with M."""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from src.screens.world_map import (
    MAP_ZOOM_MAX, MAP_ZOOM_MIN, _blit_scaled, clamped_view,
    enemy_marker_positions, open_world_map, zoomed_view,
)


class ZoomAnchorTests(unittest.TestCase):
    def under_cursor(self, view, zoom, anchor):
        """The point on the sheet currently beneath ``anchor``."""

        return ((anchor[0] - view[0]) / zoom, (anchor[1] - view[1]) / zoom)

    def test_the_chart_under_the_cursor_stays_under_the_cursor(self):
        view, zoom, anchor = (100.0, 50.0), 1.0, (500, 300)
        before = self.under_cursor(view, zoom, anchor)

        for new_zoom in (1.25, 2.0, 3.0, 1.6, 1.0):
            moved = zoomed_view(view, zoom, new_zoom, anchor)
            self.assertEqual(
                self.under_cursor(moved, new_zoom, anchor), before
            )
            view, zoom = moved, new_zoom

    def test_zooming_about_different_points_moves_the_sheet_differently(self):
        left = zoomed_view((0.0, 0.0), 1.0, 2.0, (100, 100))
        right = zoomed_view((0.0, 0.0), 1.0, 2.0, (900, 100))
        self.assertNotEqual(left, right)

    def test_the_zoom_range_starts_at_the_fitted_sheet(self):
        self.assertEqual(MAP_ZOOM_MIN, 1.0)
        self.assertGreater(MAP_ZOOM_MAX, MAP_ZOOM_MIN)


class ClampTests(unittest.TestCase):
    SCREEN = (1920, 1080)

    def test_a_sheet_smaller_than_the_screen_is_centred(self):
        for view in ((0, 0), (-4000, 900), (5000, -20)):
            with self.subTest(view=view):
                self.assertEqual(
                    clamped_view(view, (800, 600), self.SCREEN),
                    ((1920 - 800) / 2, (1080 - 600) / 2),
                )

    def test_a_larger_sheet_cannot_be_dragged_off_the_screen(self):
        sheet = (3000, 2000)

        # Dragged down and right past its own top-left corner.
        self.assertEqual(clamped_view((500, 500), sheet, self.SCREEN), (0, 0))
        # Dragged up and left past its bottom-right corner.
        self.assertEqual(
            clamped_view((-9000, -9000), sheet, self.SCREEN),
            (1920 - 3000, 1080 - 2000),
        )
        # A view already inside the range is left alone.
        self.assertEqual(clamped_view((-40, -60), sheet, self.SCREEN), (-40, -60))


class EnemyMarkerTests(unittest.TestCase):
    def enemy(self, center):
        from types import SimpleNamespace

        rect = pygame.Rect(0, 0, 20, 20)
        rect.center = center
        return SimpleNamespace(active=True, state="chase", rect=rect)

    def test_marks_are_carried_by_the_zoom(self):
        map_rect = pygame.Rect(20, 30, 300, 200)
        enemies = (self.enemy((100, 100)),)

        at_one = enemy_marker_positions(enemies, (0, 0), map_rect, 0.5)
        at_two = enemy_marker_positions(enemies, (0, 0), map_rect, 0.5, zoom=2.0)

        self.assertEqual(at_one, [(70, 80)])
        self.assertEqual(at_two, [(140, 160)])

    def test_the_view_offset_moves_the_marks_with_the_sheet(self):
        map_rect = pygame.Rect(0, 0, 300, 200)
        enemies = (self.enemy((100, 100)),)

        panned = enemy_marker_positions(enemies, (250, 400), map_rect, 1.0)
        self.assertEqual(panned, [(350, 500)])


class BlitScaledTests(unittest.TestCase):
    def test_only_the_visible_part_of_the_sheet_is_scaled(self):
        source = pygame.Surface((100, 100))
        source.fill((255, 0, 0))
        target = pygame.Surface((50, 50))
        target.fill((0, 0, 0))

        # Sheet is larger than the target and hangs off the top-left.
        _blit_scaled(target, source, pygame.Rect(-25, -25, 100, 100))

        self.assertEqual(target.get_at((0, 0))[:3], (255, 0, 0))
        self.assertEqual(target.get_at((49, 49))[:3], (255, 0, 0))

    def test_a_sheet_entirely_off_screen_paints_nothing(self):
        source = pygame.Surface((100, 100))
        source.fill((255, 0, 0))
        target = pygame.Surface((50, 50))
        target.fill((7, 8, 9))

        _blit_scaled(target, source, pygame.Rect(400, 400, 100, 100))

        self.assertEqual(target.get_at((25, 25))[:3], (7, 8, 9))


class MapViewerSmokeTests(unittest.TestCase):
    """The viewer survives a wheel, a drag and a reset without complaint."""

    SCREEN = (640, 360)

    def setUp(self):
        self.screen = pygame.Surface(self.SCREEN)
        self.texture = pygame.Surface((600, 400))
        self.texture.fill((90, 120, 80))
        self.player = pygame.Rect(0, 0, 16, 16)
        self.player.center = (300, 200)
        self.zones = [
            {"name": "Test Hollow", "is_boss_zone": False,
             "rect": pygame.Rect(50, 40, 200, 160)},
        ]

    def run_map(self, frames):
        pumped = [0]
        escape = pygame.event.Event(
            pygame.KEYDOWN, {"key": pygame.K_ESCAPE, "unicode": "", "mod": 0}
        )

        def scripted(*_args, **_kwargs):
            index = pumped[0]
            pumped[0] += 1
            return frames[index] if index < len(frames) else [escape]

        with patch("pygame.event.get", scripted), \
                patch("pygame.display.flip"), \
                patch("pygame.mouse.get_pos", lambda: (320, 180)):
            return open_world_map(
                self.screen, self.texture, self.player, 600, 400, self.zones,
                background=pygame.Surface(self.SCREEN),
            )

    def test_wheel_drag_and_reset_all_run(self):
        wheel = pygame.event.Event(pygame.MOUSEWHEEL, {"y": 1, "x": 0})
        press = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"pos": (320, 180), "button": 1}
        )
        drag = pygame.event.Event(
            pygame.MOUSEMOTION,
            {"pos": (420, 240), "rel": (100, 60), "buttons": (1, 0, 0)},
        )
        release = pygame.event.Event(
            pygame.MOUSEBUTTONUP, {"pos": (420, 240), "button": 1}
        )
        reset = pygame.event.Event(
            pygame.KEYDOWN, {"key": pygame.K_r, "unicode": "r", "mod": 0}
        )

        night = self.run_map([
            [wheel], [wheel], [press], [drag], [release], [reset], [],
        ])
        self.assertFalse(night)

    def test_the_click_that_opened_the_map_does_not_close_it(self):
        """Clicking the minimap presses in gameplay and releases in here.

        The stray release used to land on the backdrop and shut the sheet
        the instant it opened, so the map looked like it refused to open.
        """

        release = pygame.event.Event(
            pygame.MOUSEBUTTONUP, {"pos": (2, 2), "button": 1}
        )
        escape = pygame.event.Event(
            pygame.KEYDOWN, {"key": pygame.K_ESCAPE, "unicode": "", "mod": 0}
        )
        pumped = [0]
        frames = [[release], [], [], [escape]]

        def scripted(*_args, **_kwargs):
            index = pumped[0]
            pumped[0] += 1
            return frames[index] if index < len(frames) else []

        with (
            patch("pygame.event.get", scripted),
            patch("pygame.display.flip"),
            patch("pygame.mouse.get_pos", lambda: (2, 2)),
        ):
            open_world_map(
                self.screen, self.texture, self.player, 600, 400, self.zones,
                background=pygame.Surface(self.SCREEN),
            )

        # It stayed open until the escape on frame four.
        self.assertGreaterEqual(pumped[0], 4)

    def test_a_click_off_the_sheet_still_closes_the_map(self):
        press = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"pos": (2, 2), "button": 1}
        )
        release = pygame.event.Event(
            pygame.MOUSEBUTTONUP, {"pos": (2, 2), "button": 1}
        )
        # No escape needed: the click itself must end the loop, so a
        # script that never sends one still returns.
        pumped = [0]
        frames = [[press], [release]]

        def scripted(*_args, **_kwargs):
            index = pumped[0]
            pumped[0] += 1
            return frames[index] if index < len(frames) else []

        with patch("pygame.event.get", scripted), \
                patch("pygame.display.flip"), \
                patch("pygame.mouse.get_pos", lambda: (2, 2)):
            open_world_map(
                self.screen, self.texture, self.player, 600, 400, self.zones,
                background=pygame.Surface(self.SCREEN),
            )

        self.assertLessEqual(pumped[0], 4, "the map did not close on the click")


if __name__ == "__main__":
    unittest.main()
