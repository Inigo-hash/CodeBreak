"""Every Castle room resolves complete, reachable and bounded camps."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from collections import deque
import unittest
import pygame
from pytmx.util_pygame import load_pygame
from src.data.rooms import ROOM_STAGES
from src.screens.game import object_collision_rects
from src.systems.enemy_spawns import resolve_encounter_spawns
from src.systems.combat import ENEMY_BODY_SIZES
from src.entities.enemy import Enemy


class CastleRoomEnemyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((640, 640))
        cls.rooms = {}
        for name, room in ROOM_STAGES['castle']['rooms'].items():
            tmx = load_pygame(room['map'])
            bounds = pygame.Rect(0, 0, tmx.width * 16, tmx.height * 16)
            blockers = object_collision_rects(tmx) + [
                pygame.Rect(x*16, y*16, 16, 16)
                for layer in tmx.visible_layers if hasattr(layer, 'data')
                for x, y, gid in layer if gid and
                (tmx.get_tile_properties_by_gid(gid) or {}).get('collidable')]
            start = tuple(round(v*16) for v in room['spawn'])
            seen = {start}
            queue = deque([start])
            while queue:
                x, y = queue.popleft()
                for dx, dy in ((8, 0), (-8, 0), (0, 8), (0, -8)):
                    point = x+dx, y+dy
                    body = pygame.Rect(*point, 16, 16)
                    if point not in seen and bounds.contains(body) and body.collidelist(blockers) < 0:
                        seen.add(point)
                        queue.append(point)
            world = room['world']
            spawns = resolve_encounter_spawns(world['encounters'], bounds.w, bounds.h,
                blockers, set(), 16, start, zones=world['zones'])
            cls.rooms[name] = room, bounds, blockers, seen, spawns

    def test_all_twenty_enemies_resolve_reachably_with_safe_doors(self):
        ids = []
        for name, (room, bounds, blockers, seen, spawns) in self.rooms.items():
            with self.subTest(room=name):
                self.assertEqual(len(spawns), 4, 'Never silently omit an authored member')
                ids.extend(e['id'] for e in room['world']['encounters'])
                for spawn in spawns:
                    body = pygame.Rect(0, 0, *ENEMY_BODY_SIZES[spawn['enemy_id']])
                    body.center = spawn['position']
                    self.assertEqual(body.collidelist(blockers), -1)
                    self.assertTrue(any(pygame.Rect(*p, 16, 16).collidepoint(body.center) for p in seen))
                    patrol = pygame.Rect(spawn['zone_rect'])
                    self.assertTrue(patrol.contains(body))
                    for arrival in [room['spawn'], *room['arrivals'].values()]:
                        safe = pygame.Rect(round(arrival[0]*16), round(arrival[1]*16), 16, 16).inflate(48, 48)
                        self.assertFalse(patrol.colliderect(safe))
                    for route in room['routes']:
                        door = pygame.Rect(*(round(v*16) for v in route['rect']))
                        self.assertFalse(patrol.colliderect(door))
        self.assertEqual(len(ids), len(set(ids)))

    def test_actual_pursuit_stays_inside_chase_bounds(self):
        for name, (room, bounds, blockers, seen, spawns) in self.rooms.items():
            for spawn in spawns:
                with self.subTest(room=name, camp=spawn['encounter_id']):
                    enemy = Enemy(self.screen, bounds.w, bounds.h, *spawn['position'],
                        enemy_id=spawn['enemy_id'], zone_rect=spawn['zone_rect'])
                    player = pygame.Rect(round(room['spawn'][0]*16), round(room['spawn'][1]*16), 16, 16)
                    enemy.state = 'chase'
                    for _ in range(40):
                        enemy.update(.05, player, blockers + [player], bounds.w, bounds.h, navigation_rects=blockers)
                        self.assertTrue(enemy.chase_bounds.contains(enemy.rect))
                        self.assertEqual(enemy.rect.collidelist(blockers), -1)

    def test_stage_two_roster_and_kapre_two_attack_sequences(self):
        from src.data.stages import get_stage
        self.assertEqual(set(get_stage('castle')['enemies']),
                         {'duwende_mandurug', 'kapre_usikan', 'white_lady', 'zombie_aktan'})
        for species in ('kapre_usikan', 'corrupted_core_kapre'):
            enemy = Enemy(self.screen, 640, 640, 320, 240, enemy_id=species)
            player = pygame.Rect(310, 270, 16, 16)
            for expected in ('attack', 'ultimate', 'attack'):
                enemy.state = 'chase'
                enemy.attack_cooldown = 0
                enemy.update(.01, player, [], 640, 640)
                self.assertEqual(enemy.state, 'attack')
                self.assertEqual(enemy.attack_animation, expected)
                self.assertEqual(len(enemy.frames[expected]['south']), 9)
                enemy.draw_frames(1, 0, 0)
            enemy.reset()
            self.assertEqual(enemy.attack_count, 0)
        for species in ('white_lady', 'zombie_aktan'):
            enemy = Enemy(self.screen, 640, 640, 320, 240, enemy_id=species)
            self.assertTrue(all(enemy.frames[group][d] for group in enemy.frames
                                for d in ('north', 'south', 'east', 'west')))

    def test_aktan_arena_resolves_and_requires_five_keys(self):
        from src.data.stages import get_stage
        from src.systems.stage_gate import evaluate_boss_access, evaluate_stage_gate
        stage = get_stage('castle')
        self.assertEqual(stage['completion']['required_boss'], 'zombie_aktan')
        room, bounds, blockers, seen, _ = self.rooms['throne']
        zone = next(z for z in room['world']['zones'] if z.get('is_boss_zone'))
        x, y, w, h = zone['rect']
        records = resolve_encounter_spawns(({'id': 'castle_boss',
            'anchor': (x+w/2, y+h/2), 'enemies': ('zombie_aktan',),
            'spawn_margin': room['world']['boss_spawn_margin'], 'require_path': False},),
            bounds.w, bounds.h, blockers, set(), 16, (320, 528), zones=room['world']['zones'])
        self.assertEqual(len(records), 1)
        self.assertTrue(any(pygame.Rect(*p, 16, 16).collidepoint(records[0]['position']) for p in seen))
        self.assertFalse(evaluate_boss_access(stage, 1, stage['manual']['topics']).unlocked)
        self.assertTrue(evaluate_boss_access(stage, 5, stage['manual']['topics']).unlocked)
        self.assertFalse(evaluate_stage_gate(stage, 5, stage['manual']['topics'], ['zombie_aktan']).unlocked)

    def test_enemies_cross_patrol_edge_and_land_melee_at_game_zoom(self):
        for species in ('duwende_mandurug', 'kapre_usikan', 'white_lady'):
            with self.subTest(enemy=species):
                enemy = Enemy(self.screen, 640, 640, 320, 240, enemy_id=species,
                    zone_rect=(290, 210, 60, 60), chase_range=120, combat_scale=1/2.5)
                enemy.state = 'chase'
                player = pygame.Rect(382, 232, 16, 16)
                damage = 0
                crossed = False
                for _ in range(100):
                    damage += enemy.update(.05, player, [player], 640, 640, navigation_rects=[])
                    crossed |= not enemy.zone.contains(enemy.rect)
                self.assertTrue(crossed, 'Patrol edge must not stop pursuit')
                self.assertGreater(damage, 0, 'Enemy must land a close-range attack')

    def test_home_leash_does_not_cancel_close_attack_or_allow_wall_hits(self):
        enemy = Enemy(self.screen, 640, 640, 320, 240, enemy_id='kapre_usikan',
                      chase_range=80, combat_scale=1/2.5)
        enemy.rect.center = (450, 240)
        enemy.x, enemy.y = enemy.rect.topleft
        enemy.state = 'return'
        player = pygame.Rect(470, 232, 16, 16)
        damage = sum(enemy.update(.05, player, [player], 640, 640, navigation_rects=[])
                     for _ in range(30))
        self.assertGreater(damage, 0)
        enemy.reset()
        enemy.state = 'chase'
        player.center = (350, 240)
        wall = pygame.Rect(338, 200, 5, 80)
        self.assertEqual(sum(enemy.update(.05, player, [wall, player], 640, 640,
                                         navigation_rects=[wall]) for _ in range(40)), 0)

    def test_unlimited_training_pursuit_uses_finite_map_bounds(self):
        enemy = Enemy(self.screen, 1280, 720, 320, 240,
                      chase_range=float('inf'), disengage_range=float('inf'))
        self.assertEqual(enemy.chase_bounds, pygame.Rect(0, 0, 1280, 720))
        enemy.state = 'chase'
        enemy.update(.05, pygame.Rect(500, 240, 16, 16), [], 1280, 720)
        self.assertTrue(enemy.chase_bounds.contains(enemy.rect))


if __name__ == '__main__':
    unittest.main()
