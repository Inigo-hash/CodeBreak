"""Capture actual Stage 3 gameplay frames with disposable in-memory fixtures.

Run from the repository root. No save slots, credentials or network are used.
These preview entry, an active boss reload, and the restored exit; the automated
campaign tests separately validate challenge submissions and completion writes.
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
sys.path.insert(0,str(ROOT))
os.chdir(ROOT)
import pygame
from src.screens.game import game_screen
from src.data.citadel import CITADEL_TOPICS, CITADEL_FINAL_ID
from src.data.stages import get_stage
from src.systems.save_manager import new_game_state
from src.systems.topic_mastery import complete_topic_challenge


class Captured(Exception):
    pass


def capture(screen,state,path):
    frames=0
    def present():
        nonlocal frames
        caller=sys._getframe(1)
        while caller and caller.f_code is not game_screen.__code__:
            caller=caller.f_back
        if caller and 'dt' in caller.f_locals:
            frames+=1
            if frames==3:
                assert caller.f_locals['stage']['id']=='citadel'
                pygame.image.save(screen,str(path))
                raise Captured
    with patch.object(pygame.display,'flip',side_effect=present),patch('src.screens.game.StageLoadingScreen.finish'):
        try:
            game_screen(screen,save_state=state)
        except Captured:
            pass
    assert path.is_file(), 'Gameplay never rendered'
    print(path,flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=Path('/tmp/citadel-preview'))
    args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    pygame.init();screen=pygame.display.set_mode((1920,1080))
    state=new_game_state()
    state.update(stage='Citadel',completed_stages=['island','castle'],weapon_obtained=True,weapon_equipped=True)
    capture(screen,state,args.output_dir/'entry.png')
    for topic in CITADEL_TOPICS.values():
        for cid in topic['challenge_ids']:
            state=complete_topic_challenge(state,get_stage('citadel'),topic['id'],cid)
    state.update(active_boss='citadel_flame_warden',map_position=[304,352])
    capture(screen,state,args.output_dir/'boss.png')
    state.update(active_boss=None,map_position=[304,208],stage_progress={'defeated_enemies':['citadel_flame_warden']})
    state['challenges_passed'].append(CITADEL_FINAL_ID)
    capture(screen,state,args.output_dir/'restored-exit.png')
    pygame.quit()


if __name__=='__main__':
    main()
