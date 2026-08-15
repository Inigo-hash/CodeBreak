# "themes" lists the color themes offered by the COLOR THEME setting.
# The names must match the keys in src/ui/editor_theme.py's THEMES dict;
# picking one calls editor_theme.apply_theme() to restyle the coding
# environment. BLUE is index 0 so the editor still opens in CodeBreak's
# original palette.

settings_state = {
    "music_vol": 0.55,
    "sfx_vol": 0.45,
    "themes": ["BLUE", "DARK", "LIGHT"],
    "theme_index": 0,
    "dragging_music": False,
    "dragging_sfx": False,
}

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