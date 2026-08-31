import pygame
from src.systems.audio import handle_music_shortcut

from src.ui.theme import UI_COLORS, body_font, title_font


# ---------------------------------------------------------
# Colors
# ---------------------------------------------------------
#
# The shared modal palette from ui/theme.py. These exact values used to be
# written out here, and again in topic_lesson.py, and again in
# inventory.py, under three different sets of names - so a change to "the
# colour of a modal window" meant finding every copy. Names are kept local
# because they read better at the call sites below.

PANEL_BG = UI_COLORS["modal_panel"]
PANEL_INNER = UI_COLORS["modal_inner"]

FRAME = UI_COLORS["modal_frame"]
FRAME_HOVER = UI_COLORS["modal_frame_hover"]

ACCENT = UI_COLORS["modal_accent"]

TEXT_MAIN = UI_COLORS["modal_text"]
TEXT_DIM = UI_COLORS["modal_text_dim"]

BUTTON_BG = UI_COLORS["modal_button"]
BUTTON_HOVER = UI_COLORS["modal_button_hover"]


class TopicFoundScreen:

    def __init__(self, screen, topic_id, background=None):

        self.screen = screen
        self.topic_id = topic_id

        self.screen_w, self.screen_h = screen.get_size()

        # Frozen gameplay screen behind the popup.
        self.background = (
            background
            if background is not None
            else screen.copy()
        )

        # -------------------------------------------------
        # Fonts
        # -------------------------------------------------

        self.title_font = title_font(30)

        self.topic_font = title_font(25)

        self.text_font = body_font(17)

        self.button_font = title_font(16, bold=False)

        # Temporary display name.
        #
        # variables      -> Variables
        # data_types     -> Data Types
        # control_flow   -> Control Flow
        #
        # Later this should come from topics.py instead.
        self.topic_name = (
            topic_id
            .replace("_", " ")
            .title()
        )

        # -------------------------------------------------
        # Popup geometry
        # -------------------------------------------------

        panel_width = min(620, int(self.screen_w * 0.55))
        panel_height = 360

        self.panel_rect = pygame.Rect(
            (self.screen_w - panel_width) // 2,
            (self.screen_h - panel_height) // 2,
            panel_width,
            panel_height
        )

        button_width = 180
        button_height = 48
        button_gap = 20

        total_button_width = (
            button_width * 2
            + button_gap
        )

        button_left = (
            self.panel_rect.centerx
            - total_button_width // 2
        )

        button_y = self.panel_rect.bottom - 85

        self.start_button = pygame.Rect(
            button_left,
            button_y,
            button_width,
            button_height
        )

        self.store_button = pygame.Rect(
            button_left + button_width + button_gap,
            button_y,
            button_width,
            button_height
        )

    # ---------------------------------------------------------
    # Main loop
    # ---------------------------------------------------------

    def run(self):

        clock = pygame.time.Clock()

        # Prevent the E key that opened this popup from immediately
        # affecting something else.
        pygame.event.clear()

        while True:

            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if handle_music_shortcut(event):
                    continue

                if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                ):
                    return "cancel"

                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                ):

                    if self.start_button.collidepoint(event.pos):

                        return "start"

                    if self.store_button.collidepoint(event.pos):

                        return "store"

            self.draw(mouse_pos)

            pygame.display.flip()

            clock.tick(60)

    # ---------------------------------------------------------
    # Drawing
    # ---------------------------------------------------------

    def draw(self, mouse_pos):

        # ----------------------------------
        # Frozen gameplay background
        # ----------------------------------

        self.screen.blit(
            self.background,
            (0, 0)
        )

        # Dark overlay.
        overlay = pygame.Surface(
            (self.screen_w, self.screen_h),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 0, 0, 165)
        )

        self.screen.blit(
            overlay,
            (0, 0)
        )

        # ----------------------------------
        # Main panel
        # ----------------------------------

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

        # Inner content area.
        inner_rect = pygame.Rect(
            self.panel_rect.left + 20,
            self.panel_rect.top + 70,
            self.panel_rect.width - 40,
            150
        )

        pygame.draw.rect(
            self.screen,
            PANEL_INNER,
            inner_rect,
            border_radius=8
        )

        # ----------------------------------
        # Title
        # ----------------------------------

        title = self.title_font.render(
            "TOPIC DISCOVERED!",
            True,
            ACCENT
        )

        self.screen.blit(
            title,
            (
                self.panel_rect.centerx
                - title.get_width() // 2,

                self.panel_rect.top + 22
            )
        )

        # ----------------------------------
        # Message
        # ----------------------------------

        message = self.text_font.render(
            "Congratulations! You found a new learning topic.",
            True,
            TEXT_DIM
        )

        self.screen.blit(
            message,
            (
                self.panel_rect.centerx
                - message.get_width() // 2,

                inner_rect.top + 25
            )
        )

        # Topic name.
        topic = self.topic_font.render(
            self.topic_name,
            True,
            TEXT_MAIN
        )

        self.screen.blit(
            topic,
            (
                self.panel_rect.centerx
                - topic.get_width() // 2,

                inner_rect.centery + 10
            )
        )

        # ----------------------------------
        # Buttons
        # ----------------------------------

        self.draw_button(
            self.start_button,
            "START",
            mouse_pos
        )

        self.draw_button(
            self.store_button,
            "STORE IN BAG",
            mouse_pos
        )

    def draw_button(self, rect, label, mouse_pos):

        hovered = rect.collidepoint(mouse_pos)

        color = (
            BUTTON_HOVER
            if hovered
            else BUTTON_BG
        )

        border = (
            ACCENT
            if hovered
            else FRAME
        )

        pygame.draw.rect(
            self.screen,
            color,
            rect,
            border_radius=6
        )

        pygame.draw.rect(
            self.screen,
            border,
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


def open_topic_found(
    screen,
    topic_id,
    background=None
):

    return TopicFoundScreen(
        screen,
        topic_id,
        background
    ).run()
