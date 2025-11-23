from src.agents.ghost import Ghost
from src.logic.first_order import FOLKB, Predicate, Variable, Constant
import random

class FOLGhost(Ghost):
    def __init__(self, color="Pink"):
        super().__init__(color)
        self.kb = FOLKB()
        # We might want to keep a persistent KB for the map
        # But for movement decisions, we might clear the transient state

    def decide_move(self, grid):
        # Rebuild KB for the current state to decide best move
        # We want to ask: BestMove(Self, ?m)
        
        self.kb.clauses = [] # Clear for now
        
        x, y = self.position
        me = Constant("Me")
        
        # 1. Add facts about current position and connectivity from Belief Map
        # At(Me, x, y)
        # Connected(x, y, nx, ny)
        
        self.kb.tell(Predicate("At", [me, Constant(f"C_{x}_{y}")]))
        
        moves = []
        neighbors = [(0, -1), (0, 1), (1, 0), (-1, 0)]
        for dx, dy in neighbors:
            nx, ny = x + dx, y + dy
            cell_type = self.belief_map.get((nx, ny), 'Unknown')
            if cell_type != 'Wall':
                moves.append((nx, ny))
        for mx, my in moves:
            self.kb.tell(Predicate("Connected", [Constant(f"C_{x}_{y}"), Constant(f"C_{mx}_{my}")]))
            self.kb.tell(Predicate("Safe", [Constant(f"C_{mx}_{my}")]))
            
            # Add direction info to the connection?
            # Connected(Current, Next, Direction)
            # Let's infer direction or just return the Next cell as the move
        
        # 2. Add facts about Pacman
        target = self.last_known_pacman_pos
        if target:
            tx, ty = target
            self.kb.tell(Predicate("PacmanAt", [Constant(f"C_{tx}_{ty}")]))
            
            # Heuristic: If Connected(Me, Next) & Closer(Next, Pacman) -> BestMove(Me, Next)
            # Defining "Closer" in FOL is hard without math.
            # We can pre-calculate "Closer" facts in Python and inject them.
            
            for mx, my in moves:
                dist_current = abs(x - tx) + abs(y - ty)
                dist_next = abs(mx - tx) + abs(my - ty)
                if dist_next < dist_current:
                    self.kb.tell(Predicate("Closer", [Constant(f"C_{mx}_{my}"), Constant(f"C_{tx}_{ty}")]))

        # 3. Rules
        # Rule 1: If Connected(Me, ?next) & Safe(?next) & PacmanAt(?p) & Closer(?next, ?p) -> BestMove(Me, ?next)
        
        # Variables
        v_next = Variable("next")
        v_p = Variable("p")
        
        # Body: Connected(Me, ?next), Safe(?next), PacmanAt(?p), Closer(?next, ?p)
        # Head: BestMove(Me, ?next)
        
        # We need to handle the case where multiple are true.
        # Let's just check entailment for each direction.
        
        # Basic Chasing Rules
        # We will add a rule: BestMove is a move that is Closer to Pacman.
        
        rule_body = [
            Predicate("At", [me, Variable("curr")]), 
            Predicate("Connected", [Variable("curr"), v_next]),
            Predicate("Safe", [v_next]),
            Predicate("PacmanAt", [v_p]),
            Predicate("Closer", [v_next, v_p])
        ]
        
        self.kb.tell((Predicate("BestMove", [me, v_next]), rule_body))
        
        # Rule 2: Exploration - If no Pacman visible, prefer moves that are Safe.
        # This is a weak rule, but better than nothing.
        # Connected(Me, ?next) & Safe(?next) -> PossibleMove(Me, ?next)
        
        self.kb.tell((Predicate("PossibleMove", [me, v_next]), [
            Predicate("At", [me, Variable("curr")]),
            Predicate("Connected", [Variable("curr"), v_next]),
            Predicate("Safe", [v_next])
        ]))
        
        # Query
        # First try to find BestMove (Chase)
        query = Predicate("BestMove", [me, Variable("m")])
        results = list(self.kb.ask(query))
        
        if results:
            choice = results[0][Variable("m")]
            parts = choice.name.split('_')
            return (int(parts[1]), int(parts[2]))
            
        # If no BestMove, try PossibleMove (Explore)
        query_explore = Predicate("PossibleMove", [me, Variable("m")])
        results_explore = list(self.kb.ask(query_explore))
        
        if results_explore:
            # Pick a random one from possible moves to avoid repetitive patterns
            # Or pick one that we haven't visited recently?
            # For now, random choice from valid moves is better than always first.
            choices = [res[Variable("m")] for res in results_explore]
            choice = random.choice(choices)
            parts = choice.name.split('_')
            return (int(parts[1]), int(parts[2]))
        
        # Fallback
        if moves: return random.choice(moves)
        return (x, y)
