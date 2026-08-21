## Entry Point
## Run with: python main.py
## Install deps: pip install -r requirements.txt

from ui.gui import ChessGameGUI

if __name__ == "__main__":
    game = ChessGameGUI()
    game.run()
