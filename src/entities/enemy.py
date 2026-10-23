from pathlib import Path
import heapq
import math

import pygame
from src.data.combat_difficulty import COMBAT_PROFILES

from src.systems.combat import (
    ENEMY_BODY_SIZES, enemy_stats_for_tier, attack_connects, attack_path_blocked,
    move_rect, normalized_toward,
)


class Enemy:
    """Independent combatant with HP, AI, cooldowns, and animation."""

    _frame_cache = {}
    _flying_enemy_ids = frozenset(("manananggal",))
    # (movement folder, attack folder, flinch filename, visible height, canvas)
    _asset_config = {
        "kapre_usikan": ("walking", "attack", "{direction}.png", 180, (250, 220)),
        "white_lady": ("floating", "white_lady_attack", "{direction}.png", 120, (180, 144)),
        "zombie_aktan": ("walking", "attacking", "{direction}.png", 130, (180, 150)),
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
                 disengage_range=None, return_tolerance=None,
                 combat_scale=1.0, combat_tier=1, is_boss=False):
        self.screen = screen
        self.enemy_id = enemy_id
        self.group_id = group_id
        self.combat_tier = combat_tier
        self.is_boss = is_boss
        self.stats = enemy_stats_for_tier(enemy_id, combat_tier, is_boss=is_boss)
        self.committed_attacks = COMBAT_PROFILES[combat_tier]['committed_attacks']
        self.combat_scale = max(0.01, float(combat_scale))
        self.spawn = (
            world_x if world_x is not None else map_width // 2 - 100,
            world_y if world_y is not None else map_height // 2,
        )
        self.center_x, self.center_y = map(float, self.spawn)
        self.rect = pygame.Rect(0, 0, *ENEMY_BODY_SIZES[enemy_id])
        self.rect.center = self.spawn
        self.allowed_ground_cells = None
        self.ground_tile_size = 0
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
        self.attack_direction = None
        self.attack_animation = "attack"
        self.attack_count = 0
        self.attack_range = self.stats.attack_range * self.combat_scale
        self.attack_width = max(
            30, max(ENEMY_BODY_SIZES[enemy_id]) + 12
        ) * self.combat_scale
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
        # Patrol labels describe home territory, not an invisible combat wall.
        # A pursuing enemy may cross the label edge within its home leash.
        map_bounds = pygame.Rect(0, 0, map_width, map_height)
        if math.isfinite(self.chase_range):
            margin = min(max(map_width, map_height), max(0, round(self.chase_range)))
            self.chase_bounds = self.zone.inflate(margin * 2, margin * 2).clip(map_bounds)
        else:
            # Training deliberately has no leash; infinity is not a pixel size.
            self.chase_bounds = map_bounds
        self.return_buffer = 28
        self.stuck_time = 0.0
        self.detour_time = 0.0
        self.detour_direction = (0.0, 0.0)
        self._last_position = self.rect.center
        self._resume_state = "chase"
        self.return_path = []
        self.chase_path = []
        self.chase_goal = None
        self.path_retry = 0.0
        # Boss phases may tune these per instance without changing the
        # shared immutable stats used by every enemy of the same species.
        self.movement_speed_multiplier = 1.0
        self.attack_cooldown_multiplier = 1.0
        self.attack_damage_multiplier = 1.0

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
            if self.enemy_id in ("kapre_usikan", "corrupted_core_kapre"):
                paths["ultimate"] = {}
            for direction in ("north", "south", "east", "west"):
                paths["walking"][direction] = self._numbered_frames(
                    root / move_group / direction
                )
                paths["attack"][direction] = self._numbered_frames(
                    root / attack_group / direction
                )
                if "ultimate" in paths:
                    paths["ultimate"][direction] = self._numbered_frames(root / "ultimate" / direction)
                if self.enemy_id == "white_lady":
                    # There is no separate flinch sheet; keep the walking animation intact.
                    paths["flinch"][direction] = paths["attack"][direction][:1]
                    continue
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
                if not paths:
                    raise ValueError(f"Missing enemy animation frames: {group}/{direction}")
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

    @property
    def flies_over_terrain(self):
        """Whether scenery should be excluded from movement blockers."""

        return self.enemy_id in self._flying_enemy_ids

    def update(self, dt, player_rect, collision_rects, map_width, map_height,
               navigation_rects=None):
        self.just_started_attack = False
        if not self.active:
            return 0
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.action_timer = max(0.0, self.action_timer - dt)
        self.path_retry = max(0.0, self.path_retry - dt)
        direction, distance = normalized_toward(self.rect.center, player_rect.center)
        terrain_blockers = (
            navigation_rects if navigation_rects is not None else collision_rects
        )
        path_blocked = attack_path_blocked(
            self.rect, player_rect, terrain_blockers
        )
        # An attack commits to the direction it telegraphed. Tracking the
        # player throughout the wind-up made dodging sideways meaningless.
        if self.state != "attack":
            self._face(direction)
        home_distance = math.dist(self.rect.center, self.spawn)
        # Visible melee range takes precedence over the home leash.

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
            if self.action_timer == 0:
                self.state = "chase"
            return 0

        damage = 0
        if self.state == "attack":
            # Patrol-zone borders are invisible to the player. Once an enemy
            # is close enough to strike, crossing that bookkeeping boundary
            # must not cancel its attack.
            if distance > max(self.disengage_range, self.attack_range):
                self.state = "return"
                self.action_timer = 0.0
                return 0
            elapsed = self.stats.attack_duration - self.action_timer
            if elapsed >= self.stats.attack_duration * 0.52 and not self.attack_connected:
                self.attack_connected = True
                if (distance <= self.attack_range
                        and not path_blocked
                        and attack_connects(
                            self.rect, player_rect, self.facing,
                            reach=self.attack_range,
                            width=self.attack_width,
                            direction=self.attack_direction,
                        )):
                    damage = round(
                        self.stats.attack_damage * self.attack_damage_multiplier
                    )
            if self.action_timer == 0:
                self.state = "chase"
            return damage

        # Do not regenerate harmlessly beside a player who is still in melee.
        if self.state == "return" and distance <= self.attack_range and not path_blocked:
            self.state = "chase"
            self.return_path.clear()

        # Otherwise return home after the player disengages.
        if self.state == "return":
            self.chase_path.clear()
            self.chase_goal = None
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
                self._move(target_direction, self.stats.movement_speed * 0.7, dt,
                           collision_rects, map_width, map_height,
                           allow_detour=False)
            return 0

        if (self.state == "chase" and distance > self.attack_range
                and (home_distance > self.chase_range or distance > self.disengage_range)):
            self.state = "return"
            return 0

        if (distance <= self.attack_range and not path_blocked
                and self.attack_cooldown == 0 and self.state == "chase"):
            self.state = "attack"
            self.attack_count += 1
            self.attack_animation = ("ultimate" if "ultimate" in self.frames
                                     and self.attack_count % 2 == 0 else "attack")
            self.current = 0
            self.animation_timer = 0.0
            self.action_timer = self.stats.attack_duration
            self.attack_cooldown = (
                self.stats.attack_cooldown * self.attack_cooldown_multiplier
            )
            self.attack_connected = False
            # The artwork uses cardinal facings, while a player can stand
            # anywhere around the enemy. Save the exact wind-up direction
            # so diagonal targets can be hit and sideways dodges still work.
            self.attack_direction = direction
            self.just_started_attack = True
        elif self.state == "chase":
            self.state = "chase"
            # Refresh routes while the target moves instead of walking an
            # obsolete path all the way to its old endpoint. Terrain alone
            # drives pathfinding; other enemies remain local movement
            # blockers so a crowd does not repeatedly compute identical
            # detours around itself.
            static_blockers = terrain_blockers
            direct_blocked = any(
                blocker.clipline(self.rect.center, player_rect.center)
                for blocker in static_blockers
            )
            target_moved = (
                self.chase_goal is None
                or math.dist(self.chase_goal, player_rect.center) > 32
            )
            if not direct_blocked:
                self.chase_path.clear()
                self.chase_goal = None
            elif self.path_retry == 0 and (
                    not self.chase_path or target_moved):
                self.chase_path = self._find_path_to(
                    player_rect.center, static_blockers,
                    map_width, map_height, self.chase_bounds,
                )
                self.chase_goal = player_rect.center
                self.path_retry = 0.45
            while (self.chase_path
                   and math.dist(self.rect.center, self.chase_path[0]) <= 4):
                self.chase_path.pop(0)
            move_direction = direction
            if self.chase_path:
                move_direction, _ = normalized_toward(
                    self.rect.center, self.chase_path[0]
                )
            became_stuck = self._move(
                move_direction,
                self.stats.movement_speed * self.movement_speed_multiplier, dt,
                collision_rects, map_width, map_height,
                movement_bounds=self.chase_bounds,
            )
            if became_stuck and self.path_retry == 0:
                self.chase_path = self._find_path_to(
                    player_rect.center, static_blockers,
                    map_width, map_height, self.chase_bounds,
                )
                self.chase_goal = player_rect.center
                self.path_retry = 0.75
        elif distance <= self.detection_range and not path_blocked:
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
        before_x, before_y = self.x, self.y
        frame_scale = max(0.0, dt) * 60.0
        dx, dy = direction[0] * speed * frame_scale, direction[1] * speed * frame_scale
        self.x, self.y = move_rect(self.rect, self.x, self.y, dx, dy, blockers, bounds)
        # Collision resolution can snap an overlapping body to a blocker's
        # far edge (especially when a phase summons a crowd). Never accept
        # that as movement, or leave the body embedded in another wall.
        if (not self._body_on_allowed_ground(self.rect)
                or self.rect.collidelist(blockers) != -1
                or math.dist(before, self.rect.center) > math.hypot(dx, dy) + 2):
            self.rect.center = before
            self.x, self.y = before_x, before_y

        moved = math.dist(before, self.rect.center)
        trying = abs(dx) + abs(dy) > 0.01
        self.stuck_time = self.stuck_time + dt if trying and moved < 0.25 else 0.0
        became_stuck = allow_detour and self.stuck_time >= 0.35
        if became_stuck:
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
        return became_stuck

    def _body_on_allowed_ground(self, rect):
        """Keep every enemy body fully on the authored dirt battlefield."""
        allowed_cells = getattr(self, "allowed_ground_cells", None)
        tile_size = getattr(self, "ground_tile_size", 0)
        if allowed_cells is None or not tile_size:
            return True
        points = (
            rect.center,
            (rect.left + 2, rect.top + 2),
            (rect.right - 3, rect.top + 2),
            (rect.left + 2, rect.bottom - 3),
            (rect.right - 3, rect.bottom - 3),
        )
        size = tile_size
        return all(
            (x // size, y // size) in allowed_cells
            for x, y in points
        )

    def _find_return_path(self, blockers, map_width, map_height):
        """Build deterministic collision-safe waypoints back to spawn."""
        return self._find_path_to(
            self.spawn, blockers, map_width, map_height,
            pygame.Rect(0, 0, map_width, map_height),
        )

    def _find_path_to(self, target, blockers, map_width, map_height,
                      movement_bounds=None):
        """Build deterministic body-safe waypoints to ``target``.

        Chase calls this only after direct pursuit stalls, so ordinary open
        ground remains cheap while a large Tikbalang can route around trees
        instead of oscillating inside the same dead end.
        """
        step = 8
        start = (round(self.rect.centerx / step), round(self.rect.centery / step))
        goal = (round(target[0] / step), round(target[1] / step))
        bounds = (
            pygame.Rect(movement_bounds)
            if movement_bounds is not None
            else pygame.Rect(0, 0, map_width, map_height)
        )
        margin = 24
        min_x = max(math.ceil(bounds.left / step),
                    min(start[0], goal[0]) - margin)
        max_x = min(math.floor(bounds.right / step),
                    max(start[0], goal[0]) + margin)
        min_y = max(math.ceil(bounds.top / step),
                    min(start[1], goal[1]) - margin)
        max_y = min(math.floor(bounds.bottom / step),
                    max(start[1], goal[1]) + margin)

        def walkable(node):
            if node in (start, goal):
                return True
            probe = pygame.Rect(0, 0, self.rect.width, self.rect.height)
            probe.center = (node[0] * step, node[1] * step)
            return (bounds.contains(probe)
                    and probe.collidelist(blockers) == -1
                    and self._body_on_allowed_ground(probe))

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
        nodes.append(tuple(target))
        return nodes

    def receive_damage(self, amount):
        if not self.active or self.state == "defeated":
            return False
        self.hp = max(0, self.hp - max(0, amount))
        # Later-stage strikes keep their telegraphed direction and timing
        # when hit. Damage still lands; a lethal hit always stops the strike.
        if self.hp > 0 and self.state == "attack" and self.committed_attacks:
            return True
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
        self.attack_count = 0
        self.attack_animation = "attack"
        self.attack_direction = None
        self.stuck_time = 0.0
        self.detour_time = 0.0
        self.return_path.clear()
        self.chase_path.clear()
        self.chase_goal = None
        self.path_retry = 0.0
        self.movement_speed_multiplier = 1.0
        self.attack_cooldown_multiplier = 1.0
        self.attack_damage_multiplier = 1.0

    def _face(self, direction):
        dx, dy = direction
        if abs(dx) > abs(dy):
            self.facing = "east" if dx > 0 else "west"
        elif dy:
            self.facing = "south" if dy > 0 else "north"

    def draw_frames(self, ZOOM, camera_x, camera_y, sprite_scale=1):
        if not self.active:
            return
        group = self.attack_animation if self.state == "attack" else "flinch" if self.state in ("flinch", "defeated") else "walking"
        frames = self.frames[group][self.facing]
        if self.state == "attack":
            # Play the full authored sequence once over the attack duration.
            # Rendering may run at any FPS and must not advance combat time.
            progress = 1.0 - self.action_timer / self.stats.attack_duration
            self.current = min(len(frames) - 1, max(0, int(progress * len(frames))))
        elif self.state in ("idle", "alert"):
            self.current = 0
            self.animation_timer = 0
        else:
            self.animation_timer += 1
            if self.animation_timer >= 6:
                self.animation_timer = 0
                self.current = (self.current + 1) % len(frames)
        frame = frames[self.current % len(frames)]
        if sprite_scale != 1:
            frame = pygame.transform.scale(frame, (round(frame.get_width() * sprite_scale), round(frame.get_height() * sprite_scale)))
        draw_x = self.rect.centerx * ZOOM - camera_x - frame.get_width() // 2
        # The normalized canvas keeps visible feet three pixels above its
        # bottom; attach that baseline to the collision rect's bottom.
        draw_y = self.rect.bottom * ZOOM - camera_y - (frame.get_height() - 3 * sprite_scale)
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
            if (self.committed_attacks and self.state == "attack"
                    and self.action_timer > self.stats.attack_duration * .48):
                # A shape plus exclamation mark explains a committed wind-up
                # without depending on colour or an additional art asset.
                x, y = round(bar.centerx), round(bar.y - 12)
                pygame.draw.polygon(self.screen, (255, 210, 105),
                                    ((x, y - 9), (x - 9, y + 7), (x + 9, y + 7)))
                pygame.draw.line(self.screen, (26, 19, 6), (x, y - 4), (x, y + 1), 2)
                pygame.draw.circle(self.screen, (26, 19, 6), (x, y + 4), 1)
