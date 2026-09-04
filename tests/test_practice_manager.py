import unittest

from src.learning.practice_manager import PracticeManager


class TestPracticeManager(unittest.TestCase):

    def test_uses_every_template_before_repeat(self):
        manager = PracticeManager()

        templates = [
            "a",
            "b",
            "c",
            "d",
            "e",
        ]

        selected = [
            manager.choose_template(
                "variables",
                templates,
            )
            for _ in range(5)
        ]

        self.assertEqual(
            set(selected),
            set(templates),
        )

        self.assertEqual(
            len(selected),
            len(set(selected)),
        )

    def test_new_cycle_does_not_repeat_immediately(self):
        manager = PracticeManager()

        templates = [
            "a",
            "b",
            "c",
            "d",
            "e",
        ]

        first_cycle = [
            manager.choose_template(
                "variables",
                templates,
            )
            for _ in range(5)
        ]

        next_template = manager.choose_template(
            "variables",
            templates,
        )

        self.assertNotEqual(
            first_cycle[-1],
            next_template,
        )


if __name__ == "__main__":
    unittest.main()