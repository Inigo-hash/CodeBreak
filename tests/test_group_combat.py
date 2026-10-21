"""A crowd can land independent strikes without defeating dodge immunity."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import math
import unittest

import pygame
from src.entities.enemy import Enemy
from src.systems.combat import ENEMY_STATS, PlayerCombat, PLAYER_INVULNERABILITY
from src.ui.damage_numbers import DamageNumbers


class GroupCombatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((640, 480))

    def test_mixed_group_attacks_together_and_every_strike_deals_damage(self):
        player = PlayerCombat()
        rect = pygame.Rect(290, 230, 20, 20)
        specs = (('tiyanak_sinta', (270, 240)), ('tiyanak_sinta', (330, 240)),
                 ('manananggal', (300, 210)), ('tikbalang', (300, 270)))
        enemies = [Enemy(self.screen, 640, 480, *position, enemy_id=identity,
                         combat_scale=.5) for identity, position in specs]
        effects = DamageNumbers()
        for enemy in enemies:
            enemy.state = 'chase'
            enemy.update(.001, rect, [], 640, 480, navigation_rects=[])
            self.assertEqual(enemy.state, 'attack')

        for _ in range(75):
            player.update(.01)
            for enemy in enemies:
                damage = enemy.update(.01, rect, [], 640, 480, navigation_rects=[])
                if damage:
                    effects.apply_damage(player, rect.center, damage, source=enemy)
        expected = sum(enemy.stats.attack_damage for enemy in enemies)
        self.assertEqual(player.hp, player.max_hp - expected)
        self.assertEqual(len(effects.hits), len(enemies))

    def test_grace_blocks_repeat_hits_from_one_enemy_but_not_another(self):
        player = PlayerCombat()
        first, second = object(), object()
        self.assertTrue(player.take_damage(5, source=first))
        self.assertFalse(player.take_damage(5, source=first))
        self.assertTrue(player.take_damage(8, source=second))
        self.assertEqual(player.hp, player.max_hp - 13)
        player.update(PLAYER_INVULNERABILITY + .01)
        self.assertTrue(player.take_damage(5, source=first))

    def test_every_species_can_hit_a_stationary_player_at_diagonal_angles(self):
        # Radial range used to start a cardinal swing which could never
        # reach diagonal targets. The enemy then stood still and missed
        # forever. Exercise campaign and tutorial combat scales.
        for identity in ENEMY_STATS:
            for scale in (.5, 1.0):
                enemy = Enemy(self.screen, 640, 480, 320, 240,
                              enemy_id=identity, combat_scale=scale)
                for angle in range(0, 360, 45):
                    with self.subTest(enemy=identity, scale=scale, angle=angle):
                        enemy.reset()
                        distance = enemy.attack_range * .95
                        rect = pygame.Rect(0, 0, 16, 16)
                        rect.center = (round(320 + math.cos(math.radians(angle)) * distance),
                                       round(240 + math.sin(math.radians(angle)) * distance))
                        enemy.state = 'chase'
                        enemy.update(.001, rect, [], 640, 480, navigation_rects=[])
                        self.assertEqual(enemy.state, 'attack')
                        damage = enemy.update(enemy.stats.attack_duration * .53,
                                              rect, [], 640, 480, navigation_rects=[])
                        self.assertEqual(damage, enemy.stats.attack_damage)

    def test_moving_sideways_after_diagonal_windup_evades_every_species(self):
        for identity in ENEMY_STATS:
            for scale in (.5, 1.0):
                with self.subTest(enemy=identity, scale=scale):
                    enemy = Enemy(self.screen, 640, 480, 320, 240,
                                  enemy_id=identity, combat_scale=scale)
                    offset = round(enemy.attack_range * .95 / math.sqrt(2))
                    rect = pygame.Rect(0, 0, 16, 16)
                    rect.center = (320 + offset, 240 - offset)
                    enemy.state = 'chase'
                    enemy.update(.001, rect, [], 640, 480, navigation_rects=[])
                    self.assertEqual(enemy.state, 'attack')
                    # Stay within melee range but move 90 degrees around
                    # the attacker after it has committed to the northeast.
                    rect.center = (320 - offset, 240 - offset)
                    damage = enemy.update(enemy.stats.attack_duration * .53,
                                          rect, [], 640, 480, navigation_rects=[])
                    self.assertEqual(damage, 0)

    def test_dodge_protects_against_every_attacker(self):
        player = PlayerCombat()
        self.assertTrue(player.start_dodge())
        for _ in range(5):
            self.assertFalse(player.take_damage(10, source=object()))
        self.assertEqual(player.hp, player.max_hp)
        player.update(.25)
        self.assertTrue(player.take_damage(10, source=object()))

    def test_lethal_group_damage_and_respawn_clear_attack_grace(self):
        player = PlayerCombat()
        first, second = object(), object()
        player.hp = 10
        self.assertTrue(player.take_damage(6, source=first))
        self.assertTrue(player.take_damage(6, source=second))
        self.assertEqual(player.hp, 0)
        self.assertEqual(player.state, 'defeated')
        self.assertFalse(player.take_damage(6, source=object()))
        player.reset()
        self.assertTrue(player.take_damage(6, source=first))
