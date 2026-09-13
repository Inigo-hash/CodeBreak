"""Caret placement follows the code font and scrolled character boundaries."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
from unittest.mock import patch
import pygame
from src.data.challenges import CHALLENGES
from src.ui.code_editor import CodeEditor
from src.ui import editor_renderer as renderer_module
from src.ui.theme import MONO_REGULAR


class EditorCaretTests(unittest.TestCase):
    def test_rendered_caret_covers_glyphs_at_multiple_font_sizes(self):
        pygame.init()
        screen = pygame.display.set_mode((1280, 720))
        for size in (16, 24, 32):
            with self.subTest(size=size):
                font = pygame.font.Font(MONO_REGULAR, size)
                editor = CodeEditor(screen, CHALLENGES['print_001'], screen.copy())
                line = 'print("Hello, World!")'
                editor.text_buffer.lines = [line]
                editor.text_buffer.set_cursor(0, len(line))
                renderer = editor.renderer
                with patch.object(renderer_module, 'TEXT_FONT', font), \
                     patch.object(renderer_module, 'LINE_SPACING', font.get_linesize() + 2), \
                     patch.object(pygame.time, 'get_ticks', return_value=0), \
                     patch.object(pygame.draw, 'line', wraps=pygame.draw.line) as draw_line:
                    renderer.draw()
                    expected_x = renderer.get_text_origin_x() + font.size(line)[0]
                    caret = [c.args for c in draw_line.call_args_list
                             if len(c.args) == 5 and c.args[2][0] == expected_x
                             and c.args[3][0] == expected_x and c.args[4] == 2]
                    self.assertEqual(len(caret), 1)
                    glyph = font.render('Mg', True, (255,255,255)).get_bounding_rect()
                    origin_y = renderer.editor_rect.y + 15
                    self.assertLessEqual(caret[0][2][1], origin_y + glyph.top)
                    self.assertGreaterEqual(caret[0][3][1], origin_y + glyph.bottom - 1)

    def test_click_chooses_nearest_boundary_after_horizontal_scroll(self):
        pygame.init()
        screen = pygame.display.set_mode((1280, 720))
        editor = CodeEditor(screen, CHALLENGES['print_001'], screen.copy())
        line = 'print("Hello, World!")'
        editor.text_buffer.lines = [line]
        renderer = editor.renderer
        renderer.h_scroll_offset = 30
        font = renderer_module.TEXT_FONT
        for col in range(len(line)):
            left, right = font.size(line[:col])[0], font.size(line[:col+1])[0]
            for fraction, expected in ((0.2, col), (0.8, col+1)):
                click = (renderer.get_text_origin_x() + left + (right-left)*fraction,
                         renderer.editor_rect.y + 20)
                self.assertEqual(renderer.get_cursor_position_from_mouse(click), (0, expected))
