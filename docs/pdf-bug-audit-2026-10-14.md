# Audit of bugs or smth.pdf

Reviewed all 19 pages, including screenshots, against the current working tree.
The report includes issues already repaired by earlier changes; those fixes were
checked rather than replaced. Crossed-out items and suggestions were assessed
as report content, not as separate commands.

## Remaining issues repaired

- Page 2 / 11: slider help explicitly describes dragging left and right and the
  resulting volume changes. Both settings panels share this copy.
- Page 11: dodge now uses either Shift key. Gameplay, tutorial instructions,
  practice checklist, boss introduction, HUD, and shared manuals agree.
- Page 16: an expired password lockout clears its stale warning. Cancel is on
  the left and Continue is on the right.
- Page 18 / 19: result popup titles and messages fit their slots; practice
  button labels fit their buttons. Checker feedback renders its complete
  wrapped text, including the answer after `Expected:` and blank lines.
- Page 19: dismissing a result consumes the remaining events in that batch,
  preventing the acknowledgement key's TEXTINPUT from altering the code.

## Existing fixes checked

| Pages | Finding in the current implementation |
| --- | --- |
| 1, 8 | Player movement clamps to map bounds; sprite feet are anchored to the collision body's bottom. Tile-object collision uses the correct bottom origin, and the statue base is solid. |
| 1, 13–15 | Collision-safe enemy spawns, escape-route checks, navigation around obstacles, cross-patrol melee, and return-to-combat behavior are implemented and covered by regression tests. Flying enemies use their own terrain handling. |
| 2–3 | New settings start at font size 25; existing saved preferences remain intact. Intro explains main-menu navigation, question marks, and the help/settings locations. |
| 3–5 | First-launch walkthrough persists its seen state and can be replayed using Help. Menu labels fit their buttons; settings suppress underlying menu hover and input. Editor actions are numbered. Painted fireflies and blue motes have animated overlays. |
| 6 | Display sizing accommodates monitor aspect ratios; authored signs have readable interactions. |
| 7 | Gameplay redraws the map every frame; the boss health bar is drawn only for a live boss. Current HUD frames are ordinary UI, and low-health corner marks are a health warning rather than a lingering boss effect. |
| 8–10 | Chests/barrels link to real lessons, guarded caches require cleared encounters, boss access checks keys and topics, and the entrance trigger handles developer rearming. Loading tips respond to left/right mouse buttons anywhere. New players must equip their sword before attacking. |
| 11–12 | Damage numbers exist for enemy and player hits. Save-slot labels and progress text use bounded layout. |
| 17 | Castle is correctly named and the atlas uses authored map previews. Stage 3 remains a future Citadel placeholder; no nonexistent playable stage was added. |
| 17–18 | Tutorial uses idle animations and renders characters/enemies at the larger practice scale. |

Gameplay settings remain available through **Escape → Settings**. The gear
described by the introductory menu guide is the main-menu settings button.

## Validation

- 162 PDF-related regression tests passed across menu layout, settings,
  passwords, editor feedback, tutorial, loading, interactions, maps, enemy
  navigation, boss triggers, stage gates, completion, and handoff.
- Added behavioral regression cases for password countdown expiry,
  acknowledgement text leakage, and complete checker details.
- Headless tests verify these behaviors; they do not replace manual playtesting
  of the exact screenshot locations and perceived visual scale.

The existing local ghost, music, and dash-through-enemy changes are preserved.
