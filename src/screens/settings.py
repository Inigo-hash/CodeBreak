import sys
import pygame

from src.settings_state import current_theme_name, cycle_theme, settings_state, swatch_color


class SettingsPanel:
    """The shared Settings panel used by every screen."""

    def __init__(self, screen):
        self.screen = screen
        self.is_open = True
        self.dragging_music = self.dragging_sfx = False
        self.title_font = pygame.font.SysFont("consolas", 32, bold=True)
        self.label_font = pygame.font.SysFont("consolas", 18)
        self.button_font = pygame.font.SysFont("consolas", 22, bold=True)
        self._layout()

    def _layout(self):
        width, height = self.screen.get_size()
        self.panel = pygame.Rect(0, 0, min(380, width - 40), min(480, height - 40))
        self.panel.center = (width // 2, height // 2)
        self.music_bar = pygame.Rect(self.panel.left + 28, self.panel.top + 160, self.panel.width - 56, 14)
        self.sfx_bar = pygame.Rect(self.panel.left + 28, self.panel.top + 240, self.panel.width - 56, 14)
        arrow_y = self.panel.top + 350
        self.left_arrow = pygame.Rect(self.panel.left + 60, arrow_y, 40, 28)
        self.right_arrow = pygame.Rect(self.panel.right - 100, arrow_y, 40, 28)
        self.back_button = pygame.Rect(self.panel.centerx - 70, self.panel.bottom - 56, 140, 36)

    def open(self):
        self.is_open = True
        self.dragging_music = self.dragging_sfx = False

    def close(self):
        self.is_open = False
        self.dragging_music = self.dragging_sfx = False

    def handle_event(self, event):
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.dragging_music = self.music_bar.collidepoint(event.pos)
            self.dragging_sfx = self.sfx_bar.collidepoint(event.pos)
            if self.left_arrow.collidepoint(event.pos):
                cycle_theme(-1)
            elif self.right_arrow.collidepoint(event.pos):
                cycle_theme(1)
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

    def _update_volume(self, mouse_x):
        if self.dragging_music:
            settings_state["music_vol"] = max(0.0, min(1.0, (mouse_x - self.music_bar.left) / self.music_bar.width))
            pygame.mixer.music.set_volume(settings_state["music_vol"])
        if self.dragging_sfx:
            settings_state["sfx_vol"] = max(0.0, min(1.0, (mouse_x - self.sfx_bar.left) / self.sfx_bar.width))

    def draw(self):
        if not self.is_open:
            return
        width, height = self.screen.get_size()
        if self.panel.center != (width // 2, height // 2):
            self._layout()
        small = pygame.transform.smoothscale(self.screen, (max(1, width // 8), max(1, height // 8)))
        self.screen.blit(pygame.transform.smoothscale(small, (width, height)), (0, 0))
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        pygame.draw.rect(self.screen, (36, 38, 48), self.panel)
        pygame.draw.rect(self.screen, (90, 94, 110), self.panel, 4)
        pygame.draw.rect(self.screen, (26, 28, 36), self.panel.inflate(-24, -24))
        self._text(self.title_font, "SETTINGS", (255, 255, 255), center=(self.panel.centerx, self.panel.top + 34))
        self._text(self.label_font, "TEXT SPEED", (200, 200, 210), (self.panel.left + 28, self.panel.top + 70))
        self._text(self.label_font, "SLOW    NORMAL    INSTANT", (160, 170, 190), (self.panel.left + 28, self.panel.top + 96))
        self._draw_slider("MUSIC", self.music_bar, settings_state["music_vol"])
        self._draw_slider("SFX", self.sfx_bar, settings_state["sfx_vol"])
        self._text(self.label_font, "COLOR THEME", (200, 200, 210), (self.panel.left + 28, self.panel.top + 300))
        for rect in (self.left_arrow, self.right_arrow):
            color = (60, 90, 130) if rect.collidepoint(pygame.mouse.get_pos()) else (50, 55, 70)
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
        pygame.draw.polygon(self.screen, (80, 180, 255), [(self.left_arrow.right - 8, self.left_arrow.top + 6), (self.left_arrow.right - 8, self.left_arrow.bottom - 6), (self.left_arrow.left + 6, self.left_arrow.centery)])
        pygame.draw.polygon(self.screen, (80, 180, 255), [(self.right_arrow.left + 8, self.right_arrow.top + 6), (self.right_arrow.left + 8, self.right_arrow.bottom - 6), (self.right_arrow.right - 6, self.right_arrow.centery)])
        theme = current_theme_name()
        self._text(self.button_font, theme, swatch_color(theme), center=(self.panel.centerx, self.left_arrow.centery))
        pygame.draw.rect(self.screen, (24, 25, 31), self.back_button, border_radius=4)
        pygame.draw.rect(self.screen, (62, 68, 82), self.back_button, 2, border_radius=4)
        self._text(self.button_font, "BACK", (255, 255, 255), center=self.back_button.center)

    def _draw_slider(self, label, bar, value):
        self._text(self.label_font, label, (200, 200, 210), (bar.left, bar.top - 20))
        pygame.draw.rect(self.screen, (30, 32, 40), bar, border_radius=4)
        knob_x = bar.left + int((bar.width - 16) * value)
        pygame.draw.rect(self.screen, (255, 220, 120), (knob_x, bar.top - 2, 16, 18), border_radius=3)

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
            panel.handle_event(event)
        panel.draw()
        pygame.display.flip()
        clock.tick(60)
