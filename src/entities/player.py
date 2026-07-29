import pygame


class MainCharacter():
    def __init__(self, screen, map_width, map_height):
        self.screen = screen

        # 8 frames each
        idle_right_frames = [pygame.image.load(f"assets/images/frames/main_character/idle/idle_right/frame_{i}.png").convert_alpha() for i in range(8)]
        self.idle_right_frames = [pygame.transform.scale(f, (f.get_width() // 5, f.get_height() // 5)) for f in idle_right_frames]

        walking_left_frames = [pygame.image.load(f"assets/images/frames/main_character/walking/walking_left/frame_{i}.png").convert_alpha() for i in range(8)]
        self.walking_left_frames = [pygame.transform.scale(f, (f.get_width() // 5, f.get_height() // 5)) for f in walking_left_frames]

        walking_right_frames = [pygame.image.load(f"assets/images/frames/main_character/walking/walking_right/frame_{i}.png").convert_alpha() for i in range(8)]
        self.walking_right_frames = [pygame.transform.scale(f, (f.get_width() // 5, f.get_height() // 5)) for f in walking_right_frames]

        walking_forward_frames = [pygame.image.load(f"assets/images/frames/main_character/walking/walking_forward/frame_{i}.png").convert_alpha() for i in range(8)]
        self.walking_forward_frames = [pygame.transform.scale(f, (f.get_width() // 5, f.get_height() // 5)) for f in walking_forward_frames]


        target_size = self.walking_forward_frames[0].get_size()

        walking_backward_frames = [pygame.image.load(f"assets/images/frames/main_character/walking/walking_backward/frame_{i}.png").convert_alpha() for i in range(8)]
        self.walking_backward_frames = [self.normalize_frame(f, target_size) for f in walking_backward_frames]

        self.current_frames = self.idle_right_frames
        self.pos_x, self.pos_y = map_width // 2, map_height // 2
        self.current, self.timer = 0, 0

    def normalize_frame(self, image, size):
        scale_factor = min(size[0] / image.get_width(), size[1] / image.get_height())
        new_w = int(image.get_width() * scale_factor + 150)
        new_h = int(image.get_height() * scale_factor + 150)
        scaled = pygame.transform.scale(image, (new_w, new_h))

        canvas = pygame.Surface(size, pygame.SRCALPHA)
        rect = scaled.get_rect(center=(size[0] // 2, size[1] // 2))
        canvas.blit(scaled, rect)
        return canvas

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
        self.center_x = player_rect.centerx
        self.center_y = player_rect.centery

    def draw_frames(self, ZOOM, camera_x, camera_y):
        self.timer += 1
        if self.timer >= 6:
            self.timer = 0
            self.current = (self.current + 1) % 8

        frame = self.current_frames[self.current]
        draw_x = self.center_x * ZOOM - camera_x - frame.get_width() // 2
        draw_y = self.center_y * ZOOM - camera_y - frame.get_height() // 2
        self.screen.blit(frame, (draw_x, draw_y))