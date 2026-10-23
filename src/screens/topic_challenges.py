"""Choose required challenges independently; completed ones become practice."""
import pygame
from src.data.challenges import CHALLENGES
from src.data.topics import topic_challenge_ids
from src.ui.theme import body_font, title_font, UI_COLORS, draw_button, TIER_PRIMARY, TIER_SECONDARY
from src.ui.text_layout import fit_text


def open_topic_challenges(screen, topic, passed):
    background = screen.copy()
    clock = pygame.time.Clock()
    w, h = screen.get_size()
    panel = pygame.Rect(0, 0, min(680, w - 40), 300)
    panel.center = (w // 2, h // 2)
    rows = [(cid, pygame.Rect(panel.x + 24, panel.y + 84 + i * 66, panel.w - 48, 52))
            for i, cid in enumerate(topic_challenge_ids(topic))]
    focus = next((i for i, (cid, _) in enumerate(rows) if cid not in passed), 0)
    font = body_font(20)
    while True:
        screen.blit(background, (0, 0))
        shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 185))
        screen.blit(shade, (0, 0))
        pygame.draw.rect(screen, UI_COLORS['modal_panel'], panel, border_radius=10)
        pygame.draw.rect(screen, UI_COLORS['gold'], panel, 2, border_radius=10)
        heading = fit_text(title_font(26), topic['title'] + ' - Challenges',
                           UI_COLORS['gold'], (panel.w - 48, 44))
        screen.blit(heading, heading.get_rect(midtop=(panel.centerx, panel.y + 20)))
        next_required = next((cid for cid, _ in rows if cid not in passed), None)
        for index, (cid, rect) in enumerate(rows):
            done = cid in passed
            label = CHALLENGES[cid]['title'] + (' - Passed / Practice' if done else ' - Not passed')
            draw_button(screen, rect, label, font,
                        hovered=rect.collidepoint(pygame.mouse.get_pos()) or index == focus,
                        tier=TIER_PRIMARY if cid == next_required else TIER_SECONDARY)
            if index == focus:
                pygame.draw.rect(screen, UI_COLORS['blue_bright'], rect.inflate(6, 6), 2, border_radius=7)
        required_count = len(rows)
        note = f'Pass all {required_count} challenges to master this topic. Replays earn no rewards.'
        rendered = fit_text(body_font(16), note, UI_COLORS['text_dim'], (panel.w - 48, 28))
        screen.blit(rendered, (panel.x + 24, panel.bottom - 48))
        hint = fit_text(body_font(16), 'Up/Down or Tab: select | Enter: open | Esc: return', UI_COLORS['text_dim'], (panel.w - 48, 20))
        screen.blit(hint, (panel.x + 24, panel.bottom - 28))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
            if event.type == pygame.KEYDOWN and rows:
                if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_TAB):
                    step = -1 if event.key == pygame.K_UP or (event.key == pygame.K_TAB and getattr(event, 'mod', 0) & pygame.KMOD_SHIFT) else 1
                    focus = (focus + step) % len(rows)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return rows[focus][0]
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for cid, rect in rows:
                    if rect.collidepoint(event.pos):
                        return cid
        clock.tick(60)
