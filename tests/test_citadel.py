"""Stage 3 mapped curriculum, safe execution, mastery, and developer fixtures."""
import re
import unittest
import pygame
from pytmx.util_pygame import load_pygame
from src.data.stage3_topics import CITADEL_TOPICS, CITADEL_CHALLENGES, CITADEL_TOPIC_ORDER, CITADEL_CHALLENGE_IDS
from src.data.citadel import CITADEL_STAGE
from src.data.topics import TOPICS, topic_challenge_ids
from src.data.challenges import CHALLENGES
from src.data.developer_solutions import DEVELOPER_SOLUTIONS
from src.learning.challenge_manager import ChallengeManager
from src.learning.sandbox import run_user_code
from src.systems.topic_mastery import complete_topic_challenge
from src.systems.enemy_spawns import resolve_encounter_spawns, body_is_on_path
from src.systems.checkpoints import statue_checkpoint_position
from src.systems.combat import ENEMY_BODY_SIZES


class Stage3CurriculumTests(unittest.TestCase):
    def test_six_existing_tiled_ids_match_topic_registry(self):
        with open("assets/map/tmx/map3.tmx", encoding="utf-8") as source:
            tiled_ids = set(re.findall(r'<property name="topic_id" value="([^"]+)"', source.read()))
        self.assertEqual(tiled_ids, set(CITADEL_TOPIC_ORDER))
        for topic_id, topic in CITADEL_TOPICS.items():
            self.assertIs(TOPICS[topic_id], topic)
            self.assertTrue(set(topic_challenge_ids(topic)).issubset(CHALLENGES))

    def test_topics_are_locked_in_the_authored_sequential_order(self):
        expected = {
            "object_oriented_programming_lesson": [],
            "modules_imports_lesson": ["object_oriented_programming_lesson"],
            "file_handling_lesson": ["modules_imports_lesson"],
            "advance_error_handling_lesson": ["file_handling_lesson"],
            "advance_data_structure_lesson": ["advance_error_handling_lesson"],
            "code_validation_lesson": ["advance_data_structure_lesson"],
        }
        self.assertEqual(
            {topic_id: topic["requirements"] for topic_id, topic in CITADEL_TOPICS.items()},
            expected,
        )

    def test_problem_counts_match_reference_outline(self):
        self.assertEqual([len(topic_challenge_ids(CITADEL_TOPICS[tid])) for tid in CITADEL_TOPIC_ORDER], [6, 2, 2, 1, 3, 1])
        self.assertEqual(len(CITADEL_CHALLENGE_IDS), 15)

    def test_every_stage3_problem_has_a_valid_f7_solution(self):
        manager = ChallengeManager()
        self.assertTrue(set(CITADEL_CHALLENGE_IDS).issubset(DEVELOPER_SOLUTIONS))
        for challenge_id in CITADEL_CHALLENGE_IDS:
            with self.subTest(challenge=challenge_id):
                passed, feedback = manager.validate(CHALLENGES[challenge_id], DEVELOPER_SOLUTIONS[challenge_id])
                self.assertTrue(passed, feedback)

    def test_safe_standard_imports_work_but_other_imports_are_rejected(self):
        self.assertTrue(run_user_code("import math\nvalue = math.sqrt(81)")["success"])
        self.assertTrue(run_user_code("import json\nvalue = json.loads('{\\"x\\": 2}')")["success"])
        self.assertFalse(run_user_code("import os")["success"])

    def test_mastery_key_requires_every_challenge_in_topic(self):
        state = {"keys": 0, "challenges_passed": [], "topics_completed": []}
        topic_id = CITADEL_TOPIC_ORDER[0]
        ids = topic_challenge_ids(CITADEL_TOPICS[topic_id])
        state = complete_topic_challenge(state, CITADEL_STAGE, topic_id, ids[0])
        self.assertEqual(state["keys"], 0)
        for challenge_id in ids[1:]:
            state = complete_topic_challenge(state, CITADEL_STAGE, topic_id, challenge_id)
        self.assertEqual(state["keys"], 1)
        self.assertIn(topic_id, state["topics_completed"])

    def test_citadel_patrol_groups_stay_near_their_authored_anchors(self):
        pygame.init()
        try:
            world = CITADEL_STAGE["world"]
            tmx = load_pygame(world["map"])
            runtime_path_gids = {
                runtime_gid
                for authored_gid in world["path_gids"]
                for runtime_gid, _flags in (tmx.map_gid(authored_gid) or ())
            }
            path_cells = {
                (x, y)
                for layer in tmx.visible_layers
                if getattr(layer, "name", None) == world["path_layer"]
                for x, y, gid in layer
                if gid in runtime_path_gids
            }
            # Match the real game loader: enemy placement must account for
            # collidable tiles and Tiled object boundaries, not an empty
            # collision list (which made the old spawn test over-optimistic).
            collision_rects = []
            for layer in tmx.visible_layers:
                if not hasattr(layer, "data"):
                    continue
                for x, y, gid in layer:
                    props = tmx.get_tile_properties_by_gid(gid) if gid else None
                    if props and props.get("collidable"):
                        collision_rects.append(pygame.Rect(
                            x * tmx.tilewidth, y * tmx.tileheight,
                            tmx.tilewidth, tmx.tileheight,
                        ))
            from src.screens.game import object_collision_rects
            collision_rects.extend(object_collision_rects(tmx))
            spawns = resolve_encounter_spawns(
                world["encounters"], tmx.width * tmx.tilewidth,
                tmx.height * tmx.tileheight, collision_rects, path_cells, tmx.tilewidth,
                (round(86 / 120 * 1920), round(92 / 120 * 1920)),
                zones=world["zones"],
                max_enemies=world.get("max_enemies"),
            )
        finally:
            pygame.quit()

        self.assertEqual(world["max_enemies"], 23)
        self.assertEqual(len(spawns), 23)
        bodies = []
        for spawn in spawns:
            body = pygame.Rect(0, 0, *ENEMY_BODY_SIZES[spawn["enemy_id"]])
            body.center = spawn["position"]
            self.assertTrue(body_is_on_path(body, path_cells, 16))
            self.assertTrue(all(not body.colliderect(blocker) for blocker in collision_rects))
            self.assertTrue(all(not body.colliderect(other) for other in bodies))
            bodies.append(body)
        by_camp = {}
        for spawn in spawns:
            by_camp.setdefault(spawn["encounter_id"], []).append(spawn)
        for camp in world["encounters"]:
            anchor = (round(camp["anchor"][0] * 1920),
                      round(camp["anchor"][1] * 1920))
            width, height = camp["zone_size"]
            margin = camp.get("spawn_margin", 0)
            half_w, half_h = width // 2 - margin, height // 2 - margin
            with self.subTest(camp=camp["id"]):
                self.assertLessEqual(len(by_camp[camp["id"]]), len(camp["enemies"]))
                for spawn in by_camp[camp["id"]]:
                    x, y = spawn["position"]
                    body = pygame.Rect(0, 0, *ENEMY_BODY_SIZES[spawn["enemy_id"]])
                    body.center = spawn["position"]
                    self.assertTrue(body_is_on_path(body, path_cells, 16))
                    # A spawn may leave its local camp only when local land
                    # was exhausted; it must still remain on island path.


    def test_statue_checkpoint_is_on_land_beside_the_statue(self):
        pygame.init()
        try:
            from pytmx.util_pygame import load_pygame
            from src.screens.game import load_interactables, object_collision_rects
            world = CITADEL_STAGE["world"]
            tmx = load_pygame(world["map"])
            runtime_path_gids = {
                runtime_gid
                for authored_gid in world["path_gids"]
                for runtime_gid, _flags in (tmx.map_gid(authored_gid) or ())
            }
            path_cells = {
                (x, y)
                for layer in tmx.visible_layers
                if getattr(layer, "name", None) == world["path_layer"]
                for x, y, gid in layer
                if gid in runtime_path_gids
            }
            statue = next(item for item in load_interactables(tmx)
                          if item["actions"] == "search_statue")
            position = statue_checkpoint_position(
                statue["rect"], (16, 16), tmx.width * 16, tmx.height * 16,
                path_cells, 16, object_collision_rects(tmx),
            )
            self.assertIsNotNone(position)
            player = pygame.Rect(position, (16, 16))
            self.assertFalse(player.colliderect(statue["rect"]))
            self.assertGreaterEqual(player.centerx, statue["rect"].right)
            self.assertTrue(body_is_on_path(player, path_cells, 16))
        finally:
            pygame.quit()

    def test_citadel_boss_has_a_collision_free_spawn_inside_its_arena(self):
        pygame.init()
        try:
            from src.screens.game import object_collision_rects
            world = CITADEL_STAGE["world"]
            tmx = load_pygame(world["map"])
            collision_rects = []
            for layer in tmx.visible_layers:
                if not hasattr(layer, "data"):
                    continue
                for x, y, gid in layer:
                    props = tmx.get_tile_properties_by_gid(gid) if gid else None
                    if props and props.get("collidable"):
                        collision_rects.append(pygame.Rect(
                            x * tmx.tilewidth, y * tmx.tileheight,
                            tmx.tilewidth, tmx.tileheight,
                        ))
            collision_rects.extend(object_collision_rects(tmx))
            boss_zone = next(z for z in world["zones"] if z.get("is_boss_zone"))
            map_width = tmx.width * tmx.tilewidth
            map_height = tmx.height * tmx.tileheight
            spawn = resolve_encounter_spawns(
                ({
                    "id": "citadel_boss",
                    "anchor": (
                        boss_zone["rect"][0] + boss_zone["rect"][2] / 2,
                        boss_zone["rect"][1] + boss_zone["rect"][3] / 2,
                    ),
                    "zone_size": (
                        round(boss_zone["rect"][2] * map_width),
                        round(boss_zone["rect"][3] * map_height),
                    ),
                    "spawn_margin": world["boss_spawn_margin"],
                    "require_path": False,
                    "enemies": ("zombie_lapu_lapu",),
                },),
                map_width, map_height, collision_rects, set(), tmx.tilewidth,
                (round(86 / 120 * map_width), round(92 / 120 * map_height)),
                zones=world["zones"],
            )
        finally:
            pygame.quit()

        self.assertEqual(len(spawn), 1)
        boss_body = pygame.Rect(0, 0, *ENEMY_BODY_SIZES["zombie_lapu_lapu"])
        boss_body.center = spawn[0]["position"]
        self.assertTrue(all(not boss_body.colliderect(blocker) for blocker in collision_rects))
        self.assertTrue(spawn[0]["zone_rect"].contains(boss_body))

    def test_citadel_boss_and_assessment_are_progression_gated(self):
        from src.data.final_assessments import assessment_ids_for_stage
        from src.data.enemies import ENEMIES
        from src.systems.combat import BOSS_PHASES
        completion = CITADEL_STAGE["completion"]
        self.assertEqual(completion["required_keys"], 6)
        self.assertEqual(completion["required_boss"], "zombie_lapu_lapu")
        self.assertEqual(completion["required_final_challenge"], "citadel_expedition_final")
        self.assertEqual(
            assessment_ids_for_stage(CITADEL_STAGE),
            ("citadel_expedition_final", "citadel_json_final", "citadel_route_final"),
        )
        self.assertIn("zombie_lapu_lapu", ENEMIES)
        self.assertIn("zombie_lapu_lapu", ENEMY_BODY_SIZES)
        self.assertIn("zombie_lapu_lapu", BOSS_PHASES)
        boss_zones = [zone for zone in CITADEL_STAGE["world"]["zones"] if zone.get("is_boss_zone")]
        self.assertEqual(len(boss_zones), 1)
        self.assertEqual(boss_zones[0]["name"], "The Lapu-Lapu Arena")
        self.assertTrue(CITADEL_STAGE["progress"]["enabled"])
        self.assertEqual(len(CITADEL_STAGE["world"]["encounters"]), 7)



if __name__ == "__main__":
    unittest.main()
