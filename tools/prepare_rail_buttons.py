"""
prepare_rail_buttons.py

One-time asset step: turn the 2x2 reference sheet of stage-rail buttons into
four trimmed PNGs with transparent backgrounds, which src/ui/stage_panel.py
loads at runtime.

    python tools/prepare_rail_buttons.py

Reads   assets/images/ui/stage_rail_buttons.png
Writes  assets/images/ui/rail_manual.png
        assets/images/ui/rail_enemies.png
        assets/images/ui/rail_items.png
        assets/images/ui/rail_objectives.png

Doing this ahead of time rather than at launch keeps numpy out of the game's
runtime dependencies and means the repo carries clean, ready-to-blit art.
Re-run it if the sheet is ever redrawn.
"""

import os
import sys

import numpy as np
import pygame

SOURCE = "assets/images/ui/stage_rail_buttons.png"
OUT_DIR = "assets/images/ui"

# Sheet reading order: top-left, top-right, bottom-left, bottom-right.
TABS = ["manual", "enemies", "items", "objectives"]

# A pixel this bright and this grey is background, not art. The sheet's
# white is anti-aliased at the edges, so a plain colour-key would leave a
# pale halo around every plaque.
WHITE_LEVEL = 236
CHROMA_TOLERANCE = 12


def knock_out_white(surface):
    """Return a copy with the white page turned transparent."""
    rgb = pygame.surfarray.pixels3d(surface).astype(np.int16)
    alpha = pygame.surfarray.pixels_alpha(surface)

    brightness = rgb.min(axis=2)
    chroma = rgb.max(axis=2) - rgb.min(axis=2)
    background = (brightness >= WHITE_LEVEL) & (chroma <= CHROMA_TOLERANCE)

    # Feather the boundary: pixels that are nearly background fade out rather
    # than leaving a hard, slightly-white fringe against the game world.
    near = (brightness >= WHITE_LEVEL - 24) & (chroma <= CHROMA_TOLERANCE) & ~background
    alpha[background] = 0
    alpha[near] = np.clip((WHITE_LEVEL - brightness[near]) * 10, 0, 255).astype(alpha.dtype)

    del rgb, alpha
    return surface


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))

    if not os.path.exists(SOURCE):
        sys.exit(
            f"Missing {SOURCE}\n"
            "Save the 2x2 button reference sheet there first, then re-run."
        )

    sheet = pygame.image.load(SOURCE).convert_alpha()
    half_w = sheet.get_width() // 2
    half_h = sheet.get_height() // 2

    for index, tab in enumerate(TABS):
        column, row = index % 2, index // 2
        cell = sheet.subsurface(
            (column * half_w, row * half_h, half_w, half_h)
        ).copy()

        knock_out_white(cell)

        # Trim the empty margin so every button's rect is its own artwork and
        # the four end up consistently sized relative to each other.
        bounds = cell.get_bounding_rect(min_alpha=8)
        if bounds.width and bounds.height:
            cell = cell.subsurface(bounds).copy()

        out = f"{OUT_DIR}/rail_{tab}.png"
        pygame.image.save(cell, out)
        print(f"{out}  {cell.get_width()}x{cell.get_height()}")


if __name__ == "__main__":
    main()
