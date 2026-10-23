"""Capture real Castle gameplay and a profile opened by clicking its HUD card.

Run from the repo root: python tools/check_character_hud.py --output-dir /tmp/character-hud
Uses in-memory fixtures and no save slot. Screenshots are actual Pygame frames.
"""
import argparse
import os
from pathlib import Path
import sys
from unittest.mock import patch

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['CODEBREAK_DEBUG'] = '0'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import pygame
from src.screens.game import game_screen
from src.systems.save_manager import new_game_state


class Captured(Exception):
    pass


def capture(screen, identity, destination, profile=False):
    state = new_game_state()
    state.update(stage='Castle', room_id='throne', character_id=identity,
                 hearts=4, keys=2, bonus_time=140)
    frames = 0
    captured = False
    def present():
        nonlocal frames, captured
        caller = sys._getframe(1)
        name = caller.f_code.co_name
        if name == 'finish':
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        if name == 'game_screen':
            frames += 1
            hud = caller.f_locals['gameplay_hud']
            assert hud.state['character_id'] == identity
            if frames == 3:
                if profile:
                    pygame.event.post(pygame.event.Event(
                        pygame.MOUSEBUTTONDOWN, button=1, pos=hud.profile_rect.center))
                else:
                    pygame.image.save(screen, str(destination))
                    captured = True
                    raise Captured()
        elif name == 'profile_screen' and profile:
            pygame.image.save(screen, str(destination))
            captured = True
            raise Captured()
        if frames > 10:
            raise AssertionError('Click did not open the profile')
    with patch.object(pygame.display, 'flip', present):
        try:
            game_screen(screen, save_state=state)
        except Captured:
            pass
    assert captured, 'Gameplay never rendered'
    print(destination, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('/tmp/character-hud'))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080))
    for identity in ('man', 'woman'):
        capture(screen, identity, args.output_dir / f'{identity}-gameplay.png')
        capture(screen, identity, args.output_dir / f'{identity}-profile.png', profile=True)
    pygame.quit()


if __name__ == '__main__':
    main()
