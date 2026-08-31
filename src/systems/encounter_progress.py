"""Completion rules for authored overworld enemy groups."""


def newly_cleared_encounter_ids(enemies, authored_ids, already_cleared=()):
    """Return authored groups whose spawned members are all defeated."""

    authored = set(authored_ids or ())
    cleared = set(already_cleared or ())
    members = {encounter_id: [] for encounter_id in authored - cleared}
    for enemy in enemies:
        group_id = getattr(enemy, "group_id", "")
        if group_id in members:
            members[group_id].append(enemy)
    return tuple(
        encounter_id for encounter_id in authored_ids
        if encounter_id in members
        and members[encounter_id]
        and all(getattr(enemy, "state", "") == "defeated"
                for enemy in members[encounter_id])
    )
