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

class NotVisited(Predicate):
    pass

class LastSeen(Predicate):
    pass

class BestChaseMove(Predicate):
    pass

class PossibleExploreMove(Predicate):
    pass

class LeadsToPacman(Predicate):
    pass


# Helpers / variables used in rules
v_me = Constant("Me")
v_curr = Variable("curr")
v_next = Variable("next")
v_target = Variable("target")

class StrategicGhost(Ghost):
    """
    Uses First-Order Logic to move Strategically.
    Rules:
    - Avoid Dead Ends (unless Pacman is there).
    - If Pacman is far, move randomly/explore.
    - If Pacman is close (within 8 units), Chase.
    - If Pacman is TOO close (within 2 units), maybe Flee? (Clyde behavior) - Let's stick to Strategic Chase.
    """
    def __init__(self, color="Orange"):
        super().__init__(color)
        self.kb = FOLKB()
        self.visited = set()

    def decide_move(self, grid):
        # Transient state: clear clauses but keep agent memory (self.visited)
        self.kb.clauses = []

        x, y = self.position
        self.visited.add((x, y))

        me = Constant("Me")
        curr_c = Constant(f"C_{x}_{y}")
        
        # Fact 1: Current Position
        self.kb.tell((Predicate("At", [me, curr_c]), []))

        neighbors = [(0, -1), (0, 1), (1, 0), (-1, 0)]
        valid_moves = []
        
        # Analyze surroundings to detect Dead Ends
        # A cell is a dead end if it has only 1 valid neighbor (which is where we came from)
        # But we need to know if the NEIGHBOR is a dead end.
        
        for dx, dy in neighbors:
            nx, ny = x + dx, y + dy
            next_c = Constant(f"C_{nx}_{ny}")
            cell_type = self.belief_map.get((nx, ny), 'Unknown')

            if cell_type != 'Wall':
                valid_moves.append((nx, ny))
                
                # Fact 2: Connectivity
                self.kb.tell((Predicate("Connected", [curr_c, next_c]), []))
                # Fact 3: Safety
                self.kb.tell((Predicate("Safe", [next_c]), []))
                
                # Check if this neighbor is a Dead End (simplified check: does it have < 2 exits?)
                # We can't easily check the neighbor's neighbors without querying the grid/belief map deeper.
                # Let's assume we can query belief map for neighbor's neighbors.
                n_exits = 0
                for ndx, ndy in neighbors:
                    nnx, nny = nx + ndx, ny + ndy
                    if self.belief_map.get((nnx, nny), 'Unknown') != 'Wall':
                        n_exits += 1
                
                if n_exits <= 1:
                     self.kb.tell((Predicate("DeadEnd", [next_c]), []))
                else:
                     self.kb.tell((Predicate("NotDeadEnd", [next_c]), []))

                # Fact 4: Visited Status
                if (nx, ny) in self.visited:
                    self.kb.tell((Predicate("Visited", [next_c]), []))
                else:
                    self.kb.tell((Predicate("NotVisited", [next_c]), []))
            
            # Fact 5 (Pacman perception)
            if self.last_known_pacman_pos:
                px, py = self.last_known_pacman_pos
                
                # Distance logic
                dist = abs(px - nx) + abs(py - ny)
                
                if dist < 8:
                    self.kb.tell((Predicate("CloseToPacman", [next_c]), []))
                
                if dist < abs(px - x) + abs(py - y):
                     self.kb.tell((Predicate("Closer", [next_c]), []))

        # 2. Add Rules
        v_next = Variable("m")

        # Rule 1: Strategic Move - Not Dead End AND Closer to Pacman (if close)
        # If Pacman is close, we want to get closer, but avoid dead ends if possible?
        # Actually, if Pacman is in a dead end, we should go there.
        # Let's simplify:
        # If CloseToPacman(m) AND Closer(m) -> BestMove(m)
        self.kb.tell((Predicate("BestMove", [v_next]), [
            Predicate("Safe", [v_next]),
            Predicate("CloseToPacman", [v_next]),
            Predicate("Closer", [v_next])
        ]))

        # Rule 2: Explore - Not Dead End AND Not Visited -> ExploreMove(m)
        self.kb.tell((Predicate("ExploreMove", [v_next]), [
            Predicate("Safe", [v_next]),
            Predicate("NotDeadEnd", [v_next]),
            Predicate("NotVisited", [v_next])
        ]))

        # Rule 3: Good Move (General) - Not Dead End -> GoodMove(m)
        self.kb.tell((Predicate("GoodMove", [v_next]), [
            Predicate("Safe", [v_next]),
            Predicate("NotDeadEnd", [v_next])
        ]))
        
        # Rule 4: Any Safe Move -> PossibleMove(m)
        self.kb.tell((Predicate("PossibleMove", [v_next]), [
            Predicate("Safe", [v_next])
        ]))

        # 3. Decide
        # Priority 1: BestMove
        query = Predicate("BestMove", [Variable("m")])
        results = list(self.kb.ask(query))
        if results:
            choice = results[0][Variable("m")]
            parts = choice.name.split('_')
            return (int(parts[1]), int(parts[2]))

        # Priority 2: ExploreMove (Unvisited & Not Dead End)
        query = Predicate("ExploreMove", [Variable("m")])
        results = list(self.kb.ask(query))
        if results:
            import random
            choice = random.choice(results)[Variable("m")]
            parts = choice.name.split('_')
            return (int(parts[1]), int(parts[2]))

        # Priority 3: GoodMove (Avoid Dead Ends, but maybe visited)
        query = Predicate("GoodMove", [Variable("m")])
        results = list(self.kb.ask(query))
        if results:
            # Pick random good move
            import random
            choice = random.choice(results)[Variable("m")]
            parts = choice.name.split('_')
            return (int(parts[1]), int(parts[2]))

        # Priority 4: PossibleMove (Fallback)
        query = Predicate("PossibleMove", [Variable("m")])
        results = list(self.kb.ask(query))
        if results:
            import random
            choice = random.choice(results)[Variable("m")]
            parts = choice.name.split('_')
            return (int(parts[1]), int(parts[2]))

        return None