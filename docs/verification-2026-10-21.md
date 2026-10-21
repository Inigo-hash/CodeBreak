# CodeBreak verification — 21 October 2026

The available Island → Castle campaign passes an automated progression run
through the final Castle exit. The resulting temporary save records both
completed stages and 29 passing challenge markers: nine Island lessons,
18 Castle challenges, and the two stage finals.

## Fixes verified

- Restored all nine required Castle lesson terminals to their intended rooms.
  Each placement has a unique persistent ID, visible terminal artwork, and a
  reachable interaction position with clear line of sight. Restored Dining's
  independent searches and removed obsolete lesson mappings.
- Cancelled discoveries and unfinished lessons can be revisited, including
  after loading a save. Island lesson keys arrive immediately and only once.
  Independent caches award their bonus once; untagged scenery remains empty.
- Enemy strikes use their committed aim during windup, including diagonals.
  Sideways movement can evade that aim. Attack light follows the same aim.
  Multiple attackers can deal damage independently while dodge protection
  remains global.
- Confirmed the recent minimap, tutor, editor, low-health and game-over changes.
  Review is available after a coding death and absent after an ordinary
  combat death. The tutor and its chat window retain their bottom-right anchor.
- Expanded reference solutions to cover the five additional iterative/list
  challenges. Every shipped graded challenge has an accepted runnable solution.

## Results

| Check | Result |
| --- | --- |
| Complete test suite | 387 tests across 44 isolated modules; all pass |
| Campaign progression | Island lessons, final, handoff, Castle lessons, final, legitimate exit |
| Campaign completion save | `completed_stages = ["island", "castle"]`; 29 challenge markers |
| Core boss combat simulation | 30 connected sword hits, all three phases, one dodge; 81 HP remaining |
| Zombie Aktan combat simulation | 36 connected sword hits, one dodge; 100 HP remaining |
| Actual entry point | `main.py` boot and 90 main-menu frames; clean quit |
| Screen rendering | 51 states at 1920×1080; seven key states at 1280×720 and at 1024×768 with larger text |
| Python compilation and whitespace | Pass |
| Player save slots and settings | File hashes unchanged |

The test runner uses the workspace virtual environment and a fresh temporary
save/settings directory in each process. SDL modules run separately to avoid
global display state leaking between suites.

## Scope

The campaign run submits real code through the production editor/checkers and
exercises prerequisites, rewards, saving, stage handoff, assessments and gates.
UI choices, room routing and boss completion checkpoints are scripted. It is
an automated verification, not a continuous manual keyboard playthrough.

The separate boss simulations use production movement, collision, attack,
damage, cooldown and dodge methods at 60 Hz. HP is not overridden. Their arenas
exclude map terrain and reinforcement waves. Automated geometry tests also
cover every enemy species at eight angles and both combat scales.

The tutor relay is covered by local tests; live external model responses were
not requested. Citadel remains the game's intentionally unavailable future
chapter. Castle is the last currently authored playable stage.

## Workspace evidence

- [Suite results](../../.codex_verification/suite-report.json)
- [Campaign trace](../../.codex_verification/campaign_finish_report.json)
- [Boss combat results](../../.codex_verification/boss_combat_verification.json)
- [Screen rendering manifest](../../.codex_verification/layout-1920/manifest.json)
- [Startup capture](../../.codex_verification/startup-main-menu.png)

Repeatable verification scripts and individual test logs are in
`D:\VScode\.codex_verification`.
