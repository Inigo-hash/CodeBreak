"""
practice_manager.py

Chooses practice problems for Code Practice.

Each topic uses a shuffle-bag:
- every template is used once before any repeat
- the bag is reshuffled after it becomes empty
- the first template of a new cycle will not be the
  same as the final template from the previous cycle
"""

import random


class PracticeManager:

    def __init__(self):
        # topic_id -> remaining shuffled template IDs
        self._bags = {}

        # topic_id -> most recently selected template ID
        self._last_template = {}

    def _refill_bag(
        self,
        topic_id,
        template_ids,
    ):
        """
        Create a fresh shuffled bag for one topic.
        """

        bag = list(template_ids)

        random.shuffle(bag)

        previous = self._last_template.get(
            topic_id
        )

        # Prevent the last template from the previous
        # cycle immediately repeating in the new cycle.
        if (
            previous is not None
            and len(bag) > 1
            and bag[-1] == previous
        ):
            swap_index = next(
                (
                    index
                    for index, template_id in enumerate(bag)
                    if template_id != previous
                ),
                None,
            )

            if swap_index is not None:
                bag[-1], bag[swap_index] = (
                    bag[swap_index],
                    bag[-1],
                )

        self._bags[topic_id] = bag

    def choose_template(
        self,
        topic_id,
        template_ids,
    ):
        """
        Return the next template ID for a topic.

        Every supplied template will be selected exactly
        once before the next shuffle begins.
        """

        if not template_ids:
            return None

        bag = self._bags.get(topic_id)

        if not bag:
            self._refill_bag(
                topic_id,
                template_ids,
            )

            bag = self._bags[topic_id]

        template_id = bag.pop()

        self._last_template[topic_id] = template_id

        return template_id