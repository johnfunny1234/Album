# Album Rhythm Round

A lightweight arrow-key rhythm round that plays alongside any MP3 you provide. Use the left, right, up, and down arrows to hit the targets as the song plays.

## Setup

1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Launch the game to reach the main menu, then import a song via the on-screen button:

```bash
python rhythm_game.py
```

- Click **Import MP3** (or press **I**) to open a file picker and choose your song. This is the simplest way to play.
- Press **Esc** on the import screen to quit without starting a round.
- If you provided a path on the command line that cannot be found, the main menu will show a red error message and let you pick a valid file instead of exiting.

Controls during a round:

- **Arrow keys:** Hit the matching arrow as it crosses the target outline near the bottom of the screen.
- **Close window:** Quit the round.

You can still launch directly from the command line if you prefer, and the main menu will appear if the path is missing:

```bash
python rhythm_game.py path/to/song.mp3
```

Use `--spawn-interval` to tune difficulty (lower values spawn arrows faster):

```bash
python rhythm_game.py path/to/song.mp3 --spawn-interval 700
```

## Building a Windows executable

You can bundle the script into a standalone Windows executable with PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed rhythm_game.py
```

The resulting executable will be available in the `dist/` directory. Ensure you distribute it together with any MP3s you want to play.
