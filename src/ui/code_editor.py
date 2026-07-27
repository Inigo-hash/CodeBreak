import pygame

from learning.challenge_manager import ChallengeManager
from .editor_theme import *
from .text_buffer import TextBuffer
from .editor_renderer import EditorRenderer
from .problem_panel import ProblemPanel
from .output_panel import OutputPanel
from .editor_widgets import Button

class CodeEditor:

    def __init__(self, challenge):
        
        self.challenge = challenge

        self.text_buffer = TextBuffer()

        self.renderer = EditorRenderer()

        self.problem_panel = ProblemPanel(challenge)

        self.output_panel = OutputPanel()

        self.challenge_manager = ChallengeManager()

        self.running = False

        self.finished = False

        self.result = False

        self.buttons = [

            Button(
                WINDOW_WIDTH - 410,
                WINDOW_HEIGHT - 55,
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
                "Run"
            ),

            Button(
                WINDOW_WIDTH - 275,
                WINDOW_HEIGHT - 55,
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
                "Submit"
            ),

            Button(
                WINDOW_WIDTH - 140,
                WINDOW_HEIGHT - 55,
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
                "Exit"
            )

        ]

    def validate(self):

        self.output_panel.clear()

        code = self.text_buffer.text

        success, message = self.challenge_manager.validate(

        self.challenge,

        code

    )

        self.output_panel.add(message)

        return success

    def submit(self):

        passed = self.validate()

        if passed:

            self.output_panel.add("Challenge Complete!")

            self.finished = True

            self.result = True

        else:

            self.output_panel.add("Challenge Failed.")

    def handle_buttons(self, event):

        if self.buttons[0].clicked(event):

            self.output_panel.clear()

            self.validate()

        elif self.buttons[1].clicked(event):

            self.output_panel.clear()

            self.submit()

        elif self.buttons[2].clicked(event):

            self.running = False

    def draw(self, screen):

        self.problem_panel.draw(screen)

        self.renderer.draw(

            screen,

            self.challenge,

            self.text_buffer,

            self.output_panel,

            self.buttons

        )

    def handle_events(self, event):

        if event.type == pygame.QUIT:

            self.running = False

            return

        self.text_buffer.handle_event(event)

        self.handle_buttons(event)

    def run(self, screen):

        clock = pygame.time.Clock()

        self.running = True

        while self.running:

            clock.tick(FPS)

            for event in pygame.event.get():

                self.handle_events(event)

            self.draw(screen)

        return self.result