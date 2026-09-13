# PR5 / PR6 current repository audit

Reviewed 2026-09-11 at HEAD `f7742e8`. The working tree was clean before this work. No commits, player-save edits, or content redesigns were made.

The pre-edit audit was presented in the conversation before edits. This file records that assessment and subsequent results. DONE denotes implemented behavior supported by code inspection and relevant automated tests, not full hands-on acceptance.

| Task | Pre-edit status | Evidence / files involved | Action and result |
|---|---|---|---|
| 1. Editor and gameplay UI | DONE | `src/ui/code_editor.py`, `editor_renderer.py`, `problem_panel.py`; editor feedback and Tagama tests | Retained numbered Run/Submit, hints, output/error feedback and settings. |
| 2. Tutorial loading | DONE | `src/screens/loading.py`, `tutorial.py`; `test_loading_screen.py` | Retained shared presenter, tutorial tips, wraparound note navigation and SPACE completion. |
| 3. Loading and night lighting | DONE | `loading.py`, `src/ui/night_lighting.py`, `fog.py`; loading/night tests | Retained responsive layout, fog, torches and delayed healing. Castle correctly disables island night lighting. |
| 4. Practice Mode | DONE | `tutorial.py` practice-only waves and oval bounds; `src/learning/practice_manager.py`, `src/data/practice_templates.py`, `game.py`; practice/tutorial tests | Retained three combat trials and independent code practice. Code practice does not invoke campaign completion; combat practice uses local state. |
| 5. Fresh Stage 1 gameplay review | PARTIALLY DONE | Tutorial, gate reachability, combat and progression tests; `tools/tagama_smoke.py` | Fresh idle campaign and reload exercised. Full tutorial-to-victory traversal remains unverified. |
| 6. Combat balance | DONE | `src/systems/combat.py`, `src/entities/enemy.py`; boss, night and Tagama tests | Preserved damage, cooldowns, dodge immunity, damage grace, healing and boss phases. |
| 7. Challenge validation | DONE | `src/learning/challenge_manager.py`, `sandbox.py`, validators, `code_editor.py`; learning/Tagama tests | Retained AST objectives plus actual final values/output and hidden input checks for shipped content. |
| 8. Progression | PARTIALLY DONE | `game.py`, `stage_gate.py`, `stage_progress.py`, `save_manager.py`, `src/entities/chest.py` | Fixed ordinary-death checkpoint. Bonus time is awarded, trapped, displayed and saved but has no gameplay spending/countdown rule; left that design gap explicit. |
| 9. Beginner-to-Intermediate transition | DONE | `src/systems/stage_handoff.py`, `start_game_menu.py`; 23 handoff tests | Preserved destination checks, stage-local resets, learning/inventory/security carry-over and transition saves. |
| 10. Stage 2 preparation | PARTIALLY DONE | `src/data/stages.py`, `zones.py`, `assets/map/tmx/map2_castle_lobby.tmx`; handoff/map tests | Real Castle loop loads and renders. Foundation exists; map art remains unfinished and encounters, boss and exit are explicitly unauthored. |
| 11. Intermediate content | PARTIALLY DONE | Castle manual has empty topics; shared challenge routing, sandbox and stage contract exist | No finalized lesson specifications found. Loading tips preview concepts but are not lesson definitions. Did not invent content or validators. |
| 12. Regression testing | PARTIALLY DONE | Existing 21 test modules | Ran all 189 existing tests; added one real-loop death checkpoint regression with two heart-count cases. |
| 13. Coding pipeline | DONE | Actual editor Run/Submit tests, map reachability, `game.py` successful-lesson save | Preserved existing routing, prerequisite/topic state and immediate completion persistence. |
| 14. Enemy behavior | DONE | `enemy.py`, `src/systems/enemy_spawns.py`, `combat.py`; Tagama/September tests | Retained line of sight, alert/chase/return leash, body blockers, swept movement and spawn escape checks. Flying behavior remains species-specific. |
| 15. Combat polish | DONE | Manananggal, Tikbalang, Tiyanak tests; `src/ui/damage_numbers.py` | Retained single hit registration, damage, cooldowns and animations. |
| 16. Interactable collision | DONE | `game.py`, map and tileset solids; guarded-prop, stage gate and chest tests | Existing wall-aware interaction, solid artwork and one-shot chest behavior retained. Tests cover required lesson reachability, not every possible traversal. |
| 17. UI scaling | PARTIALLY DONE | `src/display.py`, HUD/editor/menu/manual tests and six-size previews | Found and fixed Castle title overflowing HUD card. Preserved aspect scaling; physical-monitor/DPI acceptance remains outstanding. |
| 18. Full save/game flow | PARTIALLY DONE | Atomic save tests, progression round trips, fresh autosave smoke | Fixed death penalty/respawn persistence; fresh autosave reload passed. Full campaign traversal with reloads at all requested points remains outstanding. |
| 19. Final Stage 1 playtest | NOT DONE | Previous reports explicitly deferred hands-on completion | Automated checks below do not constitute a player-driven end-to-end playtest. |

## History and intentional preservation

- `fc09bb9` explicitly reverted onboarding redesign `558806b`: REVERTED / NO LONGER APPLICABLE. No reason beyond the explicit revert is documented in its message. The current tutorial and subsequent improvements were preserved.
- `fc0a77f` introduced validation/topic-state improvements; `c6c162a` added Code Practice; `1916d08` improved attack connection checks.
- `872d9cc` connected the stages; `642a457` added behavioral coverage and fixes; `a081969` added the latest UI/combat/map improvements. `cdf803d` and `e6c3594` changed Castle map content. These implementations were inspected rather than recreated.
- Historical `CLAUDE.md` claims about AST-only validation, ten required topics, and eight failing tests are stale. Current code has runtime validation, nine required campaign topics and a passing baseline.
- Kept the existing five-heart reset at zero, combat tuning, controls (Q dodge), save schema and security, two practice modes, shared loading presenter, progression and transition architecture.

## Changes and bug register

| Severity | Finding | Resolution |
|---|---|---|
| Major | Ordinary death deducted a heart only in memory; Main Menu returned before saving, and retry waited for later autosave. Reload could discard the penalty and checkpoint. | `src/screens/game.py` now performs existing recovery and saves the safe respawn and heart count before opening Game Over. The modal still shows the previously rendered defeat frame. Boss recovery is unchanged. |
| Minor | `CASTLE Stage 2 - Intermediate` drew beyond the fixed-width progress card. | `src/ui/gameplay_hud.py` sizes the card from its title with screen-width bounds and an ellipsis fallback for unusually long titles. No stage-specific layout branch. |
| Polish | Previous documentation reports clipboard deprecation; no functional editor failure reproduced. | Left unchanged. |

No Critical failure was reproduced. The Major issue above is fixed; this does not establish that untested campaign paths contain no Major bugs. Unauthored Castle gameplay and unspecified bonus-time consumption remain design/content gaps, not invented implementations.

## Verification and limits

- Baseline: **189 tests passed**, all existing modules run in separate processes using the installed Python 3.13.12 and `.uv-cache/game-tools` dependencies.
- New `tests/test_death_checkpoint.py`: failed before the fix in both subcases (five hearts and last heart), passed afterward. Exercises the actual game loop, forces defeat after a rendered frame, opens the Game Over callback and reads the temporary save before returning to Main Menu. Confirms heart count, safe position and retained bonus/challenge state. It is an injected death scenario, not a combat playthrough.
- After the gameplay fix: **69 existing affected tests passed** across boss, guarded props, Stage 1 systems, handoff, Tagama and tutorial modules. After the HUD fix: **9 September regression tests passed**. Together with the new test, the repository now contains 190 tests; the whole suite was not rerun after the edits.
- `tools/september_report_smoke.py`: both normal and F3 entry produced one boss intro followed by retreat and removed the boss. This uses prepared gate progress and does not claim earned campaign victory.
- Existing `tools/tagama_smoke.py`, with output redirected to `.uv-cache/current-audit-previews`: fresh game ran 32 seconds, created an autosave and reloaded for two seconds with matching position, keys and challenges. All saves were temporary. Headless timing is not a representative performance benchmark.
- Castle ran through the real loading and gameplay loop for two seconds from a stage-handoff state, without marking the Island complete. It rendered its spawn/HUD successfully.
- Generated gameplay, editor, manual and Castle previews at 1280x720, 1366x768, 1920x1080, 2560x1440, 1280x1024 and 2560x1080. Inspected laptop gameplay/editor/Castle and 5:4 manual images; then rendered and inspected the corrected Castle HUD. These are scaled offscreen previews, not physical display tests.
- Full fresh-save tutorial, all nine lessons and encounters, normal boss victory, earned Castle transition and repeated reloads along that route were **not completed**. Combat feel, audio and Windows 125%/150% DPI require hands-on acceptance. Task 19 remains NOT DONE; tasks 5 and 18 remain PARTIALLY DONE.

Reproduce the new regression in this workspace:

```powershell
$env:PYTHONPATH = '.uv-cache/game-tools'
$env:SDL_VIDEODRIVER = 'dummy'
$env:SDL_AUDIODRIVER = 'dummy'
& ./.uv-python/cpython-3.13.12-windows-x86_64-none/python.exe -m unittest discover -s tests -p test_death_checkpoint.py
```
