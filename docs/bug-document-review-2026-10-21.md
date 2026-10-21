# Bug document review — 21 October 2026

Source: the connected Google Doc `bugs or smth`, including its screenshots.
The source wording and screenshots are preserved. Strikethrough means the
specific requirement has implementation evidence and passing regression or
layout checks; it does not mean every possible device and game state was tested.

## Changes from this review

- Player damage now creates red floating numbers for successful monster and
  trap hits. Numbers use actual health lost, including lethal damage capped by
  remaining HP; dodges and invulnerability do not create false hits.
- Saves record an active boss encounter. Reloading an unfinished fight restores
  that boss at full health instead of leaving an empty arena. Recorded victory
  overrides any stale active marker. Older saves without this marker still
  require leaving and re-entering the boss doorway.
- New settings default to font size 28 instead of 25. Saved font preferences
  remain intact. Settings help text uses a larger font too.
- The replayable menu walkthrough now explains Mang Tahimik and music mute.

## Existing fixes verified

The isolated test suite and 51 rendered screen states cover menu and editor
layout, modal input ownership, password lockout expiry, signs and statue
collision, map bounds, enemy navigation and attack rules, guarded loot,
lesson/boss requirements, sword equipping, tutorial sprite sizing/animation,
loading controls, stage names, and doorway-triggered boss introductions.
Shift is the current dodge key. Historic audit documents describe older keys.

The earlier October 14 audit incorrectly said player damage numbers already
existed. Enemy numbers existed; this review adds the missing player path.

## Items intentionally left open in the source

- Vince's unspecified "other recommendations"; only the numbered-button part
  can be verified from the supplied description.
- Replacing the atlas artwork and removing Topic Guidance are design choices.
  Topic Guidance is used by the current mastery/progress feature.
- Stage 3 remains under development as requested.
- The latest location-specific Tikbalang, minimap movement, and post-developer
  boss-damage reports need a reproducible save/input sequence. Generic behavior
  tests pass, but they do not prove those exact screenshot scenarios resolved.
- The new unclear-coding-instructions entry does not identify a challenge or
  quote the confusing wording.

## Validation

- 367 tests passed across 41 modules using a separate process per module.
- Rendered all 51 audit states at 1024x768 with font size 28, including the
  modified walkthrough/help panels.
- New behavioral tests cover player damage feedback and a real gameplay
  save/reload of an unfinished boss encounter, plus stale victory markers.
- Headless rendering and tests do not replace a complete manual campaign
  playthrough on the reporter's computer.
