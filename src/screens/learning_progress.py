"""Separate progress overview and topic guidance screens; no practice side effects."""
import pygame
from src.systems.learning_progress import progress_snapshot
from src.ui.theme import UI_COLORS, body_font, title_font, draw_panel, draw_button
from src.ui.text_layout import fit_text


def learning_progress_panel(size, topics_only=False):
    width, height = size
    panel = pygame.Rect(0, 0, min(880 if topics_only else 800, width-48),
                        min(900 if topics_only else 680, height-48))
    panel.center = (width//2, height//2)
    return panel


def _wrapped(text, font, width):
    lines, line = [], ''
    for word in text.split():
        candidate = (line + ' ' + word).strip()
        if line and font.size(candidate)[0] > width:
            lines.append(line)
            line = word
        else:
            line = candidate
    return lines + ([line] if line else [])


def draw_learning_progress(screen, stage, state, topics_only=False, scroll=0, background=None):
    """Render one frame and return the scroll limit and navigation hit boxes."""
    width, height = screen.get_size()
    if background is not None:
        screen.blit(background, (0, 0))
    else:
        screen.fill(UI_COLORS['stone_deep'])
    veil = pygame.Surface((width, height), pygame.SRCALPHA)
    veil.fill((0, 0, 0, 175)); screen.blit(veil, (0, 0))
    panel = learning_progress_panel((width, height), topics_only)
    draw_panel(screen, panel, emphasized=True, radius=12)
    font = body_font(18)
    small = body_font(16)
    heading = title_font(26)
    x = panel.left + 48
    title = fit_text(heading, 'TOPIC GUIDANCE' if topics_only else 'PLAYER PROGRESS',
                     UI_COLORS['gold'], (panel.w-128, 42))
    screen.blit(title, title.get_rect(midtop=(panel.centerx, panel.top+36)))
    switch = pygame.Rect(panel.right - 233, panel.top + 96, 185, 36)
    back = pygame.Rect(panel.right - 173, panel.bottom - 78, 125, 36)
    draw_button(screen, switch, 'Progress' if topics_only else 'Topic Guidance', small,
                hovered=switch.collidepoint(pygame.mouse.get_pos()))
    draw_button(screen, back, 'Back [ESC]', small, hovered=back.collidepoint(pygame.mouse.get_pos()))
    snapshot = progress_snapshot(stage, state)
    gate = snapshot['gate']
    summary = fit_text(small, f"{stage.get('name', 'Stage')}  |  Completed: "
                       f"{gate.completed_topics}/{gate.required_topics}",
                       UI_COLORS['text_dim'], (switch.left-x-20, 30))
    screen.blit(summary, summary.get_rect(midleft=(x, switch.centery)))
    content = pygame.Rect(x, panel.top + 152, panel.width - 96, panel.height - 250)
    entries = []
    if topics_only:
        for index, row in enumerate(snapshot['topics'], 1):
            entries.append((f"{index}. {row['title']}  -  {row['status']}",
                            UI_COLORS['modal_success'] if row['status'] == 'Completed' else UI_COLORS['gold'], 8))
            entries.append(('Discovery: ' + ('Discovered' if row['discovered'] else 'Not yet discovered'), UI_COLORS['text'], 0))
            entries.append(('Prerequisites: ' + (', '.join(row['requirements']) or 'None'), UI_COLORS['text_dim'], 0))
            if row['missing']:
                entries.append(('Complete first: ' + ', '.join(row['missing']), UI_COLORS['text'], 0))
            elif row['status'] != 'Completed':
                entries.append(('Next: Open its stored lesson or find its learning object in the world.'
                                if row['discovered'] else 'Next: Find its learning object in the world.', UI_COLORS['text'], 0))
            entries.append(('', UI_COLORS['text'], 12))
    else:
        entries = [
            (f"Stage completion: {snapshot['percent']}%", UI_COLORS['gold'], 12),
            (f'Topics: {gate.completed_topics}/{gate.required_topics}', UI_COLORS['text'], 8),
            (f'Keys: {gate.keys}/{gate.required_keys}', UI_COLORS['text'], 8),
            ('Boss: ' + ('Defeated' if gate.boss_defeated else 'Not defeated'), UI_COLORS['text'], 8),
            ('Final assessment: ' + ('Passed' if gate.final_challenge_completed else
                                     'Available' if gate.boss_defeated else 'Locked until boss victory'), UI_COLORS['text'], 8),
            ('Stage exit: ' + ('Ready' if gate.unlocked else 'Requirements remaining'), UI_COLORS['text'], 18),
            ('Next objective: ' + snapshot['next'], UI_COLORS['gold'], 18),
        ]
        history = state.get('final_assessments', {}).get(stage.get('id'), {}).get('history', [])
        if history:
            last = history[-1]
            entries.append((f"Last assessment: {last['result'].replace('_', ' ')}  |  Attempts: {len(history)}",
                            UI_COLORS['text_dim'], 8))
        entries.append(('Progress counts required topics, the boss, and the final assessment. '
                        'All required keys are also needed for 100%.', UI_COLORS['text_dim'], 0))
    rendered = []
    total = 0
    for text, color, gap in entries:
        total += gap
        for line in _wrapped(text, font, content.width - 18):
            rendered.append((line, color, total))
            total += font.get_linesize() + 3
    limit = max(0, total - content.height)
    scroll = max(0, min(scroll, limit))
    old_clip = screen.get_clip(); screen.set_clip(content)
    for line, color, y in rendered:
        screen.blit(font.render(line, True, color), (content.left, content.top + y - scroll))
    screen.set_clip(old_clip)
    if limit:
        track = pygame.Rect(content.right-5, content.top, 4, content.height)
        pygame.draw.rect(screen, UI_COLORS['stone_light'], track, border_radius=2)
        thumb_height = max(24, round(content.height*content.height/total))
        thumb = pygame.Rect(track.x, track.y+round((track.h-thumb_height)*scroll/limit), 4, thumb_height)
        pygame.draw.rect(screen, UI_COLORS['gold'], thumb, border_radius=2)
    footer = 'Scroll / Up / Down for more' if limit else 'ESC to return to gameplay'
    footer_surface = fit_text(small, footer, UI_COLORS['text_dim'], (back.left-x-20, 28))
    screen.blit(footer_surface, footer_surface.get_rect(midleft=(x,back.centery)))
    return limit, switch, back


def open_learning_progress(screen, stage, state, topics_only=False, background=None):
    background = background if background is not None else screen.copy()
    clock = pygame.time.Clock()
    scroll = 0
    while True:
        limit, switch, back = draw_learning_progress(screen, stage, state, topics_only, scroll, background)
        scroll = max(0, min(scroll, limit))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                if event.key in (pygame.K_DOWN, pygame.K_PAGEDOWN): scroll += 80
                if event.key in (pygame.K_UP, pygame.K_PAGEUP): scroll -= 80
            if event.type == pygame.MOUSEWHEEL: scroll -= event.y * 55
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back.collidepoint(event.pos): return
                if switch.collidepoint(event.pos):
                    topics_only = not topics_only; scroll = 0
        clock.tick(60)
