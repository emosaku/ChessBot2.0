import chess.polyglot
import random
from pathlib import Path

_DEFAULT_BOOK = Path(__file__).parent.parent / "assets" / "books" / "8moves_v3.bin"


class OpeningBook:
    """Weighted random selection from a Polyglot opening book."""

    def __init__(self, book_path: Path = _DEFAULT_BOOK):
        self._path = Path(book_path)
        self._reader = chess.polyglot.open_reader(str(self._path)) if self._path.exists() else None

    def get_move(self, board: chess.Board) -> chess.Move | None:
        if self._reader is None:
            return None
        try:
            entries = list(self._reader.find_all(board))
            if not entries:
                return None
            total = sum(e.weight for e in entries)
            rand = random.uniform(0, total)
            for entry in entries:
                rand -= entry.weight
                if rand <= 0:
                    return entry.move
            return entries[0].move
        except Exception:
            return None

    def close(self):
        if self._reader:
            self._reader.close()
