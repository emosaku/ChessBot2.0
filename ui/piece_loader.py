import pygame
import sys
from pathlib import Path
from ui.constants import SQUARE_SIZE, SMALL_ICON_SIZE

_PIECE_CODES = [
    'wP', 'wN', 'wB', 'wR', 'wQ', 'wK',
    'bP', 'bN', 'bB', 'bR', 'bQ', 'bK',
]


class PieceLoader:
    """Loads and scales piece PNGs from a given directory."""

    @staticmethod
    def load(images_dir: Path, square_size: int = SQUARE_SIZE) -> dict[str, pygame.Surface]:
        """Full-size pieces with alpha transparency preserved."""
        images: dict[str, pygame.Surface] = {}
        for code in _PIECE_CODES:
            path = images_dir / f'{code}.png'
            if not path.exists():
                print(f"ERROR: Missing piece image {path}")
                sys.exit(1)
            img = pygame.image.load(str(path)).convert_alpha()
            images[code] = pygame.transform.smoothscale(img, (square_size - 10, square_size - 10))
        return images

    @staticmethod
    def load_small(images_dir: Path, size: int = SMALL_ICON_SIZE) -> dict[str, pygame.Surface]:
        """Tiny icons for the captured-pieces sidebar display."""
        images: dict[str, pygame.Surface] = {}
        for code in _PIECE_CODES:
            path = images_dir / f'{code}.png'
            if not path.exists():
                continue
            img = pygame.image.load(str(path)).convert_alpha()
            images[code] = pygame.transform.smoothscale(img, (size, size))
        return images
