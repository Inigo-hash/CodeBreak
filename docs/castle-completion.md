# Castle completion and audit fixes

Implemented 18 October 2026, from main `a3fa2a8`.
Debug mode deliberately remains enabled during development.

## Player behavior

| Room | Topics | Mastery reward |
| --- | --- | --- |
| Dining | Lists (existing two challenges) | Key 1 |
| Library | Tuples, Dictionaries | Key 2 after both topics |
| Dungeon | For Loops, While Loops | Key 3 after both topics |
| Dungeon | Nested Loops, Break and Continue | Key 4 after both topics |
| Throne | Functions, Try and Except | Key 5 after both topics |

There are nine topics and 18 required challenges. Each topic has explanation,
a worked example separate from its challenge stories, starter scaffolding,
four progressive hints, boundary cases and practice access. Later terminals
require the preceding topic's mastery. Room passages stay available for
exploration and retreat; lesson prerequisites and the boss gate enforce
learning progression. Lesson terminals have visible gold console markers
that turn green when mastered.

The five keys plus all lesson challenges unlock Zombie Aktan's arena. Boss
victory unlocks one of three report assessments, each with a 15-minute base
limit. These combine collections, loops, return values and conversion error
handling. Every test invocation uses the timed sandbox, fresh globals and
copied input. Input/actual/expected feedback is retained. Deliberate syntax
checks supplement behavioral checks for the loop/error/helper lessons.

Earned bonus time adds up to 300 seconds to the next final assessment attempt.
Starting spends only that allocation, saved together with its deadline and
consumed rotation entry. Declining the briefing, taking required practice,
or replaying a mastered lesson spends none. Failed or interrupted Castle
attempts require a solved untimed report before another timed attempt.
Lessons, keys and boss victory survive retakes; no assessment heart penalty.

Passing any Castle assessment writes the stable `castle_supply_final`
completion marker. The exit exists only in the Throne arena, at tiles
(18, 11) through (22, 13). It checks all lessons, five keys, boss victory and
the final marker. A legitimate exit records Castle completion and returns to
the main menu. Citadel remains an unavailable future chapter. Developer
exploration can still bypass gates but does not claim campaign completion.

## Other fixes

- White Lady loads `white_lady/floating` and `white_lady/white_lady_attack`
  correctly, using all nine frames in all four directions. Flinch alone
  reuses an attack pose. Missing animation sequences report which group and
  direction is absent.
- Mang Tahimik's source portrait already had a load cache; scaled HUD sizes
  are now cached too, eliminating repeated resizes.
- Topic mastery is reconciled independently from shared bundle rewards.
  This avoids a prerequisite deadlock between Tuples and Dictionaries.
- The stage gate bounds the missing-challenge list and shows final-assessment
  status. Assessment instructions scroll while confirmation stays visible.
- The loading-screen test checks the tutorial call's loading argument through
  the AST, allowing the additional character-selection argument.
- Atlas copy, manual, tutor knowledge, README and architecture notes reflect
  the implemented content. Earlier milestone reports are marked historical.

## Verification

All **334 tests across 38 modules passed**, with each module in a separate
Python process using dummy SDL video/audio. Compilation and `git diff --check`
also passed. The existing Island, ghost attack, combat, saves, editor, tutor,
room encounters and stage-handoff suites remained passing.

New verification covers all authored solutions and incorrect returns;
practice registration; topic prerequisites and exact once-only five-key
rewards; saved room/boss/mastery progress; real-map player-sized reachability
and interaction line of sight for every terminal and the exit; four-direction
White Lady frames; scaled-image caching; capped bonus time; interrupted
attempts; and unsolved/solved practice before retaking.

The real gameplay integration opens actual editors in all teaching rooms,
submits valid function solutions, earns five keys, runs an actual assessment
editor, spends 300 of 400 bonus seconds, exits through the legitimate gate,
and reloads the completed save. UI selections and boss victory are simulated;
it is not a claim of a manual combat playthrough. The enemy suites separately
exercise pursuit, melee, walls, animation and boss placement.

Rendered game frames in Library, Dungeon and Throne were visually inspected.
Terminal placements over dark wall areas were moved onto visible floor.
Assessment timings and educational quality still need learner playtesting;
automated correctness checks do not establish learning effectiveness.
