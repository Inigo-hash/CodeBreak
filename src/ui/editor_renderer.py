"""
editor_renderer.py

Draws the entire CodeBreak coding environment.

Responsibilities:
- Draw background
- Draw header
- Draw objective pane   (left)
- Draw code editor pane (center)
- Draw output pane      (right)
- Draw the draggable dividers between those panes
- Draw button area

Layout
------
The popup body is one horizontal row of three panes:

    [ objective ] || [ code editor ] || [ output ]

The two dividers ("||") can be dragged by the player, so the space
each pane gets is not fixed. Their positions are stored as
fractions of the body width - never as pixel values - so the layout
stays correct on any window size and survives a window resize.

This class ONLY draws (and works out where things go).
It does not handle typing, validation, or game logic.
"""

import pygame

from src.ui.editor_widgets import Button, VerticalScrollbar
from src.ui.output_panel import OutputPanel
from src.ui.problem_panel import ProblemPanel
from src.ui.editor_theme import *
from src.ui.syntax_highlighter import highlight_line, compute_line_states
from src.ui.gear_icon import draw_gear_medallion

# Extra pixels around a divider that still count as "on" it, so the
# player does not have to hit a 10px target exactly.
SPLITTER_GRAB_MARGIN = 3

# The EXIT button parked in the title bar, left of the settings wheel.
EXIT_BUTTON_WIDTH = 92

EXIT_BUTTON_HEIGHT = 36

# Gap between the EXIT button and the settings wheel beside it.
EXIT_BUTTON_GAP = 10


class EditorRenderer:
    """
    Responsible for drawing every visual part
    of the coding environment.
    """

    def __init__(self, screen, challenge, text_buffer, background=None):

        self.screen = screen
        self.challenge = challenge
        self.text_buffer = text_buffer
        self.background = background
        self.last_input_time = 0
        self.scroll_offset = 0

        # Horizontal scroll, in pixels. The editor pane is only one
        # of three now, so a long line no longer always fits - this
        # slides the code sideways to keep the cursor in view.
        self.h_scroll_offset = 0

        # UI Components
        self.problem_panel = ProblemPanel(challenge)
        self.output_panel = OutputPanel()

        # Scrollbar of the code editor itself. The objective and
        # output panes own theirs, since they scroll independently.
        self.editor_scrollbar = VerticalScrollbar()

        # ----------------------------------
        # Divider Positions
        # ----------------------------------
        # Stored as fractions of the body width:
        # 0.0 is the far left edge, 1.0 the far right edge.

        self.left_split = DEFAULT_LEFT_SPLIT
        self.right_split = DEFAULT_RIGHT_SPLIT

        # Name of the divider the mouse is currently over
        # ("left", "right" or None). Only used for highlighting.
        self.hovered_splitter = None

        # ----------------------------------
        # Buttons
        # ----------------------------------
        # Created once here and repositioned by the layout pass, so
        # CodeEditor can safely hold on to these exact objects.

        self.run_button = Button(
            0, 0, BUTTON_WIDTH, BUTTON_HEIGHT - 10, "RUN", "secondary"
        )
        self.submit_button = Button(
            0, 0, BUTTON_WIDTH, BUTTON_HEIGHT - 10, "SUBMIT", "primary"
        )

        # Leaving lives in the title bar, next to the settings wheel -
        # NOT in the action row. Typed code is not saved yet, so a button
        # that throws it away must not sit a few pixels from SUBMIT.
        self.exit_button = Button(
            0, 0, EXIT_BUTTON_WIDTH, EXIT_BUTTON_HEIGHT, "EXIT", "tertiary"
        )

        # Window size the current layout was built for. Comparing
        # against it each frame is what lets the editor survive the
        # window being resized while it is open.
        self._layout_screen_size = None

        self.apply_layout()

    # ==================================================
    # Layout
    # ==================================================

    def _compute_panel_rect(self):
        """
        Work out how big the popup should be for the current window.

        The popup takes up most of the window, but never grows past
        the maximum bounds (so it stays readable on a big monitor)
        and never spills outside a small window.
        """

        screen_width, screen_height = self.screen.get_size()

        width = min(
            PANEL_MAX_WIDTH,
            max(
                PANEL_MIN_WIDTH,
                int(screen_width * PANEL_SCREEN_RATIO_X)
            )
        )

        height = min(
            PANEL_MAX_HEIGHT,
            max(
                PANEL_MIN_HEIGHT,
                int(screen_height * PANEL_SCREEN_RATIO_Y)
            )
        )

        # Never let the popup hang off the edge of a small window.
        width = min(width, max(200, screen_width - PANEL_SCREEN_MARGIN))
        height = min(height, max(200, screen_height - PANEL_SCREEN_MARGIN))

        panel_rect = pygame.Rect(0, 0, width, height)
        panel_rect.center = self.screen.get_rect().center

        return panel_rect

    def _clamp_splits(self, body_width):
        """
        Keep both dividers in a sane place:
        - in order (left divider always left of the right one)
        - far enough apart that no pane gets squashed to nothing
        """

        if body_width <= 0:
            return

        half = SPLITTER_WIDTH / 2

        left_pixels = self.left_split * body_width
        right_pixels = self.right_split * body_width

        # Width the body needs before the minimum pane sizes can
        # all be honored at once.
        required_width = (
            (MIN_SIDE_PANE_WIDTH * 2)
            + MIN_EDITOR_PANE_WIDTH
            + (SPLITTER_WIDTH * 2)
        )

        if body_width >= required_width:

            leftmost = MIN_SIDE_PANE_WIDTH + half
            rightmost = body_width - MIN_SIDE_PANE_WIDTH - half

            left_pixels = max(
                leftmost,
                min(
                    left_pixels,
                    rightmost - MIN_EDITOR_PANE_WIDTH - SPLITTER_WIDTH
                )
            )

            right_pixels = max(
                left_pixels + MIN_EDITOR_PANE_WIDTH + SPLITTER_WIDTH,
                min(right_pixels, rightmost)
            )

        else:

            # Window too small for the minimums - just keep the
            # dividers inside the body and in the right order.
            left_pixels = max(half, min(left_pixels, body_width - half))

            right_pixels = max(
                left_pixels + SPLITTER_WIDTH,
                min(right_pixels, body_width - half)
            )

        self.left_split = left_pixels / body_width
        self.right_split = right_pixels / body_width

    def apply_layout(self):
        """
        Rebuild every rectangle from the current window size and
        divider positions.

        Called on startup, whenever a divider is dragged, and
        whenever the window size changes.
        """

        self._layout_screen_size = self.screen.get_size()

        self.panel_rect = self._compute_panel_rect()

        # ----------------------------------
        # Header (top) and Buttons (bottom)
        # ----------------------------------

        inner_width = self.panel_rect.width - (PADDING * 2)

        self.header_rect = pygame.Rect(
            self.panel_rect.x + PADDING,
            self.panel_rect.y + PADDING,
            inner_width,
            HEADER_HEIGHT
        )

        self.button_rect = pygame.Rect(
            self.panel_rect.x + PADDING,
            self.panel_rect.bottom - PADDING - BUTTON_HEIGHT,
            inner_width,
            BUTTON_HEIGHT
        )

        # Settings wheel, parked at the right end of the title bar.
        # Sized to the header so it still fits if HEADER_HEIGHT changes.
        gear_radius = max(10, HEADER_HEIGHT // 2 - 9)

        self.settings_gear_center = (
            self.header_rect.right - gear_radius - 16,
            self.header_rect.centery
        )

        self.settings_gear_radius = gear_radius

        # Clickable area, a little larger than the wheel so it is not
        # fiddly to hit.
        self.settings_gear_rect = pygame.Rect(0, 0, 0, 0)
        self.settings_gear_rect.size = (gear_radius * 2 + 12, gear_radius * 2 + 12)
        self.settings_gear_rect.center = self.settings_gear_center

        # EXIT sits immediately left of the wheel, both of them in the
        # title bar and well away from RUN / SUBMIT at the bottom.
        self.exit_button.rect.size = (EXIT_BUTTON_WIDTH, EXIT_BUTTON_HEIGHT)
        self.exit_button.rect.midright = (
            self.settings_gear_rect.left - EXIT_BUTTON_GAP,
            self.header_rect.centery
        )

        # ----------------------------------
        # Body: everything between them
        # ----------------------------------

        body_top = self.header_rect.bottom + PADDING
        body_bottom = self.button_rect.top - PADDING

        self.body_rect = pygame.Rect(
            self.panel_rect.x + PADDING,
            body_top,
            inner_width,
            max(0, body_bottom - body_top)
        )

        self._clamp_splits(self.body_rect.width)

        # ----------------------------------
        # Dividers
        # ----------------------------------

        half = SPLITTER_WIDTH // 2

        left_center = self.body_rect.x + int(
            self.left_split * self.body_rect.width
        )

        right_center = self.body_rect.x + int(
            self.right_split * self.body_rect.width
        )

        self.left_splitter_rect = pygame.Rect(
            left_center - half,
            self.body_rect.y,
            SPLITTER_WIDTH,
            self.body_rect.height
        )

        self.right_splitter_rect = pygame.Rect(
            right_center - half,
            self.body_rect.y,
            SPLITTER_WIDTH,
            self.body_rect.height
        )

        # ----------------------------------
        # The Three Panes
        # ----------------------------------

        self.problem_rect = pygame.Rect(
            self.body_rect.x,
            self.body_rect.y,
            max(0, self.left_splitter_rect.x - self.body_rect.x),
            self.body_rect.height
        )

        self.editor_column_rect = pygame.Rect(
            self.left_splitter_rect.right,
            self.body_rect.y,
            max(0, self.right_splitter_rect.x - self.left_splitter_rect.right),
            self.body_rect.height
        )

        self.output_rect = pygame.Rect(
            self.right_splitter_rect.right,
            self.body_rect.y,
            max(0, self.body_rect.right - self.right_splitter_rect.right),
            self.body_rect.height
        )

        # The editor column is split again: a small file tab on top
        # and the code area underneath. Every piece of cursor and
        # scroll math works off editor_rect (the code area only).

        self.tab_rect = pygame.Rect(
            self.editor_column_rect.x,
            self.editor_column_rect.y,
            self.editor_column_rect.width,
            EDITOR_TAB_HEIGHT
        )

        self.editor_rect = pygame.Rect(
            self.editor_column_rect.x,
            self.editor_column_rect.y + EDITOR_TAB_HEIGHT,
            self.editor_column_rect.width,
            max(0, self.editor_column_rect.height - EDITOR_TAB_HEIGHT)
        )

        # ----------------------------------
        # Button Positions
        # ----------------------------------

        # Only the two safe actions live down here now.

        spacing = 25

        total_width = (BUTTON_WIDTH * 2) + spacing

        start_x = self.panel_rect.x + (
            self.panel_rect.width - total_width
        ) // 2

        button_y = self.button_rect.y + 5

        self.run_button.rect.topleft = (start_x, button_y)

        self.submit_button.rect.topleft = (
            start_x + BUTTON_WIDTH + spacing,
            button_y
        )

        # Resizing the panes can invalidate both scroll positions
        # (a shorter editor for the vertical one, a narrower editor
        # for the horizontal one), so re-check both here.
        self.clamp_scroll_offset()

        self.clamp_horizontal_scroll()

    # ==================================================
    # Divider Dragging
    # ==================================================

    def get_splitter_at(self, position):
        """
        Return "left", "right" or None depending on which divider
        (if any) the given point is on.
        """

        left = self.left_splitter_rect.inflate(
            SPLITTER_GRAB_MARGIN * 2, 0
        )

        if left.collidepoint(position):
            return "left"

        right = self.right_splitter_rect.inflate(
            SPLITTER_GRAB_MARGIN * 2, 0
        )

        if right.collidepoint(position):
            return "right"

        return None

    def drag_splitter(self, name, mouse_x):
        """
        Move one divider to follow the mouse.

        The new position is stored as a fraction of the body width,
        then clamped by the layout pass so a pane can never be
        dragged smaller than its minimum width.
        """

        if self.body_rect.width <= 0:
            return

        fraction = (mouse_x - self.body_rect.x) / self.body_rect.width

        if name == "left":
            self.left_split = fraction
        else:
            self.right_split = fraction

        self.apply_layout()

    # ==================================================
    # Public Draw Function
    # ==================================================

    def draw(self):

        # Rebuild the layout if the window changed size while
        # the editor was open.
        if self.screen.get_size() != self._layout_screen_size:
            self.apply_layout()

        self.hovered_splitter = self.get_splitter_at(
            pygame.mouse.get_pos()
        )

        self.draw_background()

        self.draw_panel_frame()

        self.draw_header()

        self.draw_problem_panel()

        self.draw_editor_panel()

        self.draw_output_panel()

        self.draw_splitters()

        self.draw_button_panel()

    # ==================================================
    # Individual Sections
    # ==================================================

    def draw_background(self):
        """Draw the dimmed game screen behind the popup."""

        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(BACKGROUND_COLOR)

        # Dark translucent overlay so the popup reads as a popup
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

    def draw_panel_frame(self):
        """Draw the popup panel itself, behind all the sections."""

        pygame.draw.rect(
            self.screen,
            BACKGROUND_COLOR,
            self.panel_rect,
            border_radius=PANEL_RADIUS
        )
        pygame.draw.rect(
            self.screen,
            BORDER_COLOR,
            self.panel_rect,
            2,
            border_radius=PANEL_RADIUS
        )

    def draw_header(self):
        """Draw the title bar."""

        pygame.draw.rect(
            self.screen,
            HEADER_COLOR,
            self.header_rect,
            border_radius=PANEL_RADIUS
        )

        title = TITLE_FONT.render(
            f'CodeBreak - {self.challenge["title"]}',
            True,
            TEXT_COLOR
        )

        self.screen.blit(
            title,
            (self.header_rect.x + 20,
             self.header_rect.centery - title.get_height() // 2)
        )

        # A persistent three-step map answers the beginner's most common
        # question before they need to ask it: what do I do after typing?
        guide_text = "TYPE CODE    >    RUN    >    SUBMIT"
        guide = SMALL_FONT.render(guide_text, True, SECONDARY_TEXT)
        guide_rect = guide.get_rect(center=self.header_rect.center)
        title_right = self.header_rect.x + 20 + title.get_width() + 24
        if guide_rect.left >= title_right and guide_rect.right < self.exit_button.rect.left - 12:
            badge = guide_rect.inflate(22, 12)
            pygame.draw.rect(self.screen, PANEL_COLOR, badge, border_radius=badge.height // 2)
            pygame.draw.rect(self.screen, BORDER_COLOR, badge, 1,
                             border_radius=badge.height // 2)
            self.screen.blit(guide, guide_rect)

        self.exit_button.update()
        self.exit_button.draw(self.screen)

        self.draw_settings_gear()

    def draw_settings_gear(self):
        """
        Draw the settings wheel in the title bar.

        Same artwork as the main menu's settings medallion (see
        src/ui/gear_icon.py). It idles slowly and spins up on hover, so
        it reads as a button rather than decoration.
        """

        hovered = self.settings_gear_rect.collidepoint(pygame.mouse.get_pos())

        seconds = pygame.time.get_ticks() / 1000.0
        speed = 3.9 if hovered else 0.4

        draw_gear_medallion(
            self.screen,
            self.settings_gear_center,
            self.settings_gear_radius,
            spin_degrees=seconds * speed * 60
        )

    def draw_problem_panel(self):

        self.problem_panel.draw(
            self.screen,
            self.problem_rect
        )

    # ==========================================================
    # Dividers
    # ==========================================================

    def draw_splitters(self):
        """
        Draw both draggable dividers, with a little grip in the
        middle so it's obvious they can be moved.
        """

        for name, rect in (
            ("left", self.left_splitter_rect),
            ("right", self.right_splitter_rect),
        ):

            color = (
                SPLITTER_HOVER_COLOR
                if self.hovered_splitter == name
                else SPLITTER_COLOR
            )

            # A slim bar down the middle of the divider's grab area,
            # so the divider reads as a handle rather than a gap.
            bar = rect.inflate(-2, -PADDING * 2)

            pygame.draw.rect(
                self.screen,
                color,
                bar,
                border_radius=SPLITTER_WIDTH // 2
            )

            # Grip dots, centered.
            for offset in (-12, -6, 0, 6, 12):

                pygame.draw.circle(
                    self.screen,
                    SPLITTER_GRIP_COLOR,
                    (rect.centerx, rect.centery + offset),
                    2
                )

    # ==========================================================
    # Code Editor
    # ==========================================================

    def draw_editor_tab(self):
        """Draw the small file tab that sits above the code area."""

        pygame.draw.rect(
            self.screen,
            TAB_COLOR,
            self.tab_rect,
            border_top_left_radius=PANEL_RADIUS,
            border_top_right_radius=PANEL_RADIUS
        )

        # Skip the tab label itself if the pane got dragged so
        # narrow that it would not fit.
        if self.tab_rect.width < 60:
            return

        label_rect = pygame.Rect(
            self.tab_rect.x + 8,
            self.tab_rect.y + 4,
            min(110, self.tab_rect.width - 16),
            self.tab_rect.height - 4
        )

        pygame.draw.rect(
            self.screen,
            TAB_ACTIVE_COLOR,
            label_rect,
            border_top_left_radius=6,
            border_top_right_radius=6
        )

        label = SMALL_FONT.render("main.py", True, TEXT_COLOR)

        self.screen.blit(
            label,
            label.get_rect(center=label_rect.center)
        )

    def draw_editor_panel(self):
        """Draw the code editor with automatic vertical scrolling."""

        self.draw_editor_tab()

        pygame.draw.rect(
            self.screen,
            EDITOR_COLOR,
            self.editor_rect,
            border_bottom_left_radius=PANEL_RADIUS,
            border_bottom_right_radius=PANEL_RADIUS
        )

        # Outline around the tab and the code area together, so the
        # editor is framed exactly like the panes either side of it.
        pygame.draw.rect(
            self.screen,
            BORDER_COLOR,
            self.editor_column_rect,
            2,
            border_radius=PANEL_RADIUS
        )

        # ----------------------------------
        # Editor Settings
        # ----------------------------------

        line_spacing = LINE_SPACING

        max_visible_lines = self.get_max_visible_lines()

        # ----------------------------------
        # Clamp scroll to valid range (does NOT force-follow cursor)
        # ----------------------------------

        self.clamp_scroll_offset()

        # ----------------------------------
        # Draw Line Numbers
        # ----------------------------------

        visible_lines = self.text_buffer.lines[
            self.scroll_offset:
            self.scroll_offset + max_visible_lines
        ]

        for i in range(len(visible_lines)):

            line_number = self.scroll_offset + i + 1

            number = SMALL_FONT.render(
                str(line_number),
                True,
                SECONDARY_TEXT
            )

            self.screen.blit(
                number,
                (
                    self.editor_rect.x + 12,
                    self.editor_rect.y + 15 + (i * line_spacing)
                )
            )

        # ----------------------------------
        # Divider
        # ----------------------------------

        pygame.draw.line(
            self.screen,
            BORDER_COLOR,
            (
                self.editor_rect.x + LINE_NUMBER_WIDTH,
                self.editor_rect.y
            ),
            (
                self.editor_rect.x + LINE_NUMBER_WIDTH,
                self.editor_rect.bottom
            ),
            2
        )

        # ----------------------------------
        # Clip everything code-related
        # ----------------------------------
        # The code area is now only as wide as the middle pane, so a
        # long line has to be cut off at the pane's edge instead of
        # being drawn straight over the output pane next to it.

        previous_clip = self.screen.get_clip()

        self.screen.set_clip(self.get_code_area_rect())

        # ----------------------------------
        # Draw Selection Highlight
        # ----------------------------------
        # Drawn before the text so highlighted characters
        # remain fully readable on top of the highlight.

        self.draw_selection()

        # ----------------------------------
        # Draw User Code (syntax highlighted)
        # ----------------------------------

        text_x = self.get_text_origin_x()

        text_y = self.editor_rect.y + 15

        # Multi-line (triple-quoted) strings can open on a line far
        # above the ones currently on screen and still be "open" by
        # the time we reach the visible lines - so the state has to
        # be computed starting from line 0 of the whole buffer, not
        # just from the visible slice.
        line_states = compute_line_states(self.text_buffer.lines)

        for offset, line in enumerate(visible_lines):

            line_index = self.scroll_offset + offset

            segments, _ = highlight_line(
                line,
                line_states[line_index]
            )

            segment_x = text_x

            for segment_text, segment_color in segments:

                if not segment_text:
                    continue

                rendered = TEXT_FONT.render(
                    segment_text,
                    True,
                    segment_color
                )

                self.screen.blit(
                    rendered,
                    (segment_x, text_y)
                )

                segment_x += rendered.get_width()

            text_y += line_spacing

        # Empty code panes used to look inactive. This placeholder makes it
        # explicit that the center pane is where keyboard input belongs.
        if len(self.text_buffer.lines) == 1 and not self.text_buffer.lines[0]:
            placeholder = SMALL_FONT.render(
                "Start typing your Python code here...", True, SECONDARY_TEXT
            )
            self.screen.blit(placeholder, (text_x + 3, self.editor_rect.y + 42))

        # ----------------------------------
        # Draw Cursor
        # ----------------------------------

        current_line = self.text_buffer.lines[
            self.text_buffer.cursor_row
        ]

        text_before_cursor = current_line[
            :self.text_buffer.cursor_col
        ]

        cursor_x = (
            self.get_text_origin_x()
            + TEXT_FONT.size(text_before_cursor)[0]
        )

        # Convert actual cursor row into visible row
        visible_cursor_row = (
            self.text_buffer.cursor_row
            - self.scroll_offset
        )

        cursor_y = (
            self.editor_rect.y
            + 15
            + visible_cursor_row * line_spacing
        )

        # ----------------------------------
        # Blinking Cursor
        # ----------------------------------

        current_time = pygame.time.get_ticks()

        if current_time - self.last_input_time < 500:
            show_cursor = True
        else:
            show_cursor = (current_time // 500) % 2 == 0

        if (
            show_cursor
            and 0 <= visible_cursor_row < max_visible_lines
        ):
            pygame.draw.line(
                self.screen,
                TEXT_COLOR,
                (cursor_x, cursor_y),
                (cursor_x, cursor_y + 18),
                2
            )

        self.screen.set_clip(previous_clip)

        self.draw_scrollbar()

    def get_code_area_rect(self):
        """
        The part of the editor the code itself is drawn in:
        everything right of the line-number gutter, minus the strip
        the scrollbar lives in.

        That strip is reserved whether or not a scrollbar is
        currently showing, so code never appears to shift sideways
        the moment one appears.
        """

        reserved = SCROLLBAR_WIDTH + (SCROLLBAR_MARGIN * 2)

        return pygame.Rect(
            self.editor_rect.x + LINE_NUMBER_WIDTH + 2,
            self.editor_rect.y + 2,
            max(0, self.editor_rect.width - LINE_NUMBER_WIDTH - 2 - reserved),
            max(0, self.editor_rect.height - 4)
        )

    def get_text_origin_x(self):
        """
        Screen X where column 0 of a line of code is drawn.

        Everything that has to line up with the code - the text
        itself, the selection highlight, the blinking cursor and
        the click-to-position math - goes through here, so they can
        never disagree about where the horizontal scroll has put
        the text.
        """

        return (
            self.editor_rect.x
            + LINE_NUMBER_WIDTH
            + 15
            - self.h_scroll_offset
        )

    def get_max_horizontal_scroll(self):
        """
        How far sideways the code can scroll: enough to bring the
        end of the longest line into view, and no further.
        """

        if not self.text_buffer.lines:
            return 0

        widest_line = max(
            TEXT_FONT.size(line)[0]
            for line in self.text_buffer.lines
        )

        # A little breathing room past the last character.
        return max(
            0,
            widest_line - self.get_code_area_rect().width + 20
        )

    def clamp_horizontal_scroll(self):
        """Keep the horizontal scroll within the valid range."""

        self.h_scroll_offset = max(
            0,
            min(
                self.h_scroll_offset,
                self.get_max_horizontal_scroll()
            )
        )

    # ==========================================================
    # Selection Highlight
    # ==========================================================

    def draw_selection(self):
        """
        Draws a translucent highlight rectangle behind every
        selected character, one row at a time. Only draws over
        rows that are currently scrolled into view.
        """

        if not self.text_buffer.has_selection():
            return

        start_row, start_col, end_row, end_col = (
            self.text_buffer.get_selection_range()
        )

        line_spacing = LINE_SPACING
        max_visible_lines = self.get_max_visible_lines()

        text_x = self.get_text_origin_x()
        text_y = self.editor_rect.y + 15

        # Only rows within this range are actually drawn on screen.
        first_visible_row = self.scroll_offset
        last_visible_row = self.scroll_offset + max_visible_lines - 1

        # Walk through every line the selection touches.
        for row in range(start_row, end_row + 1):

            # Skip rows that are scrolled out of view -
            # no point highlighting something that isn't drawn.
            if row < first_visible_row or row > last_visible_row:
                continue

            line = self.text_buffer.lines[row]

            # The first and last selected lines are only
            # partially highlighted; lines in between are
            # highlighted in full.
            col_start = start_col if row == start_row else 0
            col_end = end_col if row == end_row else len(line)

            # Measure pixel positions using the font, so the
            # highlight lines up exactly with the rendered text.
            x_start = text_x + TEXT_FONT.size(line[:col_start])[0]
            x_end = text_x + TEXT_FONT.size(line[:col_end])[0]

            # Guarantee a minimum width so an empty selected
            # line (e.g. a fully selected blank line) still
            # shows a visible highlight sliver.
            width = max(4, x_end - x_start)

            row_in_view = row - self.scroll_offset

            highlight_rect = pygame.Rect(
                x_start,
                text_y + (row_in_view * line_spacing),
                width,
                18
            )

            # Use a separate surface with per-pixel alpha so the
            # highlight can be semi-transparent over the code.
            highlight_surface = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
            highlight_surface.fill((100, 150, 255, 90))

            self.screen.blit(highlight_surface, highlight_rect.topleft)

    def draw_output_panel(self):
        """Draw the output panel."""

        self.output_panel.draw(
            self.screen,
            self.output_rect
        )


    # ==========================================================
    # Scrolling Helpers
    # ==========================================================

    def get_max_visible_lines(self):
        """Calculate how many code lines can fit inside the editor."""

        return max(
            1,
            (self.editor_rect.height - 30) // LINE_SPACING
        )


    def get_max_scroll_offset(self):
        """Calculate the furthest position the editor can scroll down."""

        max_visible_lines = self.get_max_visible_lines()

        return max(
            0,
            len(self.text_buffer.lines) - max_visible_lines
        )


    def clamp_scroll_offset(self):
        """Keep the scroll position within the valid range."""

        self.scroll_offset = max(
            0,
            min(
                self.scroll_offset,
                self.get_max_scroll_offset()
            )
        )


    def ensure_cursor_visible(self):
        """
        Automatically scroll the editor when the cursor moves
        outside the visible area - vertically when it leaves the
        visible lines, horizontally when it runs off the side of
        the pane on a long line.
        """

        max_visible_lines = self.get_max_visible_lines()
        cursor_row = self.text_buffer.cursor_row

        # Cursor moved above the visible area.
        if cursor_row < self.scroll_offset:

            self.scroll_offset = cursor_row

        # Cursor moved below the visible area.
        elif cursor_row >= self.scroll_offset + max_visible_lines:

            self.scroll_offset = (
                cursor_row
                - max_visible_lines
                + 1
            )

        # Make sure the new scroll position is valid.
        self.clamp_scroll_offset()

        self.ensure_cursor_visible_horizontally()


    def ensure_cursor_visible_horizontally(self):
        """
        Slide the code sideways so the cursor stays inside the
        editor pane while typing a long line.
        """

        view_width = self.get_code_area_rect().width

        if view_width <= 0:
            return

        line = self.text_buffer.lines[self.text_buffer.cursor_row]

        # How far the cursor sits from the start of the line.
        cursor_pixels = TEXT_FONT.size(
            line[:self.text_buffer.cursor_col]
        )[0]

        # Kept between the cursor and the pane edge, so the cursor
        # never sits right up against the border.
        edge_margin = 30

        # Cursor ran off the left edge.
        if cursor_pixels < self.h_scroll_offset + edge_margin:

            self.h_scroll_offset = cursor_pixels - edge_margin

        # Cursor ran off the right edge.
        elif cursor_pixels > self.h_scroll_offset + view_width - edge_margin:

            self.h_scroll_offset = (
                cursor_pixels
                - view_width
                + edge_margin
            )

        self.clamp_horizontal_scroll()


    # ==========================================================
    # Mouse Cursor Position
    # ==========================================================

    def get_cursor_position_from_mouse(self, mouse_pos):
        """
        Convert a mouse click inside the editor
        into a text buffer row and column.
        """

        mouse_x, mouse_y = mouse_pos

        line_spacing = LINE_SPACING
        max_visible_lines = self.get_max_visible_lines()

        # Uses the same origin the code is drawn from, so a click
        # always lands on the character under the mouse even when
        # the code is scrolled sideways.
        text_x = self.get_text_origin_x()

        text_y = self.editor_rect.y + 15

        # ----------------------------------
        # Determine Which Line Was Clicked
        # ----------------------------------

        # Calculate the line position relative
        # to the visible editor area.
        row_in_view = (
            mouse_y - text_y
        ) // line_spacing

        row_in_view = max(
            0,
            min(
                row_in_view,
                max_visible_lines - 1
            )
        )

        # Convert the visible line position
        # into the actual line in the text buffer.
        row = self.scroll_offset + row_in_view

        row = max(
            0,
            min(
                row,
                len(self.text_buffer.lines) - 1
            )
        )

        line = self.text_buffer.lines[row]

        # ----------------------------------
        # Determine Which Column Was Clicked
        # ----------------------------------

        relative_x = mouse_x - text_x

        # Default to the end of the line.
        col = len(line)

        # Compare the mouse position with the
        # width of each section of the text.
        for i in range(len(line) + 1):

            width = TEXT_FONT.size(line[:i])[0]

            if width > relative_x:

                col = i - 1
                break

        # Keep the column within the valid range.
        col = max(
            0,
            min(col, len(line))
        )

        return row, col


    # ==========================================================
    # Scrollbar
    # ==========================================================

    @property
    def scrollbar_track_rect(self):
        """Editor scrollbar track (None when everything fits)."""

        return self.editor_scrollbar.track_rect


    @property
    def scrollbar_thumb_rect(self):
        """Editor scrollbar thumb (None when everything fits)."""

        return self.editor_scrollbar.thumb_rect


    def set_scroll_from_mouse_y(self, mouse_y):
        """Set the scroll position based on the mouse Y position."""

        # No scrollbar means there is nothing to scroll.
        if not self.editor_scrollbar.track_rect:
            return

        self.scroll_offset = self.editor_scrollbar.offset_from_mouse_y(
            mouse_y,
            self.get_max_scroll_offset()
        )

        self.clamp_scroll_offset()


    def draw_scrollbar(self):
        """Draw the editor scrollbar and draggable thumb."""

        self.editor_scrollbar.update(
            self.editor_rect,
            len(self.text_buffer.lines),
            self.get_max_visible_lines(),
            self.scroll_offset
        )

        self.editor_scrollbar.draw(self.screen)


    # ==========================================================
    # Button Panel
    # ==========================================================

    def draw_button_panel(self):
        """Draw the buttons at the bottom of the editor."""

        pygame.draw.rect(
            self.screen,
            PANEL_COLOR,
            self.button_rect,
            border_radius=PANEL_RADIUS
        )

        self.run_button.update()
        self.submit_button.update()

        self.run_button.draw(self.screen)
        self.submit_button.draw(self.screen)

        shortcut = SMALL_FONT.render(
            "F1 = Light   F2 = Dark   F10 = Mute", True, SECONDARY_TEXT
        )
        shortcut_rect = shortcut.get_rect(
            midleft=(self.button_rect.left + 14, self.button_rect.centery)
        )
        # RUN is the leftmost button in this row now that leaving moved
        # up to the title bar, so that is what the hint must clear.
        if shortcut_rect.right < self.run_button.rect.left - 10:
            self.screen.blit(shortcut, shortcut_rect)


    # ==========================================================
    # Component Getters
    # ==========================================================

    def get_output_panel(self):
        """Return the output panel."""

        return self.output_panel


    def get_problem_panel(self):
        """Return the objective panel."""

        return self.problem_panel


    def get_run_button(self):
        """Return the Run button."""

        return self.run_button


    def get_submit_button(self):
        """Return the Submit button."""

        return self.submit_button


    def get_exit_button(self):
        """Return the title-bar Exit button."""

        return self.exit_button
