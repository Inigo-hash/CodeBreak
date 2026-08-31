"""Menu buttons have to hold their own labels.

"RETURN TO MAIN MENU" is the longest label in the game and used to render
past the right rim of its button, because the width was a fixed share of
the screen while the label was not.
"""

from contextlib import ExitStack
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()

import src.screens.main_menu as main_menu
from src.screens.main_menu import (
    LABEL_RIM_MARGIN, MEDALLION_CLEARANCE, MM_LABELS, compute_menu_layout,
    menu_button_width,
)
from src.screens.start_game_menu import SG_LABELS, start_menu_layout

SCREEN_WIDTHS = (1280, 1600, 1920, 2560)


class MenuButtonFitTests(unittest.TestCase):
    def label_room(self, width):
        """Pixels a label may use between the medallion and the rim."""

        return width - MEDALLION_CLEARANCE - LABEL_RIM_MARGIN

    def test_every_menu_label_fits_its_button(self):
        for labels in (MM_LABELS, SG_LABELS):
            for screen_width in SCREEN_WIDTHS:
                width = menu_button_width(screen_width, labels)
                for label in labels:
                    with self.subTest(label=label, screen_width=screen_width):
                        self.assertLessEqual(
                            main_menu._button_font.size(label)[0],
                            self.label_room(width),
                        )

    def test_the_longest_label_is_what_widens_the_button(self):
        short = menu_button_width(1920, ["QUIT"])
        long = menu_button_width(1920, ["RETURN TO MAIN MENU"])
        self.assertGreater(long, short)

    def test_layout_uses_the_fitted_width_for_every_row(self):
        rects, bw, *_ = compute_menu_layout(1920, 1080, len(SG_LABELS), SG_LABELS)

        self.assertEqual(bw, menu_button_width(1920, SG_LABELS))
        self.assertTrue(all(rect.width == bw for rect in rects))
        # Rows stay centred on the screen whatever the width works out to.
        self.assertTrue(all(rect.centerx == 1920 // 2 for rect in rects))

    def test_a_caller_that_passes_no_labels_keeps_the_plain_width(self):
        self.assertEqual(menu_button_width(1920), int(1920 * 0.20))
        rects, *_ = compute_menu_layout(1920, 1080, 3)
        self.assertEqual(rects[0].width, int(1920 * 0.20))

    def test_short_menus_are_not_widened_at_all(self):
        self.assertEqual(
            menu_button_width(1920, MM_LABELS), menu_button_width(1920)
        )


class TransitionTargetTests(unittest.TestCase):
    """The crumble must assemble into the buttons the next screen draws.

    It used to build its own layout from the wrong menu's labels, so the
    debris settled into main-menu-sized buttons that snapped wider the
    instant the start-game menu took over.
    """

    def test_start_game_transition_assembles_into_the_start_menu_buttons(self):
        clicked = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": compute_menu_layout(
                main_menu.SCREEN_WIDTH, main_menu.SCREEN_HEIGHT,
                3, MM_LABELS,
            )[0][0].center, "button": 1},
        )
        frames = [[clicked]]
        pumped = [0]

        def scripted(*_args, **_kwargs):
            index = pumped[0]
            pumped[0] += 1
            return frames[index] if index < len(frames) else []

        silenced = (
            patch("src.screens.intro.opening_walkthrough"),
            patch("src.ui.transitions.crumble_transition"),
            patch("src.screens.start_game_menu.start_game_menu",
                  side_effect=SystemExit),
            patch("pygame.event.get", scripted),
            patch("pygame.display.flip"),
            patch("pygame.mixer.music.load"),
            patch("pygame.mixer.music.play"),
        )
        with ExitStack() as stack:
            crumble = [stack.enter_context(p) for p in silenced][1]
            with self.assertRaises(SystemExit):
                main_menu.main_menu()

        self.assertTrue(crumble.called, "the transition never ran")
        assembled_into = crumble.call_args[0][5]
        expected = start_menu_layout(
            main_menu.SCREEN_WIDTH, main_menu.SCREEN_HEIGHT
        )
        self.assertEqual(
            [tuple(rect) for rect in assembled_into],
            [tuple(rect) for rect in expected],
        )


if __name__ == "__main__":
    unittest.main()
