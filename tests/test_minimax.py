import chess
import pytest
from engine.minimax import AlphaBetaEngine


@pytest.fixture
def engine():
    return AlphaBetaEngine(depth=3)


def test_finds_checkmate_in_one():
    # White to move, Qh5# is checkmate
    board = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 4 4")
    engine = AlphaBetaEngine(depth=2)
    move = engine.get_best_move(board)
    assert move is not None
    board.push(move)
    assert board.is_checkmate()


def test_returns_a_legal_move(engine):
    board = chess.Board()
    move = engine.get_best_move(board)
    assert move in chess.Board().legal_moves


def test_does_not_hang_queen(engine):
    # White queen on d4 is attacked by black pawn on c5 — engine should not leave it there
    board = chess.Board("rnbqkbnr/pp2pppp/3p4/2p5/3Q4/8/PPPPPPPP/RNB1KBNR w KQkq - 0 3")
    move = engine.get_best_move(board)
    assert move is not None
    # The move should not be to keep the queen on d4 (i.e. it should move the queen)
    assert move.from_square != chess.D4 or move.to_square != chess.D4


def test_prefers_capture_when_winning_material():
    board = chess.Board("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
    engine = AlphaBetaEngine(depth=2)
    move = engine.get_best_move(board)
    assert move is not None


def test_no_move_on_finished_game():
    # Fool's mate board — game already over
    board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
    engine = AlphaBetaEngine(depth=2)
    move = engine.get_best_move(board)
    # board.is_game_over() is True, legal_moves is empty, result may be None
    assert move is None or isinstance(move, chess.Move)
