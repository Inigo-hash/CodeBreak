import sys

import pygame

from src.settings_state import (
    MAX_FONT_SIZE, MIN_FONT_SIZE, ROWS, TEXT_SPEEDS, VOLUME_STEP,
    current_font_size, current_text_speed, current_theme_name,
    cycle_text_speed, cycle_theme, set_text_speed,
    set_font_size, settings_state, swatch_color,
)
from src.systems.audio import apply_music_volume, handle_music_shortcut, music_shortcut_label
from src.ui.theme import UI_COLORS, body_font, draw_button, draw_panel, title_font


HELP_COPY = {
    "font_size": "Use - / +, the arrow keys, or select the number and type a size from 12 to 28.",
    "text_speed": "Select Slow, Normal, or Instant to control how quickly dialogue appears.",
    "music": "Drag or click the slider, use - / +, or press Left / Right. F10 mutes or unmutes music.",
    "sfx": "Drag or click the slider, use - / +, or press Left / Right to set sound-effects volume.",
    "theme": "Use either arrow to change the coding editor's color combination.",
}


class SettingsPanel:
    """Accessible settings panel shared by the menu and pause screen."""

    def __init__(self, screen):
        self.screen = screen
        self.is_open = True
        self.dragging_music = self.dragging_sfx = False
        self.focus = 0

        # The focus ring exists so keyboard players can see which row the
        # arrow keys will change. A mouse user already knows - the pointer
        # is right there - so the ring stays hidden until an arrow key is
        # actually pressed, and a click puts it away again.
        self.keyboard_focus = False

        self.help_topic = None
        self.editing_font_size = False
        self.font_size_text = str(current_font_size())
        self._refresh_fonts()
        self._layout()

    def _refresh_fonts(self):
        self.title_font = title_font(30)
        self.label_font = body_font(17)
        self.option_font = body_font(14, bold=True)
        self.button_font = title_font(20)
        self.help_font = body_font(13)

    def _layout(self):
        width, height = self.screen.get_size()
        self.panel = pygame.Rect(0, 0, min(640, width - 40), min(690, height - 40))
        self.panel.center = (width // 2, height // 2)
        option_width = (self.panel.width - 76) // 3
        self.font_minus = pygame.Rect(self.panel.centerx - 104,
                                      self.panel.top + 105, 40, 34)
        self.font_input = pygame.Rect(self.panel.centerx - 54,
                                      self.panel.top + 105, 108, 34)
        self.font_plus = pygame.Rect(self.panel.centerx + 64,
                                     self.panel.top + 105, 40, 34)
        self.speed_rects = [
            pygame.Rect(self.panel.left + 28 + i * (option_width + 10),
                        self.panel.top + 185, option_width, 34)
            for i in range(len(TEXT_SPEEDS))
        ]
        self.music_bar = pygame.Rect(self.panel.left + 78, self.panel.top + 276,
                                     self.panel.width - 156, 20)
        self.sfx_bar = pygame.Rect(self.panel.left + 78, self.panel.top + 356,
                                   self.panel.width - 156, 20)
        self.music_minus = pygame.Rect(self.panel.left + 28, self.music_bar.top - 7, 38, 34)
        self.music_plus = pygame.Rect(self.panel.right - 66, self.music_bar.top - 7, 38, 34)
        self.sfx_minus = pygame.Rect(self.panel.left + 28, self.sfx_bar.top - 7, 38, 34)
        self.sfx_plus = pygame.Rect(self.panel.right - 66, self.sfx_bar.top - 7, 38, 34)
        arrow_y = self.panel.top + 455
        self.left_arrow = pygame.Rect(self.panel.left + 60, arrow_y, 40, 34)
        self.right_arrow = pygame.Rect(self.panel.right - 100, arrow_y, 40, 34)
        self.back_button = pygame.Rect(self.panel.centerx - 80, self.panel.bottom - 56, 160, 40)
        self.help_rects = {
            "font_size": pygame.Rect(self.panel.right - 58, self.panel.top + 70, 26, 26),
            "text_speed": pygame.Rect(self.panel.right - 58, self.panel.top + 150, 26, 26),
            "music": pygame.Rect(self.panel.right - 58, self.panel.top + 236, 26, 26),
            "sfx": pygame.Rect(self.panel.right - 58, self.panel.top + 316, 26, 26),
            "theme": pygame.Rect(self.panel.right - 58, self.panel.top + 413, 26, 26),
        }

    def open(self):
        self.is_open = True
        self.dragging_music = self.dragging_sfx = False

        # Opening the panel is not itself arrow-key navigation, so start
        # with no ring showing whichever way the player got here.
        self.keyboard_focus = False

    def close(self):
        self.is_open = False
        self.dragging_music = self.dragging_sfx = False
        self.keyboard_focus = False

    def handle_event(self, event):
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN:
            if self.editing_font_size:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._commit_font_size()
                elif event.key == pygame.K_ESCAPE:
                    self.editing_font_size = False
                    self.font_size_text = str(current_font_size())
                elif event.key == pygame.K_BACKSPACE:
                    self.font_size_text = self.font_size_text[:-1]
                elif event.unicode.isdigit() and len(self.font_size_text) < 2:
                    self.font_size_text += event.unicode
                return True
            return self._handle_key(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.keyboard_focus = False
            for topic, rect in self.help_rects.items():
                if rect.collidepoint(event.pos):
                    self.help_topic = None if self.help_topic == topic else topic
                    return True
            self.dragging_music = self.music_bar.collidepoint(event.pos)
            self.dragging_sfx = self.sfx_bar.collidepoint(event.pos)
            if self.dragging_music:
                self.focus = ROWS.index("music")
            elif self.dragging_sfx:
                self.focus = ROWS.index("sfx")
            if self.font_input.collidepoint(event.pos):
                self.editing_font_size = True
                self.font_size_text = ""
                self.focus = ROWS.index("font_size")
            elif self.font_minus.collidepoint(event.pos):
                self._change_font_size(-1)
            elif self.font_plus.collidepoint(event.pos):
                self._change_font_size(1)
            for index, rect in enumerate(self.speed_rects):
                if rect.collidepoint(event.pos):
                    set_text_speed(TEXT_SPEEDS[index])
                    self.focus = ROWS.index("text_speed")
            for rect, row, step in (
                (self.music_minus, "music", -1), (self.music_plus, "music", 1),
                (self.sfx_minus, "sfx", -1), (self.sfx_plus, "sfx", 1),
            ):
                if rect.collidepoint(event.pos):
                    self.focus = ROWS.index(row)
                    self._adjust(step)
            if self.left_arrow.collidepoint(event.pos):
                cycle_theme(-1)
                self.focus = ROWS.index("theme")
            elif self.right_arrow.collidepoint(event.pos):
                cycle_theme(1)
                self.focus = ROWS.index("theme")
            elif self.back_button.collidepoint(event.pos):
                self.close()
            self._update_volume(event.pos[0])
            return True
        if event.type == pygame.MOUSEMOTION:
            self._update_volume(event.pos[0])
            return self.dragging_music or self.dragging_sfx
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_music = self.dragging_sfx = False
            return True
        return False

    def _handle_key(self, event):
        if event.key == pygame.K_ESCAPE:
            self.close()
            return True
        if event.key in (pygame.K_UP, pygame.K_DOWN):
            step = -1 if event.key == pygame.K_UP else 1
            self.focus = (self.focus + step) % len(ROWS)
            self.keyboard_focus = True
            return True
        if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            self._adjust(-1 if event.key == pygame.K_LEFT else 1)
            self.keyboard_focus = True
            return True
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.close()
            return True
        return False

    def _adjust(self, step):
        row = ROWS[self.focus]
        if row == "font_size":
            self._change_font_size(step)
        elif row == "text_speed":
            cycle_text_speed(step)
        elif row == "theme":
            cycle_theme(step)
        else:
            key = "music_vol" if row == "music" else "sfx_vol"
            settings_state[key] = max(0.0, min(1.0, settings_state[key] + step * VOLUME_STEP))
            if row == "music":
                apply_music_volume()

    def _update_volume(self, mouse_x):
        if self.dragging_music:
            settings_state["music_vol"] = max(
                0.0, min(1.0, (mouse_x - self.music_bar.left) / self.music_bar.width)
            )
            apply_music_volume()
        if self.dragging_sfx:
            settings_state["sfx_vol"] = max(
                0.0, min(1.0, (mouse_x - self.sfx_bar.left) / self.sfx_bar.width)
            )

    def _change_font_size(self, step):
        set_font_size(current_font_size() + step)
        self.font_size_text = str(current_font_size())
        self.editing_font_size = False
        self._refresh_fonts()
        self.focus = ROWS.index("font_size")

    def _commit_font_size(self):
        if self.font_size_text:
            set_font_size(int(self.font_size_text))
        self.font_size_text = str(current_font_size())
        self.editing_font_size = False
        self._refresh_fonts()

    def draw(self):
        if not self.is_open:
            return
        width, height = self.screen.get_size()
        if self.panel.center != (width // 2, height // 2):
            self._layout()
        small = pygame.transform.smoothscale(
            self.screen, (max(1, width // 8), max(1, height // 8))
        )
        self.screen.blit(pygame.transform.smoothscale(small, (width, height)), (0, 0))
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        draw_panel(self.screen, self.panel, radius=9)
        self._text(self.title_font, "SETTINGS", UI_COLORS["gold"],
                   center=(self.panel.centerx, self.panel.top + 34))
        self._text(self.label_font, "FONT SIZE", UI_COLORS["text"],
                   (self.panel.left + 28, self.panel.top + 72))
        self._draw_font_size_input()
        self._text(self.label_font, "TEXT SPEED", UI_COLORS["text"],
                   (self.panel.left + 28, self.panel.top + 152))
        self._draw_choices(TEXT_SPEEDS, self.speed_rects, current_text_speed())
        self._draw_slider("MUSIC", self.music_bar, settings_state["music_vol"],
                          self.music_minus, self.music_plus)
        self._draw_slider("SOUND EFFECTS (SFX)", self.sfx_bar, settings_state["sfx_vol"],
                          self.sfx_minus, self.sfx_plus)
        self._text(self.label_font, "COLOR THEME", UI_COLORS["text"],
                   (self.panel.left + 28, self.panel.top + 415))
        for rect in (self.left_arrow, self.right_arrow):
            color = (60, 90, 130) if rect.collidepoint(pygame.mouse.get_pos()) else (50, 55, 70)
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
        pygame.draw.polygon(self.screen, UI_COLORS["blue_bright"], [
            (self.left_arrow.right - 8, self.left_arrow.top + 7),
            (self.left_arrow.right - 8, self.left_arrow.bottom - 7),
            (self.left_arrow.left + 6, self.left_arrow.centery),
        ])
        pygame.draw.polygon(self.screen, UI_COLORS["blue_bright"], [
            (self.right_arrow.left + 8, self.right_arrow.top + 7),
            (self.right_arrow.left + 8, self.right_arrow.bottom - 7),
            (self.right_arrow.right - 6, self.right_arrow.centery),
        ])
        theme = current_theme_name()
        self._text(self.button_font, theme, swatch_color(theme),
                   center=(self.panel.centerx, self.left_arrow.centery))
        self._draw_help_buttons()
        self._draw_focus_ring()
        self._draw_help_text()
        self._text(self.help_font,
                   f"Arrow keys work here too  |  {music_shortcut_label()}",
                   UI_COLORS["text_dim"], center=(self.panel.centerx, self.back_button.top - 18))
        draw_button(self.screen, self.back_button, "BACK", self.button_font,
                    hovered=self.back_button.collidepoint(pygame.mouse.get_pos()))

    def _draw_choices(self, names, rects, selected):
        mouse_pos = pygame.mouse.get_pos()
        for name, rect in zip(names, rects):
            active = name == selected
            fill = UI_COLORS["stone_light"] if active or rect.collidepoint(mouse_pos) else (34, 36, 46)
            pygame.draw.rect(self.screen, fill, rect, border_radius=4)
            pygame.draw.rect(self.screen,
                             UI_COLORS["gold"] if active else UI_COLORS["bronze_dark"],
                             rect, 2, border_radius=4)
            self._text(self.option_font, name,
                       UI_COLORS["text"] if active else UI_COLORS["text_dim"], center=rect.center)

    def _draw_font_size_input(self):
        for rect, symbol in ((self.font_minus, "-"), (self.font_plus, "+")):
            pygame.draw.rect(self.screen, UI_COLORS["stone_light"], rect, border_radius=4)
            pygame.draw.rect(self.screen, UI_COLORS["bronze"], rect, 2, border_radius=4)
            self._text(self.button_font, symbol, UI_COLORS["text"], center=rect.center)
        pygame.draw.rect(self.screen, (22, 24, 32), self.font_input, border_radius=4)
        pygame.draw.rect(
            self.screen,
            UI_COLORS["blue_bright"] if self.editing_font_size else UI_COLORS["gold"],
            self.font_input, 2, border_radius=4,
        )
        value = self.font_size_text if self.editing_font_size else str(current_font_size())
        self._text(self.option_font, value or "|", UI_COLORS["text"],
                   center=self.font_input.center)
        self._text(self.help_font, f"{MIN_FONT_SIZE}-{MAX_FONT_SIZE}",
                   UI_COLORS["text_dim"],
                   center=(self.panel.centerx, self.font_input.bottom + 7))

    def _draw_help_buttons(self):
        mouse = pygame.mouse.get_pos()
        for topic, rect in self.help_rects.items():
            active = self.help_topic == topic or rect.collidepoint(mouse)
            pygame.draw.circle(self.screen,
                               UI_COLORS["blue_bright"] if active else UI_COLORS["bronze"],
                               rect.center, 12)
            self._text(self.option_font, "?", UI_COLORS["stone_deep"], center=rect.center)

    def _draw_help_text(self):
        mouse = pygame.mouse.get_pos()
        hovered_topic = next(
            (name for name, rect in self.help_rects.items()
             if rect.collidepoint(mouse)),
            None,
        )
        topic = hovered_topic or self.help_topic
        if topic is None:
            self._text(
                self.help_font,
                "Hover or select a ? for help.",
                UI_COLORS["text_dim"],
                center=(self.panel.centerx, self.panel.top + 535),
            )
            return

        anchor = self.help_rects[topic]
        bubble_width = min(420, self.panel.width - 100)
        text_width = bubble_width - 28
        words = HELP_COPY[topic].split()
        lines, current = [], ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if not current or self.help_font.size(candidate)[0] <= text_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)

        line_height = self.help_font.get_height() + 4
        bubble = pygame.Rect(
            anchor.left - bubble_width - 14,
            anchor.centery - (len(lines) * line_height + 22) // 2,
            bubble_width,
            len(lines) * line_height + 22,
        )
        bubble.clamp_ip(self.panel.inflate(-24, -24))
        pygame.draw.rect(
            self.screen, (18, 21, 29), bubble,
            border_radius=7,
        )
        pygame.draw.rect(
            self.screen, UI_COLORS["blue_bright"], bubble, 2,
            border_radius=7,
        )
        pointer_y = max(bubble.top + 12, min(anchor.centery, bubble.bottom - 12))
        pygame.draw.polygon(
            self.screen, UI_COLORS["blue_bright"],
            ((bubble.right - 1, pointer_y - 7),
             (anchor.left - 3, anchor.centery),
             (bubble.right - 1, pointer_y + 7)),
        )
        for index, line in enumerate(lines):
            self._text(
                self.help_font, line, UI_COLORS["parchment"],
                (bubble.left + 14, bubble.top + 10 + index * line_height),
            )

    def _draw_focus_ring(self):
        # Keyboard-only affordance - see keyboard_focus in __init__.
        if not self.keyboard_focus:
            return
        row = ROWS[self.focus]
        if row == "font_size":
            target = self.font_minus.union(self.font_plus).inflate(8, 8)
        elif row == "text_speed":
            target = self.speed_rects[0].union(self.speed_rects[-1]).inflate(8, 8)
        elif row == "music":
            target = self.music_minus.union(self.music_plus).inflate(8, 8)
        elif row == "sfx":
            target = self.sfx_minus.union(self.sfx_plus).inflate(8, 8)
        else:
            target = self.left_arrow.union(self.right_arrow).inflate(10, 10)
        pygame.draw.rect(self.screen, UI_COLORS["blue_bright"], target, 2, border_radius=5)

    def _draw_slider(self, label, bar, value, minus, plus):
        self._text(self.label_font, label, UI_COLORS["text"], (bar.left, bar.top - 38))
        pygame.draw.rect(self.screen, UI_COLORS["stone_deep"], bar, border_radius=5)
        fill = bar.copy()
        fill.width = max(0, round(bar.width * value))
        pygame.draw.rect(self.screen, UI_COLORS["blue"], fill, border_radius=5)
        knob_x = bar.left + int((bar.width - 18) * value)
        pygame.draw.rect(self.screen, UI_COLORS["gold"],
                         (knob_x, bar.top - 4, 18, 28), border_radius=4)
        for rect, symbol in ((minus, "-"), (plus, "+")):
            pygame.draw.rect(self.screen, UI_COLORS["stone_light"], rect, border_radius=4)
            pygame.draw.rect(self.screen, UI_COLORS["bronze"], rect, 2, border_radius=4)
            self._text(self.button_font, symbol, UI_COLORS["text"], center=rect.center)
        self._text(self.help_font, f"{round(value * 100)}%", UI_COLORS["text_dim"],
                   (bar.right - 36, bar.top - 38))

    def _text(self, font, value, color, position=None, center=None):
        rendered = font.render(value, True, color)
        self.screen.blit(rendered, rendered.get_rect(center=center) if center else position)


def settings_screen(screen):
    panel = SettingsPanel(screen)
    clock = pygame.time.Clock()
    while panel.is_open:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if handle_music_shortcut(event):
                continue
            panel.handle_event(event)
        panel.draw()
        pygame.display.flip()
        clock.tick(60)
