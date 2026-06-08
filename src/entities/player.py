import sys, os
import pygame


pygame.init()

screen = pygame.display.set_mode((400, 300))  
pygame.display.set_caption("Walk Animation")

frames = [pygame.image.load(f"assets/images/frames/main_character/idle_right/frame_{i}.png").convert_alpha() for i in range(8)]
frames = [pygame.transform.scale(f, (f.get_width() // 4, f.get_height() // 4)) for f in frames] 

screen = pygame.display.set_mode((frames[0].get_width() + 40, frames[0].get_height() + 40))
clock = pygame.time.Clock()

current, timer = 0, 0

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    timer += 1
    if timer >= 6:
        timer = 0
        current = (current + 1) % len(frames)
        
    screen.fill((30, 30, 30))
    screen.blit(frames[current], (20, 20))
    pygame.display.flip()
    clock.tick(60)