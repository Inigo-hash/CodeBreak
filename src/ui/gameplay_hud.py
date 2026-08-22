"""Responsive, state-driven HUD for the gameplay screen."""

import pygame

from src.ui.theme import UI_COLORS, body_font, draw_panel, title_font


ICON_STRIP_PATH = "assets/images/ui/gameplay_hud_icons.png"
PORTRAIT_PATH = "assets/images/characters/main_character/main_character_profile.png"
MAX_HEARTS = 5

PANEL = (*UI_COLORS["stone_deep"], 225)
INNER = (*UI_COLORS["stone"], 238)
METAL = UI_COLORS["bronze_dark"]
GOLD = UI_COLORS["gold"]
TEXT = UI_COLORS["text"]
DIM = UI_COLORS["text_dim"]
CRIMSON = UI_COLORS["crimson"]
BLUE = UI_COLORS["blue_bright"]

# Portrait framing, shared with the full profile screen so the small card and
# the big one are trimmed the same way.
PORTRAIT_FRAME = (80, 55, 32)
PORTRAIT_INNER = (194, 126, 48)
PORTRAIT_BACKING = (8, 16, 25)
NAME_GOLD = (236, 205, 149)


def load_hud_icons():
    """Slice the three-cell icon strip: heart, key, topic."""
    strip = pygame.image.load(ICON_STRIP_PATH).convert_alpha()
    cell_width = strip.get_width() // 3
    return [
        strip.subsurface((index * cell_width, 0, cell_width, strip.get_height())).copy()
        for index in range(3)
    ]


def load_portrait():
    return pygame.image.load(PORTRAIT_PATH).convert_alpha()


def draw_profile_frame(surface, rect, emphasized=False):
    """Carved stone/bronze frame matching main_character_profile.png.

    Lives at module level because profile.py draws the same frame at full
    size — the small HUD card and the screen it opens have to be recognisably
    the same object.
    """
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    local = panel.get_rect()
    pygame.draw.rect(panel, (*UI_COLORS["stone_deep"], 238), local, border_radius=5)
    pygame.draw.rect(panel, UI_COLORS["stone_light"], local, 5, border_radius=5)
    pygame.draw.rect(panel, UI_COLORS["bronze"], local.inflate(-10, -10), 3, border_radius=4)
    pygame.draw.rect(panel, (*UI_COLORS["stone"], 245), local.inflate(-18, -18), border_radius=3)
    pygame.draw.rect(panel, (9, 23, 36, 235), local.inflate(-24, -24), border_radius=2)
    pygame.draw.rect(
        panel,
        UI_COLORS["blue"] if emphasized else UI_COLORS["bronze_dark"],
        local.inflate(-24, -24),
        2,
        border_radius=2,
    )

    # Blocky carved corner caps and central blue focus gem.
    cap = 16
    for x, y in ((3, 3), (local.width - cap - 3, 3),
                 (3, local.height - cap - 3),
                 (local.width - cap - 3, local.height - cap - 3)):
        pygame.draw.rect(panel, UI_COLORS["stone_light"], (x, y, cap, cap))
        pygame.draw.rect(panel, UI_COLORS["bronze"], (x + 3, y + 3, cap - 6, cap - 6), 2)

    gem_center = (local.centerx, 8)
    pygame.draw.polygon(panel, (113, 70, 31), [
        (gem_center[0], 0), (gem_center[0] + 12, 8),
        (gem_center[0], 16), (gem_center[0] - 12, 8),
    ])
    pygame.draw.polygon(panel, UI_COLORS["blue"], [
        (gem_center[0], 3), (gem_center[0] + 6, 8),
        (gem_center[0], 13), (gem_center[0] - 6, 8),
    ])
    surface.blit(panel, rect)


MINIMAP_FRAME = 20     # thickness of the carved surround, in pixels


def build_minimap_frame(size, thickness=MINIMAP_FRAME, radius=7):
    """
    The carved stone surround for the minimap, with the viewport punched
    out of the middle and the cardinal letters inked into the band.

    Returned as a pre-rendered surface with a transparent centre so the
    per-frame job stays "blit terrain, blit this over it" - the frame has
    no moving parts, and rebuilding this stack of rects sixty times a
    second to draw the same pixels would be waste.

    Same plate, bronze rim and corner caps as `draw_profile_frame`, minus
    its focus gem: the gem sits top-centre on the profile card, which is
    exactly where N has to go here.
    """

    frame = pygame.Surface(size, pygame.SRCALPHA)
    local = frame.get_rect()
    view = local.inflate(-thickness * 2, -thickness * 2)

    pygame.draw.rect(frame, (5, 6, 9, 150), local.move(0, 5), border_radius=radius)
    pygame.draw.rect(frame, (*UI_COLORS["stone_deep"], 242), local, border_radius=radius)
    pygame.draw.rect(frame, UI_COLORS["stone_light"], local, 4, border_radius=radius)

    # Stone face, lit along the top and shaded along the bottom so the
    # band reads as a slab with depth rather than a printed border. Bronze
    # is an accent line here, not the material - a band of solid bronze is
    # what made the first pass look like a picture frame.
    face = local.inflate(-6, -6)
    pygame.draw.rect(frame, UI_COLORS["stone"], face, border_radius=max(2, radius - 3))
    pygame.draw.line(frame, (69, 72, 84), (face.left + 4, face.top + 1),
                     (face.right - 4, face.top + 1), 1)
    pygame.draw.line(frame, UI_COLORS["bronze_dark"], (face.left + 4, face.bottom - 1),
                     (face.right - 4, face.bottom - 1), 1)
    pygame.draw.rect(frame, UI_COLORS["bronze"], face, 1, border_radius=max(2, radius - 3))

    # The viewport sits in a recess: a dark step down into the stone, then
    # a thin bronze lip right at the terrain.
    pygame.draw.rect(frame, UI_COLORS["stone_deep"], view.inflate(10, 10), 5)
    pygame.draw.rect(frame, UI_COLORS["bronze"], view.inflate(3, 3), 2)

    # Punch the viewport. Everything drawn after this point has to stay
    # inside the band, or it will hang over the map.
    frame.fill((0, 0, 0, 0), view)

    cap = thickness - 8
    for x, y in ((2, 2), (local.width - cap - 2, 2),
                 (2, local.height - cap - 2),
                 (local.width - cap - 2, local.height - cap - 2)):
        pygame.draw.rect(frame, UI_COLORS["stone_light"], (x, y, cap, cap))
        pygame.draw.rect(frame, UI_COLORS["stone_deep"], (x, y, cap, cap), 1)
        pygame.draw.rect(frame, UI_COLORS["bronze"], (x + 3, y + 3, cap - 6, cap - 6), 2)

    # Cardinals on the band rather than floating over the terrain, where
    # they used to compete with the zone names for the same pixels.
    letter_font = title_font(max(9, thickness // 2))
    band = thickness // 2
    for text, center, along in (
        ("N", (local.centerx, band), "h"),
        ("S", (local.centerx, local.bottom - band), "h"),
        ("W", (band, local.centery), "v"),
        ("E", (local.right - band, local.centery), "v"),
    ):
        label = letter_font.render(text, True, GOLD)
        frame.blit(label, label.get_rect(center=center))

        # Bronze ticks flanking each letter, so the band reads as a scale.
        for step in (-1, 1):
            if along == "h":
                x = center[0] + step * (label.get_width() // 2 + 6)
                pygame.draw.line(frame, METAL, (x, center[1] - 3), (x, center[1] + 3), 2)
            else:
                y = center[1] + step * (label.get_height() // 2 + 5)
                pygame.draw.line(frame, METAL, (center[0] - 3, y), (center[0] + 3, y), 2)

    return frame


def build_view_vignette(size, band=24, strength=135):
    """
    A dark gradient hugging the inside of the minimap viewport.

    Two jobs: it settles the terrain into the frame instead of letting a
    bright tile butt straight up against the stone, and it darkens the
    busiest part of the crop - the edges, where zone names and the sea
    tend to land - so the labels over it stay readable.

    Drawn as concentric one-pixel rings, which is a gradient with no
    blurring and no per-frame cost; the caller builds it once.
    """

    veil = pygame.Surface(size, pygame.SRCALPHA)
    rect = veil.get_rect()
    for step in range(band):
        alpha = int(strength * ((band - step) / band) ** 2)
        pygame.draw.rect(veil, (6, 8, 12, alpha), rect.inflate(-step * 2, -step * 2), 1)
    return veil


def draw_framed_portrait(surface, portrait, rect):
    """Bronze-trimmed portrait tile, at whatever size `rect` asks for."""
    pygame.draw.rect(surface, PORTRAIT_BACKING, rect)
    surface.blit(pygame.transform.scale(portrait, rect.size), rect)
    pygame.draw.rect(surface, PORTRAIT_FRAME, rect, 4)
    pygame.draw.rect(surface, PORTRAIT_INNER, rect.inflate(-8, -8), 2)


def draw_heart_row(surface, icons, x, y, active, size=25, gap=29):
    """The five-heart life row. Spent hearts stay in place, greyed out."""
    heart = pygame.transform.scale(icons[0], (size, size))
    empty = heart.copy()
    empty.fill((58, 58, 66, 175), special_flags=pygame.BLEND_RGBA_MULT)
    active = max(0, min(MAX_HEARTS, int(active)))
    for index in range(MAX_HEARTS):
        surface.blit(heart if index < active else empty, (x + index * gap, y))


def draw_stat_bar(surface, font, x, y, width, label, current, maximum,
                  fill_color=CRIMSON, emphasized=False, label_width=92):
    """Label on the left, thin rounded bar on the right.

    An unset maximum draws as "-- / --" rather than a full-looking 0/0 bar,
    so a stat that is not wired up yet reads as unknown instead of broken.
    """
    ratio = 0.0
    if current is not None and maximum:
        current = max(0, min(current, maximum))
        ratio = current / maximum
        text = f"{label} {current} / {maximum}"
    else:
        text = f"{label} -- / --"
    surface.blit(font.render(text, True, TEXT if maximum else DIM), (x, y - 1))

    bar = pygame.Rect(x + label_width, y + 2, max(40, width - label_width), 13)
    pygame.draw.rect(surface, (12, 13, 18), bar, border_radius=3)
    fill = bar.copy()
    fill.width = round(bar.width * ratio)
    if fill.width:
        pygame.draw.rect(surface, fill_color, fill, border_radius=3)
    pygame.draw.rect(surface, (255, 90, 90) if emphasized else METAL, bar, 2,
                     border_radius=3)


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
        self.font = body_font(15)
        self.bold = title_font(17)
        self.small = body_font(13, bold=True)
        self.icons = self._load_icons()
        self.portrait = self._load_portrait()
        self.profile_rect = pygame.Rect(0, 0, 0, 0)

    def _load_icons(self):
        return load_hud_icons()

    def _load_portrait(self):
        return load_portrait()

    def draw(self, interaction_prompt=None, in_combat=False,
             current_hp=None, max_hp=None, bonus_time=None):
        width, height = self.screen.get_size()
        margin = max(10, round(min(width, height) * 0.016))
        self.profile_rect = pygame.Rect(margin, margin, min(510, width // 2), 134)
        # Everything stacks in one left-hand column under the profile card so
        # the panels read as a single group instead of floating apart.
        progress_rect = pygame.Rect(margin, self.profile_rect.bottom + 8,
                                    min(275, width // 3), 92)
        weapon_rect = pygame.Rect(margin, progress_rect.bottom + 8, 250, 42)
        bonus_rect = pygame.Rect(margin, weapon_rect.bottom + 8, 112, 42)

        self.draw_character_profile(current_hp, max_hp, in_combat)
        self.draw_stage_progress(progress_rect)
        self.draw_weapon(weapon_rect.left, weapon_rect.top)
        self.draw_bonus_time(bonus_rect.left, bonus_rect.top,
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
        draw_framed_portrait(self.screen, self.portrait, portrait_rect)

        text_left = portrait_rect.right + 13
        self.screen.blit(self.bold.render("BOBILES THE EXPLORER", True, NAME_GOLD),
                         (text_left, self.profile_rect.top + 20))
        self.draw_hearts(text_left, self.profile_rect.top + 50)
        self.draw_hp_bar(text_left, self.profile_rect.top + 90,
                         self.profile_rect.right - text_left - 14,
                         current_hp, max_hp, in_combat)

    def draw_hearts(self, x, y):
        draw_heart_row(self.screen, self.icons, x, y, self.state.get("hearts", 0))

    def draw_hp_bar(self, x, y, width, current_hp, max_hp, emphasized=False):
        draw_stat_bar(self.screen, self.small, x, y, width, "HP",
                      current_hp, max_hp, emphasized=emphasized)

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
        draw_panel(self.screen, rect, emphasized=emphasized, radius=7, alpha=225)

    def _profile_panel(self, rect, emphasized=False):
        draw_profile_frame(self.screen, rect, emphasized=emphasized)

    def _draw_sword_placeholder(self, x, y):
        pygame.draw.line(self.screen, (190, 195, 205), (x - 7, y + 8), (x + 9, y - 8), 5)
        pygame.draw.line(self.screen, (245, 245, 235), (x - 5, y + 6), (x + 10, y - 9), 2)
        pygame.draw.line(self.screen, GOLD, (x - 9, y + 2), (x - 2, y + 9), 4)

    def _draw_clock_placeholder(self, x, y):
        pygame.draw.circle(self.screen, GOLD, (x, y), 10, 2)
        pygame.draw.line(self.screen, TEXT, (x, y), (x, y - 6), 2)
        pygame.draw.line(self.screen, TEXT, (x, y), (x + 5, y + 3), 2)
