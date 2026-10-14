# Button hierarchy and interaction update

Use one prominent action per decision. Preserve the game's stone, bronze,
and gold visual identity while making actions understandable before hover.

| Treatment | Meaning | Examples |
| --- | --- | --- |
| Gold fill, dark text | Recommended next step | Next, Start Challenge, Start Assessment, Resume, password Continue |
| Green fill, light text | Advance after success | Challenge Continue, Next Problem |
| Navy fill and border | Alternative or navigation | Back, Cancel, Store in Bag, Review Code |
| Red fill and explicit label | Irreversible change | Delete Save, Replace Save |
| Muted fill, no hover glow | Temporarily unavailable | Password Continue during lockout |
| Additional light outline | Keyboard selection | Boss-dialog Tab / arrow navigation |

Color accompanies explicit labels and borders. Keep the primary button visible
at rest; do not require hover to discover which action advances the flow.
Continue Game takes priority over Start New Game when a save exists.
Challenge selection highlights the next incomplete challenge; completed rows
retain their Passed / Practice labels.

Labels fit their actual button rectangles. Shared semantic green/red fills use
light text; gold uses dark text. The editor's Submit label selects light or dark
text for the strongest contrast with the active editor theme's fill.

This pass covers the shared renderer, start-game and password screens,
introductory guide, lessons, topic discovery and challenge selection,
assessment briefing, pause actions, boss dialogs, editor action widgets,
and submission feedback. Map art, gameplay sprites and code syntax palettes
retain their own visual systems.

Boss dialogs support Tab / Left / Right to select, Enter to confirm, and Escape
to take the secondary option. Existing shortcuts and hit rectangles are retained.
Password lockout remains enforced by its event handler as well as its appearance.
