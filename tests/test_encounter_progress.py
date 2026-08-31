"""Encounter clears trigger once and survive save round-trips."""

import unittest
from types import SimpleNamespace

from src.data.encounters import BEGINNER_STAGE_ENCOUNTERS
from src.systems.combat import BASE_SWORD_DAMAGE, ENEMY_STATS
from src.systems.encounter_progress import newly_cleared_encounter_ids
from src.systems.stage_progress import StageProgress


class EncounterProgressTests(unittest.TestCase):
    @staticmethod
    def enemy(group_id, state):
        return SimpleNamespace(group_id=group_id, state=state)

    def test_every_island_encounter_authors_a_coding_topic(self):
        self.assertTrue(BEGINNER_STAGE_ENCOUNTERS)
        self.assertTrue(all(item.get("topic_id")
                            for item in BEGINNER_STAGE_ENCOUNTERS))

    def test_beginner_camps_allow_up_to_nine_balanced_enemies(self):
        sizes = [len(item["enemies"]) for item in BEGINNER_STAGE_ENCOUNTERS]
        self.assertEqual(max(sizes), 9)
        self.assertEqual(sum(sizes), 55)

    def test_regular_enemies_have_short_beginner_kill_times(self):
        expected_hits = {"tiyanak_sinta": 2, "manananggal": 3, "tikbalang": 4}
        for enemy_id, maximum_hits in expected_hits.items():
            hp = ENEMY_STATS[enemy_id].max_hp
            hits = (hp + BASE_SWORD_DAMAGE - 1) // BASE_SWORD_DAMAGE
            self.assertLessEqual(hits, maximum_hits)

    def test_group_clears_only_after_every_member_is_defeated(self):
        enemies = [self.enemy("camp", "defeated"), self.enemy("camp", "chase")]
        self.assertEqual(newly_cleared_encounter_ids(enemies, ("camp",)), ())
        enemies[1].state = "defeated"
        self.assertEqual(
            newly_cleared_encounter_ids(enemies, ("camp",)), ("camp",)
        )

    def test_empty_or_non_authored_groups_do_not_trigger(self):
        boss_wave = [self.enemy("boss_wave_750", "defeated")]
        self.assertEqual(
            newly_cleared_encounter_ids(boss_wave, ("normal_camp",)), ()
        )

    def test_clear_is_one_shot_and_round_trips(self):
        progress = StageProgress()
        self.assertTrue(progress.clear_encounter("camp"))
        self.assertFalse(progress.clear_encounter("camp"))
        restored = StageProgress.from_dict(progress.to_dict())
        self.assertTrue(restored.has_cleared_encounter("camp"))
        enemies = [self.enemy("camp", "defeated")]
        self.assertEqual(newly_cleared_encounter_ids(
            enemies, ("camp",), restored.cleared_encounters
        ), ())


if __name__ == "__main__":
    unittest.main()
