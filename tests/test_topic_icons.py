import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.screens.inventory import PlayerInventory
from src.ui.topic_icons import TOPIC_ICON_STYLES, topic_icon


class TopicIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_every_stage_one_topic_has_distinct_nonempty_artwork(self):
        rendered = []

        for topic_id in TOPIC_ICON_STYLES:
            icon = topic_icon(topic_id)
            self.assertEqual(icon.get_size(), (48, 48))
            self.assertGreater(icon.get_bounding_rect(min_alpha=1).width, 0)
            rendered.append(pygame.image.tobytes(icon, "RGBA"))

        self.assertEqual(len(set(rendered)), len(TOPIC_ICON_STYLES))

    def test_stored_topics_receive_an_icon_automatically(self):
        inventory = PlayerInventory()

        self.assertTrue(inventory.add_topic("variables", "Variables"))
        self.assertIs(inventory.bag[0].icon, topic_icon("variables"))

    def test_unknown_future_topic_gets_generic_book_artwork(self):
        inventory = PlayerInventory()

        inventory.add_topic("future_topic", "Future Topic")

        self.assertIsNotNone(inventory.bag[0].icon)
        self.assertEqual(inventory.bag[0].icon.get_size(), (48, 48))


if __name__ == "__main__":
    unittest.main()
