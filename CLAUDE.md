# CodeBreak

A Pygame game-based learning system: a top-down island you explore, with
Python coding challenges at terminals scattered across it. Solving lessons
earns the keys that open the stage exit; a boss guards the way out.

Written for a Software Engineering thesis, so the learning system is the
point, not a side feature.

## Running it

```bash
python main.py
```

Dependencies are in `requirements.txt` (pygame, pytmx, numpy).

## Running the tests

Run each module in a separate process with the repository root on the path.
Pygame/SDL teardown can segfault when every module shares one process.

```bash
for f in tests/test_*.py; do
  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python -m unittest discover -s tests -p "$(basename "$f")" || exit 1
done
```

Install `requirements.txt` and `server/requirements.txt` for the complete suite.
A headless startup smoke check is:
`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy timeout 10 python main.py`.
A timeout exit code of 124 means the game stayed open for that check.

## Where things live

| Concern | Location |
|---|---|
| Entry point | `main.py` -> `src/screens/main_menu.py` |
| Gameplay loop | `src/screens/game.py` (`game_screen`) |
| Other screens | `src/screens/` - menus, world map, inventory, tutorial, boss modals, stage info |
| Authored content | `src/data/` - pure data, no pygame |
| Game rules | `src/systems/` - combat, spawns, save, stage gate, stage handoff, progress, boss trigger, audio |
| Learning system | `src/learning/` - sandbox (runs code), challenge_manager (routes), validators/ |
| Editor + HUD | `src/ui/` |
| Entities | `src/entities/` - player, enemy, chest |
| Map | `assets/map/tmx/` - `map1.tmx` (Island), `map2_castle_lobby.tmx` (Castle), authored in Tiled |

`src/data/` is the first place to look for "how do I change what the game
contains". Nothing in it imports pygame or draws anything.

## The stage contract

`src/data/stages.py` holds one record per stage. Its `world` block is
everything `game_screen` needs to load that stage - map, music, boss music,
night, spawn, zones, encounters, walkable-ground layer and gids,
save-migration version. `stage_world(stage)` fills in defaults for anything
omitted.

A stage with no `world["map"]` is content-only: menus and saves can name
it, but entering it returns to the main menu instead of crashing.

**Stage order** is authored too. A record's `next_stage` names where its
exit gate leads; `src/systems/stage_handoff.py` resolves that, decides
whether the next stage has a map to walk into, and rewrites the save for
it - keeping what the player learned, dropping what belonged to the stage
just left. `game_screen` returns `"next_stage"` after writing that save,
and `run_stage_chain` in `start_game_menu.py` reloads the slot and
re-enters gameplay on the new stage. A stage naming no next stage, or one
with no map, still ends the run at the main menu.

**Adding a stage** means writing a `world` block and authoring a TMX map -
`game.py` should not need editing. If you find yourself adding a stage
check inside `game_screen`, the value belongs in the stage record instead.

Map coordinates in data files are **fractions of map size** (0.0-1.0), not
pixels - spawn, zone rects, encounter anchors, the exit rect. This survives
a map resize. `F6` prints the player's current fraction (DEBUG_MODE only,
`src/config.py`).

## Adding a lesson

Five places, in this order:

1. `src/data/topics.py` - the lesson text, keyed by `topic_id`, naming its `challenge_id`.
2. `src/data/challenges.py` - the problem, its `type`, and the `expected` data.
3. `src/learning/validators/` - a validator for that `type`, registered in `challenge_manager.py`.
4. The TMX map - an object with a `topic_id` property, so the lesson is reachable.
5. `src/data/stages.py` - list the challenge id in the stage's `manual.topics` and `completion.topic_key_rewards`.

`tests/test_stage_gate.py` checks that every required lesson is both mapped
and walkable from spawn, so a lesson authored in data but not placed on the
map fails the tests rather than stranding a player.

## Conventions worth knowing

- **Data modules are pure.** `src/data/*` never imports pygame.
- **Boss tuning is per boss**, in `combat.BOSS_PHASES` - thresholds, sword
  damage, aggression, reinforcement pools. A boss with no entry takes
  normal weapon damage and never changes phase.
- **`resolve_encounter_spawns` takes `zones` keyword-only with no default**,
  deliberately: a new stage must not silently resolve spawns against
  another stage's zone labels.
- **Comments explain why, not what.** Existing files carry the reasoning
  behind non-obvious choices; match that when editing them.
- `game_screen` is ~3,400 lines and holds loading, input, combat, drawing
  and saving. It should be split, but incrementally, behind the tests.

## Current state

**Stage 1 (Island)** has nine required beginner lessons, nine keys, a
Corrupted Core boss and a timed assessment rotation. Searchable props, torch
healing, room/stage save checkpoints, password-protected slots and inventory
are implemented. Preserve its existing progression contract.

**Stage 2 (Castle)** has five connected maps, nine intermediate topic groups
and 18 required function challenges. Dining: Lists; Library: Tuples and
Dictionaries; Dungeon: For/While/Nested Loops and Break/Continue; Throne:
Functions and Try/Except. `castle_curriculum.py` owns the new lesson data.
Two challenges master a topic; five bundles each earn one key exactly once.
Topic mastery is separate from bundle rewards, so a prerequisite topic can
unlock the next one before a shared key bundle is complete.

All five keys and all required challenges unlock Zombie Aktan's Throne arena.
Boss victory unlocks a three-report timed assessment rotation. Failed or
interrupted Castle attempts require a solved untimed practice report before
retaking. Passing records `castle_supply_final` as the completion marker,
regardless of which rotation variant was used. The exit exists only in
Throne. Completing Castle saves completion and returns to the menu; Citadel
has no playable map yet.

Earned `bonus_time` extends final assessment attempts by up to 300 seconds per
attempt. It is spent and persisted with the started attempt; unspent time
remains saved. Declining the briefing or doing required practice spends none.

White Lady uses `white_lady/floating` and `white_lady/white_lady_attack`.
There are no dedicated flinch frames, so flinch reuses an attack pose.
Missing animation sequences raise a clear asset error instead of crashing
through `max()` on an empty sequence.

Debug mode remains enabled by default for active development, by request.
Developer exploration itself still requires F4 and never marks a bypassed
stage as legitimately complete. Assessment timings and new curriculum need
learner playtesting; automated tests do not establish teaching effectiveness.
See `docs/castle-completion.md` for the current implementation and verification.

## Design docs

`docs/` holds the design references, written from the code and dated:

| File | What it answers |
|---|---|
| `style-guide.md` | Every colour token and what it means, the type scale, and which screens still declare their own palette |
| `style-guide-migration.md` | The worked example - two screens moved onto the shared tokens, with the pixel-diff proof |
| `screen-flow.md` | How all 19 screens connect, what opens and closes each one, and the navigation inconsistencies found |

They describe the code on the day they were audited (31 Aug 2026). Re-check
them before relying on the per-screen tables.

## Older docs

`project_structure_v1.md`, `v2.md` and `v3.md` are historical snapshots of
an earlier layout and are out of date - they predate `src/systems/`,
`tests/`, and most of `src/data/`. Trust this file and the source.
