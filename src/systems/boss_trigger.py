"""Flag-driven boss-zone entry rules shared by gameplay and tests."""


def boss_zone_at(zone_records, point):
    """Return the zone marked ``is_boss_zone`` containing ``point``."""

    for zone in zone_records:
        if zone.get("is_boss_zone") and zone["rect"].collidepoint(point):
            return zone
    return None


def boss_main_entrance_rect(zone):
    """The centered south doorway, rather than the whole label zone."""
    if not zone or not zone.get("is_boss_zone"):
        return None
    rect = zone["rect"]
    corridor_width = max(96, round(rect.width * 0.28))
    corridor_depth = max(64, round(rect.height * 0.18))
    entrance = rect.copy()
    entrance.width = corridor_width
    entrance.height = corridor_depth * 2
    entrance.centerx = rect.centerx
    entrance.centery = rect.bottom
    return entrance


def boss_main_entrance_at(zone, point):
    entrance = boss_main_entrance_rect(zone)
    return entrance is not None and entrance.collidepoint(point)


class BossEntranceTrigger:
    """Show one warning per doorway approach, even after pushing back.

    Walk clear of the doorway before rearming. Crossing the rectangular
    zone's side edges or holding movement against a sealed gate cannot
    repeatedly reopen a dismissed modal.
    """

    def __init__(self):
        self.armed = True

    def update(self, zone, point):
        entrance = boss_main_entrance_rect(zone)
        if entrance is None:
            return False
        if not entrance.inflate(32, 32).collidepoint(point):
            self.armed = True
        if (self.armed and entrance.collidepoint(point)
                and zone["rect"].collidepoint(point)):
            self.armed = False
            return True
        return False


def should_trigger_boss(previous_zone, current_zone, defeated=False,
                        boss_active=False):
    """Trigger once on entry, never by matching a hard-coded zone name."""

    entered = current_zone is not None and current_zone is not previous_zone
    return entered and not defeated and not boss_active


def required_boss_id(stage):
    """Return the boss that must be beaten before the stage exit opens."""

    return stage.get("completion", {}).get("required_boss")
