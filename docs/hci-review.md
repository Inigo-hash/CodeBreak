# UI and HCI review — 23 October 2026

This is a code, automated interaction, and rendered-layout review, not a user study or accessibility certification.

## Improvements delivered

| Usability concern | Change |
| --- | --- |
| User control during a slow tutor request | Use guide button / Ctrl+G ends waiting and immediately shows labelled saved help. Subsequent questions use saved help while the old worker finishes; no additional concurrent worker is launched in that session. Late answers are discarded. |
| Accurate status | Connecting status lives in the active UI, not permanently inside a chat message. It disappears when waiting ends. |
| Clear recovery | Empty input and rejected submissions provide feedback. Draft text remains intact. |
| Discoverability | Visible Back button, character counter, keyboard history scrolling, and guide shortcut. |
| Large text | Tutor input height grows with font size; heading, controls and footer use bounded text fitting. |
| Recognition of intent | Continuing a saved game resolves to Continue Game instructions instead of Python continue. |
| Keyboard learning flow | Lessons scroll with arrows, Page Up/Down and Home/End; Enter opens and confirms challenges; Escape cancels confirmation. Visible lesson scrollbar and shortcut hint. |
| Challenge selection | Up/Down and Tab/Shift+Tab select challenges; Enter opens. Initial focus selects the first unfinished challenge, with a visible outline. Passed challenges remain labelled as practice. |
| Consistency | Settings support Tab/Shift+Tab across rows; learning progress supports Tab to switch views. |

## Evidence

175 unique tests passed in separate processes:

- Tutor client 9; guide 7; backup/recovery 17; chat 8; server 28.
- HCI navigation 6; text-layout regressions 11; menu layout 6.
- Configurable progress 6; Stage 2 Dining 23.
- Button design 6; inventory design 3; save slots 11.
- Character selection 7; stage selection 16; editor feedback 11.

31 offline reference checks passed. A 10-second headless startup stayed open (expected timeout 124). `git diff --check` passed. Relevant tests were repeated after final adjustments without adding those repeats to the total. Two initially attempted test names had no matching modules and are not counted.

Rendered and inspected tutor at 960x640 and 640x480 with enlarged text, plus Lists lesson and challenge selection at 960x640. Existing layout regressions cover menus, tutor helper, practice cards, controls, manual, atlas and tutorial at larger text sizes. This does not establish that every screen fits every resolution. Image-profile warnings and an httpx dependency deprecation warning did not fail the tests.

## Remaining limitations and next learner test

- Pygame controls have no screen-reader semantics. Keyboard improvements do not constitute full accessibility.
- Some screens still use mouse-specific affordances, including settings help tooltips and inventory drag-and-drop. Audit those workflows with keyboard-only players before claiming universal keyboard access.
- Font fitting can make labels smaller in cramped windows. Prefer the normal game resolution for a demonstration; inspect readability on the actual projector.
- A saved reference is not a generative AI. Unknown questions may receive an honest help menu. The online provider and hosting service can still be unavailable.
- Use guide stops waiting in the interface; it does not cancel an HTTP request already sent or recover its quota. One worker per chat session remains bounded until the request finishes.
- Chat conversations are still scoped to an opened modal, not persisted across closing and reopening it.

Rehearse with a first-time learner: continue an existing save, find objectives, read Lists using only the keyboard, open the unfinished challenge, ask the tutor during a simulated outage, choose Use guide, ask another question, then save and leave. Observe hesitation, wrong clicks, task completion and whether the learner can distinguish saved help from live AI. Do not claim measured usability improvements until this is done.
