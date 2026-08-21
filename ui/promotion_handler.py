import chess


class PromotionHandler:
    """Detects pawn promotions and applies a default queen promotion."""

    @staticmethod
    def is_promotion(board: chess.Board, move: chess.Move) -> bool:
        piece = board.piece_at(move.from_square)
        if not piece or piece.piece_type != chess.PAWN:
            return False
        rank = chess.square_rank(move.to_square)
        return (piece.color == chess.WHITE and rank == 7) or (piece.color == chess.BLACK and rank == 0)

    @staticmethod
    def with_queen_promotion(move: chess.Move) -> chess.Move:
        return chess.Move(move.from_square, move.to_square, promotion=chess.QUEEN)
