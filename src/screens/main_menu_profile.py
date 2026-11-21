"""Save-slot profile browser opened from the main menu."""
import pygame
from src.systems import save_manager
from src.data.characters import character_title
from src.ui.theme import UI_COLORS, body_font, draw_button, title_font


def main_menu_profile(screen, background=None):
    width, height = screen.get_size()
    panel = pygame.Rect(0, 0, min(760, width - 40), min(560, height - 40))
    panel.center = (width // 2, height // 2)
    rows = [pygame.Rect(panel.left + 36, panel.top + 112 + i * 112, panel.width - 72, 94)
            for i in range(save_manager.NUM_SLOTS)]
    back = pygame.Rect(panel.centerx - 75, panel.bottom - 62, 150, 40)
    font = body_font(17)
    title = title_font(28)
    clock = pygame.time.Clock()
    if background is None:
        background = screen.copy()
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((4, 6, 12, 190))
    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back.collidepoint(event.pos):
                    running = False
                for index, rect in enumerate(rows):
                    if rect.collidepoint(event.pos):
                        state = save_manager.load_slot(index + 1)
                        if state:
                            _show_profile_details(screen, background, state, index + 1)
        screen.blit(background, (0, 0))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (27, 30, 42), panel, border_radius=10)
        pygame.draw.rect(screen, (178, 133, 65), panel, 3, border_radius=10)
        heading = title.render("PLAYER PROFILES", True, UI_COLORS["gold"])
        screen.blit(heading, heading.get_rect(center=(panel.centerx, panel.top + 54)))
        for index, rect in enumerate(rows):
            state = save_manager.load_slot(index + 1)
            pygame.draw.rect(screen, (40, 43, 54), rect, border_radius=7)
            pygame.draw.rect(screen, (116, 99, 73), rect, 2, border_radius=7)
            label = f"SAVE SLOT {index + 1}"
            detail = "No saved explorer" if not state else character_title(state.get("character_id", "man"))
            cert_count = len((state or {}).get("certificates", []))
            first = font.render(label, True, UI_COLORS["gold"])
            second = font.render(detail, True, UI_COLORS["text"])
            third = body_font(13).render(f"Certificates: {cert_count}", True, UI_COLORS["text_dim"])
            screen.blit(first, (rect.left + 20, rect.top + 12))
            screen.blit(second, (rect.left + 20, rect.top + 39))
            screen.blit(third, (rect.left + 20, rect.top + 64))
            if state:
                hint = body_font(13).render("VIEW PROFILE  >", True, UI_COLORS["gold"])
                screen.blit(hint, hint.get_rect(midright=(rect.right - 18, rect.centery)))
        draw_button(screen, back, "BACK", font, hovered=back.collidepoint(pygame.mouse.get_pos()))
        pygame.display.flip()


def _show_profile_details(screen, background, state, slot):
    width, height = screen.get_size()
    panel = pygame.Rect(0, 0, min(620, width - 40), min(430, height - 40))
    panel.center = (width // 2, height // 2)
    back = pygame.Rect(panel.centerx - 70, panel.bottom - 58, 140, 38)
    font = body_font(17)
    clock = pygame.time.Clock()
    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and back.collidepoint(event.pos):
                running = False
        screen.blit(background, (0, 0))
        shade = pygame.Surface((width, height), pygame.SRCALPHA)
        shade.fill((4, 6, 12, 190))
        screen.blit(shade, (0, 0))
        pygame.draw.rect(screen, (27, 30, 42), panel, border_radius=10)
        pygame.draw.rect(screen, (178, 133, 65), panel, 3, border_radius=10)
        lines = [
            f"PLAYER PROFILE — SLOT {slot}",
            character_title(state.get("character_id", "man")),
            f"Current stage: {state.get('stage', 'Island')}",
            f"Stages completed: {len(state.get('completed_stages', []))}",
            f"Certificates earned: {len(state.get('certificates', []))}",
        ]
        y = panel.top + 55
        for index, line in enumerate(lines):
            rendered = (title_font(24) if index == 0 else font).render(line, True, UI_COLORS["gold"] if index == 0 else UI_COLORS["text"])
            screen.blit(rendered, rendered.get_rect(center=(panel.centerx, y)))
            y += 52
        draw_button(screen, back, "BACK", font, hovered=back.collidepoint(pygame.mouse.get_pos()))
        pygame.display.flip()
