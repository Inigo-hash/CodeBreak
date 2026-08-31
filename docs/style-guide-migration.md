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
