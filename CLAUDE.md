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

There is no pytest in this environment, and `tests/` has no `__init__.py`,
so `unittest discover` cannot import it as a package. Run modules by name
with the repo root on the path:

```bash
PYTHONPATH=. python -m unittest tests.test_stage_gate
```

Running every module in one process segfaults during teardown (SDL, not a
test failure). Loop over them instead:

```bash
for f in tests/test_*.py; do n=$(basename $f .py); PYTHONPATH=. python -m unittest "tests.$n"; done
```

158 tests, 150 passing. The eight failures predate the stage handoff work
and are all tuning that drifted from its own tests: the torch heal rate
(`test_night_lighting`), the manananggal's reach
(`test_bug_report_regressions`), the trapped chest's authoring
(`test_stage1_systems`), and the Island's tenth lesson, which the data
lists nine of (`test_stage_gate`). To check a change boots the real game
without a display:
`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy timeout 10 python main.py`.

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
- `game_screen` is ~2,200 lines and holds loading, input, combat, drawing
  and saving. It should be split, but incrementally, behind the tests.

## Current state

**Stage 1 (Island)** is playable and complete: 10 beginner lessons, three
roaming enemy types, a boss with four armour phases, night lighting with fixed
torches, save slots with PBKDF2-protected passwords (deletable from the slot
panel, password required for a protected one), a paper world map, and
a stage information panel. Searchable props are guarded (`systems/guards.py`):
a prop with enemies camped around it stays shut until they are defeated, and
standing in torchlight regenerates energy four times as fast and heals
at the same rate.

**Stage 2 (Castle)** is enterable. Clearing the Island's gate now hands the
run over to `map2_castle_lobby.tmx` instead of returning to the main menu:
the player keeps their lessons, stored topics and cleared-stage list, loses
the Island's keys and map position, and arrives at the foot of the grand
staircase with a full heart row. The lobby is lit rather than night, has
two named zones and one placeholder objective, and is otherwise empty. It
still needs: the rest of the map drawn (its lower half is void), 10
intermediate lessons with behavioural validators, enemies and encounters, a
boss, and an exit gate - all of them additions to `stages.py` rather than
to `game.py`.

**Known gaps**, in rough priority:

- Validators check code *shape* via AST, not behaviour. Beginner syntax
  lessons survive this; loops and functions will not. Stage 2 needs
  behavioural validation - run the code, compare output - using the
  sandbox that already exists.
- `bonus_time` is awarded by kills and chests, displayed, and saved, but
  nothing consumes it.
- The exit gate's key requirement and lesson requirement are the same
  condition: keys only come from those lessons, one each.
- Hearts reset to 5 on reaching zero, so death has no lasting cost.

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
