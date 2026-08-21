import chess
from engine.base_engine import BaseEngine
from engine.evaluator import BoardEvaluator
from engine.opening_book import OpeningBook


class AlphaBetaEngine(BaseEngine):
    """Alpha-beta pruned minimax search."""

    def __init__(self, depth: int = 4, evaluator: BoardEvaluator = None):
        super().__init__(depth, evaluator)
        self.name = "AlphaBeta"
        self._book = OpeningBook()

    def get_best_move(self, board: chess.Board) -> chess.Move:
        book_move = self._book.get_move(board)
        if book_move and book_move in board.legal_moves:
            return book_move
        return self._search(board)

    def _search(self, board: chess.Board) -> chess.Move:
        best_move = None
        if board.turn == chess.WHITE:
            best_value = float('-inf')
            for move in board.legal_moves:
                board.push(move)
                value = self._alphabeta(board, self.depth - 1, float('-inf'), float('inf'), False)
                board.pop()
                if value > best_value:
                    best_value = value
                    best_move = move
        else:
            best_value = float('inf')
            for move in board.legal_moves:
                board.push(move)
                value = self._alphabeta(board, self.depth - 1, float('-inf'), float('inf'), True)
                board.pop()
                if value < best_value:
                    best_value = value
                    best_move = move
        return best_move

    def _alphabeta(self, board: chess.Board, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        if depth == 0 or board.is_game_over():
            return self.evaluator.evaluate(board)

        if maximizing:
            max_eval = float('-inf')
            for move in board.legal_moves:
                board.push(move)
                val = self._alphabeta(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, val)
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in board.legal_moves:
                board.push(move)
                val = self._alphabeta(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, val)
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return min_eval
