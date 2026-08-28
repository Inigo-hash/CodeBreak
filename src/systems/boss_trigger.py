"""Flag-driven boss-zone entry rules shared by gameplay and tests."""


def boss_zone_at(zone_records, point):
    """Return the zone marked ``is_boss_zone`` containing ``point``."""

    for zone in zone_records:
        if zone.get("is_boss_zone") and zone["rect"].collidepoint(point):
            return zone
    return None


def should_trigger_boss(previous_zone, current_zone, defeated=False,
                        boss_active=False):
    """Trigger once on entry, never by matching a hard-coded zone name."""

    entered = current_zone is not None and current_zone is not previous_zone
    return entered and not defeated and not boss_active


def required_boss_id(stage):
    """Return the boss that must be beaten before the stage exit opens."""

    return stage.get("completion", {}).get("required_boss")
