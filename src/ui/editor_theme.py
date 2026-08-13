"""
editor_theme.py

Contains all colors, fonts, spacing, and sizing used by the
CodeBreak coding environment.

Changing values here automatically updates the appearance
of the entire editor.
"""

import pygame

# --------------------------------------------------
# Window
# --------------------------------------------------

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

PADDING = 15

# --------------------------------------------------
# Popup Panel (medium-sized overlay instead of fullscreen)
# --------------------------------------------------

PANEL_WIDTH = 820
PANEL_HEIGHT = 600

# --------------------------------------------------
# Colors
# --------------------------------------------------

BACKGROUND_COLOR = (24, 28, 36)

HEADER_COLOR = (36, 41, 51)

PANEL_COLOR = (46, 52, 64)

EDITOR_COLOR = (30, 34, 42)

OUTPUT_COLOR = (20, 22, 28)

BUTTON_COLOR = (70, 110, 180)

BUTTON_HOVER_COLOR = (90, 135, 210)

TEXT_COLOR = (240, 240, 240)

SECONDARY_TEXT = (180, 180, 180)

BORDER_COLOR = (85, 90, 100)

SUCCESS_COLOR = (70, 200, 120)

ERROR_COLOR = (220, 80, 80)

# --------------------------------------------------
# Syntax Highlighting
# --------------------------------------------------

SYNTAX_KEYWORD_COLOR = (198, 120, 221)     # def, if, return, for...

SYNTAX_BUILTIN_COLOR = (86, 182, 194)      # print, len, range...

SYNTAX_STRING_COLOR = (152, 195, 121)      # "text", 'text'

SYNTAX_NUMBER_COLOR = (209, 154, 102)      # 18, 3.14

SYNTAX_COMMENT_COLOR = (106, 115, 125)     # # comment

SYNTAX_FUNCTION_COLOR = (229, 192, 123)    # name after def / class

SYNTAX_SELF_COLOR = (224, 108, 117)        # self, cls

SYNTAX_DECORATOR_COLOR = (209, 154, 102)   # @staticmethod

# --------------------------------------------------
# Fonts
# --------------------------------------------------

pygame.font.init()

TITLE_FONT = pygame.font.SysFont("consolas", 28, bold=True)

HEADER_FONT = pygame.font.SysFont("consolas", 22)

TEXT_FONT = pygame.font.SysFont("consolas", 20)

CODE_FONT = pygame.font.SysFont("consolas", 22)

SMALL_FONT = pygame.font.SysFont("consolas", 16)

# --------------------------------------------------
# Layout
# --------------------------------------------------

HEADER_HEIGHT = 50

OBJECTIVE_HEIGHT = 90

EDITOR_HEIGHT = 230

OUTPUT_HEIGHT = 90

BUTTON_HEIGHT = 50

BUTTON_WIDTH = 150

LINE_NUMBER_WIDTH = 55

PANEL_RADIUS = 8

BUTTON_RADIUS = 8