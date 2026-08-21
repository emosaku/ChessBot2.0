import chess
from game.game_state import GameState
from engine.base_engine import BaseEngine


class GameController:
    """
    Orchestrates whose turn it is and routes moves to the right handler.
    Knows about the engine and the player color; knows nothing about rendering.
    """

    def __init__(self, state: GameState, engine: BaseEngine, player_color: chess.Color):
        self.state = state
        self.engine = engine
        self.player_color = player_color

    def is_player_turn(self) -> bool:
        return self.state.board.turn == self.player_color

    def apply_player_move(self, move: chess.Move) -> bool:
        """Returns True if the move was accepted."""
        if not self.is_player_turn() or self.state.game_over:
            return False
        return self.state.push_move(move)

    def apply_engine_move(self) -> chess.Move | None:
        """Asks the engine for a move and applies it. Returns the move or None."""
        if self.is_player_turn() or self.state.game_over:
            return None
        move = self.engine.get_best_move(self.state.board)
        if move:
            self.state.push_move(move)
        return move
