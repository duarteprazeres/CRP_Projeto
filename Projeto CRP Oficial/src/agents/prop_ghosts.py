from src.agents.ghost import Ghost
from src.logic.propositional import PropositionalKB, Symbol, And, Or, Not, Implication
import random


class PropGhost(Ghost):
    def __init__(self, color="Red"):
        super().__init__(color)
        self.kb = PropositionalKB()

    def update(self, view, pacman_pos):
        super().update(view, pacman_pos)
        # In a real full implementation, we would update the KB with every cell seen. "Cell_1_1_Safe", "Cell_1_2_Wall", etc. For performance/simplicity, we will rebuild a small local KB each turn or just add relevant facts about the immediate surroundings.
        pass


class StalkerGhost(PropGhost):
    """
    Uses Propositional Logic to chase Pacman.
    Rules:
    - If Pacman is Visible -> Chase directly.
    - If Pacman is NOT Visible but Last Known Position exists -> Go to Last Known.
    - If Lost -> Explore/Search.
    """
    def decide_move(self, grid):
        self.kb.retract_all() # Clears KB from previous turn
        x, y = self.position
        dirs = {'North': (0, -1), 'South': (0, 1), 'East': (1, 0), 'West': (-1, 0)}
        
        # Get valid moves based on BELIEF MAP (not just immediate grid, though they should match for adjacent)
        # We use the grid object passed in only to check bounds/walls for immediate execution safety,
        # but our logic should rely on self.belief_map
        valid_moves = self.get_valid_moves(grid)
        
        # 1. Add facts (atomic propositions)
        for d_name, (dx, dy) in dirs.items():
            nx, ny = x + dx, y + dy
            
            # Fact: {D}Safe
            if (nx, ny) in valid_moves:
                self.kb.tell(Symbol(f"{d_name}Safe"))
            else:
                self.kb.tell(Not(Symbol(f"{d_name}Safe")))

            # Fact: Pacman{D} (Directional sensing)
            # We use self.last_known_pacman_pos which is updated by update()
            if self.last_known_pacman_pos:
                px, py = self.last_known_pacman_pos
                
                # Check if this direction is the BEST step towards the target
                # We can use a simple distance check or BFS on belief map
                dist_current = abs(px - x) + abs(py - y)
                dist_new = abs(px - nx) + abs(py - ny)
                
                if dist_new < dist_current:
                     self.kb.tell(Symbol(f"Pacman{d_name}"))
                else:
                     self.kb.tell(Not(Symbol(f"Pacman{d_name}")))

        # 2. Add rules
        # Rule 1: Chase - If Pacman is in direction D and D is safe, then BestMoveD
        for d in dirs:
            self.kb.tell(Implication(
                And(Symbol(f"Pacman{d}"), Symbol(f"{d}Safe")), 
                Symbol(f"BestMove{d}")
            ))

        # Rule 2: Explore - If D is Safe, it is a ValidMoveD
        for d in dirs:
            self.kb.tell(Implication(Symbol(f"{d}Safe"), Symbol(f"ValidMove{d}")))

        # 3. Decide movement
        best_moves = []
        valid_moves_list = []
        
        # Check for BestMove (Chase)
        for d, (dx, dy) in dirs.items():
            if self.kb.ask(Symbol(f"BestMove{d}")):
                best_moves.append((dx, dy))
        
        # Check for ValidMove (Fallback)
        for d, (dx, dy) in dirs.items():
            if self.kb.ask(Symbol(f"ValidMove{d}")):
                valid_moves_list.append((dx, dy))

        # Execute Decision
        if best_moves:
            self.last_move = random.choice(best_moves)
            return (x + self.last_move[0], y + self.last_move[1])
        
        if valid_moves_list:
            # If we have no "BestMove" (maybe Pacman is not known, or we are blocked),
            # Try to move towards the "Unknown" or just random valid
            # For Stalker, if lost, maybe go to random valid
            self.last_move = random.choice(valid_moves_list)
            return (x + self.last_move[0], y + self.last_move[1])
        
        return None


class AmbushGhost(PropGhost):
    """
    Uses Propositional Logic to Ambush Pacman.
    Rules:
    - Target is 4 steps ahead of Pacman's current direction.
    - If Pacman not visible, target last known pos.
    """
    def __init__(self, color="Pink"):
        super().__init__(color)
        self.last_move = None

    def decide_move(self, grid):
        self.kb.retract_all()
        x, y = self.position
        dirs = {'North': (0, -1), 'South': (0, 1), 'East': (1, 0), 'West': (-1, 0)}
        valid_moves = self.get_valid_moves(grid)

        # 1. Determine Target
        target_x, target_y = x, y # Default to current if no info
        
        if self.last_known_pacman_pos:
            px, py = self.last_known_pacman_pos
            # Try to predict ahead. We don't know Pacman's direction explicitly unless we track history,
            # but we can guess or just target the position itself if we can't predict.
            # For simplicity in this PL agent without history tracking: Target Pacman directly but maybe offset?
            # Actually, let's try to target a specific offset if we can infer direction, 
            # but since we don't have history here easily, let's just target Pacman but use different rules.
            # OR, we can assume Pacman is moving away from us?
            
            # Let's implement a simple "Ambush" by targeting a spot that is NOT Pacman's exact spot but close?
            # Better: "Pinky" usually targets 4 tiles in front. Without direction, we target the cell 
            # that minimizes distance to (px, py) but also maximizes distance to other ghosts? Too complex for PL.
            
            # Let's stick to: Target = Pacman Pos. BUT, we prioritize moves that cut off?
            # Let's use the "Ambush" logic: If we are close to Pacman, try to move to a neighbor of Pacman that he is NOT in.
            target_x, target_y = px, py

        # 2. Add Facts
        for d_name, (dx, dy) in dirs.items():
            nx, ny = x + dx, y + dy
            
            if (nx, ny) in valid_moves:
                self.kb.tell(Symbol(f"{d_name}Safe"))
            else:
                self.kb.tell(Not(Symbol(f"{d_name}Safe")))

            # Direction to Target
            # Check if this direction reduces distance to Target
            dist_current = abs(target_x - x) + abs(target_y - y)
            dist_new = abs(target_x - nx) + abs(target_y - ny)
            
            if dist_new < dist_current:
                self.kb.tell(Symbol(f"ToTarget{d_name}"))
            else:
                self.kb.tell(Not(Symbol(f"ToTarget{d_name}")))

        # 3. Add Rules
        # Rule: If Safe and ToTarget -> AmbushMove
        for d in dirs:
            self.kb.tell(Implication(
                And(Symbol(f"{d}Safe"), Symbol(f"ToTarget{d}")),
                Symbol(f"AmbushMove{d}")
            ))
            
        # Rule: If Safe -> PossibleMove (Fallback)
        for d in dirs:
            self.kb.tell(Implication(Symbol(f"{d}Safe"), Symbol(f"PossibleMove{d}")))

        # 4. Decide
        ambush_moves = []
        possible_moves = []
        
        for d, (dx, dy) in dirs.items():
            if self.kb.ask(Symbol(f"AmbushMove{d}")):
                ambush_moves.append((dx, dy))
            if self.kb.ask(Symbol(f"PossibleMove{d}")):
                possible_moves.append((dx, dy))
                
        if ambush_moves:
            self.last_move = random.choice(ambush_moves)
            return (x + self.last_move[0], y + self.last_move[1])
            
        if possible_moves:
            self.last_move = random.choice(possible_moves)
            return (x + self.last_move[0], y + self.last_move[1])
            
        return None
