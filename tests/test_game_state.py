import chess
import pytest
from game.game_state import GameState


@pytest.fixture
def state():
    return GameState()


def test_initial_state(state):
    assert not state.game_over
    assert state.result is None
    assert state.board == chess.Board()


def test_push_legal_move_returns_true(state):
    move = chess.Move.from_uci("e2e4")
    assert state.push_move(move) is True
    assert state.board.peek() == move


def test_push_illegal_move_returns_false(state):
    illegal = chess.Move.from_uci("e2e5")
    assert state.push_move(illegal) is False


def test_reset_clears_board(state):
    state.push_move(chess.Move.from_uci("e2e4"))
    state.reset()
    assert state.board == chess.Board()
    assert not state.game_over


def test_checkmate_detected(state):
    # Fool's mate
    for uci in ["f2f3", "e7e5", "g2g4", "d8h4"]:
        state.push_move(chess.Move.from_uci(uci))
    assert state.game_over
    assert state.result == "black"
    assert "Checkmate" in state.status_message


def test_stalemate_detected(state):
    # A known stalemate FEN
    state.board = chess.Board("5k2/5P2/5K2/8/8/8/8/8 b - - 0 1")
    state._detect_terminal()
    assert state.game_over
    assert state.result == "draw"


def test_insufficient_material_draw(state):
    state.board = chess.Board("k7/8/8/8/8/8/8/K7 w - - 0 1")
    state._detect_terminal()
    assert state.game_over
    assert state.result == "draw"
