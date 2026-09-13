"""Bounded text rendering for fixed UI slots and wrapped messages."""
import pygame


def fit_text(font, text, color, size):
    """Keep a complete label inside its slot without stretching its aspect."""
    rendered = font.render(str(text), True, color)
    width, height = max(1, int(size[0])), max(1, int(size[1]))
    scale = min(1.0, width / max(1, rendered.get_width()),
                height / max(1, rendered.get_height()))
    if scale < 1:
        rendered = pygame.transform.smoothscale(rendered, (
            max(1, int(rendered.get_width() * scale)),
            max(1, int(rendered.get_height() * scale))))
    return rendered


def wrap_text(text, font, max_width):
    """
    Break `text` into a list of lines that each fit within
    `max_width` pixels when rendered with `font`.

    Wrapping happens at spaces where possible. A single "word" too
    long to fit on its own line (a long error message with no
    spaces, say) is split mid-word rather than allowed to overflow
    the pane.

    Existing newlines in the text are preserved as line breaks.
    """

    # A pane too narrow to fit anything - return the text as-is
    # rather than looping forever trying to break it up.
    if max_width <= 0:
        return [text]

    lines = []

    for paragraph in text.split("\n"):

        # Preserve deliberate blank lines.
        if not paragraph:
            lines.append("")
            continue

        current = ""

        for word in paragraph.split(" "):

            candidate = word if not current else current + " " + word

            # The word still fits on the current line.
            if font.size(candidate)[0] <= max_width:
                current = candidate
                continue

            # It does not fit, so the line ends here.
            if current:
                lines.append(current)
                current = ""

            # The word alone is wider than the pane - chop it into
            # pieces that do fit, one line at a time.
            while font.size(word)[0] > max_width:

                cut = 1

                while (
                    cut < len(word)
                    and font.size(word[:cut + 1])[0] <= max_width
                ):
                    cut += 1

                lines.append(word[:cut])

                word = word[cut:]

            current = word

        lines.append(current)

    return lines


def draw_text_block(surface, text, font, color, rect, *, center=False):
    """Wrap first; fit the complete block if a fixed slot is still too short."""
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return
    lines = wrap_text(text, font, rect.width)
    line_height = font.get_linesize() + 3
    block = pygame.Surface((rect.width, max(1, len(lines) * line_height)), pygame.SRCALPHA)
    for index, line in enumerate(lines):
        rendered = fit_text(font, line, color, (rect.width, line_height))
        x = (rect.width - rendered.get_width()) // 2 if center else 0
        block.blit(rendered, (x, index * line_height))
    if block.get_height() > rect.height:
        scale = rect.height / block.get_height()
        block = pygame.transform.smoothscale(block, (
            max(1, int(block.get_width() * scale)), rect.height))
    x = rect.centerx - block.get_width() // 2 if center else rect.x
    surface.blit(block, (x, rect.y))
