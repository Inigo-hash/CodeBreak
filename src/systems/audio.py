"""Music controls and event-based SFX shared by every screen."""

from array import array
import math
from pathlib import Path
import random
import pygame
import numpy as np

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

MUSIC_SHORTCUT = pygame.K_F10
_crumble_sounds = {}


def effective_music_volume():
    return 0.0 if settings_state.get("music_muted", False) else settings_state["music_vol"]


def apply_music_volume():
    """Apply both the slider and mute state to pygame's music channel."""

    if pygame.mixer.get_init():
        pygame.mixer.music.set_volume(effective_music_volume())


def toggle_music_mute():
    settings_state["music_muted"] = not settings_state.get("music_muted", False)
    apply_music_volume()
    return settings_state["music_muted"]


def handle_music_shortcut(event):
    """F10 works everywhere without colliding with M, the map key."""

    if event.type == pygame.KEYDOWN and event.key == MUSIC_SHORTCUT:
        toggle_music_mute()
        return True
    return False


def music_shortcut_label():
    state = "Unmute" if settings_state.get("music_muted", False) else "Mute"
    return f"F10 = {state} music"


def _build_crumble_sound(phase="break"):
    """Synthesize layered masonry instead of a single electronic noise.

    A convincing brick break needs separate events: the initial low impact,
    sharp brittle fractures, tumbling chunks, and a noisy debris tail.  The
    old sound mixed one sine wave with white noise, which read as a zap/hiss.
    """

    mixer = pygame.mixer.get_init()
    if not mixer:
        return None
    sample_rate, _format, channels = mixer
    rng = random.Random(9917 if phase == "break" else 2718)
    duration = 0.72 if phase == "break" else 0.46
    if phase == "break":
        cracks = [
            (0.018, 1180, 62, 0.48), (0.052, 840, 48, 0.55),
            (0.096, 1360, 72, 0.34), (0.145, 620, 40, 0.48),
            (0.218, 980, 55, 0.30), (0.310, 710, 44, 0.24),
        ]
        thuds = [(0.0, 92, 16, 0.75), (0.19, 76, 22, 0.52),
                 (0.34, 108, 27, 0.38), (0.51, 68, 25, 0.28)]
    else:
        cracks = [(0.055, 560, 46, 0.22), (0.165, 760, 58, 0.16)]
        thuds = [(0.0, 74, 20, 0.48), (0.105, 102, 25, 0.38),
                 (0.235, 64, 24, 0.32), (0.355, 88, 28, 0.20)]

    samples = array("h")
    low_noise = 0.0
    mid_noise = 0.0
    for index in range(int(sample_rate * duration)):
        t = index / sample_rate
        white = rng.uniform(-1.0, 1.0)
        low_noise += 0.035 * (white - low_noise)
        mid_noise += 0.24 * (white - mid_noise)

        # Grit is filtered noise, like many small fragments scraping and
        # bouncing, with a slower tail than the first impact.
        tail = max(0.0, 1.0 - t / duration)
        grit = (mid_noise - low_noise) * (tail ** 1.7) * (
            0.58 if phase == "break" else 0.38
        )

        fracture = 0.0
        for start, frequency, damping, strength in cracks:
            age = t - start
            if age >= 0:
                # Two close resonances make each crack irregular rather than
                # a clean musical ping.
                fracture += strength * math.exp(-age * damping) * (
                    math.sin(math.tau * frequency * age)
                    + 0.42 * math.sin(math.tau * frequency * 1.47 * age)
                )

        chunks = 0.0
        for start, frequency, damping, strength in thuds:
            age = t - start
            if age >= 0:
                chunks += strength * math.exp(-age * damping) * (
                    math.sin(math.tau * frequency * age)
                    + low_noise * 1.8
                )

        # Brief broadband snap at the first collision, followed by a low
        # non-tonal rumble. tanh gives the impact weight without clipping.
        snap = white * math.exp(-t * 95) * (0.85 if phase == "break" else 0.35)
        rumble = low_noise * math.exp(-t * 5.2) * (1.15 if phase == "break" else 0.75)
        mixed = snap + fracture + chunks + grit + rumble
        value = int(math.tanh(mixed * 1.35) * 21000)
        for _ in range(max(1, channels)):
            samples.append(value)
    try:
        return pygame.mixer.Sound(buffer=samples.tobytes())
    except pygame.error:
        return None

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


CUSTOM_BREAK_SFX_PATH = "assets/audios/sfx/crumble.mp3"
 

BREAK_TARGET_SECONDS = 0.52
SETTLE_TARGET_SECONDS = 0.56
_custom_crumble_sounds = {}

def _resample_to_duration(samples, target_seconds, sample_rate):
    """
    Return a NEW sample array that plays back in `target_seconds` at the
    ORIGINAL sample rate.
 
    This is naive resampling ("play it faster"), not true time-stretch:
    it picks evenly spaced samples out of the original array rather than
    reconstructing the waveform, so shortening the clip also raises its
    pitch slightly - the same effect as speeding up a tape or record.
 
    `samples` may be mono (1-D) or stereo (2-D: frames x channels);
    indexing along axis 0 works for both.
    """
 
    original_frames = samples.shape[0]
    target_frames = max(1, int(round(target_seconds * sample_rate)))
 
    # Evenly spaced positions across the original clip, rounded to the
    # nearest real sample index.
    positions = np.linspace(0, original_frames - 1, target_frames)
    indices = np.round(positions).astype(np.int64)
 
    return samples[indices]
 
 
 
def _load_and_process_custom_crumble_sound(phase):
    """
    Load CUSTOM_BREAK_SFX_PATH once, derive both "break" and "settle"
    from it, cache both, and return whichever `phase` was asked for.
 
    Returns None (for both phases) if the file is missing or this
    environment can't do sample-array manipulation - callers are
    expected to fall back to another sound source in that case.
    """
 
    if phase in _custom_crumble_sounds:
        return _custom_crumble_sounds[phase]
 
    mixer = pygame.mixer.get_init()
    if not mixer:
        return None
 
    sample_rate, _format, _channels = mixer
 
    try:
        source = pygame.mixer.Sound(CUSTOM_BREAK_SFX_PATH)
    except (pygame.error, FileNotFoundError):
        # No custom file present - leave the cache empty so every future
        # call keeps returning None cheaply instead of retrying the load.
        _custom_crumble_sounds["break"] = None
        _custom_crumble_sounds["settle"] = None
        return None
 
    try:
        samples = pygame.sndarray.array(source)
    except NotImplementedError:
        # This pygame build has no numpy/sndarray support.
        _custom_crumble_sounds["break"] = None
        _custom_crumble_sounds["settle"] = None
        return None
 
    break_samples = _resample_to_duration(
        samples, BREAK_TARGET_SECONDS, sample_rate
    )
    # Reversed independently from "break" - it has its own target
    # duration, so this is not just break_samples flipped.
    settle_samples = _resample_to_duration(
        samples, SETTLE_TARGET_SECONDS, sample_rate
    )[::-1]
 
    # np.ascontiguousarray is needed because slicing with [::-1] produces
    # a reversed VIEW with negative strides, which pygame.sndarray cannot
    # read directly - this copies it into normal, forward-laid-out memory.
    _custom_crumble_sounds["break"] = pygame.sndarray.make_sound(
        np.ascontiguousarray(break_samples)
    )
    _custom_crumble_sounds["settle"] = pygame.sndarray.make_sound(
        np.ascontiguousarray(settle_samples)
    )
 
    return _custom_crumble_sounds[phase]
 
 
# ----------------------------------------------------------------------
# Integration: replace play_crumble_sfx() in audio.py with this version
# ----------------------------------------------------------------------
 

def play_crumble_sfx(phase="break"):
    """
    Play the "break" or "settle" crumble sfx.
 
    Tries the custom, resampled/reversed clip first; falls back to the
    original synthesized sound (_build_crumble_sound, already defined
    in audio.py) if no custom file is available.
    """
 
    sound = _load_and_process_custom_crumble_sound(phase)
 
    if sound is None:
        # Falls back to the existing synthesis + cache already defined
        # in audio.py (_crumble_sounds / _build_crumble_sound).
        sound = _crumble_sounds.get(phase)
        if sound is None:
            sound = _build_crumble_sound(phase)
            _crumble_sounds[phase] = sound
 
    if sound is None:
        return False
 
    sound.set_volume(min(1.0, settings_state["sfx_vol"] * 1.1))
    sound.play()
    return True
