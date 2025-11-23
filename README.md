# Album Rhythm Round

A lightweight arrow-key rhythm round that plays alongside any MP3 you provide. Use the left, right, up, and down arrows to hit the targets as the song plays.

## Setup

1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the game by pointing it at an MP3 file:

```bash
python rhythm_game.py path/to/song.mp3
```

Controls:

- **Arrow keys:** Hit the matching arrow as it crosses the target outline near the bottom of the screen.
- **Close window:** Quit the round.

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
