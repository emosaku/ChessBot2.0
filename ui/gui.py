import pygame
import chess
from pathlib import Path

from engine.minimax import AlphaBetaEngine
from engine.expectimax import ExpectimaxEngine
from game.game_state import GameState
from game.game_controller import GameController
from ui.constants import WIDTH, HEIGHT, SQUARE_SIZE, MENU_BUTTON_RECTS
from ui.renderer import BoardRenderer
from ui.event_handler import EventHandler, EventResult
from ui.piece_loader import PieceLoader
from ui.promotion_handler import PromotionHandler
from ui.animation import MoveAnimation

_MENU_OPTIONS = [
    ("Minimax", chess.WHITE),
    ("Minimax", chess.BLACK),
]


class ChessGameGUI:
    """
    Top-level coordinator: wires together renderer, event handler, game state,
    controller, and animation. Contains no game logic itself.
    """

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess Engine")
        self.clock = pygame.time.Clock()

        images_dir = Path(__file__).parent / 'images'
        piece_images = PieceLoader.load(images_dir)
        small_images = PieceLoader.load_small(images_dir)
        bg_image = self._load_bg(images_dir / 'beach_bg.jpg')

        self.renderer = BoardRenderer(self.screen, piece_images, small_images, bg_image)
        self.events = EventHandler()

        self.state = GameState()
        self.controller: GameController | None = None
        self.selected_square: int | None = None
        self.screen_state = "MENU"
        self.animation: MoveAnimation | None = None

    # -------------------------------------------------------------- lifecycle

    def run(self):
        while True:
            if self.screen_state == "MENU":
                self._tick_menu()
            else:
                self._tick_game()
            pygame.display.flip()
            self.clock.tick(60)

    # -------------------------------------------------------------- helpers

    @staticmethod
    def _load_bg(path: Path) -> pygame.Surface | None:
        if not path.exists():
            return None
        img = pygame.image.load(str(path)).convert()
        return pygame.transform.smoothscale(img, (WIDTH, HEIGHT))

    @staticmethod
    def _piece_key(board: chess.Board, square: int) -> str | None:
        piece = board.piece_at(square)
        if not piece:
            return None
        return ('w' if piece.color == chess.WHITE else 'b') + piece.symbol().upper()

    @staticmethod
    def _hovered_button(pos: tuple[int, int]) -> int | None:
        for i, (x, y, w, h) in enumerate(MENU_BUTTON_RECTS):
            if x <= pos[0] <= x + w and y <= pos[1] <= y + h:
                return i
        return None

    # -------------------------------------------------------------- menu

    def _tick_menu(self):
        hover_idx = self._hovered_button(pygame.mouse.get_pos())

        for result, data in self.events.process_menu_events():
            if result == EventResult.KEY_PRESSED:
                mapping = {pygame.K_1: 0, pygame.K_2: 1}
                if data in mapping:
                    self._start_game(*_MENU_OPTIONS[mapping[data]])
            elif result == EventResult.MENU_CLICKED:
                idx = self._hovered_button(data)
                if idx is not None:
                    self._start_game(*_MENU_OPTIONS[idx])

        self.renderer.draw_menu(hovered_idx=hover_idx)

    def _start_game(self, engine_name: str, player_color: chess.Color):
        self.state.reset()
        engine = AlphaBetaEngine(depth=5) if engine_name == "Minimax" else ExpectimaxEngine(depth=2)
        self.controller = GameController(self.state, engine, player_color)
        self.selected_square = None
        self.animation = None
        self.screen_state = "PLAYING"
        self.state.status_message = (
            "Your move" if self.state.board.turn == player_color else "Engine thinking..."
        )
        if not self.controller.is_player_turn():
            pygame.time.set_timer(pygame.USEREVENT, 500)

    # -------------------------------------------------------------- game

    def _tick_game(self):
        animating = self.animation is not None and not self.animation.done
        if animating:
            self.animation.advance()
            animating = not self.animation.done  # re-check after advance

        for result, data in self.events.process_game_events():
            if result == EventResult.KEY_PRESSED and data == pygame.K_r:
                self.animation = None
                self.screen_state = "MENU"
                return
            if result == EventResult.SQUARE_CLICKED and not animating and not self.state.game_over:
                if self.controller.is_player_turn():
                    self._handle_square(data)
            if result == EventResult.ENGINE_TIMER and not animating:
                self._run_engine()

        # Re-evaluate: _handle_square may have just started a new animation this tick.
        still_animating = self.animation is not None and not self.animation.done
        if not still_animating and not self.state.game_over and not self.controller.is_player_turn():
            self._run_engine()

        eval_score = self.controller.engine.evaluator.evaluate(self.state.board)
        anim = self.animation if (self.animation and not self.animation.done) else None
        self.renderer.draw_board(self.state.board, self.selected_square, anim)
        self.renderer.draw_sidebar(
            self.state.board, eval_score,
            self.state.status_message,
            self.controller.engine.name,
            self.state.captured,
        )

    def _handle_square(self, square: int):
        if self.selected_square is None:
            piece = self.state.board.piece_at(square)
            if piece and piece.color == self.controller.player_color:
                self.selected_square = square
        else:
            move = chess.Move(self.selected_square, square)
            if PromotionHandler.is_promotion(self.state.board, move):
                move = PromotionHandler.with_queen_promotion(move)

            if self.controller.apply_player_move(move):
                # Board is now updated: piece is at move.to_square
                key = self._piece_key(self.state.board, move.to_square)
                if key:
                    self.animation = MoveAnimation(key, move.from_square, move.to_square)
                self.selected_square = None
                self.state.status_message = "Engine thinking..."
            else:
                self.selected_square = None

    def _run_engine(self):
        move = self.controller.apply_engine_move()
        if move:
            key = self._piece_key(self.state.board, move.to_square)
            if key:
                self.animation = MoveAnimation(key, move.from_square, move.to_square)
        if not self.state.game_over:
            self.state.status_message = "Your move"
