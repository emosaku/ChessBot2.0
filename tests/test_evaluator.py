import chess
import pytest
from engine.evaluator import BoardEvaluator, PSTEvaluator


@pytest.fixture
def evaluator():
    return BoardEvaluator()


@pytest.fixture
def pst():
    return PSTEvaluator()


# ------------------------------------------------------------------ BoardEvaluator (base)

def test_starting_position_is_equal(evaluator):
    assert evaluator.evaluate(chess.Board()) == 0


def test_white_extra_pawn_is_positive(evaluator):
    board = chess.Board()
    board.remove_piece_at(chess.E7)
    assert evaluator.evaluate(board) > 0


def test_black_extra_queen_is_negative(evaluator):
    board = chess.Board()
    board.remove_piece_at(chess.D1)
    assert evaluator.evaluate(board) < 0


def test_stalemate_is_zero(evaluator):
    board = chess.Board("5k2/5P2/5K2/8/8/8/8/8 b - - 0 1")
    assert evaluator.evaluate(board) == 0


def test_checkmate_white_loses(evaluator):
    board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
    assert evaluator.evaluate(board) == -99999


def test_insufficient_material_is_draw(evaluator):
    board = chess.Board("k7/8/8/8/8/8/8/K7 w - - 0 1")
    assert evaluator.evaluate(board) == 0


# ------------------------------------------------------------------ PSTEvaluator

def test_pst_starting_position_is_equal(pst):
    # Symmetric starting position must score 0
    assert pst.evaluate(chess.Board()) == 0


def test_pst_white_extra_pawn_positive(pst):
    board = chess.Board()
    board.remove_piece_at(chess.E7)
    assert pst.evaluate(board) > 0


def test_pst_black_extra_queen_negative(pst):
    board = chess.Board()
    board.remove_piece_at(chess.D1)
    assert pst.evaluate(board) < 0


def test_pst_stalemate_is_zero(pst):
    board = chess.Board("5k2/5P2/5K2/8/8/8/8/8 b - - 0 1")
    assert pst.evaluate(board) == 0


def test_pst_checkmate_white_loses(pst):
    board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
    assert pst.evaluate(board) == -99999


def test_pst_centralised_knight_scores_higher(pst):
    # Same material, only knight placement differs: e4 (central) vs b1 (corner).
    # Add pawns so the position is not insufficient-material (KNK is a draw).
    board_central = chess.Board("8/pppppppp/8/8/4N3/8/PPPPPPPP/K6k w - - 0 1")
    board_corner  = chess.Board("8/pppppppp/8/8/8/8/PPPPPPPP/KN5k w - - 0 1")
    assert pst.evaluate(board_central) > pst.evaluate(board_corner)


def test_pst_doubled_pawn_penalty(pst):
    # Two white pawns on the same file should score worse than two on different files
    board_doubled  = chess.Board("k7/8/8/8/8/P7/P7/K7 w - - 0 1")
    board_spread   = chess.Board("k7/8/8/8/8/P7/1P6/K7 w - - 0 1")
    assert pst.evaluate(board_spread) > pst.evaluate(board_doubled)


def test_pst_passed_pawn_bonus(pst):
    # A passed pawn on rank 6 should score higher than one on rank 2
    board_advanced = chess.Board("k7/P7/8/8/8/8/8/K7 w - - 0 1")
    board_early    = chess.Board("k7/8/8/8/8/8/P7/K7 w - - 0 1")
    assert pst.evaluate(board_advanced) > pst.evaluate(board_early)


def test_pst_isolated_pawn_penalty(pst):
    # Isolated pawn should score worse than a supported pawn
    board_isolated = chess.Board("k7/8/8/8/8/8/P6P/K7 w - - 0 1")  # both isolated
    board_connected = chess.Board("k7/8/8/8/8/8/PP6/K7 w - - 0 1")  # connected
    assert pst.evaluate(board_connected) > pst.evaluate(board_isolated)
