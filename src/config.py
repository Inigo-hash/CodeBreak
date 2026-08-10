import os

# Must be set before pygame.init() (SDL reads this hint at video subsystem
# init). Without it, SDL auto-minimizes the exclusive-fullscreen window the
# instant it loses OS focus, which is what happens when a screenshot tool
# (Snipping Tool, Game Bar, PrintScreen) briefly steals focus to capture.
os.environ["SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS"] = "0"

import pygame

pygame.init()

FULLSCREEN = True

DISPLAY = pygame.display.Info()

NATIVE_WIDTH = DISPLAY.current_w
NATIVE_HEIGHT = DISPLAY.current_h

if FULLSCREEN:
    SCREEN_WIDTH = NATIVE_WIDTH
    SCREEN_HEIGHT = NATIVE_HEIGHT
else:
    SCREEN_WIDTH = int(NATIVE_WIDTH * 0.8)
    SCREEN_HEIGHT = int(NATIVE_HEIGHT * 0.8)