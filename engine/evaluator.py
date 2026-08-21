import chess


class BoardEvaluator:
    """
    Pure material balance only.
    Positive score = good for white, negative = good for black.
    """

    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 0,
    }

    def evaluate(self, board: chess.Board) -> float:
        if board.is_checkmate():
            return -99999 if board.turn == chess.WHITE else 99999
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        value = 0
        for piece_type, piece_value in self.PIECE_VALUES.items():
            value += len(board.pieces(piece_type, chess.WHITE)) * piece_value
            value -= len(board.pieces(piece_type, chess.BLACK)) * piece_value
        return value


# ---------------------------------------------------------------------------
# Piece-square tables (from white's perspective, a1=index 0, h8=index 63)
# Source: chessprogramming.org / Toga II / standard beginner PST values
# ---------------------------------------------------------------------------

# fmt: off
_PST_PAWN = [
     0,   0,   0,   0,   0,   0,   0,   0,
    50,  50,  50,  50,  50,  50,  50,  50,
    10,  10,  20,  30,  30,  20,  10,  10,
     5,   5,  10,  25,  25,  10,   5,   5,
     0,   0,   0,  20,  20,   0,   0,   0,
     5,  -5, -10,   0,   0, -10,  -5,   5,
     5,  10,  10, -20, -20,  10,  10,   5,
     0,   0,   0,   0,   0,   0,   0,   0,
]

_PST_KNIGHT = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,   0,   0,   0,   0, -20, -40,
    -30,   0,  10,  15,  15,  10,   0, -30,
    -30,   5,  15,  20,  20,  15,   5, -30,
    -30,   0,  15,  20,  20,  15,   0, -30,
    -30,   5,  10,  15,  15,  10,   5, -30,
    -40, -20,   0,   5,   5,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]

_PST_BISHOP = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,  10,  10,   5,   0, -10,
    -10,   5,   5,  10,  10,   5,   5, -10,
    -10,   0,  10,  10,  10,  10,   0, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]

_PST_ROOK = [
     0,   0,   0,   0,   0,   0,   0,   0,
     5,  10,  10,  10,  10,  10,  10,   5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
     0,   0,   0,   5,   5,   0,   0,   0,
]

_PST_QUEEN = [
    -20, -10, -10,  -5,  -5, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,   5,   5,   5,   0, -10,
     -5,   0,   5,   5,   5,   5,   0,  -5,
      0,   0,   5,   5,   5,   5,   0,  -5,
    -10,   5,   5,   5,   5,   5,   0, -10,
    -10,   0,   5,   0,   0,   0,   0, -10,
    -20, -10, -10,  -5,  -5, -10, -10, -20,
]

# King wants to castle and stay behind pawns in the middlegame
_PST_KING_MG = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
     20,  20,   0,   0,   0,   0,  20,  20,
     20,  30,  10,   0,   0,  10,  30,  20,
]

# King wants to centralize in the endgame
_PST_KING_EG = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10,   0,   0, -10, -20, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -30,   0,   0,   0,   0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50,
]
# fmt: on

# Precompute mirrored tables for black (flip rank)
def _mirror(table: list[int]) -> list[int]:
    mirrored = []
    for rank in range(7, -1, -1):
        mirrored.extend(table[rank * 8 : rank * 8 + 8])
    return mirrored


_PST: dict[tuple, list[int]] = {
    (chess.PAWN,   chess.WHITE): _PST_PAWN,
    (chess.PAWN,   chess.BLACK): _mirror(_PST_PAWN),
    (chess.KNIGHT, chess.WHITE): _PST_KNIGHT,
    (chess.KNIGHT, chess.BLACK): _mirror(_PST_KNIGHT),
    (chess.BISHOP, chess.WHITE): _PST_BISHOP,
    (chess.BISHOP, chess.BLACK): _mirror(_PST_BISHOP),
    (chess.ROOK,   chess.WHITE): _PST_ROOK,
    (chess.ROOK,   chess.BLACK): _mirror(_PST_ROOK),
    (chess.QUEEN,  chess.WHITE): _PST_QUEEN,
    (chess.QUEEN,  chess.BLACK): _mirror(_PST_QUEEN),
    # King tables are phase-dependent; stored separately
    (chess.KING,   chess.WHITE, "mg"): _PST_KING_MG,
    (chess.KING,   chess.BLACK, "mg"): _mirror(_PST_KING_MG),
    (chess.KING,   chess.WHITE, "eg"): _PST_KING_EG,
    (chess.KING,   chess.BLACK, "eg"): _mirror(_PST_KING_EG),
}

# Non-pawn material threshold below which we consider it the endgame
_ENDGAME_MATERIAL_THRESHOLD = 1300  # approx rook + minor piece each side


class PSTEvaluator(BoardEvaluator):
    """
    Material balance + piece-square tables + pawn structure + phase-aware king safety.
    Drop-in replacement for BoardEvaluator — same sign convention.
    """

    def evaluate(self, board: chess.Board) -> float:
        if board.is_checkmate():
            return -99999 if board.turn == chess.WHITE else 99999
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        phase = self._game_phase(board)
        score = 0
        score += self._material_and_pst(board, phase)
        score += self._pawn_structure(board)
        return score

    # ------------------------------------------------------------------ phase

    def _game_phase(self, board: chess.Board) -> str:
        non_pawn = sum(
            len(board.pieces(pt, color)) * v
            for pt, v in [(chess.KNIGHT, 320), (chess.BISHOP, 330),
                          (chess.ROOK, 500), (chess.QUEEN, 900)]
            for color in (chess.WHITE, chess.BLACK)
        )
        return "eg" if non_pawn <= _ENDGAME_MATERIAL_THRESHOLD else "mg"

    # ------------------------------------------------------------------ material + PST

    def _material_and_pst(self, board: chess.Board, phase: str) -> float:
        score = 0
        for color in (chess.WHITE, chess.BLACK):
            sign = 1 if color == chess.WHITE else -1
            for piece_type, base_value in self.PIECE_VALUES.items():
                for square in board.pieces(piece_type, color):
                    score += sign * base_value
                    if piece_type == chess.KING:
                        table = _PST[(chess.KING, color, phase)]
                    else:
                        table = _PST[(piece_type, color)]
                    score += sign * table[square]
        return score

    # ------------------------------------------------------------------ pawn structure

    def _pawn_structure(self, board: chess.Board) -> float:
        score = 0
        for color in (chess.WHITE, chess.BLACK):
            sign = 1 if color == chess.WHITE else -1
            pawns = board.pieces(chess.PAWN, color)
            opp_pawns = board.pieces(chess.PAWN, not color)

            files_with_pawns: dict[int, int] = {}
            for sq in pawns:
                f = chess.square_file(sq)
                files_with_pawns[f] = files_with_pawns.get(f, 0) + 1

            for sq in pawns:
                f = chess.square_file(sq)
                r = chess.square_rank(sq)

                # Doubled pawn penalty
                if files_with_pawns[f] > 1:
                    score += sign * (-20)

                # Isolated pawn penalty (no friendly pawns on adjacent files)
                has_neighbor = (
                    (f > 0 and (f - 1) in files_with_pawns) or
                    (f < 7 and (f + 1) in files_with_pawns)
                )
                if not has_neighbor:
                    score += sign * (-15)

                # Passed pawn bonus (no opposing pawns ahead on same or adjacent files)
                passed = True
                ahead = range(r + 1, 8) if color == chess.WHITE else range(r - 1, -1, -1)
                for opp_sq in opp_pawns:
                    opp_f = chess.square_file(opp_sq)
                    opp_r = chess.square_rank(opp_sq)
                    if abs(opp_f - f) <= 1 and opp_r in ahead:
                        passed = False
                        break
                if passed:
                    # Bonus scales with how far advanced the pawn is
                    advancement = r if color == chess.WHITE else (7 - r)
                    score += sign * (20 + advancement * 10)

        return score
