import pygame
import chess
import sys
from ui.constants import BOARD_SIZE, SQUARE_SIZE


class EventResult:
    QUIT          = "quit"
    SQUARE_CLICKED = "square_clicked"
    KEY_PRESSED   = "key_pressed"
    ENGINE_TIMER  = "engine_timer"
    MENU_CLICKED  = "menu_clicked"   # data is (x, y) pixel position


class EventHandler:
    """Translates raw pygame events into domain-level (EventResult, data) tuples."""

    def process_menu_events(self) -> list[tuple[str, object]]:
        results = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                results.append((EventResult.KEY_PRESSED, event.key))
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                results.append((EventResult.MENU_CLICKED, event.pos))
        return results

    def process_game_events(self) -> list[tuple[str, object]]:
        results = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                results.append((EventResult.KEY_PRESSED, event.key))
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x, y = event.pos
                if x < BOARD_SIZE:
                    col = x // SQUARE_SIZE
                    row = y // SQUARE_SIZE
                    square = chess.square(col, 7 - row)
                    results.append((EventResult.SQUARE_CLICKED, square))
            if event.type == pygame.USEREVENT:
                pygame.time.set_timer(pygame.USEREVENT, 0)
                results.append((EventResult.ENGINE_TIMER, None))
        return results
