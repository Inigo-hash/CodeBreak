"""Action hierarchy, focus visibility, disabled state and text contrast."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
from unittest.mock import patch
import pygame
from src.ui.theme import (draw_button, title_font, readable_button_text,
                          UI_COLORS, TIER_PRIMARY, TIER_SECONDARY,
                          TIER_SUCCESS, TIER_DANGER)


class ButtonDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((800, 600))

    def render(self, tier, **options):
        surface = pygame.Surface((300, 100))
        draw_button(surface, pygame.Rect(20, 20, 260, 52), 'CONTINUE',
                    title_font(20), tier=tier, **options)
        return surface

    def test_action_roles_have_distinct_filled_backgrounds(self):
        colors = {tuple(self.render(tier).get_at((40, 46))) for tier in
                  (TIER_PRIMARY, TIER_SECONDARY, TIER_SUCCESS, TIER_DANGER)}
        self.assertEqual(len(colors), 4)

    def test_disabled_button_does_not_glow_when_hovered(self):
        plain = self.render(TIER_PRIMARY, enabled=False)
        hovered = self.render(TIER_PRIMARY, enabled=False, hovered=True)
        self.assertEqual(pygame.image.tostring(plain, 'RGB'),
                         pygame.image.tostring(hovered, 'RGB'))

    def test_keyboard_focus_has_an_outline_beyond_the_button(self):
        plain = self.render(TIER_SECONDARY)
        focused = self.render(TIER_SECONDARY, focused=True)
        self.assertNotEqual(plain.get_at((15, 40)), focused.get_at((15, 40)))

    def test_editor_action_text_adapts_to_light_and_dark_fills(self):
        self.assertEqual(readable_button_text((70, 200, 120)), (12, 24, 18))
        self.assertEqual(readable_button_text((0, 100, 0)), UI_COLORS['text'])

    @patch('pygame.event.get')
    def test_boss_dialog_tab_then_enter_activates_selected_alternative(self, events):
        from src.screens.boss_encounter import _boss_modal
        events.return_value = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB),
                               pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]
        result = _boss_modal(pygame.Surface((800, 600)), 'Choose', '', [],
                             ('BEGIN FIGHT', 'fight'), ('RETREAT', 'retreat'))
        self.assertEqual(result, 'retreat')

    @patch('pygame.event.get')
    def test_boss_dialog_enter_keeps_primary_default(self, events):
        from src.screens.boss_encounter import _boss_modal
        events.return_value = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]
        result = _boss_modal(pygame.Surface((800, 600)), 'Choose', '', [],
                             ('BEGIN FIGHT', 'fight'), ('RETREAT', 'retreat'))
        self.assertEqual(result, 'fight')
