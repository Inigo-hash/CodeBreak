""" import sys, os



pygame.init()

screen = pygame.display.set_mode((400, 300))  
pygame.display.set_caption("Walk Animation")

frames = [pygame.image.load(f"assets/images/frames/main_character/walking/walking_forward/frame_{i}.png").convert_alpha() for i in range(8)]
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
    clock.tick(60) """

import pygame


class MainCharacter():
    def __init__(self, screen, map_width, map_height):
        self.screen = screen
        
        # 8 frames 
        idle_right_frames = [pygame.image.load(f"assets/images/frames/main_character/idle/idle_right/frame_{i}.png").convert_alpha() for i in range(8)]
        self.idle_right_frames = [pygame.transform.scale(f, (f.get_width() // 5, f.get_height() // 5)) for f in idle_right_frames] 
    
        walking_left_frames = [pygame.image.load(f"assets/images/frames/main_character/walking/walking_left/frame_{i}.png").convert_alpha() for i in range(8)]
        self.walking_left_frames = [pygame.transform.scale(f, (f.get_width() // 5, f.get_height() // 5)) for f in walking_left_frames] 

        walking_right_frames = [pygame.image.load(f"assets/images/frames/main_character/walking/walking_right/frame_{i}.png").convert_alpha() for i in range(8)]
        self.walking_right_frames = [pygame.transform.scale(f, (f.get_width() // 5, f.get_height() // 5)) for f in walking_right_frames] 
        
        walking_forward_frames = [pygame.image.load(f"assets/images/frames/main_character/walking/walking_forward/frame_{i}.png").convert_alpha() for i in range(8)]
        self.walking_forward_frames = [pygame.transform.scale(f, (f.get_width() // 4.5, f.get_height() // 4.5)) for f in walking_forward_frames] 
        
        walking_backward_frames = [pygame.image.load(f"assets/images/frames/main_character/walking/walking_backward/frame_{i}.png").convert_alpha() for i in range(8)]
        self.walking_backward_frames = [pygame.transform.scale(f, (f.get_width() // 5, f.get_height() // 5)) for f in walking_backward_frames] 


        self.current_frames = idle_right_frames
        self.pos_x, self.pos_y = map_width // 2, map_height // 2
        self.current, self.timer = 0, 0
        


    def update_frames(self, keys):
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.current_frames = self.walking_forward_frames
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.current_frames = self.walking_backward_frames
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.current_frames = self.walking_left_frames
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.current_frames = self.walking_right_frames
        else:
            self.current_frames = self.idle_right_frames  

    def update_position(self, dx, dy, player_rect, player_x, player_y, collision_rects, map_width, map_height):
        player_x += dx
        player_rect.x = round(player_x)
        for rect in collision_rects:
            if player_rect.colliderect(rect):
                if dx > 0:
                    player_rect.right = rect.left
                elif dx < 0:
                    player_rect.left = rect.right
                player_x = float(player_rect.x)

        player_y += dy
        player_rect.y = round(player_y)
        for rect in collision_rects:
            if player_rect.colliderect(rect):
                if dy > 0:
                    player_rect.bottom = rect.top
                elif dy < 0:
                    player_rect.top = rect.bottom
                player_y = float(player_rect.y)

        player_rect.clamp_ip(pygame.Rect(0, 0, map_width, map_height))

        self.pos_x = float(player_rect.x)
        self.pos_y = float(player_rect.y)     

    def draw_frames(self, ZOOM, camera_x, camera_y):
        self.timer += 1
        if self.timer >= 6:
            self.timer = 0
            self.current = (self.current + 1) % 8
        self.screen.blit(self.current_frames[self.current], (self.pos_x * ZOOM - camera_x, self.pos_y * ZOOM - camera_y))


