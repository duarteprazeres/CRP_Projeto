from src.agents.ghost import Ghost
from src.logic.propositional import PropositionalKB, Symbol, And, Or, Not, Implication
import random

class PropGhost(Ghost):
    def __init__(self, color="Red"):
        super().__init__(color)
        self.kb = PropositionalKB()

    def update(self, view, pacman_pos):
        super().update(view, pacman_pos)
        # In a real full implementation, we would update the KB with every cell seen.
        # "Cell_1_1_Safe", "Cell_1_2_Wall", etc.
        # For performance/simplicity, we will rebuild a small local KB each turn 
        # or just add relevant facts about the immediate surroundings.
        pass

class StalkerGhost(PropGhost):
    """
    Uses Propositional Logic to chase Pacman.
    Rules:
    - If Pacman is North and North is Safe -> Move North
    - If Pacman is South and South is Safe -> Move South
    ...
    """
    def decide_move(self, grid):
        # NOTE: We ignore the 'grid' argument to enforce partial observability.
        # We only use self.belief_map.
        
        self.kb.retract_all()
        x, y = self.position
        
        # 1. Identify valid moves from Belief Map
        # We can only move to cells we KNOW are Empty (or visited).
        # If a cell is Unknown, we might risk it? No, usually we move to known empty.
        # But to explore, we must move towards Unknown.
        # Let's say we can move to any cell that is NOT a Wall.
        
        possible_moves = []
        neighbors = [(0, -1), (0, 1), (1, 0), (-1, 0)] # N, S, E, W
        for dx, dy in neighbors:
            nx, ny = x + dx, y + dy
            cell_type = self.belief_map.get((nx, ny), 'Unknown')
            if cell_type != 'Wall':
                possible_moves.append((nx, ny))
        
        if not possible_moves:
            return (x, y)

        # 2. Goal Selection
        target = self.last_known_pacman_pos
        
        # If we don't have a target or we reached it and he's gone, explore.
        if not target or target == (x, y):
            # Exploration: Find nearest 'Unknown' cell or just random walk
            # For Stalker, let's just random walk if lost
            return random.choice(possible_moves)

        # 3. Pathfinding (BFS) to Target
        # We want to move towards 'target' using only known safe cells.
        # If target is in 'Unknown' area, we path to the boundary.
        
        path = self._bfs((x, y), target)
        
        if path and len(path) > 1:
            return path[1] # Next step
        
        # If no path found (blocked by walls or unknown), random move
        return random.choice(possible_moves)

    def _bfs(self, start, goal):
        queue = [[start]]
        visited = {start}
        
        # Limit depth to avoid lag
        max_depth = 20 
        
        while queue:
            path = queue.pop(0)
            node = path[-1]
            
            if len(path) > max_depth:
                continue
                
            if node == goal:
                return path
            
            for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
                nx, ny = node[0] + dx, node[1] + dy
                if (nx, ny) not in visited:
                    # We can traverse Empty and Unknown cells.
                    # We treat Unknown as walkable for planning.
                    cell_type = self.belief_map.get((nx, ny), 'Unknown')
                    if cell_type != 'Wall':
                        visited.add((nx, ny))
                        new_path = list(path)
                        new_path.append((nx, ny))
                        queue.append(new_path)
        return None

class RandomGhost(PropGhost):
    """
    Uses Propositional Logic but with different rules.
    Patroller: Prefers to keep moving in the same direction until blocked, then turns.
    Avoids immediate 180 turns to prevent stuck loops.
    """
    def __init__(self, color="Blue"):
        super().__init__(color)
        self.last_move = None

    def decide_move(self, grid):
        self.kb.retract_all()
        x, y = self.position
        
        # Get valid moves from Belief Map
        moves = []
        neighbors = [(0, -1), (0, 1), (1, 0), (-1, 0)]
        for dx, dy in neighbors:
            nx, ny = x + dx, y + dy
            cell_type = self.belief_map.get((nx, ny), 'Unknown')
            if cell_type != 'Wall':
                moves.append((nx, ny))
                
        # Check if Pacman is within 4 cells (Manhattan distance) and chase!
        target = self.last_known_pacman_pos
        if target:
            dist = abs(target[0] - x) + abs(target[1] - y)
            if dist <= 4:
                # Greedy chase: pick move that minimizes distance to target
                best_move = None
                min_dist = float('inf')
                
                for mx, my in moves:
                    d = abs(target[0] - mx) + abs(target[1] - my)
                    if d < min_dist:
                        min_dist = d
                        best_move = (mx, my)
                
                if best_move:
                    self.last_move = (best_move[0] - x, best_move[1] - y)
                    return best_move
        
        dirs = {'North': (0, -1), 'South': (0, 1), 'East': (1, 0), 'West': (-1, 0)}
        reverse_dir = {
            (0, -1): (0, 1), (0, 1): (0, -1), (1, 0): (-1, 0), (-1, 0): (1, 0)
        }
        
        # 1. Add facts
        for d_name, (dx, dy) in dirs.items():
            nx, ny = x + dx, y + dy
            if (nx, ny) in moves:
                self.kb.tell(Symbol(f"{d_name}Safe"))
                if self.last_move and (dx, dy) == reverse_dir.get(self.last_move):
                     self.kb.tell(Symbol(f"{d_name}Backtrack"))
            else:
                self.kb.tell(Not(Symbol(f"{d_name}Safe")))

        # 2. Rules
        # GoodMove is any Safe move that is NOT Backtrack
        for d in dirs:
            self.kb.tell(Implication(And(Symbol(f"{d}Safe"), Not(Symbol(f"{d}Backtrack"))), Symbol(f"GoodMove{d}")))

        # 3. Decide
        # Get all GoodMoves
        good_moves = []
        for d, (dx, dy) in dirs.items():
            if self.kb.ask(Symbol(f"GoodMove{d}")):
                good_moves.append((dx, dy))
        
        # If we have good moves (forward/turn), pick one randomly
        if good_moves:
            choice = random.choice(good_moves)
            self.last_move = choice
            return (x + choice[0], y + choice[1])
            
        # If no good moves (dead end), we must backtrack
        if moves:
            choice = random.choice(moves)
            dx, dy = choice[0] - x, choice[1] - y
            self.last_move = (dx, dy)
            return choice
            
        return (x, y)
