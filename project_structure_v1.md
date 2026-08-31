> **Outdated.** This is a snapshot of an earlier layout, kept for history.
> It predates `src/systems/`, `src/data/stages.py`, `tests/`, the learning
> sandbox, and the stage/boss systems. See `CLAUDE.md` in the repo root for
> the current structure.

This file is a merged representation of a subset of the codebase, containing files not matching ignore patterns, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching these patterns are excluded: assets/**
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
````
src/
  entities/
    enemy.py
    player.py
  screens/
    game.py
    main_menu.py
    settings.py
    sprites.py
    tutorial.py
  ui/
    button.py
    code_editor.py
    hud.py
  utils/
    constants.py
    helpers.py
  settings_state.py
.gitignore
AI_TestCase_Generation_Process.md
main.py
README.md
requirements.txt
````

# Files

## File: src/entities/enemy.py
````python

````

## File: src/screens/sprites.py
````python

````

## File: src/screens/tutorial.py
````python
import pygame
import sys
from src.ui.button import Button

def tutorial_screen(screen):
    BLUE = (70, 130, 180)
    LIGHT_BLUE = (100, 160, 210)
    GRAY = (50, 50, 50)
    WHITE = (255, 255, 255)
    
    back_button = Button(50, 50, 200, 60, "Back", BLUE, LIGHT_BLUE)
    
    title_font = pygame.font.Font(None, 80)
    clock = pygame.time.Clock()
    running = True
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        back_button.check_hover(mouse_pos)
        
        if back_button.is_clicked(mouse_pos, mouse_pressed):
            return  # Go back to main menu
        
        screen.fill(GRAY)
        
        title = title_font.render("Tutorial (Coming Soon)", True, WHITE)
        screen.blit(title, (screen.get_width()//2 - title.get_width()//2, 200))
        
        back_button.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
````

## File: src/ui/button.py
````python
import pygame

WHITE = (255, 255, 255)

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pygame.font.Font(None, 50)  # ✅ Create font here instead
    
    def draw(self, surface):
        current_color = self.hover_color if self.is_hovered else self.color
        
        pygame.draw.rect(surface, current_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, 3, border_radius=10)
        
        text_surface = self.font.render(self.text, True, WHITE)  # ✅ Use self.font
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]
````

## File: src/ui/code_editor.py
````python

````

## File: src/ui/hud.py
````python

````

## File: src/utils/constants.py
````python
# Screen settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
LIGHT_GRAY = (100, 100, 100)
BLUE = (70, 130, 180)
LIGHT_BLUE = (100, 160, 210)
GREEN = (50, 200, 50)
RED = (200, 50, 50)

# Game settings
FPS = 60
````

## File: src/utils/helpers.py
````python

````

## File: src/settings_state.py
````python
settings_state = {
    "music_vol": 0.55,
    "sfx_vol": 0.45,
    "themes": ["GREEN", "BLUE", "ORANGE", "PURPLE"],
    "theme_index": 0,
    "dragging_music": False,
    "dragging_sfx": False,
}
````

## File: AI_TestCase_Generation_Process.md
````markdown
# AI CLI Process: Auto-Generate Test Case Spreadsheets

## How this works
You (the tester) give the AI **one input**: the component name (e.g. "Main Menu").
The AI never asks what to test — it only asks for the component name if missing.
Everything else below, the AI does on its own.

---

## STEP 1 — Take the component name
Input: a single component (e.g. `Main Menu`, `Inventory`, `Settings`).
Use this to build the Test Case ID prefix — first letters of the component, e.g.:
- Main Menu → `MM`
- Settings → `SNG`
- Inventory → `INV`

---

## STEP 2 — List all scenarios for that component
The AI brainstorms every distinct thing a user can DO in that component, and lists each as its own **scenario**. One scenario = one test case block = one sheet in the workbook.

Example, component = "Main Menu":
1. Starting a new game
2. Loading a saved game
3. Opening Settings (volume, sfx, theme)
4. Quitting the game
5. Navigating menu with keyboard vs mouse
6. Clicking outside a menu popup (does it close?)
7. Rapid double-clicking a button (does it break?)

Rule: include both normal (happy path) scenarios AND edge cases (invalid input, spam clicking, empty state, etc).

---

## STEP 3 — Build each scenario into a full test case block
For every scenario from Step 2, fill out this exact structure (matches your existing template):

| Field | Rule |
|---|---|
| Test Case ID | `{PREFIX}_{number}` e.g. `MM_001`, `MM_002` (increment per scenario) |
| Test Case Description | One line: what part of the component this test covers |
| Created By | Leave blank or use placeholder — tester fills in |
| Reviewed By | Leave blank |
| Version | `1.0` |
| QA Tester's Log | Leave blank |
| Tester's Name | Leave blank |
| Date Tested | Leave blank |
| Test Case (Pass/Fail/Not Executed) | `Not Executed` (default) |
| Prerequisites | Tools/state needed before testing (e.g. "pygame package", "save file exists") |
| Test Data | Inputs needed (e.g. "Mouse click", "Keyboard arrow keys", sample username/password) |
| Test Scenario | Short sentence describing the scenario (from Step 2) |

---

## STEP 4 — Write the steps + expected results
For each scenario, break it into individual steps. Each step needs:
- **Step No.** — sequential number
- **Step Details** — exact action to perform (be specific: which button, which click type, which direction)
- **Expected Results** — what should visibly happen if it works correctly
- **Actual Results** — leave blank (tester fills in after running)
- **Pass/Fail/Not Executed/Suspended** — default to `Not Executed`

Rule: one action per step. Don't combine two actions into one row.

---

## STEP 5 — Fill the spreadsheet using this exact cell map
Each test case gets its own sheet. Use this layout (matches `Settings_Testing.xlsx`):

| Cell | Content |
|---|---|
| A1 | `Test Case ID` |
| C1 | the ID (e.g. `MM_001`) |
| D1 | `Test Case Description` |
| F1 | description text |
| A2 | `Created By` |
| D2 | `Reviewed By` |
| H2 | `Version` / J2 = `1.0` |
| A4 | `QA Tester's Log` |
| A6 | `Tester's Name` / D6 `Date Tested` / H6 `Test Case (Pass/Fail/Not Executed)` |
| A8 | `S No.` / B8 `Prerequisites:` / G8 `S No.` / H8 `Test Data` |
| A9:A12 | 1–4 (prerequisite row numbers) / B9:B12 prerequisite text |
| G9:G12 | 1–4 (test data row numbers) / H9:H12 test data text |
| A14 | `Test Scenario` / B14 scenario sentence |
| A16 | `Step No.` / B16 `Step Details` / D16 `Expected Results` / F16 `Actual Results` / I16 `Pass / Fail / Not executed / Suspended` |
| A18+ | step rows: step number, step detail, expected result, (actual left blank), `Not Executed` |

Sheet name = the Test Case ID (e.g. `MM_001`).

---

## STEP 6 — Save and hand back
- One `.xlsx` file, one sheet per scenario, named after the component (e.g. `MainMenu_Testing.xlsx`).
- Recalculate/save with no formula errors.
- Tell the tester how many scenarios/test cases were generated.

---

## Example prompt to give the AI CLI
```
Using the process in AI_TestCase_Generation_Process.md, generate test cases 
for the component: "Main Menu". Base the format on Settings_Testing.xlsx.
```

That's the whole loop — you only ever type the component name.
````

## File: requirements.txt
````

````

## File: .gitignore
````
__pycache__/
*.pyc
__pycache__/
*.pyc
````

## File: README.md
````markdown
# CodeBreak
A Game-Based Learning System for Teaching Python Programming Through Combat Challenges 

What Each Folder Is For
assets/ — all your game resources

images/ — sprites, backgrounds, UI elements
sounds/ — background music and sound effects
fonts/ — custom fonts for text

src/ — all your Python code organized by purpose

screens/ — different game screens (menu, settings, game levels)
entities/ — game objects (player, enemies)
ui/ — UI components (buttons, code editor, HUD)
utils/ — helper functions and constants

main.py — the entry point that runs everything
````

## File: src/screens/settings.py
````python
import pygame
import sys
from src.settings_state import settings_state as _settings_state

def settings_screen(screen):
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

    # Colors
    STONE_DARK = (28, 30, 38)
    STONE_MID = (42, 46, 58)
    STONE_LIGHT = (62, 68, 82)
    BLUE_GLOW = (80, 180, 255)
    YELLOW_GLOW = (255, 220, 120)
    GREEN_TIP = (60, 255, 140)
    WHITE = (255, 255, 255)
    METAL_FRAME = (90, 94, 110)

    # Fonts
    font_title = pygame.font.SysFont("consolas", 32, bold=True)
    font_label = pygame.font.SysFont("consolas", 18)
    font_btn   = pygame.font.SysFont("consolas", 22, bold=True)

    # State
    themes      = ["GREEN", "BLUE", "ORANGE", "PURPLE"]
    theme_index = 0
    dragging_music = False
    dragging_sfx   = False

    # Panel rect
    pr = pygame.Rect(SCREEN_WIDTH // 2 - 190, SCREEN_HEIGHT // 2 - 240, 380, 480)

    # Slider rects
    music_bar = pygame.Rect(pr.left + 28, pr.top + 160, pr.width - 56, 14)
    sfx_bar   = pygame.Rect(pr.left + 28, pr.top + 240, pr.width - 56, 14)

    # Arrow rects
    arrow_y     = pr.top + 320
    left_arrow  = pygame.Rect(pr.left + 60,   arrow_y, 40, 28)
    right_arrow = pygame.Rect(pr.right - 100, arrow_y, 40, 28)

    # Back button rect
    back_r = pygame.Rect(pr.centerx - 70, pr.bottom - 56, 140, 36)

    clock = pygame.time.Clock()
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if music_bar.collidepoint(event.pos):
                    dragging_music = True
                if sfx_bar.collidepoint(event.pos):
                    dragging_sfx = True
                if left_arrow.collidepoint(event.pos):
                    theme_index = (theme_index - 1) % len(themes)
                if right_arrow.collidepoint(event.pos):
                    theme_index = (theme_index + 1) % len(themes)
                if back_r.collidepoint(event.pos):
                    return  # back to main menu

            if event.type == pygame.MOUSEBUTTONUP:
                dragging_music = False
                dragging_sfx   = False

            if event.type == pygame.MOUSEMOTION:
                if dragging_music:
                    _settings_state["music_vol"] = max(0.0, min(1.0, (event.pos[0] - music_bar.left) / music_bar.width))
                    pygame.mixer.music.set_volume(_settings_state["music_vol"])
                if dragging_sfx:
                    _settings_state["sfx_vol"] = max(0.0, min(1.0, (event.pos[0] - sfx_bar.left) / sfx_bar.width))

        # --- Draw ---
        # Dim overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # Panel background
        pygame.draw.rect(screen, (36, 38, 48), pr)
        pygame.draw.rect(screen, METAL_FRAME, pr, 4)
        pygame.draw.rect(screen, (26, 28, 36), pr.inflate(-24, -24))

        # Title
        title = font_title.render("SETTINGS", True, WHITE)
        screen.blit(title, (pr.centerx - title.get_width() // 2, pr.top + 16))

        # TEXT SPEED
        screen.blit(font_label.render("TEXT SPEED", True, (200, 200, 210)), (pr.left + 28, pr.top + 70))
        screen.blit(font_label.render("SLOW    NORMAL    INSTANT", True, (160, 170, 190)), (pr.left + 28, pr.top + 96))

        # MUSIC slider
        screen.blit(font_label.render("MUSIC", True, (200, 200, 210)), (pr.left + 28, pr.top + 140))
        pygame.draw.rect(screen, (30, 32, 40), music_bar, border_radius=4)
        mx = music_bar.left + int((music_bar.width - 16) * _settings_state["music_vol"])
        pygame.draw.rect(screen, YELLOW_GLOW, (mx, music_bar.top - 2, 16, 18), border_radius=3)

        # SFX slider
        screen.blit(font_label.render("SFX", True, (200, 200, 210)), (pr.left + 28, pr.top + 220))
        pygame.draw.rect(screen, (30, 32, 40), sfx_bar, border_radius=4)
        sx = sfx_bar.left + int((sfx_bar.width - 16) * _settings_state["sfx_vol"])
        pygame.draw.rect(screen, YELLOW_GLOW, (sx, sfx_bar.top - 2, 16, 18), border_radius=3)

        # SYNTAX THEME
        screen.blit(font_label.render("SYNTAX THEME", True, (200, 200, 210)), (pr.left + 28, pr.top + 300))

        # Left arrow
        pygame.draw.rect(screen, (50, 55, 70), left_arrow, border_radius=4)
        tri_l = [
            (left_arrow.right - 8,  left_arrow.top + 6),
            (left_arrow.right - 8,  left_arrow.bottom - 6),
            (left_arrow.left + 6,   left_arrow.centery),
        ]
        pygame.draw.polygon(screen, BLUE_GLOW, tri_l)

        # Right arrow
        pygame.draw.rect(screen, (50, 55, 70), right_arrow, border_radius=4)
        tri_r = [
            (right_arrow.left + 8,  right_arrow.top + 6),
            (right_arrow.left + 8,  right_arrow.bottom - 6),
            (right_arrow.right - 6, right_arrow.centery),
        ]
        pygame.draw.polygon(screen, BLUE_GLOW, tri_r)

        # Theme label
        theme_colors = {
            "GREEN":  (60, 255, 140),
            "BLUE":   (80, 180, 255),
            "ORANGE": (255, 160, 60),
            "PURPLE": (180, 100, 255),
        }
        current_theme = themes[theme_index]
        th = font_btn.render(current_theme, True, theme_colors[current_theme])
        screen.blit(th, (pr.centerx - th.get_width() // 2, arrow_y + 4))

        # Back button
        pygame.draw.rect(screen, STONE_MID, back_r, border_radius=4)
        pygame.draw.rect(screen, STONE_LIGHT, back_r, 2, border_radius=4)
        bt = font_btn.render("BACK", True, WHITE)
        screen.blit(bt, (back_r.centerx - bt.get_width() // 2, back_r.centery - bt.get_height() // 2))

        pygame.display.flip()
        clock.tick(60)
````

## File: src/entities/player.py
````python
import pygame


class MainCharacter():
    def __init__(self, screen, map_width, map_height):
        self.screen = screen

        # 8 frames each
        idle_right_frames = [pygame.image.load(f"assets/images/frames/main_character/idle/idle_right/frame_{i}.png").convert_alpha() for i in range(8)]
        self.idle_right_frames = [pygame.transform.scale(f, (f.get_width() // 5, f.get_height() // 5)) for f in idle_right_frames]

        walking_left_frames = [pygame.image.load(f"assets/images/frames/main_character/walking/walking_left/frame_{i}.png").convert_alpha() for i in range(8)]
        self.walking_left_frames = [pygame.transform.scale(f, (f.get_width() // 5, f.get_height() // 5)) for f in walking_left_frames]

        walking_right_frames = [pygame.image.load(f"assets/images/frames/main_character/walking/walking_right/frame_{i}.png").convert_alpha() for i in range(8)]
        self.walking_right_frames = [pygame.transform.scale(f, (f.get_width() // 5, f.get_height() // 5)) for f in walking_right_frames]

        walking_forward_frames = [pygame.image.load(f"assets/images/frames/main_character/walking/walking_forward/frame_{i}.png").convert_alpha() for i in range(8)]
        self.walking_forward_frames = [pygame.transform.scale(f, (f.get_width() // 5, f.get_height() // 5)) for f in walking_forward_frames]


        target_size = self.walking_forward_frames[0].get_size()

        walking_backward_frames = [pygame.image.load(f"assets/images/frames/main_character/walking/walking_backward/frame_{i}.png").convert_alpha() for i in range(8)]
        self.walking_backward_frames = [self.normalize_frame(f, target_size) for f in walking_backward_frames]

        self.current_frames = self.idle_right_frames
        self.pos_x, self.pos_y = map_width // 2, map_height // 2
        self.current, self.timer = 0, 0

    def normalize_frame(self, image, size):
        scale_factor = min(size[0] / image.get_width(), size[1] / image.get_height())
        new_w = int(image.get_width() * scale_factor + 150)
        new_h = int(image.get_height() * scale_factor + 150)
        scaled = pygame.transform.scale(image, (new_w, new_h))

        canvas = pygame.Surface(size, pygame.SRCALPHA)
        rect = scaled.get_rect(center=(size[0] // 2, size[1] // 2))
        canvas.blit(scaled, rect)
        return canvas

    def update_frames(self, keys):
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.current_frames = self.walking_forward_frames
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.current_frames = self.walking_backward_frames
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.current_frames = self.walking_left_frames
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.current_frames = self.walking_right_frames
        else:
            self.current_frames = self.idle_right_frames

    def update_position(self, dx, dy, player_rect, player_x, player_y, collision_rects, map_width, map_height):
        player_x += dx
        player_rect.x = round(player_x)
        for rect in collision_rects:
            if player_rect.colliderect(rect):
                if dx > 0:
                    player_rect.right = rect.left
                elif dx < 0:
                    player_rect.left = rect.right
                player_x = float(player_rect.x)

        player_y += dy
        player_rect.y = round(player_y)
        for rect in collision_rects:
            if player_rect.colliderect(rect):
                if dy > 0:
                    player_rect.bottom = rect.top
                elif dy < 0:
                    player_rect.top = rect.bottom
                player_y = float(player_rect.y)

        player_rect.clamp_ip(pygame.Rect(0, 0, map_width, map_height))

        self.pos_x = float(player_rect.x)
        self.pos_y = float(player_rect.y)

    def draw_frames(self, ZOOM, camera_x, camera_y):
        self.timer += 1
        if self.timer >= 6:
            self.timer = 0
            self.current = (self.current + 1) % 8
        self.screen.blit(self.current_frames[self.current], (self.pos_x * ZOOM - camera_x, self.pos_y * ZOOM - camera_y))
````

## File: main.py
````python
import pygame
import sys
from src.screens.main_menu import main_menu
from pytmx.util_pygame import load_pygame

# Initialize Pygame
pygame.init()

def main():
    # Start with main menu
    main_menu()

if __name__ == "__main__":
    main()
````

## File: src/screens/game.py
````python
from pytmx.util_pygame import load_pygame
import pygame
import sys
from src.settings_state import settings_state as _settings_state
from src.entities.player import MainCharacter

def game_screen(screen):
    clock = pygame.time.Clock()

    pygame.mixer.music.load("assets/audios/gameStage1Bgm.mp3")  
    pygame.mixer.music.set_volume(_settings_state["music_vol"])  # ← use saved volume                  
    pygame.mixer.music.play(-1)

    # --- Load Map ---
    tmx_data = load_pygame("assets/map/tmx/basic.tmx")
    TILE_SIZE = tmx_data.tilewidth

    map_width  = tmx_data.width  * TILE_SIZE
    map_height = tmx_data.height * TILE_SIZE

    # --- Build collision rects from tile custom properties ---
    collision_rects = []
    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'data'):
            for x, y, gid in layer:
                if gid == 0:
                    continue
                props = tmx_data.get_tile_properties_by_gid(gid)
                if props and props.get('collidable'):
                    collision_rects.append(
                        pygame.Rect(
                            x * TILE_SIZE,
                            y * TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE
                        )
                    )

    # --- Load interactive objects from Object Layer ---
    interactables = []
    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'name') and layer.name == "Object Layer 1":
            for obj in layer:
                if obj.properties.get('types') == 'interactive':
                    interactables.append({
                        'rect': pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height)),
                        'actions': obj.properties.get('actions'),
                        'inspecting': False,
                        'inspect_progress': 0.0
                    })

    # --- Player Setup ---
    SCREEN_W, SCREEN_H = screen.get_size()
    player_size = TILE_SIZE
    player_rect = pygame.Rect(
        map_width  // 2,
        map_height // 2,
        player_size,
        player_size
    )

    # Float position to avoid integer truncation causing uneven movement
    player_rect.clamp_ip(pygame.Rect(0, 0, map_width, map_height))
    player_x = float(player_rect.x)
    player_y = float(player_rect.y)
    player_speed = 2.50
    player_color = (255, 50, 50)

    # --- Fonts ---
    font = pygame.font.SysFont("consolas", 18)
    inspect_font = pygame.font.SysFont("consolas", 20)
    pause_title_font = pygame.font.SysFont("consolas", 40, bold=True)
    pause_button_font = pygame.font.SysFont("consolas", 24, bold=True)
    INSPECT_TIME = 2.0  # seconds to hold E

    # --- Camera with zoom ---
    camera_x = 0
    camera_y = 0

    ZOOM = 2 # increase this to zoom in more (ex. 2, 3, or 4)

    def update_camera():
        cx = player_rect.centerx * ZOOM - SCREEN_W // 2
        cy = player_rect.centery * ZOOM - SCREEN_H // 2
        cx = max(0, min(cx, map_width * ZOOM - SCREEN_W))
        cy = max(0, min(cy, map_height * ZOOM - SCREEN_H))
        return cx, cy

    # --- Pre-render map ---
    def render_map_surface():
        surf = pygame.Surface((map_width, map_height))
        for layer in tmx_data.visible_layers:
            if hasattr(layer, 'data'):
                for x, y, gid in layer:
                    if gid == 0:
                        continue
                    tile = tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        surf.blit(tile, (x * TILE_SIZE, y * TILE_SIZE))
        return surf

    map_surface = render_map_surface()
    # Scale the pre-rendered map once at startup based on ZOOM level (e.g. ZOOM=2 doubles the size)
    # This avoids rescaling every frame which would slow down the game
    map_surface = pygame.transform.scale(map_surface, (map_width * ZOOM, map_height * ZOOM))

    # --- Pause menu setup ---
    paused = False
    show_pause_settings = False

    PAUSE_MENU_OPTIONS = [
        ("RESUME", "resume"),
        ("SETTINGS", "settings"),
        ("RETURN TO MAIN MENU", "main_menu"),
    ]
    PAUSE_BTN_WIDTH, PAUSE_BTN_HEIGHT, PAUSE_BTN_GAP = 320, 56, 18
    pause_by0 = SCREEN_H // 2 - 60
    pause_center_x = SCREEN_W // 2 - PAUSE_BTN_WIDTH // 2

    pause_buttons = []
    for i, (label, action) in enumerate(PAUSE_MENU_OPTIONS):
        pause_buttons.append({
            "label": label,
            "action": action,
            "rect": pygame.Rect(
                pause_center_x,
                pause_by0 + i * (PAUSE_BTN_HEIGHT + PAUSE_BTN_GAP),
                PAUSE_BTN_WIDTH,
                PAUSE_BTN_HEIGHT
            )
        })

    settings_panel_rect = pygame.Rect(SCREEN_W // 2 - 220, SCREEN_H // 2 - 160, 440, 320)
    music_bar = pygame.Rect(settings_panel_rect.left + 30, settings_panel_rect.top + 100, settings_panel_rect.width - 60, 14)
    sfx_bar   = pygame.Rect(settings_panel_rect.left + 30, settings_panel_rect.top + 170, settings_panel_rect.width - 60, 14)
    settings_back_rect = pygame.Rect(settings_panel_rect.centerx - 70, settings_panel_rect.bottom - 56, 140, 36)
    dragging_music = False
    dragging_sfx = False

    def draw_pause_button(surf, rect, label, hovered):
        color = (60, 90, 130) if hovered else (40, 42, 54)
        border_color = (120, 180, 230) if hovered else (90, 94, 110)
        pygame.draw.rect(surf, color, rect, border_radius=6)
        pygame.draw.rect(surf, border_color, rect, 2, border_radius=6)
        txt = pause_button_font.render(label, True, (255, 255, 255))
        surf.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

    def draw_pause_menu(surf, mouse_pos):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))
        title = pause_title_font.render("PAUSED", True, (255, 255, 255))
        surf.blit(title, (SCREEN_W // 2 - title.get_width() // 2, pause_by0 - 100))
        for btn in pause_buttons:
            hovered = btn["rect"].collidepoint(mouse_pos)
            draw_pause_button(surf, btn["rect"], btn["label"], hovered)

    def draw_pause_settings(surf, mouse_pos):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))
        pygame.draw.rect(surf, (36, 38, 48), settings_panel_rect, border_radius=8)
        pygame.draw.rect(surf, (90, 94, 110), settings_panel_rect, 3, border_radius=8)
        title = pause_button_font.render("SETTINGS", True, (255, 255, 255))
        surf.blit(title, (settings_panel_rect.centerx - title.get_width() // 2, settings_panel_rect.top + 20))

        surf.blit(font.render("MUSIC", True, (200, 200, 210)), (music_bar.left, music_bar.top - 26))
        pygame.draw.rect(surf, (20, 22, 30), music_bar, border_radius=4)
        mx = music_bar.left + int((music_bar.width - 16) * _settings_state["music_vol"])
        pygame.draw.rect(surf, (255, 220, 120), (mx, music_bar.top - 2, 16, 18), border_radius=3)

        surf.blit(font.render("SFX", True, (200, 200, 210)), (sfx_bar.left, sfx_bar.top - 26))
        pygame.draw.rect(surf, (20, 22, 30), sfx_bar, border_radius=4)
        sx = sfx_bar.left + int((sfx_bar.width - 16) * _settings_state["sfx_vol"])
        pygame.draw.rect(surf, (255, 220, 120), (sx, sfx_bar.top - 2, 16, 18), border_radius=3)

        back_hovered = settings_back_rect.collidepoint(mouse_pos)
        draw_pause_button(surf, settings_back_rect, "BACK", back_hovered)

    running = True
    main_character = MainCharacter(screen, map_width, map_height)
    while running:
        clock.tick(60)
        mouse_pos = pygame.mouse.get_pos()

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if show_pause_settings:
                        show_pause_settings = False
                    elif paused:
                        paused = False
                    else:
                        paused = True

            if event.type == pygame.MOUSEBUTTONDOWN:
                if paused and not show_pause_settings:
                    for btn in pause_buttons:
                        if btn["rect"].collidepoint(event.pos):
                            if btn["action"] == "resume":
                                paused = False
                            elif btn["action"] == "settings":
                                show_pause_settings = True
                            elif btn["action"] == "main_menu":
                                pygame.mixer.music.stop()
                                return
                elif paused and show_pause_settings:
                    if music_bar.collidepoint(event.pos):
                        dragging_music = True
                    if sfx_bar.collidepoint(event.pos):
                        dragging_sfx = True
                    if settings_back_rect.collidepoint(event.pos):
                        show_pause_settings = False

            if event.type == pygame.MOUSEBUTTONUP:
                dragging_music = False
                dragging_sfx = False

        if dragging_music:
            _settings_state["music_vol"] = max(0.0, min(1.0, (mouse_pos[0] - music_bar.left) / music_bar.width))
            pygame.mixer.music.set_volume(_settings_state["music_vol"])
        if dragging_sfx:
            _settings_state["sfx_vol"] = max(0.0, min(1.0, (mouse_pos[0] - sfx_bar.left) / sfx_bar.width))

        if paused:
            screen.blit(map_surface, (-camera_x, -camera_y))
            pygame.draw.rect(
                screen,
                player_color,
                pygame.Rect(
                    player_rect.x * ZOOM - camera_x,
                    player_rect.y * ZOOM - camera_y,
                    player_rect.width * ZOOM,
                    player_rect.height * ZOOM
                )
            )
            if show_pause_settings:
                draw_pause_settings(screen, mouse_pos)
            else:
                draw_pause_menu(screen, mouse_pos)
            pygame.display.flip()
            continue

        # --- Movement ---
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy =  1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx =  1
        
        # Normalize diagonal movement so it's the same speed as cardinal directions
        if dx != 0 and dy != 0:
            dx *= 0.7071 # 1/sqrt(2)
            dy *= 0.7071

        dx *= player_speed
        dy *= player_speed

        # --- Collision (horizontal) ---
        player_x += dx
        player_rect.x = round(player_x)
        for rect in collision_rects:
            if player_rect.colliderect(rect):
                if dx > 0:
                    player_rect.right = rect.left
                elif dx < 0:
                    player_rect.left = rect.right
                # Only resync the float when a collision actually adjusted the rect.
                # Resyncing unconditionally every frame discards the leftover
                # sub-pixel fraction (e.g. the .5 in speed 2.5), which is what
                # was causing the inconsistent / direction-dependent speed.
                player_x = float(player_rect.x)

        # --- Collision (vertical) ---
        player_y += dy
        player_rect.y = round(player_y)
        for rect in collision_rects:
            if player_rect.colliderect(rect):
                if dy > 0:
                    player_rect.bottom = rect.top
                elif dy < 0:
                    player_rect.top = rect.bottom
                player_y = float(player_rect.y)

        # --- Keep player inside map bounds ---
        player_rect.clamp_ip(pygame.Rect(0, 0, map_width, map_height))
        player_x = float(player_rect.x)
        player_y = float(player_rect.y)

        # --- Camera ---
        camera_x, camera_y = update_camera()

        # --- Check if player is near an interactable ---
        near_interactable = None
        for item in interactables:
            # player_rect is in UNSCALED world coordinates (ZOOM is only
            # applied when drawing to the screen), so the detection rect
            # must stay unscaled too to match it.
            detection_rect = item['rect'].inflate(20, 20)

            if player_rect.colliderect(detection_rect):
                near_interactable = item
                break

        # --- Handle E key hold ---
        if near_interactable:
            if keys[pygame.K_e]:
                near_interactable['inspect_progress'] += 1 / 60 / INSPECT_TIME
                near_interactable['inspect_progress'] = min(near_interactable['inspect_progress'], 1.0)
                if near_interactable['inspect_progress'] >= 1.0:
                    near_interactable['inspecting'] = True
            else:
                near_interactable['inspect_progress'] = max(
                    0, near_interactable['inspect_progress'] - 1 / 60 / INSPECT_TIME
                )
                if not near_interactable['inspecting']:
                    near_interactable['inspect_progress'] = 0.0
        else:
            for item in interactables:
                item['inspect_progress'] = 0.0
                item['inspecting'] = False

        # --- Draw ---
        screen.blit(map_surface, (-camera_x, -camera_y))

        # Draw player (scaled position)
        pygame.draw.rect(
            screen,
            player_color,
            pygame.Rect(
                player_rect.x * ZOOM - camera_x,
                player_rect.y * ZOOM - camera_y,
                player_rect.width * ZOOM,
                player_rect.height * ZOOM
            )
        )

        # --- Draw interaction UI ---
        if near_interactable:
            # Scale the interactable position to match the zoomed map
            cam_x = near_interactable['rect'].x * ZOOM - camera_x
            cam_y = near_interactable['rect'].y * ZOOM - camera_y - 30

            if not near_interactable['inspecting']:
                # "Hold E" prompt
                prompt = inspect_font.render("Hold E to search", True, (255, 255, 255))
                screen.blit(prompt, (cam_x, cam_y))

                # Progress bar background
                bar_w = 80
                pygame.draw.rect(screen, (50, 50, 50),
                                 (cam_x, cam_y + 22, bar_w, 8))
                # Progress bar fill
                pygame.draw.rect(screen, (255, 220, 50),
                                 (cam_x, cam_y + 22,
                                  int(bar_w * near_interactable['inspect_progress']), 8))
            else:
                # Show message based on object type
                action = near_interactable.get('actions', '')
                if action == 'search_barrel':
                    message = 'The barrel is empty.'
                elif action == 'search_burrow':
                    message = 'The burrow is empty.'
                elif action == 'search_vase':
                    message = 'The vase is empty.'
                elif action == 'search_hay':
                    message = 'The hay is empty.'
                else:
                    message = "Nothing here."
                msg = inspect_font.render(message, True, (255, 255, 200))
                box = pygame.Rect(
                    SCREEN_W // 2 - msg.get_width() // 2 - 10,
                    SCREEN_H // 2 - msg.get_height() // 2 - 10,
                    msg.get_width() + 20,
                    msg.get_height() + 20
                )
                pygame.draw.rect(screen, (20, 20, 20), box, border_radius=6)
                pygame.draw.rect(screen, (200, 200, 100), box, 2, border_radius=6)
                screen.blit(msg, (SCREEN_W // 2 - msg.get_width() // 2,
                                  SCREEN_H // 2 - msg.get_height() // 2))

                close_hint = font.render("Release E to close", True, (180, 180, 180))
                screen.blit(close_hint, (SCREEN_W // 2 - close_hint.get_width() // 2,
                                         SCREEN_H // 2 + msg.get_height()))

                if not keys[pygame.K_e]:
                    near_interactable['inspecting'] = False
                    near_interactable['inspect_progress'] = 0.0

        # ESC hint
        hint = font.render("ESC = Pause", True, (255, 255, 255))
        screen.blit(hint, (10, 10))

        main_character.update_position(dx, dy, player_rect, player_x, player_y, collision_rects, map_width, map_height)   
        main_character.update_frames(keys)
        main_character.draw_frames(ZOOM, camera_x, camera_y)
        
        
        pygame.display.flip()
````

## File: src/screens/main_menu.py
````python
import math
import random
import sys
import pygame
from src.screens.game import game_screen
from src.settings_state import settings_state as _settings_state

# Initialize Pygame
pygame.init()

# Screen settings
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
pygame.display.set_caption("CodeBreak - Main Menu")

background = pygame.image.load("assets/images/backgrounds/mainMenuBg.png").convert()
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
screen.blit(background, (0, 0))

# Palette
STONE_DARK = (28, 30, 38)
STONE_MID = (42, 46, 58)
STONE_LIGHT = (62, 68, 82)
BLUE_GLOW = (80, 180, 255)
BLUE_DEEP = (35, 90, 140)
YELLOW_GLOW = (255, 220, 120)
GREEN_TIP = (60, 255, 140)
GREEN_PLAY = (80, 220, 120)
WHITE = (255, 255, 255)
METAL_FRAME = (90, 94, 110)
ROBOT_BLUE = (70, 140, 220)

# Fonts
_button_font = pygame.font.SysFont("consolas", 26, bold=True)
_small = pygame.font.SysFont("consolas", 18)
_tip_font = pygame.font.SysFont("consolas", 17)


def _fallback_font(size, bold=False):
    return pygame.font.Font(None, size)


try:
    _ = _button_font.render("x", True, WHITE)
except Exception:
    _button_font = _fallback_font(24, True)
    _small = _fallback_font(18)
    _tip_font = _fallback_font(17)


def _stone_texture(surf: pygame.Surface, rect: pygame.Rect, seed: int) -> None:
    rng = random.Random(seed)
    surf.fill(STONE_MID, rect)
    for _ in range(120):
        x = rect.left + rng.randint(0, rect.width - 1)
        y = rect.top + rng.randint(0, rect.height - 1)
        c = rng.choice([STONE_DARK, STONE_LIGHT, (50, 54, 68)])
        pygame.draw.rect(surf, c, (x, y, rng.randint(2, 5), rng.randint(1, 3)))
    pygame.draw.rect(surf, STONE_LIGHT, rect, 2)
    hi = tuple(min(255, c + 35) for c in STONE_LIGHT)
    pygame.draw.line(surf, hi, rect.topleft, (rect.right - 1, rect.top), 1)
    lo = tuple(max(0, c - 25) for c in STONE_DARK)
    pygame.draw.line(surf, lo, (rect.left, rect.bottom - 1), rect.bottomright, 1)


def _draw_menu_icon(surf: pygame.Surface, kind: str, rect: pygame.Rect) -> None:
    ix = rect.left + 28
    iy = rect.centery
    if kind == "play":
        pygame.draw.polygon(surf, GREEN_PLAY, [(ix - 10, iy - 14), (ix - 10, iy + 14), (ix + 14, iy)])
    elif kind == "chest":
        pygame.draw.rect(surf, BLUE_DEEP, (ix - 14, iy - 10, 28, 20), border_radius=2)
        pygame.draw.rect(surf, BLUE_GLOW, (ix - 14, iy - 14, 28, 6), border_radius=2)
        pygame.draw.rect(surf, STONE_LIGHT, (ix - 14, iy - 10, 28, 20), 2, border_radius=2)
    elif kind == "gear":
        pygame.draw.circle(surf, (140, 140, 150), (ix, iy), 14)
        for a in range(0, 360, 45):
            rad = math.radians(a)
            x1 = ix + int(10 * math.cos(rad))
            y1 = iy + int(10 * math.sin(rad))
            x2 = ix + int(18 * math.cos(rad))
            y2 = iy + int(18 * math.sin(rad))
            pygame.draw.line(surf, (180, 180, 190), (x1, y1), (x2, y2), 4)
        pygame.draw.circle(surf, (60, 62, 72), (ix, iy), 6)
    elif kind == "quit":
        pygame.draw.line(surf, (255, 80, 80), (ix - 12, iy - 12), (ix + 12, iy + 12), 5)
        pygame.draw.line(surf, (255, 80, 80), (ix - 12, iy + 12), (ix + 12, iy - 12), 5)


def _draw_stone_button(
    surf: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    icon: str,
    hovered: bool,
    seed: int,
) -> None:
    r = rect.inflate(4, 4) if hovered else rect
    tmp = pygame.Surface((r.w, r.h))
    _stone_texture(tmp, tmp.get_rect(), seed)
    if hovered:
        overlay = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        overlay.fill((*BLUE_GLOW[:3], 40))
        tmp.blit(overlay, (0, 0))
    surf.blit(tmp, r.topleft)
    _draw_menu_icon(surf, icon, pygame.Rect(r.left, r.top, r.w, r.h))
    txt = _button_font.render(label, True, WHITE)
    surf.blit(txt, (r.left + 52, r.centery - txt.get_height() // 2))


def _draw_robot_tip(surf: pygame.Surface, t: float) -> None:
    rx, ry = SCREEN_WIDTH - 200, SCREEN_HEIGHT - 140
    pygame.draw.rect(surf, ROBOT_BLUE, (rx - 36, ry - 50, 72, 70), border_radius=6)
    pygame.draw.rect(surf, (40, 90, 150), (rx - 36, ry - 50, 72, 70), 2, border_radius=6)
    pygame.draw.rect(surf, (20, 40, 70), (rx - 24, ry - 42, 48, 28))
    eye_y = ry - 32
    pygame.draw.rect(surf, (180, 220, 255), (rx - 16, eye_y, 12, 8))
    pygame.draw.rect(surf, (180, 220, 255), (rx + 4, eye_y, 12, 8))
    pygame.draw.rect(surf, (60, 80, 120), (rx - 6, eye_y + 12, 12, 3))
    pygame.draw.rect(surf, ROBOT_BLUE, (rx - 50, ry - 30, 14, 36), border_radius=3)
    pygame.draw.rect(surf, ROBOT_BLUE, (rx + 36, ry - 30, 14, 36), border_radius=3)
    scr = pygame.Rect(rx + 44, ry - 38, 28, 40)
    pygame.draw.rect(surf, (230, 210, 160), scr, border_radius=2)
    pygame.draw.rect(surf, (120, 100, 70), scr, 1, border_radius=2)
    pygame.draw.rect(surf, ROBOT_BLUE, (rx - 22, ry + 18, 16, 22), border_radius=3)
    pygame.draw.rect(surf, ROBOT_BLUE, (rx + 6, ry + 18, 16, 22), border_radius=3)
    tip_r = pygame.Rect(SCREEN_WIDTH - 520, SCREEN_HEIGHT - 118, 300, 72)
    pulse = int(80 + 40 * math.sin(t * 3))
    pygame.draw.rect(surf, (10, 40, 20), tip_r, border_radius=4)
    pygame.draw.rect(surf, (GREEN_TIP[0] // 2, GREEN_TIP[1] // 2, GREEN_TIP[2] // 2), tip_r, 2, border_radius=4)
    glow_s = pygame.Surface((tip_r.w, tip_r.h), pygame.SRCALPHA)
    pygame.draw.rect(glow_s, (*GREEN_TIP[:3], pulse // 4), glow_s.get_rect(), border_radius=4)
    surf.blit(glow_s, tip_r.topleft)
    tip_lines = ["TIP: Think before you type...", "The dungeon punishes mistakes."]
    for i, line in enumerate(tip_lines):
        surf.blit(_tip_font.render(line, True, GREEN_TIP), (tip_r.left + 12, tip_r.top + 10 + i * 22))


def _draw_interactive_settings(surf: pygame.Surface, mouse_pos, show: bool) -> bool:
    s = _settings_state
    pr = pygame.Rect(SCREEN_WIDTH - 620, 200, 380, 480)

    # Rects
    music_bar   = pygame.Rect(pr.left + 28, pr.top + 160, pr.width - 56, 14)
    sfx_bar     = pygame.Rect(pr.left + 28, pr.top + 240, pr.width - 56, 14)
    arrow_y     = pr.top + 350
    left_arrow  = pygame.Rect(pr.left + 60,   arrow_y, 40, 28)
    right_arrow = pygame.Rect(pr.right - 100, arrow_y, 40, 28)
    back_r      = pygame.Rect(pr.centerx - 70, pr.bottom - 56, 140, 36)

    mouse_pressed = pygame.mouse.get_pressed()

    # Click handling
    if mouse_pressed[0]:
        if music_bar.collidepoint(mouse_pos):
            s["dragging_music"] = True
        if sfx_bar.collidepoint(mouse_pos):
            s["dragging_sfx"] = True
        if left_arrow.collidepoint(mouse_pos):
            s["theme_index"] = (s["theme_index"] - 1) % len(s["themes"])
        if right_arrow.collidepoint(mouse_pos):
            s["theme_index"] = (s["theme_index"] + 1) % len(s["themes"])
        if back_r.collidepoint(mouse_pos):
            return False  # close panel
    else:
        s["dragging_music"] = False
        s["dragging_sfx"]   = False

    if s["dragging_music"]:
        s["music_vol"] = max(0.0, min(1.0, (mouse_pos[0] - music_bar.left) / music_bar.width))
        pygame.mixer.music.set_volume(s["music_vol"]) # update volume immediately
    if s["dragging_sfx"]:
        s["sfx_vol"] = max(0.0, min(1.0, (mouse_pos[0] - sfx_bar.left) / sfx_bar.width))

    # Draw panel
    pygame.draw.rect(surf, (36, 38, 48), pr)
    pygame.draw.rect(surf, METAL_FRAME, pr, 4)
    pygame.draw.rect(surf, (26, 28, 36), pr.inflate(-24, -24))

    title = _button_font.render("SETTINGS", True, WHITE)
    surf.blit(title, (pr.centerx - title.get_width() // 2, pr.top + 16))

    # Text speed
    surf.blit(_small.render("TEXT SPEED", True, (200, 200, 210)), (pr.left + 28, pr.top + 70))
    surf.blit(_small.render("SLOW    NORMAL    INSTANT", True, (160, 170, 190)), (pr.left + 28, pr.top + 96))

    # Music
    surf.blit(_small.render("MUSIC", True, (200, 200, 210)), (pr.left + 28, pr.top + 140))
    pygame.draw.rect(surf, (30, 32, 40), music_bar, border_radius=4)
    mx = music_bar.left + int((music_bar.width - 16) * s["music_vol"])
    pygame.draw.rect(surf, YELLOW_GLOW, (mx, music_bar.top - 2, 16, 18), border_radius=3)

    # SFX
    surf.blit(_small.render("SFX", True, (200, 200, 210)), (pr.left + 28, pr.top + 220))
    pygame.draw.rect(surf, (30, 32, 40), sfx_bar, border_radius=4)
    sx = sfx_bar.left + int((sfx_bar.width - 16) * s["sfx_vol"])
    pygame.draw.rect(surf, YELLOW_GLOW, (sx, sfx_bar.top - 2, 16, 18), border_radius=3)

    # Syntax theme
    surf.blit(_small.render("SYNTAX THEME", True, (200, 200, 210)), (pr.left + 28, pr.top + 300))
    pygame.draw.rect(surf, (50, 55, 70), left_arrow, border_radius=4)
    pygame.draw.rect(surf, (50, 55, 70), right_arrow, border_radius=4)
    tri_l = [(left_arrow.right - 8, left_arrow.top + 6), (left_arrow.right - 8, left_arrow.bottom - 6), (left_arrow.left + 6, left_arrow.centery)]
    tri_r = [(right_arrow.left + 8, right_arrow.top + 6), (right_arrow.left + 8, right_arrow.bottom - 6), (right_arrow.right - 6, right_arrow.centery)]
    pygame.draw.polygon(surf, BLUE_GLOW, tri_l)
    pygame.draw.polygon(surf, BLUE_GLOW, tri_r)
    theme_colors = {"GREEN": (60, 255, 140), "BLUE": (80, 180, 255), "ORANGE": (255, 160, 60), "PURPLE": (180, 100, 255)}
    current = s["themes"][s["theme_index"]]
    th = _button_font.render(current, True, theme_colors[current])
    surf.blit(th, (pr.centerx - th.get_width() // 2, arrow_y + 4))

    # Back button
    pygame.draw.rect(surf, STONE_MID, back_r, border_radius=4)
    pygame.draw.rect(surf, STONE_LIGHT, back_r, 2, border_radius=4)
    bt = _button_font.render("BACK", True, WHITE)
    surf.blit(bt, (back_r.centerx - bt.get_width() // 2, back_r.centery - bt.get_height() // 2))

    return True  # keep panel open

def main_menu():
    from src.screens.settings import settings_screen
    from src.screens.tutorial import tutorial_screen

    show_settings = False

    bw, bh = 380, 64
    by0 = SCREEN_HEIGHT // 2 - 80
    gap = 16

    center_x = SCREEN_WIDTH // 2 - bw // 2   # horizontally centered

    rects = [
        pygame.Rect(center_x, by0 + 0 * (bh + gap), bw, bh),  # START
        pygame.Rect(center_x, by0 + 1 * (bh + gap), bw, bh),  # CONTINUE
        pygame.Rect(center_x, by0 + 2 * (bh + gap), bw, bh),  # SETTINGS
        pygame.Rect(center_x, by0 + 3 * (bh + gap), bw, bh),  # QUIT
    ]

    icons = ["play", "chest", "gear", "quit"]
    labels = ["START NEW GAME", "CONTINUE", "SETTINGS", "QUIT"]
    seeds = [11, 22, 33, 44]

    clock = pygame.time.Clock()
    logo = pygame.image.load("assets/images/logos/codebreakLogo.png").convert_alpha()
    logo = pygame.transform.scale(logo, (620, 400))
    running = True

    pygame.mixer.music.load("assets/audios/mainMenuBgm.mp3")
    pygame.mixer.music.set_volume(_settings_state["music_vol"])
    pygame.mixer.music.play(-1)  # -1 means loop forever

    while running:
        t = pygame.time.get_ticks() / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        hovers = [r.collidepoint(mouse_pos) for r in rects]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if rects[0].collidepoint(event.pos):
                    pygame.mixer.music.stop()
                    game_screen(screen)
                    pygame.mixer.music.load("assets/audios/mainMenuBgm.mp3")  # ← add
                    pygame.mixer.music.set_volume(_settings_state["music_vol"])                         # ← add
                    pygame.mixer.music.play(-1) # resume when back
                if rects[1].collidepoint(event.pos):
                    pygame.mixer.music.stop()
                    tutorial_screen(screen)
                if rects[2].collidepoint(event.pos):
                    show_settings = not show_settings
                if rects[3].collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()


        screen.blit(background, (0, 0))
        screen.blit(logo, (SCREEN_WIDTH // 2 - logo.get_width() // 2, 0))

        for rect, label, icon, h, seed in zip(rects, labels, icons, hovers, seeds):
            _draw_stone_button(screen, rect, label, icon, h, seed)

        _draw_robot_tip(screen, t)
        ver = _small.render("v1.0", True, WHITE)
        screen.blit(ver, (16, SCREEN_HEIGHT - ver.get_height() - 12))

        if show_settings:
            show_settings = _draw_interactive_settings(screen, mouse_pos, show_settings)

        pygame.display.flip()
        clock.tick(60)
````
