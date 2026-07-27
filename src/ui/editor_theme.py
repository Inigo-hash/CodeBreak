import pygame

pygame.font.init()

# ----------------------------
# WINDOW
# ----------------------------
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

FPS = 60

# ----------------------------
# COLORS
# ----------------------------
BACKGROUND = (30, 30, 30)

TOP_BAR = (45, 45, 45)

SIDEBAR = (37, 37, 38)

EDITOR_BG = (24, 24, 24)

OUTPUT_BG = (20, 20, 20)

PANEL_BG = (35, 35, 35)

BUTTON = (50, 100, 200)

BUTTON_HOVER = (70, 120, 230)

BUTTON_TEXT = (255, 255, 255)

TEXT = (220, 220, 220)

TEXT_SECONDARY = (170, 170, 170)

LINE_NUMBER = (120, 120, 120)

CURSOR = (255, 255, 255)

SUCCESS = (50, 200, 50)

ERROR = (220, 80, 80)

BORDER = (70, 70, 70)

# ----------------------------
# FONTS
# ----------------------------
TITLE_FONT = pygame.font.SysFont("consolas", 24, bold=True)

HEADER_FONT = pygame.font.SysFont("consolas", 20)

TEXT_FONT = pygame.font.SysFont("consolas", 18)

EDITOR_FONT = pygame.font.SysFont("consolas", 20)

BUTTON_FONT = pygame.font.SysFont("consolas", 18, bold=True)

OUTPUT_FONT = pygame.font.SysFont("consolas", 18)

# ----------------------------
# LAYOUT
# ----------------------------
TOP_BAR_HEIGHT = 55

PROBLEM_PANEL_WIDTH = 360

OUTPUT_HEIGHT = 150

PADDING = 15

LINE_HEIGHT = 28

LINE_NUMBER_WIDTH = 50

BUTTON_WIDTH = 120

BUTTON_HEIGHT = 40

BUTTON_SPACING = 15

EDITOR_MARGIN = 10