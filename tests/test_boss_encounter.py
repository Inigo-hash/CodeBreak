"""Boss-zone triggering, boss data, and outcome-branch regressions."""

import os
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from pytmx.util_pygame import load_pygame

from src.data.encounters import BEGINNER_PATH_GIDS
from src.data.enemies import ENEMIES
from src.data.stages import get_stage
from src.data.zones import ZONES
from src.entities.enemy import Enemy
from src.screens.boss_encounter import (
    open_boss_intro, open_boss_result, open_boss_retreat_warning,
)
from src.screens.game import boss_sword_damage
from src.systems.boss_trigger import (
    boss_main_entrance_at, boss_zone_at, required_boss_id,
    should_trigger_boss,
)
from src.systems.combat import ENEMY_BODY_SIZES, ENEMY_STATS
from src.systems.enemy_spawns import resolve_encounter_spawns
from src.systems.stage_progress import StageProgress


class BossTriggerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1, 1))

    def setUp(self):
        self.stage = get_stage("island")
        self.boss_id = required_boss_id(self.stage)
        self.zone = {
            "name": "The Corrupted Core",
            "rect": pygame.Rect(100, 100, 300, 220),
            "is_boss_zone": True,
        }

    def test_corrupted_core_is_the_authored_boss_zone(self):
        boss_zones = [zone for zone in ZONES if zone.get("is_boss_zone")]
        self.assertEqual(len(boss_zones), 1)
        self.assertEqual(boss_zones[0]["name"], "The Corrupted Core")

    def test_trigger_uses_zone_flag_and_only_fires_on_entry(self):
        current = boss_zone_at([self.zone], (150, 150))
        self.assertIs(current, self.zone)
        self.assertTrue(should_trigger_boss(None, current))
        self.assertFalse(should_trigger_boss(current, current))
        self.assertFalse(should_trigger_boss(None, current, defeated=True))
        self.assertFalse(should_trigger_boss(None, current, boss_active=True))
        self.assertIsNone(boss_zone_at([self.zone], (20, 20)))

    def test_retreat_warning_corridor_is_only_at_main_south_entrance(self):
        self.assertTrue(
        boss_main_entrance_at(self.zone, (self.zone["rect"].centerx, 330))
        )
        self.assertFalse(
            boss_main_entrance_at(self.zone, (95, self.zone["rect"].centery))
        )
        self.assertFalse(
            boss_main_entrance_at(self.zone, (405, self.zone["rect"].centery))
        )

    def test_boss_intro_corridor_rejects_side_zone_entry(self):
        side_entry = (self.zone["rect"].left + 4, self.zone["rect"].centery)
        main_entry = (self.zone["rect"].centerx, self.zone["rect"].bottom + 8)
        self.assertFalse(boss_main_entrance_at(self.zone, side_entry))
        self.assertTrue(boss_main_entrance_at(self.zone, main_entry))

    def test_boss_has_distinct_record_stats_body_and_assets(self):
        self.assertEqual(self.boss_id, "corrupted_core_kapre")
        self.assertIn(self.boss_id, self.stage["enemies"])
        self.assertEqual(ENEMIES[self.boss_id]["threat"], "Boss")
        self.assertEqual(ENEMIES[self.boss_id]["family"], "Kapre")
        self.assertIn("Kapre", ENEMIES[self.boss_id]["name"])
        self.assertIn(self.boss_id, ENEMY_STATS)
        self.assertIn(self.boss_id, ENEMY_BODY_SIZES)
        portrait = Path(ENEMIES[self.boss_id]["portrait"])
        self.assertTrue(portrait.is_file())

        enemy = Enemy(
            self.screen, 1000, 800,
            world_x=500, world_y=400,
            enemy_id=self.boss_id,
        )
        for animation in ("walking", "attack", "flinch"):
            self.assertTrue(all(
                enemy.frames[animation][direction]
                for direction in ("north", "south", "east", "west")
            ))
        boss_height = enemy.frames["walking"]["south"][0].get_height()
        tikbalang_target_height = Enemy._asset_config["tikbalang"][3]
        self.assertGreaterEqual(boss_height, round(tikbalang_target_height * 2.2))
        self.assertGreaterEqual(
            Enemy._asset_config[self.boss_id][3], 200
        )
        self.assertGreater(
            ENEMY_BODY_SIZES[self.boss_id][1],
            ENEMY_BODY_SIZES["tikbalang"][1],
        )
        self.assertEqual(ENEMY_STATS[self.boss_id].max_hp, 1000)

    def test_core_armor_phases_take_exactly_thirty_connected_hits(self):
        hp = ENEMY_STATS[self.boss_id].max_hp
        damage_seen = []
        while hp > 0:
            damage = boss_sword_damage(hp)
            damage_seen.append(damage)
            hp = max(0, hp - damage)

        self.assertEqual(len(damage_seen), 30)
        self.assertEqual(sorted(set(damage_seen)), [25, 35, 40, 45])

    def test_boss_defeat_persists_and_completes_its_objective(self):
        progress = StageProgress()
        self.assertTrue(progress.defeat_enemy(self.boss_id))
        completed = progress.sync_objectives(self.stage)
        self.assertIn("island_core_boss", completed)
        restored = StageProgress.from_dict(progress.to_dict())
        self.assertIn(self.boss_id, restored.defeated_enemies)

    def test_boss_resolves_to_walkable_ground_inside_corrupted_core(self):
        map_path = Path(__file__).parents[1] / "assets" / "map" / "tmx" / "basic.tmx"
        tmx = load_pygame(str(map_path))
        tile_size = tmx.tilewidth
        map_width = tmx.width * tile_size
        map_height = tmx.height * tile_size
        runtime_path_gids = {
            runtime_gid
            for authored_gid in BEGINNER_PATH_GIDS
            for runtime_gid, _flags in tmx.map_gid(authored_gid)
        }
        collision_rects = []
        path_cells = set()
        for layer in tmx.visible_layers:
            if not hasattr(layer, "data"):
                continue
            for x, y, gid in layer:
                if not gid:
                    continue
                if layer.name == "Ground Layer 1" and gid in runtime_path_gids:
                    path_cells.add((x, y))
                properties = tmx.get_tile_properties_by_gid(gid)
                if properties and properties.get("collidable"):
                    collision_rects.append(pygame.Rect(
                        x * tile_size, y * tile_size, tile_size, tile_size
                    ))

        core = next(zone for zone in ZONES if zone.get("is_boss_zone"))
        x, y, width, height = core["rect"]
        core_rect = pygame.Rect(
            round(x * map_width), round(y * map_height),
            round(width * map_width), round(height * map_height),
        )

        ocean_padding = 30

        player_spawn = (
            map_width // 2 + tile_size * 7,
            map_height - tile_size * (ocean_padding + 5),
        )

        resolved = resolve_encounter_spawns(
            ({
                "id": "test_core_boss",
                "anchor": (
                    core_rect.centerx / map_width,
                    core_rect.centery / map_height,
                ),
                "zone_size": core_rect.size,
                "spawn_margin": tile_size * 4,
                "require_path": False,
                "enemies": (self.boss_id,),
            },),
            map_width,
            map_height,
            collision_rects,
            path_cells,
            tile_size,
            player_spawn,
        )[0]
        
        body = pygame.Rect(0, 0, *ENEMY_BODY_SIZES[self.boss_id])
        body.center = resolved["position"]
        self.assertTrue(core_rect.contains(body))
        self.assertEqual(body.collidelist(collision_rects), -1)


class BossModalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))
        cls.boss_id = required_boss_id(get_stage("island"))

    def setUp(self):
        pygame.event.clear()

    @staticmethod
    def key_event(key, unicode=""):
        return pygame.event.Event(
            pygame.KEYDOWN, {"key": key, "unicode": unicode}
        )

    def test_intro_draws_then_branches_to_fight(self):
        confirm = self.key_event(pygame.K_e, "e")
        with patch("pygame.event.get", side_effect=[[], [confirm]]):
            self.assertEqual(
                open_boss_intro(self.screen, self.boss_id), "fight"
            )

    def test_intro_escape_retreats(self):
        pygame.event.post(self.key_event(pygame.K_ESCAPE))
        self.assertEqual(
            open_boss_intro(self.screen, self.boss_id), "retreat"
        )

    def test_victory_and_defeat_have_distinct_branches(self):
        pygame.event.post(self.key_event(pygame.K_RETURN, "\r"))
        self.assertEqual(open_boss_result(self.screen, True), "continue")

        pygame.event.post(self.key_event(pygame.K_RETURN, "\r"))
        self.assertEqual(open_boss_result(self.screen, False), "retry")

        pygame.event.post(self.key_event(pygame.K_ESCAPE))
        self.assertEqual(open_boss_result(self.screen, False), "retreat")

    def test_leaving_active_boss_fight_requires_confirmation(self):
        pygame.event.post(self.key_event(pygame.K_RETURN, "\r"))
        self.assertEqual(
            open_boss_retreat_warning(self.screen), "stay"
        )

        pygame.event.post(self.key_event(pygame.K_ESCAPE))
        self.assertEqual(
            open_boss_retreat_warning(self.screen), "leave"
        )


if __name__ == "__main__":
    unittest.main()
