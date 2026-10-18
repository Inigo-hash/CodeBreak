# CodeBreak

A desktop game for learning Python through exploration, coding challenges,
and combat with Filipino folklore creatures.

## Run

Use Python 3.12 from the repository root:

```bash
python -m pip install -r requirements.txt
python main.py
```

The Island teaches nine beginner lessons. Castle adds nine intermediate topic
groups through 18 challenges, five mastery keys, Zombie Aktan and a rotating
final coding assessment. Citadel is a future chapter.

WASD/arrows move, E attacks with an equipped sword, hold E interacts, Shift
dodges, B opens the bag, G opens the atlas, and Escape opens pause/save/settings.
See the in-game manual for the full controls and lesson requirements.
Debug tools remain enabled during development; F4 toggles exploration bypass.

## Tests

Install server test dependencies too:

```bash
python -m pip install -r server/requirements.txt
```

Run test modules separately to isolate SDL teardown:

```bash
for f in tests/test_*.py; do
  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python -m unittest discover -s tests -p "$(basename "$f")" || exit 1
done
```

Game code is in `src/`, authored content in `src/data/`, map/audio/art in
`assets/`, the AI tutor relay in `server/`, and verification in `tests/`.
See [CLAUDE.md](CLAUDE.md) for architecture and [Castle completion](docs/castle-completion.md)
for the latest Castle implementation notes.
