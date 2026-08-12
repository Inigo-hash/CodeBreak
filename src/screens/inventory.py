"""
inventory.py

Minecraft-style inventory system for CodeBreak.

This module contains two cooperating pieces:

    Toolbar         - the always-visible row of 5 slots pinned to the bottom
                      centre of the screen. Shows the items the player has
                      equipped. One slot is "selected" at a time (like
                      Minecraft's hotbar) and gets a brighter gold frame.

    InventoryScreen - the full bag screen. Opened with the B key. It slides up
                      from the bottom of the screen while the frozen game
                      snapshot behind it is progressively blurred and darkened.

Both classes share a single ``PlayerInventory`` data object so the toolbar and
the bag always show the same underlying items. Right now the bag starts empty -
the data model exists so items can simply be ``add_item(...)``-ed later without
touching any of the drawing code.

Visual style deliberately matches the rest of the game's UI (profile.py,
settings.py, the pause menu): dark stone panels, a metal-grey frame and the
consolas font.

A note on where this file lives: everything here sits in screens/ for now,
even though Toolbar is really a passive widget of the kind that normally
belongs in src/ui/, and PlayerInventory/Item are plain game data rather than
UI at all. Keeping the three together while the feature is young means one
file to open. If the inventory grows - saving to disk, item tooltips,
drag-and-drop between slots - the natural split is:

    PlayerInventory + Item -> src/entities/inventory.py   (game state)
    Toolbar                -> src/ui/toolbar.py           (passive widget)
    InventoryScreen        -> stays here                  (owns its own loop)

The shared _draw_slot() helper is what both halves need, so it would move to
src/ui/ alongside Toolbar.
"""

import pygame


# ---------------------------------------------------------------------------
# Palette - kept identical to profile.py / settings.py so the new UI does not
# look bolted on. Change these in one place to restyle the whole inventory.
# ---------------------------------------------------------------------------
PANEL_BG      = (36, 38, 48)    # outer panel fill
PANEL_INNER   = (26, 28, 36)    # inset area inside the panel
SLOT_BG       = (20, 22, 28)    # empty slot interior
SLOT_BORDER   = (90, 94, 110)   # normal slot frame ("metal")
SLOT_HOVER    = (140, 146, 165) # slot frame when the mouse is over it
SLOT_SELECTED = (255, 220, 120) # slot frame of the active toolbar slot (gold)
METAL_FRAME   = (90, 94, 110)   # panel border
TEXT_MAIN     = (255, 255, 255)
TEXT_DIM      = (150, 155, 170)

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
TOOLBAR_SLOTS   = 5    # number of equipped/hotbar slots (task requirement)
BAG_COLS        = 5    # bag grid columns - matches the toolbar so it lines up
BAG_ROWS        = 4    # bag grid rows -> 5 x 4 = 20 bag slots

SLOT_SIZE       = 54   # width & height of a single square slot (symmetric)
SLOT_GAP        = 6    # uniform gap between slots, keeps them evenly spaced
TOOLBAR_PADDING = 6    # padding between the slot row and its backing panel
TOOLBAR_BOTTOM_MARGIN = 16  # gap between the toolbar panel and screen bottom

# Duration of the inventory slide-up animation, in seconds.
SLIDE_DURATION = 0.28


# ===========================================================================
#  DATA MODEL
# ===========================================================================
class Item:
    """
    A single inventory item.

    Kept intentionally tiny for now. ``icon`` may be None, in which case the
    slot renderer falls back to drawing the first letter of the item's name.
    """

    def __init__(self, name, icon=None, count=1, description=""):
        self.name = name                # display name, e.g. "Rusty Sword"
        self.icon = icon                # optional pygame.Surface
        self.count = count              # stack size, drawn in the corner
        self.description = description  # reserved for a future tooltip


class PlayerInventory:
    """
    Holds every item the player owns.

    Storage is two flat lists of fixed length. A ``None`` entry means the slot
    is empty. Fixed-length lists (instead of a growing list) mean slot indices
    stay stable, so the UI can map a slot rectangle straight to a list index.
    """

    def __init__(self):
        # The 5 equipped items shown on the toolbar.
        self.toolbar = [None] * TOOLBAR_SLOTS
        # The 20 bag slots shown when the inventory screen is open.
        self.bag = [None] * (BAG_COLS * BAG_ROWS)
        # Which toolbar slot is currently active (0-based).
        self.selected = 0

    # -- selection helpers --------------------------------------------------
    def select(self, index):
        """Select a toolbar slot directly (used by the 1-5 number keys)."""
        if 0 <= index < TOOLBAR_SLOTS:
            self.selected = index

    def scroll_selection(self, direction):
        """
        Move the selection by ``direction`` steps, wrapping around at both
        ends - this is what the mouse wheel calls. direction is -1 or +1.
        """
        self.selected = (self.selected + direction) % TOOLBAR_SLOTS

    def get_selected_item(self):
        """Return the Item in the active toolbar slot, or None if empty."""
        return self.toolbar[self.selected]

    # -- item helpers -------------------------------------------------------
    def add_item(self, item):
        """
        Put an item into the first free slot: toolbar first, then the bag.
        Returns True on success, False if there is no room left anywhere.
        """
        for i, slot in enumerate(self.toolbar):
            if slot is None:
                self.toolbar[i] = item
                return True
        for i, slot in enumerate(self.bag):
            if slot is None:
                self.bag[i] = item
                return True
        return False  # everything is full

    def is_empty(self):
        """True when the player carries nothing at all."""
        return all(s is None for s in self.toolbar + self.bag)


# ===========================================================================
#  SHARED DRAWING HELPERS
# ===========================================================================
def _draw_slot(surface, rect, item, font, border_color, alpha=255):
    """
    Draw one square inventory slot: dark interior, coloured frame, and the
    item (icon or letter fallback) plus its stack count if the slot is filled.

    ``alpha`` lets a caller fade the whole slot in/out without duplicating any
    of this drawing code.
    """
    # Draw onto a temporary transparent surface so alpha applies to everything.
    slot_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    local = pygame.Rect(0, 0, rect.width, rect.height)

    # Slot interior + frame.
    pygame.draw.rect(slot_surf, SLOT_BG, local, border_radius=4)
    pygame.draw.rect(slot_surf, border_color, local, 2, border_radius=4)

    if item is not None:
        if item.icon is not None:
            # Scale the icon so it sits comfortably inside the slot.
            pad = 8
            icon = pygame.transform.smoothscale(
                item.icon, (rect.width - pad * 2, rect.height - pad * 2)
            )
            slot_surf.blit(icon, (pad, pad))
        else:
            # No artwork yet - show the item's initial as a placeholder.
            letter = font.render(item.name[:1].upper(), True, TEXT_MAIN)
            slot_surf.blit(
                letter,
                (local.centerx - letter.get_width() // 2,
                 local.centery - letter.get_height() // 2)
            )

        # Stack count in the bottom-right corner, only when actually stacked.
        if item.count > 1:
            count = font.render(str(item.count), True, TEXT_MAIN)
            slot_surf.blit(count, (local.right - count.get_width() - 4,
                                   local.bottom - count.get_height() - 3))

    slot_surf.set_alpha(alpha)
    surface.blit(slot_surf, rect.topleft)


def _build_slot_grid(cols, rows, left, top):
    """
    Build a list of evenly spaced, identically sized slot rectangles.

    Because every slot uses the same SLOT_SIZE and SLOT_GAP, the resulting grid
    is perfectly symmetric. Rectangles come back in reading order (left to
    right, top to bottom) so index 0 is the top-left slot.
    """
    rects = []
    for row in range(rows):
        for col in range(cols):
            rects.append(pygame.Rect(
                left + col * (SLOT_SIZE + SLOT_GAP),
                top + row * (SLOT_SIZE + SLOT_GAP),
                SLOT_SIZE,
                SLOT_SIZE
            ))
    return rects


def grid_pixel_width(cols):
    """Total pixel width taken by ``cols`` slots including the gaps between."""
    return cols * SLOT_SIZE + (cols - 1) * SLOT_GAP


def grid_pixel_height(rows):
    """Total pixel height taken by ``rows`` slots including the gaps."""
    return rows * SLOT_SIZE + (rows - 1) * SLOT_GAP


# ===========================================================================
#  TOOLBAR  (the always-on-screen hotbar)
# ===========================================================================
class Toolbar:
    """
    The 5-slot hotbar drawn at the bottom-centre of the screen.

    Usage from the game loop:

        toolbar = Toolbar(screen, player_inventory)
        ...
        toolbar.handle_event(event)   # inside the event loop
        toolbar.draw(mouse_pos)       # once per frame, after the world
    """

    def __init__(self, screen, inventory):
        self.screen = screen
        self.inventory = inventory
        self.screen_w, self.screen_h = screen.get_size()

        # Fonts: one for the item letter/count, a smaller one for slot numbers.
        self.font_item = pygame.font.SysFont("consolas", 20, bold=True)
        self.font_index = pygame.font.SysFont("consolas", 12, bold=True)
        self.font_label = pygame.font.SysFont("consolas", 14, bold=True)

        # --- Geometry -----------------------------------------------------
        # The row of slots is horizontally centred, and the backing panel is
        # just the row inflated by TOOLBAR_PADDING on every side, so the whole
        # widget stays symmetric no matter the screen size.
        row_w = grid_pixel_width(TOOLBAR_SLOTS)
        row_h = SLOT_SIZE
        row_left = (self.screen_w - row_w) // 2
        row_top = self.screen_h - TOOLBAR_BOTTOM_MARGIN - TOOLBAR_PADDING - row_h

        self.slot_rects = _build_slot_grid(TOOLBAR_SLOTS, 1, row_left, row_top)
        self.panel_rect = pygame.Rect(
            row_left - TOOLBAR_PADDING,
            row_top - TOOLBAR_PADDING,
            row_w + TOOLBAR_PADDING * 2,
            row_h + TOOLBAR_PADDING * 2
        )

    # -- input --------------------------------------------------------------
    def handle_event(self, event):
        """
        Handle hotbar input. Returns True if the event was consumed, so the
        caller can skip its own handling for that event.

        Supported:
          * number keys 1-5      -> select that slot directly
          * mouse wheel up/down  -> cycle the selection, wrapping around
          * left click on a slot -> select it
        """
        if event.type == pygame.KEYDOWN:
            # pygame.K_1 .. pygame.K_5 are consecutive keycodes, so subtracting
            # K_1 converts the keycode straight into a 0-based slot index.
            if pygame.K_1 <= event.key <= pygame.K_1 + TOOLBAR_SLOTS - 1:
                self.inventory.select(event.key - pygame.K_1)
                return True

        if event.type == pygame.MOUSEWHEEL:
            # event.y is +1 scrolling up, -1 scrolling down. Scrolling up moves
            # the selection left, which matches Minecraft's behaviour.
            if event.y != 0:
                self.inventory.scroll_selection(-1 if event.y > 0 else 1)
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.slot_rects):
                if rect.collidepoint(event.pos):
                    self.inventory.select(i)
                    return True

        return False

    # -- drawing ------------------------------------------------------------
    def draw(self, mouse_pos=(-1, -1)):
        """Draw the hotbar panel, its 5 slots and the held item's name."""
        # Semi-transparent backing panel so the world stays a little visible.
        panel = pygame.Surface(self.panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (*PANEL_BG, 200),
                         panel.get_rect(), border_radius=8)
        pygame.draw.rect(panel, METAL_FRAME,
                         panel.get_rect(), 2, border_radius=8)
        self.screen.blit(panel, self.panel_rect.topleft)

        # Individual slots.
        for i, rect in enumerate(self.slot_rects):
            if i == self.inventory.selected:
                border = SLOT_SELECTED          # active slot -> gold frame
            elif rect.collidepoint(mouse_pos):
                border = SLOT_HOVER             # mouse-over -> lighter frame
            else:
                border = SLOT_BORDER            # idle
            _draw_slot(self.screen, rect, self.inventory.toolbar[i],
                       self.font_item, border)

            # The selected slot also gets an outer ring so it is obvious at a
            # glance which item is currently in hand.
            if i == self.inventory.selected:
                pygame.draw.rect(self.screen, SLOT_SELECTED,
                                 rect.inflate(6, 6), 2, border_radius=6)

            # Small slot number (1-5) in the top-left corner of each slot.
            num = self.font_index.render(str(i + 1), True, TEXT_DIM)
            self.screen.blit(num, (rect.left + 4, rect.top + 2))

        # Name of the currently held item, centred just above the toolbar.
        held = self.inventory.get_selected_item()
        if held is not None:
            label = self.font_label.render(held.name, True, TEXT_MAIN)
            self.screen.blit(
                label,
                (self.panel_rect.centerx - label.get_width() // 2,
                 self.panel_rect.top - label.get_height() - 6)
            )


# ===========================================================================
#  INVENTORY SCREEN  (the B-key bag)
# ===========================================================================
class InventoryScreen:
    """
    The full-screen bag panel.

    It runs its own small event loop (same pattern as profile_screen) so the
    game loop only needs one call to open it. While it is open the game world
    is frozen: the snapshot taken at open time is what gets blurred.

    The opening animation does two things at once, driven by a single 0..1
    progress value:
        * the panel slides up from below the bottom edge into place
        * the background blur and dark overlay ramp up from none to full
    """

    def __init__(self, screen, inventory, background=None):
        self.screen = screen
        self.inventory = inventory
        self.screen_w, self.screen_h = screen.get_size()

        # Frozen snapshot of the game that we blur behind the panel.
        self.background = background if background is not None else screen.copy()

        self.font_title = pygame.font.SysFont("consolas", 26, bold=True)
        self.font_section = pygame.font.SysFont("consolas", 14, bold=True)
        self.font_item = pygame.font.SysFont("consolas", 20, bold=True)
        self.font_index = pygame.font.SysFont("consolas", 12, bold=True)
        self.font_hint = pygame.font.SysFont("consolas", 14, bold=True)
        self.font_empty = pygame.font.SysFont("consolas", 16, bold=True)

        # --- Panel geometry ------------------------------------------------
        # Sized from the grid itself, so the slots are always perfectly centred
        # and evenly padded no matter what the layout constants above say.
        grid_w = grid_pixel_width(BAG_COLS)
        grid_h = grid_pixel_height(BAG_ROWS)

        side_padding = 34
        bag_top = 70          # y of the bag grid inside the panel
        equipped_gap = 46     # vertical space between bag grid and equipped row

        self.panel_w = grid_w + side_padding * 2
        # vertical budget: title area + bag grid + gap + equipped row + hint
        self.panel_h = bag_top + grid_h + equipped_gap + SLOT_SIZE + 54

        self.panel_x = (self.screen_w - self.panel_w) // 2
        # Final resting Y - vertically centred on screen.
        self.panel_final_y = (self.screen_h - self.panel_h) // 2

        # Slot rectangles are stored relative to the panel's top-left corner,
        # so the slide animation only has to offset the panel once per frame.
        self.bag_rects_local = _build_slot_grid(
            BAG_COLS, BAG_ROWS, side_padding, bag_top
        )
        self.equipped_rects_local = _build_slot_grid(
            TOOLBAR_SLOTS, 1, side_padding, bag_top + grid_h + equipped_gap
        )

        # Animation state: 0.0 = fully off-screen, 1.0 = fully open.
        self.progress = 0.0

    # -- animation ----------------------------------------------------------
    @staticmethod
    def _ease_out(t):
        """
        Cubic ease-out. Makes the panel shoot up quickly then settle gently,
        which reads as much smoother than a constant-speed slide.
        """
        return 1 - pow(1 - t, 3)

    def _current_panel_y(self):
        """
        Y position for this frame. At progress 0 the panel starts just below
        the bottom edge of the screen; at progress 1 it is at its final spot.
        """
        eased = self._ease_out(self.progress)
        start_y = self.screen_h            # completely off-screen (bottom)
        return int(start_y + (self.panel_final_y - start_y) * eased)

    # -- drawing ------------------------------------------------------------
    def _draw_background(self):
        """
        Draw the frozen game snapshot, blurred and darkened in proportion to
        the animation progress so the blur "grows in" as the panel rises.
        """
        # Downscale-then-upscale is the same cheap blur used by profile.py and
        # the pause menu. A bigger divisor = blurrier, so we ramp the divisor
        # from 1 (sharp) up to 8 (fully blurred) as the panel slides up.
        eased = self._ease_out(self.progress)
        divisor = 1 + 7 * eased
        small_w = max(1, int(self.screen_w / divisor))
        small_h = max(1, int(self.screen_h / divisor))

        small = pygame.transform.smoothscale(self.background, (small_w, small_h))
        blurred = pygame.transform.smoothscale(small, (self.screen_w, self.screen_h))
        self.screen.blit(blurred, (0, 0))

        # Dark overlay fades in alongside the blur.
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(140 * eased)))
        self.screen.blit(overlay, (0, 0))

    def _draw_panel(self, mouse_pos):
        """Draw the bag panel at its current animated position."""
        panel_y = self._current_panel_y()
        panel_rect = pygame.Rect(self.panel_x, panel_y, self.panel_w, self.panel_h)

        # Panel body: outer fill, metal border, inset darker area - the same
        # three-layer look as the profile screen.
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, METAL_FRAME, panel_rect, 4, border_radius=10)
        pygame.draw.rect(self.screen, PANEL_INNER,
                         panel_rect.inflate(-14, -14), border_radius=8)

        # Title.
        title = self.font_title.render("INVENTORY", True, TEXT_MAIN)
        self.screen.blit(title,
                         (panel_rect.centerx - title.get_width() // 2,
                          panel_rect.top + 20))

        # --- Bag grid -------------------------------------------------------
        first_bag = self.bag_rects_local[0]
        bag_label = self.font_section.render("BAG", True, TEXT_DIM)
        self.screen.blit(bag_label,
                         (panel_rect.left + first_bag.left,
                          panel_rect.top + first_bag.top - 18))

        for i, local in enumerate(self.bag_rects_local):
            # Convert the panel-relative rect into screen coordinates.
            rect = local.move(panel_rect.left, panel_rect.top)
            border = SLOT_HOVER if rect.collidepoint(mouse_pos) else SLOT_BORDER
            _draw_slot(self.screen, rect, self.inventory.bag[i],
                       self.font_item, border)

        # "Your bag is empty" note, centred over the grid while it has no items.
        if all(slot is None for slot in self.inventory.bag):
            last_bag = self.bag_rects_local[-1]
            grid_rect = pygame.Rect(
                panel_rect.left + first_bag.left,
                panel_rect.top + first_bag.top,
                last_bag.right - first_bag.left,
                last_bag.bottom - first_bag.top
            )
            note = self.font_empty.render("Your bag is empty", True, TEXT_DIM)
            self.screen.blit(note,
                             (grid_rect.centerx - note.get_width() // 2,
                              grid_rect.centery - note.get_height() // 2))

        # --- Divider between the bag and the equipped row --------------------
        first_eq = self.equipped_rects_local[0]
        divider_y = panel_rect.top + first_eq.top - 26
        pygame.draw.line(
            self.screen, METAL_FRAME,
            (panel_rect.left + 24, divider_y),
            (panel_rect.right - 24, divider_y), 2
        )

        # --- Equipped (toolbar) row, mirrored inside the panel ---------------
        eq_label = self.font_section.render("EQUIPPED", True, TEXT_DIM)
        self.screen.blit(eq_label,
                         (panel_rect.left + first_eq.left,
                          panel_rect.top + first_eq.top - 18))

        for i, local in enumerate(self.equipped_rects_local):
            rect = local.move(panel_rect.left, panel_rect.top)
            if i == self.inventory.selected:
                border = SLOT_SELECTED
            elif rect.collidepoint(mouse_pos):
                border = SLOT_HOVER
            else:
                border = SLOT_BORDER
            _draw_slot(self.screen, rect, self.inventory.toolbar[i],
                       self.font_item, border)
            num = self.font_index.render(str(i + 1), True, TEXT_DIM)
            self.screen.blit(num, (rect.left + 4, rect.top + 2))

        # --- Close hint ------------------------------------------------------
        hint = self.font_hint.render("B or ESC to close", True, TEXT_DIM)
        self.screen.blit(hint,
                         (panel_rect.centerx - hint.get_width() // 2,
                          panel_rect.bottom - hint.get_height() - 18))

    # -- main loop ----------------------------------------------------------
    def run(self):
        """
        Show the inventory until the player closes it with B or ESC.

        Runs a self-contained loop (like profile_screen) so the caller only
        needs one line. Returns once the closing animation has finished.
        """
        clock = pygame.time.Clock()
        closing = False   # True once the player asks to close; plays in reverse

        # Drain any events queued before we opened, so the same B keypress that
        # opened this screen cannot immediately close it again.
        pygame.event.clear()

        while True:
            dt = clock.tick(60) / 1000.0  # seconds elapsed since the last frame

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_b, pygame.K_ESCAPE):
                        closing = True
                    # Number keys still change the equipped slot while open.
                    elif pygame.K_1 <= event.key <= pygame.K_1 + TOOLBAR_SLOTS - 1:
                        self.inventory.select(event.key - pygame.K_1)

                # Mouse wheel also cycles the equipped slot, same as the hotbar.
                if event.type == pygame.MOUSEWHEEL and event.y != 0:
                    self.inventory.scroll_selection(-1 if event.y > 0 else 1)

                # Clicking an equipped slot inside the panel selects it.
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    panel_y = self._current_panel_y()
                    for i, local in enumerate(self.equipped_rects_local):
                        if local.move(self.panel_x, panel_y).collidepoint(event.pos):
                            self.inventory.select(i)

            # Advance the slide animation - forwards while opening, backwards
            # while closing. Both directions reuse the same easing curve.
            step = dt / SLIDE_DURATION
            if closing:
                self.progress = max(0.0, self.progress - step)
            else:
                self.progress = min(1.0, self.progress + step)

            mouse_pos = pygame.mouse.get_pos()
            self._draw_background()
            self._draw_panel(mouse_pos)
            pygame.display.flip()

            # Once the close animation has fully played out, hand control back.
            if closing and self.progress <= 0.0:
                return


def open_inventory(screen, inventory, background=None):
    """
    Convenience wrapper so the game loop can open the bag in one line:

        open_inventory(screen, player_inventory, screen.copy())
    """
    InventoryScreen(screen, inventory, background).run()
