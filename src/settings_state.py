# "themes" lists the color themes offered by the COLOR THEME setting.
# The names must match the keys in src/ui/editor_theme.py's THEMES dict;
# picking one calls editor_theme.apply_theme() to restyle the coding
# environment. BLUE is index 0 so the editor still opens in CodeBreak's
# original palette.

settings_state = {
    "music_vol": 0.55,
    "sfx_vol": 0.45,
    "music_muted": False,
    "themes": ["BLUE", "DARK", "LIGHT"],
    "theme_index": 0,
    "dragging_music": False,
    "dragging_sfx": False,
    # How fast dialogue types itself out. Was a decorative row in the
    # settings panel for a long time - the label was drawn but nothing
    # read it, and nothing in the game revealed text a character at a
    # time for it to control either.
    "text_speed": "NORMAL",
    # PC games should launch with text that is at least 18 physical pixels
    # high at 1080p and let the player enlarge it.  The shared font loaders
    # read this multiplier, so the choice reaches menus, dialogue and HUDs.
    "font_size": "RECOMMENDED",
}


# Milliseconds between letters. INSTANT is 0, which every caller has to
# read as "no animation at all" rather than dividing by it.
TEXT_SPEEDS = ("SLOW", "NORMAL", "INSTANT")

TEXT_SPEED_MS = {
    "SLOW": 55,
    "NORMAL": 28,
    "INSTANT": 0,
}


# The settings a player can change, top to bottom, and how far one
# keyboard nudge moves a volume. Both panels - the menu/pause one in
# src/screens/settings.py and the one inside the code editor - build
# their rows from this, so neither can end up offering a setting the
# other does not.
FONT_SIZES = ("RECOMMENDED", "LARGE", "EXTRA LARGE")

FONT_SCALE = {
    "RECOMMENDED": 1.0,
    "LARGE": 1.35,
    "EXTRA LARGE": 2.0,
}

ROWS = ("font_size", "text_speed", "music", "sfx", "theme")

VOLUME_STEP = 0.05

# Color used to draw each theme's NAME in a settings panel, so the label
# hints at the theme it selects. Both settings panels sit on a dark
# background, so LIGHT is shown as a warm near-white rather than the
# actual white it produces inside the editor.
THEME_SWATCH_COLORS = {
    "BLUE": (80, 180, 255),
    "DARK": (150, 160, 180),
    "LIGHT": (255, 248, 230),
}


def current_theme_name():
    """Name of the color theme currently selected in the settings."""

    return settings_state["themes"][settings_state["theme_index"]]


def cycle_theme(step):
    """
    Moves the COLOR THEME setting `step` places (-1 for the left arrow,
    +1 for the right) and restyles the coding environment to match.

    Both the main menu and the in-game pause menu call this, so the two
    panels can never disagree about which theme is selected - keeping
    the index and the applied palette in one place is what stops the
    picker from silently becoming decorative again.

    Returns the name of the theme now in effect.
    """

    settings_state["theme_index"] = (
        (settings_state["theme_index"] + step) % len(settings_state["themes"])
    )

    name = current_theme_name()

    # Imported here, not at module scope: this module is pulled in very
    # early by the menus, while editor_theme builds pygame fonts as soon
    # as it loads.
    from src.ui.editor_theme import apply_theme
    apply_theme(name)

    return name


def swatch_color(name):
    """Label color for a theme name, with a safe fallback."""

    return THEME_SWATCH_COLORS.get(name, (200, 200, 210))


# ---------------------------------------------------------------------
# Text speed
# ---------------------------------------------------------------------

def current_text_speed():
    """Name of the text speed currently selected."""

    return settings_state.get("text_speed", "NORMAL")


def set_text_speed(name):
    """Select a text speed by name, ignoring anything unrecognised."""

    if name in TEXT_SPEEDS:
        settings_state["text_speed"] = name

    return current_text_speed()


def cycle_text_speed(step):
    """Move the setting `step` places, the way cycle_theme does."""

    index = TEXT_SPEEDS.index(current_text_speed())
    settings_state["text_speed"] = TEXT_SPEEDS[(index + step) % len(TEXT_SPEEDS)]

    return current_text_speed()


def letter_delay_ms():
    """Milliseconds per revealed character. 0 means show it all at once."""

    return TEXT_SPEED_MS.get(current_text_speed(), TEXT_SPEED_MS["NORMAL"])


def revealed_characters(total, elapsed_ms):
    """
    How many of `total` characters should be on screen after
    `elapsed_ms` of typing.

    Every typewriter in the game goes through here rather than keeping
    its own timing constant, so the setting reaches all of them and
    INSTANT never has to be special-cased at the call site.
    """

    delay = letter_delay_ms()

    if delay <= 0:
        return total

    return min(total, int(max(0, elapsed_ms) // delay) + 1)


def current_font_size():
    return settings_state.get("font_size", "RECOMMENDED")


def font_scale():
    return FONT_SCALE.get(current_font_size(), 1.0)


def cycle_font_size(step):
    index = FONT_SIZES.index(current_font_size())
    settings_state["font_size"] = FONT_SIZES[(index + step) % len(FONT_SIZES)]

    # Existing cached faces must be discarded before a screen rebuilds its
    # local fonts.  Imported lazily to keep settings_state dependency-light.
    from src.ui.theme import clear_font_cache
    clear_font_cache()
    return current_font_size()
