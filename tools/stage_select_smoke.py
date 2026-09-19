"""Render the atlas through the real presentation transform; no player saves."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import pygame
from src import display
from src.screens.stage_select import draw_stage_select
from src.systems.save_manager import new_game_state


def main():
    pygame.init()
    pygame.display.set_mode((1280, 720))
    output = ROOT / "docs/stage-selection-verification"
    output.mkdir(parents=True, exist_ok=True)
    for size in ((1280, 720), (1366, 768), (1920, 1080), (2560, 1440), (1280, 1024), (2560, 1080)):
        canvas = pygame.Surface(display.canvas_size_for_window(size))
        draw_stage_select(canvas, new_game_state(), time_seconds=.5)
        physical = pygame.Surface(size)
        with patch.object(display, "_window", physical), patch.object(display, "_canvas", canvas), patch.object(display, "_original_flip", lambda: None):
            display._present()
        pygame.image.save(physical, str(output / f"world-map-{size[0]}x{size[1]}.png"))
    for name, selected, state in (
        ("locked-citadel", 2, new_game_state()),
        ("completed-village", 0, dict(new_game_state(), stage="Castle", completed_stages=["island"])),
        ("available-depths", 1, dict(new_game_state(), completed_stages=["island"])),
    ):
        canvas = pygame.Surface((1280, 720))
        draw_stage_select(canvas, state, selected=selected, time_seconds=.5)
        pygame.image.save(canvas, str(output / f"{name}.png"))
    print(f"Rendered 9 atlas previews to {output}")
    pygame.quit()


if __name__ == "__main__":
    main()
