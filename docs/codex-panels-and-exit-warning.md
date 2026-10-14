# Illustrated panels and unsaved exit protection

Built-in imagegen generated `assets/images/ui/codex_frame.png`, a reusable
bronze, dark oak and slate frame with restrained ivy corners. The runtime
renderer caches scaled versions. Large shared panels and Stage Information
use the frame; bestiary cards use matching art, and active tabs are gold.
Titles and tab labels remain runtime text with bounded sizing.

Final generation prompt: Game UI asset only: wide landscape fantasy RPG codex
menu frame, 4:3 aspect, transparent outside. Dark slate blue flat empty central
panel, very thin carved bronze and dark oak rim less than 2 percent of image
width, intricate modest engraved corner fittings, small ivy accents confined
to outer corners, refined hand painted 2D outlined game art matching fantasy
illustrated wood and stone game menu plaques. Use aged bronze and restrained
warm gold highlights with dark charcoal stone. Leave entire central 94 percent
a clean near-uniform very dark navy slate surface, absolutely no text, icons,
lettering, symbols or content inside. No book or object hanging over header.
Clean rectangular shape orthographic view. Designed as a reusable backdrop
for readable white game text and tab controls. No environment, no characters,
no slots or buttons.

During gameplay, window close / Alt+F4 is intercepted even in nested menus.
Return to Main Menu uses the same progress comparison and confirmation:

- Save & Leave writes the current state before leaving.
- Leave Without Saving requires an explicit choice.
- Keep Playing is the default; Escape also cancels.
- Save errors stay in the dialog. No-slot sessions cannot choose Save & Leave.

Already-saved progress does not prompt. OS process termination, power loss,
and forcibly ending the process cannot show a Pygame warning.
