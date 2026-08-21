"""Event-based combat SFX that coexist with pygame's music channel."""

from pathlib import Path
import pygame

from src.settings_state import settings_state


COMBAT_SFX_PATHS = {
    "sword_swing": "assets/audios/sfx/sword_swing.wav",
    "sword_hit": "assets/audios/sfx/sword_hit.wav",
    "player_hurt": "assets/audios/sfx/player_hurt.wav",
    "enemy_hurt": "assets/audios/sfx/enemy_hurt.wav",
    "dodge": "assets/audios/sfx/dodge.wav",
    "enemy_attack": "assets/audios/sfx/enemy_attack.wav",
    "enemy_death": "assets/audios/sfx/enemy_death.wav",
    "player_death": "assets/audios/sfx/player_death.wav",
}


class CombatAudio:
    """Load available sounds once and play them once per requested event."""

    def __init__(self):
        self.sounds = {}
        self.missing_assets = []
        for event, path in COMBAT_SFX_PATHS.items():
            if not Path(path).is_file():
                self.missing_assets.append(path)
                continue
            try:
                self.sounds[event] = pygame.mixer.Sound(path)
            except pygame.error:
                self.missing_assets.append(path)

    def play(self, event):
        sound = self.sounds.get(event)
        if sound is None:
            return False
        sound.set_volume(settings_state["sfx_vol"])
        sound.play()
        return True
