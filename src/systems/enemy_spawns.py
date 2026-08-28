"""Resolve authored encounter anchors onto collision-free map positions."""

import math

import pygame

from src.systems.combat import ENEMY_BODY_SIZES
from src.data.zones import get_zone_record_at


_GROUP_OFFSETS = (
    (-42, -22), (42, -22), (-48, 28),
    (48, 28), (0, -48), (0, 52),
)


def _group_offset(index):
    """Return a deterministic formation offset for any group size.

    The original authored six positions are preserved. Additional enemies
    occupy progressively wider eight-point rings instead of indexing past a
    fixed tuple when encounter counts are increased in ``encounters.py``.
    """

    if index < len(_GROUP_OFFSETS):
        return _GROUP_OFFSETS[index]

    extra_index = index - len(_GROUP_OFFSETS)
    ring = extra_index // 8
    point = extra_index % 8
    radius = 84 + ring * 42
    angle = math.tau * point / 8 - math.pi / 2
    return round(math.cos(angle) * radius), round(math.sin(angle) * radius)


def resolve_encounter_spawns(encounters, map_width, map_height,
                             collision_rects, path_cells, tile_size,
                             player_spawn):
    """Return enemy records on nearby walkable ground, spaced per group."""
    resolved = []
    occupied = []
    safe_area = pygame.Rect(0, 0, 300, 220)
    safe_area.midbottom = (player_spawn[0], map_height)
    bounds = pygame.Rect(16, 16, map_width - 32, map_height - 32)

    for encounter in encounters:
        anchor_x = round(encounter["anchor"][0] * map_width)
        anchor_y = round(encounter["anchor"][1] * map_height)
        zone_record, zone_rect = get_zone_record_at(
            anchor_x, anchor_y, map_width, map_height
        )
        spawn_area = pygame.Rect(zone_rect) if zone_rect else bounds.copy()
        spawn_margin = encounter.get("spawn_margin", 0)
        if spawn_margin:
            spawn_area.inflate_ip(-spawn_margin * 2, -spawn_margin * 2)
        for index, enemy_id in enumerate(encounter["enemies"]):
            offset = _group_offset(index)
            desired = (anchor_x + offset[0], anchor_y + offset[1])
            body_size = ENEMY_BODY_SIZES[enemy_id]
            position = _nearest_walkable(
                desired, body_size, bounds, collision_rects, occupied,
                safe_area, path_cells, tile_size, spawn_area,
            )
            # Keep bodies separate without reserving an oversized 36-pixel
            # moat around every enemy. Large user-authored groups otherwise
            # exhaust narrow path areas even when valid body space remains.
            occupied.append(pygame.Rect(
                0, 0, body_size[0] + 12, body_size[1] + 12
            ))
            occupied[-1].center = position
            resolved.append({
                "encounter_id": encounter["id"],
                "enemy_id": enemy_id,
                "position": position,
                "zone_size": encounter.get("zone_size", (360, 300)),
                "zone_name": zone_record["name"] if zone_record else "Wilderness",
                "zone_rect": zone_rect,
                "detection_range": encounter.get("detection_range"),
                "chase_range": encounter.get("chase_range"),
                "disengage_range": encounter.get("disengage_range"),
                "return_tolerance": encounter.get("return_tolerance"),
            })
    return resolved


def _nearest_walkable(desired, body_size, bounds, collision_rects, occupied,
                      safe_area, path_cells, tile_size, spawn_area=None):
    # Prefer dirt paths. If a user-authored group is too large for the path
    # space in its zone, retry on any collision-free terrain in that same
    # zone rather than crashing or placing the enemy outside its territory.
    for require_path in (True, False):
        for radius in range(0, 257, 16):
            candidates = [(0, 0)] if radius == 0 else _ring(radius)
            for dx, dy in candidates:
                rect = pygame.Rect(0, 0, *body_size)
                rect.center = (desired[0] + dx, desired[1] + dy)
                if (bounds.contains(rect)
                        and (spawn_area is None or spawn_area.contains(rect))
                        and not safe_area.colliderect(rect)
                        and rect.collidelist(collision_rects) == -1
                        and rect.collidelist(occupied) == -1
                        and (not require_path or _body_is_on_path(
                            rect, path_cells, tile_size
                        ))):
                    return rect.center
    raise RuntimeError(f"No walkable enemy spawn near {desired}")


def _body_is_on_path(rect, path_cells, tile_size):
    """Require the body center and inset corners to stand on dirt tiles."""
    points = (
        rect.center,
        (rect.left + 2, rect.top + 2),
        (rect.right - 3, rect.top + 2),
        (rect.left + 2, rect.bottom - 3),
        (rect.right - 3, rect.bottom - 3),
    )
    return all((x // tile_size, y // tile_size) in path_cells for x, y in points)


def _ring(radius):
    points = []
    for value in range(-radius, radius + 1, 8):
        points.extend(((value, -radius), (value, radius),
                       (-radius, value), (radius, value)))
    # Preserve deterministic placement while dropping corner duplicates.
    return tuple(dict.fromkeys(points))
