"""Responsive, state-driven HUD for the gameplay screen."""

import pygame


ICON_STRIP_PATH = "assets/images/ui/gameplay_hud_icons.png"
PORTRAIT_PATH = "assets/images/characters/main_character/main_character_profile.png"
MAX_HEARTS = 5

PANEL = (18, 20, 28, 225)
INNER = (28, 30, 38, 238)
METAL = (90, 94, 110)
GOLD = (210, 170, 74)
TEXT = (240, 240, 235)
DIM = (150, 155, 170)
CRIMSON = (190, 42, 52)
BLUE = (80, 180, 255)


class GameplayHUD:
    """Render gameplay data without owning or mutating it."""

    def __init__(self, screen, state, stage, inventory,
                 completed_stage_topics=None, bonus_time=0):
        self.screen = screen
        self.state = state
        self.stage = stage
        self.inventory = inventory
        self.completed_stage_topics = completed_stage_topics if completed_stage_topics is not None else ()
        self.bonus_time = bonus_time
        self.font = pygame.font.Font("assets/fonts/Cinzel-VariableFont_wght.ttf", 15)
        self.bold = pygame.font.Font("assets/fonts/Cinzel-Bold.ttf", 17)
        self.small = pygame.font.Font("assets/fonts/Cinzel-Bold.ttf", 13)
        self.icons = self._load_icons()
        self.portrait = self._load_portrait()
        self.profile_rect = pygame.Rect(0, 0, 0, 0)

    def _load_icons(self):
        strip = pygame.image.load(ICON_STRIP_PATH).convert_alpha()
        cell_width = strip.get_width() // 3
        return [
            strip.subsurface((index * cell_width, 0, cell_width, strip.get_height())).copy()
            for index in range(3)
        ]

    def _load_portrait(self):
        return pygame.image.load(PORTRAIT_PATH).convert_alpha()

    def draw(self, interaction_prompt=None, in_combat=False,
             current_hp=None, max_hp=None, bonus_time=None):
        width, height = self.screen.get_size()
        margin = max(10, round(min(width, height) * 0.016))
        self.profile_rect = pygame.Rect(margin, margin, min(510, width // 2), 134)
        progress_rect = pygame.Rect(0, margin, min(275, width // 3), 92)
        # Leave the rightmost 314 px to the existing StagePanel rail.
        progress_rect.right = width - margin - 314
        if progress_rect.left <= self.profile_rect.right + 10:
            progress_rect.topleft = (margin, self.profile_rect.bottom + 8)

        self.draw_character_profile(current_hp, max_hp, in_combat)
        self.draw_stage_progress(progress_rect)
        self.draw_weapon(margin, self.profile_rect.bottom + 8)
        self.draw_bonus_time(progress_rect.left, progress_rect.bottom + 8,
                             self.bonus_time if bonus_time is None else bonus_time)

        if interaction_prompt:
            self.draw_interaction_prompt(interaction_prompt, width, height)
        if in_combat:
            self.draw_combat_controls(width, height)

    def draw_character_profile(self, current_hp, max_hp, in_combat=False):
        self._profile_panel(self.profile_rect, emphasized=in_combat)
        portrait_rect = pygame.Rect(
            self.profile_rect.left + 13,
            self.profile_rect.top + 14,
            106,
            106,
        )
        pygame.draw.rect(self.screen, (8, 16, 25), portrait_rect)
        portrait = pygame.transform.scale(self.portrait, portrait_rect.size)
        self.screen.blit(portrait, portrait_rect)
        pygame.draw.rect(self.screen, (80, 55, 32), portrait_rect, 4)
        pygame.draw.rect(self.screen, (194, 126, 48), portrait_rect.inflate(-8, -8), 2)

        text_left = portrait_rect.right + 13
        self.screen.blit(self.bold.render("BOBILES THE EXPLORER", True, (236, 205, 149)),
                         (text_left, self.profile_rect.top + 20))
        self.draw_hearts(text_left, self.profile_rect.top + 50)
        self.draw_hp_bar(text_left, self.profile_rect.top + 90,
                         self.profile_rect.right - text_left - 14,
                         current_hp, max_hp, in_combat)

    def draw_hearts(self, x, y):
        active = max(0, min(MAX_HEARTS, int(self.state.get("hearts", 0))))
        heart = pygame.transform.scale(self.icons[0], (25, 25))
        empty = heart.copy()
        empty.fill((58, 58, 66, 175), special_flags=pygame.BLEND_RGBA_MULT)
        for index in range(MAX_HEARTS):
            self.screen.blit(heart if index < active else empty, (x + index * 29, y))

    def draw_hp_bar(self, x, y, width, current_hp, max_hp, emphasized=False):
        label = "HP -- / --"
        ratio = 0.0
        if current_hp is not None and max_hp:
            current_hp = max(0, min(current_hp, max_hp))
            ratio = current_hp / max_hp
            label = f"HP {current_hp} / {max_hp}"
        label_surface = self.small.render(label, True, TEXT if current_hp is not None else DIM)
        self.screen.blit(label_surface, (x, y - 1))
        bar = pygame.Rect(x + 92, y + 2, max(40, width - 92), 13)
        pygame.draw.rect(self.screen, (12, 13, 18), bar, border_radius=3)
        fill = bar.copy()
        fill.width = round(bar.width * ratio)
        if fill.width:
            pygame.draw.rect(self.screen, CRIMSON, fill, border_radius=3)
        pygame.draw.rect(self.screen, (255, 90, 90) if emphasized else METAL, bar, 2, border_radius=3)

    def draw_stage_progress(self, rect):
        self._panel(rect)
        stage_name = self.stage.get("name", "Unknown Stage").upper()
        subtitle = self.stage.get("subtitle", "")
        title = f"{stage_name}  {subtitle}".strip()
        self.screen.blit(self.bold.render(title, True, GOLD), (rect.left + 12, rect.top + 9))

        key_icon = pygame.transform.scale(self.icons[1], (31, 31))
        topic_icon = pygame.transform.scale(self.icons[2], (31, 31))
        stage_topics = set(self.stage.get("manual", {}).get("topics", ()))
        completed_topics = stage_topics.intersection(self.completed_stage_topics)
        total_topics = len(stage_topics)
        rows = (
            (key_icon, f"KEYS  {max(0, int(self.state.get('keys', 0)))}/5"),
            (topic_icon, f"TOPICS  {len(completed_topics)}/{total_topics}"),
        )
        for index, (icon, label) in enumerate(rows):
            y = rect.top + 38 + index * 25
            self.screen.blit(icon, (rect.left + 10, y - 7))
            self.screen.blit(self.font.render(label, True, TEXT), (rect.left + 45, y))

    def draw_weapon(self, x, y):
        item = self.inventory.get_selected_item()
        is_weapon = item is not None and (
            getattr(item, "kind", None) == "weapon"
            or "sword" in item.name.lower()
        )
        name = item.name if is_weapon else "No weapon equipped"
        rect = pygame.Rect(x, y, 250, 42)
        self._panel(rect)
        self._draw_sword_placeholder(rect.left + 13, rect.centery)
        self.screen.blit(self.font.render(name, True, TEXT if is_weapon else DIM), (rect.left + 44, rect.top + 12))

    def draw_bonus_time(self, x, y, bonus_time):
        rect = pygame.Rect(x, y, 112, 42)
        self._panel(rect)
        self._draw_clock_placeholder(rect.left + 20, rect.centery)
        value = max(0, round(float(bonus_time or 0)))
        self.screen.blit(self.bold.render(f"+{value}s", True, BLUE), (rect.left + 42, rect.top + 11))

    def draw_interaction_prompt(self, prompt, width, height):
        text = self.bold.render(f"[E] {prompt}", True, TEXT)
        rect = text.get_rect()
        rect.inflate_ip(34, 20)
        rect.midbottom = (width // 2, height - 92)
        self._panel(rect, emphasized=True)
        self.screen.blit(text, text.get_rect(center=rect.center))

    def draw_combat_controls(self, width, height):
        text = self.small.render("[E] ATTACK     [L-SHIFT] DODGE", True, TEXT)
        rect = text.get_rect()
        rect.inflate_ip(24, 14)
        rect.bottomright = (width - 14, height - 14)
        self._panel(rect, emphasized=True)
        self.screen.blit(text, text.get_rect(center=rect.center))

    def _panel(self, rect, emphasized=False):
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, PANEL, surface.get_rect(), border_radius=7)
        pygame.draw.rect(surface, INNER, surface.get_rect().inflate(-8, -8), border_radius=5)
        pygame.draw.rect(surface, GOLD if emphasized else METAL, surface.get_rect(), 2, border_radius=7)
        self.screen.blit(surface, rect)

    def _profile_panel(self, rect, emphasized=False):
        """Carved stone/bronze frame matching main_character_profile.png."""
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        local = surface.get_rect()
        pygame.draw.rect(surface, (15, 13, 12, 238), local, border_radius=5)
        pygame.draw.rect(surface, (55, 48, 39, 255), local, 5, border_radius=5)
        pygame.draw.rect(surface, (123, 78, 36, 255), local.inflate(-10, -10), 3, border_radius=4)
        pygame.draw.rect(surface, (31, 27, 24, 245), local.inflate(-18, -18), border_radius=3)
        pygame.draw.rect(surface, (9, 23, 36, 235), local.inflate(-24, -24), border_radius=2)
        pygame.draw.rect(
            surface,
            (235, 150, 56) if emphasized else (94, 67, 42),
            local.inflate(-24, -24),
            2,
            border_radius=2,
        )

        # Blocky carved corner caps and central blue focus gem.
        cap = 16
        for x, y in ((3, 3), (local.width - cap - 3, 3),
                     (3, local.height - cap - 3),
                     (local.width - cap - 3, local.height - cap - 3)):
            pygame.draw.rect(surface, (70, 61, 49), (x, y, cap, cap))
            pygame.draw.rect(surface, (145, 91, 39), (x + 3, y + 3, cap - 6, cap - 6), 2)

        gem_center = (local.centerx, 8)
        pygame.draw.polygon(surface, (113, 70, 31), [
            (gem_center[0], 0), (gem_center[0] + 12, 8),
            (gem_center[0], 16), (gem_center[0] - 12, 8),
        ])
        pygame.draw.polygon(surface, (54, 151, 211), [
            (gem_center[0], 3), (gem_center[0] + 6, 8),
            (gem_center[0], 13), (gem_center[0] - 6, 8),
        ])
        self.screen.blit(surface, rect)

    def _draw_sword_placeholder(self, x, y):
        pygame.draw.line(self.screen, (190, 195, 205), (x - 7, y + 8), (x + 9, y - 8), 5)
        pygame.draw.line(self.screen, (245, 245, 235), (x - 5, y + 6), (x + 10, y - 9), 2)
        pygame.draw.line(self.screen, GOLD, (x - 9, y + 2), (x - 2, y + 9), 4)

    def _draw_clock_placeholder(self, x, y):
        pygame.draw.circle(self.screen, GOLD, (x, y), 10, 2)
        pygame.draw.line(self.screen, TEXT, (x, y), (x, y - 6), 2)
        pygame.draw.line(self.screen, TEXT, (x, y), (x + 5, y + 3), 2)
