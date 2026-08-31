import os


def _env_flag(name, default=False):
    """Read a conventional true/false environment flag."""

    value = os.environ.get(name)
    if value is None:
        return bool(default)
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Developer preview keys (F5/F6/F8). F1/F2 remain available to every player
# for light and fog control.
#
# TEMPORARY: default flipped to True for development. Set this back to
# False before any build a player will run, or set CODEBREAK_DEBUG=0 to
# turn the keys off for a single launch.
DEBUG_MODE = _env_flag("CODEBREAK_DEBUG", True)

# Must be set before pygame.init() (SDL reads this hint at video subsystem
# init). Without it, SDL auto-minimizes the exclusive-fullscreen window the
# instant it loses OS focus, which is what happens when a screenshot tool
# (Snipping Tool, Game Bar, PrintScreen) briefly steals focus to capture.
os.environ["SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS"] = "0"
# Ask SDL for physical drawable pixels on Windows displays using 125%/150%
# scaling, so letterbox math is based on the monitor rather than logical DPI.
os.environ.setdefault("SDL_WINDOWS_DPI_AWARENESS", "permonitorv2")

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
