import pygame
import chess
from pathlib import Path

from ui.constants import (
    BOARD_SIZE, SQUARE_SIZE, SIDEBAR_WIDTH, WIDTH, HEIGHT,
    LIGHT_SQUARE, DARK_SQUARE, HIGHLIGHT,
    BG_COLOR, TEXT_COLOR, DIM_COLOR, GOLD_COLOR, DIVIDER_COLOR,
    ADV_WHITE, ADV_BLACK,
    BTN_FILL, BTN_FILL_HOVER, BTN_BORDER, BTN_KEY_BG, BTN_TEXT,
    SMALL_ICON_SIZE, SMALL_ICON_GAP,
    MENU_BUTTON_RECTS, MENU_BUTTON_LABELS,
)
from ui.animation import MoveAnimation
from game.captured_tracker import CapturedTracker


class BoardRenderer:
    """
    Draws everything on screen. Holds no game state — all data arrives as arguments.
    """

    _PIECE_SYMBOL = {
        chess.PAWN: 'P', chess.KNIGHT: 'N', chess.BISHOP: 'B',
        chess.ROOK: 'R', chess.QUEEN: 'Q', chess.KING: 'K',
    }

    def __init__(
        self,
        screen: pygame.Surface,
        piece_images: dict[str, pygame.Surface],
        small_images: dict[str, pygame.Surface],
        bg_image: pygame.Surface | None = None,
    ):
        self.screen = screen
        self.piece_images = piece_images
        self.small_images = small_images
        self.bg_image = bg_image  # beach painting, scaled to (WIDTH, HEIGHT)

        self.font_lg   = pygame.font.SysFont('Georgia', 28, bold=True)
        self.font_md   = pygame.font.SysFont('Arial', 19)
        self.font_sm   = pygame.font.SysFont('Arial', 15)
        self.font_key  = pygame.font.SysFont('Arial', 22, bold=True)
        self.font_btn  = pygame.font.SysFont('Georgia', 17)

    # ------------------------------------------------------------------ board

    def draw_board(
        self,
        board: chess.Board,
        selected_square: int | None = None,
        animation: MoveAnimation | None = None,
    ):
        self._draw_squares(selected_square)
        skip = animation.to_square if (animation and not animation.done) else None
        self._draw_pieces(board, skip_square=skip)
        if animation and not animation.done:
            self._draw_animated_piece(animation)

    def _draw_squares(self, selected_square: int | None):
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(
                    self.screen, color,
                    (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE),
                )
        if selected_square is not None:
            col = chess.square_file(selected_square)
            row = 7 - chess.square_rank(selected_square)
            pygame.draw.rect(
                self.screen, HIGHLIGHT,
                (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 4,
            )

    def _draw_pieces(self, board: chess.Board, skip_square: int | None = None):
        for square in chess.SQUARES:
            if skip_square is not None and square == skip_square:
                continue
            piece = board.piece_at(square)
            if piece:
                img = self._piece_img(piece)
                col = chess.square_file(square)
                row = 7 - chess.square_rank(square)
                pad = (SQUARE_SIZE - img.get_width()) // 2
                self.screen.blit(img, (col * SQUARE_SIZE + pad, row * SQUARE_SIZE + pad))

    def _draw_animated_piece(self, animation: MoveAnimation):
        img = self.piece_images.get(animation.piece_key)
        if not img:
            return
        x, y = animation.current_topleft()
        pad = (SQUARE_SIZE - img.get_width()) // 2
        self.screen.blit(img, (int(x) + pad, int(y) + pad))

    def _piece_img(self, piece: chess.Piece) -> pygame.Surface:
        color_char = 'w' if piece.color == chess.WHITE else 'b'
        key = color_char + piece.symbol().upper()
        return self.piece_images[key]

    # ------------------------------------------------------------------ sidebar

    def draw_sidebar(
        self,
        board: chess.Board,
        eval_score: float,
        status: str,
        engine_name: str,
        captured: CapturedTracker,
    ):
        sx = BOARD_SIZE
        pygame.draw.rect(self.screen, BG_COLOR, (sx, 0, SIDEBAR_WIDTH, HEIGHT))

        y = 12
        y = self._draw_material_section(sx, y, captured, board_side=chess.BLACK)
        y = self._draw_divider(sx, y + 6)
        y = self._draw_game_info(sx, y + 10, board, eval_score, status, engine_name)
        y = self._draw_divider(sx, y + 6)
        y = self._draw_material_section(sx, y + 10, captured, board_side=chess.WHITE)
        y = self._draw_divider(sx, y + 6)
        self._draw_controls(sx, y + 10)

    def _draw_material_section(
        self, sx: int, y: int, captured: CapturedTracker, board_side: chess.Color
    ) -> int:
        """
        board_side=BLACK  → show pieces white lost (captured by black) + black's lead
        board_side=WHITE  → show pieces black lost (captured by white) + white's lead
        """
        if board_side == chess.BLACK:
            pieces = captured.sorted_black_captured()   # white pieces taken by black
            icon_prefix = 'w'
            label = "Black's captures"
            adv = -captured.advantage()                 # positive when black leads
            adv_color = ADV_BLACK
        else:
            pieces = captured.sorted_white_captured()   # black pieces taken by white
            icon_prefix = 'b'
            label = "White's captures"
            adv = captured.advantage()                  # positive when white leads
            adv_color = ADV_WHITE

        lbl = self.font_sm.render(label, True, DIM_COLOR)
        self.screen.blit(lbl, (sx + 14, y))
        y += lbl.get_height() + 4

        # Draw small piece icons in rows
        icons_per_row = (SIDEBAR_WIDTH - 28) // (SMALL_ICON_SIZE + SMALL_ICON_GAP)
        x_cursor = sx + 14
        row_y = y
        for i, piece_type in enumerate(pieces):
            sym = self._PIECE_SYMBOL.get(piece_type, 'P')
            key = icon_prefix + sym
            img = self.small_images.get(key)
            if img:
                self.screen.blit(img, (x_cursor, row_y))
            x_cursor += SMALL_ICON_SIZE + SMALL_ICON_GAP
            if (i + 1) % icons_per_row == 0:
                x_cursor = sx + 14
                row_y += SMALL_ICON_SIZE + 2

        rows_used = max(1, (len(pieces) + icons_per_row - 1) // icons_per_row)
        y += rows_used * (SMALL_ICON_SIZE + 2)

        if adv > 0:
            adv_surf = self.font_sm.render(f"+{adv}", True, adv_color)
            self.screen.blit(adv_surf, (sx + 14, y + 2))
        y += 18
        return y

    def _draw_game_info(
        self, sx: int, y: int, board: chess.Board,
        eval_score: float, status: str, engine_name: str,
    ) -> int:
        turn_text = "White to move" if board.turn == chess.WHITE else "Black to move"
        for text, color, font in [
            (turn_text, TEXT_COLOR, self.font_md),
            (f"Engine: {engine_name}", DIM_COLOR, self.font_sm),
            (f"Eval: {eval_score:+.2f}", GOLD_COLOR, self.font_sm),
        ]:
            surf = font.render(text, True, color)
            self.screen.blit(surf, (sx + 14, y))
            y += surf.get_height() + 7

        # Status box (highlight if game over)
        status_color = GOLD_COLOR if ("wins" in status or "Draw" in status) else TEXT_COLOR
        surf = self.font_md.render(status, True, status_color)
        self.screen.blit(surf, (sx + 14, y))
        y += surf.get_height() + 8
        return y

    def _draw_divider(self, sx: int, y: int) -> int:
        pygame.draw.line(self.screen, DIVIDER_COLOR, (sx + 10, y), (sx + SIDEBAR_WIDTH - 10, y), 1)
        return y

    def _draw_controls(self, sx: int, y: int):
        for line, color in [
            ("Controls", DIM_COLOR),
            ("Click — select / move piece", TEXT_COLOR),
            ("R — return to menu", TEXT_COLOR),
        ]:
            surf = self.font_sm.render(line, True, color)
            self.screen.blit(surf, (sx + 14, y))
            y += surf.get_height() + 5

    # ------------------------------------------------------------------ menu

    def draw_menu(self, hovered_idx: int | None = None):
        # Background: beach painting or flat color
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
        else:
            self.screen.fill(BG_COLOR)

        # Dark vignette overlay for readability
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 10, 6, 175))
        self.screen.blit(overlay, (0, 0))

        # Title
        title = self.font_lg.render("Chess Engine", True, GOLD_COLOR)
        shadow = self.font_lg.render("Chess Engine", True, (0, 0, 0))
        tx = WIDTH // 2 - title.get_width() // 2
        self.screen.blit(shadow, (tx + 2, 122))
        self.screen.blit(title, (tx, 120))

        subtitle = self.font_sm.render("Select a game mode to begin", True, DIM_COLOR)
        self.screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 160))

        # Buttons
        for i, (x, y, w, h) in enumerate(MENU_BUTTON_RECTS):
            self._draw_menu_button(x, y, w, h, i, hovered=(i == hovered_idx))

    def _draw_menu_button(self, x: int, y: int, w: int, h: int, idx: int, hovered: bool):
        key_label, option_text = MENU_BUTTON_LABELS[idx]
        fill = BTN_FILL_HOVER if hovered else BTN_FILL

        # Button body
        pygame.draw.rect(self.screen, fill, (x, y, w, h), border_radius=10)
        pygame.draw.rect(self.screen, BTN_BORDER, (x, y, w, h), 2, border_radius=10)

        # Key badge (left side)
        badge_w = 36
        pygame.draw.rect(self.screen, BTN_KEY_BG, (x + 10, y + (h - 32) // 2, badge_w, 32), border_radius=6)
        pygame.draw.rect(self.screen, BTN_BORDER,  (x + 10, y + (h - 32) // 2, badge_w, 32), 1, border_radius=6)
        key_surf = self.font_key.render(key_label, True, GOLD_COLOR)
        self.screen.blit(key_surf, (x + 10 + (badge_w - key_surf.get_width()) // 2,
                                    y + (h - key_surf.get_height()) // 2))

        # Option text
        opt_surf = self.font_btn.render(option_text, True, BTN_TEXT)
        self.screen.blit(opt_surf, (x + 10 + badge_w + 14, y + (h - opt_surf.get_height()) // 2))
