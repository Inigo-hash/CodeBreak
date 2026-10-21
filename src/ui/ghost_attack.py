"""White Lady attack light, driven by combat time rather than render FPS."""
import math

import pygame


def ghost_attack_pose(enemy, zoom, camera_x, camera_y):
    if not enemy.active or enemy.enemy_id != "white_lady" or enemy.state != "attack":
        return None
    progress = max(0.0, min(1.0, 1 - enemy.action_timer / enemy.stats.attack_duration))
    center = (round(enemy.rect.centerx * zoom - camera_x),
              round(enemy.rect.bottom * zoom - camera_y - 58))
    # A steady wind-up grows into a flash at the combat system's 52% hit time.
    strength = .25 + .75 * max(0.0, 1 - abs(progress - .52) / .52)
    direction = getattr(enemy, 'attack_direction', None)
    angle = (math.atan2(direction[1], direction[0]) if direction and any(direction)
             else {"east": 0, "south": math.pi / 2,
                   "west": math.pi, "north": -math.pi / 2}[enemy.facing])
    return center, progress, strength, angle, max(24, round(enemy.attack_range * zoom))


def draw_ghost_attack(surface, pose):
    if pose is None:
        return
    (x, y), progress, strength, angle, reach = pose
    radius = max(80, reach + 24)
    if not surface.get_rect().colliderect((x-radius, y-radius, radius*2, radius*2)):
        return
    glow = pygame.Surface((radius * 2 + 1, radius * 2 + 1))
    center = (radius, radius)
    for ring in range(12, 0, -1):
        size = round(radius * ring / 12)
        intensity = strength * (1 - ring / 13) ** 2
        pygame.draw.circle(glow, (round(28*intensity), round(78*intensity),
                                 round(100*intensity)), center, size)
    # Sweep in the committed attack direction; the light fades during recovery.
    sweep = angle - .9 + progress * 1.8
    points = [(round(radius + math.cos(sweep + offset) * reach),
               round(radius + math.sin(sweep + offset) * reach))
              for offset in (i * .06 - .48 for i in range(17))]
    color = tuple(round(channel * strength) for channel in (120, 220, 255))
    pygame.draw.lines(glow, color, False, points, 3)
    surface.blit(glow, (x-radius, y-radius), special_flags=pygame.BLEND_RGB_ADD)
