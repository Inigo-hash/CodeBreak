> **Outdated.** This is a snapshot of an earlier layout, kept for history.
> It predates `src/systems/`, `src/data/stages.py`, `tests/`, the learning
> sandbox, and the stage/boss systems. See `CLAUDE.md` in the repo root for
> the current structure.

# CodeBreak Project Structure v3

## Overview

CodeBreak is a Python game project built with Pygame that combines a top-down exploration experience with an educational coding challenge system. The project is organized around game screens, game entities, a UI-based code editor, and a learning module that validates player solutions.

## Folder Structure

```text
CodeBreak Project/
├── AI_TestCase_Generation_Process.md
├── main.py
├── README.md
├── requirements.txt
├── assets/
│   ├── audios/
│   ├── fonts/
│   ├── images/
│   │   ├── backgrounds/
│   │   ├── characters/
│   │   ├── enemies/
│   │   ├── frames/
│   │   ├── logos/
│   │   └── ui/
│   ├── map/
│   │   ├── tiledsets/
│   │   ├── tmx/
│   │   └── tsx/
│   └── sounds/
├── src/
│   ├── config.py
│   ├── settings_state.py
│   ├── data/
│   │   ├── challenges.py
│   │   └── topics.py
│   ├── entities/
│   │   ├── enemy.py
│   │   └── player.py
│   ├── learning/
│   │   ├── challenge_manager.py
│   │   └── validators/
│   │       └── variable_validator.py
│   ├── screens/
│   │   ├── game.py
│   │   ├── game_over.py
│   │   ├── main_menu.py
│   │   ├── profile.py
│   │   ├── settings.py
│   │   ├── sprites.py
│   │   └── tutorial.py
│   ├── ui/
│   │   ├── code_editor.py
│   │   ├── editor_renderer.py
│   │   ├── editor_theme.py
│   │   ├── editor_widgets.py
│   │   ├── output_panel.py
│   │   ├── problem_panel.py
│   │   └── text_buffer.py
│   └── utils/
│       ├── constants.py
│       └── helpers.py
```

## Important Files

### Root-Level Files

- main.py
  - Entry point of the application. It initializes Pygame and starts the main menu.

- README.md
  - Project overview and basic documentation for the CodeBreak game.

- requirements.txt
  - Lists Python dependencies needed to run the project.

- AI_TestCase_Generation_Process.md
  - Internal documentation related to generating test case ideas for the project.

### Core Configuration and State

- src/config.py
  - Stores shared runtime configuration such as fullscreen settings.

- src/settings_state.py
  - Holds persistent UI and audio settings like volume levels and selected theme.

### Game Content and Learning Data

- src/data/challenges.py
  - Contains challenge definitions, including lesson content, problem statements, and expected outcomes.

- src/data/topics.py
  - Intended to organize or reference learning topics for the project.

### Game Entities

- src/entities/player.py
  - Defines the main playable character, including animation frames, movement logic, and rendering.

- src/entities/enemy.py
  - Defines the enemy character and its animation behavior.

### Learning System

- src/learning/challenge_manager.py
  - Coordinates challenge validation by routing a challenge to the correct validator.

- src/learning/validators/variable_validator.py
  - Validates Python code for simple variable assignment challenges.

### Screens

- src/screens/main_menu.py
  - Implements the main menu interface and navigation to other screens.

- src/screens/game.py
  - Core gameplay screen. It loads the map, creates the player/enemy, handles camera movement, pause behavior, and HUD rendering.

- src/screens/settings.py
  - Implements the settings interface for audio and theme controls.

- src/screens/game_over.py
  - Handles the game-over screen flow.

- src/screens/profile.py
  - Supports profile-related UI or screen logic.

- src/screens/sprites.py
  - Contains sprite-related screen logic or supporting functionality.

- src/screens/tutorial.py
  - Placeholder or early implementation for a tutorial screen.

### UI and Editor System

- src/ui/code_editor.py
  - Main controller for the in-game coding editor. It manages input, keyboard events, scrolling, and the editor lifecycle.

- src/ui/editor_renderer.py
  - Responsible for drawing the full coding environment, including panels, buttons, the editor area, and output area.

- src/ui/editor_theme.py
  - Stores visual styling constants for the coding editor.

- src/ui/editor_widgets.py
  - Defines UI widget components used by the editor, such as buttons.

- src/ui/output_panel.py
  - Displays output from code execution or validation.

- src/ui/problem_panel.py
  - Displays the current coding problem and challenge instructions.

- src/ui/text_buffer.py
  - Stores and manages the text content typed into the code editor.

### Utility Modules

- src/utils/constants.py
  - Stores shared constants such as screen size, colors, and frame rate.

- src/utils/helpers.py
  - Contains helper functions for common operations.

## How the Major Components Relate

- main.py is the bootstrap file. It starts the game by launching the main menu.

- The main menu in src/screens/main_menu.py is the entry point into the rest of the game. It can transition into gameplay, settings, or other screens.

- The gameplay loop in src/screens/game.py uses the player and enemy entities from src/entities/ and renders the world using assets from the assets/ folder.

- The game screen also connects to the learning system by opening the coding editor when a challenge is presented.

- The code editor is built from src/ui/code_editor.py and src/ui/editor_renderer.py. These rely on text handling from src/ui/text_buffer.py and challenge display components from src/ui/problem_panel.py and src/ui/output_panel.py.

- Challenge content comes from src/data/challenges.py and is validated through src/learning/challenge_manager.py and specific validators such as src/learning/validators/variable_validator.py.

- Shared settings such as audio volume and theme selection are stored in src/settings_state.py and used by both the main menu and gameplay/settings screens.

- Assets such as maps, tile sets, sprites, music, and UI images live under assets/ and are loaded by the game screens and entities during runtime.
