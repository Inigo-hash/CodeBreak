"""Campaign stage access and independent map checkpoints."""
from copy import deepcopy

from src.data.stages import DEFAULT_STAGE_ID, STAGES, get_stage, stage_world
from src.systems.stage_handoff import STAGE_SCOPED_KEYS, stage_is_enterable


def stage_available(stage_id, state, developer_access=False):
    stage = STAGES.get(stage_id)
    if not stage_is_enterable(stage):
        return False
    completed = set(state.get("completed_stages", ()))
    return (developer_access or stage_id == DEFAULT_STAGE_ID
            or stage_id == get_stage(state.get("stage"))["id"]
            or stage_id in completed
            or any(item.get("next_stage") == stage_id and source in completed
                   for source, item in STAGES.items()))


def select_stage(state, stage_id, developer_access=False):
    """Switch maps without granting completion or losing the old checkpoint."""
    if not stage_available(stage_id, state, developer_access):
        raise ValueError("This stage is not unlocked.")
    result = deepcopy(state)
    current_id = get_stage(state.get("stage"))["id"]
    if current_id == stage_id:
        return result
    checkpoints = result.setdefault("stage_checkpoints", {})
    checkpoints[current_id] = {key: deepcopy(state.get(key)) for key in STAGE_SCOPED_KEYS}
    target = STAGES[stage_id]
    checkpoint = checkpoints.get(stage_id, {
        "keys": 0, "map_position": None, "stage_progress": {},
        "map_layout_version": stage_world(target)["map_layout_version"],
    })
    result.update(deepcopy(checkpoint))
    result["stage"] = target["name"]
    return result
