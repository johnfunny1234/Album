import argparse
import importlib.util
import math
import random
from pathlib import Path

import numpy as np
import pygame
from pydub import AudioSegment

if importlib.util.find_spec("tkinter"):
    import tkinter as tk
    from tkinter import filedialog
else:
    tk = None
    filedialog = None


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
TARGET_Y = 480
ARROW_SPEED = 240  # pixels per second
SPAWN_INTERVAL_MS = 800
WINDOW_BG = (16, 18, 32)
HIT_FLASH_DURATION = 0.25

ARROW_POSITIONS = {
    "left": 200,
    "down": 320,
    "up": 440,
    "right": 560,
}

ARROW_KEYS = {
    pygame.K_LEFT: "left",
    pygame.K_DOWN: "down",
    pygame.K_UP: "up",
    pygame.K_RIGHT: "right",
}


class Arrow:
    def __init__(self, direction: str, y: float):
        self.direction = direction
        self.y = y
        self.hit = False

    @property
    def x(self) -> int:
        return ARROW_POSITIONS[self.direction]

    def update(self, delta_seconds: float) -> None:
        self.y += ARROW_SPEED * delta_seconds


class RhythmRound:
    def __init__(
        self,
        song_path: Path,
        spawn_interval_ms: int = SPAWN_INTERVAL_MS,
        screen: pygame.Surface | None = None,
        clock: pygame.time.Clock | None = None,
        font: pygame.font.Font | None = None,
    ):
        if not pygame.get_init():
            pygame.init()
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        self.screen = screen or pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Arrow Rhythm Round")

        self.clock = clock or pygame.time.Clock()
        self.font = font or pygame.font.SysFont("arial", 24)

        self.song_path = song_path
        self.spawn_interval_ms = spawn_interval_ms
        self.arrows: list[Arrow] = []
        self.last_spawn = 0
        self.running = True
        self.score = 0
        self.combo = 0
        self.misses = 0
        self.start_time_ms = 0
        self.beat_schedule_ms = self.generate_beat_schedule()
        self.next_beat_index = 0
        self.hit_flash_time = 0.0
        self.last_hit_color = (120, 255, 200)

    def start_music(self) -> None:
        pygame.mixer.music.load(self.song_path.as_posix())
        pygame.mixer.music.play()
        now = pygame.time.get_ticks()
        self.last_spawn = now
        self.start_time_ms = now

    def generate_beat_schedule(
        self, window_ms: int = 120, min_interval_ms: int = 180
    ) -> list[int]:
        try:
            audio = AudioSegment.from_file(self.song_path)
        except Exception:
            return self._fallback_schedule()

        mono = np.array(audio.get_array_of_samples())
        if audio.channels > 1:
            mono = mono.reshape((-1, audio.channels)).mean(axis=1)

        window_samples = max(1, int(audio.frame_rate * (window_ms / 1000)))
        energies: list[float] = []
        for start in range(0, len(mono), window_samples):
            window = mono[start : start + window_samples]
            if len(window) == 0:
                break
            energies.append(float(np.sqrt(np.mean(np.square(window)))))

        if not energies:
            return self._fallback_schedule()

        median = float(np.median(energies))
        mad = float(np.median(np.abs(energies - median))) or 1.0
        threshold = median + 1.6 * mad

        beats: list[int] = []
        last_beat_time = -min_interval_ms
        for idx, energy in enumerate(energies):
            t_ms = int(idx * window_ms)
            if energy >= threshold and (t_ms - last_beat_time) >= min_interval_ms:
                beats.append(t_ms)
                last_beat_time = t_ms

        if len(beats) < 8:
            return self._fallback_schedule()
        return beats

    def _fallback_schedule(self) -> list[int]:
        try:
            length_s = pygame.mixer.Sound(self.song_path.as_posix()).get_length()
            duration_ms = int(length_s * 1000)
        except Exception:
            duration_ms = 180_000

        interval = self.spawn_interval_ms
        beats = [int(i * interval) for i in range(0, max(1, duration_ms // interval))]
        return beats or [0]

    def spawn_arrow(self) -> None:
        direction = list(ARROW_POSITIONS.keys())[self.next_beat_index % 4]
        self.arrows.append(Arrow(direction=direction, y=-50))

    def handle_key(self, direction: str) -> None:
        for arrow in sorted(self.arrows, key=lambda a: abs(a.y - TARGET_Y)):
            if arrow.direction != direction or arrow.hit:
                continue
            if abs(arrow.y - TARGET_Y) <= 48:
                arrow.hit = True
                self.score += 100
                self.combo += 1
                self.hit_flash_time = HIT_FLASH_DURATION
                self.last_hit_color = self.direction_color(direction)
                return
        self.combo = 0
        self.misses += 1

    def update_arrows(self, delta_seconds: float) -> None:
        for arrow in self.arrows:
            arrow.update(delta_seconds)
        for arrow in list(self.arrows):
            if arrow.y > TARGET_Y + 120:
                self.arrows.remove(arrow)
                if not arrow.hit:
                    self.combo = 0
                    self.misses += 1
            elif arrow.hit:
                self.arrows.remove(arrow)

    def draw_arrow(self, arrow: Arrow, color: tuple[int, int, int]) -> None:
        x = arrow.x
        y = arrow.y
        size = 32
        if arrow.direction == "left":
            points = [(x, y), (x - size, y - size), (x - size, y - 12), (x - 2 * size, y - 12),
                      (x - 2 * size, y + 12), (x - size, y + 12), (x - size, y + size)]
        elif arrow.direction == "right":
            points = [(x, y), (x + size, y - size), (x + size, y - 12), (x + 2 * size, y - 12),
                      (x + 2 * size, y + 12), (x + size, y + 12), (x + size, y + size)]
        elif arrow.direction == "up":
            points = [(x, y - size), (x - size, y), (x - 12, y), (x - 12, y + size),
                      (x + 12, y + size), (x + 12, y), (x + size, y)]
        else:  # down
            points = [(x, y + size), (x - size, y), (x - 12, y), (x - 12, y - size),
                      (x + 12, y - size), (x + 12, y), (x + size, y)]
        pygame.draw.polygon(self.screen, color, points)

    def draw_targets(self) -> None:
        for direction in ARROW_POSITIONS:
            temp_arrow = Arrow(direction, TARGET_Y)
            self.draw_arrow(temp_arrow, (70, 90, 120))

    def draw_stats(self) -> None:
        score_surface = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        combo_surface = self.font.render(f"Combo: {self.combo}", True, (255, 255, 0))
        miss_surface = self.font.render(f"Misses: {self.misses}", True, (255, 128, 128))
        self.screen.blit(score_surface, (20, 20))
        self.screen.blit(combo_surface, (20, 50))
        self.screen.blit(miss_surface, (20, 80))

    def direction_color(self, direction: str) -> tuple[int, int, int]:
        palette = {
            "left": (120, 200, 255),
            "down": (255, 140, 200),
            "up": (160, 255, 160),
            "right": (255, 200, 120),
        }
        return palette.get(direction, (200, 200, 255))

    def draw_background(self, delta_seconds: float) -> None:
        base_color = np.array(WINDOW_BG, dtype=float)
        if self.hit_flash_time > 0:
            self.hit_flash_time = max(0.0, self.hit_flash_time - delta_seconds)
            progress = self.hit_flash_time / HIT_FLASH_DURATION
            flash = np.array(self.last_hit_color, dtype=float)
            blend = base_color * (1 - progress) + flash * progress * 0.5
            color = tuple(int(c) for c in np.clip(blend, 0, 255))
        else:
            wave = (math.sin(pygame.time.get_ticks() / 800) + 1) / 2
            color = tuple(int(c + 8 * wave) for c in base_color)
        self.screen.fill(color)

    def tick(self) -> None:
        delta_seconds = self.clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key in ARROW_KEYS:
                self.handle_key(ARROW_KEYS[event.key])

        now = pygame.time.get_ticks()
        while (
            self.next_beat_index < len(self.beat_schedule_ms)
            and now - self.start_time_ms >= self.beat_schedule_ms[self.next_beat_index]
        ):
            self.spawn_arrow()
            self.last_spawn = now
            self.next_beat_index += 1

        self.update_arrows(delta_seconds)

        self.draw_background(delta_seconds)
        self.draw_targets()
        for arrow in self.arrows:
            color = self.direction_color(arrow.direction)
            if arrow.hit:
                color = tuple(min(255, c + 80) for c in color)
            self.draw_arrow(arrow, color)
        pygame.draw.rect(self.screen, (70, 90, 130), (120, TARGET_Y - 48, 520, 96), 3, 6)
        self.draw_stats()
        pygame.display.flip()

    def run(self) -> None:
        self.start_music()
        while self.running and (pygame.mixer.music.get_busy() or self.arrows):
            self.tick()


def pick_song_with_dialog() -> Path | None:
    if tk is None or filedialog is None:
        return None

    root = tk.Tk()
    root.withdraw()
    root.update()
    song_path = filedialog.askopenfilename(
        title="Import MP3",
        filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")],
    )
    root.destroy()
    return Path(song_path) if song_path else None


def show_import_screen(
    clock: pygame.time.Clock,
    font: pygame.font.Font,
    error_message: str | None = None,
) -> Path | None:
    screen = pygame.display.get_surface()
    button_rect = pygame.Rect((WINDOW_WIDTH - 240) // 2, (WINDOW_HEIGHT - 60) // 2, 240, 60)
    info_text = [
        "Main menu: import a song to start",
        "Click the button or press I to pick an MP3",
        "Press Esc to quit without playing",
        "Arrow keys hit notes once the round begins",
    ]

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_i:
                    selection = pick_song_with_dialog()
                    if selection:
                        return selection
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if button_rect.collidepoint(event.pos):
                    selection = pick_song_with_dialog()
                    if selection:
                        return selection

        screen.fill((18, 18, 26))
        pygame.draw.rect(screen, (70, 140, 255), button_rect, border_radius=8)
        pygame.draw.rect(screen, (200, 220, 255), button_rect, 2, border_radius=8)

        button_text = font.render("Import MP3", True, (10, 10, 10))
        screen.blit(
            button_text,
            button_text.get_rect(center=button_rect.center),
        )

        for idx, line in enumerate(info_text):
            surface = font.render(line, True, (200, 200, 200))
            screen.blit(surface, (WINDOW_WIDTH // 2 - surface.get_width() // 2, 140 + idx * 32))

        if error_message:
            error_surface = font.render(error_message, True, (255, 100, 100))
            screen.blit(
                error_surface,
                (WINDOW_WIDTH // 2 - error_surface.get_width() // 2, button_rect.bottom + 40),
            )

        pygame.display.flip()
        clock.tick(60)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play a quick arrow rhythm round from an MP3 file.")
    parser.add_argument("song", type=Path, nargs="?", help="Optional MP3 path. If omitted, an import dialog opens.")
    parser.add_argument(
        "--spawn-interval",
        type=int,
        default=SPAWN_INTERVAL_MS,
        help="Milliseconds between new arrows (default: %(default)s)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not pygame.get_init():
        pygame.init()
    if not pygame.mixer.get_init():
        pygame.mixer.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Arrow Rhythm Round")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 24)

    error_message: str | None = None
    song_path = Path(args.song).expanduser() if args.song else None

    while True:
        if song_path and song_path.exists():
            break

        if song_path and not song_path.exists():
            error_message = f"Song file not found: {song_path}"

        song_path = show_import_screen(clock, font, error_message=error_message)
        error_message = None

        if song_path is None:
            pygame.quit()
            return

        song_path = song_path.expanduser()

    round_ = RhythmRound(
        song_path=song_path,
        spawn_interval_ms=args.spawn_interval,
        screen=screen,
        clock=clock,
        font=font,
    )
    round_.run()
    pygame.quit()


if __name__ == "__main__":
    main()
