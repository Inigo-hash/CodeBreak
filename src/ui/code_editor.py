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

        self.screen = screen
        self.challenge = challenge

        # Controls whether the editor is open.
        self.running = False

        # Responsible only for drawing.
        self.renderer = EditorRenderer(screen, challenge, background)

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

            # Close game
            if event.type == pygame.QUIT:

                pygame.quit()
                raise SystemExit

            # Keyboard
            if event.type == pygame.KEYDOWN:

                # ESC closes the coding environment.
                if event.key == pygame.K_ESCAPE:

                    self.running = False