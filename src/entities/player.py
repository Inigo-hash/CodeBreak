import pygame
import numpy as np
import math


class MainCharacter():
    def __init__(self, screen, map_width, map_height):
        self.screen = screen
        self.is_idle = True
        self.idle_bob_timer = 0.0

        frame_sets = {
            'idle_right': "assets/images/frames/main_character/idle/idle_right",
            'idle_left': "assets/images/frames/main_character/idle/idle_left",
            'walking_left': "assets/images/frames/main_character/walking/walking_left",
            'walking_right': "assets/images/frames/main_character/walking/walking_right",
            'walking_forward': "assets/images/frames/main_character/walking/walking_forward",
            'walking_backward': "assets/images/frames/main_character/walking/walking_backward",
        }

        raw_frames = {}
        for key, path in frame_sets.items():
            raw_frames[key] = [pygame.image.load(f"{path}/frame_{i}.png").convert_alpha() for i in range(8)]

        content_heights = {}
        for key, frames in raw_frames.items():
            content_heights[key] = max(self._robust_content_height(f) for f in frames)

        target_content_height = content_heights['idle_right'] * (1 / 5)

        self.scaled = {}
        for key, frames in raw_frames.items():
            factor = target_content_height / content_heights[key]
            self.scaled[key] = [
                pygame.transform.scale(f, (max(1, round(f.get_width() * factor)), max(1, round(f.get_height() * factor))))
                for f in frames
            ]

        self.idle_right_frames = self.scaled['idle_right']
        self.idle_left_frames = self.scaled['idle_left']
        self.walking_left_frames = self.scaled['walking_left']
        self.walking_right_frames = self.scaled['walking_right']
        self.walking_forward_frames = self.scaled['walking_forward']
        self.walking_backward_frames = self.scaled['walking_backward']

        self.idle_forward_frames = [self.walking_forward_frames[0]] * 8
        self.idle_backward_frames = [self.walking_backward_frames[0]] * 8

        self.current_frames = self.idle_right_frames
        self.pos_x, self.pos_y = map_width // 2, map_height // 2
        self.center_x, self.center_y = self.pos_x, self.pos_y
        self.facing = 'right'
        self.current, self.timer = 0, 0

    @staticmethod
    def _robust_content_height(surf, min_pixels=3):
        # Ignores isolated 1-2px noise/artifacts so a stray dot doesn't inflate the measured size
        alpha = pygame.surfarray.array_alpha(surf).T  # (h, w)
        row_counts = (alpha > 0).sum(axis=1)
        rows = np.nonzero(row_counts >= min_pixels)[0]
        if len(rows) == 0:
            return surf.get_height()
        return int(rows.max() - rows.min() + 1)

    def update_frames(self, keys):
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.current_frames = self.walking_forward_frames
            self.facing = 'forward'
            self.is_idle = False
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.current_frames = self.walking_backward_frames
            self.facing = 'backward'
            self.is_idle = False
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.current_frames = self.walking_left_frames
            self.facing = 'left'
            self.is_idle = False
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.current_frames = self.walking_right_frames
            self.facing = 'right'
            self.is_idle = False
        else:
            self.is_idle = True
            idle_map = {
                'left': self.idle_left_frames,
                'right': self.idle_right_frames,
                'forward': self.idle_forward_frames,
                'backward': self.idle_backward_frames,
            }
            self.current_frames = idle_map[self.facing]

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

        if self.is_idle and self.facing in ('forward', 'backward'):
            self.idle_bob_timer += 0.06
            draw_y += math.sin(self.idle_bob_timer) * 2  # 2px amplitude float
        else:
            self.idle_bob_timer = 0.0

        self.screen.blit(frame, (draw_x, draw_y))