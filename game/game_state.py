import chess
from game.captured_tracker import CapturedTracker


class GameState:
    """
    Single source of truth for board position, terminal detection, and captured pieces.
    No rendering, no engine calls.
    """

    def __init__(self):
        self.board = chess.Board()
        self.game_over = False
        self.status_message = ""
        self.result: str | None = None  # 'white' | 'black' | 'draw' | None
        self.captured = CapturedTracker()

    def reset(self):
        self.board = chess.Board()
        self.game_over = False
        self.status_message = ""
        self.result = None
        self.captured.reset()

    def is_legal(self, move: chess.Move) -> bool:
        return move in self.board.legal_moves

    def push_move(self, move: chess.Move) -> bool:
        """Apply move if legal. Returns True on success."""
        if not self.is_legal(move):
            return False
        self.captured.record_move(self.board, move)
        self.board.push(move)
        self._detect_terminal()
        return True

    def _detect_terminal(self):
        if self.board.is_checkmate():
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            self.status_message = f"Checkmate! {winner} wins"
            self.result = "black" if self.board.turn == chess.WHITE else "white"
            self.game_over = True
        elif self.board.is_stalemate():
            self.status_message = "Stalemate! Draw"
            self.result = "draw"
            self.game_over = True
        elif self.board.is_insufficient_material():
            self.status_message = "Draw - insufficient material"
            self.result = "draw"
            self.game_over = True
        elif self.board.is_fifty_moves():
            self.status_message = "Draw - 50 move rule"
            self.result = "draw"
            self.game_over = True
