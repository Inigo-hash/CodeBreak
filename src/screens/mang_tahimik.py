"""Paused Pygame chat modal using the existing Mang Tahimik portrait."""
import re
from functools import lru_cache
import pygame
from src.systems.ai_tutor import MAX_QUESTION, TutorSession
from src.ui.theme import body_font, title_font, UI_COLORS
from src.ui.text_layout import fit_text


@lru_cache(maxsize=1)
def _helper_portrait():
    try:
        return pygame.image.load('assets/images/characters/mang_tahimik/portrait.png').convert_alpha()
    except (pygame.error, FileNotFoundError):
        return None


def tutor_helper_rect(screen, editor_panel=None):
    w, h = screen.get_size()
    if editor_panel is not None:
        side_width = w - editor_panel.right - 24
        if side_width >= 180:
            return pygame.Rect(editor_panel.right + 12, editor_panel.bottom - 110, min(230, side_width), 100)
        return pygame.Rect(editor_panel.right - 214, editor_panel.bottom - 60, 198, 44)
    return pygame.Rect(w - 250, h - 172, 230, 100)


def draw_tutor_helper(screen, rect, shortcut='H'):
    pygame.draw.rect(screen, UI_COLORS['modal_inner'], rect, border_radius=8)
    pygame.draw.rect(screen, UI_COLORS['gold'], rect, 1, border_radius=8)
    compact = rect.h < 60
    portrait_size = 34 if compact else 64
    portrait = _helper_portrait()
    if portrait:
        screen.blit(pygame.transform.smoothscale(portrait, (portrait_size, portrait_size)),
                    (rect.x + 8, rect.centery - portrait_size // 2))
    text_x = rect.x + portrait_size + 16
    text_w = rect.right - text_x - 8
    name = fit_text(title_font(18), 'Mang Tahimik', UI_COLORS['gold'], (text_w, 24))
    hint = fit_text(body_font(16), f'[{shortcut}] Chat', UI_COLORS['text'], (text_w, 22))
    screen.blit(name, (text_x, rect.centery - 23))
    screen.blit(hint, (text_x, rect.centery + 3))


def wrap_lines(text, font, width, word_wrap=True):
    # Keep words intact; only split tokens wider than a whole line.
    # Retain whitespace so code indentation and input cursor offsets survive.
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        tokens = re.findall(r'\s+|\S+', paragraph) if word_wrap else paragraph
        for token in tokens:
            if (word_wrap and not token.isspace() and line
                    and font.size(token)[0] <= width
                    and font.size(line + token)[0] > width):
                lines.append(line)
                line = ''
            for char in token:
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
        # Cache a softened snapshot once; the chat itself stays crisp.
        w, h = screen.get_size()
        small = pygame.transform.smoothscale(screen, (max(1, w // 6), max(1, h // 6)))
        self.background = pygame.transform.smoothscale(small, (w, h))
        shade = pygame.Surface((w, h), pygame.SRCALPHA)
        shade.fill((8, 12, 20, 65))
        self.background.blit(shade, (0, 0))
        self.messages = [('Mang Tahimik', 'May tanong ka ba tungkol sa Python? I can explain concepts and give hints.')]
        self.question = ''
        self.cursor = 0
        self.anchor = 0
        self.undo = []
        self.redo = []
        self.drag_scroll = None
        self.scroll_track = pygame.Rect(0, 0, 0, 0)
        self.scroll_thumb = self.scroll_track.copy()
        self.max_scroll = 0
        self.scroll = 0
        self.font = body_font(17)
        self.heading = title_font(26)
        self.caret_reset = pygame.time.get_ticks()
        self.portrait = None
        try:
            self.portrait = pygame.transform.smoothscale(pygame.image.load(
                'assets/images/characters/mang_tahimik/portrait.png').convert_alpha(), (54, 54))
        except (pygame.error, FileNotFoundError):
            pass

    def replace_selection(self, text):
        self.cursor = min(self.cursor, len(self.question))
        self.anchor = min(self.anchor, len(self.question))
        start, end = sorted((self.cursor, self.anchor))
        text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ').replace('\t', '    ')
        text = text[:max(0, MAX_QUESTION - len(self.question) + end - start)]
        self.undo.append((self.question, self.cursor, self.anchor))
        self.undo = self.undo[-100:]
        self.redo.clear()
        self.question = self.question[:start] + text + self.question[end:]
        self.cursor = self.anchor = start + len(text)
        self.caret_reset = pygame.time.get_ticks()

    def handle_key(self, event):
        mod = getattr(event, 'mod', 0)
        ctrl, shift = bool(mod & pygame.KMOD_CTRL), bool(mod & pygame.KMOD_SHIFT)
        self.cursor = min(self.cursor, len(self.question))
        self.anchor = min(self.anchor, len(self.question))
        start, end = sorted((self.cursor, self.anchor))
        if ctrl and event.key == pygame.K_a:
            self.anchor, self.cursor = 0, len(self.question)
        elif ctrl and event.key in (pygame.K_c, pygame.K_x, pygame.K_v):
            try:
                if not pygame.scrap.get_init():
                    pygame.scrap.init()
                if event.key == pygame.K_v:
                    data = pygame.scrap.get(pygame.SCRAP_TEXT)
                    if data:
                        self.replace_selection(data.decode('utf-8', errors='replace').rstrip('\x00'))
                elif start != end:
                    pygame.scrap.put(pygame.SCRAP_TEXT, (self.question[start:end] + '\x00').encode('utf-8'))
                    if event.key == pygame.K_x:
                        self.replace_selection('')
            except pygame.error:
                pass
        elif ctrl and event.key in (pygame.K_z, pygame.K_y):
            source, target = (self.redo, self.undo) if event.key == pygame.K_y or shift else (self.undo, self.redo)
            if source:
                target.append((self.question, self.cursor, self.anchor))
                self.question, self.cursor, self.anchor = source.pop()
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_HOME, pygame.K_END):
            if event.key == pygame.K_HOME:
                self.cursor = 0
            elif event.key == pygame.K_END:
                self.cursor = len(self.question)
            elif start != end and not shift:
                self.cursor = start if event.key == pygame.K_LEFT else end
            else:
                self.cursor = max(0, min(len(self.question), self.cursor + (-1 if event.key == pygame.K_LEFT else 1)))
                if ctrl:
                    direction = -1 if event.key == pygame.K_LEFT else 1
                    while 0 < self.cursor < len(self.question) and not self.question[self.cursor - (direction < 0)].isspace():
                        self.cursor += direction
            if not shift:
                self.anchor = self.cursor
        elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
            if start == end:
                self.anchor = max(0, self.cursor - 1) if event.key == pygame.K_BACKSPACE else min(len(self.question), self.cursor + 1)
            self.replace_selection('')
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.submit()
        self.caret_reset = pygame.time.get_ticks()

    def drag_scroll_to(self, y):
        travel = self.scroll_track.h - self.scroll_thumb.h
        if travel > 0:
            fraction = max(0, min(1, (y - self.scroll_track.y - self.drag_scroll) / travel))
            self.scroll = (1 - fraction) * self.max_scroll

    def submit(self):
        if self.session.submit(self.question, self.context):
            self.messages.append(('You', self.question.strip()))
            self.messages = self.messages[-20:]
            self.question = ''
            self.cursor = self.anchor = 0
            self.undo.clear()
            self.redo.clear()
            self.scroll = 0
            self.caret_reset = pygame.time.get_ticks()

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
        view = pygame.Rect(panel.x + 20, panel.y + 78, panel.w - 60, panel.h - 210)
        cards = []
        line_h = self.font.get_linesize() + 3
        for name, message in self.messages:
            lines = wrap_lines(message, self.font, view.w - 64)
            width = min(view.w - 32, max(160, max(self.font.size(line)[0] for line in lines) + 24))
            cards.append((name, lines, width, (len(lines) + 1) * line_h + 24))
        if self.session.pending:
            cards.append(('Mang Tahimik', [], min(view.w - 32, 300), 2 * line_h + 24))
        total_h = sum(card[3] + 14 for card in cards)
        max_scroll = max(0, total_h - view.h)
        self.max_scroll = max_scroll
        self.scroll = max(0, min(self.scroll, max_scroll))
        old_clip = self.screen.get_clip()
        self.screen.set_clip(view)
        y = view.y - max_scroll + self.scroll
        for name, lines, width, height in cards:
            is_user = name == 'You'
            accent = UI_COLORS['blue_bright'] if is_user else UI_COLORS['gold']
            x = view.right - width if is_user else view.x
            bubble = pygame.Rect(x, y, width, height)
            pygame.draw.rect(self.screen, (30, 49, 68) if is_user else UI_COLORS['modal_inner'], bubble, border_radius=10)
            pygame.draw.rect(self.screen, accent, bubble, 1, border_radius=10)
            self.screen.blit(self.font.render(name, True, accent), (x + 12, y + 10))
            for i, line in enumerate(lines):
                self.screen.blit(self.font.render(line, True, UI_COLORS['text']), (x + 12, y + 12 + (i + 1) * line_h))
            if not lines:
                label = self.font.render('Thinking', True, UI_COLORS['text_dim'])
                self.screen.blit(label, (x + 12, y + 12 + line_h))
                for i in range(3):
                    active = (pygame.time.get_ticks() // 300) % 3 == i
                    pygame.draw.circle(self.screen, accent if active else UI_COLORS['modal_frame'],
                                       (x + 24 + label.get_width() + i * 12, y + 12 + line_h + label.get_height() // 2), 3)
            y += height + 14
        self.screen.set_clip(old_clip)
        self.scroll_track = pygame.Rect(view.right + 8, view.y, 10, view.h)
        thumb_h = min(view.h, max(32, int(view.h * view.h / max(view.h, total_h))))
        thumb_y = view.y + int((view.h - thumb_h) * (1 - self.scroll / max_scroll)) if max_scroll else view.y
        self.scroll_thumb = pygame.Rect(self.scroll_track.x, thumb_y, 10, thumb_h)
        pygame.draw.rect(self.screen, UI_COLORS['modal_inner'], self.scroll_track, border_radius=5)
        pygame.draw.rect(self.screen, UI_COLORS['gold'] if max_scroll else UI_COLORS['modal_frame'], self.scroll_thumb, border_radius=5)
        entry = pygame.Rect(panel.x + 20, panel.bottom - 116, panel.w - 124, 66)
        self.send_rect = pygame.Rect(entry.right + 8, entry.y, 76, 66)
        pygame.draw.rect(self.screen, UI_COLORS['modal_inner'], entry, border_radius=5)
        pygame.draw.rect(self.screen, UI_COLORS['gold'], entry, 1, border_radius=5)
        pygame.draw.rect(self.screen, UI_COLORS['button_fill'], self.send_rect, border_radius=5)
        self.screen.blit(self.font.render('...' if self.session.pending else 'Ask', True,
                                         UI_COLORS['text_dim'] if self.session.pending else UI_COLORS['gold']), (self.send_rect.x + 16, self.send_rect.y + 20))
        old_clip = self.screen.get_clip()
        self.screen.set_clip(entry.inflate(-12, -8))
        lines = wrap_lines(self.question or 'Ask about Python...', self.font, entry.w - 16, word_wrap=False)
        self.cursor = min(self.cursor, len(self.question))
        self.anchor = min(self.anchor, len(self.question))
        offsets = []
        offset = 0
        for line in lines:
            offsets.append(offset)
            offset += len(line)
        caret_row = next((i for i, line in enumerate(lines) if self.cursor <= offsets[i] + len(line)), len(lines) - 1)
        first_row = max(0, caret_row - 1)
        start, end = sorted((self.cursor, self.anchor))
        for i, line in enumerate(lines[first_row:first_row + 2]):
            row_start = offsets[first_row + i]
            a, b = max(start, row_start), min(end, row_start + len(line))
            if a < b and self.question:
                selection = pygame.Rect(entry.x + 8 + self.font.size(line[:a - row_start])[0], entry.y + 7 + i * line_h,
                                        self.font.size(line[a - row_start:b - row_start])[0], line_h)
                pygame.draw.rect(self.screen, (45, 90, 130), selection)
            self.screen.blit(self.font.render(line, True, UI_COLORS['text'] if self.question else UI_COLORS['text_dim']), (entry.x + 8, entry.y + 7 + i * line_h))
        if (pygame.time.get_ticks() - self.caret_reset) % 1000 < 600:
            caret_x = entry.x + 8 + (self.font.size(lines[caret_row][:self.cursor - offsets[caret_row]])[0] if self.question else 0)
            caret_y = entry.y + 7 + (caret_row - first_row if self.question else 0) * line_h
            pygame.draw.line(self.screen, UI_COLORS['gold_bright'], (caret_x, caret_y),
                             (caret_x, caret_y + self.font.get_height()), 2)
        self.screen.set_clip(old_clip)
        status = 'Thinking... | Esc: return' if self.session.pending else 'Enter: ask | Esc: return | Ctrl+A/C/V/X/Z: edit'
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
                        self.handle_key(event)
                    elif event.type == pygame.TEXTINPUT:
                        if not pygame.key.get_mods() & pygame.KMOD_CTRL:
                            self.replace_selection(event.text)
                    elif event.type == pygame.MOUSEWHEEL:
                        self.scroll += event.y * 60
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if self.scroll_track.collidepoint(event.pos) and self.max_scroll:
                            self.drag_scroll = event.pos[1] - self.scroll_thumb.y if self.scroll_thumb.collidepoint(event.pos) else self.scroll_thumb.h // 2
                            self.drag_scroll_to(event.pos[1])
                        elif self.send_rect.collidepoint(event.pos):
                            self.submit()
                    elif event.type == pygame.MOUSEMOTION and self.drag_scroll is not None:
                        self.drag_scroll_to(event.pos[1])
                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        self.drag_scroll = None
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
