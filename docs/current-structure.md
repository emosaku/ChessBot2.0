# ChessBot2.0 — Current Structure

As of 2026-10-09 · Online version: https://claude.ai/code/artifact/e9de186d-aed0-4bc2-a750-bbcb6202b5e8

## Overview

ChessBot2.0 is a pygame desktop app where you play against an alpha-beta minimax engine. It is about 1,000 lines of Python plus a 61-test pytest suite. It uses python-chess for move generation and rules, and pygame for the window.

To run it (Python 3.12 venv, already created at `.venv`):

```bash
cd ChessBot2.0
source .venv/bin/activate
python main.py   # 1 = play White, 2 = play Black, R = back to menu
pytest           # 61 tests, under 1 second
```

Dependencies are `pygame==2.5.2`, `chess==1.11.2` and `pytest==8.3.0`.

## Directory layout

The code is split into three layers: `engine/` decides moves, `game/` holds the rules state, and `ui/` draws and takes input. Data files now live in `assets/`.

```
ChessBot2.0/
├── main.py                  entry point: ChessGameGUI().run()
├── requirements.txt         pygame, chess, pytest
├── README.md                run / test / layout
├── assets/
│   ├── books/8moves_v3.bin  Polyglot opening book (36 entries)
│   └── images/              12 piece PNGs + beach_bg.jpg (menu)
├── engine/
│   ├── base_engine.py       BaseEngine interface: get_best_move(board)
│   ├── minimax.py           AlphaBetaEngine (used by the app, depth 5)
│   ├── expectimax.py        ExpectimaxEngine (not reachable from the menu)
│   ├── evaluator.py         BoardEvaluator (material) + PSTEvaluator (default)
│   └── opening_book.py      weighted-random Polyglot lookup
├── game/
│   ├── game_state.py        board, game-over detection, captured pieces
│   ├── game_controller.py   whose turn; routes to player or engine
│   └── captured_tracker.py  captured pieces + material lead
├── ui/
│   ├── gui.py               main loop, menu/game screens, wiring
│   ├── renderer.py          board, pieces, sidebar, menu drawing
│   ├── event_handler.py     pygame events -> click/key/timer results
│   ├── animation.py         14-frame smoothstep slide of the moved piece
│   ├── piece_loader.py      loads and scales piece PNGs
│   ├── promotion_handler.py auto-promotes to queen
│   └── constants.py         sizes (640 px board, 360 px sidebar), colours
├── tests/                   61 pytest tests across engine, game and ui
└── docs/                    these two docs as markdown
```

## The engine approach

The plan is an opening dataset, then minimax in the middlegame, then an endgame dataset. Only the first two exist in the code. There is no endgame dataset, just a different king table once material runs low.

| Phase | Intended | What the code does today |
| --- | --- | --- |
| Opening | Opening dataset | `OpeningBook` reads the Polyglot book `assets/books/8moves_v3.bin` and picks a move at random, weighted by book frequency. The file holds only 36 positions (576 bytes), with 4 candidate moves from the start position, so the book runs out within the first few moves. |
| Middlegame | Minimax | `AlphaBetaEngine` runs a fixed-depth alpha-beta minimax, depth 5 in the app. It searches moves in python-chess generation order, with no move ordering, no transposition table and no time limit. |
| Endgame | Endgame dataset | No dataset. `PSTEvaluator` switches the king from a stay-sheltered table to a centralise table once combined non-pawn material for both sides is 1,300 or less. Otherwise the same depth-5 search plays the endgame. |

Every position the search reaches is scored by `PSTEvaluator`. It scores in centipawns from White's side and combines three terms:

- Material: P 100, N 320, B 330, R 500, Q 900
- Piece-square tables for each piece type, mirrored for Black
- Pawn structure: doubled −20, isolated −15, passed +20 plus 10 per rank advanced

`ExpectimaxEngine` treats the opponent as random, averaging over all replies. It was built for comparison, and the menu never offers it: both menu options start `AlphaBetaEngine`.

Measured on this machine (Italian Game middlegame, Python 3.12): depth 3 takes 0.17 s, depth 4 takes 5.1 s, and depth 5 takes 38.7 s per move. The engine evaluates about 35,000 positions a second.

## How a move flows

A player move and the engine's reply pass through all three layers: `ui/` turns a click into a move, `game/` checks and applies it, and `engine/` picks the reply.

```
Click a square (event_handler.py)
  -> Select or move (gui._handle_square)
  -> Accept if legal (game_controller.py)
  -> Apply the move (game_state.push_move)
  -> Slide the piece (animation.py, 14 frames)
  -> Engine's turn (apply_engine_move)
       In opening book?  yes -> play book move (opening_book.py)
                         no  -> alpha-beta search, depth 5, PSTEvaluator   <- runs on the UI thread, ~39 s
  -> Apply and slide (push_move + animation) -> player's turn again
```

The highlighted box is the bottleneck. `get_best_move` runs inside the 60 fps pygame loop, so nothing redraws until it returns. The UI also re-runs the evaluator on every frame just to display the eval score, about 60 calls a second on an unchanged board.

## Cleanup performed (2026-10-09)

The cleanup moved files and removed clutter without changing behaviour: all 61 tests still pass and the GUI starts up. The changes are not committed yet.

| Change | Why |
| --- | --- |
| `ui/books/` → `assets/books/` and `ui/images/` → `assets/images/` (`git mv`) | The engine was reading its opening book out of the UI folder, so the book now sits in a shared `assets/` folder. Paths are updated in `engine/opening_book.py` and `ui/gui.py`. |
| `requirements.txt`: removed `pandas`; `python-chess==1.999` → `chess==1.11.2` | No code imports pandas. `python-chess` 1.999 is an empty package that only redirects to `chess`. |
| Deleted `.DS_Store`, `__pycache__/` and `.pytest_cache/` | OS and cache clutter. `.gitignore` already covers them. |
| Added `README.md` and `docs/` | Run, test and layout instructions, plus these docs as markdown. |
| Created `.venv` on Python 3.12 | The pinned `pygame` 2.5.2 has no build for Python 3.14. |
