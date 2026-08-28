"""Shared combat rules and geometry; rendering stays with the entities/HUD."""

from dataclasses import dataclass
import math
import pygame


PLAYER_MAX_HP = 100
ATTACK_FRAME_COUNT = 9
ATTACK_FRAME_DURATION = 0.055
PLAYER_ATTACK_DURATION = ATTACK_FRAME_COUNT * ATTACK_FRAME_DURATION
# Cooldown is measured from attack start, leaving a short lockout after the
# complete wind-up/swing/recovery animation has finished.
PLAYER_ATTACK_COOLDOWN = 0.65
# Authored frames 4-5 are the visible blade-contact portion of the swing.
PLAYER_ATTACK_ACTIVE_START = 4 * ATTACK_FRAME_DURATION
PLAYER_ATTACK_ACTIVE_END = 6 * ATTACK_FRAME_DURATION
PLAYER_INVULNERABILITY = 0.65
PLAYER_DODGE_SPEED = 8.0
PLAYER_DODGE_DURATION = 0.20
PLAYER_DODGE_COOLDOWN = 0.85
PLAYER_DODGE_INVULNERABILITY = 0.24
DEATH_FRAME_COUNT = 7
DEATH_FRAME_DURATION = 0.14
DEATH_FINAL_HOLD = 0.65
PLAYER_DEFEAT_DURATION = (DEATH_FRAME_COUNT - 1) * DEATH_FRAME_DURATION + DEATH_FINAL_HOLD
PLAYER_ATTACK_REACH = 34
PLAYER_ATTACK_WIDTH = 34
BASE_SWORD_DAMAGE = 20
COMBAT_DEBUG = False
DEBUG_ENEMY_AI = False


@dataclass(frozen=True)
class EnemyStats:
    max_hp: int
    attack_damage: int
    movement_speed: float
    attack_range: float
    detection_range: float
    awareness_radius: float
    disengage_range: float
    max_chase_distance: float
    assist_range: float
    return_tolerance: float
    attack_cooldown: float
    attack_duration: float
    reward_time: int


ENEMY_STATS = {
    # Ranges are unscaled world pixels (the map uses 16-pixel tiles).
    "duwende_mandurug": EnemyStats(60, 8, 1.15, 32, 144, 96, 220, 280, 120, 4, 1.15, 0.52, 10),
    "tiyanak_sinta": EnemyStats(40, 6, 1.10, 30, 160, 96, 240, 300, 120, 4, 1.30, 0.52, 6),
    "manananggal": EnemyStats(70, 10, 1.25, 34, 200, 112, 290, 360, 150, 4, 1.15, 0.55, 10),
    "tikbalang": EnemyStats(110, 14, 1.05, 42, 176, 112, 270, 330, 140, 5, 1.25, 0.60, 16),
}

# Feet-level combat bodies, deliberately smaller than the rendered artwork.
# These drive movement collision and sword hurtbox overlap, not sprite bounds.
ENEMY_BODY_SIZES = {
    "duwende_mandurug": (26, 26),
    "tiyanak_sinta": (20, 18),
    "manananggal": (28, 28),
    "tikbalang": (36, 38),
}


FACING_VECTORS = {
    "right": (1, 0), "left": (-1, 0),
    "forward": (0, -1), "backward": (0, 1),
    "northeast": (0.7071, -0.7071), "northwest": (-0.7071, -0.7071),
    "southeast": (0.7071, 0.7071), "southwest": (-0.7071, 0.7071),
}


class PlayerCombat:
    def __init__(self):
        self.max_hp = PLAYER_MAX_HP
        self.hp = self.max_hp
        self.attack_cooldown = 0.0
        self.dodge_cooldown = 0.0
        self.invulnerable = 0.0
        self.action_time = 0.0
        self.state = "idle"
        self.attack_id = 0

    @property
    def locked(self):
        return self.state in ("attacking", "dodging", "flinch", "defeated")

    @property
    def attack_active(self):
        elapsed = PLAYER_ATTACK_DURATION - self.action_time
        return self.state == "attacking" and PLAYER_ATTACK_ACTIVE_START <= elapsed <= PLAYER_ATTACK_ACTIVE_END

    def update(self, dt):
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.dodge_cooldown = max(0.0, self.dodge_cooldown - dt)
        self.invulnerable = max(0.0, self.invulnerable - dt)
        if self.action_time > 0:
            self.action_time = max(0.0, self.action_time - dt)
            if self.action_time == 0 and self.state != "defeated":
                self.state = "idle"

    def start_attack(self):
        if self.attack_cooldown or self.locked:
            return False
        self.state = "attacking"
        self.action_time = PLAYER_ATTACK_DURATION
        self.attack_cooldown = PLAYER_ATTACK_COOLDOWN
        self.attack_id += 1
        return True

    def start_dodge(self):
        if self.dodge_cooldown or self.locked:
            return False
        self.state = "dodging"
        self.action_time = PLAYER_DODGE_DURATION
        self.dodge_cooldown = PLAYER_DODGE_COOLDOWN
        self.invulnerable = max(self.invulnerable, PLAYER_DODGE_INVULNERABILITY)
        return True

    def take_damage(self, amount):
        if self.invulnerable or self.state == "defeated":
            return False
        self.hp = max(0, self.hp - max(0, amount))
        if self.hp == 0:
            self.state = "defeated"
            # Hold the authored defeated/flinch pose long enough to read as a
            # complete death action before game.py opens the Game Over modal.
            self.action_time = PLAYER_DEFEAT_DURATION
        else:
            self.state = "flinch"
            self.action_time = 0.22
            self.invulnerable = PLAYER_INVULNERABILITY
        return True

    def reset(self):
        self.hp = self.max_hp
        self.state = "idle"
        self.action_time = 0
        self.invulnerable = 0


def attack_hitbox(player_rect, facing):
    """Continuous sword sweep from the player's body to the blade tip.

    Including the origin prevents a close enemy from becoming unhittable if
    its AI reaches or slightly crosses the player's center during a swing.
    """
    dx, dy = FACING_VECTORS.get(facing, (1, 0))
    center = (
        round(player_rect.centerx + dx * PLAYER_ATTACK_REACH),
        round(player_rect.centery + dy * PLAYER_ATTACK_REACH),
    )
    blade_tip = pygame.Rect(0, 0, PLAYER_ATTACK_WIDTH, PLAYER_ATTACK_WIDTH)
    blade_tip.center = center
    blade_origin = pygame.Rect(0, 0, PLAYER_ATTACK_WIDTH, PLAYER_ATTACK_WIDTH)
    blade_origin.center = player_rect.center
    return blade_origin.union(blade_tip)


def attack_path_blocked(player_rect, enemy_rect, blockers):
    """True only when a solid wall crosses the actual sword-to-target line."""
    start, end = player_rect.center, enemy_rect.center
    return any(wall.clipline(start, end) for wall in blockers)


def selected_weapon_damage(inventory):
    item = inventory.get_selected_item()
    if item is not None and getattr(item, "kind", None) == "weapon":
        return max(1, int(getattr(item, "damage", BASE_SWORD_DAMAGE)))
    return 0


def move_rect(rect, x, y, dx, dy, blockers, bounds):
    """Collision-safe axis-separated movement used by dodge and enemy AI."""
    x += dx
    rect.x = round(x)
    for wall in blockers:
        if rect.colliderect(wall):
            rect.right = wall.left if dx > 0 else rect.right
            rect.left = wall.right if dx < 0 else rect.left
            x = float(rect.x)
    y += dy
    rect.y = round(y)
    for wall in blockers:
        if rect.colliderect(wall):
            rect.bottom = wall.top if dy > 0 else rect.bottom
            rect.top = wall.bottom if dy < 0 else rect.top
            y = float(rect.y)
    rect.clamp_ip(bounds)
    return float(rect.x), float(rect.y)


def normalized_toward(source, target):
    dx, dy = target[0] - source[0], target[1] - source[1]
    distance = math.hypot(dx, dy)
    return ((dx / distance, dy / distance), distance) if distance else ((0, 0), 0)
