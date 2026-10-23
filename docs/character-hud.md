# Explorer HUD: pixel-art revision

The active character UI uses pixel-art-style portraits, warm charcoal plates
with clipped corners and thin bronze edges, and compact HP/energy gauges with
values inside their tracks. Lives sit below the gauges. The portrait no longer
has a separate PROFILE caption; its chevron still opens the expanded profile.
Stage progress uses a smaller heading and groups its bonus time with the stage.

## Artwork and integration

The two portraits were created with the built-in image-generation tool, not
the CLI. They are generated pixel-art-style illustrations, not a claim of
human-pixelled artwork. Both retain the salakot/travel clothing or dark hair,
red scarf and backpack details associated with the existing explorers.

Active project files:

- `assets/images/portraits/explorer_man_pixel.webp`
- `assets/images/portraits/explorer_woman_pixel.webp`

The original 1254 x 1254 outputs were encoded as WebP quality 95 for the game.
No composition or character edits were made during encoding. The renderer
uses nearest-neighbor scaling and caches portrait tiles. The preceding
painted portraits remain in the repository but are not selected by character
data. Walking sprites, character IDs, saves and gameplay rules are unchanged.

## Generation prompts

### Male explorer

Use case: stylized-concept. Asset: a square character bust portrait for the tiny HUD of a 2D pixel-art Philippine folklore adventure game. Make authentic, deliberately simplified 16-bit RPG pixel art, as if hand-pixeled on a 96 by 96 grid and enlarged with nearest-neighbor. Every edge is a staircase of clean square pixels. Use small, coherent pixel clusters and only about 24 flat colors. Two or three shading steps per material, no intermediate soft shading. A strong, appealing face and crisp silhouette are crucial. Absolutely no photographic facial details, no brush or paper texture, no painterly rendering, no smooth gradients, no anti-aliased contours, no realistic skin, no 3D, no cinematic light, no pseudo-pixelated photograph. Head and upper chest fully visible, straight posture, slight three-quarter turn toward the viewer's right. A small restrained smile and natural modest eyes; avoid large anime eyes. Adult Filipino explorer with warm brown skin. Clean flat dark charcoal-brown background. No frame, no border, no text, no symbols, no watermark. Keep the entire head and any hat inside the square, with generous 8% clearance above the head and both sides. Use muted tan, umber, dull terracotta and warm cream; simple shapes suited to the small pixel game sprites. One male explorer in his early twenties, short slightly messy dark hair, simple woven salakot hat, tan travel shirt, dull red neck scarf and dark backpack straps. Hat is a simple recognizable form, without thousands of woven details. Pixel faces should feel like a charming original game character, not a model or celebrity.

### Female explorer

Use case: stylized-concept. Asset: a square character bust portrait for the tiny HUD of a 2D pixel-art Philippine folklore adventure game. Make authentic, deliberately simplified 16-bit RPG pixel art, as if hand-pixeled on a 96 by 96 grid and enlarged with nearest-neighbor. Every edge is a staircase of clean square pixels. Use small, coherent pixel clusters and only about 24 flat colors. Two or three shading steps per material, no intermediate soft shading. A strong, appealing face and crisp silhouette are crucial. Absolutely no photographic facial details, no brush or paper texture, no painterly rendering, no smooth gradients, no anti-aliased contours, no realistic skin, no 3D, no cinematic light, no pseudo-pixelated photograph. Head and upper chest fully visible, straight posture, slight three-quarter turn toward the viewer's right. A small restrained smile and natural modest eyes; avoid large anime eyes. Adult Filipino explorer with warm brown skin. Clean flat dark charcoal-brown background. No frame, no border, no text, no symbols, no watermark. Keep the entire head and any hat inside the square, with generous 8% clearance above the head and both sides. Use muted tan, umber, dull terracotta and warm cream; simple shapes suited to the small pixel game sprites. One female explorer in her early twenties, dark brown shoulder-length hair partly tied behind her head, simple tan sleeveless travel shirt, dull red neck scarf and dark backpack straps. No hat or makeup. Pixel faces should feel like a charming original game character, not a model or celebrity.

## Verification

34 tests pass across character HUD, selection, room combat regressions, text
layout and HCI navigation, with each module run in a separate process. Layout
coverage spans 640x480 through 2560x1440 and font sizes 12, 20 and 28. Checks
cover rendered text bounds, separate resource/life rows, minimap clearance,
unknown and clamped stats, healing/energy highlights and portrait caches.

`python tools/check_character_hud.py --output-dir /tmp/character-hud-v2`
captures actual Castle gameplay for both explorers, then opens each expanded
profile using the real card click. No save slot is used. Four captured frames
were inspected. `docs/character-hud-preview.png` is the updated gameplay view.
A full campaign playthrough was not performed for this visual revision.
