# Campaign combat difficulty — 23 October 2026

Castle previously reused the Island's species stats and every sword connection interrupted an enemy attack. This made later stages feel similar and allowed attack spam to cancel their strikes. Campaign spawning now passes the room's inherited combat tier to normal enemies, bosses and boss summons.

## Tuning

`src/data/combat_difficulty.py` owns these profiles. Multipliers apply to immutable per-instance stats, never to shared `ENEMY_STATS` records.

| Setting | Island / tier 1 | Castle / tier 2 | Future Citadel / tier 3 |
| --- | ---: | ---: | ---: |
| Normal enemy HP | 1.00× | 1.35× | 1.70× |
| Boss HP | 1.00× | 1.20× | 1.55× |
| Attack damage | 1.00× | 1.30× | 1.60× |
| Movement speed | 1.00× | 1.10× | 1.18× |
| Cooldown from attack start | 1.00× | 0.85× | 0.74× |
| Committed attacks resist interruption | No | Yes | Yes |

HP and damage are rounded to whole numbers. Cooldowns retain at least 0.16 seconds of recovery after the full attack animation. Attack duration, hit timing, aim, reach, collision bodies, awareness, home leash, group sizes, rewards and player stats stay unchanged. Explicit `world.combat_tier` overrides the stage default; otherwise Island, Castle and Citadel resolve to tiers 1, 2 and 3. An unknown stage defaults to tier 1.

Examples: Duwende change from 60 HP / 8 damage to 81 HP / 10 damage in Castle and 102 HP / 13 damage in the future advanced profile. With a standard 25-damage sword, this is three, four and five successful hits. Castle's dedicated Aktan boss changes from 900 HP / 18 damage to 1,080 HP / 23 damage. Boss HP uses its own smaller multiplier to avoid applying normal-enemy durability inflation to a long fight.

## Counterplay and feedback

During a tier 2/3 attack, a nonlethal hit still damages the enemy but does not cancel its committed direction or restart its animation. A lethal hit stops it. Outside an attack, normal flinch remains. A yellow triangle containing an exclamation mark appears above the enemy health bar during wind-up. It is a warning to step or dodge sideways, then punish recovery. The Castle manual explains this rule.

Walls still block attacks and enemies cannot retarget during the wind-up. Dodge immunity still works against every attacker. Beginner/tutorial instances retain exact original stats and interruption behavior. Resetting an enemy restores its tier's maximum HP without stacking multipliers. Island's Core boss armour phases and reinforcements remain unchanged.

Citadel remains a future atlas node with no playable STAGES entry. The advanced profile is prepared and tested, not a claim that Stage 3 encounters exist. Its eventual roster, arenas and boss phases still need authoring and playtesting.

## Verification

116 unique tests passed, with each module in its own process:

- Combat difficulty: 11 (all species across tiers, real attack timing and movement, immutable base stats, attack interruption, lethal hits, sideways evasion, walls, dodge immunity, resets, room inheritance and warning rendering).
- Existing group combat 6; boss encounters 17; Castle room enemies 7; ghost attack effects 4.
- Death checkpoints 2; encounter progress 6; encounter music 6; map enemy visibility 4.
- Stage handoff 23; Castle completion 8; bug-report regressions 17; tutorial regressions 5.

Castle room pursuit checks now exercise actual tier 2 instances against the map's collision bodies. Existing spawn tests confirm all 20 ordinary Castle enemies still resolve, with reachable patrols and safe door arrivals. A first test attempt required installation of the repository's pygame/pytmx dependencies; tests passed after installation. Image-profile warnings were nonfatal.

Headless campaign smoke checks loaded Dining and an interrupted Throne boss fight through `game_screen`, replacing the loading-screen interaction and capturing the real constructed instances. Dining created tier 2 Duwende and Kapre; Throne restored tier 2 Aktan at 1,080 HP / 23 damage. Rendered the actual Dining gameplay screen and separately inspected the committed-attack warning on an attacking Kapre. These short checks do not establish complete fight balance or a full campaign playthrough. Compilation and `git diff --check` passed.

## Manual balance check

1. Fight a Duwende on Island: verify three ordinary sword hits and interruptible attacks.
2. Load Castle; fight a Dining Duwende: four hits, visible warning, no cancellation by a nonlethal hit during wind-up.
3. Dodge sideways during that warning; counterattack after the strike. Check the enemy cannot hit through a table or wall.
4. Clear a camp, change rooms, save/reload and confirm it remains cleared with unchanged bonus-time/key rules.
5. Trigger Aktan legitimately, test defeat/retry and victory, then complete the existing final assessment.
6. Have a first-time learner test these fights on the actual presentation machine. Tune profile values if fights feel tedious or dodging feels too demanding; no learner difficulty score has been measured yet.
