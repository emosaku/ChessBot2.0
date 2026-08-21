import chess
from engine.base_engine import BaseEngine
from engine.evaluator import BoardEvaluator
from engine.opening_book import OpeningBook


class ExpectimaxEngine(BaseEngine):
    """
    Expectimax search: opponent modeled as a chance node (average over all replies)
    rather than a minimizing player. Less accurate than minimax for chess, but
    useful for comparison and testing probabilistic behavior.
    """

    def __init__(self, depth: int = 2, evaluator: BoardEvaluator = None):
        super().__init__(depth, evaluator)
        self.name = "Expectimax"
        self._book = OpeningBook()

    def get_best_move(self, board: chess.Board) -> chess.Move:
        book_move = self._book.get_move(board)
        if book_move and book_move in board.legal_moves:
            return book_move
        return self._search(board)

    def _search(self, board: chess.Board) -> chess.Move:
        best_move = None
        best_value = float('-inf')
        for move in board.legal_moves:
            board.push(move)
            value = self._expectimax(board, self.depth - 1, False)
            board.pop()
            if value > best_value:
                best_value = value
                best_move = move
        return best_move

    def _expectimax(self, board: chess.Board, depth: int, is_max: bool) -> float:
        if depth == 0 or board.is_game_over():
            return self.evaluator.evaluate(board)

        if is_max:
            max_eval = float('-inf')
            for move in board.legal_moves:
                board.push(move)
                val = self._expectimax(board, depth - 1, False)
                board.pop()
                max_eval = max(max_eval, val)
            return max_eval
        else:
            moves = list(board.legal_moves)
            if not moves:
                return self.evaluator.evaluate(board)
            total = 0
            for move in moves:
                board.push(move)
                total += self._expectimax(board, depth - 1, True)
                board.pop()
            return total / len(moves)
