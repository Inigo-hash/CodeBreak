"""Campaign stage access and independent map checkpoints."""
from copy import deepcopy

from src.data.stages import DEFAULT_STAGE_ID, STAGES, get_stage, stage_world
from src.data.stage_map import stage_map_node
from src.systems.stage_handoff import STAGE_SCOPED_KEYS, stage_is_enterable


def stage_unlocked(stage_id, state, developer_access=False):
    """Read existing campaign completion, including legacy saves."""
    node = stage_map_node(stage_id)
    if node is None:
        return False
    completed = set(state.get("completed_stages", ()))
    return (developer_access or stage_id == DEFAULT_STAGE_ID
            or stage_id == get_stage(state.get("stage"))["id"]
            or stage_id in completed
            or node["unlock_after"] in completed)


def stage_available(stage_id, state, developer_access=False):
    return (stage_unlocked(stage_id, state, developer_access)
            and stage_is_enterable(STAGES.get(stage_id)))


def stage_status(stage_id, state, developer_access=False):
    if stage_id in state.get("completed_stages", ()):
        return "COMPLETED"
    if not stage_unlocked(stage_id, state, developer_access):
        return "LOCKED"
    if not stage_is_enterable(STAGES.get(stage_id)):
        return "COMING SOON"
    return "CURRENT" if stage_id == get_stage(state.get("stage"))["id"] else "AVAILABLE"


def select_stage(state, stage_id, developer_access=False):
    """Switch maps without granting completion or losing the old checkpoint."""
    if not stage_available(stage_id, state, developer_access):
        raise ValueError("This stage is not unlocked.")
    result = deepcopy(state)
    current_id = get_stage(state.get("stage"))["id"]
    if current_id == stage_id:
        return result
    checkpoints = result.setdefault("stage_checkpoints", {})
    checkpoints[current_id] = {key: deepcopy(state[key]) for key in STAGE_SCOPED_KEYS if key in state}
    target = STAGES[stage_id]
    checkpoint = {
        "keys": 0, "map_position": None, "stage_progress": {},
        "map_layout_version": stage_world(target)["map_layout_version"],
    }
    checkpoint.update(checkpoints.get(stage_id, {}))
    result.update(deepcopy(checkpoint))
    result["stage"] = target["name"]
    return result
