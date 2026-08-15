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