"""Nighttime lighting and fixed, code-drawn map torches."""

import heapq
import math

import pygame


# The stage begins at night; F1 may temporarily preview daylight.
WORLD_IS_NIGHT = True
NIGHT_COLOR = (8, 15, 40)
NIGHT_ALPHA = 228

# _light_mask's contour wobbles, so the drawn pool is both smaller and less
# round than the radius handed to the renderer. Measured against rendered
# frames: every direction is still visibly lit at 0.78 of the radius, while
# past 0.80 some directions have faded to full night. Gameplay uses 0.75 so
# an effect tied to "standing in the light" is never granted on ground the
# player can see is dark.
LIT_RADIUS_SCALE = 0.75

# The rendered pool sits slightly above the fixture itself.
LIGHT_CENTER_LIFT = 4

_NIGHT_VEIL_CACHE = {}
_LIGHT_MASK_CACHE = {}
_WARM_GLOW_CACHE = {}


def torch_screen_position(player_center, facing, elapsed_seconds):
    """Return the flame position beside the hand for the current facing."""

    left_facing = facing in ("left", "northwest", "southwest")
    side = -1 if left_facing else 1
    bob = round(math.sin(elapsed_seconds * 7.0) * 2)
    return player_center[0] + side * 28, player_center[1] - 12 + bob


def build_torch_overlay(size, flame_position, elapsed_seconds, radius=None):
    """Build a dark-blue night veil with a soft, flickering light opening."""

    width, height = size
    if radius is None:
        radius = max(145, min(300, round(height * 0.31)))

    # Two calm frequencies make the edge move organically without harsh,
    # distracting random flashes.
    flicker = (
        math.sin(elapsed_seconds * 7.3) * 4
        + math.sin(elapsed_seconds * 12.7) * 2
    )
    outer_radius = max(80, round(radius + flicker))

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((*NIGHT_COLOR, NIGHT_ALPHA))

    # Drawing from outside inward replaces the veil's alpha in concentric
    # circles. The middle stays bright while the edge fades into full night.
    rings = 22
    for index in range(rings):
        fraction = 1.0 - index / (rings - 1)
        ring_radius = max(1, round(outer_radius * fraction))
        alpha = round(18 + (NIGHT_ALPHA - 34) * (fraction ** 1.75))
        pygame.draw.circle(
            overlay,
            (*NIGHT_COLOR, alpha),
            (round(flame_position[0]), round(flame_position[1])),
            ring_radius,
        )

    return overlay


def draw_torch(surface, flame_position, facing, elapsed_seconds):
    """Draw a small held torch and warm flame above the nighttime veil."""

    x, y = map(round, flame_position)
    left_facing = facing in ("left", "northwest", "southwest")
    handle_slant = 5 if left_facing else -5

    glow = pygame.Surface((112, 112), pygame.SRCALPHA)
    glow_center = (56, 56)
    pygame.draw.circle(glow, (255, 126, 32, 18), glow_center, 48)
    pygame.draw.circle(glow, (255, 162, 46, 30), glow_center, 31)
    pygame.draw.circle(glow, (255, 205, 78, 48), glow_center, 18)
    surface.blit(glow, (x - 56, y - 56))

    # Wooden handle and metal collar.
    pygame.draw.line(surface, (48, 25, 14),
                     (x + handle_slant + 2, y + 8), (x + 2, y + 39), 7)
    pygame.draw.line(surface, (124, 72, 34),
                     (x + handle_slant, y + 8), (x, y + 38), 4)
    pygame.draw.rect(surface, (74, 77, 83), (x - 8, y + 4, 16, 7),
                     border_radius=2)
    pygame.draw.line(surface, (172, 137, 72),
                     (x - 6, y + 5), (x + 6, y + 5), 2)

    sway = round(math.sin(elapsed_seconds * 11.0) * 3)
    pygame.draw.polygon(surface, (238, 91, 25), [
        (x - 8, y + 5), (x - 5, y - 9), (x + sway, y - 21),
        (x + 8, y - 7), (x + 7, y + 5),
    ])
    pygame.draw.polygon(surface, (255, 190, 45), [
        (x - 4, y + 4), (x - 2, y - 7), (x + sway // 2, y - 14),
        (x + 4, y - 5), (x + 3, y + 4),
    ])
    pygame.draw.ellipse(surface, (255, 239, 151), (x - 2, y - 4, 5, 9))


def place_path_torches(path_cells, tile_size, placement_radius,
                       max_torches=None):
    """Place a restrained number of torches beside the paths.

    Candidate positions are the non-path cells directly beside a path, so a
    torch never stands in the player's walking lane. Positions are returned
    in unscaled world coordinates. ``placement_radius`` controls spacing and
    may be wider than the rendered light pool to preserve dark stretches.
    """

    path_centers = {
        cell: (cell[0] * tile_size + tile_size // 2,
               cell[1] * tile_size + tile_size // 2)
        for cell in path_cells
    }
    edge_cells = {
        (x + dx, y + dy)
        for x, y in path_cells
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0))
        if (x + dx, y + dy) not in path_cells
    }
    candidates = {
        cell: (cell[0] * tile_size + tile_size // 2,
               cell[1] * tile_size + tile_size // 2)
        for cell in edge_cells
    }
    uncovered = set(path_cells)
    torches = []
    radius_squared = placement_radius * placement_radius
    # Only tiles in the candidate's local grid neighborhood can possibly be
    # covered. The old candidate x every-path comparison performed millions
    # of needless distance checks and dominated stage startup time.
    cell_radius = math.ceil(placement_radius / tile_size)
    coverage_by_candidate = {}
    for cell, position in candidates.items():
        coverage = set()
        for dx in range(-cell_radius, cell_radius + 1):
            for dy in range(-cell_radius, cell_radius + 1):
                path_cell = (cell[0] + dx, cell[1] + dy)
                if path_cell not in path_cells:
                    continue
                path_position = path_centers[path_cell]
                if ((path_position[0] - position[0]) ** 2
                        + (path_position[1] - position[1]) ** 2
                        <= radius_squared):
                    coverage.add(path_cell)
        coverage_by_candidate[cell] = coverage

    coverage_heap = [
        (-len(coverage), cell[1], cell[0], cell)
        for cell, coverage in coverage_by_candidate.items()
    ]
    heapq.heapify(coverage_heap)

    while uncovered and (max_torches is None or len(torches) < max_torches):
        best_cell = None
        best_coverage = set()
        while coverage_heap:
            _estimated, _y, _x, cell = heapq.heappop(coverage_heap)
            if cell not in candidates:
                continue
            coverage = coverage_by_candidate[cell] & uncovered
            next_best_estimate = -coverage_heap[0][0] if coverage_heap else 0
            if len(coverage) < next_best_estimate:
                heapq.heappush(
                    coverage_heap,
                    (-len(coverage), cell[1], cell[0], cell),
                )
                continue
            best_cell, best_coverage = cell, coverage
            break

        # This can only happen when an authored path is wider than the light
        # diameter. Keep all torches on its edges and leave its deep interior
        # dark instead of putting a fixture in the walking lane.
        if best_cell is None or not best_coverage:
            break

        position = candidates.pop(best_cell)
        coverage_by_candidate.pop(best_cell)
        torches.append(position)
        uncovered.difference_update(best_coverage)

    return torches


def in_torch_light(point, torch_positions, radius, center_lift=0):
    """Whether ``point`` stands inside any fixed torch's visible pool.

    Units are the caller's: game.py works in unscaled world pixels and
    passes the light radius already divided by the camera zoom. The
    renderer's per-frame flicker is deliberately ignored - a boundary that
    breathed in and out would make the light's effect feel unreliable.
    """

    limit = (radius * LIT_RADIUS_SCALE) ** 2
    for torch_x, torch_y in torch_positions:
        offset_x = point[0] - torch_x
        offset_y = point[1] - (torch_y - center_lift)
        if offset_x * offset_x + offset_y * offset_y <= limit:
            return True
    return False


def _night_veil(size):
    veil = _NIGHT_VEIL_CACHE.get(size)
    if veil is None:
        veil = pygame.Surface(size, pygame.SRCALPHA)
        veil.fill((*NIGHT_COLOR, NIGHT_ALPHA))
        _NIGHT_VEIL_CACHE[size] = veil
    return veil


def _light_mask(radius, variant=0):
    """Return a cached, softly irregular mask used to restore lit world.

    A real flame does not make a geometrically perfect disc. Each variant
    uses a few gentle sine waves around its contour, producing organic pools
    of light without random frame-to-frame flashing.
    """

    cache_key = (radius, variant)
    mask = _LIGHT_MASK_CACHE.get(cache_key)
    if mask is not None:
        return mask

    diameter = radius * 2 + 2
    center = (radius + 1, radius + 1)
    mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    mask.fill((255, 255, 255, 0))
    rings = 64
    point_count = 72
    phase = variant * 1.37
    for index in range(rings):
        fraction = 1.0 - index / (rings - 1)
        # Even the center retains some blue night tint; a fixed torch should
        # make the path readable, not turn its surroundings into daylight.
        visibility = round(8 + 188 * ((1.0 - fraction) ** 0.82))
        points = []
        for point_index in range(point_count):
            angle = math.tau * point_index / point_count
            wobble = (
                0.84
                + 0.075 * math.sin(angle * 3 + phase)
                + 0.045 * math.sin(angle * 5 - phase * 0.7)
                + 0.025 * math.sin(angle * 9 + phase * 1.4)
            )
            ring_radius = radius * fraction * wobble
            # A slight vertical stretch and upward bias suits an upright
            # flame while keeping the edge soft and asymmetrical.
            x = center[0] + math.cos(angle) * ring_radius
            y = center[1] + math.sin(angle) * ring_radius * 1.06 - 3 * fraction
            points.append((round(x), round(y)))
        pygame.draw.polygon(mask, (255, 255, 255, visibility), points)
    _LIGHT_MASK_CACHE[cache_key] = mask
    return mask


def _warm_glow(radius, variant):
    """Subtle amber tint following the same irregular light contour."""

    cache_key = (radius, variant)
    glow = _WARM_GLOW_CACHE.get(cache_key)
    if glow is None:
        glow = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        glow.fill((255, 145, 48, 38))
        glow.blit(
            _light_mask(radius, variant), (0, 0),
            special_flags=pygame.BLEND_RGBA_MULT,
        )
        _WARM_GLOW_CACHE[cache_key] = glow
    return glow


def draw_night_and_torch(surface, player_center, facing, elapsed_seconds):
    """Apply the night veil, then draw the player's torch above it."""

    flame_position = torch_screen_position(
        player_center, facing, elapsed_seconds
    )
    radius = max(145, min(300, round(surface.get_height() * 0.31)))

    # Preserve only the part of the bright world that falls inside the torch
    # radius, darken the full screen using a cached veil, then composite that
    # local patch back through a cached radial mask. This avoids rebuilding a
    # full-HD/4K transparent surface 60 times per second.
    full_light_rect = pygame.Rect(
        round(flame_position[0]) - radius - 1,
        round(flame_position[1]) - radius - 1,
        radius * 2 + 2,
        radius * 2 + 2,
    )
    visible_rect = full_light_rect.clip(surface.get_rect())
    lit_world = pygame.Surface(visible_rect.size, pygame.SRCALPHA)
    if visible_rect.width and visible_rect.height:
        lit_world.blit(surface, (0, 0), visible_rect)

    surface.blit(_night_veil(surface.get_size()), (0, 0))

    if visible_rect.width and visible_rect.height:
        mask_source = pygame.Rect(
            visible_rect.x - full_light_rect.x,
            visible_rect.y - full_light_rect.y,
            visible_rect.width,
            visible_rect.height,
        )
        lit_world.blit(
            _light_mask(radius),
            (0, 0),
            mask_source,
            special_flags=pygame.BLEND_RGBA_MULT,
        )
        surface.blit(lit_world, visible_rect.topleft)

    draw_torch(surface, flame_position, facing, elapsed_seconds)


def draw_night_and_map_torches(surface, torch_positions, elapsed_seconds,
                               radius=None):
    """Darken the world and reveal it around fixed screen-space torches."""

    if radius is None:
        radius = 120

    bright_world = surface.copy()
    surface.blit(_night_veil(surface.get_size()), (0, 0))
    for torch_index, flame_position in enumerate(torch_positions):
        # Two low-amplitude frequencies produce smooth flame breathing. Each
        # fixture has a phase offset, avoiding synchronized pulsing without
        # introducing the harsh jumps of random per-frame values.
        flicker = (
            math.sin(elapsed_seconds * 6.7 + torch_index * 1.31) * 0.025
            + math.sin(elapsed_seconds * 11.3 + torch_index * 0.73) * 0.012
        )
        live_radius = max(24, round(radius * (1.0 + flicker)))
        light_x = flame_position[0] + math.sin(
            elapsed_seconds * 4.9 + torch_index
        ) * 1.5
        light_y = flame_position[1] - 4
        full_light_rect = pygame.Rect(
            round(light_x) - live_radius - 1,
            round(light_y) - live_radius - 1,
            live_radius * 2 + 2,
            live_radius * 2 + 2,
        )
        visible_rect = full_light_rect.clip(surface.get_rect())
        if not visible_rect.width or not visible_rect.height:
            continue

        lit_world = pygame.Surface(visible_rect.size, pygame.SRCALPHA)
        lit_world.blit(bright_world, (0, 0), visible_rect)
        mask_source = pygame.Rect(
            visible_rect.x - full_light_rect.x,
            visible_rect.y - full_light_rect.y,
            visible_rect.width,
            visible_rect.height,
        )
        lit_world.blit(
            _light_mask(live_radius, torch_index % 4),
            (0, 0), mask_source, special_flags=pygame.BLEND_RGBA_MULT
        )
        surface.blit(lit_world, visible_rect.topleft)
        surface.blit(
            _warm_glow(live_radius, torch_index % 4),
            visible_rect.topleft,
            mask_source,
        )

    # A small phase offset stops all flames swaying in perfect unison.
    for index, flame_position in enumerate(torch_positions):
        if surface.get_rect().inflate(80, 80).collidepoint(flame_position):
            draw_torch(
                surface, flame_position, "north",
                elapsed_seconds + index * 0.37,
            )
