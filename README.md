# ChessBot2.0

A pygame chess app where you play against an alpha-beta minimax engine.

## Run

```bash
python3.12 -m venv .venv        # once
source .venv/bin/activate
pip install -r requirements.txt  # once
python main.py
```

Press `1` to play White or `2` to play Black. Click a piece and then a square to move. Press `R` to go back to the menu.

## Test

```bash
pytest
```

## Layout

```
main.py        entry point
engine/        search (alpha-beta, expectimax), evaluation, opening book
game/          board state, turn control, captured pieces
ui/            pygame window: rendering, input, animation
assets/        opening book (books/) and piece/background images (images/)
tests/         pytest suite
tools/         benchmarks and one-off scripts
docs/          structure and enhancement docs
```

See [docs/current-structure.md](docs/current-structure.md), [docs/enhancement-proposals.md](docs/enhancement-proposals.md) and [docs/cloud-implementation.md](docs/cloud-implementation.md).
