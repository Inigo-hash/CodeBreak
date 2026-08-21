import pygame

from src.systems.combat import ENEMY_STATS, move_rect, normalized_toward


class Enemy:
    """Independent Duwende combatant with HP, AI, cooldowns, and animation."""

    def __init__(self, screen, map_width, map_height, world_x=None, world_y=None,
                 enemy_id="duwende_mandurug"):
        self.screen = screen
        self.enemy_id = enemy_id
        self.stats = ENEMY_STATS[enemy_id]
        self.spawn = (
            world_x if world_x is not None else map_width // 2 - 100,
            world_y if world_y is not None else map_height // 2,
        )
        self.center_x, self.center_y = map(float, self.spawn)
        self.rect = pygame.Rect(0, 0, 26, 26)
        self.rect.center = self.spawn
        self.x, self.y = float(self.rect.x), float(self.rect.y)
        self.frames = self._load_frames()
        self.state = "idle"
        self.facing = "south"
        self.current = 0
        self.animation_timer = 0.0
        self.action_timer = 0.0
        self.attack_cooldown = 0.0
        self.attack_connected = False
        self.hp = self.stats.max_hp
        self.active = True
        self.defeat_timer = 0.0

    def _load_frames(self):
        result = {"walking": {}, "attack": {}, "flinch": {}}
        # In this authored set "forward" shows the Duwende's back (moving
        # away/up-screen), while "backward" shows its face (moving down).
        direction_paths = {"north": "forward", "south": "backward", "east": "right", "west": "left"}
        for direction, asset in direction_paths.items():
            walk_path = f"assets/images/frames/duwende_mandurug/walking/walking_{asset}"
            attack_path = f"assets/images/frames/duwende_mandurug/attack/attack_{asset}"
            result["walking"][direction] = self._normalized_set(
                [f"{walk_path}/frame_{i}.png" for i in range(8)]
            )
            result["attack"][direction] = self._normalized_set(
                [f"{attack_path}/frame_{i}.png" for i in range(8)]
            )
            result["flinch"][direction] = self._normalized_set([
                f"assets/images/frames/duwende_mandurug/flinch/{direction}.png"
            ])
        return result

    @staticmethod
    def _normalized_set(paths, target_content_height=62, canvas_size=(78, 70)):
        """Scale a whole animation uniformly and bottom-anchor every frame.

        A direction gets one scale derived from its tallest visible frame;
        individual frame canvas dimensions never influence their own scale.
        """
        originals = [pygame.image.load(path).convert_alpha() for path in paths]
        bounds = [frame.get_bounding_rect(min_alpha=8) for frame in originals]
        tallest = max((bound.height for bound in bounds), default=1)
        scale = target_content_height / max(1, tallest)
        normalized = []

        for frame, bound in zip(originals, bounds):
            scaled = pygame.transform.scale(
                frame,
                (max(1, round(frame.get_width() * scale)),
                 max(1, round(frame.get_height() * scale))),
            )
            scaled_bound = scaled.get_bounding_rect(min_alpha=8)
            visible = scaled.subsurface(scaled_bound).copy()
            canvas = pygame.Surface(canvas_size, pygame.SRCALPHA)
            # All feet share this baseline; width changes expand equally left
            # and right instead of shifting the enemy's world position.
            destination = visible.get_rect(
                midbottom=(canvas_size[0] // 2, canvas_size[1] - 3)
            )
            canvas.blit(visible, destination)
            normalized.append(canvas)

        return normalized

    @property
    def engaged(self):
        return self.active and self.state in ("chase", "attack", "flinch")

    def update(self, dt, player_rect, collision_rects, map_width, map_height):
        if not self.active:
            return 0
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.action_timer = max(0.0, self.action_timer - dt)
        direction, distance = normalized_toward(self.rect.center, player_rect.center)
        self._face(direction)

        if self.state == "defeated":
            self.defeat_timer -= dt
            if self.defeat_timer <= 0:
                self.active = False
            return 0
        if self.state == "flinch":
            if self.action_timer == 0:
                self.state = "chase"
            return 0

        damage = 0
        if self.state == "attack":
            elapsed = self.stats.attack_duration - self.action_timer
            if elapsed >= self.stats.attack_duration * 0.52 and not self.attack_connected:
                self.attack_connected = True
                if distance <= self.stats.attack_range + 12:
                    damage = self.stats.attack_damage
            if self.action_timer == 0:
                self.state = "chase"
            return damage

        if distance <= self.stats.attack_range and self.attack_cooldown == 0:
            self.state = "attack"
            self.action_timer = self.stats.attack_duration
            self.attack_cooldown = self.stats.attack_cooldown
            self.attack_connected = False
        elif distance <= self.stats.detection_range:
            self.state = "chase"
            speed = self.stats.movement_speed
            self.x, self.y = move_rect(
                self.rect, self.x, self.y, direction[0] * speed,
                direction[1] * speed, collision_rects,
                pygame.Rect(0, 0, map_width, map_height),
            )
            self.center_x, self.center_y = self.rect.center
        else:
            home_direction, home_distance = normalized_toward(self.rect.center, self.spawn)
            if home_distance > 4:
                self.state = "return"
                self._face(home_direction)
                self.x, self.y = move_rect(
                    self.rect, self.x, self.y,
                    home_direction[0] * self.stats.movement_speed * 0.7,
                    home_direction[1] * self.stats.movement_speed * 0.7,
                    collision_rects, pygame.Rect(0, 0, map_width, map_height),
                )
                self.center_x, self.center_y = self.rect.center
            else:
                self.state = "idle"
        return damage

    def receive_damage(self, amount):
        if not self.active or self.state == "defeated":
            return False
        self.hp = max(0, self.hp - max(0, amount))
        self.current = 0
        if self.hp == 0:
            self.state = "defeated"
            self.defeat_timer = 0.55
        else:
            self.state = "flinch"
            self.action_timer = 0.20
        return True

    def reset(self):
        self.hp = self.stats.max_hp
        self.active = True
        self.state = "idle"
        self.rect.center = self.spawn
        self.x, self.y = float(self.rect.x), float(self.rect.y)
        self.center_x, self.center_y = self.rect.center
        self.attack_cooldown = 0

    def _face(self, direction):
        dx, dy = direction
        if abs(dx) > abs(dy):
            self.facing = "east" if dx > 0 else "west"
        elif dy:
            self.facing = "south" if dy > 0 else "north"

    def draw_frames(self, ZOOM, camera_x, camera_y):
        if not self.active:
            return
        group = "attack" if self.state == "attack" else "flinch" if self.state in ("flinch", "defeated") else "walking"
        frames = self.frames[group][self.facing]
        if self.state == "idle":
            self.current = 0
            self.animation_timer = 0
        else:
            self.animation_timer += 1
            if self.animation_timer >= 6:
                self.animation_timer = 0
                self.current = (self.current + 1) % len(frames)
        frame = frames[self.current % len(frames)]
        draw_x = self.rect.centerx * ZOOM - camera_x - frame.get_width() // 2
        # The normalized canvas keeps visible feet three pixels above its
        # bottom; attach that baseline to the collision rect's bottom.
        draw_y = self.rect.bottom * ZOOM - camera_y - (frame.get_height() - 3)
        if self.state == "defeated":
            frame = frame.copy()
            frame.set_alpha(max(0, min(255, round(255 * self.defeat_timer / 0.55))))
        self.screen.blit(frame, (draw_x, draw_y))
        if self.engaged:
            bar = pygame.Rect(draw_x, draw_y - 8, max(32, frame.get_width()), 5)
            pygame.draw.rect(self.screen, (20, 20, 24), bar)
            fill = bar.copy()
            fill.width = round(bar.width * self.hp / self.stats.max_hp)
            pygame.draw.rect(self.screen, (185, 42, 48), fill)
            pygame.draw.rect(self.screen, (90, 94, 110), bar, 1)
