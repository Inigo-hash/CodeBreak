"""Responsive, reusable stage-loading presentation for CodeBreak."""

from __future__ import annotations

import math
import random
import sys

import pygame

from src.ui.theme import UI_COLORS, body_font, title_font


REFERENCE_SIZE = (1920, 1080)
MIN_VISIBLE_MS = 280

STAGE_BACKGROUNDS = {
    "island": "assets/images/backgrounds/loading_island_stage1.png",
}

BEGINNER_TIPS = (
    {"text": "print() displays information on the screen.",
     "code": 'print("Hello, explorer!")'},
    {"text": "input() lets your program receive user input.",
     "code": 'name = input("Name: ")'},
    {"text": "Variables store values that can be reused later.",
     "code": "player_hp = 100"},
    {"text": "Strings are text surrounded by quotation marks.",
     "code": 'island_name = "Mactan"'},
    {"text": "A single = assigns a value, while == compares values.",
     "code": "gate_open = keys == 5"},
    {"text": "if statements allow programs to make decisions.",
     "code": "if keys == 5:"},
    {"text": "Indentation shows which Python statements belong together.",
     "code": "    open_gate()"},
    {"text": "int() converts compatible values into integers.",
     "code": 'age = int("18")'},
    {"text": "Comments in Python begin with #.",
     "code": "# Search the island"},
    {"text": "Meaningful variable names make code easier to understand.",
     "code": "remaining_enemies = 3"},
)

STAGE_TIPS = {
    "island": BEGINNER_TIPS,
}

_BACKGROUND_CACHE = {}
_LOGO_CACHE = {}
_PARCHMENT_CACHE = {}


def loading_layout(size):
    """Return reference-scaled rectangles used by drawing and tests."""

    width, height = size
    scale = min(width / REFERENCE_SIZE[0], height / REFERENCE_SIZE[1])
    margin = max(18, round(42 * scale))

    note_width = min(width - margin * 2, round(720 * scale))
    note_height = max(172, round(270 * scale))
    note = pygame.Rect(0, 0, note_width, note_height)
    note.centerx = width // 2
    note.top = round(height * 0.365)

    bar_width = min(width - margin * 4, round(760 * scale))
    bar_height = max(20, round(34 * scale))
    bar = pygame.Rect(0, 0, bar_width, bar_height)
    bar.centerx = width // 2
    bar.top = round(height * 0.855)

    status_y = bar.top - max(28, round(46 * scale))
    return {
        "scale": scale,
        "safe": pygame.Rect(margin, margin, width - margin * 2,
                            height - margin * 2),
        "note": note,
        "bar": bar,
        "status_y": status_y,
    }


class StageLoadingScreen:
    """Lightweight presenter updated by real stage-initialization phases."""

    def __init__(self, screen, stage_id="island", stage_name="Island",
                 stage_label="Stage 1", tips=None, background=None,
                 previous_frame=None, seed=None):
        self.screen = screen
        self.size = screen.get_size()
        self.stage_id = str(stage_id or "island").lower()
        self.stage_name = str(stage_name or "Island")
        self.stage_label = str(stage_label or "Stage 1")
        self.progress = 0
        self.status = "Preparing expedition..."
        self.started_at = pygame.time.get_ticks()
        self.previous_frame = (previous_frame.copy() if previous_frame is not None
                               else screen.copy())

        choices = tuple(tips or STAGE_TIPS.get(self.stage_id, BEGINNER_TIPS))
        rng = random.Random(seed) if seed is not None else random.SystemRandom()
        self.tip = rng.choice(choices)
        self._ambient_seed = random.Random(f"{self.stage_id}:{self.tip['code']}")
        self.fireflies = [
            (self._ambient_seed.random(), self._ambient_seed.random(),
             self._ambient_seed.uniform(0, math.tau),
             self._ambient_seed.uniform(0.65, 1.25))
            for _ in range(22)
        ]

        self.layout = loading_layout(self.size)
        self._build_fonts()
        self.background = self._load_background(background)
        self.logo = self._load_logo()
        self.parchment = self._build_parchment(self.layout["note"].size)
        self.night_overlay = pygame.Surface(self.size, pygame.SRCALPHA)
        self.night_overlay.fill((2, 7, 18, 82))
        self.firefly_layer = pygame.Surface(self.size, pygame.SRCALPHA)
        self._fade_from_previous()
        self.update(0, "Preparing expedition...")

    def _build_fonts(self):
        scale = self.layout["scale"]
        self.stage_font = title_font(max(16, round(28 * scale)))
        self.note_title_font = title_font(max(15, round(21 * scale)))
        self.note_font = body_font(max(16, round(23 * scale)))
        self.code_font = body_font(max(17, round(25 * scale)), bold=True)
        self.status_font = body_font(max(15, round(22 * scale)))
        self.percent_font = title_font(max(15, round(22 * scale)))

    def _load_background(self, background):
        source = background or STAGE_BACKGROUNDS.get(
            self.stage_id, "assets/images/backgrounds/mainMenuBg1.png"
        )
        cache_key = (source, self.size) if isinstance(source, str) else None
        if cache_key in _BACKGROUND_CACHE:
            return _BACKGROUND_CACHE[cache_key]
        try:
            image = (pygame.image.load(source).convert()
                     if isinstance(source, str) else source.convert())
        except (FileNotFoundError, pygame.error, AttributeError):
            image = pygame.Surface(self.size)
            image.fill((4, 11, 22))
        result = self._cover_scale(image, self.size)
        if cache_key is not None:
            _BACKGROUND_CACHE[cache_key] = result
        return result

    @staticmethod
    def _cover_scale(image, size):
        width, height = size
        factor = max(width / image.get_width(), height / image.get_height())
        scaled_size = (max(1, round(image.get_width() * factor)),
                       max(1, round(image.get_height() * factor)))
        scaled = pygame.transform.scale(image, scaled_size)
        crop = pygame.Rect(0, 0, width, height)
        crop.center = scaled.get_rect().center
        return scaled.subsurface(crop).copy()

    def _load_logo(self):
        target_width = min(round(self.size[0] * 0.36),
                           round(620 * self.layout["scale"]))
        if target_width in _LOGO_CACHE:
            return _LOGO_CACHE[target_width]
        try:
            logo = pygame.image.load(
                "assets/images/logos/codebreakLogo.png"
            ).convert_alpha()
            bounds = logo.get_bounding_rect(min_alpha=8)
            if bounds.width and bounds.height:
                logo = logo.subsurface(bounds).copy()
            target_height = max(1, round(logo.get_height()
                                         * target_width / logo.get_width()))
            result = pygame.transform.smoothscale(
                logo, (target_width, target_height)
            )
            _LOGO_CACHE[target_width] = result
            return result
        except (FileNotFoundError, pygame.error):
            return None

    @staticmethod
    def _build_parchment(size):
        if size in _PARCHMENT_CACHE:
            return _PARCHMENT_CACHE[size]
        surface = pygame.Surface(size, pygame.SRCALPHA)
        rect = surface.get_rect()
        pygame.draw.rect(surface, (195, 157, 103, 246), rect, border_radius=7)
        pygame.draw.rect(surface, (226, 194, 139, 225), rect.inflate(-10, -10),
                         border_radius=5)
        rng = random.Random(713)
        for _ in range(max(30, rect.width * rect.height // 1800)):
            x, y = rng.randrange(rect.width), rng.randrange(rect.height)
            color = rng.choice(((90, 58, 29, 22), (255, 231, 177, 18)))
            pygame.draw.circle(surface, color, (x, y), rng.choice((1, 1, 2)))
        pygame.draw.rect(surface, UI_COLORS["bronze_dark"], rect, 3,
                         border_radius=7)
        pygame.draw.rect(surface, (80, 48, 22), rect.inflate(-10, -10), 1,
                         border_radius=4)
        _PARCHMENT_CACHE[size] = surface
        return surface

    def _pump_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def _fade_from_previous(self):
        clock = pygame.time.Clock()
        duration = 120
        started = pygame.time.get_ticks()
        veil = pygame.Surface(self.size)
        veil.fill((0, 0, 0))
        while True:
            elapsed = pygame.time.get_ticks() - started
            amount = min(1.0, elapsed / duration)
            self.screen.blit(self.previous_frame, (0, 0))
            veil.set_alpha(round(255 * amount))
            self.screen.blit(veil, (0, 0))
            pygame.display.flip()
            self._pump_events()
            if amount >= 1.0:
                break
            clock.tick(60)

    @staticmethod
    def _wrap(font, text, max_width):
        lines, current = [], ""
        for word in text.split():
            candidate = f"{current} {word}".strip()
            if not current or font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def update(self, progress, status):
        """Report one completed real loading phase and repaint immediately."""

        self.progress = max(self.progress, min(100, round(progress)))
        self.status = str(status)
        self._pump_events()
        self.draw()
        pygame.display.flip()

    def draw(self):
        width, height = self.size
        scale = self.layout["scale"]
        self.screen.blit(self.background, (0, 0))

        self.screen.blit(self.night_overlay, (0, 0))
        self._draw_fireflies()

        border = self.layout["safe"]
        pygame.draw.rect(self.screen, UI_COLORS["bronze_dark"], border, 2,
                         border_radius=max(3, round(5 * scale)))
        pygame.draw.line(self.screen, UI_COLORS["gold"],
                         (border.left + round(35 * scale), border.top),
                         (border.right - round(35 * scale), border.top), 1)

        if self.logo is not None:
            logo_rect = self.logo.get_rect(
                midtop=(width // 2, max(8, round(16 * scale)))
            )
            self.screen.blit(self.logo, logo_rect)
            stage_y = logo_rect.bottom + max(4, round(8 * scale))
        else:
            fallback = title_font(max(34, round(58 * scale))).render(
                "CODEBREAK", True, UI_COLORS["gold"]
            )
            fallback_rect = fallback.get_rect(
                midtop=(width // 2, max(12, round(30 * scale)))
            )
            self.screen.blit(fallback, fallback_rect)
            stage_y = fallback_rect.bottom + max(8, round(14 * scale))

        stage_text = f"{self.stage_name.upper()}  —  {self.stage_label.upper()}"
        stage = self.stage_font.render(stage_text, True, UI_COLORS["parchment"])
        self.screen.blit(stage, stage.get_rect(midtop=(width // 2, stage_y)))

        self._draw_note()
        self._draw_progress()

    def _draw_fireflies(self):
        now = pygame.time.get_ticks() / 1000.0
        width, height = self.size
        layer = self.firefly_layer
        layer.fill((0, 0, 0, 0))
        for nx, ny, phase, speed in self.fireflies:
            x = round(nx * width + math.sin(now * speed + phase) * 5)
            y = round(ny * height + math.cos(now * speed * 0.7 + phase) * 3)
            alpha = round(38 + 72 * (0.5 + 0.5 * math.sin(now * speed + phase)))
            pygame.draw.circle(layer, (245, 183, 67, alpha), (x, y), 1)
        self.screen.blit(layer, (0, 0))

    def _draw_note(self):
        rect = self.layout["note"]
        scale = self.layout["scale"]
        self.screen.blit(self.parchment, rect)

        header_width = min(rect.width - 28, round(330 * scale))
        header = pygame.Rect(0, 0, header_width, max(32, round(46 * scale)))
        header.midtop = (rect.centerx, rect.top + max(8, round(10 * scale)))
        pygame.draw.rect(self.screen, UI_COLORS["stone_deep"], header,
                         border_radius=5)
        pygame.draw.rect(self.screen, UI_COLORS["bronze"], header, 2,
                         border_radius=5)
        label = self.note_title_font.render(
            "EXPLORER'S NOTE", True, UI_COLORS["gold"]
        )
        self.screen.blit(label, label.get_rect(center=header.center))

        pad = max(24, round(38 * scale))
        text_top = header.bottom + max(12, round(18 * scale))
        lines = self._wrap(self.note_font, self.tip["text"], rect.width - pad * 2)
        line_height = self.note_font.get_height() + max(3, round(5 * scale))
        for index, line in enumerate(lines[:2]):
            rendered = self.note_font.render(line, True, (42, 29, 18))
            self.screen.blit(rendered, (rect.left + pad,
                                        text_top + index * line_height))

        code_height = max(42, round(66 * scale))
        code_rect = pygame.Rect(rect.left + pad, rect.bottom - code_height - pad // 2,
                                rect.width - pad * 2, code_height)
        pygame.draw.rect(self.screen, (12, 15, 20), code_rect, border_radius=4)
        pygame.draw.rect(self.screen, UI_COLORS["bronze_dark"], code_rect, 2,
                         border_radius=4)
        code = self.code_font.render(self.tip["code"], True, (130, 202, 95))
        self.screen.blit(code, code.get_rect(center=code_rect.center))

    def _draw_progress(self):
        bar = self.layout["bar"]
        status = self.status_font.render(self.status, True, UI_COLORS["parchment"])
        self.screen.blit(status, status.get_rect(
            center=(self.size[0] // 2, self.layout["status_y"])
        ))

        outer = bar.inflate(10, 10)
        pygame.draw.rect(self.screen, (7, 10, 16), outer, border_radius=5)
        pygame.draw.rect(self.screen, UI_COLORS["bronze"], outer, 2,
                         border_radius=5)
        pygame.draw.rect(self.screen, UI_COLORS["stone_deep"], bar,
                         border_radius=3)
        inner = bar.inflate(-6, -6)
        fill = inner.copy()
        fill.width = round(inner.width * self.progress / 100)
        if fill.width:
            pygame.draw.rect(self.screen, UI_COLORS["blue"], fill,
                             border_radius=2)
            highlight = fill.copy()
            highlight.height = max(1, fill.height // 3)
            pygame.draw.rect(self.screen, UI_COLORS["blue_bright"], highlight,
                             border_radius=2)

        percent = self.percent_font.render(
            f"{self.progress}%", True, UI_COLORS["gold"]
        )
        self.screen.blit(percent, percent.get_rect(center=bar.center))

    def finish(self):
        """Show the completed phase briefly, then fade cleanly to gameplay."""

        self.update(100, "Ready to explore.")
        clock = pygame.time.Clock()
        while pygame.time.get_ticks() - self.started_at < MIN_VISIBLE_MS:
            self._pump_events()
            self.draw()
            pygame.display.flip()
            clock.tick(60)

        final_frame = self.screen.copy()
        veil = pygame.Surface(self.size)
        veil.fill((0, 0, 0))
        started = pygame.time.get_ticks()
        duration = 150
        while True:
            elapsed = pygame.time.get_ticks() - started
            amount = min(1.0, elapsed / duration)
            self.screen.blit(final_frame, (0, 0))
            veil.set_alpha(round(255 * amount))
            self.screen.blit(veil, (0, 0))
            pygame.display.flip()
            self._pump_events()
            if amount >= 1.0:
                break
            clock.tick(60)
