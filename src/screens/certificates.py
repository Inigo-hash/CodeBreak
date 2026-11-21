"""Fantasy-RPG certificate gallery used from the main menu and player profile."""
import os
import pygame
from src.systems import save_manager
from src.systems.certificates import certificate_pdf_bytes
from src.ui.theme import UI_COLORS, body_font, draw_button, title_font


def certificate_screen(screen, slot_num=None, *, allow_download=True, background=None):
    width, height = screen.get_size()
    clock = pygame.time.Clock()
    selected_slot = slot_num
    selected_index = 0
    status = ""
    panel = pygame.Rect(0, 0, min(900, width - 40), min(650, height - 40))
    panel.center = (width // 2, height // 2)
    back = pygame.Rect(panel.left + 28, panel.bottom - 66, 150, 42)
    download = pygame.Rect(panel.right - 218, panel.bottom - 66, 190, 42)
    slot_buttons = [
        pygame.Rect(panel.left + 30, panel.top + 105 + i * 52, 170, 42)
        for i in range(save_manager.NUM_SLOTS)
    ]
    if background is None:
        background = screen.copy()
    dim = pygame.Surface((width, height), pygame.SRCALPHA)
    dim.fill((5, 7, 12, 190))
    font_title = title_font(28)
    font = body_font(17)
    small = body_font(13)
    running = True
    while running:
        clock.tick(60)
        state = save_manager.load_slot(selected_slot) if selected_slot else None
        records = (state or {}).get("certificates", [])
        selected = records[selected_index] if records and selected_index < len(records) else None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_UP, pygame.K_DOWN) and records:
                    selected_index = (selected_index + (1 if event.key == pygame.K_DOWN else -1)) % len(records)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and allow_download and selected:
                    status = _export(selected, state)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back.collidepoint(event.pos):
                    running = False
                for index, rect in enumerate(slot_buttons):
                    if rect.collidepoint(event.pos) and save_manager.slot_exists(index + 1):
                        selected_slot = index + 1
                        selected_index = 0
                        status = ""
                if selected:
                    for index, rect in enumerate(card_rects):
                        if rect.collidepoint(event.pos):
                            selected_index = index
                    if allow_download and download.collidepoint(event.pos):
                        status = _export(selected, state)
        screen.blit(background, (0, 0))
        screen.blit(dim, (0, 0))
        pygame.draw.rect(screen, (27, 30, 42), panel, border_radius=12)
        pygame.draw.rect(screen, (178, 133, 65), panel, 3, border_radius=12)
        heading = font_title.render("CERTIFICATE VAULT", True, UI_COLORS["gold"])
        screen.blit(heading, heading.get_rect(center=(panel.centerx, panel.top + 48)))
        subtitle = small.render("Official achievements issued by CodeBreak", True, UI_COLORS["text_dim"])
        screen.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.top + 80)))
        for index, rect in enumerate(slot_buttons):
            exists = save_manager.slot_exists(index + 1)
            active = selected_slot == index + 1
            draw_button(screen, rect, f"SAVE SLOT {index + 1}", font, hovered=active, enabled=exists)
        card_rects = []
        list_left = panel.left + 225
        list_top = panel.top + 112
        if not selected_slot:
            hint = font.render("Choose a save slot to view its certificates.", True, UI_COLORS["text"])
            screen.blit(hint, (list_left, list_top))
        elif not records:
            hint = font.render("No certificates earned yet.", True, UI_COLORS["text"])
            screen.blit(hint, (list_left, list_top))
            detail = small.render("Complete a stage, including its required lessons, boss and final assessment.", True, UI_COLORS["text_dim"])
            screen.blit(detail, (list_left, list_top + 38))
        else:
            for index, cert in enumerate(records):
                rect = pygame.Rect(list_left, list_top + index * 68, panel.right - list_left - 28, 58)
                card_rects.append(rect)
                pygame.draw.rect(screen, (48, 43, 39) if index == selected_index else (35, 38, 49), rect, border_radius=6)
                pygame.draw.rect(screen, (218, 180, 105) if index == selected_index else (91, 98, 113), rect, 2, border_radius=6)
                title = font.render(cert.get("title", "Certificate"), True, UI_COLORS["gold"] if index == selected_index else UI_COLORS["text"])
                screen.blit(title, (rect.left + 14, rect.top + 7))
                date = small.render(cert.get("issued_at", "")[:10], True, UI_COLORS["text_dim"])
                screen.blit(date, (rect.left + 14, rect.top + 32))
            if selected:
                detail_y = min(panel.bottom - 135, list_top + len(records) * 68 + 10)
                for line in (selected.get("achievement", ""), selected.get("certificate_id", "")):
                    rendered = small.render(line, True, UI_COLORS["text_dim"])
                    screen.blit(rendered, (list_left, detail_y))
                    detail_y += 22
        draw_button(screen, back, "BACK", font, hovered=back.collidepoint(pygame.mouse.get_pos()))
        if allow_download:
            draw_button(screen, download, "DOWNLOAD PDF", font, hovered=download.collidepoint(pygame.mouse.get_pos()), enabled=bool(selected))
        if status:
            msg = small.render(status, True, UI_COLORS["gold"])
            screen.blit(msg, msg.get_rect(center=(panel.centerx, panel.bottom - 88)))
        pygame.display.flip()


def _export(certificate, state):
    os.makedirs("certificates", exist_ok=True)
    safe_id = "".join(ch for ch in certificate.get("certificate_id", "certificate") if ch.isalnum() or ch in "-_")
    path = os.path.abspath(os.path.join("certificates", safe_id + ".pdf"))
    player_name = (state or {}).get("player_name") or (state or {}).get("character_id", "CodeBreak Explorer")
    with open(path, "wb") as output:
        output.write(certificate_pdf_bytes(certificate, player_name))
    return f"Saved PDF: {path}"
