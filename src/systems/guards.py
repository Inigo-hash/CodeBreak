"""Props that a camp of enemies is standing over, and whether it still is.

A searchable prop with enemies camped around it belongs to them: the player
has to clear the camp before the prop will open.

Membership is decided once, when the stage loads, from where each enemy
*lives* - its spawn - rather than where it currently stands. Two
consequences, both deliberate:

- Luring a camp away from its loot is not a way around the fight. The
  guards follow the player, but the prop stays locked until they are dead.
- What the player sees is what they have to fight. The enemies standing
  around a barrel are exactly the ones holding it shut, rather than every
  enemy sharing its region of the map.

``Enemy.zone`` is deliberately not used here: for an encounter anchored
inside a named region it is that whole region (zones.py), which would lock
a prop behind enemies the player cannot even see from it.
"""

# World pixels. A camp's formation offsets reach about 130px from its
# anchor, so this covers a whole camp standing around a prop without
# reaching into the next one.
GUARD_RADIUS = 140


def assign_guards(interactables, enemies, radius=GUARD_RADIUS):
    """Record the enemies camped around each prop. Returns the same list."""

    limit = radius * radius
    for item in interactables:
        action = str(item.get("actions") or item.get("action") or "")
        if action and not action.startswith("search_"):
            # Readable scenery such as the trail sign is information, not
            # loot. Nearby enemies must not silently turn it into a locked
            # container.
            item["guards"] = []
            continue
        center = item["rect"].center
        item["guards"] = [
            enemy for enemy in enemies
            if _distance_squared(center, getattr(enemy, "spawn", None)) <= limit
        ]
    return interactables


def _distance_squared(point, spawn):
    """Squared distance to an enemy's home, or infinity if it has none."""

    if spawn is None:
        return float("inf")
    return (point[0] - spawn[0]) ** 2 + (point[1] - spawn[1]) ** 2


def remaining_guards(item):
    """The prop's guards that are still standing.

    An enemy counts as cleared once it is actually defeated, so a guard
    playing its death animation no longer holds the prop shut, while one
    that merely wandered off still does.
    """

    return [
        enemy for enemy in item.get("guards", ())
        if getattr(enemy, "state", "") != "defeated"
    ]


def is_guarded(item):
    """Whether this prop still has a living guard."""

    return bool(remaining_guards(item))
