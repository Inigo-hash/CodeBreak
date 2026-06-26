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


    """ 
     ok the usual, writing what im thinking, so for today, im thinking of generating some frames 
     for the main character, specifically the walking frames, because currently, it looks really
     bad, mmmm at the same time though i think i should be doing something else? mmm like
     maybe understanding the codebase(understanding collisions? ohhh, what )? modifying the trees?

     what if we kinda multitask? like just let the a.i generate the frames in the background?
     and then i'll understand how collision works?

    """