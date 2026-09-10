"""Headless real-loop checks of the PDF's boss-entry reproduction."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from src.screens import game
from src.systems import save_manager
from src.data.stages import get_stage
from src.systems.stage_gate import required_topic_ids

OUTPUT = Path(".uv-cache/september-verification")
OUTPUT.mkdir(parents=True, exist_ok=True)


class Done(Exception):
    pass


class Loading:
    def __init__(self, *args, **kwargs):
        pass

    def update(self, *args):
        pass

    def finish(self):
        pass


def scenario(screen, bypass):
    state = save_manager.new_game_state()
    state.update(map_position=[1504, 1000], map_layout_version=2)
    if not bypass:
        state["keys"] = 9
        state["challenges_passed"] = list(required_topic_ids(get_stage("island")))
    phase = "enter"
    frames = 0
    calls = []

    def intro(*args, **kwargs):
        nonlocal phase
        calls.append("intro")
        phase = "leave"
        return "fight"

    def retreat(*args, **kwargs):
        nonlocal phase
        calls.append("retreat")
        phase = "done"
        return "retreat"

    class Keys:
        def __getitem__(self, key):
            return key == (pygame.K_w if phase == "enter" else pygame.K_s)

    def present():
        nonlocal frames
        live = sys._getframe(1).f_locals
        if "player_rect" not in live:
            return
        frames += 1
        if frames == 1 and bypass:
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F3))
        if frames == 1:
            pygame.image.save(screen, str(OUTPUT / "gameplay.png"))
        if live["boss_enemy"] is not None:
            pygame.image.save(screen, str(OUTPUT / "boss-entry.png"))
        if phase == "done":
            assert live["boss_enemy"] is None
            assert calls == ["intro", "retreat"], calls
            raise Done()
        if frames > 240:
            raise AssertionError(f"Boss entry timed out: {live['player_rect']}, calls={calls}")

    pygame.event.clear()
    with patch.object(game, "StageLoadingScreen", Loading), \
         patch.object(game, "open_boss_intro", intro), \
         patch.object(game, "open_boss_retreat_warning", retreat), \
         patch.object(pygame.key, "get_pressed", lambda: Keys()), \
         patch.object(pygame.display, "flip", present):
        try:
            game.game_screen(screen, slot_num=1, save_state=state)
        except Done:
            pass
    return {"frames": frames, "dialogs": calls, "boss_removed_on_retreat": True}


def main():
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080))
    with tempfile.TemporaryDirectory() as folder, patch.object(save_manager, "SAVE_DIR", folder):
        results = {"normal_entry": scenario(screen, False), "F3_entry": scenario(screen, True)}
    (OUTPUT / "results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
