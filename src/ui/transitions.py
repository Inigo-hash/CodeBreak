"""
transitions.py

Reusable stone/brick crumble transition effect for menu screens.
Cuts real rendered button pixels into tiles and animates those tiles
apart/together, so the debris matches the actual button texture
instead of generic flat-colored particles.
"""

import math
import random
import pygame

CHIP_SIZE = 16  # tile size in px. Smaller = finer dust (slower), larger = chunkier (faster).


class _Chip:
    def __init__(self, image, x, y, vx, vy, rot=0.0, vrot=0.0):
        self.image = image
        self.x, self.y = x, y
        self.sx, self.sy = x, y  # start position (used by assemble phase)
        self.vx, self.vy = vx, vy
        self.alpha = 255.0
        self.rot = rot
        self.vrot = vrot
        self.target = None


def _tile_rects(rect, tile=CHIP_SIZE):
    tiles = []
    y = rect.top
    while y < rect.bottom:
        x = rect.left
        h = min(tile, rect.bottom - y)
        while x < rect.right:
            w = min(tile, rect.right - x)
            tiles.append(pygame.Rect(x, y, w, h))
            x += tile
        y += tile
    return tiles


def _spawn_burst_chips(rect, source_surface, rng):
    """Cut the real rendered button into tiles and blast them outward
    from the button's center."""
    chips = []
    cx, cy = rect.center
    for tile in _tile_rects(rect):
        try:
            img = source_surface.subsurface(tile).copy()
        except ValueError:
            continue  # tile fell outside source_surface bounds

        tx, ty = tile.center
        dx, dy = tx - cx, ty - cy
        dist = max(1.0, math.hypot(dx, dy))
        nx, ny = dx / dist, dy / dist
        speed = rng.uniform(90, 240)
        vx = nx * speed + rng.uniform(-60, 60)
        vy = ny * speed - rng.uniform(20, 90)  # slight upward kick

        chips.append(_Chip(img, tx, ty, vx, vy,
                            rng.uniform(0, 360), rng.uniform(-220, 220)))
    return chips


def _spawn_converge_chips(rect, source_surface, screen_w, screen_h, rng):
    """Cut the pre-rendered TARGET button into tiles, start them off-screen,
    and fly them inward to reassemble at the real position."""
    chips = []
    for tile in _tile_rects(rect):
        try:
            img = source_surface.subsurface(tile).copy()
        except ValueError:
            continue

        edge = rng.choice(["top", "bottom", "left", "right"])
        if edge == "top":
            sx, sy = rng.randint(0, screen_w), -20
        elif edge == "bottom":
            sx, sy = rng.randint(0, screen_w), screen_h + 20
        elif edge == "left":
            sx, sy = -20, rng.randint(0, screen_h)
        else:
            sx, sy = screen_w + 20, rng.randint(0, screen_h)

        c = _Chip(img, sx, sy, 0, 0, rng.uniform(0, 360), rng.uniform(-160, 160))
        c.target = tile.center
        c.alpha = 0.0
        chips.append(c)
    return chips


def _draw_chip(surf, chip):
    if chip.alpha <= 0:
        return
    img = chip.image
    if chip.alpha < 255:
        img = img.copy()
        img.set_alpha(max(0, min(255, int(chip.alpha))))
    # Rotation looks good but costs a re-render per chip per frame. If this
    # is slow on lower-end hardware, drop the rotate() call and just blit
    # `img` directly at (chip.x, chip.y) centered — cheap fix if needed.
    rotated = pygame.transform.rotate(img, chip.rot)
    surf.blit(rotated, rotated.get_rect(center=(chip.x, chip.y)))


def crumble_transition(screen, backdrop, old_source, old_rects, new_source, new_rects,
                        seed=0, burst_duration=0.55, assemble_duration=0.5):
    """
    Two-phase brick-crumble transition, using real pixel tiles so the
    debris matches the actual button textures on both ends.

    backdrop    : clean background+logo, no buttons — shown behind the debris
    old_source  : surface with the CURRENT buttons already rendered on it
                  (e.g. screen.copy() taken right when the click happens)
    old_rects   : rects of the buttons crumbling away (within old_source)
    new_source  : surface with the NEXT screen's buttons pre-rendered
                  OFFSCREEN (never blitted to the visible screen)
    new_rects   : rects where the new buttons will assemble (within new_source)
    """
    rng = random.Random(seed)
    clock = pygame.time.Clock()
    screen_w, screen_h = screen.get_size()

    # ---- Phase 1: burst outward ----
    chips = []
    for r in old_rects:
        chips.extend(_spawn_burst_chips(r, old_source, rng))

    duration, elapsed, gravity = burst_duration, 0.0, 600.0
    while elapsed < duration:
        dt = clock.tick(60) / 1000.0
        elapsed += dt
        pygame.event.pump()

        for c in chips:
            c.vy += gravity * dt
            c.x += c.vx * dt
            c.y += c.vy * dt
            c.rot += c.vrot * dt
            c.alpha -= 255 * (dt / duration) * 1.1

        screen.blit(backdrop, (0, 0))
        for c in chips:
            _draw_chip(screen, c)
        pygame.display.flip()

    # ---- Phase 2: assemble into new positions ----
    chips = []
    for r in new_rects:
        chips.extend(_spawn_converge_chips(r, new_source, screen_w, screen_h, rng))

    duration, elapsed = assemble_duration, 0.0
    while elapsed < duration:
        dt = clock.tick(60) / 1000.0
        elapsed += dt
        pygame.event.pump()

        progress = min(1.0, elapsed / duration)
        ease = 1 - (1 - progress) ** 3

        screen.blit(backdrop, (0, 0))
        for c in chips:
            tx, ty = c.target
            c.x = c.sx + (tx - c.sx) * ease
            c.y = c.sy + (ty - c.sy) * ease
            c.rot += c.vrot * dt * 0.4
            c.alpha = 255 * min(1.0, progress / 0.3)  # quick fade-in only, stays solid after
            _draw_chip(screen, c)
        pygame.display.flip()

    screen.blit(backdrop, (0, 0))
    pygame.display.flip()