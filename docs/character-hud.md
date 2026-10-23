# Explorer portraits and character HUD

The top-left HUD now uses a compact ink-blue card, a dedicated portrait for each
explorer, labelled lives, and health/energy values above full-width bars. The
stage card aligns to it; bonus time sits with stage progress. Both cards use
measured text rows and keep clear of the minimap at supported small sizes.
Clicking the character card opens the matching expanded profile.

## Artwork

Created with the built-in image-generation tool (not the CLI). These are
generated illustrations with an ink-and-gouache aesthetic, not a claim of
human-painted provenance. The male portrait keeps the salakot, khaki travel
clothes and red scarf; the female portrait is a dedicated illustration rather
than an enlarged walking-sprite crop. Both use the same matte pigment palette
and a simple teal backdrop. The original framed asset and walking sprites
are retained.

Project assets:

- `assets/images/portraits/explorer_man.webp`
- `assets/images/portraits/explorer_woman.webp`

Each source is 1254 x 1254 pixels. The project copies are WebP quality 90
encodings (about 180 KB each), with composition unchanged. UI scaling keeps
aspect ratio and caches the fitted tiles; portraits are not resized on every
frame. `src/data/characters.py` selects the image by saved character ID.

## Generation prompts

### Male explorer

Use case: stylized-concept. Asset type: square portrait illustration for the small top-left character HUD in CodeBreak, a Philippine folklore adventure RPG. Style: expressive ink-and-gouache illustration on subtly textured paper, like a carefully drawn illustrated travel journal. Visible imperfect brush edges, economical dark ink lines, flat matte pigment shapes, natural facial asymmetry and ordinary human features. Gentle and aesthetically refined. No glossy rendering, no faux pixel grid, no photorealism, no 3D, no cinematic bloom, no hyper-detailed AI fantasy treatment, no anime doll eyes. Composition: single head-and-shoulders portrait with a large readable face, nearly front-facing with a slight turn to the viewer's right, relaxed attentive expression. Full top of head and any headwear visible with a small margin; shoulders cropped at lower edge. Simple full-bleed muted midnight teal painted backdrop. Warm tan skin, dark umber ink, muted ochre clothing, warm terracotta red scarf. Strong silhouette and legible face when reduced to 96 pixels. Square image, artwork only, no ornamental frame, no UI, no text, no watermark, no symbols. Subject: one young adult Filipino male explorer with short tousled black hair, brown eyes, a modest woven salakot straw hat, simple worn khaki travel shirt and backpack straps. Hat has a broad simple curved silhouette but must not cover his eyes. Friendly thoughtful expression, lightly sun-weathered skin. Hand-painted character portrait, not a character sheet.

### Female explorer

Use case: stylized-concept. Asset type: square portrait illustration for the small top-left character HUD in CodeBreak, a Philippine folklore adventure RPG. Style: expressive ink-and-gouache illustration on subtly textured paper, like a carefully drawn illustrated travel journal. Visible imperfect brush edges, economical dark ink lines, flat matte pigment shapes, natural facial asymmetry and ordinary human features. Gentle and aesthetically refined. No glossy rendering, no faux pixel grid, no photorealism, no 3D, no cinematic bloom, no hyper-detailed AI fantasy treatment, no anime doll eyes. Composition: single head-and-shoulders portrait with a large readable face, nearly front-facing with a slight turn to the viewer's right, relaxed attentive expression. Full top of head and any headwear visible with a small margin; shoulders cropped at lower edge. Simple full-bleed muted midnight teal painted backdrop. Warm tan skin, dark umber ink, muted ochre clothing, warm terracotta red scarf. Strong silhouette and legible face when reduced to 96 pixels. Square image, artwork only, no ornamental frame, no UI, no text, no watermark, no symbols. Subject: one young adult Filipino female explorer with dark brown shoulder-length slightly wavy hair, a few loose strands, brown eyes, a practical sleeveless khaki travel top, backpack straps and a small terracotta scarf at the neck. No hat. Friendly quietly confident expression, lightly sun-weathered skin. Practical adventurer, natural proportions, no glamour makeup. Hand-painted character portrait, not a character sheet.

## Verification

34 tests pass across `test_character_hud.py`, `test_character_selection.py`,
`test_room_combat_regressions.py`, `test_text_layout_regressions.py` and
`test_hci_navigation.py`, each in its own process. Coverage includes both
portraits, legacy character IDs, cached images, 640x480 through 2560x1440,
small, normal and large text, text bounds, minimap clearance, clamped/unknown stats,
healing/energy highlights, keyboard/mouse dismissal and character persistence.

`python tools/check_character_hud.py` captures actual Pygame gameplay in the
Castle for both characters and opens each profile by clicking its real HUD
card. It uses in-memory fixtures and no save slot. Four frames were visually
inspected; no full campaign playthrough was performed for this UI change.
The committed gameplay preview is `docs/character-hud-preview.png`.

