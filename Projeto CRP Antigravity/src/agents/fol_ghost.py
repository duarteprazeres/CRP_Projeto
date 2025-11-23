from src.agents.ghost import Ghost
from src.logic.first_order import FOLKB, Predicate, Variable, Constant, fol_bc_ask
import random

"""FOL-based ghost agent.

The agent builds a small FOL KB each
turn (keeps Visited in external state) and queries for chase or
explore moves.
"""

class Visited(Predicate):
    pass


class LastSeen(Predicate):
    pass

class BestChaseMove(Predicate):
    pass

class PossibleExploreMove(Predicate):
    pass


# Helpers / variables used in rules
v_me = Constant("Me")
v_curr = Variable("curr")
v_next = Variable("next")
v_target = Variable("target")

class FOLGhost(Ghost):
    def __init__(self, color="Pink"):
        super().__init__(color)
        self.kb = FOLKB()

    def decide_move(self, grid):
        # Transient state: clear clauses but keep agent memory (self.visited)
        self.kb.clauses = []

        x, y = self.position
        me = Constant("Me")
        curr_c = Constant(f"C_{x}_{y}")
        # Perceive neighbors and add basic facts to KB
        # Fact 1: seed KB with the agent's current position (At(Me, C_x_y)).
        # This initial fact is used as the starting point for inferences each turn.
        self.kb.tell((Predicate("At", [me, curr_c]), []))

        neighbors = [(0, -1), (0, 1), (1, 0), (-1, 0)]
        valid_moves = []

        # Perceive neighbors and add basic facts to KB
        for dx, dy in neighbors:
            nx, ny = x + dx, y + dy
            next_c = Constant(f"C_{nx}_{ny}")
            cell_type = self.belief_map.get((nx, ny), 'Unknown')

            if cell_type != 'Wall':
                valid_moves.append((nx, ny))
                
                # Fact 2: Connectivity (relation between cells)
                self.kb.tell((Predicate("Connected", [curr_c, next_c]), []))
                # Fact 3: Safety (unary predicate)
                self.kb.tell((Predicate("Safe", [next_c]), []))
            
            # Fact 4 (FOL memory): add 'Visited' if the cell was visited (uses self.visited)
            if (nx, ny) in self.visited:
                self.kb.tell((Predicate("Visited", [next_c]), []))
            
            # Fact 5 (Pacman perception): if Pacman is adjacent
            if self.last_known_pacman_pos == (nx, ny):
                 self.kb.tell((Predicate("PacmanAt", [next_c]), []))
        
        # 2. Add Rules: chase first, otherwise consider safe moves
        v_next = Variable("m")  # use 'm' as the variable for the move

        # BestMove rule: chase when Pacman is at a cell and that cell is safe. (PacmanAt(m) & Safe(m) -> BestMove(m))
        self.kb.tell((Predicate("BestMove", [v_next]), [
            Predicate("PacmanAt", [v_next]),
            Predicate("Safe", [v_next])
        ]))

        # PossibleMove rule: any safe cell is a candidate move (Safe(m) -> PossibleMove(m))
        self.kb.tell((Predicate("PossibleMove", [v_next]), [
            Predicate("Safe", [v_next])
        ]))
        self.kb.tell((Predicate("PossibleMove", [v_next]), [
            Predicate("Safe", [v_next])
        ]))
        
        # 3. Decide the move (query)

        # Priority 1: BestMove (immediate chase)
        query_chase = Predicate("BestMove", [Variable("m")])
        results_chase = list(self.kb.ask(query_chase))
        if results_chase:
            choice = results_chase[0][Variable("m")]
            parts = choice.name.split('_')
            return (int(parts[1]), int(parts[2]))

        # Priority 2: Explore unvisited safe moves
        query_explore = Predicate("PossibleMove", [Variable("m")])
        results_explore = list(self.kb.ask(query_explore))

        unvisited_moves = []
        for res in results_explore:
            choice = res[Variable("m")]
            parts = choice.name.split('_')
            nx, ny = int(parts[1]), int(parts[2])
            
            # If the Visited(C_nx_ny) predicate is NOT in KB, it's an exploration move
            if (nx, ny) not in self.visited:
                unvisited_moves.append((nx, ny))

        if unvisited_moves:
            # Choose a random unvisited cell (pure exploration)
            mx, my = random.choice(unvisited_moves)
            self.last_move = (mx - x, my - y)
            return (mx, my)

        # Priority 3: Fallback (move to any safe cell, even if visited)
        if valid_moves:
            mx, my = random.choice(valid_moves)
            self.last_move = (mx - x, my - y)
            return (mx, my)

        self.last_move = None
        return None