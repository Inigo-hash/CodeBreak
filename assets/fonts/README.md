# Fonts

Two families, both bundled so the game renders identically on a machine that
has neither installed. Everything is loaded through `src/ui/theme.py` — no
screen should call `pygame.font.SysFont` or point at a `.ttf` directly.

| File | Role |
| --- | --- |
| `Exo2-Regular.ttf` | `ui_font(size)` — menu chrome, tips, small labels |
| `Exo2-SemiBold.ttf` | `ui_font(size, bold=True)`, `title_font(size, bold=False)` — sub-headings, tabs |
| `Exo2-Bold.ttf` | `title_font(size)` — titles and button labels |
| `JetBrainsMonoNL-Regular.ttf` | `body_font(size)` — body copy, code, output |
| `JetBrainsMonoNL-Bold.ttf` | `body_font(size, bold=True)` — emphasised body copy |

Exo 2 was picked to match the blocky sans lettering in
`assets/images/logos/codebreakLogo.png`. JetBrains Mono is the **NL**
(no-ligature) cut on purpose: the standard cut draws `==` and `!=` as single
arrow-like glyphs, which is exactly wrong for a game that teaches Python
operators.

## Sources and licence

Both families are SIL Open Font License 1.1 — see `OFL.txt`.

- Exo 2 — <https://fonts.google.com/specimen/Exo+2>
- JetBrains Mono — <https://github.com/JetBrains/JetBrainsMono> (v2.304)
