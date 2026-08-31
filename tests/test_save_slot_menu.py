"""Deleting a save from the slot panel, and modals owning the menu behind.

The menu is driven for real: scripted events are fed one list per frame,
exactly as pygame would deliver them, and the assertions are made against
the save files the menu actually writes and removes.

Coordinates are in the game's 1920x1080 canvas space. src/display.py
normally remaps window coordinates onto that canvas; setting its window to
None makes the positions here literal.
"""

import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()

# Importing main_menu creates the real display and installs display.py's
# event/mouse wrappers, so it has to happen before anything is patched.
import src.screens.main_menu as main_menu
import src.display as display

display._window = None

from src.systems import save_manager
from src.screens.start_game_menu import (
    DELETE_BUTTON_SIZE, SG_LABELS, slot_layout, start_game_menu,
)

CANVAS = (display.BASE_WIDTH, display.BASE_HEIGHT)


def panel_rect():
    """The slot panel geometry start_game_menu builds for the canvas."""

    width, height = CANVAS
    rect = pygame.Rect(0, 0, min(720, width - 60), min(620, height - 50))
    rect.center = (width // 2, height // 2)
    return rect


def confirm_buttons():
    """Centres of the confirmation modal's two buttons."""

    width, height = CANVAS
    confirm = pygame.Rect(width // 2 - 240, height // 2 - 100, 480, 200)
    yes = pygame.Rect(confirm.centerx - 160, confirm.bottom - 58, 140, 42)
    no = pygame.Rect(confirm.centerx + 20, confirm.bottom - 58, 140, 42)
    return yes.center, no.center


def click(position):
    return pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"pos": position, "button": 1}
    )


class SlotLayoutTests(unittest.TestCase):
    def test_delete_button_sits_inside_its_own_slot_row(self):
        slots, deletes = slot_layout(panel_rect(), 3)

        self.assertEqual(len(deletes), len(slots))
        for slot, delete in zip(slots, deletes):
            self.assertTrue(slot.contains(delete))
            self.assertEqual(delete.size, (DELETE_BUTTON_SIZE, DELETE_BUTTON_SIZE))

    def test_each_delete_button_belongs_to_exactly_one_slot(self):
        slots, deletes = slot_layout(panel_rect(), 3)

        for index, delete in enumerate(deletes):
            owners = [i for i, slot in enumerate(slots) if slot.colliderect(delete)]
            self.assertEqual(owners, [index])


class SlotMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.screen = pygame.Surface(CANVAS)
        rects, *_ = main_menu.compute_menu_layout(*CANVAS, len(SG_LABELS))
        cls.new_game_button = rects[0].center
        cls.continue_button = rects[1].center
        cls.return_button = rects[2].center
        cls.slots, cls.deletes = slot_layout(panel_rect(), save_manager.NUM_SLOTS)
        cls.confirm_yes, cls.confirm_no = confirm_buttons()

    def setUp(self):
        saves = tempfile.TemporaryDirectory()
        self.addCleanup(saves.cleanup)
        patcher = patch.object(save_manager, "SAVE_DIR", saves.name)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_menu(self, frames, budget=40):
        """Play scripted frames, then QUIT so the menu loop ends.

        Returns True when the menu returned on its own before the QUIT,
        which is how a leaked click on a menu button shows up.
        """

        pumped = [0]

        def scripted(*_args, **_kwargs):
            index = pumped[0]
            pumped[0] += 1
            if index < len(frames):
                return frames[index]
            if index > budget:
                return [pygame.event.Event(pygame.QUIT)]
            return []

        with patch("pygame.event.get", scripted), \
                patch("pygame.display.flip"), patch("pygame.quit"):
            try:
                start_game_menu(self.screen)
                return True
            except SystemExit:
                return False

    def test_delete_button_erases_an_unprotected_save(self):
        save_manager.save_slot(1, save_manager.new_game_state())
        self.assertTrue(save_manager.slot_exists(1))

        self.run_menu([
            [click(self.continue_button)],       # open CHOOSE YOUR ADVENTURE
            [click(self.deletes[0].center)],     # tap the slot's X
            [click(self.confirm_yes)],           # confirm DELETE
        ])

        self.assertFalse(save_manager.slot_exists(1))

    def test_keeping_the_save_leaves_it_alone(self):
        save_manager.save_slot(2, save_manager.new_game_state())

        self.run_menu([
            [click(self.continue_button)],
            [click(self.deletes[1].center)],
            [click(self.confirm_no)],            # KEEP
        ])

        self.assertTrue(save_manager.slot_exists(2))

    def test_a_protected_save_needs_its_password_before_deletion(self):
        state = save_manager.protect_state(save_manager.new_game_state(), "hunter2")
        save_manager.save_slot(3, state)

        self.run_menu([
            [click(self.continue_button)],
            [click(self.deletes[2].center)],
            [click(self.confirm_yes)],           # opens the password modal
        ])

        self.assertTrue(save_manager.slot_exists(3))

    def test_delete_is_offered_in_the_new_game_panel_too(self):
        save_manager.save_slot(1, save_manager.new_game_state())

        self.run_menu([
            [click(self.new_game_button)],       # CHOOSE A SLOT FOR A NEW GAME
            [click(self.deletes[0].center)],
            [click(self.confirm_yes)],
        ])

        self.assertFalse(save_manager.slot_exists(1))

    def test_an_empty_slot_has_nothing_to_delete(self):
        self.assertFalse(save_manager.slot_exists(1))

        left_early = self.run_menu([
            [click(self.continue_button)],
            [click(self.deletes[0].center)],
            [click(self.confirm_yes)],
        ])

        self.assertFalse(save_manager.slot_exists(1))
        # The stray confirm click must not have escaped the panel either.
        self.assertFalse(left_early)

    def test_menu_buttons_behind_the_panel_cannot_be_clicked(self):
        """RETURN TO MAIN MENU sits under the panel; it must stay inert."""

        left_early = self.run_menu([
            [click(self.continue_button)],
            [click(self.return_button)],
        ])

        self.assertFalse(left_early)


if __name__ == "__main__":
    unittest.main()
