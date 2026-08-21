"""
topic_lesson.py

Displays the lesson belonging to a discovered topic.

The screen does not decide which coding challenge exists.
It simply displays the topic and returns the player's decision.
"""

import pygame

from src.ui.editor_widgets import wrap_text
from src.ui.theme import body_font, title_font


# ---------------------------------------------------------
# Palette
# ---------------------------------------------------------

PANEL_BG = (36, 38, 48)
PANEL_INNER = (26, 28, 36)

FRAME = (90, 94, 110)
ACCENT = (255, 220, 120)

TEXT_MAIN = (255, 255, 255)
TEXT_DIM = (160, 165, 180)

BUTTON_BG = (42, 46, 58)
BUTTON_HOVER = (60, 90, 130)

SUCCESS = (120, 200, 140)
DANGER = (220, 110, 110)


class TopicLessonScreen:

    def __init__(self, screen, topic, background=None):

        self.screen = screen
        self.topic = topic

        self.screen_w, self.screen_h = screen.get_size()

        self.background = (
            background
            if background is not None
            else screen.copy()
        )

        # -------------------------------------------------
        # Fonts
        # -------------------------------------------------

        self.title_font = title_font(28)

        self.difficulty_font = body_font(14, bold=True)

        self.lesson_font = body_font(17)

        self.button_font = title_font(16, bold=False)

        self.confirm_font = title_font(18, bold=False)

        # -------------------------------------------------
        # Main panel
        # -------------------------------------------------

        panel_width = min(
            850,
            int(self.screen_w * 0.72)
        )

        panel_height = min(
            700,
            int(self.screen_h * 0.82)
        )

        self.panel_rect = pygame.Rect(
            (self.screen_w - panel_width) // 2,
            (self.screen_h - panel_height) // 2,
            panel_width,
            panel_height
        )

        # Lesson content area.
        self.lesson_rect = pygame.Rect(
            self.panel_rect.left + 30,
            self.panel_rect.top + 90,
            self.panel_rect.width - 60,
            self.panel_rect.height - 190
        )

        # Start challenge button.
        self.challenge_button = pygame.Rect(
            self.panel_rect.centerx - 110,
            self.panel_rect.bottom - 72,
            220,
            44
        )

        # -------------------------------------------------
        # Confirmation popup
        # -------------------------------------------------

        confirm_width = 430
        confirm_height = 200

        self.confirm_rect = pygame.Rect(
            (self.screen_w - confirm_width) // 2,
            (self.screen_h - confirm_height) // 2,
            confirm_width,
            confirm_height
        )

        button_width = 120
        button_height = 42
        gap = 20

        self.yes_button = pygame.Rect(
            self.confirm_rect.centerx
            - button_width
            - gap // 2,

            self.confirm_rect.bottom - 65,

            button_width,
            button_height
        )

        self.no_button = pygame.Rect(
            self.confirm_rect.centerx
            + gap // 2,

            self.confirm_rect.bottom - 65,

            button_width,
            button_height
        )

        # -------------------------------------------------
        # Lesson scrolling
        # -------------------------------------------------

        self.scroll_offset = 0

        self.line_height = (
            self.lesson_font.get_height() + 5
        )

        self.show_confirmation = False

        self.lesson_lines = self.build_lesson_lines()

    # ---------------------------------------------------------
    # Lesson text
    # ---------------------------------------------------------

    def build_lesson_lines(self):

        lines = []

        max_width = self.lesson_rect.width - 30

        for raw_line in self.topic["lesson"].strip().splitlines():

            # Preserve blank lines.
            if not raw_line.strip():
                lines.append("")
                continue

            wrapped = wrap_text(
                raw_line,
                self.lesson_font,
                max_width
            )

            lines.extend(wrapped)

        return lines

    def max_scroll(self):

        visible = (
            self.lesson_rect.height
            // self.line_height
        )

        return max(
            0,
            len(self.lesson_lines) - visible
        )

    # ---------------------------------------------------------
    # Main loop
    # ---------------------------------------------------------

    def run(self):

        clock = pygame.time.Clock()

        pygame.event.clear()

        while True:

            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

                # -----------------------------------------
                # Confirmation popup
                # -----------------------------------------

                if self.show_confirmation:

                    if (
                        event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                    ):

                        if self.yes_button.collidepoint(event.pos):

                            return "challenge"

                        if self.no_button.collidepoint(event.pos):

                            self.show_confirmation = False

                    if (
                        event.type == pygame.KEYDOWN
                        and event.key == pygame.K_ESCAPE
                    ):

                        self.show_confirmation = False

                    continue

                # -----------------------------------------
                # Lesson screen
                # -----------------------------------------

                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:

                        return "close"

                if event.type == pygame.MOUSEWHEEL:

                    self.scroll_offset -= event.y * 3

                    self.scroll_offset = max(
                        0,
                        min(
                            self.scroll_offset,
                            self.max_scroll()
                        )
                    )

                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                ):

                    if self.challenge_button.collidepoint(event.pos):

                        self.show_confirmation = True

            self.draw(mouse_pos)

            pygame.display.flip()

            clock.tick(60)

    # ---------------------------------------------------------
    # Drawing
    # ---------------------------------------------------------

    def draw(self, mouse_pos):

        # -----------------------------------------
        # Background
        # -----------------------------------------

        self.screen.blit(
            self.background,
            (0, 0)
        )

        overlay = pygame.Surface(
            (self.screen_w, self.screen_h),
            pygame.SRCALPHA
        )

        overlay.fill((0, 0, 0, 175))

        self.screen.blit(
            overlay,
            (0, 0)
        )

        # -----------------------------------------
        # Main panel
        # -----------------------------------------

        pygame.draw.rect(
            self.screen,
            PANEL_BG,
            self.panel_rect,
            border_radius=10
        )

        pygame.draw.rect(
            self.screen,
            FRAME,
            self.panel_rect,
            3,
            border_radius=10
        )

        # Title
        title = self.title_font.render(
            self.topic["title"],
            True,
            ACCENT
        )

        self.screen.blit(
            title,
            (
                self.panel_rect.left + 30,
                self.panel_rect.top + 25
            )
        )

        difficulty = self.difficulty_font.render(
            self.topic.get(
                "difficulty",
                ""
            ).upper(),
            True,
            TEXT_DIM
        )

        self.screen.blit(
            difficulty,
            (
                self.panel_rect.right
                - difficulty.get_width()
                - 30,

                self.panel_rect.top + 34
            )
        )

        # -----------------------------------------
        # Lesson area
        # -----------------------------------------

        pygame.draw.rect(
            self.screen,
            PANEL_INNER,
            self.lesson_rect,
            border_radius=7
        )

        pygame.draw.rect(
            self.screen,
            FRAME,
            self.lesson_rect,
            1,
            border_radius=7
        )

        old_clip = self.screen.get_clip()

        self.screen.set_clip(
            self.lesson_rect
        )

        y = (
            self.lesson_rect.top
            + 15
            - self.scroll_offset
            * self.line_height
        )

        for line in self.lesson_lines:

            if line:

                text = self.lesson_font.render(
                    line,
                    True,
                    TEXT_MAIN
                )

                self.screen.blit(
                    text,
                    (
                        self.lesson_rect.left + 15,
                        y
                    )
                )

            y += self.line_height

        self.screen.set_clip(old_clip)

        # -----------------------------------------
        # Start challenge button
        # -----------------------------------------

        self.draw_button(
            self.challenge_button,
            "START CHALLENGE",
            mouse_pos,
            ACCENT
        )

        # -----------------------------------------
        # Confirmation
        # -----------------------------------------

        if self.show_confirmation:

            self.draw_confirmation(
                mouse_pos
            )

    def draw_confirmation(self, mouse_pos):

        # Extra darkness behind confirmation box.
        overlay = pygame.Surface(
            (self.screen_w, self.screen_h),
            pygame.SRCALPHA
        )

        overlay.fill((0, 0, 0, 130))

        self.screen.blit(
            overlay,
            (0, 0)
        )

        pygame.draw.rect(
            self.screen,
            PANEL_BG,
            self.confirm_rect,
            border_radius=10
        )

        pygame.draw.rect(
            self.screen,
            ACCENT,
            self.confirm_rect,
            2,
            border_radius=10
        )

        text = self.confirm_font.render(
            "Start this topic's challenge?",
            True,
            TEXT_MAIN
        )

        self.screen.blit(
            text,
            (
                self.confirm_rect.centerx
                - text.get_width() // 2,

                self.confirm_rect.top + 42
            )
        )

        self.draw_button(
            self.yes_button,
            "YES",
            mouse_pos,
            SUCCESS
        )

        self.draw_button(
            self.no_button,
            "NO",
            mouse_pos,
            DANGER
        )

    def draw_button(
        self,
        rect,
        label,
        mouse_pos,
        border_color
    ):

        hovered = rect.collidepoint(mouse_pos)

        pygame.draw.rect(
            self.screen,
            BUTTON_HOVER
            if hovered
            else BUTTON_BG,

            rect,
            border_radius=6
        )

        pygame.draw.rect(
            self.screen,
            border_color if hovered else FRAME,
            rect,
            2,
            border_radius=6
        )

        text = self.button_font.render(
            label,
            True,
            TEXT_MAIN
        )

        self.screen.blit(
            text,
            (
                rect.centerx - text.get_width() // 2,
                rect.centery - text.get_height() // 2
            )
        )


def open_topic_lesson(
    screen,
    topic,
    background=None
):

    return TopicLessonScreen(
        screen,
        topic,
        background
    ).run()