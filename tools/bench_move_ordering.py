import sys, time, chess
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
from engine.minimax import AlphaBetaEngine
VAL = {1:100,2:320,3:330,4:500,5:900,6:0}
def order(board):
    def key(m):
        if board.is_capture(m):
            v = board.piece_at(m.to_square); a = board.piece_at(m.from_square)
            return -(10*(VAL[v.piece_type] if v else 100) - VAL[a.piece_type]) - 10000
        return -1000 if m.promotion else 0
    return sorted(board.legal_moves, key=key)
class Ordered(AlphaBetaEngine):
    def _search(self, board):
        best=None; white=board.turn==chess.WHITE; bv=float('-inf') if white else float('inf')
        a,b=float('-inf'),float('inf')
        for m in order(board):
            board.push(m); v=self._ab(board,self.depth-1,a,b,not white); board.pop()
            if (white and v>bv) or (not white and v<bv): bv,best=v,m
            if white: a=max(a,v)
            else: b=min(b,v)
        return best
    def _ab(self, board, d, a, b, mx):
        if d==0: return self.evaluator.evaluate(board)
        moves=order(board)
        if not moves: return self.evaluator.evaluate(board)
        if mx:
            v=float('-inf')
            for m in moves:
                board.push(m); v=max(v,self._ab(board,d-1,a,b,False)); board.pop(); a=max(a,v)
                if b<=a: break
            return v
        v=float('inf')
        for m in moves:
            board.push(m); v=min(v,self._ab(board,d-1,a,b,True)); board.pop(); b=min(b,v)
            if b<=a: break
        return v
fen="r1bq1rk1/pppp1ppp/2n2n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 1"
for d in (4,5):
    e=Ordered(depth=d); t=time.time(); m=e._search(chess.Board(fen)); print(f"ordered depth {d}: {m} {time.time()-t:.2f}s")
