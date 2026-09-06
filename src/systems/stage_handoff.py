"""Carrying one run from a finished stage into the next one.

Clearing a stage used to end the run: the exit gate saved and dropped the
player back at the main menu, because the Island was the only stage with
a map. Where a stage leads next is authored in stages.py (`next_stage`)
rather than coded here, so adding stage 3 stays a data change.

This module answers the two questions game.py asks at the exit gate:

    next_stage(stage)          where does this stage lead, if anywhere?
    stage_is_enterable(stage)  is there actually a map to walk into?

and then rewrites the save for the stage being entered. Pure logic, like
stage_gate.py - no pygame, so the tests exercise the real rules.
"""

from src.data.stages import get_stage, stage_world


# A new stage begins on a full heart row, the same way a new game does.
# Mirrors save_manager.new_game_state() and ui.gameplay_hud.MAX_HEARTS;
# tests/test_stage_handoff.py fails if those three drift apart.
FULL_HEARTS = 5

# Save keys that describe the stage just left rather than the player, and
# so must not follow them through the gate. Keys are re-earned from the
# new stage's lessons, the map position belongs to a map that is no longer
# loaded, and stage_progress is reset by advance_save_state below.
STAGE_SCOPED_KEYS = ("keys", "map_position", "map_layout_version",
                     "stage_progress")


def next_stage_id(stage):
    """Return the id of the stage this one leads to, or None if it ends."""

    target = (stage or {}).get("next_stage")
    return str(target).strip().lower() if target else None


def next_stage(stage):
    """Return the next stage's record, or None when the run ends here.

    get_stage() falls back to the Island for an id it does not know, which
    is right for a save naming a deleted stage and wrong here - a typo in
    `next_stage` would quietly send a finished player back to stage 1.
    The record handed back is checked against the id that was asked for.
    """

    target_id = next_stage_id(stage)
    if not target_id:
        return None

    candidate = get_stage(target_id)
    return candidate if candidate.get("id") == target_id else None


def stage_is_enterable(stage):
    """Whether a stage has an authored map for game.py to load.

    The same condition game_screen() uses to refuse a content-only stage,
    kept here so the exit gate can decide *before* the transition whether
    there is anywhere to go.
    """

    return bool(stage) and bool(stage_world(stage)["map"])


def has_playable_next_stage(stage):
    """Whether clearing this stage should hand off instead of ending the run."""

    return stage_is_enterable(next_stage(stage))


def advance_save_state(save_state, from_stage, to_stage):
    """Return the save a run carries out of `from_stage` and into `to_stage`.

    What the player keeps is what they learned and what they finished:
    lessons passed, topics discovered, stored notes, bonus time, their
    weapon, and the list of stages cleared - which `from_stage` is added
    to here, so the handoff and the return-to-menu path record completion
    the same way.

    What belonged to the stage just left is dropped. Its keys are gone
    because the next stage's exit wants its own; the map position points
    into a map that is no longer loaded; and StageProgress is reset rather
    than merged because its ids are only unique within one stage - Tiled
    object ids and encounter ids restart on a new map, and an objective
    like "search a barrel" would count itself done on arrival off an
    Island discovery.

    Hearts are refilled: a stage exit sits on the far side of a boss
    fight, and starting stage 2 on one heart is a punishment for winning.
    """

    state = dict(save_state or {})

    cleared = [str(stage_id) for stage_id in state.get("completed_stages", ())]
    finished_id = (from_stage or {}).get("id")
    if finished_id and finished_id not in cleared:
        cleared.append(finished_id)

    state.update({
        # Saves have always stored the display name ("Island"), and
        # get_stage() resolves either that or the id.
        "stage": to_stage.get("name", to_stage.get("id", "")),
        "hearts": FULL_HEARTS,
        "keys": 0,
        "map_position": None,
        "map_layout_version": stage_world(to_stage)["map_layout_version"],
        "stage_progress": {},
        "completed_stages": cleared,
    })

    return state
