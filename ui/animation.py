import chess
from ui.constants import SQUARE_SIZE


class MoveAnimation:
    """
    Interpolates a piece image from one board square to another over FRAMES ticks.
    The board is already updated when animation starts — the renderer skips drawing
    the piece at to_square and instead draws it at the animated position.
    """

    FRAMES = 14  # ~230 ms at 60 fps

    def __init__(self, piece_key: str, from_sq: int, to_sq: int, square_size: int = SQUARE_SIZE):
        self.piece_key = piece_key
        self.to_square = to_sq

        self._from_x = float(chess.square_file(from_sq) * square_size)
        self._from_y = float((7 - chess.square_rank(from_sq)) * square_size)
        self._to_x   = float(chess.square_file(to_sq)   * square_size)
        self._to_y   = float((7 - chess.square_rank(to_sq))   * square_size)

        self.frame = 0

    @property
    def done(self) -> bool:
        return self.frame >= self.FRAMES

    def advance(self):
        self.frame = min(self.frame + 1, self.FRAMES)

    def current_topleft(self) -> tuple[float, float]:
        """Top-left pixel of the animating square at this frame (smoothstep eased)."""
        t = self.frame / self.FRAMES
        t = t * t * (3.0 - 2.0 * t)  # smooth-step: ease in and out
        x = self._from_x + (self._to_x - self._from_x) * t
        y = self._from_y + (self._to_y - self._from_y) * t
        return x, y
