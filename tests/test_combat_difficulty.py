"""Campaign difficulty changes actual fights without removing counterplay."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
import pygame
from src.data.stages import STAGES, stage_world
from src.data.rooms import ROOM_STAGES
from src.systems.rooms import world_for_room
from src.systems.combat import ENEMY_STATS, enemy_stats_for_tier, PlayerCombat
from src.entities.enemy import Enemy


class DifficultyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((640, 640))

    def enemy(self, tier=1, species='duwende_mandurug', **kwargs):
        return Enemy(self.screen, 640, 640, 300, 300, enemy_id=species,
                     combat_scale=.4, combat_tier=tier, **kwargs)

    def begin_attack(self, enemy):
        player = pygame.Rect(0, 0, 16, 16)
        player.center = (enemy.rect.centerx + round(enemy.attack_range * .85), enemy.rect.centery)
        enemy.state = 'chase'
        enemy.update(.001, player, [], 640, 640, navigation_rects=[])
        self.assertEqual(enemy.state, 'attack')
        return player

    def test_beginner_stats_are_exact_original_objects(self):
        for species, base in ENEMY_STATS.items():
            self.assertIs(enemy_stats_for_tier(species), base)
            self.assertIs(enemy_stats_for_tier(species, is_boss=True), base)

    def test_each_species_gets_stronger_across_tiers_without_geometry_or_reward_changes(self):
        for species, base in ENEMY_STATS.items():
            for tier in (2, 3):
                for boss in (False, True):
                    stats = enemy_stats_for_tier(species, tier, is_boss=boss)
                    prior = enemy_stats_for_tier(species, tier - 1, is_boss=boss)
                    self.assertGreater(stats.max_hp, prior.max_hp)
                    self.assertGreater(stats.attack_damage, prior.attack_damage)
                    self.assertGreater(stats.movement_speed, prior.movement_speed)
                    self.assertLess(stats.attack_cooldown, prior.attack_cooldown)
                    self.assertGreaterEqual(stats.attack_cooldown - stats.attack_duration, .16 - 1e-9)
                    for field in ('attack_duration', 'attack_range', 'detection_range', 'awareness_radius',
                                  'disengage_range', 'max_chase_distance', 'assist_range', 'reward_time'):
                        self.assertEqual(getattr(stats, field), getattr(base, field))
            self.assertEqual(ENEMY_STATS[species], base)

    def test_tier_survives_every_castle_room_and_future_citadel_is_not_playable(self):
        self.assertEqual(stage_world(STAGES['island'])['combat_tier'], 1)
        for room in ROOM_STAGES['castle']['rooms']:
            world = world_for_room('castle', stage_world(STAGES['castle']), {'room_id': room})
            self.assertEqual(world['combat_tier'], 2)
        future = stage_world({'id': 'citadel'})
        self.assertEqual(future['combat_tier'], 3)
        self.assertIsNone(future['map'])
        self.assertNotIn('citadel', STAGES)
        self.assertEqual(stage_world({'id': 'custom', 'world': {'combat_tier': 2}})['combat_tier'], 2)

    def test_actual_instances_have_scaled_hp_damage_and_unchanged_bodies(self):
        base, castle, citadel = [self.enemy(tier) for tier in (1, 2, 3)]
        self.assertEqual([e.hp for e in (base, castle, citadel)], [60, 81, 102])
        self.assertEqual(base.rect.size, castle.rect.size)
        for enemy in (base, castle, citadel):
            player = self.begin_attack(enemy)
            damage = enemy.update(enemy.stats.attack_duration * .53, player, [], 640, 640)
            self.assertEqual(damage, enemy.stats.attack_damage)
            self.assertEqual(enemy.update(.01, player, [], 640, 640), 0)

    def test_sword_hit_cannot_cancel_later_stage_attack_but_lethal_hit_can(self):
        for tier in (2, 3):
            enemy = self.enemy(tier)
            player = self.begin_attack(enemy)
            direction, timer, cooldown = enemy.attack_direction, enemy.action_timer, enemy.attack_cooldown
            self.assertTrue(enemy.receive_damage(25))
            self.assertEqual(enemy.hp, enemy.stats.max_hp - 25)
            self.assertEqual(enemy.state, 'attack')
            self.assertEqual((enemy.attack_direction, enemy.action_timer, enemy.attack_cooldown),
                             (direction, timer, cooldown))
            self.assertEqual(enemy.update(enemy.stats.attack_duration * .53, player, [], 640, 640),
                             enemy.stats.attack_damage)
            enemy.receive_damage(enemy.hp)
            self.assertEqual(enemy.state, 'defeated')
            self.assertEqual(enemy.update(.01, player, [], 640, 640), 0)

    def test_beginner_attack_still_interrupts(self):
        enemy = self.enemy()
        self.begin_attack(enemy)
        enemy.receive_damage(25)
        self.assertEqual(enemy.state, 'flinch')

    def test_later_stage_attacks_keep_committed_aim_and_wall_checks(self):
        for tier in (2, 3):
            enemy = self.enemy(tier)
            player = self.begin_attack(enemy)
            enemy.receive_damage(1)
            player.center = (300, 300 - round(enemy.attack_range * .85))
            self.assertEqual(enemy.update(enemy.stats.attack_duration * .53, player, [], 640, 640), 0)
            enemy = self.enemy(tier)
            player = self.begin_attack(enemy)
            wall = pygame.Rect(310, 275, 4, 50)
            self.assertEqual(enemy.update(enemy.stats.attack_duration * .53, player, [wall], 640, 640), 0)

    def test_reset_retains_difficulty_and_boss_uses_separate_hp_budget(self):
        enemy = self.enemy(2, 'zombie_aktan', is_boss=True)
        self.assertEqual(enemy.stats.max_hp, 1080)
        self.assertEqual(enemy.stats.attack_damage, 23)
        enemy.receive_damage(100)
        enemy.reset()
        self.assertEqual(enemy.hp, 1080)
        self.assertTrue(enemy.committed_attacks)
        self.assertEqual(enemy.movement_speed_multiplier, 1)
        self.assertEqual(ENEMY_STATS['zombie_aktan'].max_hp, 900)

    def test_dodge_still_prevents_damage_from_stronger_enemies(self):
        player = PlayerCombat()
        self.assertTrue(player.start_dodge())
        for tier in (2, 3):
            self.assertFalse(player.take_damage(self.enemy(tier).stats.attack_damage, source=object()))
        self.assertEqual(player.hp, player.max_hp)

    def test_actual_chase_speed_and_time_between_attacks_scale(self):
        positions, intervals = [], []
        for tier in (1, 2, 3):
            enemy = self.enemy(tier)
            enemy.state = 'chase'
            far = pygame.Rect(400, 290, 16, 16)
            enemy.update(.1, far, [], 640, 640)
            positions.append(enemy.x)
            enemy = self.enemy(tier)
            player = self.begin_attack(enemy)
            elapsed = 0
            while enemy.attack_count < 2 and elapsed < 3:
                enemy.update(.01, player, [], 640, 640)
                elapsed += .01
            self.assertEqual(enemy.attack_count, 2)
            intervals.append(elapsed)
        self.assertLess(positions[0], positions[1])
        self.assertLess(positions[1], positions[2])
        self.assertGreater(intervals[0], intervals[1])
        self.assertGreater(intervals[1], intervals[2])

    def test_warning_draw_does_not_advance_or_redirect_attack(self):
        enemy = self.enemy(2)
        self.begin_attack(enemy)
        before = enemy.action_timer, enemy.attack_direction, enemy.hp
        enemy.draw_frames(2.5, 0, 0)
        self.assertEqual((enemy.action_timer, enemy.attack_direction, enemy.hp), before)
