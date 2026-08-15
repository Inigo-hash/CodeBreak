"""
text_buffer.py

Stores and edits the user's code.

Responsibilities
----------------
- Store lines of code.
- Handle typing (including auto-closing brackets/quotes).
- Handle backspace (including deleting an empty auto-closed pair).
- Handle Enter.
- Handle cursor movement.

This class does NOT draw anything.
"""

import pygame


# ==========================================================
# Auto-Closing Brackets / Quotes
# ==========================================================
#
# Typing one of these opening characters inserts its closing
# partner too, with the cursor left in between - the same
# "auto-closing" behavior used by editors like Trinket and VS Code.

AUTO_CLOSE_PAIRS = {
    "(": ")",
    "[": "]",
    "{": "}",
}

# Quotes close themselves (there's no separate opening/closing
# character), so they need slightly different handling than
# bracket pairs - see TextBuffer._handle_auto_close().
AUTO_CLOSE_QUOTES = {'"', "'"}

CLOSING_BRACKETS = set(AUTO_CLOSE_PAIRS.values())


class TextBuffer:

    def __init__(self):

        # Start with one empty line.
        self.lines = [""]

        # Cursor position
        self.cursor_row = 0
        self.cursor_col = 0

        # Selection anchors.
        # selection_start marks where the user began selecting.
        # selection_end marks where the cursor currently is
        # while the selection is active.
        self.selection_start = None
        self.selection_end = None

        # Cursor position captured at the moment a selection begins
        # (whether via Shift+Arrow or Select All). Used to restore
        # the cursor to its true pre-selection spot after an undo.
        self.pre_selection_cursor = None

        # ==========================================================
        # Undo / Redo History
        # ==========================================================

        # Stores previous editor states for undo operations.
        self.undo_stack = []

        # Stores undone editor states for redo operations.
        self.redo_stack = []

        # ==========================================================
        # Character Input
        # ==========================================================

    def insert(self, character):
        # Auto-closing only applies to a single typed character
        # with no selection in the way (typing over a selection
        # just replaces it, same as before this feature existed).
        if (
            len(character) == 1
            and not self.has_selection()
            and self._handle_auto_close(character)
        ):
            return

        # If a selection is active, restore the cursor to where it
        # was before selecting began, so undo restores it there.
        if self.has_selection():
            self.cursor_row, self.cursor_col = self.pre_selection_cursor

        self.save_state()

        if self.has_selection():
            self.delete_selection()

        self._insert_character(character)

    def _handle_auto_close(self, char):
        """
        Implements auto-closing brackets and quotes.

        - Typing an opening bracket ("(", "[", "{") inserts its
          closing partner too, leaving the cursor in between.
        - Typing a closing bracket right before its own matching
          partner steps over it instead of inserting a duplicate,
          so finishing a pair by hand doesn't leave "))" behind.
        - Quotes behave the same way, but only pair up when they
          aren't touching a word or number - typing a quote in the
          middle of an identifier, or an apostrophe in a
          contraction like "it's", just inserts a single character,
          since there's no real string to pair there.

        Returns True if this fully handled the keystroke (the
        caller should skip the normal insert in that case).
        """

        line = self.lines[self.cursor_row]
        col = self.cursor_col

        next_char = line[col] if col < len(line) else ""
        prev_char = line[col - 1] if col > 0 else ""

        # ---- Closing bracket typed right before its match ----
        if char in CLOSING_BRACKETS and next_char == char:
            self.cursor_col += 1
            return True

        # ---- Quote character ----
        if char in AUTO_CLOSE_QUOTES:

            # The same quote already sits right after the cursor -
            # step over it rather than inserting a duplicate.
            if next_char == char:
                self.cursor_col += 1
                return True

            def is_word_char(c):
                return c.isalnum() or c == "_"

            # Beside a word/number - a lone quote, not a pair.
            if is_word_char(prev_char) or is_word_char(next_char):
                return False

            self.save_state()
            self._insert_character(char)
            self._insert_character(char)
            self.cursor_col -= 1
            return True

        # ---- Opening bracket ----
        if char in AUTO_CLOSE_PAIRS:
            self.save_state()
            self._insert_character(char)
            self._insert_character(AUTO_CLOSE_PAIRS[char])
            self.cursor_col -= 1
            return True

        return False


    def _insert_character(self, character):
        """Inserts one character at the cursor without touching undo history."""

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
        if self.has_selection():
            self.cursor_row, self.cursor_col = self.pre_selection_cursor

            self.save_state()
            self.delete_selection()
            return

        # Deletes both sides of an empty auto-closed pair at once
        # (cursor sitting inside "()", "''", etc. with nothing
        # typed between them yet), instead of leaving the closing
        # half behind with nothing left to pair it with.
        if self.cursor_col > 0:

            line = self.lines[self.cursor_row]

            prev_char = line[self.cursor_col - 1]
            next_char = (
                line[self.cursor_col]
                if self.cursor_col < len(line)
                else ""
            )

            is_empty_pair = (
                AUTO_CLOSE_PAIRS.get(prev_char) == next_char
                or (prev_char in AUTO_CLOSE_QUOTES and next_char == prev_char)
            )

            if is_empty_pair:

                self.save_state()

                self.lines[self.cursor_row] = (
                    line[:self.cursor_col - 1]
                    + line[self.cursor_col + 1:]
                )

                self.cursor_col -= 1

                return

        # Deletes the character immediately before the cursor.
        if self.cursor_col > 0:

            self.save_state()

            line = self.lines[self.cursor_row]

            self.lines[self.cursor_row] = (
                line[:self.cursor_col - 1]
                + line[self.cursor_col:]
            )

            self.cursor_col -= 1

            return

        # Merges the current line with the previous line.
        if self.cursor_row > 0:

            self.save_state()

            previous_row = self.cursor_row - 1

            previous = self.lines[previous_row]
            current = self.lines[self.cursor_row]

            self.cursor_col = len(previous)

            self.lines[previous_row] = previous + current

            del self.lines[self.cursor_row]

            self.cursor_row = previous_row

    # ==========================================================
    # Enter
    # ==========================================================
    def new_line(self):
        if self.has_selection():
            self.cursor_row, self.cursor_col = self.pre_selection_cursor

        self.save_state()

        if self.has_selection():
            self.delete_selection()

        self._insert_newline()


    def _insert_newline(self):
        """Splits the current line at the cursor without touching undo history."""

        line = self.lines[self.cursor_row]

        left = line[:self.cursor_col]
        right = line[self.cursor_col:]

        indentation = ""

        for char in left:
            if char == " ":
                indentation += " "
            else:
                break

        if left.rstrip().endswith(":"):
            indentation += "    "

        self.lines[self.cursor_row] = left

        self.lines.insert(
            self.cursor_row + 1,
            indentation + right
        )

        self.cursor_row += 1
        self.cursor_col = len(indentation)

    def _insert_newline_plain(self):
        """
        Splits the current line at the cursor WITHOUT adding any
        automatic indentation.

        Used only during paste (insert_text). Pasted text already
        contains its own indentation as literal spaces, so running
        it through the auto-indent logic in _insert_newline() would
        stack a second layer of indentation on top of it.
        """

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
    # Bulk Text Insertion (Paste)
    # ==========================================================

    def insert_text(self, text):
        """
        Inserts a block of text - which may span multiple lines - as a
        SINGLE undoable operation. Used by paste, so pasting several
        lines undoes in one Ctrl+Z instead of one character at a time.
        """

        if self.has_selection():
            self.cursor_row, self.cursor_col = self.pre_selection_cursor

        # Save state exactly once, before any part of the paste happens.
        self.save_state()

        if self.has_selection():
            self.delete_selection()

        for char in text:
            if char == "\n":
                self._insert_newline_plain()
            else:
                self._insert_character(char)
                
    # ==========================================================
    # Tab / Indentation
    # ==========================================================

    def indent(self):
        # Saves the editor state before changing indentation.
        self.save_state()

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
        # Saves the editor state before changing indentation.
        self.save_state()

        line = self.lines[self.cursor_row]

        # Determines how many leading spaces can be removed.
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
        """Move the cursor one character to the left."""

        if self.cursor_col > 0:
            self.cursor_col -= 1


    def move_right(self):
        """Move the cursor one character to the right."""

        if self.cursor_col < len(self.lines[self.cursor_row]):
            self.cursor_col += 1


    def move_up(self):
        """Move the cursor to the same column on the previous line."""

        if self.cursor_row > 0:

            self.cursor_row -= 1

            # Prevent the cursor from going past
            # the end of the new line.
            self.cursor_col = min(
                self.cursor_col,
                len(self.lines[self.cursor_row])
            )


    def move_down(self):
        """Move the cursor to the same column on the next line."""

        if self.cursor_row < len(self.lines) - 1:

            self.cursor_row += 1

            # Prevent the cursor from going past
            # the end of the new line.
            self.cursor_col = min(
                self.cursor_col,
                len(self.lines[self.cursor_row])
            )

    def set_cursor(self, row, col):
        """Move the cursor to a specific row and column."""

        # Keep the row within the available lines.
        row = max(0, min(row, len(self.lines) - 1))

        # Keep the column within the selected line.
        col = max(0, min(col, len(self.lines[row])))

        self.cursor_row = row
        self.cursor_col = col

    # ==========================================================
    # Selection
    # ==========================================================
    #
    # A selection is stored as two (row, col) points:
    # - selection_start: where the drag/shift-select began
    # - selection_end:   where the cursor currently is
    #
    # These two points are not guaranteed to be in order
    # (the user might select backwards), so get_selection_range()
    # is responsible for sorting them before use.
    # ==========================================================

    def start_selection(self, row, col):
        self.selection_start = (row, col)
        self.selection_end = (row, col)

        # Remember where the cursor was before selecting began, so
        # an undo after deleting this selection can restore it here.
        self.pre_selection_cursor = (row, col)

    def update_selection(self, row, col):
        """
        Move the "active" end of the selection to a new position,
        keeping the original anchor point fixed.
        Called continuously while the user is still selecting
        (holding Shift and pressing arrows, or dragging the mouse).
        """
        if self.selection_start is None:
            self.selection_start = (row, col)

        if self.pre_selection_cursor is None:
            self.pre_selection_cursor = self.selection_start

        self.selection_end = (row, col)

    def clear_selection(self):
        """
        Cancel the current selection.
        Called whenever the user clicks elsewhere or moves
        the cursor without holding Shift.
        """
        self.selection_start = None
        self.selection_end = None
        self.pre_selection_cursor = None

    def has_selection(self):
        """
        Returns True only if a selection exists AND it actually
        spans more than one position. A selection where start
        and end are identical is treated as "no selection" -
        this happens if the user taps Shift+Arrow and releases
        without actually moving.
        """

        return (
            self.selection_start is not None
            and self.selection_end is not None
            and self.selection_start != self.selection_end
        )

    def get_selection_range(self):
        """
        Returns the selection as (start_row, start_col, end_row, end_col),
        always ordered so that "start" comes before "end" in the text -
        regardless of which direction the user actually selected in.

        This matters because a user can select either left-to-right
        or right-to-left, but every other method in this class
        assumes start always comes first.
        """

        start_row, start_col = self.selection_start
        end_row, end_col = self.selection_end

        # If the recorded "start" point actually comes after
        # the "end" point in the text, swap them.
        if (start_row, start_col) > (end_row, end_col):
            start_row, start_col, end_row, end_col = (
                end_row, end_col, start_row, start_col
            )

        return start_row, start_col, end_row, end_col

    def get_selected_text(self):
        """
        Returns the currently selected text as a single string,
        with newlines joining separate lines. Used by Ctrl+C
        to know what to place on the clipboard.
        """

        if not self.has_selection():
            return ""

        start_row, start_col, end_row, end_col = self.get_selection_range()

        # Selection is entirely within a single line.
        if start_row == end_row:
            return self.lines[start_row][start_col:end_col]

        # Selection spans multiple lines:
        # 1. Grab the tail end of the first line.
        # 2. Grab every full line in between.
        # 3. Grab the beginning of the last line.
        selected = [self.lines[start_row][start_col:]]

        for row in range(start_row + 1, end_row):
            selected.append(self.lines[row])

        selected.append(self.lines[end_row][:end_col])

        return "\n".join(selected)

    def delete_selection(self):
        """
        Removes the selected text from the buffer and places
        the cursor where the selection used to start.
        Used by Backspace, typing over a selection, and Ctrl+X (cut).
        """

        if not self.has_selection():
            return

        start_row, start_col, end_row, end_col = self.get_selection_range()

        # Keep the part of the first line before the selection,
        # and the part of the last line after the selection.
        # Everything in between (including the highlighted parts
        # of the first/last line) gets discarded.
        first_part = self.lines[start_row][:start_col]
        last_part = self.lines[end_row][end_col:]

        # Remove every line the selection touched...
        del self.lines[start_row:end_row + 1]

        # ...and replace it with a single merged line.
        self.lines.insert(start_row, first_part + last_part)

        # Move the cursor to exactly where the selection started.
        self.cursor_row = start_row
        self.cursor_col = start_col

        self.clear_selection()

    def select_all(self):
        # Remember where the cursor actually was before Select All
        # was triggered - NOT the start of the document - so undo
        # restores the cursor to this exact spot.
        self.pre_selection_cursor = (self.cursor_row, self.cursor_col)

        last_row = len(self.lines) - 1
        last_col = len(self.lines[last_row])

        self.selection_start = (0, 0)
        self.selection_end = (last_row, last_col)

        self.cursor_row = last_row
        self.cursor_col = last_col

    # ==========================================================
    # Undo / Redo
    # ==========================================================

    def save_state(self):
        # Stores the current editor state before an edit.
        state = (
            self.lines.copy(),
            self.cursor_row,
            self.cursor_col
        )

        self.undo_stack.append(state)

        # A new edit invalidates the existing redo history.
        self.redo_stack.clear()

    def undo(self):
        # Stops the operation when there is no previous state.
        if not self.undo_stack:
            return

        # Stores the current state so it can be restored by redo.
        current_state = (
            self.lines.copy(),
            self.cursor_row,
            self.cursor_col
        )

        self.redo_stack.append(current_state)

        # Restores the most recent previous editor state.
        previous_state = self.undo_stack.pop()

        self.lines = previous_state[0].copy()
        self.cursor_row = previous_state[1]
        self.cursor_col = previous_state[2]

        # Removes any selection after restoring the previous state.
        self.clear_selection()

    def redo(self):
        # Stops the operation when there is no state to restore.
        if not self.redo_stack:
            return

        # Stores the current state so it can be undone again.
        current_state = (
            self.lines.copy(),
            self.cursor_row,
            self.cursor_col
        )

        self.undo_stack.append(current_state)

        # Restores the most recently undone editor state.
        next_state = self.redo_stack.pop()

        self.lines = next_state[0].copy()
        self.cursor_row = next_state[1]
        self.cursor_col = next_state[2]

        # Removes any selection after restoring the next state.
        self.clear_selection()