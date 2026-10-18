# Text layout audit

Checked 51 rendered UI states with `tools/layout_audit.py`, covering menus,
settings, character selection, stage information, lessons, challenges, practice,
tutorial dialogue and confirmations, inventory, tutor, editor and feedback,
boss dialogs, gates, defeat, gameplay HUD, and maps.

Capture matrix: 1280x720, 1920x1080, and 1920x1536 at font size 28;
2560x1080 at font size 25. Review included compact, tall, and ultrawide layouts.
The captures exercise representative content, not every possible player state.

Changes reserve separate rectangles for labels, icons, descriptions, buttons,
and decorative borders. Long controls scroll, tutorial dialogue paginates,
map labels avoid each other, and bounded text fits its available space. Empty
text surfaces are handled safely before scaling.

Validation: 344 tests across 39 independently executed test modules passed,
including ten text-layout regressions. The gate click regression was updated
for the relocated button and rerun successfully. `git diff --check` passed.

Reproduce a capture set from the repository root:

```sh
python tools/layout_audit.py --output /tmp/codebreak-layout --size 1280x720 --font-size 28
```
