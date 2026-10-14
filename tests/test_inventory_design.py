import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
import pygame
from src.screens.inventory import PlayerInventory, InventoryScreen, Toolbar
from src.ui.stage_panel import StagePanel


class InventoryDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 720))

    def test_bag_slots_fit_panel_and_hit_testing_matches_rendering(self):
        for size in ((640, 480), (800, 600), (1280, 720), (1920, 1080)):
            screen = pygame.Surface(size)
            bag = InventoryScreen(screen, PlayerInventory())
            bag.progress = 1
            panel = pygame.Rect(bag.panel_x, bag.panel_final_y, bag.panel_w, bag.panel_h)
            self.assertTrue(screen.get_rect().contains(panel))
            for name, rects in (('bag', bag.bag_rects_local), ('toolbar', bag.equipped_rects_local)):
                for index, local in enumerate(rects):
                    rect = local.move(panel.topleft)
                    self.assertTrue(panel.contains(rect))
                    self.assertEqual(bag._slot_at(rect.center), (name, index))
            bag._draw_panel((-1, -1))

    def test_sword_has_art_and_dragging_still_equips_it(self):
        inv = PlayerInventory()
        inv.set_weapon_state(True, False)
        self.assertIsNotNone(inv.bag[0].icon)
        bag = InventoryScreen(pygame.Surface((1280, 720)), inv)
        bag.progress = 1
        item = inv.bag[0]
        bag.drag = {'origin': ('bag', 0), 'item': item, 'lifted': False}
        bag._lift()
        destination = bag.equipped_rects_local[0].move(bag.panel_x, bag.panel_final_y).center
        bag._drop(destination)
        self.assertIs(inv.toolbar[0], item)
        self.assertIsNone(inv.bag[0])

    def test_illustrated_rail_controls_fit_and_keep_shortcuts(self):
        for size in ((1280, 720), (1920, 1080)):
            screen = pygame.Surface(size)
            rail = StagePanel(screen, learning_progress=True)
            self.assertIsNotNone(rail._learning_sprites)
            previous = rail.button_rects['objectives']
            for tab in ('practice', 'progress', 'topic_guidance'):
                rect = rail.button_rects[tab]
                self.assertTrue(screen.get_rect().contains(rect))
                self.assertFalse(previous.colliderect(rect))
                self.assertEqual(rail.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)), tab)
                previous = rect
            self.assertEqual(rail.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)), 'progress')
            self.assertEqual(rail.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_t)), 'topic_guidance')
            rail.draw()
