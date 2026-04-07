import pygame
import sys
from src.ui.button import Button

def settings_screen(screen):
    from src.screens.main_menu import main_menu
    
    BLUE = (70, 130, 180)
    LIGHT_BLUE = (100, 160, 210)
    GRAY = (50, 50, 50)
    WHITE = (255, 255, 255)
    
    back_button = Button(50, 50, 200, 60, "Back", BLUE, LIGHT_BLUE)
    
    title_font = pygame.font.Font(None, 80)
    clock = pygame.time.Clock()
    running = True
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        back_button.check_hover(mouse_pos)
        
        if back_button.is_clicked(mouse_pos, mouse_pressed):
            return  # Go back to main menu
        
        screen.fill(GRAY)
        
        title = title_font.render("Settings", True, WHITE)
        screen.blit(title, (screen.get_width()//2 - title.get_width()//2, 200))
        
        back_button.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)