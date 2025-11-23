import argparse
import random
from pathlib import Path

import pygame


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
TARGET_Y = 480
ARROW_SPEED = 240  # pixels per second
SPAWN_INTERVAL_MS = 800

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
    def __init__(self, song_path: Path, spawn_interval_ms: int = SPAWN_INTERVAL_MS):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Arrow Rhythm Round")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 24)

        self.song_path = song_path
        self.spawn_interval_ms = spawn_interval_ms
        self.arrows: list[Arrow] = []
        self.last_spawn = 0
        self.running = True
        self.score = 0
        self.combo = 0
        self.misses = 0

    def start_music(self) -> None:
        pygame.mixer.music.load(self.song_path.as_posix())
        pygame.mixer.music.play()
        self.last_spawn = pygame.time.get_ticks()

    def spawn_arrow(self) -> None:
        direction = random.choice(list(ARROW_POSITIONS.keys()))
        self.arrows.append(Arrow(direction=direction, y=-50))

    def handle_key(self, direction: str) -> None:
        for arrow in sorted(self.arrows, key=lambda a: abs(a.y - TARGET_Y)):
            if arrow.direction != direction or arrow.hit:
                continue
            if abs(arrow.y - TARGET_Y) <= 48:
                arrow.hit = True
                self.score += 100
                self.combo += 1
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
            self.draw_arrow(temp_arrow, (80, 80, 80))

    def draw_stats(self) -> None:
        score_surface = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        combo_surface = self.font.render(f"Combo: {self.combo}", True, (255, 255, 0))
        miss_surface = self.font.render(f"Misses: {self.misses}", True, (255, 128, 128))
        self.screen.blit(score_surface, (20, 20))
        self.screen.blit(combo_surface, (20, 50))
        self.screen.blit(miss_surface, (20, 80))

    def tick(self) -> None:
        delta_seconds = self.clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key in ARROW_KEYS:
                self.handle_key(ARROW_KEYS[event.key])

        now = pygame.time.get_ticks()
        if now - self.last_spawn >= self.spawn_interval_ms:
            self.spawn_arrow()
            self.last_spawn = now

        self.update_arrows(delta_seconds)

        self.screen.fill((20, 20, 30))
        self.draw_targets()
        for arrow in self.arrows:
            color = (0, 200, 255) if not arrow.hit else (120, 255, 120)
            self.draw_arrow(arrow, color)
        pygame.draw.rect(self.screen, (40, 40, 60), (120, TARGET_Y - 48, 520, 96), 2)
        self.draw_stats()
        pygame.display.flip()

    def run(self) -> None:
        self.start_music()
        while self.running and (pygame.mixer.music.get_busy() or self.arrows):
            self.tick()
        pygame.quit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play a quick arrow rhythm round from an MP3 file.")
    parser.add_argument("song", type=Path, help="Path to an MP3 file to play")
    parser.add_argument(
        "--spawn-interval",
        type=int,
        default=SPAWN_INTERVAL_MS,
        help="Milliseconds between new arrows (default: %(default)s)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.song.exists():
        raise SystemExit(f"Song file not found: {args.song}")
    round_ = RhythmRound(song_path=args.song, spawn_interval_ms=args.spawn_interval)
    round_.run()


if __name__ == "__main__":
    main()
