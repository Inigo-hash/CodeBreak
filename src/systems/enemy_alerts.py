"""Nearby camp members react when the player lands a hit on an ally."""
import math
from src.systems.combat import attack_path_blocked


def alert_camp(victim, enemies, terrain):
    if not victim.group_id or victim.group_id == 'ungrouped':
        return
    for ally in enemies:
        if (ally is victim or ally.group_id != victim.group_id
                or not ally.active or ally.state != 'idle'):
            continue
        if math.dist(ally.rect.center, victim.rect.center) > ally.assist_range:
            continue
        if attack_path_blocked(ally.rect, victim.rect, terrain):
            continue
        # Preserve the normal reaction delay, then use collision-aware pursuit.
        ally.state = 'alert'
        ally.action_timer = .18
