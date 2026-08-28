from pathlib import Path
import heapq
import math

import pygame

from src.systems.combat import (
    ENEMY_BODY_SIZES, ENEMY_STATS, move_rect, normalized_toward,
)


class Enemy:
    """Independent combatant with HP, AI, cooldowns, and animation."""

    _frame_cache = {}
    # (movement folder, attack folder, flinch filename, visible height, canvas)
    _asset_config = {
        "tiyanak_sinta": ("walking", "attacking", "{direction}.png", 40, (72, 50)),
        "manananggal": ("flying", "attacking", "manananggal_{direction}.png", 76, (110, 88)),
        "tikbalang": ("walking", "attacking", "{direction}.png", 88, (124, 98)),
        "corrupted_core_kapre": (
            # More than twice the 88px Tikbalang silhouette: this is meant
            # to read as a colossal boss even before its health bar appears.
            # The combat body remains smaller than this artwork so the boss
            # looks massive without snagging on scenery or feeling unfair.
            "walking", "attack", "{direction}.png", 210, (270, 228)
        ),
    }
    _asset_sources = {
        "corrupted_core_kapre": "kapre_usikan",
    }

    def __init__(self, screen, map_width, map_height, world_x=None, world_y=None,
                 enemy_id="duwende_mandurug", zone_size=(360, 300),
                 detection_range=None, chase_range=None, zone_rect=None,
                 zone_name="Wilderness", group_id="ungrouped",
                 disengage_range=None, return_tolerance=None):
        self.screen = screen
        self.enemy_id = enemy_id
        self.group_id = group_id
        self.stats = ENEMY_STATS[enemy_id]
        self.spawn = (
            world_x if world_x is not None else map_width // 2 - 100,
            world_y if world_y is not None else map_height // 2,
        )
        self.center_x, self.center_y = map(float, self.spawn)
        self.rect = pygame.Rect(0, 0, *ENEMY_BODY_SIZES[enemy_id])
        self.rect.center = self.spawn
        self.x, self.y = float(self.rect.x), float(self.rect.y)
        if enemy_id not in self._frame_cache:
            self._frame_cache[enemy_id] = self._load_frames()
        self.frames = self._frame_cache[enemy_id]
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
        self.just_started_attack = False
        self.detection_range = detection_range or self.stats.detection_range
        self.awareness_radius = self.stats.awareness_radius
        self.disengage_range = disengage_range or self.stats.disengage_range
        self.chase_range = chase_range or self.stats.max_chase_distance
        self.assist_range = self.stats.assist_range
        self.return_tolerance = return_tolerance or self.stats.return_tolerance
        self.zone_name = zone_name
        if zone_rect:
            self.zone = pygame.Rect(zone_rect)
        else:
            self.zone = pygame.Rect(0, 0, *zone_size)
            self.zone.center = self.spawn
            self.zone.clamp_ip(pygame.Rect(0, 0, map_width, map_height))
        self.return_buffer = 28
        self.stuck_time = 0.0
        self.detour_time = 0.0
        self.detour_direction = (0.0, 0.0)
        self._last_position = self.rect.center
        self._resume_state = "chase"
        self.return_path = []

    def _load_frames(self):
        result = {"walking": {}, "attack": {}, "flinch": {}}
        if self.enemy_id in self._asset_config:
            move_group, attack_group, flinch_name, target_height, canvas = (
                self._asset_config[self.enemy_id]
            )
            root = Path("assets/images/frames") / self._asset_sources.get(
                self.enemy_id, self.enemy_id
            )
            paths = {"walking": {}, "attack": {}, "flinch": {}}
            for direction in ("north", "south", "east", "west"):
                paths["walking"][direction] = self._numbered_frames(
                    root / move_group / direction
                )
                paths["attack"][direction] = self._numbered_frames(
                    root / attack_group / direction
                )
                paths["flinch"][direction] = [
                    str(root / "flinch" / flinch_name.format(direction=direction))
                ]
            return self._normalized_animations(paths, target_height, canvas)

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
    def _numbered_frames(folder):
        return [str(path) for path in sorted(
            folder.glob("frame_*.png"),
            key=lambda path: int(path.stem.rsplit("_", 1)[1]),
        )]

    @classmethod
    def _normalized_animations(cls, animation_paths, target_height, canvas_size):
        """Use one scale for every state/direction belonging to an enemy.

        Shorter crouched or recoiling poses may occupy less height naturally,
        but changing animation sets never applies a different character scale.
        """
        loaded = {}
        tallest = 1
        for group, directions in animation_paths.items():
            loaded[group] = {}
            for direction, paths in directions.items():
                originals = [pygame.image.load(path).convert_alpha() for path in paths]
                loaded[group][direction] = originals
                tallest = max(tallest, *(frame.get_bounding_rect(min_alpha=8).height
                                         for frame in originals))

        scale = target_height / tallest
        return {
            group: {
                direction: cls._normalized_set(
                    frames, canvas_size=canvas_size, fixed_scale=scale
                )
                for direction, frames in directions.items()
            }
            for group, directions in loaded.items()
        }

    @staticmethod
    def _normalized_set(paths, target_content_height=62, canvas_size=(78, 70),
                        fixed_scale=None):
        """Scale a whole animation uniformly and bottom-anchor every frame.

        A direction gets one scale derived from its tallest visible frame;
        individual frame canvas dimensions never influence their own scale.
        """
        originals = [
            path if isinstance(path, pygame.Surface)
            else pygame.image.load(path).convert_alpha()
            for path in paths
        ]
        bounds = [frame.get_bounding_rect(min_alpha=8) for frame in originals]
        tallest = max((bound.height for bound in bounds), default=1)
        scale = fixed_scale if fixed_scale is not None else target_content_height / max(1, tallest)
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

    def update(self, dt, player_rect, collision_rects, map_width, map_height,
               navigation_rects=None):
        self.just_started_attack = False
        if not self.active:
            return 0
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.action_timer = max(0.0, self.action_timer - dt)
        direction, distance = normalized_toward(self.rect.center, player_rect.center)
        self._face(direction)
        home_distance = math.dist(self.rect.center, self.spawn)
        # Encounters own a specific part of the map. A player must enter that
        # authored area before its enemies engage, and chase movement below is
        # clamped to the same boundary so enemies cannot follow indefinitely.
        player_in_chase_zone = self.zone.collidepoint(player_rect.center)

        if self.state == "defeated":
            self.defeat_timer -= dt
            if self.defeat_timer <= 0:
                self.active = False
            return 0
        if self.state == "flinch":
            if self.action_timer == 0:
                self.state = self._resume_state
            return 0
        if self.state == "alert":
            if not player_in_chase_zone:
                self.state = "return"
            elif self.action_timer == 0:
                self.state = "chase"
            return 0

        damage = 0
        if self.state == "attack":
            if (not player_in_chase_zone or home_distance > self.chase_range
                    or distance > self.disengage_range):
                self.state = "return"
                self.action_timer = 0.0
                return 0
            elapsed = self.stats.attack_duration - self.action_timer
            if elapsed >= self.stats.attack_duration * 0.52 and not self.attack_connected:
                self.attack_connected = True
                if distance <= self.stats.attack_range + 12:
                    damage = self.stats.attack_damage
            if self.action_timer == 0:
                self.state = "chase"
            return damage

        # RETURN is deliberately non-interruptible: an enemy must get home
        # before it can detect the player again.
        if self.state == "return":
            self.hp = min(self.stats.max_hp, self.hp + self.stats.max_hp * 0.5 * dt)
            home_direction, home_distance = normalized_toward(self.rect.center, self.spawn)
            if home_distance <= self.return_tolerance:
                self.state = "idle"
                self.hp = self.stats.max_hp
                self.stuck_time = 0.0
                self.return_path.clear()
            else:
                if not self.return_path:
                    self.detour_time = 0.0
                    self.return_path = self._find_return_path(
                        navigation_rects if navigation_rects is not None else collision_rects,
                        map_width, map_height,
                    )
                target = self.return_path[0] if self.return_path else self.spawn
                target_direction, target_distance = normalized_toward(
                    self.rect.center, target
                )
                # Grid waypoints sit only eight pixels apart. Reaching each
                # closely prevents cutting a corner with a large body rect.
                if self.return_path and target_distance <= 2:
                    self.return_path.pop(0)
                    target = self.return_path[0] if self.return_path else self.spawn
                    target_direction, _ = normalized_toward(self.rect.center, target)
                return_blockers = (
                    navigation_rects if navigation_rects is not None else collision_rects
                )
                self._move(target_direction, self.stats.movement_speed * 0.7, dt,
                           return_blockers, map_width, map_height,
                           allow_detour=False)
            return 0

        if self.state == "chase" and (not player_in_chase_zone
                or home_distance > self.chase_range
                or distance > self.disengage_range):
            self.state = "return"
            return 0

        if distance <= self.stats.attack_range and self.attack_cooldown == 0 and self.state == "chase":
            self.state = "attack"
            self.action_timer = self.stats.attack_duration
            self.attack_cooldown = self.stats.attack_cooldown
            self.attack_connected = False
            self.just_started_attack = True
        elif self.state == "chase" and player_in_chase_zone:
            self.state = "chase"
            self._move(direction, self.stats.movement_speed, dt,
                       collision_rects, map_width, map_height,
                       movement_bounds=self.zone)
        elif distance <= self.detection_range and player_in_chase_zone:
            # A short reaction makes detection readable and prevents an enemy
            # outside melee range from attacking on the acquisition frame.
            self.state = "alert"
            self.action_timer = 0.18
        else:
            home_direction, home_distance = normalized_toward(self.rect.center, self.spawn)
            if home_distance > 4:
                self.state = "return"
            else:
                self.state = "idle"
        return damage

    def _move(self, direction, speed, dt, blockers, map_width, map_height,
              allow_detour=True, movement_bounds=None):
        """Move collision-safely, slide along corners, and escape dead ends."""
        bounds = (pygame.Rect(movement_bounds) if movement_bounds is not None
                  else pygame.Rect(0, 0, map_width, map_height))
        if allow_detour and self.detour_time > 0:
            self.detour_time = max(0.0, self.detour_time - dt)
            direction = self.detour_direction
        self._face(direction)
        before = self.rect.center
        dx, dy = direction[0] * speed, direction[1] * speed
        self.x, self.y = move_rect(self.rect, self.x, self.y, dx, dy, blockers, bounds)

        moved = math.dist(before, self.rect.center)
        trying = abs(dx) + abs(dy) > 0.01
        self.stuck_time = self.stuck_time + dt if trying and moved < 0.25 else 0.0
        if allow_detour and self.stuck_time >= 0.35:
            # Perpendicular choices preserve collision and create a short
            # wall-following detour instead of teleporting through geometry.
            choices = [(-direction[1], direction[0]), (direction[1], -direction[0])]
            choices.sort(key=lambda candidate: math.dist(
                (self.rect.centerx + candidate[0] * speed * 8,
                 self.rect.centery + candidate[1] * speed * 8),
                self.spawn,
            ))
            for candidate in choices:
                probe = self.rect.copy()
                move_rect(probe, float(probe.x), float(probe.y),
                          candidate[0] * speed * 2, candidate[1] * speed * 2,
                          blockers, bounds)
                if probe.center != self.rect.center:
                    self.detour_direction = candidate
                    self.detour_time = 0.45
                    break
            self.stuck_time = 0.0
        self.center_x, self.center_y = self.rect.center

    def _find_return_path(self, blockers, map_width, map_height):
        """Build deterministic collision-safe waypoints back to spawn."""
        step = 8
        start = (round(self.rect.centerx / step), round(self.rect.centery / step))
        goal = (round(self.spawn[0] / step), round(self.spawn[1] / step))
        margin = 24
        min_x = max(0, min(start[0], goal[0]) - margin)
        max_x = min(map_width // step, max(start[0], goal[0]) + margin)
        min_y = max(0, min(start[1], goal[1]) - margin)
        max_y = min(map_height // step, max(start[1], goal[1]) + margin)

        def walkable(node):
            if node in (start, goal):
                return True
            probe = pygame.Rect(0, 0, self.rect.width, self.rect.height)
            probe.center = (node[0] * step, node[1] * step)
            return (0 <= probe.left and probe.right <= map_width
                    and 0 <= probe.top and probe.bottom <= map_height
                    and probe.collidelist(blockers) == -1)

        frontier = [(0, start)]
        came_from = {start: None}
        costs = {start: 0}
        while frontier:
            _priority, current = heapq.heappop(frontier)
            if current == goal:
                break
            for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                nxt = (current[0] + dx, current[1] + dy)
                if not (min_x <= nxt[0] <= max_x and min_y <= nxt[1] <= max_y):
                    continue
                if not walkable(nxt):
                    continue
                cost = costs[current] + 1
                if cost < costs.get(nxt, 1_000_000):
                    costs[nxt] = cost
                    came_from[nxt] = current
                    heuristic = abs(goal[0] - nxt[0]) + abs(goal[1] - nxt[1])
                    heapq.heappush(frontier, (cost + heuristic, nxt))

        if goal not in came_from:
            return []
        nodes = []
        current = goal
        while current != start:
            nodes.append((current[0] * step, current[1] * step))
            current = came_from[current]
        nodes.reverse()
        nodes.append(self.spawn)
        return nodes

    def receive_damage(self, amount):
        if not self.active or self.state == "defeated":
            return False
        self.hp = max(0, self.hp - max(0, amount))
        self.current = 0
        if self.hp == 0:
            self.state = "defeated"
            self.defeat_timer = 0.55
        else:
            self._resume_state = "return" if self.state == "return" else "chase"
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
        self.stuck_time = 0.0
        self.detour_time = 0.0
        self.return_path.clear()

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
        if self.state in ("idle", "alert"):
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
