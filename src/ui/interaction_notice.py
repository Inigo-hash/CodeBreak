"""Readable exploration feedback with the dismissal hint inside its panel."""
import pygame
from src.ui.theme import UI_COLORS, body_font, draw_panel
from src.ui.text_layout import wrap_text, draw_text_block


def draw_interaction_notice(screen, message):
    width = min(600, screen.get_width()-48)
    font, small = body_font(20), body_font(14, bold=True)
    lines = wrap_text(message, font, width-48)
    body_height = min(len(lines)*font.get_linesize()+12, screen.get_height()-180)
    panel = pygame.Rect(0, 0, width, body_height+104)
    panel.center = screen.get_rect().center
    draw_panel(screen, panel, radius=12, alpha=255)
    screen.blit(small.render('EXPLORATION', True, UI_COLORS['gold']), (panel.x+24, panel.y+16))
    draw_text_block(screen, message, font, UI_COLORS['text'],
                    pygame.Rect(panel.x+24, panel.y+44, width-48, body_height), center=True)
    footer_y = panel.bottom-38
    pygame.draw.line(screen, UI_COLORS['bronze_dark'], (panel.x+24, footer_y-10), (panel.right-24, footer_y-10))
    hint = small.render('Release E to close', True, UI_COLORS['text_dim'])
    screen.blit(hint, hint.get_rect(midtop=(panel.centerx, footer_y)))
    return panel
