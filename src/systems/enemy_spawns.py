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
                encounter.get("require_path", True),
            )
            # A crowded authored group must never prevent the stage loading.
            # If every valid dirt position is already occupied, omit only
            # that excess member instead of putting it on grass or raising.
            if position is None:
                continue
            # Reserve the real combat body. Enemy-to-enemy collision keeps
            # the group separated after loading without wasting dirt space.
            occupied.append(pygame.Rect(0, 0, *body_size))
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
                      safe_area, path_cells, tile_size, spawn_area=None,
                      require_path=True):
    # Enemies belong on the authored dirt battlefield. Never fall back to
    # collision-free grass when a formation cannot use its first choice.
    max_radius = max(256, spawn_area.width, spawn_area.height) if spawn_area else 512
    for radius in range(0, max_radius + 1, 16):
        candidates = [(0, 0)] if radius == 0 else _ring(radius)
        for dx, dy in candidates:
            rect = pygame.Rect(0, 0, *body_size)
            rect.center = (desired[0] + dx, desired[1] + dy)
            if (bounds.contains(rect)
                    and (spawn_area is None or spawn_area.contains(rect))
                    and not safe_area.colliderect(rect)
                    and rect.collidelist(collision_rects) == -1
                    and rect.collidelist(occupied) == -1
                    and (not require_path
                         or body_is_on_path(rect, path_cells, tile_size))):
                return rect.center
    return None


def body_is_on_path(rect, path_cells, tile_size):
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
