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