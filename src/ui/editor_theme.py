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
# Popup Panel (overlay that grows with the window)
# --------------------------------------------------

# The popup is no longer a fixed box. It scales with the window so
# the three panes (objective / code / output) each get a usable
# amount of room, while the bounds below stop it from stretching
# absurdly wide on a large monitor or overflowing a small one.

PANEL_SCREEN_RATIO_X = 0.94

PANEL_SCREEN_RATIO_Y = 0.92

PANEL_MAX_WIDTH = 1440

PANEL_MAX_HEIGHT = 880

PANEL_MIN_WIDTH = 700

PANEL_MIN_HEIGHT = 460

# Smallest gap kept between the popup and the window edge.
PANEL_SCREEN_MARGIN = 24

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

# Draggable dividers between the objective / code / output panes.
SPLITTER_COLOR = (46, 52, 64)

SPLITTER_HOVER_COLOR = (70, 110, 180)

SPLITTER_GRIP_COLOR = (120, 128, 142)

# Tab strip above the code area ("main.py").
TAB_COLOR = (36, 41, 51)

TAB_ACTIVE_COLOR = (46, 52, 64)

# Scrollbar track / thumb (shared by every scrollable pane).
SCROLLBAR_TRACK_COLOR = (52, 58, 70)

SCROLLBAR_THUMB_COLOR = (120, 128, 142)

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

BUTTON_HEIGHT = 50

BUTTON_WIDTH = 150

LINE_NUMBER_WIDTH = 55

PANEL_RADIUS = 8

BUTTON_RADIUS = 8

# Vertical distance between two lines of code in the editor.
LINE_SPACING = 20

# Tab strip that sits above the code area and shows the file name.
EDITOR_TAB_HEIGHT = 30

# --------------------------------------------------
# Three-Pane Layout
# --------------------------------------------------
#
# The popup body is split into three side-by-side panes:
#
#     [ objective ] || [ code editor ] || [ output ]
#
# The two "||" dividers are draggable, so the player decides how
# much room each pane gets. Their positions are stored as fractions
# of the body width (see EditorRenderer), which keeps the layout
# correct no matter how large the window is.

# Width of a draggable divider - wide enough to grab comfortably.
SPLITTER_WIDTH = 10

# A pane can never be dragged smaller than these widths, so no pane
# can be squashed until its content becomes unreadable.
MIN_SIDE_PANE_WIDTH = 160

MIN_EDITOR_PANE_WIDTH = 280

# Default divider positions, as fractions of the body width.
DEFAULT_LEFT_SPLIT = 0.22

DEFAULT_RIGHT_SPLIT = 0.72

# --------------------------------------------------
# Scrollbars
# --------------------------------------------------

SCROLLBAR_WIDTH = 8

SCROLLBAR_MARGIN = 4

# Shortest a scrollbar thumb is allowed to get, so it stays
# grabbable even with a very long document.
SCROLLBAR_MIN_THUMB = 20

# Lines the objective / output panes move per mouse-wheel notch.
# The code editor deliberately stays at one line per notch, which
# is what it has always done.
WHEEL_LINES = 3