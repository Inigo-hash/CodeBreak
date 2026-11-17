import unittest
from collections import namedtuple

import pygame

from src.systems.tile_animations import AnimatedTileRenderer, _frame_index


AnimationFrame = namedtuple("AnimationFrame", "gid duration")


class FakeTileLayer:
    def __init__(self, tiles):
        self.data = True
        self.tiles = list(tiles)

    def __iter__(self):
        return iter(self.tiles)


class FakeTmxMap:
    def __init__(self):
        self.visible_layers = [
            FakeTileLayer([(0, 0, 20)]),
            FakeTileLayer([(1, 0, 20), (1, 0, 10)]),
        ]
        self.tile_properties = {
            10: {
                "frames": [
                    AnimationFrame(11, 100),
                    AnimationFrame(12, 100),
                ]
            }
        }
        self.images = {}
        for gid, color in {
            10: (80, 80, 80),
            11: (255, 0, 0),
            12: (0, 0, 255),
            20: (0, 255, 0),
        }.items():
            image = pygame.Surface((16, 16))
            image.fill(color)
            self.images[gid] = image

    def get_tile_image_by_gid(self, gid):
        return self.images.get(gid)


class TileAnimationTests(unittest.TestCase):
    def test_frame_index_respects_frame_durations_and_loops(self):
        frames = ((11, 100), (12, 100), (13, 200))

        self.assertEqual(_frame_index(frames, 0), 0)
        self.assertEqual(_frame_index(frames, 99), 0)
        self.assertEqual(_frame_index(frames, 100), 1)
        self.assertEqual(_frame_index(frames, 200), 2)
        self.assertEqual(_frame_index(frames, 399), 2)
        self.assertEqual(_frame_index(frames, 400), 0)

    def test_renderer_updates_animated_cell_and_keeps_other_tiles(self):
        tmx_map = FakeTmxMap()
        surface = pygame.Surface((32, 16))
        surface.fill((0, 0, 0))
        # Match the static map render that exists before the first animation tick.
        surface.blit(tmx_map.get_tile_image_by_gid(20), (0, 0))
        renderer = AnimatedTileRenderer(tmx_map, tile_size=16, zoom=1)

        # First update paints the first authored animation frame.
        self.assertEqual(renderer.update(surface, 1000), 1)
        self.assertEqual(surface.get_at((20, 5))[:3], (255, 0, 0))

        # No redraw is needed while the same frame remains active.
        self.assertEqual(renderer.update(surface, 1099), 0)

        # At 100 ms, the second frame is drawn over the lower tile layer.
        self.assertEqual(renderer.update(surface, 1100), 1)
        self.assertEqual(surface.get_at((20, 5))[:3], (0, 0, 255))

        # The unrelated static tile remains untouched.
        self.assertEqual(surface.get_at((5, 5))[:3], (0, 255, 0))

    def test_renderer_is_noop_when_map_has_no_placed_animations(self):
        tmx_map = FakeTmxMap()
        tmx_map.visible_layers = [FakeTileLayer([(0, 0, 20)])]
        surface = pygame.Surface((16, 16))
        renderer = AnimatedTileRenderer(tmx_map, tile_size=16, zoom=1)

        self.assertFalse(renderer.has_animations)
        self.assertEqual(renderer.update(surface, 0), 0)


if __name__ == "__main__":
    unittest.main()
