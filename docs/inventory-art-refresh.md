# Inventory artwork refresh

Created with the built-in imagegen tool and copied into the project:

- `assets/images/ui/inventory_frame.png`: fantasy leather, timber and bronze
  frame with ivy and a satchel. Labels, slots and highlights remain live UI.
- `assets/images/ui/rail_learning.png`: three transparent illustrated plaques
  for Code Practice, Progress and Topic Guidance. Runtime source rectangles
  isolate the plaques; labels and hotkeys remain live UI.

Final inventory prompt: Generate a game UI asset, not a screenshot. Single
tall rectangular fantasy adventurer inventory panel on a transparent background,
portrait 3:4 composition. Painterly crisp 2D fantasy art, deep charcoal slate
empty inset, warm brown leather and carved dark timber outer frame, bronze/gold
trim, small ivy clusters, leather satchel at top center. Central 80 percent empty
dark navy for runtime slots. No text, letters, grid, icons or characters in the
center. Orthographic front view, transparent exterior, no scenery.

Final rail prompt: Transparent sprite sheet of three fantasy RPG horizontal
plaques stacked vertically. Slate and bronze with cyan code rune and quill;
carved wood with compass and rolled map; charcoal slate with book and purple
crystal. Crisp painterly outlines, ivy corners, blank dark centers for runtime
white text, transparent exterior. No text, letters, words or surrounding UI.

The inventory retains twenty bag slots and five hotbar slots. Slots adapt to
window height; a code-drawn sword icon replaces the letter placeholder.
Regression checks cover slot geometry, hit testing, drag-to-equip, illustrated
rail click targets, and Progress / Topic Guidance keyboard shortcuts.
