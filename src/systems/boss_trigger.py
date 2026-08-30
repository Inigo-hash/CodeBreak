"""Flag-driven boss-zone entry rules shared by gameplay and tests."""


def boss_zone_at(zone_records, point):
    """Return the zone marked ``is_boss_zone`` containing ``point``."""

    for zone in zone_records:
        if zone.get("is_boss_zone") and zone["rect"].collidepoint(point):
            return zone
    return None


def boss_main_entrance_at(zone, point):
    """Return whether a point is in the Core's centered south doorway.

    The named zone is rectangular for map labeling, but its visible walls
    are irregular. Restricting retreat confirmation to this narrow corridor
    prevents invisible side edges from behaving like exits.
    """
    if not zone or not zone.get("is_boss_zone"):
        return False
    rect = zone["rect"]
    corridor_width = max(96, round(rect.width * 0.28))
    corridor_depth = max(64, round(rect.height * 0.18))
    entrance = rect.copy()
    entrance.width = corridor_width
    entrance.height = corridor_depth * 2
    entrance.centerx = rect.centerx
    entrance.centery = rect.bottom
    return entrance.collidepoint(point)


def should_trigger_boss(previous_zone, current_zone, defeated=False,
                        boss_active=False):
    """Trigger once on entry, never by matching a hard-coded zone name."""

    entered = current_zone is not None and current_zone is not previous_zone
    return entered and not defeated and not boss_active


def required_boss_id(stage):
    """Return the boss that must be beaten before the stage exit opens."""

    return stage.get("completion", {}).get("required_boss")
