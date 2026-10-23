"""Portrait selection, readable resources and bounded character cards."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from itertools import combinations
from pathlib import Path
import unittest
from unittest.mock import patch
import pygame
from src.data.characters import CHARACTERS
from src.data.stages import get_stage
from src.screens.mang_tahimik import tutor_minimap_rect
from src.screens.profile import profile_layout, profile_screen
from src.settings_state import settings_state
from src.ui.gameplay_hud import (GameplayHUD, character_card_layout, load_portrait,
    draw_resource_meter, _portrait_tile, HEAL_GREEN, TORCH_AMBER)
from src.ui.text_layout import fit_text
from src.ui.theme import body_font, title_font, clear_font_cache


class CharacterHudTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((960, 640))

    def tearDown(self):
        clear_font_cache()

    def test_both_characters_have_dedicated_cached_illustrations(self):
        portraits = []
        for identity, record in CHARACTERS.items():
            self.assertTrue(Path(record['portrait']).is_file())
            self.assertNotEqual(record['portrait'], record['preview'])
            image = load_portrait(identity)
            self.assertGreaterEqual(min(image.get_size()), 512)
            self.assertIs(image, load_portrait(identity))
            portraits.append(image)
        self.assertNotEqual(pygame.image.tobytes(portraits[0], 'RGB'),
                            pygame.image.tobytes(portraits[1], 'RGB'))
        for old_id in ('old-save-id', None, [], {}):
            self.assertIs(load_portrait(old_id), load_portrait('man'))

    def test_card_rows_fit_and_do_not_hide_the_minimap_at_large_text_sizes(self):
        for size in ((640, 480), (800, 600), (1280, 720), (1920, 1080), (2560, 1440)):
            for font_size in (12, 20, 28):
                with self.subTest(size=size, font=font_size), patch.dict(settings_state, font_size=font_size):
                    clear_font_cache()
                    screen = pygame.Surface(size)
                    hud = GameplayHUD(screen, {'character_id': 'woman', 'hearts': 4}, get_stage('castle'))
                    card, *parts = character_card_layout(size, hud.bold.get_height(), hud.small.get_height())
                    self.assertTrue(screen.get_rect().contains(card))
                    self.assertTrue(all(card.contains(part) for part in parts))
                    self.assertFalse(any(a.colliderect(b) for a, b in combinations(parts, 2)))
                    with patch.object(hud, 'draw_stage_progress', wraps=hud.draw_stage_progress) as progress:
                        hud.draw(current_hp=30, max_hp=100, current_energy=25, max_energy=100)
                    self.assertEqual(hud.profile_rect, card)
                    stage_card = progress.call_args.args[0]
                    self.assertEqual(stage_card.width, card.width)
                    self.assertFalse(card.colliderect(stage_card))
                    self.assertFalse(stage_card.colliderect(tutor_minimap_rect(screen)))

    def test_rendered_profile_text_stays_inside_its_card_without_overlaps(self):
        # Record the actual glyph surfaces, not only planned rectangles.
        class RecordingSurface(pygame.Surface):
            def __init__(self, size):
                super().__init__(size)
                self.text = []
            def blit(self, source, destination, *args, **kwargs):
                if id(source) in labels:
                    position = destination.topleft if isinstance(destination, pygame.Rect) else destination[:2]
                    self.text.append((labels[id(source)][1], source.get_rect(topleft=position)))
                return super().blit(source, destination, *args, **kwargs)
        def record(font, text, color, size):
            image = fit_text(font, text, color, size)
            labels[id(image)] = image, text
            return image
        for size, identity, font_size in (((640, 480), 'woman', 28),
                                        ((1920, 1080), 'man', 20),
                                        ((1920, 1080), 'man', 12)):
            labels = {}
            with patch.dict(settings_state, font_size=font_size):
                clear_font_cache()
                screen = RecordingSurface(size)
                hud = GameplayHUD(screen, {'character_id': identity, 'hearts': 3}, get_stage('castle'))
                hud.profile_rect = character_card_layout(size, hud.bold.get_height(), hud.small.get_height())[0]
                with patch('src.ui.gameplay_hud.fit_text', side_effect=record):
                    hud.draw_character_profile(80, 100, current_energy=42, max_energy=100)
            self.assertTrue(all(hud.profile_rect.contains(rect) for _, rect in screen.text))
            for (text, a), (other, b) in combinations(screen.text, 2):
                self.assertFalse(a.colliderect(b), (text, other))

    def test_meter_clamps_values_and_never_shows_unknown_energy_as_full(self):
        screen = pygame.Surface((320, 100))
        rect = pygame.Rect(10, 10, 220, 32)
        font = body_font(15)
        for current, maximum, expected in ((300, 100, '100 / 100'), (-4, 100, '0 / 100'),
                                           (None, 100, '-- / --'), (0, 0, '-- / --')):
            with patch('src.ui.gameplay_hud.fit_text', wraps=fit_text) as render:
                bar = draw_resource_meter(screen, font, rect, 'ENERGY', current, maximum)
            self.assertEqual(render.call_args_list[1].args[1], expected)
            self.assertTrue(rect.contains(bar))

    def test_recovery_highlights_and_portrait_cache_are_preserved(self):
        screen = pygame.Surface((1280, 720))
        hud = GameplayHUD(screen, {'hearts': 5}, get_stage('island'))
        _portrait_tile.cache_clear()
        bars = []
        def record_meter(*args, **kwargs):
            bar = draw_resource_meter(*args, **kwargs)
            bars.append(bar)
            return bar
        for _ in range(2):
            with patch('src.ui.gameplay_hud.draw_resource_meter', side_effect=record_meter):
                hud.draw(current_hp=40, max_hp=100, current_energy=30, max_energy=100,
                         hp_healing=True, energy_boosted=True)
        self.assertEqual(_portrait_tile.cache_info().misses, 1)
        self.assertGreaterEqual(_portrait_tile.cache_info().hits, 1)
        health, energy = bars[-2:]
        self.assertEqual(screen.get_at((health.x+4, health.y+3))[:3], HEAL_GREEN)
        self.assertEqual(screen.get_at((energy.x+4, energy.y+3))[:3], TORCH_AMBER)

    def test_expanded_profile_fits_and_closes_with_keyboard_or_mouse(self):
        for size in ((640, 480), (1280, 720), (1920, 1080)):
            with patch.dict(settings_state, font_size=28):
                clear_font_cache()
                screen = pygame.Surface(size)
                layout = profile_layout(size, title_font(26).get_height(), title_font(24).get_height(), body_font(15, True).get_height())
                panel = layout.pop('panel')
                self.assertTrue(screen.get_rect().contains(panel))
                self.assertTrue(all(panel.contains(part) for part in layout.values()))
                self.assertFalse(any(a.colliderect(b) for a, b in combinations(layout.values(), 2)))
                events = (pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
                          pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=layout['back'].center))
                for event in events:
                    with patch('pygame.event.get', return_value=[event]):
                        profile_screen(screen, character_id='woman', name='A very long explorer name', max_pp=0)
