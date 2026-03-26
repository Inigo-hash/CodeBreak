import pygame
import sys

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

# Button class
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
    
    def draw(self, surface):
        # Choose color based on hover state
        current_color = self.hover_color if self.is_hovered else self.color
        
        # Draw button rectangle
        pygame.draw.rect(surface, current_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, 3, border_radius=10)  # Border
        
        # Draw button text
        text_surface = button_font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]

# Create buttons
start_button = Button(SCREEN_WIDTH//2 - 150, 300, 300, 70, "Start Game", BLUE, LIGHT_BLUE)
settings_button = Button(SCREEN_WIDTH//2 - 150, 400, 300, 70, "Settings", BLUE, LIGHT_BLUE)
exit_button = Button(SCREEN_WIDTH//2 - 150, 500, 300, 70, "Exit", BLUE, LIGHT_BLUE)

# Main menu loop
def main_menu():
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
            print("Start Game clicked!")  # Replace with actual game start later
            # For now, just show it works
            
        if settings_button.is_clicked(mouse_pos, mouse_pressed):
            print("Settings clicked!")  # Replace with settings screen later
            
        if exit_button.is_clicked(mouse_pos, mouse_pressed):
            pygame.quit()
            sys.exit()
        
        # Draw everything
        screen.fill(GRAY)  # Background
        
        # Draw title
        title_text = title_font.render("CodeBreak", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 150))
        screen.blit(title_text, title_rect)
        
        # Draw buttons
        start_button.draw(screen)
        settings_button.draw(screen)
        exit_button.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)  # 60 FPS

# Run the main menu
if __name__ == "__main__":
    main_menu()