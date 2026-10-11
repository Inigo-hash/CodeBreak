# Stage 2: verified Castle implementation plan

Audit date: 2026-10-11. Repository baseline: `cd9b5b4`.
Design source: [Miro — G1 Flowchart](https://miro.com/app/board/uXjVGETpWHg=/), read directly in view-only mode, including the Intermediate, CodeBreak Overview, and In-game Code Editor documents and flowchart.

**Status: first Dining Lists milestone implemented; the rest of Castle remains an exploration preview.** See [the Dining implementation and verification report](stage2-dining-milestone.md). This is not a complete playable learning stage. This document distinguishes board requirements, observed code, and implementation proposals. Room placements and enemy names in the earlier suggested plan were not requirements found on the board.

## What the board actually requires

| Requirement | Stage 2 interpretation |
| --- | --- |
| Intermediate collections | Lists (access/add/remove), tuples (immutable/indexed), dictionaries (access/update/iterate) |
| Intermediate control flow | `for`, `while`, **nested loops**, `break`, `continue` |
| Intermediate functions | Define/call functions, parameters and return values |
| Intermediate errors | **`try`/`except`**, including invalid input / `ValueError` |
| Intermediate validator | Named functions evaluated on multiple inputs; meaningful failed-case feedback; alternative correct solutions accepted |
| Learning support | Worked example with a different problem; progressive feedback, conceptual hint, structural hint, partial skeleton |
| Mastery | Complete all challenges for a topic; attempts and time alone do not prove mastery |
| Progression | All topics and five keys unlock the exit path, followed by a combined final coding assessment |
| Failed final assessment | Practice coding before another attempt; no heart penalty for assessment failure |
| Rewards | One-time chest rewards; replay is practice. Completion offers a stronger weapon or bonus time |
| Persistence | Multiple save slots; save challenge, topic, enemy, key and checkpoint progress |
| Survival | Five hearts; combat/trap failure costs a heart; previously completed stages remain completed |

**Sets are not in the board's Intermediate list.** Keep them out of the required curriculum unless deliberately added later. OOP, imports/modules, file/JSON handling and comprehensions belong to the board's Advanced stage.

Two board inconsistencies require an explicit implementation choice:

- Restart: overview punishment text and flowchart differ about retaining current-stage progress. Proposal: zero hearts returns to the stage arrival with five hearts while keeping mastered lessons, earned keys, weapons and consumed rewards. Reset only transient combat/position state. Verify this against the agreed game design before changing death rules.
- Controls: board describes Shift dodge / F interaction; the current game uses Q dodge and E interactions/search. Keep current controls in this Stage 2 work; treat rebinding as a separate task with updated tutorial/manual.

## Verified repository state

| Area | Observed state / consequence |
| --- | --- |
| Maps | Five connected TMX maps: Lobby, Dining, Library, Dungeon Prison, Throne. Dungeon filename `map3_dungeon_prison.tmx` is still a Stage 2 room |
| Routes | Lobby connects directly to all four rooms; return routes exist. Room unlocking is not authored yet |
| Map objects | No TMX object-group objects in these five maps: lesson terminals, searchable props, switches, traps and exit still need placement |
| Stage record | `castle` topics/enemies/items empty; required keys zero; no boss, final challenge or exit rectangle |
| Atlas | Called Stage 2 “The Ancient Depths” with forest/temple description, although it opens Castle |
| Room checkpoints | Save room-local stage progress; stage/player keys, learned challenges and inventory remain shared |
| Encounters | Non-default rooms originally forced encounter lists empty, preventing room-authored content |
| Assessment | Screen and gameplay originally tied to Island / `stage1_final_001`; Stage 1 has a four-problem timed rotation |
| Challenge execution | Existing restricted execution and timeout infrastructure. Named-function, multi-input return-value testing still needs implementation |
| Stage 3 | Atlas placeholder `citadel`; no playable Stage 3 record/map for automatic handoff |
| Mang Tahimik | Server prompt derives context from stage/room/challenge data; authoring those records will update his factual context |

### Foundation changes delivered with this plan

- Room records may contain a `world` block with encounters/zones and other map-specific overrides. Non-lobby rooms retain safe empty defaults when no content is authored. Copies isolate runtime edits from shared data.
- Stage gates/assessment prerequisite checks include boss victories in other room checkpoints and ignore a stale checkpoint for the active room.
- Gameplay completion marker/reminder/assessment trigger uses `completion.required_final_challenge`.
- Assessment sessions are stage-specific. `completion.final_assessment_ids` optionally supplies a rotation; Stage 1 keeps its existing default rotation. Other stages default to their required final challenge. Unauthored assessments show an unavailable message rather than starting an Island assessment.
- Castle atlas description/name and manual now describe the actual five-room preview.
- These changes do **not** claim lessons, spawns, boss or a finishable Stage 2 already exist.

## Proposed room content and route

The following is a concrete proposal, not a room assignment found in Miro. Keep room IDs/map filenames stable for old saves. Start with existing art and a small number of enemies.

| Room | Required teaching / playable content | Proposed unlock and rewards |
| --- | --- | --- |
| Lobby | Safe arrival; recap; Mang Tahimik; readable stage manual; worked introduction to the function-test format | Dining and Library available. Dungeon opens after collections. Throne opens after all pre-throne topics. No combat or reward farming |
| Dining | Lists: indexing, length, append/remove/pop; one worked example, at least two distinct challenges; searchable tables/crates; one small Duwende encounter | Key 1 after complete list mastery; revisit for practice |
| Library | Tuples, indexing and immutability; dictionary lookup/update/iteration; worked examples and at least two challenges per topic; guarded archive | Key 2 after both topics; collections unlock Dungeon. Use an existing enemy initially |
| Dungeon, outer cells | `for` and `while`; progress-safe cell switches, readable trap signals, checkpoint | Key 3 after both loop topics; switches check saved mastery |
| Dungeon, inner cells | Nested loops; `break` and `continue`; combine collections with traversal | Key 4 after both topics. Safe retreat to Lobby; unique encounter and prop IDs |
| Throne approach / room | Functions (parameters/return), `try`/`except`; at least two challenges per topic; final worked example; arena; assessment and real exit | Key 5 after both topics. All topic mastery + five keys unlock boss/assessment path. Exit additionally requires the authored boss if retained, and passed final assessment |

Nine required topic groups: lists, tuples, dictionaries, for loops, while loops, nested loops, loop control, functions, exception handling. Final assessment is a separate requirement. Functions can be previewed early using supplied `def`/`return` starter code; assess function mastery in the Throne lessons.

**Do not give one key for every challenge.** Five bundle-completion rewards must be idempotent. The current key helper is per challenge; extend it to bundle mastery or assign one designated final challenge per bundle a reward only when all prerequisites are satisfied. Explicitly set other rewards to zero and prevent prerequisite bypass. Keep Stage 1's existing nine-key contract untouched.

### Lesson/challenge authoring contract

For each topic author: stable ID, explanation, worked example, learning objective, prerequisites, two or more non-identical challenges, starter code where needed, expected behavior, boundary cases, four hint levels, practice variants, and Mang Tahimik topic context. Store authoring in `src/data/`; rules in `src/systems/` or `src/learning/`.

Intermediate challenge tests should include empty and single-element collections, duplicates, boundary indices, missing dictionary keys, termination conditions, and invalid input where applicable. Show input/actual/expected for failures without leaking an entire reference solution.

Named-function validator acceptance:

1. Select a documented function name/parameters from the challenge record.
2. Execute both player code and every test invocation inside the existing timed sandbox, not by calling a returned function after timeout protection is removed.
3. Isolate input/mutable test data between cases; enforce timeout for infinite loops inside the function.
4. Compare return values as values, not only printed output. Preserve valid alternative implementations; use AST checks only for deliberate lesson requirements.
5. Preserve existing Stage 1 validators. Syntax/runtime feedback includes useful line information.

## Encounters and boss decisions

| Candidate | Evidence | Recommended use |
| --- | --- | --- |
| Duwende Mandurug | Bestiary, enemy handling and combat stats exist | First Dining encounter; small group only |
| Tikbalang | Bestiary, animation configuration and combat stats exist | Later heavy guard after narrow-room collision checks |
| Zombie Aktan / Zombie Lapu-Lapu | Asset folders exist; no corresponding registered gameplay definitions found | Deferred until movement/attack/flinch, hitboxes, stats, bestiary and spawn behavior are registered/tested |
| White Lady | `white_lady_attack` frames exist; no registered gameplay definition found | Deferred until complete asset coverage and behavior are verified |
| “Castle Warden” | Proposed identity, not a board-named boss | Optional deliberate existing-asset variant; never represent it as completed new art |

The board calls the final coding assessment a **boss-battle equivalent**. It does not specify a new physical Castle boss. Proposed implementation retains combat + assessment to follow the existing Stage 1 structure, but physical boss identity remains a design choice. Do not hold the teaching slice hostage to a new boss roster.

If a physical boss is retained: register a distinct persistent boss ID; configure room-local arena/zones, spawn anchor, safe entrance/retreat, health and readable telegraphed attacks. Initial two phases can reuse established attack behavior with tuned recovery and escalation. Test collision-safe spawn, no attack through walls, arena disengagement, loss/retry, victory persistence and no repeat reward. Add phase/attack complexity only after playtesting.

No speculative coordinates are prescribed here: inspect tile collision and test each authored object/spawn in-game before accepting its position. The lobby/terminal/door arrival areas must remain safe, accessible and clear of patrol paths.

## Proposed final assessment

Story: produce a castle supply report from records and a threshold.

Example contract: `build_supply_report(records, minimum)` returns a dictionary of totals for valid item records meeting the threshold. Records contain immutable `(item, quantity)` tuples; invalid quantities are skipped through `try`/`except`; iterate a list, accumulate dictionary totals, use a helper function, and return the result. Alternate versions can traverse nested room inventories or stop on a sentinel. Each version must exercise only taught concepts and have multiple independent test cases.

Use at least three variants, authored limits after beginner/intermediate playtesting, fresh saved deadlines, progressive hints and a practice requirement after failure. Preserve mastery, keys and boss victory across retakes. Existing timed rotation handles consumed attempts, but **mandatory failed-assessment practice is not implemented by the foundation changes** and needs its own saved state/UI before completion is accepted.

Completion should present the board's weapon-or-time choice, persist it once, and mark Castle complete. Until Citadel has a real stage/map, return safely to the menu with an honest “Stage 3 coming later” state rather than pretending to enter it. Connect `next_stage` only when Stage 3 is enterable.

## Build order and acceptance gates

### 1. Dining vertical slice — next implementation milestone

- [ ] Named-function validator and timeout/boundary tests.
- [ ] Lists lesson, worked example, two challenges, progressive hints and practice versions.
- [ ] Actual reachable terminal/searchable prop positions, authored through supported map objects.
- [ ] One collision-safe Duwende encounter with unique `castle_dining_*` IDs in the Dining room's `world` block.
- [ ] Bundle mastery earns Key 1 once; save/reload/re-entry keeps it and the cleared encounter.
- [ ] Mang Tahimik correctly explains Castle/list content from registered records.
- [ ] Walk through Lobby → Dining → Lobby → Dining and reload a slot; no duplicated rewards, blocked arrivals or repopulated cleared encounter.

### 2. Collections and Dungeon

- [ ] Library tuple/dictionary lessons, challenges and Key 2.
- [ ] Route prerequisite evaluator and locked-door feedback; no permanent lockout or bypass.
- [ ] For/while/nested/control-flow content, cell switches, traps/checkpoints, Keys 3–4.
- [ ] Termination, nested-loop edge cases and alternate valid code tested.
- [ ] Save each room independently; stage manual/objectives reflect aggregate stage progress.

### 3. Throne and completion

- [ ] Functions / errors topics and Key 5; all required topic challenges registered.
- [ ] Decide combat boss or assessment-only design; if combat, implement verified arena/telegraphs/retry.
- [ ] Authored assessment rotation and failed-attempt practice gate.
- [ ] Room-local exit rectangle and completion prerequisites; inaccessible until requirements satisfied.
- [ ] One-time weapon/time reward and honest Stage 3 placeholder/handoff.
- [ ] Room/boss music, bestiary, item descriptions and full Stage 2 manual updated.

### 4. Release checks

- [ ] All terminal/door/switch/chest positions reachable from intended arrival; no spawn inside solid/restricted tiles.
- [ ] At most small groups in tight rooms; safe lesson interaction and retreat.
- [ ] Existing Stage 1 completion and timed assessment rotation still work.
- [ ] Restart behavior explicitly agreed, then tested against board expectation.
- [ ] Saves across rooms, interrupted assessments, practice retakes and older slots migrate safely.
- [ ] Playtest beginner learners: readability, hints, timing, encounter difficulty and mastery criteria.

## Verification delivered now

`tests/test_stage2_foundation.py` covers authored room encounters without cross-map leakage/data mutation, transition reward/checkpoint persistence, cross-room boss records with stale active checkpoint exclusion, Stage 1 rotation compatibility, Stage 2 attempt isolation, and the Stage 2 assessment-screen pass callback. These verify foundations; headless tests do not certify unplaced objects or unbuilt content as playable.

Validation run: 6 foundation tests, 23 stage-handoff tests and 12 atlas/world-map tests passed (41 total); Python compilation and whitespace checks passed. Broader gate suite passed 15/16. Its `test_castle_exit_trigger_is_reachable_from_player_spawn` failure was reproduced on unchanged `cd9b5b4` (despite its name it tests the Island stage). The ending suite's boss-checkpoint test still expects the old warning modal; its identical failure was also reproduced on unchanged main. The ending suite was interrupted when its final editor mock entered an interactive assessment; it is not reported as a passing suite. Repair those legacy test fixtures separately; they do not validate new Castle placements.
