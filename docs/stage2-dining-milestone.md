> Combat follow-up: regular Kapre art is now 180px tall (previously 108px), with unchanged movement body. Enemies can pursue beyond their home patrol label within bounded chase territory; close melee is not cancelled by the home leash, and returning enemies defend themselves in melee. Stage 2 melee reaches were increased. Walls still block attacks. Initial strict patrol-containment claims below are superseded by this pursuit behavior.

> Roster correction: Castle regular camps now mix **Mandurug Duwende, Kapre Usikan and White Lady**. **Zombie Aktan** is the configured final boss in the upper Throne arena, gated behind five keys. Kapre (including the Island boss variant) alternates normal/ultimate nine-frame attack sequences. White Lady currently reuses the first attack pose for locomotion/flinch because separate assets are absent. Unfinished Castle curriculum/completion remains unavailable.

> Subsequent combat expansion: all five Castle rooms now contain two persistent Duwende camps (four enemies per room, twenty total). Dining retains its original camp ID and adds a northern group. Door approaches and the Lists terminal remain outside patrol regions. Other rooms still have unfinished lessons. The original milestone test results below describe the initial delivery; see `tests/test_castle_room_enemies.py` for the added collision/reachability/patrol checks.

# Stage 2 Dining milestone delivery

Verified 2026-10-11. No commits or pushes were made.

## Delivered behavior

Dining contains the Lists lesson, two individually tracked function challenges, separate library-themed practice versions, a searchable table, a one-time +15-second crate, and a two-member Duwende Mandurug camp. The lesson teaches indexing, negative indexing, len(), append(), first-match remove(), and pop(), with a separate playlist worked example and four progressive hints per challenge. Function syntax is supplied scaffolding; full Functions mastery is future content.

`describe_items(items)` returns `(first, last, count)`, including `(None, None, 0)` for an empty list. `update_items(items, added, removed)` copies, appends, removes the first matching target if present, then pops if nonempty. A single-item pop returns that item even when the remaining list is empty. Both challenges leave the original input list unchanged.

The checker accepts alternative implementations and executes both submitted source and function calls inside the timed sandbox, with fresh globals and deep-copied inputs per case. Failures report input, actual return or exception, and expected return. Stage 1's existing validation path is retained.

Passing both required challenges creates one atomic save snapshot containing challenge passes, topic mastery, Key 1, and its claim marker. The existing temporary-file/fsync/replace slot writer commits the snapshot before the live game publishes the reward. Reconciliation is idempotent. Practice and repeated submissions grant no required completion or extra keys.

Castle is configured for five keys, with only the first Lists bundle implemented. Encounters grant zero Castle keys. Other rooms remain previews; Castle's unfinished exit, final assessment and next-stage handoff remain unavailable. Stage 1 retains nine keys and its encounter rewards.

## Foundation integration and local work

The two incoming commits through `a425030` were reconciled into the working tree using HEAD/base, incoming content, and local content. No reset, checkout overwrite, commit, index update, or push was used. The six foundation tests passed immediately after integration and again after implementation. HEAD intentionally remains at the prior commit; the foundation and milestone are uncommitted working-tree changes.

The original ten modified files were preserved: `src/entities/enemy.py`, `src/entities/player.py`, `src/screens/game.py`, `src/screens/main_menu.py`, `src/screens/mang_tahimik.py`, `src/screens/tutorial.py`, `src/ui/code_editor.py`, `tests/test_boss_encounter.py`, `tests/test_editor_feedback.py`, and `tests/test_mang_tahimik.py`. Original overlapping files are backed up outside the repository at `D:/VScode/.stage2-local-backup`.

## Changed files

New milestone files:

- `src/data/castle_lists.py`: lesson, challenges, cases, hints and practice variants.
- `src/screens/topic_challenges.py`: individual completion status and challenge selection.
- `src/systems/topic_mastery.py`: pure mastery/reward snapshot construction and reconciliation.
- `tests/test_stage2_dining.py`: sandbox, mastery, placement, persistence and real gameplay integration checks.
- `docs/stage2-dining-milestone.md`: this report.

Milestone modifications:

- `assets/map/tmx/map2_dining_area.tmx`: existing-asset art, lesson terminal, independent table/crate and persistent IDs.
- `src/data/challenges.py`, `src/data/topics.py`, `src/data/practice_templates.py`: authored content registration and optional multi-challenge topics.
- `src/learning/sandbox.py`, `src/learning/challenge_manager.py`: timed function cases and return feedback.
- `src/data/encounters.py`, `src/data/rooms.py`, `src/data/items.py`: room-specific camp, patrol bounds and searchable table action.
- `src/data/stages.py`, `src/data/stage_map.py`: five-key configuration, honest manual and preview status.
- `src/screens/game.py`: challenge flow, atomic mastery saves, explicit object IDs, independent searches, room encounter key configuration, indoor patrol support and autosaves.
- `src/systems/save_manager.py`, `src/systems/stage_handoff.py`, `src/systems/stage_selection.py`: reconciliation and stage-scoped claim persistence.
- `src/systems/rooms.py`, `src/systems/stage_progress.py`, `src/systems/learning_progress.py`: room aggregation, mastery objectives and individual challenge guidance.
- `src/systems/stage_gate.py`: keep unfinished Castle completion unavailable.
- `src/ui/code_editor.py`, `src/ui/gameplay_hud.py`: starters, function-case feedback space and Castle challenge counts.
- `server/tutor_prompt.py`: authored Dining facts without checker cases or complete solutions.
- `tests/test_learning_challenges.py`, `tests/test_stage1_systems.py`, `tests/test_tutor_server.py`: updated registry fixtures, Dining expectations and tutor grounding coverage.
- `docs/stage2-implementation-plan.md`: integrated plan and updated milestone status.

Additional foundation files brought in unchanged from the incoming work: `src/data/final_assessments.py`, `src/screens/final_assessment.py`, `src/systems/final_assessment.py`, and `tests/test_stage2_foundation.py`. Other foundation changes overlap the milestone files above. Preserved local-only files listed earlier are not new milestone edits.

## Placement and persistence verification

The Dining map has 40 by 40 tiles and 326 original blocked tile rectangles. Candidate placements were accepted after player-body path and interaction-line-of-sight checks against actual map collisions:

| Object | Tile anchor | Persistent ID |
| --- | --- | --- |
| Lists terminal | (6, 30) | `castle_dining_lists_terminal` |
| Searchable table | (8, 25) | `castle_dining_table_01` |
| Searchable crate | (31, 21) | `castle_dining_crate_01` |
| Two-member camp | near (32, 17) | `castle_dining_duwende_01` |

Tests verify the real resolved enemy bodies, exactly two spawns, safe southern arrival, reachable approaches to all props, and actual enemy updates staying inside the northeast camp bounds when lured. The camp is separate from the lesson terminal and southern route. Missing enemies fail assertions.

A headless real-game integration test exercises Lobby -> Dining -> both real editor validations -> one key -> encounter clear -> Lobby -> Dining -> actual crate/table interactions -> slot reload. It confirms one key/claim, Lists mastery, consumed props and no restored encounter or repeat crate reward. Input and encounter defeat are simulated; this is not a manual human combat playtest. Interrupted atomic replacement is separately tested, followed by a successful retry that awards exactly once.

## Exact test results

Each test module ran in a separate Python process with dummy SDL video/audio, using `D:/VScode/.venv/Scripts/python.exe -m unittest discover -s tests -p test_NAME.py`.

| Suite | Passed / run |
| --- | --- |
| `test_stage2_dining.py` | 21/21 |
| `test_stage2_foundation.py` | 6/6 |
| `test_stage_gate.py` | 15/16 |
| `test_stage_handoff.py` | 23/23 |
| `test_stage_selection.py` | 16/16 |
| `test_practice_manager.py` | 2/2 |
| `test_learning_challenges.py` | 3/3 |
| `test_encounter_progress.py` | 6/6 |
| `test_guarded_props.py` | 9/9 |
| `test_editor_feedback.py` | 9/9 |
| `test_tutor_server.py` | 8/8 |
| `test_save_slot_menu.py` | 8/8 |
| `test_stage1_systems.py` | 6/6 |
| `test_editor_caret.py` | 2/2 |
| `test_mang_tahimik.py` | 8/8 |
| `test_tutorial_regressions.py` | 5/5 |
| `test_boss_encounter.py` | 17/17 |
| `test_world_map_view.py` | 12/12 |
| `test_september_report.py` | 9/9 |

Total: **185/186 passed**, with one previously reproduced baseline failure and no new test failures.

The unchanged failure is `test_stage_gate.StageGateTests.test_castle_exit_trigger_is_reachable_from_player_spawn` at `tests/test_stage_gate.py:197`: `The authored castle exit cannot be reached from spawn`. It already failed before Dining implementation. The old learning registry fixture mismatch for `free_coding` was fixed while adding function challenge fixtures; that suite now passes 3/3.

Installed the server's declared `server/requirements.txt` into the workspace virtual environment, including httpx. Tutor tests now pass 8/8. The earlier missing-httpx import was an environment blocker, not a baseline test failure. `pip check` reports no broken requirements. `compileall -q src server` and `git diff --check` pass (Git emits line-ending conversion notices only). This report covers the listed relevant checks, not every test in the repository.

## In-game testing steps

1. From `D:/VScode/CodeBreak`, run `D:/VScode/.venv/Scripts/python.exe main.py`. Load a Castle save, or use a save with Castle unlocked and select Castle through the World Atlas (G). Normal Stage 1 unlock rules remain in force.
2. In Castle Lobby, walk to the northwest Dining doorway (approach around tiles 6-10, 13-15). Hold E at **Enter Dining Area**. You arrive safely at the southern center of Dining.
3. Walk west to the bookshelf terminal near tile (6, 30), approach its edge and hold E to read Lists. Read the lesson, then choose either challenge. Use RUN, then SUBMIT; use the success popup's CONTINUE to return to the selection. After only one challenge, confirm Keys stays 0/5 and the other challenge remains unfinished. Leaving/reloading now should preserve the first pass.
4. Pass the other challenge. Confirm both show Passed / Practice, Lists is mastered and Keys becomes exactly 1/5. Reopen and replay a completed challenge, or use the practice system (P); no additional keys should appear. Include an empty list and a single-item pop when checking your implementation.
5. Search the table near (8, 25) and crate near (31, 21) by approaching and holding E. The crate adds 15 seconds exactly once. Search rewards do not complete Lists or grant keys.
6. Go northeast near (32, 17), defeat both Duwende Mandurug using existing combat controls (E attack, Q dodge). Confirm the encounter clears and Keys stays 1/5. Enemies should remain inside their camp rather than pursue you to the terminal or southern entrance.
7. Return to the southern doorway, hold E for Castle Lobby, then re-enter Dining. Confirm the camp remains cleared and the props stay consumed.
8. Press Esc, select SAVE GAME, return to the menu and reload the same slot. Confirm Keys 1/5, both challenge passes, Lists mastery, cleared camp and no repeat crate time. The remaining Castle curriculum and completion route should still be presented as unfinished.
