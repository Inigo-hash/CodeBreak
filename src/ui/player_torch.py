"""A held visual torch attached to the current player frame.

Its light is visual only: stationary map torches still control healing.
The selected inventory torch supplies this visual; no new sprite assets are required.
"""
import math
import pygame
from src.ui.night_lighting import draw_torch

LEFT_FACINGS = frozenset(('left', 'northwest', 'southwest'))


def held_torch_pose(bounds, facing, elapsed_seconds, combat_state='idle'):
    """Return (flame center, draw scale), or None for a fallen/unrendered player."""
    if bounds is None or bounds.height <= 0 or combat_state == 'defeated':
        return None
    scale = max(0.35, min(0.9, bounds.height / 155.0))
    side = 0.22 if facing in LEFT_FACINGS else 0.78
    hand_x = bounds.left + bounds.width * side
    hand_y = bounds.top + bounds.height * 0.58
    # The existing torch's handle ends 38 px below its flame center.
    flame = (round(hand_x), round(hand_y - 38 * scale
                                 + math.sin(elapsed_seconds * 7) * scale))
    return flame, scale


def draw_held_torch(surface, pose, facing, elapsed_seconds):
    """Scale the existing drawn flame and handle to match the player's sprite."""
    if pose is None:
        return
    flame, scale = pose
    patch = pygame.Surface((112, 112), pygame.SRCALPHA)
    draw_torch(patch, (56, 56), facing, elapsed_seconds)
    size = max(1, round(112 * scale))
    patch = pygame.transform.scale(patch, (size, size))
    surface.blit(patch, (flame[0] - size // 2, flame[1] - size // 2))
