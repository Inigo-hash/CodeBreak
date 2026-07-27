import pygame

from .editor_theme import *


class EditorRenderer:

    def __init__(self):

        self.cursor_visible = True

        self.cursor_timer = 0

    def draw(

            self,

            screen,

            challenge,

            text_buffer,

            output_panel,

            buttons

    ):

        screen.fill(BACKGROUND)

        pygame.draw.rect(

            screen,

            TOP_BAR,

            (

                0,

                0,

                WINDOW_WIDTH,

                TOP_BAR_HEIGHT

            )

        )

        title = TITLE_FONT.render(

            challenge["title"],

            True,

            TEXT

        )

        screen.blit(title, (20, 15))

        editor_x = PROBLEM_PANEL_WIDTH

        editor_y = TOP_BAR_HEIGHT

        editor_w = WINDOW_WIDTH - PROBLEM_PANEL_WIDTH

        editor_h = WINDOW_HEIGHT - TOP_BAR_HEIGHT - OUTPUT_HEIGHT

        pygame.draw.rect(

            screen,

            EDITOR_BG,

            (

                editor_x,

                editor_y,

                editor_w,

                editor_h

            )

        )

        pygame.draw.line(

            screen,

            BORDER,

            (

                editor_x + LINE_NUMBER_WIDTH,

                editor_y

            ),

            (

                editor_x + LINE_NUMBER_WIDTH,

                editor_y + editor_h

            ),

            2

        )

        for i, line in enumerate(text_buffer.lines):

            y = editor_y + 20 + i * LINE_HEIGHT

            ln = TEXT_FONT.render(

                str(i + 1),

                True,

                LINE_NUMBER

            )

            screen.blit(

                ln,

                (

                    editor_x + 10,

                    y

                )

            )

            txt = EDITOR_FONT.render(

                line,

                True,

                TEXT

            )

            screen.blit(

                txt,

                (

                    editor_x + LINE_NUMBER_WIDTH + 15,

                    y

                )

            )

        self.cursor_timer += 1

        if self.cursor_timer >= 30:

            self.cursor_visible = not self.cursor_visible

            self.cursor_timer = 0

        if self.cursor_visible:

            row = text_buffer.cursor_row

            col = text_buffer.cursor_col

            line = text_buffer.lines[row][:col]

            offset = EDITOR_FONT.size(line)[0]

            cx = (

                editor_x

                + LINE_NUMBER_WIDTH

                + 15

                + offset

            )

            cy = (

                editor_y

                + 20

                + row * LINE_HEIGHT

            )

            pygame.draw.line(

                screen,

                CURSOR,

                (cx, cy),

                (cx, cy + 22),

                2

            )

        output_panel.draw(screen)

        for button in buttons:

            button.update()

            button.draw(screen)

        pygame.display.flip()