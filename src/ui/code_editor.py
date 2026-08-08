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

            # -------------------------------
            # Text Input
            # -------------------------------

            if event.type == pygame.TEXTINPUT:

                self.text_buffer.insert(event.text)
                self.last_input_time = pygame.time.get_ticks()

            # -------------------------------
            # Keyboard
            # -------------------------------

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    self.running = False

                elif event.key == pygame.K_BACKSPACE:

                    self.text_buffer.backspace()
                    self.last_input_time = pygame.time.get_ticks()
                    
                elif event.key == pygame.K_TAB:

                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:

                        self.text_buffer.dedent()

                    else:

                        self.text_buffer.indent()

                    self.last_input_time = pygame.time.get_ticks()

                elif event.key == pygame.K_RETURN:

                    self.text_buffer.new_line()
                    self.last_input_time = pygame.time.get_ticks()

                elif event.key == pygame.K_LEFT:

                    self.text_buffer.move_left()
                    self.last_input_time = pygame.time.get_ticks()

                elif event.key == pygame.K_RIGHT:

                    self.text_buffer.move_right()
                    self.last_input_time = pygame.time.get_ticks()

                elif event.key == pygame.K_UP:

                    self.text_buffer.move_up()
                    self.last_input_time = pygame.time.get_ticks()

                elif event.key == pygame.K_DOWN:

                    self.text_buffer.move_down()
                    self.last_input_time = pygame.time.get_ticks()