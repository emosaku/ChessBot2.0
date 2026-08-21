import chess

PIECE_VALUES: dict[int, int] = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}

_SORT_ORDER = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]


class CapturedTracker:
    """
    Tracks pieces captured by each side and computes material advantage.
    white_captured = black pieces taken by white
    black_captured = white pieces taken by black
    """

    def __init__(self):
        self.white_captured: list[int] = []
        self.black_captured: list[int] = []

    def record_move(self, board: chess.Board, move: chess.Move):
        """Must be called BEFORE board.push(move)."""
        if board.is_en_passant(move):
            if board.turn == chess.WHITE:
                self.white_captured.append(chess.PAWN)
            else:
                self.black_captured.append(chess.PAWN)
        else:
            captured = board.piece_at(move.to_square)
            if captured:
                if captured.color == chess.BLACK:
                    self.white_captured.append(captured.piece_type)
                else:
                    self.black_captured.append(captured.piece_type)

    def reset(self):
        self.white_captured.clear()
        self.black_captured.clear()

    def white_score(self) -> int:
        return sum(PIECE_VALUES[p] for p in self.white_captured)

    def black_score(self) -> int:
        return sum(PIECE_VALUES[p] for p in self.black_captured)

    def advantage(self) -> int:
        """Positive = white leads, negative = black leads."""
        return self.white_score() - self.black_score()

    def sorted_white_captured(self) -> list[int]:
        return sorted(self.white_captured, key=lambda p: _SORT_ORDER.index(p) if p in _SORT_ORDER else 99)

    def sorted_black_captured(self) -> list[int]:
        return sorted(self.black_captured, key=lambda p: _SORT_ORDER.index(p) if p in _SORT_ORDER else 99)
