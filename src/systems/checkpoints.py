"""Safe player checkpoint placement beside authored healing statues."""

import pygame


def statue_checkpoint_position(statue_rect, player_size, map_width, map_height,
                               path_cells, tile_size, collision_rects):
    """Choose a collision-free player position on land beside the statue.

    The right-hand side is preferred so the player appears beside, rather
    than on top of, the statue. Only authored walkable path cells are valid.
    """
    if not path_cells:
        return None

    bounds = pygame.Rect(0, 0, map_width, map_height)
    target = (statue_rect.right + player_size[0] / 2 + 8,
              statue_rect.centery)
    candidates = []
    for cell_x, cell_y in path_cells:
        center = (cell_x * tile_size + tile_size // 2,
                  cell_y * tile_size + tile_size // 2)
        body = pygame.Rect(0, 0, *player_size)
        body.center = center
        if (not bounds.contains(body)
                or body.colliderect(statue_rect)
                or body.collidelist(collision_rects) != -1):
            continue
        samples = (body.center,
                   (body.left + 2, body.top + 2),
                   (body.right - 3, body.top + 2),
                   (body.left + 2, body.bottom - 3),
                   (body.right - 3, body.bottom - 3))
        if not all((x // tile_size, y // tile_size) in path_cells
                   for x, y in samples):
            continue
        right_side_penalty = 0 if body.centerx >= statue_rect.right else 1
        distance = abs(body.centerx - target[0]) + abs(body.centery - target[1])
        candidates.append(((right_side_penalty, distance), body.topleft))

    return min(candidates, key=lambda candidate: candidate[0])[1] if candidates else None
