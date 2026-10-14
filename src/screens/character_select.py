"""New-game character selection with mouse and keyboard support."""
import math
import pygame
from src.data.characters import CHARACTERS
from src.systems.audio import handle_music_shortcut
from src.ui.theme import UI_COLORS, title_font, body_font, draw_panel, draw_button, TIER_PRIMARY
from src.ui.text_layout import fit_text, draw_text_block


def character_select_layout(size):
    w, h = size
    panel = pygame.Rect(0, 0, min(1120, w-40), min(760, h-32))
    panel.center = (w//2, h//2)
    gap, padding = 24, 28
    card_w = (panel.w - padding*2 - gap)//2
    cards = [pygame.Rect(panel.x+padding+i*(card_w+gap), panel.y+116,
                         card_w, panel.h-240) for i in range(2)]
    confirm = pygame.Rect(0, 0, min(380, panel.w-320), 48)
    confirm.midbottom = (panel.centerx, panel.bottom-38)
    back = pygame.Rect(panel.x+28, confirm.y, 110, 48)
    return panel, cards, confirm, back


def character_preview(identity):
    image = pygame.image.load(CHARACTERS[identity]['preview']).convert_alpha()
    return image.subsurface(image.get_bounding_rect(min_alpha=8)).copy()


def draw_character_selection(screen, background, selected, previews, elapsed=0, keyboard=False):
    panel, cards, confirm, back = character_select_layout(screen.get_size())
    screen.blit(background, (0, 0))
    veil = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    veil.fill((5, 8, 15, 215))
    screen.blit(veil, (0, 0))
    draw_panel(screen, panel, radius=14)
    heading = fit_text(title_font(32), 'CHOOSE YOUR EXPLORER', UI_COLORS['gold'], (panel.w-64, 44))
    screen.blit(heading, heading.get_rect(midtop=(panel.centerx, panel.top+20)))
    sub = fit_text(body_font(17), 'Two explorers. Your adventure. Choose who you want to play.', UI_COLORS['text_dim'], (panel.w-64, 30))
    screen.blit(sub, sub.get_rect(midtop=(panel.centerx, panel.top+74)))
    mouse = pygame.mouse.get_pos()
    for identity, card in zip(CHARACTERS, cards):
        chosen = identity == selected
        hovered = card.collidepoint(mouse)
        pygame.draw.rect(screen, (30, 38, 52) if chosen else UI_COLORS['modal_inner'], card, border_radius=12)
        pygame.draw.rect(screen, UI_COLORS['gold'] if chosen else UI_COLORS['blue'] if hovered else UI_COLORS['modal_frame'], card, 3 if chosen else 1, border_radius=12)
        badge = 'SELECTED' if chosen else 'CLICK TO SELECT'
        screen.blit(body_font(13, bold=True).render(badge, True, UI_COLORS['gold'] if chosen else UI_COLORS['text_dim']), (card.x+18, card.y+16))
        preview_h = max(60, min(235, card.h-170))
        image = previews[identity]
        factor = min(preview_h/image.get_height(), (card.w-60)/image.get_width())
        sprite = pygame.transform.scale(image, (max(1, round(image.get_width()*factor)), max(1, round(image.get_height()*factor))))
        baseline = card.y+42+preview_h
        pygame.draw.ellipse(screen, (12, 16, 24), (card.centerx-52, baseline-9, 104, 18))
        screen.blit(sprite, sprite.get_rect(midbottom=(card.centerx, baseline+round(math.sin(elapsed*2)*2))))
        title_y = baseline+16
        title = fit_text(title_font(22), CHARACTERS[identity]['title'], UI_COLORS['text'], (card.w-32, 32))
        screen.blit(title, title.get_rect(midtop=(card.centerx, title_y)))
        compact = card.h < 290
        description = CHARACTERS[identity]['short_description' if compact else 'description']
        draw_text_block(screen, description, body_font(13 if compact else 16), UI_COLORS['text_dim'],
                        pygame.Rect(card.x+24, title_y+40, card.w-48, max(22, card.bottom-title_y-56)), center=True)
    note = fit_text(body_font(15), 'Same health, energy, damage and controls. Your choice is saved with this adventure.', UI_COLORS['text_dim'], (panel.w-56, 26))
    screen.blit(note, note.get_rect(center=(panel.centerx, confirm.top-26)))
    draw_button(screen, confirm, 'CONTINUE AS '+CHARACTERS[selected]['label'], title_font(20),
                hovered=confirm.collidepoint(mouse), tier=TIER_PRIMARY, focused=keyboard)
    draw_button(screen, back, 'BACK', title_font(18), hovered=back.collidepoint(mouse))
    hint = fit_text(body_font(12), 'LEFT / RIGHT or TAB: choose   ENTER: continue   ESC: back', UI_COLORS['text_dim'], (panel.w-40, 20))
    screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom-15)))


def open_character_select(screen):
    background = screen.copy()
    previews = {identity: character_preview(identity) for identity in CHARACTERS}
    identities = list(CHARACTERS)
    selected, keyboard = 0, False
    clock = pygame.time.Clock()
    while True:
        _, cards, confirm, back = character_select_layout(screen.get_size())
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if handle_music_shortcut(event):
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB):
                    selected = 1-selected
                    keyboard = True
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return identities[selected]
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                keyboard = False
                if back.collidepoint(event.pos):
                    return None
                if confirm.collidepoint(event.pos):
                    return identities[selected]
                for i, card in enumerate(cards):
                    if card.collidepoint(event.pos):
                        selected = i
        draw_character_selection(screen, background, identities[selected], previews, pygame.time.get_ticks()/1000, keyboard)
        pygame.display.flip()
        clock.tick(60)
