"""Nighttime lighting and the player's code-drawn torch."""

import math

import pygame


# The stage begins at night; F1 may temporarily preview daylight.
WORLD_IS_NIGHT = True
NIGHT_COLOR = (8, 15, 40)
NIGHT_ALPHA = 218

_NIGHT_VEIL_CACHE = {}
_LIGHT_MASK_CACHE = {}


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


def _night_veil(size):
    veil = _NIGHT_VEIL_CACHE.get(size)
    if veil is None:
        veil = pygame.Surface(size, pygame.SRCALPHA)
        veil.fill((*NIGHT_COLOR, NIGHT_ALPHA))
        _NIGHT_VEIL_CACHE[size] = veil
    return veil


def _light_mask(radius):
    """Return a cached radial alpha mask used to restore the lit world."""

    mask = _LIGHT_MASK_CACHE.get(radius)
    if mask is not None:
        return mask

    diameter = radius * 2 + 2
    center = (radius + 1, radius + 1)
    mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    mask.fill((255, 255, 255, 0))
    rings = 48
    for index in range(rings):
        fraction = 1.0 - index / (rings - 1)
        ring_radius = max(1, round(radius * fraction))
        visibility = round(12 + 239 * ((1.0 - fraction) ** 0.72))
        pygame.draw.circle(
            mask, (255, 255, 255, visibility), center, ring_radius
        )
    _LIGHT_MASK_CACHE[radius] = mask
    return mask


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
