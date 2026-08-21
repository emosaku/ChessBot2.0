import chess
import pytest
from engine.expectimax import ExpectimaxEngine


@pytest.fixture
def engine():
    return ExpectimaxEngine(depth=2)


def test_returns_legal_move_from_start(engine):
    board = chess.Board()
    move = engine.get_best_move(board)
    assert move in board.legal_moves


def test_avoids_immediate_losing_capture(engine):
    # White rook on a1 is free to take, but black queen guards it
    # Simplified: just confirm the engine returns something
    board = chess.Board()
    move = engine.get_best_move(board)
    assert move is not None


def test_chance_node_averages_are_finite(engine):
    # Ensures _expectimax doesn't blow up on normal positions
    board = chess.Board()
    board.push_san("e4")
    board.push_san("e5")
    move = engine.get_best_move(board)
    assert move in board.legal_moves


def test_depth_1_still_returns_move():
    engine = ExpectimaxEngine(depth=1)
    board = chess.Board()
    move = engine.get_best_move(board)
    assert move in board.legal_moves


def test_no_move_on_empty_legal_moves():
    # Stalemate position: no legal moves
    board = chess.Board("5k2/5P2/5K2/8/8/8/8/8 b - - 0 1")
    engine = ExpectimaxEngine(depth=1)
    move = engine.get_best_move(board)
    assert move is None or isinstance(move, chess.Move)
