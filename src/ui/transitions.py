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

from src.systems.audio import play_crumble_sfx

CHIP_SIZE = 18


class _Chip:
    def __init__(self, image, x, y, vx, vy, rot=0.0, vrot=0.0,
                 delay=0.0):
        self.image = image
        self.x, self.y = x, y
        self.sx, self.sy = x, y  # start position (used by assemble phase)
        self.vx, self.vy = vx, vy
        self.alpha = 255.0
        self.rot = rot
        self.start_rot = rot
        self.vrot = vrot
        self.target = None
        self.delay = delay


def _tile_rects(rect, rng, tile=CHIP_SIZE):
    """Cut staggered, irregular masonry pieces instead of a square grid."""
    tiles = []
    y = rect.top
    while y < rect.bottom:
        h = min(rng.randint(tile - 5, tile + 5), rect.bottom - y)
        x = rect.left - (tile // 2 if ((y - rect.top) // tile) % 2 else 0)
        while x < rect.right:
            w = rng.randint(tile - 6, tile + 8)
            piece = pygame.Rect(x, y, w, h).clip(rect)
            if piece.width > 3 and piece.height > 3:
                tiles.append(piece)
            x += w
        y += h
    return tiles


def _spawn_burst_chips(rect, source_surface, rng):
    """Cut the real rendered button into tiles and blast them outward
    from the button's center."""
    chips = []
    cx, cy = rect.center
    for tile in _tile_rects(rect, rng):
        try:
            img = source_surface.subsurface(tile).copy()
        except ValueError:
            continue  # tile fell outside source_surface bounds

        tx, ty = tile.center
        dx, dy = tx - cx, ty - cy
        dist = max(1.0, math.hypot(dx, dy))
        nx, ny = dx / dist, dy / dist
        speed = rng.uniform(45, 125)
        vx = nx * speed + rng.uniform(-28, 28)
        vy = ny * speed - rng.uniform(10, 55)
        # Top-center fractures first, then the collapse travels down/out.
        delay = ((tile.centery - rect.top) / max(1, rect.height)) * 0.10
        delay += abs(tile.centerx - cx) / max(1, rect.width) * 0.045

        chips.append(_Chip(img, tx, ty, vx, vy,
                            rng.uniform(-5, 5), rng.uniform(-145, 145), delay))
    return chips


def _spawn_converge_chips(rect, source_surface, screen_w, screen_h, rng):
    """Form target buttons from nearby rubble instead of screen-edge confetti."""
    chips = []
    for tile in _tile_rects(rect, rng):
        try:
            img = source_surface.subsurface(tile).copy()
        except ValueError:
            continue

        angle = rng.uniform(0, math.tau)
        distance = rng.uniform(55, 190)
        sx = tile.centerx + math.cos(angle) * distance
        sy = tile.centery + math.sin(angle) * distance + rng.uniform(15, 65)

        delay = ((tile.centery - rect.top) / max(1, rect.height)) * 0.10
        c = _Chip(img, sx, sy, 0, 0, rng.uniform(-55, 55), 0, delay)
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


def _draw_dust(surf, dust, elapsed):
    layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    for x, y, radius, delay, life in dust:
        age = elapsed - delay
        if not 0 <= age <= life:
            continue
        progress = age / life
        alpha = round(75 * (1 - progress))
        drift_y = y - progress * 16
        pygame.draw.circle(layer, (151, 126, 91, alpha),
                           (round(x), round(drift_y)), radius)
    surf.blit(layer, (0, 0))


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
    play_crumble_sfx("break")
    clock = pygame.time.Clock()
    screen_w, screen_h = screen.get_size()

    # ---- Phase 1: burst outward ----
    chips = []
    dust = []
    for r in old_rects:
        chips.extend(_spawn_burst_chips(r, old_source, rng))
        for _ in range(max(5, r.width // 30)):
            dust.append((rng.randint(r.left, r.right),
                         rng.randint(r.top, r.bottom), rng.randint(1, 3),
                         rng.uniform(0.04, 0.18), rng.uniform(0.28, 0.48)))

    duration = max(0.48, burst_duration)
    elapsed, gravity = 0.0, 720.0
    while elapsed < duration:
        dt = clock.tick(60) / 1000.0
        elapsed += dt
        pygame.event.pump()

        for c in chips:
            if elapsed < c.delay:
                continue
            c.vy += gravity * dt
            c.x += c.vx * dt
            c.y += c.vy * dt
            c.rot += c.vrot * dt
            c.alpha -= 255 * (dt / max(0.1, duration - c.delay)) * 0.95

        screen.blit(backdrop, (0, 0))
        for c in chips:
            _draw_chip(screen, c)
        _draw_dust(screen, dust, elapsed)
        pygame.display.flip()

    # ---- Phase 2: assemble into new positions ----
    chips = []
    for r in new_rects:
        chips.extend(_spawn_converge_chips(r, new_source, screen_w, screen_h, rng))

    play_crumble_sfx("settle")
    duration, elapsed = max(0.52, assemble_duration), 0.0
    while elapsed < duration:
        dt = clock.tick(60) / 1000.0
        elapsed += dt
        pygame.event.pump()

        screen.blit(backdrop, (0, 0))
        for c in chips:
            progress = max(0.0, min(1.0,
                (elapsed - c.delay) / max(0.01, duration - c.delay)
            ))
            # Ease-out-back gives each stone a subtle weighty final settle.
            q = progress - 1
            ease = 1 + 2.70158 * q ** 3 + 1.70158 * q ** 2
            tx, ty = c.target
            c.x = c.sx + (tx - c.sx) * ease
            c.y = c.sy + (ty - c.sy) * ease
            c.rot = c.start_rot * (1 - progress)
            c.alpha = 255 * min(1.0, progress / 0.22)
            _draw_chip(screen, c)
        pygame.display.flip()

    # Finish on the fully rendered destination, avoiding a blank-menu flash.
    screen.blit(new_source, (0, 0))
    pygame.display.flip()
