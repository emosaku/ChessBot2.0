import chess
import pytest
from game.game_state import GameState
from game.game_controller import GameController
from engine.minimax import AlphaBetaEngine


@pytest.fixture
def controller():
    state = GameState()
    engine = AlphaBetaEngine(depth=1)
    return GameController(state, engine, chess.WHITE)


def test_player_turn_at_start(controller):
    assert controller.is_player_turn()


def test_apply_player_move_advances_board(controller):
    move = chess.Move.from_uci("e2e4")
    result = controller.apply_player_move(move)
    assert result is True
    assert not controller.is_player_turn()  # now engine's turn


def test_apply_illegal_player_move_rejected(controller):
    move = chess.Move.from_uci("e2e5")
    assert controller.apply_player_move(move) is False


def test_engine_move_not_allowed_on_player_turn(controller):
    assert controller.apply_engine_move() is None


def test_engine_move_applied_after_player_move(controller):
    controller.apply_player_move(chess.Move.from_uci("e2e4"))
    engine_move = controller.apply_engine_move()
    assert engine_move is not None
    assert isinstance(engine_move, chess.Move)


def test_no_moves_after_game_over(controller):
    # Trigger fool's mate
    for uci in ["f2f3", "e7e5", "g2g4", "d8h4"]:
        controller.state.push_move(chess.Move.from_uci(uci))
    assert controller.state.game_over
    assert controller.apply_player_move(chess.Move.from_uci("a2a3")) is False
    assert controller.apply_engine_move() is None
