"""Headless gameplay/autosave smoke and reproducible resolution previews.

Run from the repository root: python tools/tagama_smoke.py
Uses temporary save slots; never opens or changes a player's saves.
"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["CODEBREAK_DEBUG"] = "0"

import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import pygame
from src.screens.game import game_screen
from src.screens.stage_info import open_stage_info
from src.data.stages import get_stage
from src.data.challenges import CHALLENGES
from src.systems import save_manager
from src.systems.stage_progress import StageProgress
from src.ui.code_editor import CodeEditor
from src import display

OUTPUT = ROOT / "docs" / "tagama-verification"
OUTPUT.mkdir(parents=True, exist_ok=True)


class CaptureComplete(Exception):
    pass


def previews(canvas, name):
    for size in ((1280, 720), (1366, 768), (1920, 1080), (2560, 1440), (1280, 1024), (2560, 1080)):
        physical = pygame.Surface(size)
        with patch.object(display, "_window", physical), patch.object(display, "_canvas", canvas), patch.object(display, "_original_flip", lambda: None):
            display._present()
        pygame.image.save(physical, str(OUTPUT / f"{name}-{size[0]}x{size[1]}.png"))


def run_game(canvas, state, seconds, label):
    samples = []
    started = None
    previous = None

    def present():
        nonlocal started, previous
        if sys._getframe(1).f_code.co_name == "finish":
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        if sys._getframe(1).f_code.co_name != "game_screen":
            return
        now = time.perf_counter()
        if started is None:
            started = now
            print(f"{label}: gameplay started", flush=True)
            live = sys._getframe(1).f_locals
            assert live["gameplay_state"]["keys"] == state["keys"]
            assert live["save_challenges_passed"] == state["challenges_passed"]
            if state.get("map_position"):
                assert [live["player_x"], live["player_y"]] == state["map_position"]
        if previous is not None:
            samples.append(now - previous)
        previous = now
        if now - started >= seconds:
            previews(canvas, label)
            raise CaptureComplete()

    with patch.object(pygame.display, "flip", present):
        try:
            game_screen(canvas, slot_num=1, save_state=state)
        except CaptureComplete:
            pass
    assert samples, "Gameplay never rendered"
    return {"frames": len(samples), "seconds": round(sum(samples), 2),
            "average_fps": round(len(samples) / sum(samples), 1),
            "worst_frame_ms": round(max(samples) * 1000, 1)}


def main():
    pygame.init()
    canvas = pygame.display.set_mode((1920, 1080))
    with tempfile.TemporaryDirectory() as folder, patch.object(save_manager, "SAVE_DIR", folder):
        result = {"fresh_game": run_game(canvas, save_manager.new_game_state(), 32, "gameplay")}
        assert save_manager.slot_exists(1), "Periodic autosave did not create a slot"
        saved = save_manager.load_slot(1)
        assert saved["map_position"] is not None
        assert saved["keys"] == 0 and saved["challenges_passed"] == []
        result["reload"] = run_game(canvas, saved, 2, "reloaded")
        result["autosave_restored"] = True

    background = canvas.copy()
    def capture_manual():
        previews(canvas, "stage-manual")
        raise CaptureComplete()
    with patch.object(pygame.display, "flip", capture_manual):
        try:
            open_stage_info(canvas, get_stage("island"), StageProgress(), background=background)
        except CaptureComplete:
            pass

    editor = CodeEditor(canvas, CHALLENGES["variables_001"], background)
    editor.text_buffer.lines = ["age = 18"]
    editor.renderer.draw()
    previews(canvas, "code-editor")
    (OUTPUT / "smoke-results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    pygame.quit()


if __name__ == "__main__":
    main()
