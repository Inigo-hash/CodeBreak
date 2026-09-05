import pygame
import sys
from src.screens.main_menu import main_menu
from src.settings_state import load_settings
from pytmx.util_pygame import load_pygame

# Initialize Pygame
pygame.init()
pygame.key.set_repeat(400, 35)

def main():
    # Settings are read before the first screen builds a font or starts the
    # music, so a returning player gets the volume, theme, text speed and
    # text size they chose last time rather than the defaults.
    load_settings()

    # Start with main menu
    main_menu()

if __name__ == "__main__":
    main()

        