# Stage Selection World Map

Implemented 2026-09-19 using the supplied **ChatGPT Image Sep 19, 2026, 09_57_47 AM.png**. The earlier two-card concept has been replaced by one continuous illustrated world. No playable map was replaced or removed.

## How to open it

- **Start New Game:** select/authenticate a save slot, finish the tutorial, then choose a stage.
- **Continue Game:** select/authenticate your save slot, then choose a stage.
- **During gameplay or from the pause menu:** press **G** to open the World Atlas. Press G again or Escape to close it. Selecting the current stage resumes the same live encounter; selecting another unlocked stage saves the map checkpoint and travels through the existing stage chain.
- Hover or click the village, temple, citadel, their plaques, or their markers to inspect that stage. Click **ENTER STAGE** to travel.
- Up/right/Tab select the next stage; down/left select the previous stage; Enter travels; Escape or Back cancels.

Selection does not write to disk until an available destination is entered. In gameplay, cancelling or selecting the current stage does not reload or reset it. Password protection remains before loading a slot from the menu. The G shortcut is listed in the gameplay HUD, How To Play and Stage Manual.

## Stage behavior

| Atlas location | Gameplay destination | Unlock rule |
|---|---|---|
| Stage 1 — The Forgotten Village | Existing Island map | Initially available; completed stages remain selectable |
| Stage 2 — The Ancient Depths | Existing Castle lobby preview, explicitly labelled in the panel | Complete Stage 1; existing saves already in Castle remain accessible |
| Stage 3 — The Corrupted Citadel | Future map hook; no playable map is currently connected | Stage 2 completion unlocks the landmark, but entry additionally requires an authored map |

Developer Mode can bypass campaign locks for existing maps. It does not mark stages complete or permit entry into the missing Citadel map. Completion comes from the existing `completed_stages` save field; there is no new completion/unlock database.

Map position, keys and stage-scoped progress use the checkpoint mechanism already in this checkout. Switching maps preserves those checkpoints along with shared lessons, inventory, equipped state and password data. The original save object is not mutated during selection. Older saves without checkpoint data can still open their current map; previously visited maps without a recorded checkpoint begin at their normal spawn.

## Presentation

The supplied image is copied intact into the repository. The full image is fitted without stretching or cropping. The surrounding viewport uses a softened forest-and-sea backdrop derived at render time from the artwork, a feathered map edge, drifting golden dust and an antique border. The original image is unchanged. Native plaques replace its baked stage labels; status seals replace its baked locks/waypoint. Current-stage glow, completed checks, locked markers, subtle selection pulses and softly highlighted/dimmed regions are rendered by Pygame.

Landmarks and region polygons are normalized to the map image. Hit testing converts canvas coordinates into the map's coordinates after the existing display layer converts physical mouse positions to canvas positions. The parchment information panel owns its own input area; hidden map regions cannot intercept its buttons.

## Files changed

- `src/screens/stage_select.py`: continuous map rendering, hotspots, markers, panel, keyboard/mouse interactions and responsive geometry.
- `src/screens/start_game_menu.py`: connect selection to new/continued games after authentication; save the chosen checkpoint before entering the existing stage chain.
- `src/screens/game.py`: G shortcut, modal pause/resume, saved travel and visible shortcut hint.
- `src/data/controls.py`: document the World Atlas shortcut in the shared controls.
- `src/systems/stage_selection.py`: shared unlock/status rules, future map availability and checkpoint defaults for older saves.
- `src/data/stage_map.py`: three named landmarks, normalized hit regions and gameplay destination hooks.
- `assets/images/backgrounds/stage_select_world_reference.png`: unchanged copy of the supplied artwork. The earlier generated `stage_select_world.png` is retained but no longer used by this screen.
- `tests/test_stage_selection.py`: 16 behavioral tests, including live gameplay travel and pause/current-stage behavior.
- `tools/stage_select_smoke.py`: reproducible headless previews through the actual presentation transform; no save writes.
- This report, the two test logs and nine previews in `docs/stage-selection-verification/`.

## Verification

- **Broader suite: 217 tests passed across 25 modules**, each in its own process for SDL isolation. [Full log](stage-selection-test-results.txt).
- **Final stage-selection suite: 16 tests passed**, including real gameplay boot/checkpoint retention, G travel, opening from pause and retaining the current boss instance. [Targeted log](stage-selection-targeted-results.txt).
- Tests cover initial availability, locked Stage 2/3 rejection, completed-stage selection, future Citadel map hookup, developer access, legacy saves, checkpoint save/load round trips, cancellation without writes, existing Island gameplay entry, and retention of Castle progress after an Island gameplay save.
- Hotspot and mouse-transform assertions passed at **1280×720, 1366×768, 1920×1080, 2560×1440, 1280×1024 and 2560×1080**.
- Smoke generated six resolution previews plus locked Citadel, completed Village and available Depths states. Inspected the laptop and 5:4 layouts and the locked/available panels; corrected marker/text overlap and paragraph sizing.
- `git diff --check` passed. All save tests used temporary slots. No player save was modified; nothing was committed or pushed.

Example: [1366×768 world map](stage-selection-verification/world-map-1366x768.png).

Reproduce:

```powershell
D:/VScode/.venv/Scripts/python.exe -m unittest discover -s tests -p test_stage_selection.py
D:/VScode/.venv/Scripts/python.exe tools/stage_select_smoke.py
```

## Remaining content and manual checks

No additional selection-screen artwork is needed. The **Ancient Depths playable map/lesson content** and **Corrupted Citadel playable map/content** remain future work. To connect the latter, add a `citadel` stage record with its `world.map` and normal stage data; selection already checks its prerequisite and map availability. Existing Castle campaign behavior is unchanged.

Physical monitor readability, Windows DPI, fullscreen/windowed interaction and a complete human-controlled campaign remain **MANUAL VERIFICATION REQUIRED**. The supplied illustration has a taller aspect ratio than most monitors; side space intentionally preserves the complete northern and southern landmarks.
