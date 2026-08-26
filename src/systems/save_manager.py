import json
import os
import base64
import hashlib
import hmac
import secrets

SAVE_DIR = "saves"
NUM_SLOTS = 3
PASSWORD_MIN_LENGTH = 4
PASSWORD_ROUNDS = 180_000


def _ensure_save_dir() -> None:
    os.makedirs(SAVE_DIR, exist_ok=True)


def _slot_path(slot: int) -> str:
    return os.path.join(SAVE_DIR, f"slot_{slot}.json")


def slot_exists(slot: int) -> bool:
    return os.path.isfile(_slot_path(slot))


def load_slot(slot: int):
    if not slot_exists(slot):
        return None
    with open(_slot_path(slot), "r") as f:
        return json.load(f)


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
    return f"{stage}  |  Hearts: {hearts}  |  Keys: {keys}/5  |  {lock}"


def new_game_state() -> dict:
    return {
        "stage": "Island",
        "hearts": 5,
        "keys": 0,
        "topics_completed": [],
        "bonus_time": 0,
        "challenges_passed": [],
        "map_position": None,
        "inventory": [],
        "weapon_obtained": True,
        "weapon_equipped": True,
        # Discovered enemies/items and completed objectives for the stage
        # information panel. Filled in by StageProgress.to_dict() on save;
        # an empty dict here means "nothing discovered yet".
        "stage_progress": {},
    }
