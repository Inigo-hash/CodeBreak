"""
text_buffer.py

Stores and edits the user's code.

Responsibilities
----------------
- Store lines of code.
- Handle typing.
- Handle backspace.
- Handle Enter.
- Handle cursor movement.

This class does NOT draw anything.
"""

import pygame


class TextBuffer:

    def __init__(self):

        # Start with one empty line.
        self.lines = [""]

        # Cursor position
        self.cursor_row = 0
        self.cursor_col = 0

    # ==========================================================
    # Character Input
    # ==========================================================

    def insert(self, character):

        line = self.lines[self.cursor_row]

        self.lines[self.cursor_row] = (
            line[:self.cursor_col]
            + character
            + line[self.cursor_col:]
        )

        self.cursor_col += 1

    # ==========================================================
    # Backspace
    # ==========================================================

    def backspace(self):

        # Delete inside current line
        if self.cursor_col > 0:

            line = self.lines[self.cursor_row]

            self.lines[self.cursor_row] = (
                line[:self.cursor_col - 1]
                + line[self.cursor_col:]
            )

            self.cursor_col -= 1

            return

        # Merge with previous line
        if self.cursor_row > 0:

            previous = self.lines[self.cursor_row - 1]
            current = self.lines[self.cursor_row]

            self.cursor_col = len(previous)

            self.lines[self.cursor_row - 1] = previous + current

            del self.lines[self.cursor_row]

            self.cursor_row -= 1

    # ==========================================================
    # Enter
    # ==========================================================

    def new_line(self):

        line = self.lines[self.cursor_row]

        left = line[:self.cursor_col]
        right = line[self.cursor_col:]

        self.lines[self.cursor_row] = left

        self.lines.insert(
            self.cursor_row + 1,
            right
        )

        self.cursor_row += 1
        self.cursor_col = 0

    # ==========================================================
    # Cursor Movement
    # ==========================================================

    def move_left(self):

        if self.cursor_col > 0:
            self.cursor_col -= 1

    def move_right(self):

        if self.cursor_col < len(self.lines[self.cursor_row]):
            self.cursor_col += 1

    def move_up(self):

        if self.cursor_row > 0:

            self.cursor_row -= 1

            self.cursor_col = min(
                self.cursor_col,
                len(self.lines[self.cursor_row])
            )

    def move_down(self):

        if self.cursor_row < len(self.lines) - 1:

            self.cursor_row += 1

            self.cursor_col = min(
                self.cursor_col,
                len(self.lines[self.cursor_row])
            )