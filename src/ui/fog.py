"""Soft, seamless fog used by the F2 atmosphere preview."""

import random

import pygame


def build_fog_texture(width, height, seed=7):
    """Create a mirrored cloud texture that tiles without hard seams."""

    def build_layer(small_width, small_height, max_alpha, layer_seed):
        rng = random.Random(layer_seed)
        small = pygame.Surface((small_width, small_height), pygame.SRCALPHA)
        for y in range(small_height):
            for x in range(small_width):
                small.set_at(
                    (x, y),
                    (205, 215, 220, rng.randint(0, max_alpha)),
                )
        layer = pygame.transform.smoothscale(small, (width, height))
        return pygame.transform.smoothscale(
            pygame.transform.smoothscale(
                layer, (max(1, width // 2), max(1, height // 2))
            ),
            (width, height),
        )

    base = build_layer(28, 20, 26, seed)
    detail = build_layer(52, 36, 14, seed + 99)
    base.blit(detail, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    fog = pygame.Surface((width * 2, height * 2), pygame.SRCALPHA)
    fog.blit(base, (0, 0))
    fog.blit(pygame.transform.flip(base, True, False), (width, 0))
    fog.blit(pygame.transform.flip(base, False, True), (0, height))
    fog.blit(pygame.transform.flip(base, True, True), (width, height))
    return fog


def draw_fog(surface, fog_texture, camera_x, camera_y, drift_x, drift_y):
    """Tile the fog over the current viewport using world-relative motion."""

    fog_width, fog_height = fog_texture.get_size()
    offset_x = int(camera_x - drift_x)
    offset_y = int(camera_y - drift_y)
    start_x = -(offset_x % fog_width)
    start_y = -(offset_y % fog_height)

    for y in range(start_y - fog_height,
                   surface.get_height() + fog_height, fog_height):
        for x in range(start_x - fog_width,
                       surface.get_width() + fog_width, fog_width):
            surface.blit(fog_texture, (x, y))
