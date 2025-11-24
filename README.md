# Album Rhythm Round

A lightweight arrow-key rhythm round that listens to any MP3 you provide, generates arrows on the song's stronger beats, and lights up the lane colors when you time your hits correctly.

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

1. Run the command above after installing the requirements (skipping this step can trigger ModuleNotFound errors).
2. Click **Import MP3** (or press **I**) to open a file picker and choose your song. This is the simplest way to play.
3. Press **Esc** on the import screen to quit without starting a round.
4. If you provided a path on the command line that cannot be found, the main menu will show a red error message and let you pick a valid file instead of exiting.

What happens under the hood:

- When you pick a song, the game scans the audio (RMS energy peaks every ~120 ms) to find the loudest beats and uses those timestamps to schedule arrows.
- If beat analysis fails for any reason, it falls back to steady spawns using the configured interval so you can still play.
- Each lane has its own color, and successful hits cause a brief flash across the background so you can feel your timing.

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

## Why this build is better

- **Simple setup:** Only `pygame` and `pydub` are required—no `numpy` or heavy extras—so fresh Windows installs avoid missing-module errors.
- **Menu-first flow:** The import button and on-screen guidance keep players in-app when a path is wrong instead of crashing back to the shell.
- **Beat-aware arrows:** The game listens to each MP3, pulls energy peaks, and syncs arrows to those beats with a steady fallback if decoding fails.
- **Readable visuals:** Color-coded lanes, background flashes on hits, and target outlines make timing feedback obvious.

## Building a Windows executable

You can bundle the script into a standalone Windows executable with PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed rhythm_game.py
```

The resulting executable will be available in the `dist/` directory. Ensure you distribute it together with any MP3s you want to play.
