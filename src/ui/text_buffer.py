import pygame


class TextBuffer:

    def __init__(self):

        self.lines = [""]

        self.cursor_row = 0

        self.cursor_col = 0

    @property
    def text(self):

        return "\n".join(self.lines)

    def insert(self, character):

        line = self.lines[self.cursor_row]

        self.lines[self.cursor_row] = (
            line[:self.cursor_col]
            + character
            + line[self.cursor_col:]
        )

        self.cursor_col += len(character)

    def enter(self):

        current = self.lines[self.cursor_row]

        left = current[:self.cursor_col]

        right = current[self.cursor_col:]

        self.lines[self.cursor_row] = left

        self.lines.insert(self.cursor_row + 1, right)

        self.cursor_row += 1

        self.cursor_col = 0

    def backspace(self):

        if self.cursor_col > 0:

            line = self.lines[self.cursor_row]

            self.lines[self.cursor_row] = (
                line[:self.cursor_col - 1]
                + line[self.cursor_col:]
            )

            self.cursor_col -= 1

            return

        if self.cursor_row == 0:

            return

        previous = self.lines[self.cursor_row - 1]

        current = self.lines.pop(self.cursor_row)

        self.cursor_row -= 1

        self.cursor_col = len(previous)

        self.lines[self.cursor_row] = previous + current

    def delete(self):

        line = self.lines[self.cursor_row]

        if self.cursor_col < len(line):

            self.lines[self.cursor_row] = (
                line[:self.cursor_col]
                + line[self.cursor_col + 1:]
            )

            return

        if self.cursor_row == len(self.lines) - 1:

            return

        self.lines[self.cursor_row] += self.lines.pop(self.cursor_row + 1)

    def move_left(self):

        if self.cursor_col > 0:

            self.cursor_col -= 1

            return

        if self.cursor_row > 0:

            self.cursor_row -= 1

            self.cursor_col = len(self.lines[self.cursor_row])

    def move_right(self):

        line = self.lines[self.cursor_row]

        if self.cursor_col < len(line):

            self.cursor_col += 1

            return

        if self.cursor_row < len(self.lines) - 1:

            self.cursor_row += 1

            self.cursor_col = 0

    def move_up(self):

        if self.cursor_row == 0:

            return

        self.cursor_row -= 1

        self.cursor_col = min(
            self.cursor_col,
            len(self.lines[self.cursor_row])
        )

    def move_down(self):

        if self.cursor_row >= len(self.lines) - 1:

            return

        self.cursor_row += 1

        self.cursor_col = min(
            self.cursor_col,
            len(self.lines[self.cursor_row])
        )

    def handle_event(self, event):

        if event.type != pygame.KEYDOWN:

            return

        if event.key == pygame.K_BACKSPACE:

            self.backspace()

        elif event.key == pygame.K_DELETE:

            self.delete()

        elif event.key == pygame.K_RETURN:

            self.enter()

        elif event.key == pygame.K_TAB:

            self.insert("    ")

        elif event.key == pygame.K_LEFT:

            self.move_left()

        elif event.key == pygame.K_RIGHT:

            self.move_right()

        elif event.key == pygame.K_UP:

            self.move_up()

        elif event.key == pygame.K_DOWN:

            self.move_down()

        elif event.unicode and event.unicode.isprintable():

            self.insert(event.unicode)