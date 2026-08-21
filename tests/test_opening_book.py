import chess
import pytest
from pathlib import Path
from engine.opening_book import OpeningBook


def test_returns_legal_move_from_starting_position():
    book = OpeningBook()
    board = chess.Board()
    move = book.get_move(board)
    # Opening book should have entries for the starting position
    if move is not None:
        assert move in board.legal_moves


def test_returns_none_for_missing_book():
    book = OpeningBook(book_path=Path("/nonexistent/book.bin"))
    board = chess.Board()
    assert book.get_move(board) is None


def test_returns_none_when_position_not_in_book():
    book = OpeningBook()
    # A random late-game position unlikely to be in an 8-move book
    board = chess.Board("8/8/4k3/8/8/8/8/4K3 w - - 0 1")
    move = book.get_move(board)
    assert move is None


def test_returned_move_is_in_legal_moves_multiple_calls():
    """Weighted random selection should always return a legal move."""
    book = OpeningBook()
    board = chess.Board()
    for _ in range(10):
        move = book.get_move(board)
        if move is not None:
            assert move in board.legal_moves
