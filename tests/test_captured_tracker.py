import chess
import pytest
from game.captured_tracker import CapturedTracker


@pytest.fixture
def tracker():
    return CapturedTracker()


def test_initial_state_empty(tracker):
    assert tracker.white_captured == []
    assert tracker.black_captured == []
    assert tracker.advantage() == 0


def test_reset_clears_state(tracker):
    tracker.white_captured.append(chess.QUEEN)
    tracker.black_captured.append(chess.ROOK)
    tracker.reset()
    assert tracker.white_captured == []
    assert tracker.black_captured == []


def test_white_captures_black_pawn(tracker):
    board = chess.Board()
    board.push_san("e4")
    board.push_san("d5")
    move = chess.Move.from_uci("e4d5")
    tracker.record_move(board, move)
    assert chess.PAWN in tracker.white_captured


def test_black_captures_white_pawn(tracker):
    board = chess.Board()
    board.push_san("e4")
    board.push_san("d5")
    board.push_san("Nf3")
    board.push_san("dxe4")
    # After those moves the last move was dxe4 (black capturing white pawn)
    # Let's just test record_move directly:
    board2 = chess.Board()
    board2.push_san("e4")
    board2.push_san("d5")
    board2.push_san("c4")
    # Now black can take c4 with d5xc4
    move = chess.Move.from_uci("d5c4")
    tracker.record_move(board2, move)
    assert chess.PAWN in tracker.black_captured


def test_no_capture_not_recorded(tracker):
    board = chess.Board()
    move = chess.Move.from_uci("e2e4")
    tracker.record_move(board, move)
    assert tracker.white_captured == []
    assert tracker.black_captured == []


def test_white_score(tracker):
    tracker.white_captured = [chess.PAWN, chess.QUEEN, chess.ROOK]
    assert tracker.white_score() == 1 + 9 + 5


def test_black_score(tracker):
    tracker.black_captured = [chess.BISHOP, chess.KNIGHT]
    assert tracker.black_score() == 3 + 3


def test_advantage_white_leads(tracker):
    tracker.white_captured = [chess.QUEEN]   # 9 pts
    tracker.black_captured = [chess.PAWN]    # 1 pt
    assert tracker.advantage() == 8


def test_advantage_black_leads(tracker):
    tracker.white_captured = [chess.PAWN]    # 1 pt
    tracker.black_captured = [chess.QUEEN]   # 9 pts
    assert tracker.advantage() == -8


def test_advantage_equal(tracker):
    tracker.white_captured = [chess.PAWN]
    tracker.black_captured = [chess.PAWN]
    assert tracker.advantage() == 0


def test_sorted_white_captured_order(tracker):
    tracker.white_captured = [chess.PAWN, chess.QUEEN, chess.ROOK, chess.KNIGHT]
    result = tracker.sorted_white_captured()
    assert result[0] == chess.QUEEN
    assert result[1] == chess.ROOK
    assert result[-1] == chess.PAWN


def test_game_state_tracks_captures_via_push_move():
    from game.game_state import GameState
    state = GameState()
    # Set up a position where white can capture on d5
    state.board.push_san("e4")
    state.board.push_san("d5")
    state.push_move(chess.Move.from_uci("e4d5"))
    assert chess.PAWN in state.captured.white_captured


def test_game_state_reset_clears_captures():
    from game.game_state import GameState
    state = GameState()
    state.board.push_san("e4")
    state.board.push_san("d5")
    state.push_move(chess.Move.from_uci("e4d5"))
    state.reset()
    assert state.captured.white_captured == []
