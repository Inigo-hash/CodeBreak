# Style Guide Migration — Worked Example

**Date:** 31 August 2026
**Scope:** `ui/theme.py`, `screens/how_to_play.py`, `screens/topic_found.py`

The first two screens moved onto the shared palette, as the proof that the
style guide describes the game that exists rather than one we would like to
have.

## What changed

1. **`ui/theme.py`** gained the 13-token `modal_*` group. Every value was
   copied from what screens were already drawing — nothing was invented and
   nothing was adjusted to taste.
2. **`screens/how_to_play.py`** — 8 local constants and 4 inline colors
   replaced by token lookups. The old constant names are kept, because
   `tutorial.py` imports two of them to draw the same manual.
3. **`screens/topic_found.py`** — 9 local constants replaced. Names kept
   local; they read better at the call sites.

Both files now contain **zero color literals**.

## Proof it changed nothing

Both screens were rendered headlessly before and after the change at
1920x1080 and compared pixel by pixel:

| Screen | Differing pixels |
|---|---|
| How To Play | 0 of 196,608 sampled |
| Topic Found | 0 of 196,608 sampled |

All 16 test modules pass.

## The one deliberate difference

`tutorial.py` imports `STONE_DARK` from `how_to_play.py` to fill the inner
area of its stage manual. That constant was 28, 30, 38, while How To Play
drew its own inner area with 26, 28, 36 — so the two copies of what is
meant to be *the same sheet of paper* were two shades apart. Both now use
`modal_inner`, so the tutorial's manual shifts by two values and finally
matches the panel it is a copy of.

## What this buys

Before, "make the secondary text in modal windows lighter" meant finding
five files and hoping you got them all. Now it is one line in `theme.py`.
That is also what makes the pending sign-off decisions cheap: collapsing
the five dim greys into one is now a single edit for every screen that has
been migrated.

## Recipe for the next screen

1. Screenshot the screen headlessly (drive the loop, capture a frame).
2. Replace each local constant with the `UI_COLORS` token holding the same
   value. If no token matches, that colour is either art (leave it) or a
   genuinely new token (add it, and add it to the guide).
3. Screenshot again and diff. Zero differences means the tokens describe
   the screen correctly.
4. If a difference *is* intended, say so in this file — like the tutorial
   note above.

---

# Round two — 5 September 2026

**Scope:** `topic_lesson.py`, `inventory.py`, `tutorial.py`, plus the two
palette decisions.

## What changed

1. Two more tokens, again copied from what the screens already drew:
   `modal_danger` (220, 110, 110) and `modal_slot` (20, 22, 28).
2. The three remaining modal screens moved onto the shared palette. The
   tutorial also stopped importing `STONE_DARK` and `STONE_LIGHT` from
   `how_to_play.py` and now reads the theme directly, so the two screens
   are no longer coupled.
3. The signed-off decisions applied: `blue_bright` is now 80, 180, 255, and
   secondary text everywhere is one grey at 170, 175, 190.

Left deliberately local: the tutorial's green Begin accent and its
practice-room floor. Both are scene art, not interface chrome.

## Proof

The Topic Lesson screen is deterministic and was diffed pixel by pixel:
**85 changed pixels of 518,400 sampled**, every one of them the secondary
text colour and its antialiasing — the intended change, nothing else.

The inventory could not be diffed this way: two captures of the *same*
code differ by 485,077 pixels, because that screen animates. It was
verified by value instead — each of its nine constants was compared against
what it held before:

| Screen | Constants unchanged | Intentionally changed |
|---|---|---|
| `inventory.py` | 8 | 1 (`TEXT_DIM`) |
| `topic_lesson.py` | 9 | 1 (`TEXT_DIM`) |

**A note for the next round:** pixel-diffing only proves anything on a
screen that draws the same frame twice. Check that first, and fall back to
comparing values when it doesn't.
