"""Shared combat rules and geometry; rendering stays with the entities/HUD."""

from dataclasses import dataclass
import math
import pygame


PLAYER_MAX_HP = 100
PLAYER_MAX_ENERGY = 100
# Energy is the dodge budget: four dodges from full, and a steady trickle
# back so a fight is paced by when the player spends it, not by a cooldown
# alone. Regen is per second and applied continuously, not in 1s ticks.
PLAYER_DODGE_ENERGY_COST = 25
PLAYER_ENERGY_REGEN = 8.0
# Standing in a lit torch's pool restores the dodge budget four times as
# fast: a full dodge back roughly every second and a quarter, which makes
# the lit stretches of path worth retreating to during a night fight.
PLAYER_TORCH_ENERGY_REGEN = 32.0
# The same light closes wounds at the same rate it restores energy: five
# seconds in a pool takes the player from near death back to full. A lit
# stretch of path is therefore a genuine refuge rather than a slow drip,
# and the pressure comes from reaching one rather than from waiting in it.
PLAYER_TORCH_HP_REGEN = 20.0
# Torchlight is recovery space, not armour.  Passive healing starts only
# after the player has avoided damage for a moment, preventing a weak enemy
# from being out-healed while its attack is still connecting.
PLAYER_TORCH_HEAL_DELAY = 2.0
ATTACK_FRAME_COUNT = 9
ATTACK_FRAME_DURATION = 0.055
PLAYER_ATTACK_DURATION = ATTACK_FRAME_COUNT * ATTACK_FRAME_DURATION
# Cooldown is measured from attack start, leaving a short lockout after the
# complete wind-up/swing/recovery animation has finished.
PLAYER_ATTACK_COOLDOWN = 0.65
# Authored frames 4-5 are the visible blade-contact portion of the swing.
PLAYER_ATTACK_ACTIVE_START = 4 * ATTACK_FRAME_DURATION
PLAYER_ATTACK_ACTIVE_END = 6 * ATTACK_FRAME_DURATION
PLAYER_INVULNERABILITY = 0.85
PLAYER_DODGE_SPEED = 8.0
PLAYER_DODGE_DURATION = 0.20
PLAYER_DODGE_COOLDOWN = 0.85
PLAYER_DODGE_INVULNERABILITY = 0.24
DEATH_FRAME_COUNT = 7
DEATH_FRAME_DURATION = 0.14
DEATH_FINAL_HOLD = 0.65
PLAYER_DEFEAT_DURATION = (DEATH_FRAME_COUNT - 1) * DEATH_FRAME_DURATION + DEATH_FINAL_HOLD
# Combat reach is authored at the same 1x pixel scale as the character art.
# The campaign map is rendered at 2x, so callers pass ``scale=1 / ZOOM``;
# the 1x tutorial can use the defaults.  Keeping that conversion explicit
# prevents a logical range from silently doubling while sprites stay fixed.
PLAYER_ATTACK_REACH = 48
PLAYER_ATTACK_WIDTH = 40
BASE_SWORD_DAMAGE = 25
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
    # Attack ranges share the fixed, 1x character-art scale. Enemy instances
    # convert only that value into campaign world units; detection/chase
    # distances remain authored against the map itself.
    "duwende_mandurug": EnemyStats(60, 8, 1.15, 80, 144, 96, 220, 280, 120, 4, 1.15, 0.52, 10),
    "tiyanak_sinta": EnemyStats(40, 5, 1.00, 80, 145, 88, 220, 280, 110, 4, 1.45, 0.58, 6),
    "manananggal": EnemyStats(60, 8, 1.10, 92, 175, 100, 255, 320, 130, 4, 1.35, 0.62, 10),
    "tikbalang": EnemyStats(80, 10, 0.95, 104, 155, 100, 240, 300, 125, 5, 1.45, 0.68, 16),
    "corrupted_core_kapre": EnemyStats(
        1000, 18, 1.10, 144, 260, 180, 520, 640, 220, 6, 1.10, 0.66, 45
    ),
}

# Feet-level combat bodies, deliberately smaller than the rendered artwork.
# These drive movement collision and sword hurtbox overlap, not sprite bounds.
ENEMY_BODY_SIZES = {
    "duwende_mandurug": (26, 26),
    "tiyanak_sinta": (20, 18),
    "manananggal": (28, 28),
    "tikbalang": (36, 38),
    "corrupted_core_kapre": (58, 64),
}


@dataclass(frozen=True)
class BossPhase:
    """One armour phase of a boss fight, entered by crossing ``threshold``.

    ``sword_damage`` is what a connected player swing takes off once the
    phase has been entered, ``aggression`` scales the boss's speed, attack
    rate and damage, and ``reinforcements`` is the pool a summoned wave
    draws from. Order matters: pool order decides which member a random
    draw picks, and phases are read in the order written here.
    """

    threshold: int
    sword_damage: int
    aggression: float
    reinforcements: tuple


# Per-boss fight tuning, keyed by the enemy id a stage names as its
# ``required_boss``. A boss with no entry here simply takes the player's
# ordinary weapon damage and never changes phase, so a stage can ship its
# boss before its phase table is tuned.
BOSS_PHASES = {
    "corrupted_core_kapre": {
        # Damage per connected hit before the first armour break. With the
        # phase damage below, the 1000-HP Core boss takes 10, 8, 6 and 6
        # hits: exactly 30 successful connections.
        "base_sword_damage": 25,
        "phases": (
            BossPhase(750, 35, 1.05, ("tiyanak_sinta", "manananggal")),
            BossPhase(500, 40, 1.10,
                      ("tiyanak_sinta", "manananggal", "tikbalang")),
            BossPhase(250, 45, 1.15,
                      ("manananggal", "tikbalang", "tiyanak_sinta")),
        ),
    },
}


def boss_phase_table(boss_id):
    """Return the authored phases for a boss, or an empty table."""

    return BOSS_PHASES.get(boss_id, {"base_sword_damage": 0, "phases": ()})


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
        self.max_energy = PLAYER_MAX_ENERGY
        # Kept as a float so partial-second regen accumulates instead of
        # being rounded away every frame; the HUD is what rounds it.
        self.energy = float(self.max_energy)
        # Health is a whole number everywhere it is read, so partial points
        # of healing are banked here until they add up to one.
        self._hp_regen_pool = 0.0
        self.attack_cooldown = 0.0
        self.dodge_cooldown = 0.0
        self.invulnerable = 0.0
        self.heal_delay = 0.0
        self.action_time = 0.0
        self.state = "idle"
        self.attack_id = 0

    @property
    def locked(self):
        return self.state in ("attacking", "dodging", "flinch", "defeated")

    @property
    def can_dodge(self):
        return not (self.dodge_cooldown or self.locked) and self.energy >= PLAYER_DODGE_ENERGY_COST

    @property
    def attack_active(self):
        elapsed = PLAYER_ATTACK_DURATION - self.action_time
        return self.state == "attacking" and PLAYER_ATTACK_ACTIVE_START <= elapsed <= PLAYER_ATTACK_ACTIVE_END

    @property
    def passive_healing_ready(self):
        return self.heal_delay == 0 and self.state != "defeated"

    def update(self, dt, energy_regen=PLAYER_ENERGY_REGEN, hp_regen=0.0):
        """Advance timers and regen, both rates given per second.

        A caller standing somewhere restorative passes faster rates; health
        regen defaults to zero because nothing heals the player by simply
        existing.
        """

        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.dodge_cooldown = max(0.0, self.dodge_cooldown - dt)
        self.invulnerable = max(0.0, self.invulnerable - dt)
        self.heal_delay = max(0.0, self.heal_delay - dt)
        self.energy = min(float(self.max_energy), self.energy + energy_regen * dt)
        self._regenerate_health(dt, hp_regen)
        if self.action_time > 0:
            self.action_time = max(0.0, self.action_time - dt)
            if self.action_time == 0 and self.state != "defeated":
                self.state = "idle"

    def _regenerate_health(self, dt, hp_regen):
        """Heal in whole points, keeping the fraction for the next frame.

        A downed player is never healed: torchlight closes wounds, it does
        not raise the dead. Standing at full health banks nothing, so the
        first point of healing after taking a hit still costs its time.
        """

        if (hp_regen <= 0 or not self.passive_healing_ready
                or not 0 < self.hp < self.max_hp):
            self._hp_regen_pool = 0.0
            return

        self._hp_regen_pool += hp_regen * dt
        healed = int(self._hp_regen_pool)
        if healed:
            self._hp_regen_pool -= healed
            self.hp = min(self.max_hp, self.hp + healed)

    def start_attack(self):
        if self.attack_cooldown or self.locked:
            return False
        self.state = "attacking"
        self.action_time = PLAYER_ATTACK_DURATION
        self.attack_cooldown = PLAYER_ATTACK_COOLDOWN
        self.attack_id += 1
        return True

    def start_dodge(self):
        if not self.can_dodge:
            return False
        self.energy -= PLAYER_DODGE_ENERGY_COST
        self.state = "dodging"
        self.action_time = PLAYER_DODGE_DURATION
        self.dodge_cooldown = PLAYER_DODGE_COOLDOWN
        self.invulnerable = max(self.invulnerable, PLAYER_DODGE_INVULNERABILITY)
        return True

    def take_damage(self, amount):
        amount = max(0, int(amount or 0))
        if amount == 0 or self.invulnerable or self.state == "defeated":
            return False
        self.hp = max(0, self.hp - amount)
        self._hp_regen_pool = 0.0
        self.heal_delay = PLAYER_TORCH_HEAL_DELAY
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

    def heal(self, amount):
        """Apply an immediate consumable heal and return points restored."""

        amount = max(0, int(amount or 0))
        if amount == 0 or self.state == "defeated" or self.hp >= self.max_hp:
            return 0
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        self._hp_regen_pool = 0.0
        return self.hp - before

    def reset(self):
        self.hp = self.max_hp
        self.energy = float(self.max_energy)
        self._hp_regen_pool = 0.0
        self.state = "idle"
        self.action_time = 0
        self.invulnerable = 0
        self.heal_delay = 0
        self.attack_cooldown = 0
        self.dodge_cooldown = 0


def attack_sweep_points(player_rect, facing, reach=PLAYER_ATTACK_REACH,
                        width=PLAYER_ATTACK_WIDTH, scale=1.0):
    """Return the four corners of a narrow, directional attack corridor."""

    dx, dy = FACING_VECTORS.get(facing, (1, 0))
    reach = max(0.0, float(reach) * scale)
    half_width = max(0.5, float(width) * scale / 2.0)
    perpendicular = (-dy, dx)
    start = (
        player_rect.centerx - dx * half_width,
        player_rect.centery - dy * half_width,
    )
    end = (
        player_rect.centerx + dx * (reach + half_width),
        player_rect.centery + dy * (reach + half_width),
    )
    return tuple(
        (round(point[0] + perpendicular[0] * side * half_width),
         round(point[1] + perpendicular[1] * side * half_width))
        for point, side in (
            (start, -1), (end, -1), (end, 1), (start, 1)
        )
    )


def attack_connects(attacker_rect, target_rect, facing,
                    reach=PLAYER_ATTACK_REACH, width=PLAYER_ATTACK_WIDTH,
                    scale=1.0):
    """Whether a target intersects the actual directional attack corridor.

    Expanding the target by the corridor width and clipping its centre-line
    against the attack segment is the rectangle equivalent of a swept blade.
    Unlike an axis-aligned union, it stays narrow for diagonal attacks.
    """

    dx, dy = FACING_VECTORS.get(facing, (1, 0))
    reach = max(0.0, float(reach) * scale)
    width = max(1, round(float(width) * scale))
    start = attacker_rect.center
    end = (
        round(start[0] + dx * reach),
        round(start[1] + dy * reach),
    )
    expanded_target = target_rect.inflate(width, width)
    return expanded_target.collidepoint(start) or bool(
        expanded_target.clipline(start, end)
    )


def attack_hitbox(player_rect, facing, scale=1.0):
    """Bounding rectangle of the directional sword sweep.

    Including the origin prevents a close enemy from becoming unhittable if
    its AI reaches or slightly crosses the player's center during a swing.
    Damage checks should use :func:`attack_connects`; this rectangle remains
    useful for debug drawing and broad-phase callers.
    """

    points = attack_sweep_points(player_rect, facing, scale=scale)
    left = min(point[0] for point in points)
    top = min(point[1] for point in points)
    right = max(point[0] for point in points)
    bottom = max(point[1] for point in points)
    return pygame.Rect(left, top, max(1, right - left), max(1, bottom - top))


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
