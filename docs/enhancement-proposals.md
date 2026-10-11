# ChessBot2.0 — Enhancement Proposals

As of 2026-10-09 · Online version: https://claude.ai/code/artifact/4a91a995-4247-4871-8e6a-948e81108291

## Summary

The biggest problem today is that one engine move takes 38.7 s at depth 5, and the window is frozen for that time. Fix that first, in the code on your own machine. GCP only helps after the search can use many cores.

1. **Run the engine off the UI thread.** The window stays at 60 fps while the engine thinks. This change matters most for how smooth the app feels.
2. **Speed up the search itself:** move ordering, iterative deepening with a time limit, and a transposition table. These cut the nodes searched for the same move quality.
3. **Visual upgrade:** time-based animation, animated castling and captures, legal-move dots, last-move and check highlights, drag-and-drop, and a sharper SVG piece set.
4. **Fill the opening and endgame:** our own opening book built from Lichess games (decided: Option B), and Syzygy endgame tablebases (the missing endgame dataset).
5. **GCP:** the engine on a Spot VM next to the Syzygy tables, a Cloud Run job that builds the opening book, and later a bigger VM for a parallel search.

## Enhancement 1a: Visuals

Moves already slide with a 14-frame smoothstep (`ui/animation.py`). The board feels jerky for two other reasons: the window freezes while the engine searches, and several moves skip the animation.

### Smoother moves

| Change | Where | Why |
| --- | --- | --- |
| Run `get_best_move` in a `concurrent.futures.ProcessPoolExecutor`, sending the FEN in and getting a UCI move back. Poll the future each frame. | `ui/gui.py` `_run_engine` | The main loop keeps drawing at 60 fps while the engine thinks. A process rather than a thread, because Python's GIL would make a search thread steal frames. |
| Time-based animation: move by `dt` from `clock.tick()` instead of counting frames, with an ease-out cubic curve. | `ui/animation.py` | Speed no longer depends on the frame rate. Ease-out feels snappier than ease-in-out for piece moves. |
| Animate the rook when castling, and fade out a captured piece over the slide. | `ui/animation.py`, `renderer.py` | Today the rook teleports and captured pieces vanish on the first frame. |
| Drag-and-drop with the piece following the cursor, plus click-click as now. | `event_handler.py` (add `MOUSEMOTION`/`MOUSEBUTTONUP`) | Feels like Lichess or chess.com. |
| Compute the eval only when the board changes, not every frame. | `ui/gui.py` `_tick_game` | It is evaluated about 60 times a second now. Caching frees CPU and stops a full search from being needed just for display. |

### Better-looking board and pieces

- **Pieces:** replace the mixed-size PNGs (bP.png is 136 KB, the rest 18 to 60 KB) with one SVG set, such as Lichess's cburnett or merida (check each set's licence). Render them with `cairosvg` to exactly `SQUARE_SIZE` at 2× scale for Retina, so they are not blurred by `smoothscale`.
- **Retina sharpness:** draw to a 2× surface and pass `pygame.SCALED`, or set the display size in physical pixels. On a Mac, a 1× pygame window is upscaled and looks soft.
- **Board:** add a theme setting with flat colours or a wood texture. Show a1–h8 coordinates in the square corners and a subtle inner shadow along the board edge.
- **Feedback overlays:** legal-move dots when a piece is selected, a ring on capturable squares, last-move highlight on both squares, and a red glow on a king in check.
- **Sidebar:** a vertical eval bar beside the board instead of the `Eval: +0.35` text, a scrolling move list in SAN, and a promotion picker (`promotion_handler.py` always picks a queen today).
- **Sound:** short move, capture and check clicks via `pygame.mixer`.

If you later move the engine to GCP (1c), a web front end becomes an option: chessground, Lichess's open-source board, gives all of the above for free. It would replace pygame, so treat it as a separate decision.

## Enhancement 1b: Engine speed

Sorting captures first already makes depth 5 about 12× faster on your Mac, 38.7 s down to 3.15 s, and the engine picks the same move. Alpha-beta is only as good as its move order, and today the engine searches in generation order.

Measured on an Apple M5, Python 3.12, from an Italian Game middlegame (`r1bq1rk1/pppp1ppp/2n2n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w`):

| Search | Depth 4 | Depth 5 | Move chosen |
| --- | --- | --- | --- |
| Current `AlphaBetaEngine` | 5.11 s | 38.7 s | f3g5 at depth 5 |
| + captures first, by most valuable victim (MVV-LVA), promotions next | 0.29 s | 3.15 s | f3g5 at depth 5 |

The prototype is in `tools/bench_move_ordering.py` (run it from the project root) and is not merged into the engine yet. These steps are in priority order; each builds on the last:

1. **Move ordering:** MVV-LVA captures, then killer moves (quiet moves that caused a cutoff at the same depth), then the history heuristic. The measured 12× above comes from the first part alone.
2. **Iterative deepening with a time limit:** search depth 1, 2, 3 and so on until a budget such as 3 s runs out, then play the best move from the last finished depth. The engine always answers on time, and each depth's best line orders the next.
3. **Transposition table:** cache score, depth and best move by Zobrist hash (`chess.polyglot.zobrist_hash(board)`). Many positions are reached by several move orders and get searched only once.
4. **Quiescence search:** at depth 0, keep searching captures until the position is quiet. This adds strength rather than speed: it stops the engine stopping its search halfway through an exchange.
5. **Cheaper nodes:** drop `board.is_game_over()` at every node (it checks repetition and other draw rules) and test for an empty move list instead. Skip the three `is_checkmate`/`is_stalemate`/`is_insufficient_material` calls at the top of `evaluate()`. Later, update material and piece-square scores incrementally on push/pop instead of rescanning 64 squares.
6. **Negamax:** fold the duplicated max and min branches (and the duplicated `_search`) into one function. Steps 2–4 then need writing only once.
7. **Python's ceiling:** python-chess searches about 35,000 positions a second here, while engines written in C or Rust search millions. After steps 1–5, the next jump is the search core in Rust (via `pyo3` with the `shakmaty` crate), with Python kept for the UI. Running the engine process under PyPy is a cheaper middle step.
8. **Parallel search (Lazy SMP):** several processes search the same tree and share the transposition table. This is the step that makes more cores, and therefore GCP, pay off.

To know whether a change made the engine stronger and not just faster, add a match harness. It plays the engine against an older version of itself, or against Stockfish at a fixed skill level, through `chess.engine`, then reports the score over 100+ games.

## Enhancement 1c: Running on GCP

GCP makes the engine faster only once the search runs in parallel (1b, step 8). Until then, your 10-core Apple M5 is as fast as anything you would rent. Today's engine uses one core, and one Cloud vCPU is a hyperthread, which is not faster than an M5 core.

The full deployment plan, with commands, costs and failure handling, is in [ChessBot2.0 — Cloud Implementation](https://claude.ai/code/artifact/25febc9a-bfe1-4945-bb6b-308d2f847896) ([local copy](cloud-implementation.md)).

| Option | Cores | Speed gain over your Mac | Best for |
| --- | --- | --- | --- |
| Cloud Run service: FastAPI takes `{fen, time_ms}` and returns a move; pygame calls it over HTTP | up to 8 vCPU per instance ([docs](https://docs.cloud.google.com/run/docs/configuring/cpu)) | None. 8 vCPU is fewer than your 10 cores. | Playing from any device, a web front end, and scaling to zero when idle |
| Compute Engine VM (C4D, general-purpose, Hyperdisk only) running the same service, started only for a session | C4D goes up to 384 vCPU ([docs](https://docs.cloud.google.com/compute/docs/machine-types)) | Only with Lazy SMP. Parallel chess search scales well below linearly, so 4× the cores buys well under 4× the depth. | Deep analysis and long time controls |
| Cloud Run jobs or Batch with Spot VMs, running offline work | many short-lived workers | Not about move time | Building the opening book, self-play matches, tuning the evaluator |

Recommended setup:

1. Wrap the engine as a small HTTP service (`POST /move` with FEN and a time budget) in a Docker image. That is the same pattern as Fantasydashboard's Dockerfile and Cloud Run deploy. The pygame client gets an `--engine-url` flag and falls back to the local engine.
2. Deploy it straight to a small C4D Spot VM rather than Cloud Run, because the tablebase disk cannot attach to a Cloud Run service. Cloud Run is used only for the book-build job.
3. Once Lazy SMP exists, point the same image at a C4D VM on Spot pricing (larger sizes up to c4d-highcpu-384), started before a session and stopped after. Check the cost of the size you pick in the [GCP pricing calculator](https://cloud.google.com/products/calculator).
4. Put the 3–5 and 6-piece Syzygy tablebases (150.1 GiB) on a 200 GB Hyperdisk Balanced volume attached to the VM, and use the Lichess tablebase API for 7-piece positions at the root. They are too large for a Cloud Run container (see the next section).

The biggest payoff from GCP is offline: build a large opening book from millions of Lichess games, and tune the evaluator's weights by having the engine play itself thousands of times in parallel.

## Opening, middlegame and endgame

The approach is an opening dataset, then minimax for the middlegame, then an endgame dataset. Only the middlegame is fully built. The opening book is a 36-entry stub, and the endgame dataset does not exist yet.

| Phase | Today | Proposal |
| --- | --- | --- |
| Opening: dataset | `assets/books/8moves_v3.bin`: 36 positions, 4 replies to the start position. The engine leaves the book within the first few moves. | Decided 2026-10-09: Option B, our own Polyglot book built from the [Lichess open database](https://database.lichess.org/) (CC0, monthly PGN files). Filters, build steps and `OpeningBook` changes are in the Option B plan below; the build runs as a Cloud Run job. |
| Middlegame: minimax | Alpha-beta, fixed depth 5, no ordering, about 39 s per move. | Section 1b: ordering, iterative deepening on a time budget, a transposition table and quiescence. Then tune the evaluator's weights (material, piece-square tables, pawn terms) by self-play or Texel tuning against game results. |
| Endgame: dataset | None. The king switches to a centralising table once non-pawn material for both sides is 1,300 or less, and the same search plays on. | Syzygy tablebases, probed with python-chess's `chess.syzygy.open_tablebase()`, then `probe_wdl()` / `probe_dtz()` ([docs](https://python-chess.readthedocs.io/en/latest/syzygy.html)). The 3–5 piece set is 939 MiB and fits locally. The 6-piece set is 149.2 GiB and belongs on a GCP disk; the 7-piece set is over 16.7 TiB ([sizes](https://www.chessprogramming.org/Syzygy_Bases)). When the position has few enough pieces, play the move that keeps the best result and shortest distance-to-zero (DTZ) instead of searching. |

The endgame threshold has a quirk. `_ENDGAME_MATERIAL_THRESHOLD = 1300` is commented "approx rook + minor piece each side", but the code sums both sides. The endgame table therefore turns on later than intended, at about one rook plus one minor piece in total.

### Opening: Option B, our own Lichess book (decided 2026-10-09)

We build our own Polyglot book from Lichess games rather than download one. That lets us pick the rating floor, time controls and depth, and keeps the licence simple (CC0). The build runs as a Cloud Run job, described in the cloud implementation doc.

1. **Source:** the 3 most recent monthly files from the Lichess open database.
2. **Filter:** both players rated 2200+, rapid, classical, or blitz of 3+2 or longer.
3. **Count:** replay the first 24 plies, recording games, wins and draws per (`chess.polyglot.zobrist_hash`, move).
4. **Prune:** keep moves with 30+ games that score 45%+ for the side playing them.
5. **Write:** `struct.pack(">QHHI", key, move, weight, 0)` per entry, sorted by key. The move is packed as `to_file | to_rank<<3 | from_file<<6 | from_rank<<9 | promo<<12`, and castling is stored as king takes own rook (`e1h1`).

`OpeningBook` changes: default to `assets/books/lichess.bin`, fall back to `8moves_v3.bin`, add `mode` (`weighted` or `best`) and a `max_moves` cut-off of 12. Acceptance test: from 1.e4 e5 2.Nf3, 1.d4 d5 and 1.e4 c5, the engine stays in book for at least 8 moves.

### Using Syzygy correctly

| File | Gives | Where it is used |
| --- | --- | --- |
| WDL (`.rtbw`) | win / draw / loss | Inside the search, at any node with few enough pieces |
| DTZ (`.rtbz`) | moves until the next capture or pawn move | Only at the root, to choose the actual move |

- WDL has five values: +2 win, +1 cursed win (drawn by the 50-move rule), 0 draw, −1 blessed loss, −2 loss. Score ±1 as a draw, not a win.
- Probe in the search only when `board.halfmove_clock == 0` and the position has no castling rights. WDL assumes a fresh 50-move counter, and positions with castling rights are not in the tables.
- At the root, a win counts only if `dtz + board.halfmove_clock <= 100`. Among winning moves prefer a capture or pawn move, then the smallest |DTZ|; when losing, the largest |DTZ|.
- Score tablebase wins as ±(20000 − ply), below the engine's mate score of 99999.
- Use `get_wdl` / `get_dtz`, which return None when a table is missing, so a missing file never crashes the search.
- Coverage (decided 2026-10-09): the 3–5 and 6-piece files (150.1 GiB) live on the cloud VM's disk. 7-piece positions go to the Lichess tablebase API at the root only, since self-hosting 7-piece files is 16.7 TiB.

## Further enhancements

| Enhancement | Detail | Size |
| --- | --- | --- |
| Draw by repetition | `GameState._detect_terminal` checks checkmate, stalemate, insufficient material and the 50-move rule, but not repetition. A game can repeat forever. Add `board.is_repetition(3)` or `can_claim_threefold_repetition()`. | Small (bug) |
| Difficulty levels | Menu choices such as Easy / Medium / Hard, mapped to time budgets like 0.2 s, 1 s and 3 s, once iterative deepening exists. | Small |
| Expose Expectimax | Both menu buttons start `AlphaBetaEngine`. Add a third button, or drop `ExpectimaxEngine`. | Small |
| Undo, hint, PGN export | `U` takes back a move pair, `H` shows the engine's suggested move, and the game can be saved as PGN. | Small |
| Engine info panel | Depth reached, nodes per second and the principal variation, shown in the sidebar while thinking. | Medium |
| CI | A GitHub Actions workflow running `pytest` and `ruff` on each push, as in Fantasydashboard. | Small |
| Package layout | Move code under `src/chessbot/` with a `pyproject.toml` once the engine service (1c) needs to be installed separately from the UI. | Medium |

## Suggested order of work

The first three steps take a move from about 39 s to a fixed few seconds and keep the window at 60 fps, all on your Mac with no cloud cost.

1. Move the engine into a separate process so the UI never freezes (1a).
2. Merge move ordering, then add iterative deepening with a time budget (1b, steps 1–2).
3. Add the transposition table, quiescence and cheaper nodes (1b, steps 3–5), checked with the match harness.
4. Visual pass: time-based animation, castling and capture animation, overlays, SVG pieces at 2× (1a).
5. Opening: build the Lichess book with `tools/build_book.py` (Option B). Endgame: 3–5 piece Syzygy tables locally, wired in following the Syzygy rules above.
6. The engine as an HTTP service on a C4D Spot VM with the 3–5 and 6-piece tables, following the cloud implementation doc.
7. Lazy SMP, then a bigger C4D Spot VM for deep play (1b step 8, 1c steps 3–4).
8. Rust search core, if Python is still the limit.
