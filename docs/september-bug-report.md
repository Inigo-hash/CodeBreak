# September PDF fixes

Reviewed all 11 pages of **bugs or smth.pdf**, supplied September 10, 2026. The PDF was used as the bug/design reference for the user's request to fix the game. Attributions to other people and suggestions inside it were not treated as separate instructions to contact anyone or use external services.

| PDF page | Reported issue | Resolution |
|---|---|---|
| 1 | Character extends over the shore | Anchor the visible feet to the collision body's bottom instead of centering the entire sprite on that body. Existing terrain and map-bound collision remains active. |
| 1 | Tikbalang gets trapped | Spawn placement now checks that an enemy-sized body has an escape route, rejecting isolated pockets instead of merely checking that the spawn rectangle is empty. |
| 1 | Objects cannot be interacted with | Existing action/type compatibility retained; existing sign tiles now expose reading interactions. All barrels/chests are linked to a lesson. |
| 2 | Settings explanations need what/how/effect | Rewrote all five help descriptions; both hover and click continue to show help. |
| 2–3 | Default text is too small | New/default settings start at 25. Existing saved font choices remain respected. |
| 3 | Next placement, redundant intro controls, unclear help location | Back and Next use opposite sides of a larger panel; tips wrap. Page 2 explains every main-menu action and the three Start Game choices. Page 3 identifies the top-right help/settings controls and explains the question marks. |
| 3 | Gear disappears after Start Game | Added an operable settings gear to the Start Game screen with modal input ownership. |
| 3 | First-time menu walkthrough and replay | Persist whether the opening walkthrough was seen. Show automatically once; HELP replays it. |
| 3 | Numbered editor buttons | Added `1. RUN` and `2. SUBMIT`; button widths account for the longer labels. Existing output guidance, editor line numbers, validation feedback, and separate title-bar Exit are retained. |
| 3 | Stationary fireflies and blue glow | Existing `AmbientParticles` already modulates painted specks and draws blue glow sprites. Existing particle regression tests pass; no replacement bitmap was needed. |
| 4 | Return to Main Menu text spills out | Existing label-aware menu sizing already fixes this. Layout tests now also allow width growth for larger fonts on taller monitor aspects. |
| 5 | Main-menu buttons hover beneath Settings | Suppressed background hover/focus, including Help and gear, while Settings owns the screen. |
| 6 | Black bands above/below game | Initial virtual canvas matches the monitor aspect, extending the view without cropping controls or stretching gameplay. Uniform mouse/presentation scaling is retained. |
| 6 | Sign popup | Hold E beside the existing starter-path signs to read directions; the HUD says Read Sign. |
| 7 | Corner designs persist outside boss battle | These were low-health warning marks. Their overlay now appears only while engaged in combat; the HP bar still shows health outside combat. |
| 7 | Boss cannot use parts of arena | Authored a larger boss movement rectangle covering the terrace, independent of its entrance label. Physical walls/trees remain solid. |
| 8 | Coding and combat need a connection | Existing guard-before-search and keys/lessons-before-boss rules retained. Previously unlinked barrels/chests introduce their nearest authored lesson; chest rewards require its challenge to be passed. |
| 8 | Loading tips should use mouse buttons anywhere | Already implemented: left mouse advances and right mouse goes back. Regression tests pass. Also corrected the stale loading tip from ten keys to nine. |
| 8 | Equip sword before attacking | New games put the starter sword in the bag. HUD/manual explain moving it to the hotbar and selecting it. The player's idle/walk pose visibly carries the selected sword using existing sword animation assets. Old saves retain their equipment choice. |
| 8 | Standing/floating on statue | Load solid object-layer collisions with Tiled's correct tile-object origin, and author solid bases for the pictured statue. |
| 9 | Two locked-gate buttons do the same thing | Already fixed: a locked gate has one centered Continue Exploring button. Regression test passes. |
| 10 | F3 boss popup appears only on leaving | Rearm the entrance latch when F3 changes access. Real game-loop checks for normal entry and F3 both produce intro on entry, then retreat on exit; retreat removes the boss. |
| 11 | Damage numbers | Successful sword hits in campaign and training display actual HP lost in floating, fading numbers, including boss damage. Effects expire automatically. |
| 11 | Change dodge and manuals | Q now dodges in campaign and tutorial. Updated controls, HUD, tutorial checklist/dialogue, boss instructions, and game-over advice. |

The reference to Vince's **“other recommendations”** does not specify what those recommendations were. The concrete numbered-button request was implemented; undisclosed changes were not invented.

Verification:

- Full isolated-process regression run: **189 tests passed**. Output: `.uv-cache/report-tests-final.txt`.
- Added nine behavioral regressions in `tests/test_september_report.py`.
- Strengthened lesson reachability to include object-layer solids; all nine required lessons remain reachable.
- Real-loop smoke: `tools/september_report_smoke.py`; both normal/F3 entry checks pass, with one intro followed by one retreat and no boss left behind. Uses temporary save storage.
- Visually inspected rendered larger-font intro, Settings, editor, and gameplay screens. Temporary captures are under `.uv-cache/`.
- Existing editor behavior tests verify Run versus Submit; loading, gate, equipment, combat, save, menu and tutorial tests also pass.

These checks are automated and headless, not a full player-driven campaign completion or physical-monitor/DPI playtest. Resizing a window to a different aspect after launch still uses aspect-preserving fit; the fullscreen monitor aspect is selected at launch. No player saves were used, and nothing was committed or pushed.

Reproduce in this workspace:

```powershell
$env:PYTHONPATH = '.uv-cache/game-tools'
$env:SDL_VIDEODRIVER = 'dummy'
$env:SDL_AUDIODRIVER = 'dummy'
Get-ChildItem tests/test_*.py | ForEach-Object {
    & ./.uv-python/cpython-3.13.12-windows-x86_64-none/python.exe -m unittest discover -s tests -p $_.Name
    if ($LASTEXITCODE -ne 0) { throw "Failed: $($_.Name)" }
}
& ./.uv-python/cpython-3.13.12-windows-x86_64-none/python.exe tools/september_report_smoke.py
```
