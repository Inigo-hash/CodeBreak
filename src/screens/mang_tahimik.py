"""Paused Pygame chat modal using the existing Mang Tahimik portrait."""
import pygame
from src.systems.ai_tutor import MAX_QUESTION, TutorSession
from src.ui.theme import body_font, title_font, UI_COLORS


def wrap_lines(text, font, width):
    # Preserve code whitespace and split long tokens as well as prose.
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for char in paragraph:
            if line and font.size(line + char)[0] > width:
                lines.append(line)
                line = ''
            line += char
        lines.append(line)
    return lines


class MangTahimikChat:
    def __init__(self, screen, context=None, session=None):
        self.screen = screen
        self.context = context or {}
        self.session = session or TutorSession()
        self.background = screen.copy()
        self.messages = [('Mang Tahimik', 'May tanong ka ba tungkol sa Python? I can explain concepts and give hints.')]
        self.question = ''
        self.scroll = 0
        self.font = body_font(17)
        self.heading = title_font(26)
        self.portrait = None
        try:
            self.portrait = pygame.transform.smoothscale(pygame.image.load(
                'assets/images/characters/mang_tahimik/portrait.png').convert_alpha(), (54, 54))
        except (pygame.error, FileNotFoundError):
            pass

    def submit(self):
        if self.session.submit(self.question, self.context):
            self.messages.append(('You', self.question.strip()))
            self.messages = self.messages[-20:]
            self.question = ''
            self.scroll = 0

    def draw(self):
        w, h = self.screen.get_size()
        panel = pygame.Rect(0, 0, min(880, w - 24), h - 24)
        panel.center = (w // 2, h // 2)
        self.screen.blit(self.background, (0, 0))
        pygame.draw.rect(self.screen, UI_COLORS['modal_panel'], panel, border_radius=10)
        pygame.draw.rect(self.screen, UI_COLORS['gold'], panel, 2, border_radius=10)
        if self.portrait:
            self.screen.blit(self.portrait, (panel.x + 16, panel.y + 12))
        self.screen.blit(self.heading.render('Mang Tahimik', True, UI_COLORS['gold']), (panel.x + 82, panel.y + 20))
        view = pygame.Rect(panel.x + 20, panel.y + 78, panel.w - 40, panel.h - 210)
        rows = []
        for name, message in self.messages:
            rows.append((name + ':', UI_COLORS['gold']))
            rows.extend((line, UI_COLORS['text']) for line in wrap_lines(message, self.font, view.w - 16))
            rows.append(('', UI_COLORS['text']))
        line_h = self.font.get_linesize() + 3
        max_scroll = max(0, len(rows) * line_h - view.h)
        self.scroll = max(0, min(self.scroll, max_scroll))
        old_clip = self.screen.get_clip()
        self.screen.set_clip(view)
        y = view.y - max_scroll + self.scroll
        for line, color in rows:
            self.screen.blit(self.font.render(line, True, color), (view.x, y))
            y += line_h
        self.screen.set_clip(old_clip)
        entry = pygame.Rect(panel.x + 20, panel.bottom - 116, panel.w - 124, 66)
        self.send_rect = pygame.Rect(entry.right + 8, entry.y, 76, 66)
        pygame.draw.rect(self.screen, UI_COLORS['modal_inner'], entry, border_radius=5)
        pygame.draw.rect(self.screen, UI_COLORS['button_fill'], self.send_rect, border_radius=5)
        self.screen.blit(self.font.render('Ask', True, UI_COLORS['gold']), (self.send_rect.x + 16, self.send_rect.y + 20))
        old_clip = self.screen.get_clip()
        self.screen.set_clip(entry.inflate(-12, -8))
        lines = wrap_lines(self.question or 'Ask about Python...', self.font, entry.w - 16)
        for i, line in enumerate(lines[-2:]):
            self.screen.blit(self.font.render(line, True, UI_COLORS['text']), (entry.x + 8, entry.y + 7 + i * line_h))
        self.screen.set_clip(old_clip)
        status = 'Thinking... You can press ESC to return.' if self.session.pending else 'Enter: ask | Esc: return | Mouse wheel: scroll'
        self.screen.blit(self.font.render(status, True, UI_COLORS['text_dim']), (panel.x + 20, panel.bottom - 38))

    def run(self):
        clock = pygame.time.Clock()
        pygame.key.start_text_input()
        try:
            while True:
                self.draw()
                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        raise SystemExit
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            return
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            self.submit()
                        elif event.key == pygame.K_BACKSPACE:
                            self.question = self.question[:-1]
                    elif event.type == pygame.TEXTINPUT:
                        self.question = (self.question + event.text)[:MAX_QUESTION]
                    elif event.type == pygame.MOUSEWHEEL:
                        self.scroll += event.y * 60
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if self.send_rect.collidepoint(event.pos):
                            self.submit()
                answer = self.session.poll()
                if answer is not None:
                    self.messages.append(('Mang Tahimik', answer))
                    self.messages = self.messages[-20:]
                    self.scroll = 0
                clock.tick(60)
        finally:
            pygame.key.stop_text_input()


def open_mang_tahimik(screen, context=None):
    MangTahimikChat(screen, context).run()
