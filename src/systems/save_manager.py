import json
import os
import base64
import hashlib
import hmac
import secrets

from src.data.stages import get_stage
from src.systems.boss_trigger import required_boss_id
from src.systems.stage_gate import required_key_count, required_topic_ids

SAVE_DIR = "saves"
NUM_SLOTS = 3
PASSWORD_MIN_LENGTH = 4
PASSWORD_ROUNDS = 180_000

TOPIC_ID_MIGRATIONS = {
    "operators": "operators_lesson",
    "string_basics": "strings_lesson",
}

CHALLENGE_ID_MIGRATIONS = {
    "operators_001": "operators_lesson_001",
    "string_basics_001": "strings_lesson_001",
}

def _ensure_save_dir() -> None:
    os.makedirs(SAVE_DIR, exist_ok=True)


def _slot_path(slot: int) -> str:
    return os.path.join(SAVE_DIR, f"slot_{slot}.json")


def slot_exists(slot: int) -> bool:
    return os.path.isfile(_slot_path(slot))

def _unique(values):
    """Remove duplicates while keeping the original order."""
    return list(dict.fromkeys(values))


def migrate_save_state(state: dict) -> dict:
    """Update old topic/challenge IDs to the current format."""

    # ---------------------------------------------------------
    # Topic IDs
    # ---------------------------------------------------------

    for field in (
        "topics_discovered",
        "topics_completed",
        "stored_topics",
        "inventory",
    ):
        values = state.get(field)

        if not isinstance(values, list):
            continue

        migrated = [
            TOPIC_ID_MIGRATIONS.get(value, value)
            for value in values
        ]

        # Either old Control Flow topic counts as having discovered/stored
        # the new combined topic.
        if field in ("topics_discovered", "stored_topics", "inventory"):
            if "conditionals" in values or "boolean_logic" in values:
                migrated.append("control_flow_lesson")

        # Completing BOTH old lessons means the combined lesson was completed.
        if field == "topics_completed":
            if (
                "conditionals" in values
                and "boolean_logic" in values
            ):
                migrated.append("control_flow_lesson")

        migrated = [
            value
            for value in migrated
            if value not in ("conditionals", "boolean_logic")
        ]

        state[field] = _unique(migrated)

    # ---------------------------------------------------------
    # Challenge IDs
    # ---------------------------------------------------------

    passed = state.get("challenges_passed", [])

    if isinstance(passed, list):

        migrated_passed = [
            CHALLENGE_ID_MIGRATIONS.get(value, value)
            for value in passed
        ]

        # The player must have completed both old challenges before
        # receiving credit for the new combined Control Flow challenge.
        if (
            "conditionals_001" in passed
            and "boolean_logic_001" in passed
        ):
            migrated_passed.append(
                "control_flow_lesson_001"
            )

        migrated_passed = [
            value
            for value in migrated_passed
            if value not in (
                "conditionals_001",
                "boolean_logic_001",
            )
        ]

        state["challenges_passed"] = _unique(
            migrated_passed
        )

    return state

def load_slot(slot: int):
    if not slot_exists(slot):
        return None

    with open(_slot_path(slot), "r") as f:
        state = json.load(f)

    return migrate_save_state(state)


def save_slot(slot: int, state: dict) -> None:
    _ensure_save_dir()
    with open(_slot_path(slot), "w") as f:
        json.dump(state, f, indent=2)


def is_protected(state: dict | None) -> bool:
    security = (state or {}).get("_security", {})
    return bool(security.get("salt") and security.get("password_hash"))


def protect_state(state: dict, password: str) -> dict:
    """Attach salted password verification data without storing plaintext."""

    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ROUNDS
    )
    state["_security"] = {
        "version": 1,
        "algorithm": "pbkdf2_sha256",
        "rounds": PASSWORD_ROUNDS,
        "salt": base64.b64encode(salt).decode("ascii"),
        "password_hash": base64.b64encode(digest).decode("ascii"),
    }
    return state


def verify_password(state: dict | None, password: str) -> bool:
    if not is_protected(state):
        return False
    security = state["_security"]
    try:
        salt = base64.b64decode(security["salt"])
        expected = base64.b64decode(security["password_hash"])
        rounds = int(security.get("rounds", PASSWORD_ROUNDS))
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, rounds
        )
    except (ValueError, TypeError, KeyError):
        return False
    return hmac.compare_digest(actual, expected)


def delete_slot(slot: int) -> None:
    path = _slot_path(slot)
    if os.path.isfile(path):
        os.remove(path)


def slot_summary(slot: int) -> str:
    data = load_slot(slot)
    if data is None:
        return "Empty"
    stage = data.get("stage", "Unknown")
    hearts = data.get("hearts", "?")
    keys = data.get("keys", 0)
    lock = "Protected" if is_protected(data) else "Needs password"
    required_keys = required_key_count(get_stage(stage))
    return f"{stage}  |  Hearts: {hearts}  |  Keys: {keys}/{required_keys}  |  {lock}"


def slot_progress(slot: int) -> int:
    """Return meaningful stage completion from lessons plus the boss."""
    data = load_slot(slot)
    if data is None:
        return 0
    stage = get_stage(data.get("stage", "Island"))
    stage_id = stage.get("id", "").lower()
    completed_stages = {
        str(value).lower() for value in data.get("completed_stages", ())
    }
    if stage_id and stage_id in completed_stages:
        return 100

    topic_ids = required_topic_ids(stage)
    passed = set(data.get("challenges_passed", ()))
    completed_topics = sum(topic_id in passed for topic_id in topic_ids)
    boss_id = required_boss_id(stage)
    defeated = set(
        data.get("stage_progress", {}).get("defeated_enemies", ())
    )
    completed_boss = int(not boss_id or boss_id in defeated)
    total_units = len(topic_ids) + int(bool(boss_id))
    if total_units == 0:
        return 0
    return round(100 * (completed_topics + completed_boss) / total_units)


def new_game_state() -> dict:
    return {
        "stage": "Island",
        "hearts": 5,
        "keys": 0,
        "topics_discovered": [],
        "topics_completed": [],
        "bonus_time": 0,
        "challenges_passed": [],
        "completed_stages": [],
        "map_position": None,
        "stored_topics": [],
        "weapon_obtained": True,
        "weapon_equipped": True,
        # Discovered enemies/items and completed objectives for the stage
        # information panel. Filled in by StageProgress.to_dict() on save;
        # an empty dict here means "nothing discovered yet".
        "stage_progress": {},
    }
