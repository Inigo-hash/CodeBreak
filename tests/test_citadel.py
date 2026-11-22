"""Stage 3 mapped curriculum, safe execution, mastery, and developer fixtures."""
import re
import unittest
from src.data.stage3_topics import CITADEL_TOPICS, CITADEL_CHALLENGES, CITADEL_TOPIC_ORDER, CITADEL_CHALLENGE_IDS
from src.data.citadel import CITADEL_STAGE
from src.data.topics import TOPICS, topic_challenge_ids
from src.data.challenges import CHALLENGES
from src.data.developer_solutions import DEVELOPER_SOLUTIONS
from src.learning.challenge_manager import ChallengeManager
from src.learning.sandbox import run_user_code
from src.systems.topic_mastery import complete_topic_challenge


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

    def test_citadel_patrols_added_without_boss_content(self):
        self.assertEqual(set(CITADEL_STAGE["enemies"]), {"white_lady", "zombie_aktan"})
        encounters = CITADEL_STAGE["world"]["encounters"]
        self.assertEqual(len(encounters), 6)
        self.assertEqual(len({camp["id"] for camp in encounters}), 6)
        self.assertTrue(all(camp["require_path"] is False for camp in encounters))
        compositions = [camp["enemies"] for camp in encounters]
        self.assertIn(("zombie_aktan",) * 4, compositions)
        self.assertIn(("white_lady",) * 4, compositions)
        self.assertIn(("zombie_aktan", "white_lady") * 2, compositions)
        self.assertEqual(CITADEL_STAGE["world"]["zones"], ())
        self.assertNotIn("required_boss", CITADEL_STAGE["completion"])
        self.assertEqual(CITADEL_STAGE["completion"]["required_keys"], 6)


if __name__ == "__main__":
    unittest.main()
