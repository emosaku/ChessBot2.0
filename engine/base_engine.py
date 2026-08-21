from abc import ABC, abstractmethod
import chess
from engine.evaluator import BoardEvaluator, PSTEvaluator


class BaseEngine(ABC):
    """Abstract interface all search engines must satisfy."""

    def __init__(self, depth: int = 2, evaluator: BoardEvaluator = None):
        self.depth = depth
        self.name = "Base"
        self.evaluator = evaluator or PSTEvaluator()

    @abstractmethod
    def get_best_move(self, board: chess.Board) -> chess.Move:
        """Return the best move for the current position."""
        pass
