"""
gear_icon.py

Draws the stone medallion and the spinning metal gear used for the
game's settings controls.

This lives on its own because two very different screens need the exact
same artwork: the main menu's settings row, and the small button in the
coding environment's title bar. Keeping one implementation means the
two can't slowly drift apart into "almost the same" gears.

Everything is drawn procedurally at whatever radius the caller asks
for, so the same wheel works as a 22px menu medallion or a 16px button.
The proportions below are expressed as fractions of the radius, chosen
so that a radius of 22 reproduces the main menu's original artwork
pixel for pixel.
"""

import math
import random

import pygame

# --------------------------------------------------
# Palette
# --------------------------------------------------
#
# Deliberately fixed rather than themed: this is the game's own stone
# and metal look, and it stays the same in every color theme.

STONE_DARK = (14, 14, 18)

STONE_MID = (24, 25, 31)

STONE_LIGHT = (38, 39, 47)

METAL_FRAME = (90, 94, 110)

YELLOW_GLOW = (255, 220, 120)

SILVER_LIGHT = (225, 228, 232)

SILVER_MID = (160, 165, 172)

SILVER_DARK = (95, 98, 105)

SILVER_SHINE = (250, 252, 255)

BRONZE_LIGHT = (218, 177, 86)

BRONZE_MID = (158, 105, 48)

BRONZE_DARK = (78, 50, 29)

WHITE = (255, 255, 255)


def draw_medallion(surf, center, radius, seed):
    """
    Draws the carved stone disc that every menu icon sits on.

    `seed` fixes the speckle pattern, so a given icon keeps the same
    stone texture from frame to frame instead of fizzing.
    """

    rng = random.Random(seed)
    cx, cy = center

    # Outer metal ring
    pygame.draw.circle(surf, METAL_FRAME, (cx, cy), radius + 4)
    pygame.draw.circle(surf, STONE_DARK, (cx, cy), radius + 4, 2)

    # Inner stone fill
    pygame.draw.circle(surf, STONE_MID, (cx, cy), radius)

    # Subtle stone texture speckles
    for _ in range(14):
        ang = rng.uniform(0, math.tau)
        dist = rng.uniform(0, max(1, radius - 3))
        x = cx + int(dist * math.cos(ang))
        y = cy + int(dist * math.sin(ang))
        c = rng.choice([STONE_DARK, STONE_LIGHT])
        pygame.draw.circle(surf, c, (x, y), rng.randint(1, 2))

    # Beveled highlight (top-left) and shadow (bottom-right)
    hi = tuple(min(255, c + 40) for c in STONE_LIGHT)
    lo = tuple(max(0, c - 25) for c in STONE_DARK)
    bbox = (cx - radius, cy - radius, radius * 2, radius * 2)
    pygame.draw.arc(surf, hi, bbox, math.radians(135), math.radians(225), 2)
    pygame.draw.arc(surf, lo, bbox, math.radians(-45), math.radians(45), 2)

    # Gold engraved ring accent
    pygame.draw.circle(surf, YELLOW_GLOW, (cx, cy), radius, 1)


def draw_gear(surf, center, radius, spin_degrees=0.0):
    """
    Draws the metal gear itself, rotated `spin_degrees` around its hub.

    `radius` is the medallion radius the gear should fit inside, not the
    gear's own size - the gear is sized to sit neatly on that disc.
    """

    ix, iy = center

    root_radius = max(4, round(radius * 0.50))
    tooth_radius = max(root_radius + 2, round(radius * 0.76))
    hub_outer = max(3, round(radius * 0.31))
    hole_radius = max(2, round(radius * 0.15))

    # Twelve blocky teeth give the settings icon a clear cog silhouette.
    teeth = []
    tooth_count = 12
    for tooth in range(tooth_count):
        center_angle = math.radians(spin_degrees + tooth * 360 / tooth_count)
        half_tooth = math.radians(5.5)
        half_gap = math.radians(11.5)
        for angle, distance in (
            (center_angle - half_gap, root_radius),
            (center_angle - half_tooth, tooth_radius),
            (center_angle + half_tooth, tooth_radius),
            (center_angle + half_gap, root_radius),
        ):
            teeth.append((ix + round(math.cos(angle) * distance),
                          iy + round(math.sin(angle) * distance)))
    pygame.draw.polygon(surf, BRONZE_DARK, teeth)
    pygame.draw.polygon(surf, BRONZE_MID, teeth, 2)
    pygame.draw.circle(surf, BRONZE_MID, (ix, iy), root_radius)
    pygame.draw.circle(surf, BRONZE_DARK, (ix, iy), root_radius, 2)

    # Six shaded spokes join the rim to a drilled center hub.
    for a in range(0, 360, 60):
        rad = math.radians(a + spin_degrees)
        x1 = ix + round(hub_outer * math.cos(rad))
        y1 = iy + round(hub_outer * math.sin(rad))
        x2 = ix + round(root_radius * math.cos(rad))
        y2 = iy + round(root_radius * math.sin(rad))
        pygame.draw.line(surf, BRONZE_LIGHT, (x1, y1), (x2, y2), 3)
        pygame.draw.line(surf, BRONZE_DARK, (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 1)

    pygame.draw.circle(surf, BRONZE_DARK, (ix, iy), hub_outer)
    pygame.draw.circle(surf, BRONZE_LIGHT, (ix, iy), hub_outer, 2)
    pygame.draw.circle(surf, STONE_DARK, (ix, iy), hole_radius)
    pygame.draw.circle(surf, BRONZE_DARK, (ix, iy), hole_radius, 1)
    # Fixed upper-left glint keeps the aged metal readable while rotating.
    glint_radius = max(3, root_radius - 2)
    bbox = (ix - glint_radius, iy - glint_radius,
            glint_radius * 2, glint_radius * 2)
    pygame.draw.arc(surf, SILVER_SHINE, bbox,
                    math.radians(125), math.radians(205), 1)


def draw_gear_medallion(surf, center, radius, spin_degrees=0.0, seed=None):
    """Medallion plus gear - the complete settings wheel."""

    if seed is None:
        seed = sum(map(ord, "gear"))

    draw_medallion(surf, center, radius, seed)
    draw_gear(surf, center, radius, spin_degrees)
