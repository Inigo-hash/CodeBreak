import pygame
import numpy as np
import math

from src.systems.combat import (
    ATTACK_FRAME_DURATION, DEATH_FRAME_COUNT, DEATH_FRAME_DURATION,
    PLAYER_DODGE_DURATION,
)


class MainCharacter():
    def __init__(self, screen, map_width, map_height):
        self.screen = screen
        self.is_idle = True
        self.idle_bob_timer = 0.0

        # NOTE: fill in the actual folder paths for the four new
        # diagonal walking sets below (walking_northeast, etc).
        # Each folder is expected to contain frame_0.png ... frame_7.png,
        # same as every other entry here.
        frame_sets = {
            'idle_right': "assets/images/frames/main_character/idle/idle_right",
            'idle_left': "assets/images/frames/main_character/idle/idle_left",
            'idle_forward': "assets/images/frames/main_character/idle/idle_forward",
            'idle_backward': "assets/images/frames/main_character/idle/idle_backward",
            'idle_northeast': "assets/images/frames/main_character/idle/idle_forward_right",
            'idle_northwest': "assets/images/frames/main_character/idle/idle_forward_left",
            'idle_southeast': "assets/images/frames/main_character/idle/idle_backward_right",
            'idle_southwest': "assets/images/frames/main_character/idle/idle_backward_left",
            'walking_left': "assets/images/frames/main_character/walking/walking_left",
            'walking_right': "assets/images/frames/main_character/walking/walking_right",
            'walking_forward': "assets/images/frames/main_character/walking/walking_forward",
            'walking_backward': "assets/images/frames/main_character/walking/walking_backward",
            'walking_northeast': "assets/images/frames/main_character/walking/walking_forward_right",
            'walking_northwest': "assets/images/frames/main_character/walking/walking_forward_left",
            'walking_southeast': "assets/images/frames/main_character/walking/walking_backward_right",
            'walking_southwest': "assets/images/frames/main_character/walking/walking_backward_left",
        }

        raw_frames = {}
        for key, path in frame_sets.items():
            raw_frames[key] = [pygame.image.load(f"{path}/frame_{i}.png").convert_alpha() for i in range(8)]

        content_heights = {}
        for key, frames in raw_frames.items():
            content_heights[key] = max(self._robust_content_height(f) for f in frames)

        target_content_height = content_heights['idle_right'] * (1 / 2)

        # self.scaled holds every direction's frames, cardinal and
        # diagonal alike, keyed by the same names used in frame_sets.
        self.scaled = {}
        for key, frames in raw_frames.items():
            factor = target_content_height / content_heights[key]
            self.scaled[key] = [
                pygame.transform.scale(f, (max(1, round(f.get_width() * factor)), max(1, round(f.get_height() * factor))))
                for f in frames
            ]

        combat_directions = {
            'right': 'right', 'left': 'left',
            'forward': 'forward', 'backward': 'backward',
            'northeast': 'forward_right', 'northwest': 'forward_left',
            'southeast': 'backward_right', 'southwest': 'backward_left',
        }
        compass_directions = {
            'right': 'east', 'left': 'west',
            'forward': 'north', 'backward': 'south',
            'northeast': 'north-east', 'northwest': 'north-west',
            'southeast': 'south-east', 'southwest': 'south-west',
        }
        self.attack_frames = {}
        self.flinch_frames = {}
        self.dodge_frames = {}
        self.death_frames = {}
        for facing, asset_direction in combat_directions.items():
            attack_path = f"assets/images/frames/main_character/attacking/attacking_{asset_direction}"
            attacks = [pygame.image.load(f"{attack_path}/frame_{i}.png").convert_alpha() for i in range(9)]
            factor = target_content_height / max(self._robust_content_height(frame) for frame in attacks)
            self.attack_frames[facing] = [
                pygame.transform.scale(frame, (max(1, round(frame.get_width() * factor)),
                                               max(1, round(frame.get_height() * factor))))
                for frame in attacks
            ]
            flinch_name = compass_directions[facing]
            flinch = pygame.image.load(
                f"assets/images/frames/main_character/flinch_with_sword/{flinch_name}.png"
            ).convert_alpha()
            factor = target_content_height / self._robust_content_height(flinch)
            self.flinch_frames[facing] = [pygame.transform.scale(
                flinch, (max(1, round(flinch.get_width() * factor)),
                         max(1, round(flinch.get_height() * factor)))
            )]
            upright = self.flinch_frames[facing][0]
            # No authored death sheet exists. Build a deliberate fall from
            # the authored defeated pose, ending horizontally on the ground.
            self.death_frames[facing] = [
                pygame.transform.rotate(
                    upright, (-90 if facing not in ('left', 'northwest', 'southwest') else 90)
                    * index / (DEATH_FRAME_COUNT - 1)
                )
                for index in range(DEATH_FRAME_COUNT)
            ]
            sword_direction = flinch_name
            dodge_path = f"assets/images/frames/main_character/dodging/unsheathed/{sword_direction}"
            dodges = [pygame.image.load(f"{dodge_path}/frame_{i}.png").convert_alpha() for i in range(4)]
            factor = target_content_height / max(self._robust_content_height(frame) for frame in dodges)
            self.dodge_frames[facing] = [
                pygame.transform.scale(frame, (max(1, round(frame.get_width() * factor)),
                                               max(1, round(frame.get_height() * factor))))
                for frame in dodges
            ]

        # Named attributes kept for the original four directions so
        # nothing else that references them directly breaks.
        self.idle_right_frames = self.scaled['idle_right']
        self.idle_left_frames = self.scaled['idle_left']
        self.walking_left_frames = self.scaled['walking_left']
        self.walking_right_frames = self.scaled['walking_right']
        self.walking_forward_frames = self.scaled['walking_forward']
        self.walking_backward_frames = self.scaled['walking_backward']

        # New diagonal walking sets.
        self.walking_northeast_frames = self.scaled['walking_northeast']
        self.walking_northwest_frames = self.scaled['walking_northwest']
        self.walking_southeast_frames = self.scaled['walking_southeast']
        self.walking_southwest_frames = self.scaled['walking_southwest']

        # Idle poses that have no dedicated asset are synthesized by
        # freezing on the first frame of that direction's walking set.
        self.idle_forward_frames = self.scaled['idle_forward']
        self.idle_backward_frames = self.scaled['idle_backward']
        self.idle_northeast_frames = self.scaled['idle_northeast']
        self.idle_northwest_frames = self.scaled['idle_northwest']
        self.idle_southeast_frames = self.scaled['idle_southeast']
        self.idle_southwest_frames = self.scaled['idle_southwest']

        self.current_frames = self.idle_right_frames
        self.pos_x, self.pos_y = map_width // 2, map_height // 2
        self.center_x, self.center_y = self.pos_x, self.pos_y
        self.facing = 'right'
        self.current, self.timer = 0, 0
        self.frame_elapsed = 0.0
        self.combat_state = "idle"

    def set_combat_state(self, state):
        """Apply combat animation priority without letting movement cancel it."""
        if state == self.combat_state:
            return
        self.combat_state = state
        self.current = 0
        self.timer = 0
        self.frame_elapsed = 0.0

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
        if self.combat_state == "attacking":
            self.current_frames = self.attack_frames[self.facing]
            self.is_idle = False
            return
        if self.combat_state == "defeated":
            self.current_frames = self.death_frames[self.facing]
            self.is_idle = False
            return
        if self.combat_state == "flinch":
            self.current_frames = self.flinch_frames[self.facing]
            self.is_idle = False
            return
        if self.combat_state == "dodging":
            self.current_frames = self.dodge_frames[self.facing]
            self.is_idle = False
            return
        up = keys[pygame.K_w] or keys[pygame.K_UP]
        down = keys[pygame.K_s] or keys[pygame.K_DOWN]
        left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        right = keys[pygame.K_d] or keys[pygame.K_RIGHT]

            # Cancel true opposites so a+d / w+s net to "not pressed" instead
            # of one arbitrarily winning.
        if up and down:
            up = down = False
        if left and right:
            left = right = False

        # Diagonal combos are checked FIRST. If these ran after the
        # single-direction checks below, a diagonal would never be
        # reached since e.g. "up" alone would already match first.
        if up and right:
            self.current_frames = self.walking_northeast_frames
            self.facing = 'northeast'
            self.is_idle = False
        elif up and left:
            self.current_frames = self.walking_northwest_frames
            self.facing = 'northwest'
            self.is_idle = False
        elif down and right:
            self.current_frames = self.walking_southeast_frames
            self.facing = 'southeast'
            self.is_idle = False
        elif down and left:
            self.current_frames = self.walking_southwest_frames
            self.facing = 'southwest'
            self.is_idle = False
        elif up:
            self.current_frames = self.walking_forward_frames
            self.facing = 'forward'
            self.is_idle = False
        elif down:
            self.current_frames = self.walking_backward_frames
            self.facing = 'backward'
            self.is_idle = False
        elif left:
            self.current_frames = self.walking_left_frames
            self.facing = 'left'
            self.is_idle = False
        elif right:
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
                'northeast': self.idle_northeast_frames,
                'northwest': self.idle_northwest_frames,
                'southeast': self.idle_southeast_frames,
                'southwest': self.idle_southwest_frames,
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

    def draw_frames(self, ZOOM, camera_x, camera_y, dt=1 / 60):
        if self.combat_state == "attacking":
            self.frame_elapsed += dt
            while self.frame_elapsed >= ATTACK_FRAME_DURATION:
                self.frame_elapsed -= ATTACK_FRAME_DURATION
                # Attacks are committed, non-looping actions. Hold the final
                # recovery frame until PlayerCombat releases the state.
                self.current = min(self.current + 1, len(self.current_frames) - 1)
        elif self.combat_state == "defeated":
            self.frame_elapsed += dt
            while self.frame_elapsed >= DEATH_FRAME_DURATION:
                self.frame_elapsed -= DEATH_FRAME_DURATION
                # Never loop: the last frame is the ground pose and remains
                # visible for DEATH_FINAL_HOLD before Game Over.
                self.current = min(self.current + 1, len(self.current_frames) - 1)
        elif self.combat_state == "dodging":
            self.frame_elapsed += dt
            frame_duration = PLAYER_DODGE_DURATION / len(self.current_frames)
            while self.frame_elapsed >= frame_duration:
                self.frame_elapsed -= frame_duration
                self.current = min(self.current + 1, len(self.current_frames) - 1)
        else:
            self.timer += 1
            if self.timer >= 6:
                self.timer = 0
                self.current = (self.current + 1) % len(self.current_frames)

        frame = self.current_frames[self.current]
        draw_x = self.center_x * ZOOM - camera_x - frame.get_width() // 2
        draw_y = self.center_y * ZOOM - camera_y - frame.get_height() // 2

        if self.is_idle and self.facing in ('forward', 'backward'):
            self.idle_bob_timer += 0.06
            draw_y += math.sin(self.idle_bob_timer) * 2  # 2px amplitude float
        else:
            self.idle_bob_timer = 0.0

        self.screen.blit(frame, (draw_x, draw_y))
