"""Rules for earning stage keys and unlocking a stage exit.

The rules live outside ``game.py`` so loading old saves, awarding a newly
completed lesson, and checking the exit all use the same source of truth.
"""

from dataclasses import dataclass

from src.data.challenges import CHALLENGES


DEFAULT_REQUIRED_KEYS = 10


@dataclass(frozen=True)
class StageGateStatus:
    """Everything the gate UI needs to explain why it is locked."""

    unlocked: bool
    keys: int
    required_keys: int
    completed_topics: int
    required_topics: int
    missing_topic_ids: tuple[str, ...]
    missing_topic_titles: tuple[str, ...]


def required_topic_ids(stage):
    """Return the stage's required lesson challenges in authored order."""

    return tuple(stage.get("manual", {}).get("topics", ()))


def required_key_count(stage):
    """Return the number of keys required by this stage's exit."""

    configured = stage.get("completion", {}).get(
        "required_keys", DEFAULT_REQUIRED_KEYS
    )
    try:
        return max(0, int(configured))
    except (TypeError, ValueError):
        return DEFAULT_REQUIRED_KEYS


def topic_key_reward(stage, challenge_id):
    """Return the authored key reward for a required lesson challenge."""

    rewards = stage.get("completion", {}).get("topic_key_rewards", {})
    try:
        return max(0, int(rewards.get(challenge_id, 1)))
    except (TypeError, ValueError):
        return 0


def award_topic_keys(current_keys, stage, challenge_id):
    """Award one first-completion reward without exceeding the stage cap."""

    maximum = required_key_count(stage)
    current = max(0, min(maximum, int(current_keys or 0)))
    if challenge_id not in required_topic_ids(stage):
        return current
    return min(maximum, current + topic_key_reward(stage, challenge_id))


def earned_topic_keys(stage, challenges_passed):
    """Rebuild the key count earned from required topics in an older save."""

    completed = set(challenges_passed or ())
    earned = sum(
        topic_key_reward(stage, challenge_id)
        for challenge_id in required_topic_ids(stage)
        if challenge_id in completed
    )
    return min(required_key_count(stage), earned)


def migrate_key_count(current_keys, stage, challenges_passed):
    """Keep legitimate saved keys while restoring rewards older saves missed."""

    maximum = required_key_count(stage)
    try:
        saved = max(0, int(current_keys or 0))
    except (TypeError, ValueError):
        saved = 0
    return min(maximum, max(saved, earned_topic_keys(stage, challenges_passed)))


def evaluate_stage_gate(stage, keys, challenges_passed):
    """Require both the full key total and every required lesson topic."""

    required_ids = required_topic_ids(stage)
    completed = set(challenges_passed or ())
    missing_ids = tuple(
        challenge_id for challenge_id in required_ids
        if challenge_id not in completed
    )
    missing_titles = tuple(
        CHALLENGES.get(challenge_id, {}).get("title", challenge_id)
        for challenge_id in missing_ids
    )
    required_keys = required_key_count(stage)
    try:
        current_keys = max(0, int(keys or 0))
    except (TypeError, ValueError):
        current_keys = 0

    return StageGateStatus(
        unlocked=current_keys >= required_keys and not missing_ids,
        keys=min(current_keys, required_keys),
        required_keys=required_keys,
        completed_topics=len(required_ids) - len(missing_ids),
        required_topics=len(required_ids),
        missing_topic_ids=missing_ids,
        missing_topic_titles=missing_titles,
    )
