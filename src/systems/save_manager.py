import json
import os

SAVE_DIR = "saves"
NUM_SLOTS = 3


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
    return f"{stage}  |  Hearts: {hearts}  |  Keys: {keys}/5"


def new_game_state() -> dict:
    return {
        "stage": "Island",
        "hearts": 5,
        "keys": 0,
        "topics_completed": [],
        "challenges_passed": [],
        "map_position": None,
        "inventory": [],
    }