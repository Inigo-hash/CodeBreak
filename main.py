import pygame
import sys
from src.screens.main_menu import main_menu
from pytmx.util_pygame import load_pygame

# Initialize Pygame
pygame.init()

def main():
    # Start with main menu
    main_menu()

if __name__ == "__main__":
    main()