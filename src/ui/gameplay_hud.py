"""Responsive, state-driven HUD for the gameplay screen."""

import math
from functools import lru_cache
import pygame
from src.data.characters import CHARACTERS, character_id as normalize_character_id, character_title
from src.ui.text_layout import fit_text

from src.systems.stage_gate import required_key_count

from src.systems.combat import PLAYER_DODGE_ENERGY_COST
from src.ui.theme import UI_COLORS, body_font, draw_panel, title_font


ICON_STRIP_PATH = "assets/images/ui/gameplay_hud_icons.png"
MAX_HEARTS = 5

PANEL = (*UI_COLORS["stone_deep"], 225)
INNER = (*UI_COLORS["stone"], 238)
METAL = UI_COLORS["bronze_dark"]
GOLD = UI_COLORS["gold"]
TEXT = UI_COLORS["text"]
DIM = UI_COLORS["text_dim"]
CRIMSON = UI_COLORS["crimson"]
BLUE = UI_COLORS["blue_bright"]

NAME_GOLD = (236, 205, 149)
# Warm amber for the energy bar while torchlight is accelerating regen, so
# the boost is readable without adding another HUD element. Health uses a
# green instead: both bars turning the same colour would read as one
# effect, and a red bar filling back up needs to look like healing.
TORCH_AMBER = (255, 176, 74)
HEAL_GREEN = (104, 198, 122)
LOW_HP_THRESHOLD = 0.30

_low_health_overlay_cache = {}

# The HUD redraws from scratch every frame, but its text changes only when
# the underlying number does - so most frames re-rasterised glyphs that were
# identical to the last frame's. Font.render is deterministic for a given
# font, string and colour, so the result can simply be kept.
#
# The font is part of the key (and holds it alive, so no two fonts can share
# a slot). Callers only ever blit what they get back; nothing draws into a
# returned surface, which is what makes handing out the same one safe.
_TEXT_CACHE = {}
_TEXT_CACHE_LIMIT = 512


def render_text(font, text, color):
    """Render HUD text, reusing the surface when nothing about it changed."""

    key = (font, text, tuple(color) if isinstance(color, (list, tuple)) else color)
    surface = _TEXT_CACHE.get(key)
    if surface is None:
        # Numbers like the HP readout make the key space open-ended. Dropping
        # the whole cache on overflow keeps this bounded without pretending
        # to know which entries the next frame will want.
        if len(_TEXT_CACHE) >= _TEXT_CACHE_LIMIT:
            _TEXT_CACHE.clear()
        surface = font.render(text, True, color)
        _TEXT_CACHE[key] = surface
    return surface


def build_low_health_corner_overlay(size):
    """Cache a soft crimson edge fade with a completely clear combat area."""
    cached = _low_health_overlay_cache.get(size)
    if cached is not None:
        return cached

    # Build a small, continuous gradient once. Scaling removes hard bands
    # without the cost of full-resolution per-pixel work during combat.
    sw, sh = 240, 136
    small = pygame.Surface((sw, sh), pygame.SRCALPHA)
    for y in range(sh):
        ny = min(y, sh - 1 - y) / (sh - 1)
        for x in range(sw):
            nx = min(x, sw - 1 - x) / (sw - 1)
            # A rounded contour avoids a visible rectangular inner border.
            distance = ((1.0 - 2.0 * nx) ** 4 + (1.0 - 2.0 * ny) ** 4) ** .25
            edge = max(0.0, min(1.0, (distance - .64) / .36))
            fade = edge * edge * (3.0 - 2.0 * edge)
            corner = max(0.0, 1.0 - nx / .30) * max(0.0, 1.0 - ny / .30)
            alpha = round(170 * fade + 36 * corner)
            small.set_at((x, y), (174, 18, 36, min(210, alpha)))
    overlay = pygame.transform.smoothscale(small, size)
    # Only the latest few window sizes need to stay in memory.
    if len(_low_health_overlay_cache) >= 4:
        _low_health_overlay_cache.clear()
    _low_health_overlay_cache[size] = overlay
    return overlay


def draw_low_health_warning(surface, current_hp, max_hp, time_seconds=0.0):
    """A gentle double heartbeat grows stronger as health falls below 30%."""
    if current_hp is None or not max_hp or current_hp <= 0:
        return False
    hp_ratio = max(0.0, min(1.0, current_hp / max_hp))
    if hp_ratio > LOW_HP_THRESHOLD:
        return False

    urgency = 1.0 - hp_ratio / LOW_HP_THRESHOLD
    phase = (time_seconds * (0.72 + .28 * urgency)) % 1.0
    beat = math.exp(-((phase - .10) / .075) ** 2)
    beat += .55 * math.exp(-((phase - .29) / .10) ** 2)
    alpha = round(255 * min(1.0, .65 + .20 * urgency + .15 * beat))
    overlay = build_low_health_corner_overlay(surface.get_size())
    overlay.set_alpha(alpha)
    surface.blit(overlay, (0, 0))
    return True


def load_hud_icons():
    """Slice the three-cell icon strip: heart, key, topic."""
    strip = pygame.image.load(ICON_STRIP_PATH).convert_alpha()
    cell_width = strip.get_width() // 3
    return [
        strip.subsurface((index * cell_width, 0, cell_width, strip.get_height())).copy()
        for index in range(3)
    ]


def load_portrait(character_id='man'):
    return _load_portrait_asset(normalize_character_id(character_id))


@lru_cache(maxsize=2)
def _load_portrait_asset(identity):
    return pygame.image.load(CHARACTERS[identity]['portrait']).convert_alpha()


def draw_profile_frame(surface, rect, emphasized=False):
    """A compact cut-corner game plate, shared with the expanded profile."""
    surface.blit(_profile_frame(rect.size, emphasized), rect)


@lru_cache(maxsize=24)
def _profile_frame(size, emphasized):
    panel = pygame.Surface(size, pygame.SRCALPHA)
    local = panel.get_rect()
    w, h = local.size
    shape = [(0, 5), (5, 0), (w-6, 0), (w-1, 5),
             (w-1, h-6), (w-6, h-1), (5, h-1), (0, h-6)]
    rim = UI_COLORS['gold'] if emphasized else (125, 105, 72)
    pygame.draw.polygon(panel, (22, 22, 23, 248), shape)
    pygame.draw.polygon(panel, rim, shape, 1)
    pygame.draw.line(panel, (62, 56, 44), (7, 3), (w-8, 3))
    pygame.draw.line(panel, (8, 9, 10), (7, h-4), (w-8, h-4))
    return panel


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


def build_view_vignette(size, band=24, strength=135, color=(6, 8, 12)):
    """
    A dark gradient hugging the inside of the minimap viewport.

    Two jobs: it settles what is inside the frame instead of letting it
    butt straight up against the stone, and it darkens the busiest part
    of the crop - the edges, where zone names and the sea tend to land -
    so the labels over it stay readable.

    ``color`` is worth setting to match what is being shaded: the default
    cold near-black was picked against terrain art, and shading parchment
    with it greys the paper out rather than tanning it.

    Drawn as concentric one-pixel rings, which is a gradient with no
    blurring and no per-frame cost; the caller builds it once.
    """

    veil = pygame.Surface(size, pygame.SRCALPHA)
    rect = veil.get_rect()
    for step in range(band):
        alpha = int(strength * ((band - step) / band) ** 2)
        pygame.draw.rect(veil, (*color, alpha), rect.inflate(-step * 2, -step * 2), 1)
    return veil


def draw_framed_portrait(surface, portrait, rect):
    """Fit the illustration without stretching or rescaling it each frame."""
    surface.blit(_portrait_tile(portrait, rect.size), rect)


@lru_cache(maxsize=16)
def _portrait_tile(portrait, size):
    width, height = size
    scale = max(width / portrait.get_width(), height / portrait.get_height())
    image = pygame.transform.scale(portrait, (
        max(width, round(portrait.get_width()*scale)),
        max(height, round(portrait.get_height()*scale))))
    tile = pygame.Surface(size, pygame.SRCALPHA)
    tile.blit(image, image.get_rect(center=tile.get_rect().center))
    pygame.draw.rect(tile, (38, 32, 25), tile.get_rect(), 3)
    pygame.draw.rect(tile, (151, 123, 78), tile.get_rect().inflate(-2, -2), 1)
    return tile


@lru_cache(maxsize=16)
def _heart_tiles(icon, size):
    heart = pygame.transform.scale(icon, (size, size))
    empty = heart.copy()
    empty.fill((70, 76, 86, 180), special_flags=pygame.BLEND_RGBA_MULT)
    return heart, empty


def draw_heart_row(surface, icons, x, y, active, size=25, gap=29):
    """The five-heart life row. Spent hearts stay in place, greyed out."""
    heart, empty = _heart_tiles(icons[0], size)
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
    label_width = min(label_width, max(1, width - 48))
    surface.blit(fit_text(font, text, TEXT if maximum else DIM,
                          (label_width - 8, min(20,font.get_height()))), (x, y - 1))

    bar = pygame.Rect(x + label_width, y + 2, max(40, width - label_width), 13)
    pygame.draw.rect(surface, (12, 13, 18), bar, border_radius=3)
    fill = bar.copy()
    fill.width = round(bar.width * ratio)
    if fill.width:
        pygame.draw.rect(surface, fill_color, fill, border_radius=3)
    pygame.draw.rect(surface, (255, 90, 90) if emphasized else METAL, bar, 2,
                     border_radius=3)


def character_card_layout(size, name_height=26, label_height=14):
    """Reserve real text rows before positioning portrait and resource bars."""
    width, height = size
    margin = max(10, round(min(width, height)*.016))
    card_width = min(384, max(310, round(width*.32)), width-margin*2)
    name_height = max(22, name_height)
    life_height = max(16, label_height)
    meter_height = max(20, label_height+6)
    portrait_size = 96 if card_width >= 360 else 80
    card_height = max(24+name_height+4+life_height+8+meter_height*2+6,
                      portrait_size+20)
    card = pygame.Rect(margin, margin, card_width, card_height)
    portrait = pygame.Rect(card.x+10, card.centery-portrait_size//2, portrait_size, portrait_size)
    left, right = portrait.right+12, card.right-12
    name = pygame.Rect(left, card.y+12, right-left-18, name_height)
    health = pygame.Rect(left, name.bottom+4, right-left, meter_height)
    energy = pygame.Rect(left, health.bottom+6, right-left, meter_height)
    lives = pygame.Rect(left, energy.bottom+8, right-left, life_height)
    return card, portrait, name, lives, health, energy


def draw_resource_meter(surface, font, rect, label, current, maximum,
                        fill_color=CRIMSON, emphasized=False):
    """Classic labelled gauges with values inside the track, never over art."""
    known = current is not None and maximum is not None and maximum > 0
    amount = max(0, min(current, maximum)) if known else 0
    ratio = amount/maximum if known else 0
    value = f'{round(amount)} / {round(maximum)}' if known else '-- / --'
    gutter = min(max(font.size('ENERGY')[0], font.size(label)[0])+9, rect.width//2)
    label_surface = fit_text(font, label, DIM, (gutter-7, rect.height))
    surface.blit(label_surface, label_surface.get_rect(midleft=(rect.x, rect.centery)))
    bar = pygame.Rect(rect.x+gutter, rect.y+1, rect.width-gutter, rect.height-2)
    pygame.draw.rect(surface, (8, 10, 12), bar)
    fill = bar.inflate(-4, -4)
    fill.width = round(fill.width*ratio)
    if fill.width:
        pygame.draw.rect(surface, fill_color, fill)
    pygame.draw.rect(surface, (212, 107, 98) if emphasized else (67, 78, 82),
                     bar, 1)
    number = fit_text(font, value, TEXT if known else DIM, (bar.width-8, bar.height-4))
    number_rect = number.get_rect(center=bar.center)
    shadow = number.copy()
    shadow.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(shadow, number_rect.move(1, 1))
    surface.blit(number, number_rect)
    return bar


class GameplayHUD:
    """Render gameplay data without owning or mutating it."""

    def __init__(self, screen, state, stage,
                 completed_stage_topics=None, bonus_time=0):
        self.screen = screen
        self.state = state
        self.stage = stage
        self.completed_stage_topics = completed_stage_topics if completed_stage_topics is not None else ()
        self.bonus_time = bonus_time
        self.font = body_font(15)
        self.bold = title_font(17)
        self.small = body_font(13, bold=True)
        self.stage_heading = title_font(14)
        self.icons = self._load_icons()
        self.portrait = self._load_portrait()
        self.profile_rect = pygame.Rect(0, 0, 0, 0)
        self._scaled_progress_icons = None

    def _progress_icons(self):
        if self._scaled_progress_icons is None:
            self._scaled_progress_icons = (
                pygame.transform.scale(self.icons[1], (21, 21)),
                pygame.transform.scale(self.icons[2], (21, 21)),
            )
        return self._scaled_progress_icons

    def _load_icons(self):
        return load_hud_icons()

    def _load_portrait(self):
        return load_portrait(self.state.get('character_id', 'man'))

    def draw(self, interaction_prompt=None, in_combat=False,
             current_hp=None, max_hp=None, bonus_time=None,
             current_energy=None, max_energy=None, energy_boosted=False,
             hp_healing=False):
        width, height = self.screen.get_size()
        margin = max(10, round(min(width, height) * 0.016))
        parts = character_card_layout((width, height), self.bold.get_height(), self.small.get_height())
        self.profile_rect = parts[0]
        # Everything stacks in one left-hand column under the profile card so
        # the panels read as a single group instead of floating apart.
        secondary_height = self.small.get_height()+2 if height >= 640 else 0
        progress_rect = pygame.Rect(margin, self.profile_rect.bottom+8, self.profile_rect.width,
                                    18+self.stage_heading.get_height()+max(24, self.font.get_height())
                                    +secondary_height)

        self.draw_character_profile(current_hp, max_hp, in_combat,
                                    current_energy, max_energy,
                                    energy_boosted, hp_healing)
        self.draw_stage_progress(progress_rect,
                                 self.bonus_time if bonus_time is None else bonus_time)

        if interaction_prompt:
            self.draw_interaction_prompt(interaction_prompt, width, height)
        if in_combat:
            # Unset energy means "not being tracked", so the hint stays lit
            # rather than claiming dodge is unavailable.
            self.draw_combat_controls(
                width, height,
                dodge_ready=current_energy is None or current_energy >= PLAYER_DODGE_ENERGY_COST,
            )

    def draw_character_profile(self, current_hp, max_hp, in_combat=False,
                               current_energy=None, max_energy=None,
                               energy_boosted=False, hp_healing=False):
        self._profile_panel(self.profile_rect, emphasized=in_combat)
        _, portrait_rect, name_rect, lives, health, energy = character_card_layout(
            self.screen.get_size(), self.bold.get_height(), self.small.get_height())
        draw_framed_portrait(self.screen, self.portrait, portrait_rect)
        name = character_title(self.state.get('character_id', 'man'))
        title = fit_text(self.bold, name, NAME_GOLD, name_rect.size)
        self.screen.blit(title, name_rect)
        # The card opens a real profile screen; the chevron makes that visible.
        cx, cy = self.profile_rect.right-18, name_rect.centery
        pygame.draw.lines(self.screen, GOLD, False, [(cx-3, cy-4), (cx+1, cy), (cx-3, cy+4)], 2)
        label_width = max(36, self.small.size('LIVES')[0]+8)
        label = fit_text(self.small, 'LIVES', DIM, (label_width-8, lives.height))
        self.screen.blit(label, lives)
        heart_size = min(17, lives.height, max(10, (lives.width-label_width-12)//5))
        draw_heart_row(self.screen, self.icons, lives.x+label_width, lives.y,
                       self.state.get('hearts', 0), size=heart_size, gap=heart_size+3)
        draw_resource_meter(self.screen, self.small, health, 'HP', current_hp, max_hp,
                            HEAL_GREEN if hp_healing else CRIMSON,
                            emphasized=in_combat or bool(max_hp and current_hp is not None
                                                       and current_hp/max_hp <= LOW_HP_THRESHOLD))
        draw_resource_meter(self.screen, self.small, energy, 'ENERGY', current_energy, max_energy,
                            TORCH_AMBER if energy_boosted else GOLD)

    def _stat_label_width(self):
        return max(self.small.size("HP 000 / 000")[0],
                   self.small.size("ENERGY 000 / 000")[0]) + 12

    def draw_hearts(self, x, y):
        draw_heart_row(self.screen, self.icons, x, y, self.state.get("hearts", 0))

    def draw_hp_bar(self, x, y, width, current_hp, max_hp, emphasized=False,
                    label_width=92, healing=False):
        """Health, in crimson - or green while torchlight is closing it."""

        draw_stat_bar(self.screen, self.small, x, y, width, "HP",
                      current_hp, max_hp, emphasized=emphasized,
                      fill_color=HEAL_GREEN if healing else CRIMSON,
                      label_width=label_width)

    def draw_energy_bar(self, x, y, width, current_energy, max_energy,
                        label_width=92, boosted=False):
        """The dodge budget, in gold under the red HP bar.

        It burns amber while something - torchlight, today - is refilling
        it faster than the player's own recovery would.
        """
        draw_stat_bar(self.screen, self.small, x, y, width, "ENERGY",
                      current_energy, max_energy,
                      fill_color=TORCH_AMBER if boosted else GOLD,
                      label_width=label_width)

    def draw_stage_progress(self, rect, bonus_time=0):
        stage_name = self.stage.get("name", "Unknown Stage").upper()
        subtitle = self.stage.get("subtitle", "")
        self._profile_panel(rect)
        header = pygame.Rect(rect.x+12, rect.y+8, rect.width-24, self.stage_heading.get_height())
        title = fit_text(self.stage_heading, stage_name, NAME_GOLD, (header.width-106, header.height))
        self.screen.blit(title, header)
        # Bonus time belongs to stage progress; a third floating card hid map.
        value = max(0, round(float(bonus_time or 0)))
        label = fit_text(self.small, f'+{value}s', NAME_GOLD, (78, header.height))
        self.screen.blit(label, label.get_rect(midright=(header.right, header.centery)))
        clock_x = header.right-max(38, label.get_width())-14
        pygame.draw.circle(self.screen, GOLD, (clock_x, header.centery), 6, 1)
        pygame.draw.line(self.screen, TEXT, (clock_x, header.centery), (clock_x, header.centery-4))
        pygame.draw.line(self.screen, TEXT, (clock_x, header.centery), (clock_x+3, header.centery+1))
        row_y = header.bottom+2
        if self.screen.get_height() >= 640:
            sub = fit_text(self.small, subtitle, DIM, (header.width, self.small.get_height()))
            self.screen.blit(sub, (header.x, row_y))
            row_y += self.small.get_height()+2

        # Scaled once and kept: these two never change size, and rescaling
        # them per frame was pure repeat work.
        key_icon, topic_icon = self._progress_icons()
        stage_topics = set(self.stage.get("manual", {}).get("topics", ()))
        completed_topics = stage_topics.intersection(self.completed_stage_topics)
        total_topics = len(stage_topics)
        rows = (
            (key_icon, (
                f"KEYS {max(0, int(self.state.get('keys', 0)))}"
                f"/{required_key_count(self.stage)}"
            )),
            (topic_icon, f"{('CODE' if rect.width < 360 else 'CHALLENGES') if self.stage.get('completion', {}).get('mastery_bundles') else 'TOPICS'} {len(completed_topics)}/{total_topics}"),
        )
        column_width = (rect.width-32)//2
        for index, (icon, label) in enumerate(rows):
            x = rect.x+12+index*(column_width+8)
            self.screen.blit(icon, (x, row_y))
            text = fit_text(self.font, label, TEXT, (column_width-26, max(21, self.font.get_height())))
            self.screen.blit(text, (x+26, row_y))

    def draw_bonus_time(self, x, y, bonus_time):
        value = max(0, round(float(bonus_time or 0)))
        label = f"+{value}s"
        rect = pygame.Rect(x, y, min(max(112, self.bold.size(label)[0] + 54),
                                    self.screen.get_width() - x * 2), 42)
        self._panel(rect)
        self._draw_clock_placeholder(rect.left + 20, rect.centery)
        self.screen.blit(fit_text(self.bold, label, BLUE, (rect.width - 54, 28)),
                         (rect.left + 42, rect.top + 7))

    def draw_interaction_prompt(self, prompt, width, height):
        label = prompt if prompt.startswith(("[B]", "Hold E")) else f"[E] {prompt}"
        text = render_text(self.bold, label, TEXT)
        rect = text.get_rect()
        rect.inflate_ip(34, 20)
        rect.width = min(rect.width, width - 40)
        # Leave room for the equipped-item label above the hotbar.
        rect.midbottom = (width // 2, height - 126)
        self._panel(rect, emphasized=True)
        fitted = fit_text(self.bold, label, TEXT, (rect.width - 34, rect.height - 20))
        self.screen.blit(fitted, fitted.get_rect(center=rect.center))

    def draw_combat_controls(self, width, height, dodge_ready=True):
        # Two renders instead of one line so the dodge half can grey out on
        # its own while energy is below the cost of a dodge.
        attack = render_text(self.small, "[E] ATTACK     ", TEXT)
        dodge = render_text(self.small, "[SHIFT] DODGE", TEXT if dodge_ready else DIM)
        rect = pygame.Rect(0, 0, attack.get_width() + dodge.get_width(),
                           max(attack.get_height(), dodge.get_height()))
        rect.inflate_ip(24, 14)
        rect.bottomright = (width - 14, height - 14)
        self._panel(rect, emphasized=True)
        left = rect.centerx - (attack.get_width() + dodge.get_width()) // 2
        self.screen.blit(attack, (left, rect.centery - attack.get_height() // 2))
        self.screen.blit(dodge, (left + attack.get_width(),
                                 rect.centery - dodge.get_height() // 2))

    def _panel(self, rect, emphasized=False):
        draw_panel(self.screen, rect, emphasized=emphasized, radius=7, alpha=225)

    def _profile_panel(self, rect, emphasized=False):
        draw_profile_frame(self.screen, rect, emphasized=emphasized)

    def _draw_clock_placeholder(self, x, y):
        pygame.draw.circle(self.screen, GOLD, (x, y), 10, 2)
        pygame.draw.line(self.screen, TEXT, (x, y), (x, y - 6), 2)
        pygame.draw.line(self.screen, TEXT, (x, y), (x + 5, y + 3), 2)
