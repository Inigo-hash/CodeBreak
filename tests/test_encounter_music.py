import unittest
from unittest.mock import patch

from src.systems.audio import EncounterMusic


class EncounterMusicTests(unittest.TestCase):
    @patch('src.systems.audio.pygame.mixer')
    def test_threat_switches_once_and_calm_returns_after_delay(self, mixer):
        music = EncounterMusic('explore', 'combat', 'boss')
        music.update(.1)
        music.update(.1, threatened=True)
        music.update(.1, threatened=True)
        self.assertEqual([call.args[0] for call in mixer.music.load.call_args_list],
                         ['explore', 'combat'])
        music.update(2)
        self.assertEqual(music.current, 'combat')
        music.update(.6)
        self.assertEqual(music.current, 'explore')

    @patch('src.systems.audio.pygame.mixer')
    def test_boss_takes_priority_and_falls_back_to_combat(self, mixer):
        music = EncounterMusic('explore', 'combat', 'boss')
        music.update(.1, threatened=True, boss_active=True)
        self.assertEqual(music.current, 'boss')
        music.update(.1, threatened=True)
        self.assertEqual(music.current, 'combat')
        fallback = EncounterMusic('explore', 'combat')
        fallback.update(.1, boss_active=True)
        self.assertEqual(fallback.current, 'combat')

    @patch('src.systems.audio.settings_state', {'music_muted': True, 'music_vol': .8})
    @patch('src.systems.audio.pygame.mixer')
    def test_transitions_keep_music_muted(self, mixer):
        music = EncounterMusic('explore', 'combat')
        music.update(.1, threatened=True)
        mixer.music.set_volume.assert_called_with(0.0)

    @patch('src.systems.audio.pygame.mixer')
    def test_missing_audio_device_is_safe(self, mixer):
        mixer.get_init.return_value = None
        EncounterMusic('explore', 'combat').update(.1, threatened=True)
        mixer.music.load.assert_not_called()

    @patch('src.systems.audio.settings_state', {'music_muted': False, 'music_vol': .8})
    @patch('src.systems.audio.pygame.mixer')
    def test_escape_gradually_fades_battle_then_fades_in_exploration(self, mixer):
        music = EncounterMusic('explore', 'combat')
        music.update(.1, threatened=True)
        levels = []
        for _ in range(4):
            music.update(.5)
            levels.append(mixer.music.set_volume.call_args.args[0])
        self.assertTrue(all(a > b for a, b in zip([.8] + levels, levels)))
        self.assertEqual(music.current, 'combat')
        music.update(.5)
        self.assertEqual(music.current, 'explore')
        mixer.music.play.assert_called_with(-1, fade_ms=1200)

    @patch('src.systems.audio.pygame.mixer')
    def test_new_threat_restores_fading_battle_without_restarting(self, mixer):
        music = EncounterMusic('explore', 'combat')
        music.update(.1, threatened=True)
        music.update(2)
        faded = music.gain
        music.update(.1, threatened=True)
        self.assertGreater(music.gain, faded)
        self.assertLess(music.gain, 1)
        music.update(.6, threatened=True)
        self.assertEqual(music.gain, 1)
        mixer.music.load.assert_called_once_with('combat')
