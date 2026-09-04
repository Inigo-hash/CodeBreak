"""Procedural inventory artwork for stored learning topics.

The icons are drawn in code so they stay crisp at every UI scale and do not
need a separate image asset for every lesson.  Each one shares the same little
spellbook silhouette, while its colour and code glyph identify the topic.
"""

from functools import lru_cache

import pygame

from src.ui.theme import body_font


# Short code-shaped marks remain readable in the inventory's 38px artwork
# area.  The accent is intentionally different for every Stage 1 lesson.
TOPIC_ICON_STYLES = {
    "python_syntax_basics": (">_", (65, 171, 232)),
    "variables": ("x=", (235, 185, 72)),
    "data_types": ("123", (88, 196, 135)),
    "type_casting": ("int", (235, 129, 72)),
    "input_lesson": (">?", (72, 207, 207)),
    "formatted_output": ("f{}", (170, 117, 229)),
    "operators_lesson": ("+-", (231, 91, 91)),
    "strings_lesson": ('"A"', (76, 190, 164)),
    "control_flow_lesson": ("if", (239, 158, 64)),
}

DEFAULT_TOPIC_STYLE = ("<>", (120, 205, 255))


def _shade(color, amount):
    """Lighten or darken an RGB colour without leaving the valid range."""

    return tuple(max(0, min(255, channel + amount)) for channel in color)


def _fitted_glyph(text, max_width, max_height, start_size):
    """Render a glyph small enough to remain inside its book medallion."""

    for size in range(start_size, 7, -1):
        rendered = body_font(size, bold=True).render(text, True, (246, 241, 220))
        if rendered.get_width() <= max_width and rendered.get_height() <= max_height:
            return rendered
    return body_font(8, bold=True).render(text, True, (246, 241, 220))


@lru_cache(maxsize=64)
def topic_icon(topic_id, size=48):
    """Return a cached spellbook icon for ``topic_id``.

    Unknown future topic IDs still receive a complete generic book instead of
    falling back to a letter placeholder.
    """

    size = max(28, int(size))
    glyph, accent = TOPIC_ICON_STYLES.get(topic_id, DEFAULT_TOPIC_STYLE)

    icon = pygame.Surface((size, size), pygame.SRCALPHA)
    margin = max(3, size // 12)
    book = pygame.Rect(margin, margin - 1, size - margin * 2, size - margin * 2)
    radius = max(3, size // 10)

    # The offset pages and dark drop shadow make this read as a small book,
    # not another flat letter tile.
    shadow = book.move(2, 3)
    pygame.draw.rect(icon, (3, 5, 10, 150), shadow, border_radius=radius)
    pages = book.move(2, 1)
    pygame.draw.rect(icon, (210, 190, 144), pages, border_radius=radius)
    pygame.draw.line(
        icon, (128, 103, 61),
        (pages.right - 2, pages.top + radius),
        (pages.right - 2, pages.bottom - radius), 1,
    )

    # Deep navy cover, coloured spine, and double accent rim match the game's
    # stone/bronze menu language while giving every lesson its own identity.
    pygame.draw.rect(icon, _shade(accent, -105), book, border_radius=radius)
    pygame.draw.rect(icon, accent, book, 2, border_radius=radius)
    spine_w = max(4, size // 8)
    spine = pygame.Rect(book.left + 2, book.top + 2, spine_w, book.height - 4)
    pygame.draw.rect(icon, _shade(accent, -35), spine, border_radius=2)
    pygame.draw.line(
        icon, _shade(accent, 35),
        (spine.right, spine.top + 2), (spine.right, spine.bottom - 2), 1,
    )

    # A central seal holds the code-shaped topic mark.  The tiny corner studs
    # add detail after the 48px art is scaled into a 38px inventory slot.
    seal_center = (book.centerx + spine_w // 3, book.centery - 1)
    seal_radius = max(9, size // 4)
    pygame.draw.circle(icon, (15, 20, 31), seal_center, seal_radius)
    pygame.draw.circle(icon, _shade(accent, 30), seal_center, seal_radius, 2)
    pygame.draw.circle(icon, (*accent, 45), seal_center, max(2, seal_radius - 3))

    glyph_surf = _fitted_glyph(
        glyph,
        max_width=seal_radius * 2 - 5,
        max_height=seal_radius * 2 - 4,
        start_size=max(12, size // 3),
    )
    icon.blit(glyph_surf, glyph_surf.get_rect(center=seal_center))

    stud_radius = max(1, size // 32)
    stud_x = book.right - max(5, size // 9)
    for stud_y in (book.top + max(5, size // 9), book.bottom - max(5, size // 9)):
        pygame.draw.circle(icon, _shade(accent, 45), (stud_x, stud_y), stud_radius)

    return icon
