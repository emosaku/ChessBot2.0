import chess
import pytest
from ui.promotion_handler import PromotionHandler


def test_white_pawn_on_7th_rank_is_promotion():
    board = chess.Board()
    board.set_piece_at(chess.A7, chess.Piece(chess.PAWN, chess.WHITE))
    move = chess.Move(chess.A7, chess.A8)
    assert PromotionHandler.is_promotion(board, move) is True


def test_black_pawn_on_2nd_rank_is_promotion():
    board = chess.Board()
    board.set_piece_at(chess.H2, chess.Piece(chess.PAWN, chess.BLACK))
    move = chess.Move(chess.H2, chess.H1)
    assert PromotionHandler.is_promotion(board, move) is True


def test_white_pawn_not_on_7th_is_not_promotion():
    board = chess.Board()
    board.set_piece_at(chess.E2, chess.Piece(chess.PAWN, chess.WHITE))
    move = chess.Move(chess.E2, chess.E4)
    assert PromotionHandler.is_promotion(board, move) is False


def test_non_pawn_piece_is_not_promotion():
    board = chess.Board()
    board.set_piece_at(chess.E7, chess.Piece(chess.QUEEN, chess.WHITE))
    move = chess.Move(chess.E7, chess.E8)
    assert PromotionHandler.is_promotion(board, move) is False


def test_with_queen_promotion_sets_queen():
    move = chess.Move(chess.A7, chess.A8)
    promoted = PromotionHandler.with_queen_promotion(move)
    assert promoted.promotion == chess.QUEEN
    assert promoted.from_square == chess.A7
    assert promoted.to_square == chess.A8


def test_empty_square_is_not_promotion():
    board = chess.Board()
    board.clear()
    move = chess.Move(chess.A7, chess.A8)
    assert PromotionHandler.is_promotion(board, move) is False
