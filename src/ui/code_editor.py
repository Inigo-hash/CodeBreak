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

        # Cursor blinking
        self.last_input_time = pygame.time.get_ticks()

        self.dragging_scrollbar = False

        # Responsible only for drawing.
        self.renderer = EditorRenderer(
            screen,
            challenge,
            self.text_buffer,
            background
        )

        # Reference to the Output Panel
        self.output_panel = self.renderer.get_output_panel()

        # UI Buttons
        self.run_button = self.renderer.get_run_button()
        self.submit_button = self.renderer.get_submit_button()
        self.leave_button = self.renderer.get_leave_button()

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

            self.renderer.last_input_time = self.last_input_time

            self.renderer.draw()

            pygame.display.flip()

            clock.tick(60)

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
            # Mouse Buttons
            # -------------------------------

            if self.leave_button.is_clicked(event):

                self.running = False

            # ==========================================================
            # Mouse Wheel Scrolling
            # ==========================================================

            if event.type == pygame.MOUSEWHEEL:

                # Move the editor in the opposite direction
                # of the mouse wheel movement.
                self.renderer.scroll_offset -= event.y

                # Prevent scrolling past the first or last line.
                self.renderer.clamp_scroll_offset()


            # ==========================================================
            # Mouse Clicks
            # ==========================================================

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                # ----------------------------------
                # Scrollbar Thumb
                # ----------------------------------

                if (
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

                    # Move the text cursor to that position.
                    self.text_buffer.set_cursor(row, col)

                    # Make sure the cursor remains visible.
                    self.renderer.ensure_cursor_visible()

                    # Reset the cursor blink timer.
                    self.last_input_time = pygame.time.get_ticks()


            # ==========================================================
            # Stop Scrollbar Dragging
            # ==========================================================

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:

                self.dragging_scrollbar = False


            # ==========================================================
            # Drag Scrollbar
            # ==========================================================

            if event.type == pygame.MOUSEMOTION and self.dragging_scrollbar:

                # Update the scroll position while the mouse
                # moves with the scrollbar held down.
                self.renderer.set_scroll_from_mouse_y(
                    event.pos[1]
                )

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
                # Backspace
                # ----------------------------------

                elif event.key == pygame.K_BACKSPACE:

                    # Delete the character before the cursor
                    # or merge the current line with the previous one.
                    self.text_buffer.backspace()

                    # Automatically follow the cursor.
                    self.renderer.ensure_cursor_visible()

                    # Reset the cursor blink timer.
                    self.last_input_time = pygame.time.get_ticks()

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
                # Move Cursor Left
                # ----------------------------------

                elif event.key == pygame.K_LEFT:

                    self.text_buffer.move_left()

                    # Scroll if necessary to keep the cursor visible.
                    self.renderer.ensure_cursor_visible()

                    self.last_input_time = pygame.time.get_ticks()

                # ----------------------------------
                # Move Cursor Right
                # ----------------------------------

                elif event.key == pygame.K_RIGHT:

                    self.text_buffer.move_right()

                    # Scroll if necessary to keep the cursor visible.
                    self.renderer.ensure_cursor_visible()

                    self.last_input_time = pygame.time.get_ticks()

                # ----------------------------------
                # Move Cursor Up
                # ----------------------------------

                elif event.key == pygame.K_UP:

                    self.text_buffer.move_up()

                    # Scroll upward if the cursor leaves
                    # the visible editor area.
                    self.renderer.ensure_cursor_visible()

                    self.last_input_time = pygame.time.get_ticks()

                # ----------------------------------
                # Move Cursor Down
                # ----------------------------------

                elif event.key == pygame.K_DOWN:

                    self.text_buffer.move_down()

                    # Scroll downward if the cursor leaves
                    # the visible editor area.
                    self.renderer.ensure_cursor_visible()

                    self.last_input_time = pygame.time.get_ticks()