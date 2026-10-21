"""Render actual UI states without touching player saves or making tutor calls.

Run from the repository root with dummy SDL. Captures are temporary by default.
The font-size option exercises the real accessibility scale, not enlarged images.
"""
import argparse
from collections import defaultdict
from contextlib import ExitStack
import inspect
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import pygame


class Captured(Exception):
    pass


def run(output, size, font_size, selected=None):
    pygame.init()
    pygame.display.set_mode(size)
    from src.settings_state import settings_state
    settings_state.update(font_size=font_size, walkthrough_seen=True,text_speed='INSTANT')
    from src.ui.theme import clear_font_cache
    clear_font_cache()
    from src.screens import main_menu, game
    from src.screens.start_game_menu import start_game_menu, start_menu_layout, slot_layout
    from src.screens.intro import opening_walkthrough
    from src.screens.how_to_play import how_to_play_screen
    from src.screens.settings import SettingsPanel
    from src.screens.profile import profile_screen
    from src.screens.character_select import open_character_select
    from src.screens.stage_select import draw_stage_select
    from src.screens.world_map import open_world_map
    from src.screens.stage_info import open_stage_info
    from src.screens.learning_progress import draw_learning_progress
    from src.screens.topic_found import TopicFoundScreen
    from src.screens.topic_lesson import TopicLessonScreen
    from src.screens.topic_requirements import open_topic_requirements
    from src.screens.topic_challenges import open_topic_challenges
    from src.screens.code_practice_menu import open_code_practice_menu
    from src.screens.practice_topics import open_practice_topics
    from src.screens.mang_tahimik import MangTahimikChat
    from src.screens.trap_alert import open_trap_alert
    from src.screens.final_challenge_warning import open_final_challenge_warning
    from src.screens.boss_encounter import open_boss_intro, open_boss_result, open_boss_retreat_warning
    from src.screens.assessment_briefing import assessment_dialog
    from src.screens.unsaved_exit import confirm_unsaved_exit
    from src.screens.game_over import game_over_screen
    from src.screens.inventory import InventoryScreen, PlayerInventory
    from src.screens.tutorial import tutorial_screen
    from src.ui.code_editor import CodeEditor
    from src.screens.loading import StageLoadingScreen
    from src.data.topics import TOPICS
    from src.data.challenges import CHALLENGES
    from src.data.stages import get_stage
    from src.systems.stage_progress import StageProgress
    from src.systems.stage_gate import evaluate_stage_gate
    from src.screens.stage_gate import open_stage_gate
    from src.systems import save_manager

    screen = pygame.Surface(size).convert()
    main_menu.screen = screen
    main_menu.SCREEN_WIDTH, main_menu.SCREEN_HEIGHT = size
    main_menu.background = pygame.transform.smoothscale(main_menu.background, size)
    main_menu._menu_logo_cache = None
    main_menu._menu_ambient = None
    main_menu._menu_pulse_cache = None
    background = screen.copy()
    state = save_manager.new_game_state()
    state.update(stage='Castle', room_id='library', bonus_time=12345)
    progress = StageProgress()
    for enemy in get_stage('castle')['enemies']:
        progress.discover_enemy(enemy)
    inventory = PlayerInventory()
    inventory.set_weapon_state(True, False)
    for tid, topic in TOPICS.items():
        inventory.add_topic(tid, topic['title'])
    cases = []

    def add(name, callback, loop=False, events=None, frame=None):
        cases.append((name, callback, loop, events, frame))

    add('main-menu', main_menu.main_menu, True)
    add('start-menu', lambda: start_game_menu(screen), True)
    menu_rects = start_menu_layout(*size)
    panel = pygame.Rect(0,0,min(720,size[0]-60),min(620,size[1]-50))
    panel.center = screen.get_rect().center
    slots, _ = slot_layout(panel,3)
    click = lambda rect: pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=rect.center)
    add('save-slots', lambda: start_game_menu(screen), True, [click(menu_rects[1])])
    add('password', lambda: start_game_menu(screen), True, [click(menu_rects[1]),click(slots[0])])
    add('intro', lambda: opening_walkthrough(screen, replay=True), True)
    add('intro-menu', lambda: opening_walkthrough(screen, replay=True), True,
        [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE)])
    add('intro-help', lambda: opening_walkthrough(screen, replay=True), True,
        [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE)]*2)
    add('how-to-play', lambda: how_to_play_screen(screen), True)
    def settings(help_topic=None):
        obj = SettingsPanel(screen)
        obj.open()
        obj.help_topic = help_topic
        obj.draw()
    add('settings', settings)
    add('settings-help', lambda: settings('font_size'))
    add('profile', lambda: profile_screen(screen), True)
    add('character-select', lambda: open_character_select(screen), True)
    add('atlas', lambda: draw_stage_select(screen,state,selected=1))
    for tab in ('manual','enemies','items','objectives'):
        add('stage-'+tab, lambda tab=tab: open_stage_info(screen,get_stage('castle'),progress,tab=tab), True)
    add('progress', lambda: draw_learning_progress(screen,get_stage('castle'),state))
    add('topic-guidance', lambda: draw_learning_progress(screen,get_stage('castle'),state,True))
    add('topic-found', lambda: TopicFoundScreen(screen,'castle_dictionaries').draw((-1,-1)))
    add('lesson', lambda: TopicLessonScreen(screen,TOPICS['castle_exceptions']).draw((-1,-1)))
    def lesson_confirm():
        obj = TopicLessonScreen(screen,TOPICS['castle_exceptions'])
        obj.draw((-1,-1))
        obj.draw_confirmation((-1,-1))
    add('lesson-confirm', lesson_confirm)
    add('requirements', lambda: open_topic_requirements(screen,'castle_nested_loops',[]),True)
    add('challenges', lambda: open_topic_challenges(screen,TOPICS['castle_dictionaries'],[]),True)
    add('practice-menu', lambda: open_code_practice_menu(screen),True)
    add('practice-topics', lambda: open_practice_topics(screen,get_stage('castle'),list(TOPICS)),True)
    def bag():
        obj = InventoryScreen(screen,inventory)
        obj.progress = 1
        obj._draw_panel((-1,-1))
    add('inventory',bag)
    def chat():
        obj = MangTahimikChat(screen)
        obj.question = 'how do i fix this code? ' * 18
        obj.cursor = len(obj.question)
        obj.draw()
    add('tutor',chat)
    add('trap',lambda: open_trap_alert(screen),True)
    add('final-warning',lambda: open_final_challenge_warning(screen),True)
    add('boss-intro',lambda: open_boss_intro(screen,'zombie_aktan'),True)
    add('boss-win',lambda: open_boss_result(screen,True),True)
    add('boss-loss',lambda: open_boss_result(screen,False),True)
    add('boss-retreat',lambda: open_boss_retreat_warning(screen),True)
    add('sealed-gate',lambda: open_stage_gate(screen,evaluate_stage_gate(get_stage('castle'),0,[])),True)
    completed = [*get_stage('castle')['manual']['topics'],'castle_supply_final']
    add('complete-gate',lambda: open_stage_gate(screen,evaluate_stage_gate(get_stage('castle'),5,completed,['zombie_aktan'])),True)
    add('assessment',lambda: assessment_dialog(screen,'CASTLE FINAL ASSESSMENT',[
        'Castle Supply Report', 'Time limit: 20:00. The timer starts when you press START.',
        'Includes 300 earned bonus seconds (up to 300 per attempt), spent only when you START.',
        'You can RUN, correct errors, and SUBMIT again while time remains.',
        'Timing out, exiting the editor, or closing the game ends this attempt. Your next attempt uses the stage’s assessment rotation. Boss victory is kept.',
        'ESC here returns to the game without starting an attempt.']),True)
    add('unsaved',lambda: confirm_unsaved_exit(screen,save=lambda: None),True)
    add('game-over',lambda: game_over_screen(screen),True)
    def editor(mode='challenge',feedback=None,settings=False):
        obj = CodeEditor(screen,CHALLENGES['castle_manifest_final'],screen.copy(),mode=mode,time_limit=900 if mode=='assessment' else None)
        obj.renderer.draw()
        if feedback is not None:
            obj._show_submission_feedback(feedback,'Challenge complete' if feedback else 'Try again',
                'All function cases passed.' if feedback else 'The returned answer does not match the required value.',
                'Input: read_manifest([(\'ink\', \'2\')], \'END\')\nActual: None\nExpected: {\'ink\': 2}')
            obj.draw_submission_feedback()
        if settings:
            obj.settings_panel.layout(obj.renderer.panel_rect)
            obj.settings_panel.open()
            obj.settings_panel.draw()
    add('editor',editor)
    add('editor-success',lambda:editor(feedback=True))
    add('editor-error',lambda:editor(feedback=False))
    add('editor-settings',lambda:editor(settings=True))
    def loading():
        obj = StageLoadingScreen(screen,stage_id='castle',stage_name='Dungeon Prison',stage_label='Stage 2 - Intermediate',seed=4)
        obj.progress = 76
        obj.draw()
    add('loading',loading)
    add('gameplay',lambda:game.game_screen(screen,1,state),True,frame='game_screen')
    add('world-map',lambda:game.game_screen(screen,1,state),True,frame='game_screen')
    add('pause',lambda:game.game_screen(screen,1,state),True,
        [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE,unicode='')],frame='game_screen')
    add('tutorial',lambda:tutorial_screen(screen,play_music=False),True,frame='tutorial_screen')
    add('tutorial-manual',lambda:tutorial_screen(screen,play_music=False),True,frame='tutorial_screen')
    add('tutorial-exit',lambda:tutorial_screen(screen,play_music=False),True,frame='tutorial_screen')
    add('combat-practice',lambda:tutorial_screen(screen,play_music=False,practice_only=True),True,frame='tutorial_screen')
    results = []
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as temp, patch.object(save_manager,'SAVE_DIR',temp):
        save_manager.save_slot(1,state)
        for name,callback,loop,events,target_frame in cases:
            if selected and name not in selected:
                continue
            screen.fill((12,16,24))
            tick = [0]
            def pump(*args,**kwargs):
                if target_frame:
                    frame = inspect.currentframe().f_back
                    while frame and '/src/screens/' not in frame.f_code.co_filename:
                        frame = frame.f_back
                    if frame and frame.f_code.co_name != target_frame:
                        return []
                tick[0] += 1
                return events if events and tick[0]==1 else []
            def present():
                if name == 'world-map' and inspect.currentframe().f_back.f_code.co_name == 'open_world_map':
                    raise Captured
                if target_frame:
                    frame = inspect.currentframe().f_back
                    if frame.f_code.co_name != target_frame:
                        return
                    if name == 'tutorial-manual':
                        frame.f_locals['draw_stage_manual'](screen,(-1,-1))
                    elif name == 'tutorial-exit':
                        frame.f_locals['draw_exit_confirmation'](screen)
                    elif name == 'world-map':
                        frame.f_locals['show_world_map'](False)
                raise Captured
            with ExitStack() as stack:
                stack.enter_context(patch.object(pygame.event,'get',pump))
                stack.enter_context(patch.object(pygame.display,'flip',present))
                stack.enter_context(patch.object(pygame.key,'get_pressed',return_value=defaultdict(bool)))
                stack.enter_context(patch.object(pygame.mouse,'get_pos',return_value=(-1,-1)))
                stack.enter_context(patch.object(StageLoadingScreen,'finish'))
                stack.enter_context(patch.object(StageLoadingScreen,'_fade_from_previous'))
                if name == 'game-over':
                    milliseconds = iter(range(0,1000000,5000))
                    stack.enter_context(patch.object(pygame.time,'get_ticks',side_effect=lambda: next(milliseconds)))
                try:
                    callback()
                    status = 'rendered'
                except Captured:
                    status = 'rendered'
                except Exception as error:
                    status = type(error).__name__+': '+str(error)
            if status == 'rendered':
                pygame.image.save(screen,str(output/(name+'.png')))
            results.append({'screen':name,'status':status})
            print(name,status,flush=True)
    (output/'manifest.json').write_text(json.dumps({'size':size,'font_size':font_size,'results':results},indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('/tmp/codebreak-layout'))
    parser.add_argument('--size',default='1920x1080')
    parser.add_argument('--font-size',type=int,default=28)
    parser.add_argument('--screens',nargs='*')
    args = parser.parse_args()
    run(args.output,tuple(map(int,args.size.split('x'))),args.font_size,args.screens)
