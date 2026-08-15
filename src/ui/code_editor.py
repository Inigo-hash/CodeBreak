"""
code_editor.py

Controls the in-game coding environment.

Responsibilities:
- Open the coding environment.
- Handle editor events.
- Tell the renderer what to draw.
- Close the editor and return to the game.

This class DOES NOT validate code.
Validation is handled by the ChallengeManager.
"""

import pygame

from src.ui.text_buffer import TextBuffer
from src.ui.editor_renderer import EditorRenderer
from src.ui.editor_settings import EditorSettingsPanel
from src.ui.editor_theme import (
    TEXT_COLOR,
    SUCCESS_COLOR,
    ERROR_COLOR,
    WHEEL_LINES,
)
from src.learning.sandbox import run_user_code
from src.learning.challenge_manager import ChallengeManager

class CodeEditor:
    """
    Main controller of the coding environment.
    """

    def __init__(self, screen, challenge, background=None):
        """
        Parameters
        ----------
        screen : pygame.Surface
            Main game window.

        challenge : dict
            Challenge currently being solved.

        background : pygame.Surface, optional
            Snapshot of the game screen to show dimmed behind the popup.
        """

        self.text_buffer = TextBuffer()
        self.screen = screen
        self.challenge = challenge

        # Controls whether the editor is open.
        self.running = False

        # True once the player has submitted a correct solution.
        # Callers (e.g. the tutorial) check this after run() returns
        # to know whether the challenge was actually passed, not just
        # that the editor was closed.
        self.solved = False

        # Cursor blinking
        self.last_input_time = pygame.time.get_ticks()

        self.dragging_scrollbar = False

        # Scrollbar drags for the two side panes. Each pane keeps
        # its own scroll position, so each needs its own flag.
        self.dragging_output_scrollbar = False
        self.dragging_problem_scrollbar = False

        # Which divider between the panes is being dragged
        # ("left", "right" or None).
        self.dragging_splitter = None

        # True while the user is holding the mouse button down
        # and dragging across the code to select text.
        self.dragging_text = False

        # Mouse cursor shape currently set, so it is only changed
        # when it actually needs to change.
        self.current_mouse_cursor = None

        # Enables access to the OS clipboard for Ctrl+C / Ctrl+V.
        pygame.scrap.init()

        # Routes submitted code to the correct validator
        # based on the current challenge's "type" field.
        self.challenge_manager = ChallengeManager()

        # Responsible only for drawing.
        self.renderer = EditorRenderer(
            screen,
            challenge,
            self.text_buffer,
            background
        )

        # Reference to the Output Panel
        self.output_panel = self.renderer.get_output_panel()

        # Reference to the Objective Panel (it scrolls too)
        self.problem_panel = self.renderer.get_problem_panel()

        # UI Buttons
        self.run_button = self.renderer.get_run_button()
        self.submit_button = self.renderer.get_submit_button()
        self.leave_button = self.renderer.get_leave_button()

        # Volume / theme settings, opened by the wheel in the title bar.
        # Kept in here rather than making the player walk back to the
        # main menu, which would throw away their unsaved code.
        self.settings_panel = EditorSettingsPanel(screen)

    # ---------------------------------------------------------
    # Main Loop
    # ---------------------------------------------------------

    def run(self):
        """
        Opens the coding environment.

        This loop keeps running until
        the player exits the editor.
        """

        self.running = True

        clock = pygame.time.Clock()

        while self.running:

            self.handle_events()

            self.update_mouse_cursor()

            self.renderer.last_input_time = self.last_input_time

            self.renderer.draw()

            # Drawn after the editor so it sits on top, and laid out
            # from the popup's current rect so it stays centered even
            # if the window was resized while it was open.
            self.settings_panel.layout(self.renderer.panel_rect)
            self.settings_panel.draw()

            pygame.display.flip()

            clock.tick(60)

        # Hand the game back a normal arrow cursor, whatever shape
        # the editor happened to leave it in.
        self.set_mouse_cursor(pygame.SYSTEM_CURSOR_ARROW)

    # ---------------------------------------------------------
    # Mouse Cursor Shape
    # ---------------------------------------------------------

    def set_mouse_cursor(self, cursor):
        """
        Change the mouse cursor shape, but only when it differs
        from the one already set.
        """

        if cursor == self.current_mouse_cursor:
            return

        try:
            pygame.mouse.set_cursor(cursor)

        except pygame.error:
            # Some platforms/drivers don't provide system cursors.
            # The editor works fine without them, so this is not
            # worth interrupting the game for.
            return

        self.current_mouse_cursor = cursor

    def update_mouse_cursor(self):
        """
        Show a resize cursor over the draggable dividers and a text
        cursor over the code, so it is obvious what each area does.
        """

        position = pygame.mouse.get_pos()

        # The overlay covers the editor, so keep a plain arrow over it
        # instead of the text caret the code area would ask for.
        if self.settings_panel.is_open:
            self.set_mouse_cursor(pygame.SYSTEM_CURSOR_ARROW)

        elif self.dragging_splitter or self.renderer.get_splitter_at(position):
            self.set_mouse_cursor(pygame.SYSTEM_CURSOR_SIZEWE)

        elif self.renderer.editor_rect.collidepoint(position):
            self.set_mouse_cursor(pygame.SYSTEM_CURSOR_IBEAM)

        else:
            self.set_mouse_cursor(pygame.SYSTEM_CURSOR_ARROW)

    # ---------------------------------------------------------
    # Event Handling
    # ---------------------------------------------------------

    def handle_events(self):
        """
        Handles keyboard and window events.
        """

        for event in pygame.event.get():

            # Close the game
            if event.type == pygame.QUIT:

                pygame.quit()
                raise SystemExit

            # -------------------------------
            # Settings Overlay
            # -------------------------------
            # While it is open it swallows every event, so no keystroke
            # can reach the code buffer and no click can move the caret
            # behind the panel.

            if self.settings_panel.is_open:

                self.settings_panel.handle_event(event)
                continue

            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.renderer.settings_gear_rect.collidepoint(event.pos)
            ):

                self.settings_panel.open()
                continue

            # -------------------------------
            # Mouse Buttons
            # -------------------------------

            if self.leave_button.is_clicked(event):

                self.running = False

            if self.run_button.is_clicked(event):

                self.run_code()

            if self.submit_button.is_clicked(event):

                self.submit_code()

            # ==========================================================
            # Mouse Wheel Scrolling
            # ==========================================================
            # Each pane scrolls on its own, so the wheel affects
            # whichever pane the mouse is actually hovering over.

            if event.type == pygame.MOUSEWHEEL:

                mouse_position = pygame.mouse.get_pos()

                # ----------------------------------
                # Output Pane
                # ----------------------------------

                if self.renderer.output_rect.collidepoint(mouse_position):

                    self.output_panel.scroll(-event.y * WHEEL_LINES)

                # ----------------------------------
                # Objective Pane
                # ----------------------------------

                elif self.renderer.problem_rect.collidepoint(mouse_position):

                    self.problem_panel.scroll(-event.y * WHEEL_LINES)

                # ----------------------------------
                # Code Editor
                # ----------------------------------

                else:

                    # Move the editor in the opposite direction
                    # of the mouse wheel movement.
                    self.renderer.scroll_offset -= event.y

                    # Prevent scrolling past the first or last line.
                    self.renderer.clamp_scroll_offset()


            # ==========================================================
            # Mouse Clicks
            # ==========================================================

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                splitter = self.renderer.get_splitter_at(event.pos)

                # ----------------------------------
                # Divider Between Panes
                # ----------------------------------

                if splitter:

                    # Begin resizing the panes.
                    self.dragging_splitter = splitter

                # ----------------------------------
                # Scrollbar Thumb
                # ----------------------------------

                elif (
                    self.renderer.scrollbar_thumb_rect
                    and self.renderer.scrollbar_thumb_rect.collidepoint(event.pos)
                ):

                    # Begin dragging the scrollbar thumb.
                    self.dragging_scrollbar = True

                # ----------------------------------
                # Scrollbar Track
                # ----------------------------------

                elif (
                    self.renderer.scrollbar_track_rect
                    and self.renderer.scrollbar_track_rect.collidepoint(event.pos)
                ):

                    # Jump the scrollbar to the clicked position.
                    self.renderer.set_scroll_from_mouse_y(
                        event.pos[1]
                    )

                # ----------------------------------
                # Output Pane Scrollbar
                # ----------------------------------

                elif self.output_panel.scrollbar.hit_thumb(event.pos):

                    self.dragging_output_scrollbar = True

                elif self.output_panel.scrollbar.hit_track(event.pos):

                    self.output_panel.set_scroll_from_mouse_y(
                        event.pos[1]
                    )

                # ----------------------------------
                # Objective Pane Scrollbar
                # ----------------------------------

                elif self.problem_panel.scrollbar.hit_thumb(event.pos):

                    self.dragging_problem_scrollbar = True

                elif self.problem_panel.scrollbar.hit_track(event.pos):

                    self.problem_panel.set_scroll_from_mouse_y(
                        event.pos[1]
                    )

                # ----------------------------------
                # Code Editor
                # ----------------------------------

                elif self.renderer.editor_rect.collidepoint(event.pos):

                    # Convert the mouse position into
                    # a line and column in the text buffer.
                    row, col = (
                        self.renderer.get_cursor_position_from_mouse(
                            event.pos
                        )
                    )

                    # Anchor a new selection at the click point. If the
                    # user releases without moving the mouse, start and
                    # end stay identical, so has_selection() reports
                    # False - a plain click, not a drag-selection.
                    self.text_buffer.start_selection(row, col)

                    # Move the text cursor to that position.
                    self.text_buffer.set_cursor(row, col)

                    # Begin tracking a possible drag-to-select gesture.
                    self.dragging_text = True

                    # Make sure the cursor remains visible.
                    self.renderer.ensure_cursor_visible()

                    # Reset the cursor blink timer.
                    self.last_input_time = pygame.time.get_ticks()


            # ==========================================================
            # Stop Scrollbar Dragging
            # ==========================================================

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:

                self.dragging_scrollbar = False

                self.dragging_output_scrollbar = False

                self.dragging_problem_scrollbar = False

                # Stop resizing the panes.
                self.dragging_splitter = None

                # Stop tracking the drag-to-select gesture.
                self.dragging_text = False

            # ==========================================================
            # Drag Divider Between Panes
            # ==========================================================

            if event.type == pygame.MOUSEMOTION and self.dragging_splitter:

                # Resize the panes to follow the mouse. The renderer
                # keeps every pane above its minimum width, so this
                # can be fed raw mouse positions safely.
                self.renderer.drag_splitter(
                    self.dragging_splitter,
                    event.pos[0]
                )

            # ==========================================================
            # Drag Scrollbar
            # ==========================================================

            if event.type == pygame.MOUSEMOTION and self.dragging_scrollbar:

                # Update the scroll position while the mouse
                # moves with the scrollbar held down.
                self.renderer.set_scroll_from_mouse_y(
                    event.pos[1]
                )

            if event.type == pygame.MOUSEMOTION and self.dragging_output_scrollbar:

                self.output_panel.set_scroll_from_mouse_y(
                    event.pos[1]
                )

            if event.type == pygame.MOUSEMOTION and self.dragging_problem_scrollbar:

                self.problem_panel.set_scroll_from_mouse_y(
                    event.pos[1]
                )

            # ==========================================================
            # Drag-to-Select Text
            # ==========================================================

            if event.type == pygame.MOUSEMOTION and self.dragging_text:

                # Convert the current mouse position into a
                # row/column, even if the mouse strayed outside
                # the editor rect - the position gets clamped
                # to the nearest valid line and column.
                row, col = (
                    self.renderer.get_cursor_position_from_mouse(
                        event.pos
                    )
                )

                # Stretch the selection to follow the mouse.
                self.text_buffer.update_selection(row, col)

                # Move the cursor along with the selection edge,
                # so the blinking cursor tracks the drag visually.
                self.text_buffer.set_cursor(row, col)

                # Scroll automatically if dragging past the
                # top or bottom edge of the visible editor area.
                self.renderer.ensure_cursor_visible()

            # -------------------------------
            # Text Input
            # -------------------------------

            if event.type == pygame.TEXTINPUT:

                self.text_buffer.insert(event.text)
                self.renderer.ensure_cursor_visible()
                self.last_input_time = pygame.time.get_ticks()

            # ==========================================================
            # Keyboard
            # ==========================================================

            if event.type == pygame.KEYDOWN:

                # ----------------------------------
                # Escape
                # ----------------------------------

                if event.key == pygame.K_ESCAPE:

                    # Close the coding environment.
                    self.running = False

                # ----------------------------------
                # Undo (Ctrl+Z)
                # ----------------------------------

                if (
                    event.key == pygame.K_z
                    and pygame.key.get_mods() & pygame.KMOD_CTRL
                ):
                    # Restores the previous editor state.
                    self.text_buffer.undo()

                    # Keeps the restored cursor within the visible area.
                    self.renderer.ensure_cursor_visible()

                    # Resets the cursor blink timer.
                    self.last_input_time = pygame.time.get_ticks()

                # ----------------------------------
                # Redo (Ctrl+Y)
                # ----------------------------------

                elif (
                    event.key == pygame.K_y
                    and pygame.key.get_mods() & pygame.KMOD_CTRL
                ):
                    # Restores the most recently undone editor state.
                    self.text_buffer.redo()

                    # Keeps the restored cursor within the visible area.
                    self.renderer.ensure_cursor_visible()

                    # Resets the cursor blink timer.
                    self.last_input_time = pygame.time.get_ticks()

                # ----------------------------------
                # Backspace
                # ----------------------------------

                elif event.key == pygame.K_BACKSPACE:

                    # Deletes text before the cursor.
                    self.text_buffer.backspace()

                    # Keeps the cursor within the visible area.
                    self.renderer.ensure_cursor_visible()

                    # Resets the cursor blink timer.
                    self.last_input_time = pygame.time.get_ticks()

                # ----------------------------------
                # Select All (Ctrl+A)
                # ----------------------------------

                elif (
                    event.key == pygame.K_a
                    and pygame.key.get_mods() & pygame.KMOD_CTRL
                ):
                    self.text_buffer.select_all()
                    self.renderer.ensure_cursor_visible()
                    self.last_input_time = pygame.time.get_ticks()

                # ----------------------------------
                # Copy (Ctrl+C)
                # ----------------------------------

                elif (
                    event.key == pygame.K_c
                    and pygame.key.get_mods() & pygame.KMOD_CTRL
                ):
                    self.copy_selection()

                # ----------------------------------
                # Paste (Ctrl+V)
                # ----------------------------------

                elif (
                    event.key == pygame.K_v
                    and pygame.key.get_mods() & pygame.KMOD_CTRL
                ):
                    self.paste_clipboard()

                # ----------------------------------
                # Tab / Shift + Tab
                # ----------------------------------

                elif event.key == pygame.K_TAB:

                    # Shift + Tab removes indentation.
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:

                        self.text_buffer.dedent()

                        # Keep the cursor visible after changing indentation.
                        self.renderer.ensure_cursor_visible()

                    # Tab adds indentation.
                    else:

                        self.text_buffer.indent()

                        # Keep the cursor visible after changing indentation.
                        self.renderer.ensure_cursor_visible()

                    self.last_input_time = pygame.time.get_ticks()

                # ----------------------------------
                # Enter
                # ----------------------------------

                elif event.key == pygame.K_RETURN:

                    # Create a new line and preserve
                    # the appropriate indentation.
                    self.text_buffer.new_line()

                    # Automatically scroll to the new line
                    # if it is outside the visible area.
                    self.renderer.ensure_cursor_visible()

                    self.last_input_time = pygame.time.get_ticks()

                # ----------------------------------
                # Move Cursor Left (Shift extends selection)
                # ----------------------------------

                elif event.key == pygame.K_LEFT:

                    shift_held = pygame.key.get_mods() & pygame.KMOD_SHIFT

                    # If Shift was just pressed, anchor the selection
                    # at the current cursor position before moving.
                    if shift_held and not self.text_buffer.has_selection():
                        self.text_buffer.start_selection(
                            self.text_buffer.cursor_row,
                            self.text_buffer.cursor_col
                        )

                    # A plain arrow press (no Shift) cancels
                    # any existing selection.
                    elif not shift_held:
                        self.text_buffer.clear_selection()

                    self.text_buffer.move_left()

                    # While Shift is held, stretch the selection
                    # to follow the cursor's new position.
                    if shift_held:
                        self.text_buffer.update_selection(
                            self.text_buffer.cursor_row,
                            self.text_buffer.cursor_col
                        )

                    self.renderer.ensure_cursor_visible()
                    self.last_input_time = pygame.time.get_ticks()

                # ----------------------------------
                # Move Cursor Right (Shift extends selection)
                # ----------------------------------

                elif event.key == pygame.K_RIGHT:

                    shift_held = pygame.key.get_mods() & pygame.KMOD_SHIFT

                    if shift_held and not self.text_buffer.has_selection():
                        self.text_buffer.start_selection(
                            self.text_buffer.cursor_row,
                            self.text_buffer.cursor_col
                        )
                    elif not shift_held:
                        self.text_buffer.clear_selection()

                    self.text_buffer.move_right()

                    if shift_held:
                        self.text_buffer.update_selection(
                            self.text_buffer.cursor_row,
                            self.text_buffer.cursor_col
                        )

                    self.renderer.ensure_cursor_visible()
                    self.last_input_time = pygame.time.get_ticks()

                # ----------------------------------
                # Move Cursor Up (Shift extends selection)
                # ----------------------------------

                elif event.key == pygame.K_UP:

                    shift_held = pygame.key.get_mods() & pygame.KMOD_SHIFT

                    if shift_held and not self.text_buffer.has_selection():
                        self.text_buffer.start_selection(
                            self.text_buffer.cursor_row,
                            self.text_buffer.cursor_col
                        )
                    elif not shift_held:
                        self.text_buffer.clear_selection()

                    self.text_buffer.move_up()

                    if shift_held:
                        self.text_buffer.update_selection(
                            self.text_buffer.cursor_row,
                            self.text_buffer.cursor_col
                        )

                    self.renderer.ensure_cursor_visible()
                    self.last_input_time = pygame.time.get_ticks()

                # ----------------------------------
                # Move Cursor Down (Shift extends selection)
                # ----------------------------------

                elif event.key == pygame.K_DOWN:

                    shift_held = pygame.key.get_mods() & pygame.KMOD_SHIFT

                    if shift_held and not self.text_buffer.has_selection():
                        self.text_buffer.start_selection(
                            self.text_buffer.cursor_row,
                            self.text_buffer.cursor_col
                        )
                    elif not shift_held:
                        self.text_buffer.clear_selection()

                    self.text_buffer.move_down()

                    if shift_held:
                        self.text_buffer.update_selection(
                            self.text_buffer.cursor_row,
                            self.text_buffer.cursor_col
                        )

                    self.renderer.ensure_cursor_visible()
                    self.last_input_time = pygame.time.get_ticks()

    # ---------------------------------------------------------
    # Code Execution
    # ---------------------------------------------------------

    def run_code(self):
        """
        Executes the code currently in the editor inside the
        sandbox and shows the result (printed output, or an error)
        in the output panel. This does NOT check the code against
        the challenge's objective - that only happens on Submit.
        """

        code = "\n".join(self.text_buffer.lines)

        result = run_user_code(code)

        self.output_panel.clear()

        if result["output"]:
            for line in result["output"].rstrip("\n").split("\n"):
                self.output_panel.add(line, TEXT_COLOR)

        if result["success"]:
            self.output_panel.add("Ran successfully.", SUCCESS_COLOR)
        else:
            self.output_panel.add(result["error"], ERROR_COLOR)

    def submit_code(self):
        """
        Runs the code and, if it executed without error, checks
        it against the challenge's expected solution.
        """

        code = "\n".join(self.text_buffer.lines)

        result = run_user_code(code)

        self.output_panel.clear()

        if result["output"]:
            for line in result["output"].rstrip("\n").split("\n"):
                self.output_panel.add(line, TEXT_COLOR)

        # A syntax/runtime/safety error means the code never even
        # finished running - no point checking it against the
        # challenge, since there's nothing valid to check yet.
        if not result["success"]:
            self.output_panel.add(result["error"], ERROR_COLOR)
            return

        # Passes the raw source code (not the sandbox's runtime
        # globals) since ChallengeManager's validators work by
        # parsing the code's AST, not by inspecting variable values.
        passed, feedback = self.challenge_manager.validate(
            self.challenge,
            code
        )

        if passed:
            self.solved = True

        color = SUCCESS_COLOR if passed else ERROR_COLOR
        self.output_panel.add(feedback, color)

    # ---------------------------------------------------------
    # Clipboard
    # ---------------------------------------------------------

    def copy_selection(self):
        """
        Copies the currently selected text to the system clipboard
        (not just an internal variable), so the player can paste
        it into other applications too, and vice versa.
        """

        if not self.text_buffer.has_selection():
            return

        selected_text = self.text_buffer.get_selected_text()

        # SCRAP_TEXT expects raw bytes, not a Python string.
        pygame.scrap.put(
            pygame.SCRAP_TEXT,
            selected_text.encode("utf-8")
        )

    def paste_clipboard(self):
        """
        Reads whatever text is currently on the system clipboard
        and inserts it at the cursor position as a single undoable
        operation, replacing any active selection first.
        """

        clipboard_bytes = pygame.scrap.get(pygame.SCRAP_TEXT)

        if not clipboard_bytes:
            return

        text = clipboard_bytes.decode("utf-8", errors="ignore")
        text = text.replace("\x00", "")
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        self.text_buffer.insert_text(text)

        self.renderer.ensure_cursor_visible()
        self.last_input_time = pygame.time.get_ticks()