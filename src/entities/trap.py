"""
trap.py

Map-authored, one-shot coding traps.

A trap is a plain object placed on the map's "traps_layer" in Tiled -
no custom Class/type is required, since the dedicated layer is what
identifies it. Walking into one opens a single coding challenge, drawn
only from topics the player has already completed (see
build_trap_challenge below), with a countdown. Solving it in time
avoids the damage; timing out, or leaving early, takes it.

Persistence reuses StageProgress.open_interactable() /
has_opened_interactable() - the same one-shot mechanism chests and
signs already use, keyed by the trap's own Tiled object id. A trap
that has been triggered once (pass or fail) never fires again, and
that survives save/load for free since stage_progress already
round-trips through the save file.
"""

import random

import pygame

from src.data.practice_templates import (
    get_topic_template_ids,
    generate_practice_challenge,
)


DEFAULT_DAMAGE = 20
DEFAULT_TIME_LIMIT = 180  # seconds (3 minutes)


class Trap:
    """One trap zone read from the map's "traps_layer"."""

    def __init__(
        self,
        trap_id,
        rect,
        damage=DEFAULT_DAMAGE,
        time_limit=DEFAULT_TIME_LIMIT,
    ):
        self.trap_id = trap_id
        self.rect = pygame.Rect(rect)
        self.damage = max(0, int(damage or DEFAULT_DAMAGE))
        self.time_limit = max(1, int(time_limit or DEFAULT_TIME_LIMIT))


def load_traps(tmx_data):
    """
    Read every trap object out of the map's "traps_layer".

    Returns an empty list for maps that don't have that layer yet
    (most dungeons/castle maps don't, so this has to be optional, not
    assumed).

    Per-trap damage/time_limit can be overridden with the Tiled custom
    properties "damage" and "time_limit" - both optional, both fall
    back to the defaults above when left blank.
    """

    try:
        layer = tmx_data.get_layer_by_name("traps_layer")
    except ValueError:
        return []

    traps = []

    for obj in layer:

        properties = getattr(obj, "properties", {}) or {}

        rect = pygame.Rect(
            round(obj.x), round(obj.y),
            max(1, round(obj.width)), max(1, round(obj.height)),
        )

        traps.append(
            Trap(
                trap_id=str(getattr(obj, "id", "")),
                rect=rect,
                damage=properties.get("damage", DEFAULT_DAMAGE),
                time_limit=properties.get(
                    "time_limit", DEFAULT_TIME_LIMIT
                ),
            )
        )

    return traps


def build_trap_challenge(topics_completed, practice_manager):
    """
    Pick a random challenge scoped to a topic the player already
    knows, using the exact same shuffle-bag Code Practice uses.

    Returns None when the player hasn't completed any topics yet -
    there is nothing fair to test them on, and callers should fall
    back to a plain damage trap with no challenge in that case.
    """

    if not topics_completed:
        return None

    topic_id = random.choice(topics_completed)
    template_ids = get_topic_template_ids(topic_id)
    template_id = practice_manager.choose_template(topic_id, template_ids)

    if template_id is None:
        return None

    return generate_practice_challenge(template_id)