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
    font = body_font(20)
    while True:
        screen.blit(background, (0, 0))
        shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 185))
        screen.blit(shade, (0, 0))
        pygame.draw.rect(screen, UI_COLORS['modal_panel'], panel, border_radius=10)
        pygame.draw.rect(screen, UI_COLORS['gold'], panel, 2, border_radius=10)
        screen.blit(title_font(26).render(topic['title'] + ' - Challenges', True, UI_COLORS['gold']), (panel.x + 24, panel.y + 20))
        next_required = next((cid for cid, _ in rows if cid not in passed), None)
        for cid, rect in rows:
            done = cid in passed
            label = CHALLENGES[cid]['title'] + (' - Passed / Practice' if done else ' - Not passed')
            draw_button(screen, rect, label, font,
                        hovered=rect.collidepoint(pygame.mouse.get_pos()),
                        tier=TIER_PRIMARY if cid == next_required else TIER_SECONDARY)
        note = 'Master both for Key 1. Replays earn no rewards. Esc: return'
        rendered = fit_text(body_font(16), note, UI_COLORS['text_dim'], (panel.w - 48, 28))
        screen.blit(rendered, (panel.x + 24, panel.bottom - 40))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for cid, rect in rows:
                    if rect.collidepoint(event.pos):
                        return cid
        clock.tick(60)
