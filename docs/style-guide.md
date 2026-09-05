# CodeBreak UI Style Guide

**Status:** v2, audited 31 August 2026, decisions applied 5 September 2026.
**Owner:** software design.

This is the reference for what CodeBreak's interface is made of: the colors
and what each one means, the two typefaces, and the shared drawing helpers
every screen should be built from.

It is written from the code, not from an ideal. Where screens disagree
today, the disagreement is recorded and a winner is recommended, marked
**needs sign-off** — those are design decisions, not bugs to be quietly
fixed by whoever edits the file next.

---

## 1. How to use this

Everything shared lives in `src/ui/theme.py`. A screen should import from
there rather than defining its own colors:

```python
from src.ui.theme import UI_COLORS, body_font, draw_button, draw_panel, title_font
```

Two systems are deliberately *not* part of this guide and must not be
folded into it:

| System | Where | Why it is separate |
|---|---|---|
| The paper chart | `src/ui/chart.py`, `src/screens/world_map.py` | The map is an object the character carries. Warm parchment and brown ink are the point; stone and bronze would make it another window of the interface. |
| The code editor | `src/ui/editor_theme.py` | Three player-selectable themes (BLUE / DARK / LIGHT). Its colors change at runtime by design. |

---

## 2. The palette

### 2.1 Shared tokens — `theme.UI_COLORS`

These exist today and are the vocabulary everything else should be
described in.

| Token | RGB | Role — what it *means* |
|---|---|---|
| `stone_deep` | 12, 13, 18 | Deepest recess. The outer body of a HUD panel. |
| `stone` | 29, 31, 40 | The panel face itself, one step up from the recess. |
| `stone_light` | 45, 48, 59 | Lit top edge, carved corner caps, raised surfaces. |
| `bronze_dark` | 91, 62, 34 | Shaded bottom edge; the resting border of a de-emphasised control. |
| `bronze` | 171, 119, 55 | The normal border of anything framed. The default rim. |
| `gold` | 218, 177, 86 | Headings, key labels, the primary action's fill. |
| `gold_bright` | 226, 186, 96 | Primary action, hovered. |
| `gold_deep` | 139, 105, 20 | Bottom of the primary button's gradient. |
| `gold_text_dark` | 26, 19, 6 | Text *on* gold, where light text would vanish. |
| `blue` | 72, 166, 224 | Focus. A panel that currently has the player's attention. |
| `blue_bright` | 120, 205, 255 | Hover, and the keyboard focus ring. |
| `crimson` | 190, 42, 52 | Damage, danger, HP. |
| `parchment` | 226, 207, 164 | Map paper. Only for chart surfaces. |
| `text` | 240, 237, 224 | Body text on stone. Warm off-white, not pure white. |
| `text_dim` | 156, 161, 174 | Secondary text, unset values, disabled labels. |
| `button_fill` | 20, 26, 42 | Standard button body. Deep navy, not grey — grey reads as unstyled placeholder against the menu art. |
| `button_fill_hover` | 34, 45, 69 | Standard button, hovered. |

**The rule to remember:** bronze is *normal*, blue is *focus or hover*,
gold is *heading or primary*, crimson is *danger*. If a border changes
color, it should be saying one of those four things.

### 2.2 The second palette nobody wrote down

Five screens share a *different*, lighter panel style from the HUD stone
one — and each defined it privately, under a different name. These values
were already a system; they were just never written down.

**They are now in `theme.UI_COLORS` as the `modal_*` group.** CodeBreak has
*two* legitimate panel styles, not one broken one: the dark carved **stone
panel** belongs to the HUD, where it sits on top of the world and must not
compete with it, and the lighter **modal panel** belongs to the full-screen
windows the game pauses for.

| Token | RGB | Role | Used to be called |
|---|---|---|---|
| `modal_panel` | 36, 38, 48 | Window body | `PANEL_BG`; inline in how_to_play |
| `modal_inner` | 26, 28, 36 | Inset area inside the window | `PANEL_INNER`; inline |
| `modal_frame` | 90, 94, 110 | Window border, slot border | `METAL_FRAME`, `FRAME`, `SLOT_BORDER` |
| `modal_frame_hover` | 140, 146, 165 | Border under the pointer | `FRAME_HOVER`, `SLOT_HOVER` |
| `modal_accent` | 255, 220, 120 | Headings, dividers, the selected slot | `YELLOW_GLOW`, `ACCENT`, `SLOT_SELECTED` |
| `modal_heading` | 80, 180, 255 | Section headings inside a window | `BLUE_GLOW` |
| `modal_button` | 42, 46, 58 | Button body | `BUTTON_BG`, `STONE_MID` |
| `modal_button_hover` | 60, 90, 130 | Button under the pointer | `BUTTON_HOVER`; inline |
| `modal_button_edge` | 62, 68, 82 | Button rim | `STONE_LIGHT` |
| `modal_text` | 255, 255, 255 | Titles and primary text in a window | `WHITE`, `TEXT_MAIN` |
| `modal_text_soft` | 215, 215, 220 | Body copy | `BODY_TEXT` |
| `modal_text_dim` | 170, 175, 190 | Secondary text | `TEXT_DIM` |
| `modal_success` | 120, 200, 140 | Done, passed, complete | `SUCCESS`, `TEXT_DONE` |

A `draw_modal_panel()` helper is the obvious next step, but it is not
written yet — the windows still each draw their own frame, they just no
longer each invent their own colors.

### 2.3 Real conflicts

Same name, different color, depending on which file you open:

| Name | theme.py | main_menu | how_to_play | game_over |
|---|---|---|---|---|
| "stone dark" | **12, 13, 18** | 14, 14, 18 | 28, 30, 38 | 14, 14, 18 |
| "stone mid" | **29, 31, 40** | 24, 25, 31 | 42, 46, 58 | 26, 27, 34 |
| "stone light" | **45, 48, 59** | 38, 39, 47 | 62, 68, 82 | 40, 41, 50 |

And the accents:

| Concept | Shared token | What screens actually draw |
|---|---|---|
| ~~Hover blue~~ | **settled:** `blue_bright` is now 80, 180, 255 | was 120, 205, 255 against three screens drawing 80, 180, 255 |
| Gold | `gold` 218, 177, 86 | 255, 220, 120 in five screens |
| Danger | `crimson` 190, 42, 52 | `DANGER` 220, 110, 110 in topic_lesson; `BLOOD_RED` 200, 40, 40 in game_over |
| Body text | `text` 240, 237, 224 | pure white 255, 255, 255 in five screens |
| ~~Dim text~~ | **settled:** one grey at 170, 175, 190 | was seven values: 156,161,174 · 160,165,180 · 170,175,190 · 150,155,170 · 180,180,190 · 185,188,196 |

**Seven different greys for "dimmer text" was the worst of these** — an
eighth appeared in the tutorial between the audit and the fix. Nobody chose
seven; they accumulated one screen at a time. There is now one.

**Recommendations — need sign-off:**

1. **Stone family:** keep `theme.py`'s values. The menu's are close enough
   to be invisible; How to Play's are a genuinely different, lighter grey
   and should move to the modal group instead.
2. ~~**Hover blue**~~ — **done.** `blue_bright` is 80, 180, 255, and the
   menu and Game Over now read it from the token instead of redrawing it.
3. **Gold:** keep both, named honestly — `gold` 218, 177, 86 for HUD and
   carved chrome, `modal_accent` 255, 220, 120 for headings and highlights
   inside modal windows. They are used in different contexts and the
   brighter one would look wrong on the HUD.
4. **Danger:** one value, `crimson`. Game Over's blood reds stay, as
   scene-specific art rather than UI tokens.
5. ~~**Dim text**~~ — **done.** One value, 170, 175, 190: the lightest of
   the cluster, chosen for contrast on small labels over dark panels, and
   already what the two first-migrated screens used.

---

## 3. Type

Two families, both bundled in `assets/fonts/` so the game renders the same
on a machine that has neither installed.

| Helper | Family | Use for |
|---|---|---|
| `title_font(size, bold=True)` | Exo 2 Bold / SemiBold | Titles, headings, button labels |
| `ui_font(size, bold=False)` | Exo 2 Regular / SemiBold | Menu chrome that is not a heading |
| `body_font(size, bold=False)` | JetBrains Mono NL | Body copy, stats, keys, anything code-shaped |

Two decisions worth keeping:

- **Exo 2** was chosen to echo the blocky lettering of the CodeBreak logo.
  The serif face the game used to ship sat badly against it.
- **The no-ligature cut** of JetBrains Mono is deliberate. The normal cut
  draws `==` and `!=` as single merged glyphs, which is the last thing a
  player learning Python operators should be reading.

**Sizes are requests, not pixels.** Both families render taller than the
faces the layouts were originally tuned against, so `theme.py` scales every
request — Exo 2 by 1.11, JetBrains Mono by 0.74 — to keep rendered height
where the panel maths expects it. Pass the size the layout wants and let
the helper correct it.

**Accessibility scale.** `settings_state.font_scale()` multiplies every
request, driven by the font-size setting. Because it is applied inside the
three helpers, a screen gets it for free — but only if it uses them. Any
screen that builds a `pygame.font.Font` directly opts itself out of the
accessibility setting, which is a second reason not to.

---

## 4. Components

| Helper | What it draws | Notes |
|---|---|---|
| `draw_panel(surface, rect, emphasized=False, radius=8, alpha=238)` | The carved stone HUD panel: shadow, deep body, lit top edge, shaded bottom | `emphasized=True` switches the rim from bronze to blue — that is the focus state, not decoration |
| `draw_button(surface, rect, label, font, hovered, tier)` | The standard button | Three tiers, below |
| `draw_profile_frame` (in `gameplay_hud.py`) | The bronze portrait frame | Shared by the HUD card and the profile screen so tapping the card *expands* it rather than opening a different-looking window |

**Button tiers** — a menu where every row looks the same gives the eye
nothing to land on:

| Tier | Look | Use for |
|---|---|---|
| `TIER_PRIMARY` | Gold gradient fill, always glowing, sits 3px proud | The one action the screen exists for |
| `TIER_SECONDARY` (default) | Navy fill, bronze rim, blue rim on hover | Everything ordinary |
| `TIER_TERTIARY` | Navy fill, dim rim, dim label | Exits and destructive actions that should recede |

**Geometry constants in use:** panel radius 8 (7 for buttons), 2px rims on
panels, 3px on buttons, 8px inset from panel edge to inner face, 4px drop
shadow. Spacing between stacked HUD panels is 8px; screen margin is
`min(width, height) * 0.016`.

---

## 5. Per-screen audit

| File | Local colors | Verdict |
|---|---|---|
| `ui/gameplay_hud.py` | 6 | **Fine.** Portrait bronzes, torch amber, heal green — gameplay signals and art, not generic UI. Amber and green are worth promoting to tokens if anything else ever signals "warmth" or "healing". |
| `ui/stage_panel.py` | 4 | **Fine.** Three are vine leaf greens — plaque artwork. `TEXT_DONE` should become the shared success token. |
| `ui/chart.py` | 10 | **Intentional exception.** Paper and ink. |
| `ui/gear_icon.py` | 13 | **Intentional exception.** One icon's own artwork. |
| `screens/world_map.py` | 4 | **Intentional exception.** Scorch and grime for the paper's ageing. |
| `ui/night_lighting.py`, `ui/ambient_particles.py` | 1 each | **Fine.** Effect colors. |
| `screens/stage_info.py` | 2 | **Minor.** `CARD_BG` and `DIVIDER` belong in the modal group. |
| `screens/how_to_play.py` | 8 | **Migrate.** Redefines the whole stone family at different values, plus its own white, gold and blue. Every value maps to an existing or proposed token. |
| `screens/topic_found.py` | 9 | **Migrate.** Pure duplicate of the modal palette. |
| `screens/topic_lesson.py` | 0 | **Migrated** 5 Sep. Needed one new token, `modal_danger`. |
| `screens/inventory.py` | 0 | **Migrated** 5 Sep. Needed one new token, `modal_slot`. |
| `screens/game_over.py` | 10 | **Partly migrate.** Blood reds and rivets are scene art — keep. Its stone family and blue glow are duplicates. |
| `screens/main_menu.py` | 10 | **Partly migrate.** Greens are menu-specific accents; the stone family, white and blue glow are duplicates. |
| `screens/tutorial.py` | 2 | **Migrated** 5 Sep, and no longer imports colours from another screen. The two left are scene art: the green Begin accent and the practice-room floor. |

**Nothing in `src/data/` should ever appear in this table.** Data modules
do not import pygame and do not know what anything looks like.

---

## 6. Migration order

1. ~~`how_to_play.py` and `topic_found.py`~~ — **done**, as the worked
   example for this guide. Both now hold zero color literals and render
   pixel-for-pixel identically to before. See
   `docs/style-guide-migration.md`.
2. ~~`topic_lesson.py`, `inventory.py`~~ — **done** 5 Sep.
3. ~~`tutorial.py`~~ — **done** 5 Sep; it now reads the palette directly.
4. `game_over.py`, `main_menu.py` — partly done: both now take the hover
   blue (and Game Over the dim grey) from tokens. Their stone families and
   scene art remain.

Do these one file at a time, with a screenshot before and after. There is
no test that can tell you a panel looks wrong.

---

## 7. Decisions waiting on sign-off

- [x] Add the `modal_*` values to `theme.UI_COLORS` and accept that
      CodeBreak has two panel styles. **Done** — 13 tokens, taken from the
      values screens were already drawing, so nothing changed on screen.
- [x] Change `blue_bright` to 80, 180, 255 to match what three screens
      already draw. **Done** 5 Sep.
- [ ] Keep two golds, named by context.
- [x] Collapse the dim greys into one. **Done** 5 Sep, at 170, 175, 190.
- [ ] Decide whether torch amber and heal green become shared tokens or
      stay local to the HUD.
