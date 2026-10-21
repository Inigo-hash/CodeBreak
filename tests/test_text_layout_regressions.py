"""Measure actual rendered labels at accessibility sizes, not just font constants."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from itertools import combinations
import unittest
from unittest.mock import patch
import pygame
from src.settings_state import settings_state
from src.ui.theme import body_font,title_font,ui_font,clear_font_cache
from src.ui.text_layout import fit_text,wrap_text


class RecordedSurface(pygame.Surface):
    def __init__(self,size,labels):
        super().__init__(size)
        self.labels = labels
        self.text = []

    def blit(self,source,dest,*args,**kwargs):
        item = self.labels.get(id(source))
        if item:
            position = dest.topleft if isinstance(dest,pygame.Rect) else dest[:2]
            self.text.append((item[1],source.get_rect(topleft=position)))
        return super().blit(source,dest,*args,**kwargs)


def recording_fit(labels):
    def render(font,text,color,size):
        surface = fit_text(font,text,color,size)
        labels[id(surface)] = (surface,text)
        return surface
    return render


class TextLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280,720))

    def setUp(self):
        self.setting = patch.dict(settings_state,font_size=28)
        self.setting.start()
        clear_font_cache()

    def tearDown(self):
        self.setting.stop()
        clear_font_cache()

    def test_menu_labels_stay_inside_rows_and_clear_their_icons(self):
        from src.screens import main_menu as menu
        from src.screens.start_game_menu import SG_LABELS
        for size in ((1280,720),(1366,768),(1920,1080),(1920,1536),(2560,1080)):
            for labels in (menu.MM_LABELS,SG_LABELS):
                recordings = {}
                screen = RecordedSurface(size,recordings)
                with patch.object(menu,'_button_font',title_font(26)),patch.object(menu,'fit_text',recording_fit(recordings)):
                    rows,*_ = menu.compute_menu_layout(*size,len(labels),labels)
                    for row,label in zip(rows,labels):
                        self.assertTrue(screen.get_rect().contains(row))
                        menu._draw_stone_button(screen,row,label,'play',False,11)
                for (_,text_rect),row in zip(screen.text,rows):
                    self.assertTrue(row.contains(text_rect))
                    self.assertGreaterEqual(text_rect.left,row.left+menu.MEDALLION_CLEARANCE-2)
                self.assertFalse(any(a.colliderect(b) for a,b in combinations(rows,2)))

    def test_empty_fitted_label_is_safe_even_when_font_is_taller_than_slot(self):
        result = fit_text(title_font(48),'',(255,255,255),(50,12))
        self.assertEqual(result.get_size(),(1,1))

    def test_menu_tutor_text_does_not_cover_menu_buttons(self):
        from src.screens import main_menu as menu
        from src.screens import mang_tahimik as tutor
        for size in ((1024,768),(1280,720),(1920,1080),(2560,1080)):
            recordings = {}
            screen = RecordedSurface(size,recordings)
            with patch.object(menu,'SCREEN_WIDTH',size[0]),patch.object(menu,'SCREEN_HEIGHT',size[1]), \
                    patch.object(menu,'_button_font',title_font(26)),patch.object(menu,'_tip_font',ui_font(15)), \
                    patch.object(tutor,'fit_text',recording_fit(recordings)):
                rows,*_ = menu.compute_menu_layout(*size,len(menu.MM_LABELS),menu.MM_LABELS)
                menu._draw_mang_tahimik_tip(screen,0)
            self.assertEqual(len(screen.text),2)
            self.assertEqual(tutor.menu_tutor_rect(screen).bottomright,(size[0]-14,size[1]-14))
            self.assertFalse(any(tutor.menu_tutor_rect(screen).colliderect(row) for row in rows))
            for text,rect in screen.text:
                self.assertTrue(screen.get_rect().contains(rect),text)
                self.assertFalse(any(rect.colliderect(row) for row in rows),text)

    def test_practice_card_icon_title_and_status_have_separate_areas(self):
        from src.screens.practice_topics import topic_card_layout
        for height in (76,94,140,166,220):
            card = pygame.Rect(30,30,260,height)
            parts = topic_card_layout(card)
            self.assertTrue(all(card.contains(part) for part in parts))
            self.assertFalse(any(a.colliderect(b) for a,b in combinations(parts,2)))

    def test_compact_tutor_clears_rail_hotbar_and_contains_both_text_lines(self):
        from src.screens import mang_tahimik as tutor
        from src.screens.inventory import PlayerInventory,Toolbar
        from src.ui.stage_panel import StagePanel
        for size in ((1024,768),(1280,720),(1920,1080),(1920,1536),(2560,1080)):
            recordings = {}
            screen = RecordedSurface(size,recordings)
            rect = tutor.tutor_helper_rect(screen)
            self.assertEqual(rect.right,size[0]-14)
            self.assertEqual(rect.bottom,size[1]-14)
            self.assertGreaterEqual(rect.height,100)
            minimap = tutor.tutor_minimap_rect(screen)
            self.assertEqual(minimap.bottomleft,(14,size[1]-14))
            self.assertFalse(rect.colliderect(minimap))
            self.assertTrue(screen.get_rect().contains(minimap))
            rail = StagePanel(screen,learning_progress=True)
            self.assertFalse(any(rect.colliderect(part) for part in rail.button_rects.values()))
            self.assertFalse(rect.colliderect(Toolbar(screen,PlayerInventory()).panel_rect))
            with patch.object(tutor,'fit_text',recording_fit(recordings)):
                tutor.draw_tutor_helper(screen,rect)
            self.assertEqual(len(screen.text),2)
            self.assertTrue(all(rect.contains(text_rect) for _,text_rect in screen.text))
            self.assertFalse(screen.text[0][1].colliderect(screen.text[1][1]))

    def test_chat_is_larger_and_anchored_to_bottom_right(self):
        from src.screens.mang_tahimik import tutor_chat_rect
        for size in ((640,480),(1024,768),(1920,1080),(2560,1080)):
            screen = pygame.Surface(size)
            panel = tutor_chat_rect(screen)
            self.assertEqual(panel.bottomright,(size[0]-14,size[1]-14))
            self.assertTrue(screen.get_rect().contains(panel))
        self.assertEqual(tutor_chat_rect(pygame.Surface((1920,1080))).width,1100)

    def test_control_rows_use_rendered_font_heights_and_separate_key_column(self):
        from src.screens import how_to_play as manual
        from src.data.controls import CONTROL_SECTIONS
        recordings = {}
        screen = RecordedSurface((430,6000),recordings)
        class Font:
            def __init__(self,font): self.font = font
            def __getattr__(self,name): return getattr(self.font,name)
            def render(self,text,*args,**kwargs):
                surface = self.font.render(text,*args,**kwargs)
                recordings[id(surface)] = (surface,text)
                return surface
        with patch.object(manual,'fit_text',recording_fit(recordings)):
            end = manual.draw_control_rows(screen,screen.get_rect(),CONTROL_SECTIONS,
                                           Font(title_font(18)),Font(body_font(14,True)),Font(body_font(14)))
        self.assertGreater(end,500)
        self.assertTrue(all(screen.get_rect().contains(rect) for _,rect in screen.text))
        for (text,a),(other,b) in combinations(screen.text,2):
            self.assertFalse(a.colliderect(b),(text,other,a,b))

    def test_manual_is_scrollable_instead_of_squeezing_text_rows(self):
        from src.screens.how_to_play import manual_layout,draw_manual_columns
        screen = pygame.Surface((1280,720))
        _,left,right,footer = manual_layout(*screen.get_size())
        args = (screen,left,right,footer,title_font(18),body_font(14,True),body_font(14),body_font(12))
        limit = draw_manual_columns(*args)
        self.assertGreater(limit,0)
        self.assertEqual(draw_manual_columns(*args,scroll=limit),limit)

    def test_map_labels_fit_inside_chart_without_overlapping_each_other(self):
        from src.ui.chart import layout_map_labels
        bounds = pygame.Rect(10,10,220,220)
        labels = [('Library Upper Aisle Guards',(60,65),False),
                  ('Library Lower Aisle Guards',(65,68),False),('Library',(60,65),False)]
        result = layout_map_labels(body_font(14),labels,bounds)
        self.assertEqual(len(result),3)
        self.assertTrue(all(bounds.contains(rect) for _,rect,_ in result))
        self.assertFalse(any(a[1].colliderect(b[1]) for a,b in combinations(result,2)))

    def test_tutorial_pagination_keeps_all_words_at_large_fonts(self):
        from src.screens.tutorial import paginate_dialogue
        words = ['word'+str(index) for index in range(100)]
        pages = paginate_dialogue([' '.join(words)],body_font(28),700,3)
        self.assertGreater(len(pages),1)
        self.assertEqual(' '.join(pages).split(),words)
        self.assertTrue(all(len(wrap_text(page,body_font(28),700))<=3 for page in pages))

    def test_complete_castle_manual_does_not_truncate_its_content_buffer(self):
        from src.screens.stage_info import _Fonts,_render_manual,_build_content
        from src.data.stages import get_stage
        from src.systems.stage_progress import StageProgress
        stage = get_stage('castle')
        fonts = _Fonts()
        progress = StageProgress()
        used = _render_manual(pygame.Surface((1000,18000)),fonts,stage,progress,0,0,1000)
        built = _build_content('manual',fonts,stage,progress,1000)
        self.assertGreaterEqual(built.get_height(),used)
