"""
editor_theme.py

Contains all colors, fonts, spacing, and sizing used by the
CodeBreak coding environment.

Changing values here automatically updates the appearance
of the entire editor.

COLOR THEMES
------------
The editor ships with three color themes (see THEMES below), and the
player picks one from the settings panel. A theme only ever restyles
the coding environment - the dungeon, menus and the rest of the game
are drawn from their own palettes and are never touched by this file.

Every themeable color below is a `pygame.Color` object rather than a
plain (r, g, b) tuple, and `apply_theme()` edits those objects IN PLACE
instead of reassigning them. That detail matters: the editor modules
pull these names in with `from src.ui.editor_theme import *`, which
copies whatever each name pointed at *at import time*. Rebinding
`PANEL_COLOR` here would leave all those modules holding the old value,
so switching themes would appear to do nothing. Mutating the shared
object means every module sees the new color on the very next frame,
with no reimporting and no changes needed at the call sites.
"""

import pygame

# Aliased to a private name so `from editor_theme import *` (which the editor
# modules use) does not re-export the loaders alongside the fonts themselves.
from src.ui.theme import body_font as _body_font, title_font as _title_font

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
# Color Themes
# --------------------------------------------------
#
# Each theme is a plain dict mapping a color name to an (r, g, b)
# tuple. Every theme must define every key - a missing one would
# leave that color stuck on whatever the previous theme set it to.
#
#   BLUE  - CodeBreak's own palette, the editor's original look.
#   DARK  - after Visual Studio Code's "Dark Modern".
#   LIGHT - after Visual Studio Code's "Light Modern".

THEMES = {

    # ---------------- BLUE (CodeBreak original) ----------------
    "BLUE": {
        "BACKGROUND_COLOR": (24, 28, 36),
        "HEADER_COLOR": (36, 41, 51),
        "PANEL_COLOR": (46, 52, 64),
        "EDITOR_COLOR": (30, 34, 42),
        "OUTPUT_COLOR": (20, 22, 28),
        "BUTTON_COLOR": (70, 110, 180),
        "BUTTON_HOVER_COLOR": (90, 135, 210),
        "BUTTON_TEXT_COLOR": (240, 240, 240),
        "TEXT_COLOR": (240, 240, 240),
        "SECONDARY_TEXT": (180, 180, 180),
        "BORDER_COLOR": (85, 90, 100),
        "SUCCESS_COLOR": (70, 200, 120),
        "ERROR_COLOR": (220, 80, 80),
        "SPLITTER_COLOR": (46, 52, 64),
        "SPLITTER_HOVER_COLOR": (70, 110, 180),
        "SPLITTER_GRIP_COLOR": (120, 128, 142),
        "TAB_COLOR": (36, 41, 51),
        "TAB_ACTIVE_COLOR": (46, 52, 64),
        "SCROLLBAR_TRACK_COLOR": (52, 58, 70),
        "SCROLLBAR_THUMB_COLOR": (120, 128, 142),

        "SYNTAX_KEYWORD_COLOR": (198, 120, 221),    # def, if, return, for...
        "SYNTAX_BUILTIN_COLOR": (86, 182, 194),     # print, len, range...
        "SYNTAX_STRING_COLOR": (152, 195, 121),     # "text", 'text'
        "SYNTAX_NUMBER_COLOR": (209, 154, 102),     # 18, 3.14
        "SYNTAX_COMMENT_COLOR": (106, 115, 125),    # # comment
        "SYNTAX_FUNCTION_COLOR": (229, 192, 123),   # name after def / class
        "SYNTAX_SELF_COLOR": (224, 108, 117),       # self, cls
        "SYNTAX_DECORATOR_COLOR": (209, 154, 102),  # @staticmethod
    },

    # ---------------- DARK (VS Code "Dark Modern") ----------------
    "DARK": {
        "BACKGROUND_COLOR": (24, 24, 24),
        "HEADER_COLOR": (24, 24, 24),
        "PANEL_COLOR": (31, 31, 31),
        "EDITOR_COLOR": (31, 31, 31),
        "OUTPUT_COLOR": (24, 24, 24),
        "BUTTON_COLOR": (0, 120, 212),
        "BUTTON_HOVER_COLOR": (0, 134, 239),
        "BUTTON_TEXT_COLOR": (255, 255, 255),
        "TEXT_COLOR": (204, 204, 204),
        "SECONDARY_TEXT": (157, 157, 157),
        "BORDER_COLOR": (43, 43, 43),
        "SUCCESS_COLOR": (137, 209, 133),
        "ERROR_COLOR": (248, 81, 73),
        "SPLITTER_COLOR": (43, 43, 43),
        "SPLITTER_HOVER_COLOR": (0, 120, 212),
        "SPLITTER_GRIP_COLOR": (110, 110, 110),
        "TAB_COLOR": (24, 24, 24),
        "TAB_ACTIVE_COLOR": (31, 31, 31),
        "SCROLLBAR_TRACK_COLOR": (31, 31, 31),
        "SCROLLBAR_THUMB_COLOR": (79, 79, 79),

        "SYNTAX_KEYWORD_COLOR": (86, 156, 214),     # def, if, return, for...
        "SYNTAX_BUILTIN_COLOR": (220, 220, 170),    # print, len, range...
        "SYNTAX_STRING_COLOR": (206, 145, 120),     # "text", 'text'
        "SYNTAX_NUMBER_COLOR": (181, 206, 168),     # 18, 3.14
        "SYNTAX_COMMENT_COLOR": (106, 153, 85),     # # comment
        "SYNTAX_FUNCTION_COLOR": (220, 220, 170),   # name after def / class
        "SYNTAX_SELF_COLOR": (86, 156, 214),        # self, cls
        "SYNTAX_DECORATOR_COLOR": (220, 220, 170),  # @staticmethod
    },

    # ---------------- LIGHT (VS Code "Light Modern") ----------------
    #
    # The syntax colors here are darker than the other two themes on
    # purpose. The BLUE/DARK token colors are tuned for a dark editor
    # and would wash out badly against a white background.
    "LIGHT": {
        "BACKGROUND_COLOR": (248, 248, 248),
        "HEADER_COLOR": (248, 248, 248),
        "PANEL_COLOR": (255, 255, 255),
        "EDITOR_COLOR": (255, 255, 255),
        "OUTPUT_COLOR": (248, 248, 248),
        "BUTTON_COLOR": (0, 95, 184),
        "BUTTON_HOVER_COLOR": (26, 115, 199),
        "BUTTON_TEXT_COLOR": (255, 255, 255),
        "TEXT_COLOR": (59, 59, 59),
        "SECONDARY_TEXT": (97, 97, 97),
        "BORDER_COLOR": (229, 229, 229),
        "SUCCESS_COLOR": (56, 138, 52),
        "ERROR_COLOR": (205, 49, 49),
        "SPLITTER_COLOR": (229, 229, 229),
        "SPLITTER_HOVER_COLOR": (0, 95, 184),
        "SPLITTER_GRIP_COLOR": (148, 148, 148),
        "TAB_COLOR": (236, 236, 236),
        "TAB_ACTIVE_COLOR": (255, 255, 255),
        "SCROLLBAR_TRACK_COLOR": (248, 248, 248),
        "SCROLLBAR_THUMB_COLOR": (193, 193, 193),

        "SYNTAX_KEYWORD_COLOR": (0, 0, 255),        # def, if, return, for...
        "SYNTAX_BUILTIN_COLOR": (121, 94, 38),      # print, len, range...
        "SYNTAX_STRING_COLOR": (163, 21, 21),       # "text", 'text'
        "SYNTAX_NUMBER_COLOR": (9, 134, 88),        # 18, 3.14
        "SYNTAX_COMMENT_COLOR": (0, 128, 0),        # # comment
        "SYNTAX_FUNCTION_COLOR": (121, 94, 38),     # name after def / class
        "SYNTAX_SELF_COLOR": (0, 0, 255),           # self, cls
        "SYNTAX_DECORATOR_COLOR": (121, 94, 38),    # @staticmethod
    },
}

# Order the settings panel cycles through with its arrows.
THEME_NAMES = ("BLUE", "DARK", "LIGHT")

DEFAULT_THEME = "BLUE"

# --------------------------------------------------
# Colors
# --------------------------------------------------
#
# Declared here so editors and readers can still see the full list of
# color names at a glance. The values are placeholders - apply_theme()
# at the bottom of this section fills in the real ones.

BACKGROUND_COLOR = pygame.Color(0, 0, 0)

HEADER_COLOR = pygame.Color(0, 0, 0)

PANEL_COLOR = pygame.Color(0, 0, 0)

EDITOR_COLOR = pygame.Color(0, 0, 0)

OUTPUT_COLOR = pygame.Color(0, 0, 0)

BUTTON_COLOR = pygame.Color(0, 0, 0)

BUTTON_HOVER_COLOR = pygame.Color(0, 0, 0)

# Kept separate from TEXT_COLOR: button labels sit on a saturated blue
# fill, not on the panel background, so in a light theme the ordinary
# dark body text would be nearly unreadable there.
BUTTON_TEXT_COLOR = pygame.Color(0, 0, 0)

TEXT_COLOR = pygame.Color(0, 0, 0)

SECONDARY_TEXT = pygame.Color(0, 0, 0)

BORDER_COLOR = pygame.Color(0, 0, 0)

SUCCESS_COLOR = pygame.Color(0, 0, 0)

ERROR_COLOR = pygame.Color(0, 0, 0)

# Draggable dividers between the objective / code / output panes.
SPLITTER_COLOR = pygame.Color(0, 0, 0)

SPLITTER_HOVER_COLOR = pygame.Color(0, 0, 0)

SPLITTER_GRIP_COLOR = pygame.Color(0, 0, 0)

# Tab strip above the code area ("main.py").
TAB_COLOR = pygame.Color(0, 0, 0)

TAB_ACTIVE_COLOR = pygame.Color(0, 0, 0)

# Scrollbar track / thumb (shared by every scrollable pane).
SCROLLBAR_TRACK_COLOR = pygame.Color(0, 0, 0)

SCROLLBAR_THUMB_COLOR = pygame.Color(0, 0, 0)

# --------------------------------------------------
# Syntax Highlighting
# --------------------------------------------------

SYNTAX_KEYWORD_COLOR = pygame.Color(0, 0, 0)     # def, if, return, for...

SYNTAX_BUILTIN_COLOR = pygame.Color(0, 0, 0)     # print, len, range...

SYNTAX_STRING_COLOR = pygame.Color(0, 0, 0)      # "text", 'text'

SYNTAX_NUMBER_COLOR = pygame.Color(0, 0, 0)      # 18, 3.14

SYNTAX_COMMENT_COLOR = pygame.Color(0, 0, 0)     # # comment

SYNTAX_FUNCTION_COLOR = pygame.Color(0, 0, 0)    # name after def / class

SYNTAX_SELF_COLOR = pygame.Color(0, 0, 0)        # self, cls

SYNTAX_DECORATOR_COLOR = pygame.Color(0, 0, 0)   # @staticmethod

# --------------------------------------------------
# Switching Themes
# --------------------------------------------------

_current_theme = None


def apply_theme(name):
    """
    Repaints the editor in the theme called `name` (one of THEME_NAMES).

    Each color object above is updated in place, so every module that
    already imported these names picks up the new palette on its next
    draw. Unknown names fall back to DEFAULT_THEME rather than raising,
    so a stale saved setting can never crash the game on startup.

    Returns the name of the theme actually applied.
    """

    global _current_theme

    if name not in THEMES:
        name = DEFAULT_THEME

    palette = THEMES[name]

    for color_name, (red, green, blue) in palette.items():
        color = globals()[color_name]
        color.r = red
        color.g = green
        color.b = blue
        color.a = 255

    _current_theme = name

    return name


def get_theme():
    """Returns the name of the theme currently applied."""

    return _current_theme


apply_theme(DEFAULT_THEME)

# --------------------------------------------------
# Fonts
# --------------------------------------------------

pygame.font.init()

# Chrome (window title, panel headers) uses the display face so the editor
# matches the menus; everything that has to line up with code — the buffer
# itself, the gutter, the output log — stays monospace.
# Every pane draws its body copy at the SAME size. The objective used to
# read at one size, the code at another and the output at a third, which
# made the three panes look like three different programs sitting next to
# each other. TEXT_FONT is now the single body size shared by all of them,
# and SMALL_FONT is only for the little grey section labels.

TITLE_FONT = _title_font(28)

HEADER_FONT = _title_font(23, bold=False)

BUTTON_FONT = _title_font(21, bold=False)

# Shared body size: objective text, code, and output all render at this.
TEXT_FONT = _body_font(24)

CODE_FONT = TEXT_FONT

SMALL_FONT = _body_font(20)

# --------------------------------------------------
# Layout
# --------------------------------------------------

# Tall enough for the title face plus the EXIT button and settings
# wheel that share the title bar with it.
HEADER_HEIGHT = 56

BUTTON_HEIGHT = 50

BUTTON_WIDTH = 150

LINE_NUMBER_WIDTH = 55

PANEL_RADIUS = 8

BUTTON_RADIUS = 8

# Vertical distance between two lines of code in the editor. Kept a
# little taller than TEXT_FONT's own line height so the code breathes.
LINE_SPACING = TEXT_FONT.get_linesize() + 2

# Tab strip that sits above the code area and shows the file name.
EDITOR_TAB_HEIGHT = 32

# Height of the fixed title strip ("OBJECTIVE" / "OUTPUT") at the top of
# the side panes. Derived from HEADER_FONT so bumping the font size here
# never clips those headings.
PANE_TITLE_HEIGHT = HEADER_FONT.get_height() + 14

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
MIN_SIDE_PANE_WIDTH = 200

MIN_EDITOR_PANE_WIDTH = 280

# Default divider positions, as fractions of the body width.
DEFAULT_LEFT_SPLIT = 0.25

DEFAULT_RIGHT_SPLIT = 0.73

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