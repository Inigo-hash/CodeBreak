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

        # Get existing indentation
        indentation = ""

        for char in left:
            if char == " ":
                indentation += " "
            else:
                break

        # Add 4 spaces if the line ends with a colon
        if left.rstrip().endswith(":"):
            indentation += "    "

        # Keep the current line
        self.lines[self.cursor_row] = left

        # Create the new line with indentation
        self.lines.insert(
            self.cursor_row + 1,
            indentation + right
        )

        self.cursor_row += 1
        self.cursor_col = len(indentation)

    # ==========================================================
    # Tab / Indentation
    # ==========================================================

    def indent(self):

        line = self.lines[self.cursor_row]

        self.lines[self.cursor_row] = (
            line[:self.cursor_col]
            + "    "
            + line[self.cursor_col:]
        )

        self.cursor_col += 4

    # ==========================================================
    # Remove Indentation
    # ==========================================================

    def dedent(self):

        line = self.lines[self.cursor_row]

        # Remove up to 4 spaces from the beginning
        spaces_to_remove = 0

        for i in range(min(4, len(line))):
            if line[i] == " ":
                spaces_to_remove += 1
            else:
                break

        if spaces_to_remove > 0:

            self.lines[self.cursor_row] = (
                line[spaces_to_remove:self.cursor_col]
                + line[self.cursor_col:]
            )

            self.cursor_col = max(
                0,
                self.cursor_col - spaces_to_remove
            )
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