import pygame
import sys
from src.ui.button import Button

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("CodeBreak - Main Menu")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
LIGHT_GRAY = (100, 100, 100)
BLUE = (70, 130, 180)
LIGHT_BLUE = (100, 160, 210)

# Fonts
title_font = pygame.font.Font(None, 100)
button_font = pygame.font.Font(None, 50)

# Main menu loop
def main_menu():
    from src.screens.settings import settings_screen
    from src.screens.tutorial import tutorial_screen
    
    # Create buttons
    start_button = Button(SCREEN_WIDTH//2 - 150, 300, 300, 70, "Start Game", BLUE, LIGHT_BLUE)
    settings_button = Button(SCREEN_WIDTH//2 - 150, 400, 300, 70, "Settings", BLUE, LIGHT_BLUE)
    exit_button = Button(SCREEN_WIDTH//2 - 150, 500, 300, 70, "Exit", BLUE, LIGHT_BLUE)
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        # Check button hovers
        start_button.check_hover(mouse_pos)
        settings_button.check_hover(mouse_pos)
        exit_button.check_hover(mouse_pos)
        
        # Check button clicks
        if start_button.is_clicked(mouse_pos, mouse_pressed):
            tutorial_screen(screen)  # Go to tutorial
            
        if settings_button.is_clicked(mouse_pos, mouse_pressed):
            settings_screen(screen)  # Go to settings
            
        if exit_button.is_clicked(mouse_pos, mouse_pressed):
            pygame.quit()
            sys.exit()
        
        # Draw everything
        screen.fill(GRAY)
        
        # Draw title
        title_text = title_font.render("CodeBreak", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 150))
        screen.blit(title_text, title_rect)
        
        # Draw buttons
        start_button.draw(screen)
        settings_button.draw(screen)
        exit_button.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)