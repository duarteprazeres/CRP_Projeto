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
        self.kb.retract_all() # Limpa a KB do turno anterior
        x, y = self.position
        dirs = {'North': (0, -1), 'South': (0, 1), 'East': (1, 0), 'West': (-1, 0)}
        pacman_visible = self.last_known_pacman_pos and (self.last_known_pacman_pos != self.position)
        valid_moves = self.get_valid_moves(grid)
        
        # 1. Adicionar Factos (Proposições Atómicas)
        for d_name, (dx, dy) in dirs.items():
            nx, ny = x + dx, y + dy
            
            # Facto: {D}Safe
            if (nx, ny) in valid_moves:
                self.kb.tell(Symbol(f"{d_name}Safe"))
            
            # Facto: Pacman{D} (APENAS se for na célula vizinha - Reflexivo)
            if pacman_visible and (nx, ny) == self.last_known_pacman_pos:
                self.kb.tell(Symbol(f"Pacman{d_name}"))

        # 2. Adicionar Regras
        # Regra Prioritária (Chase Reflexivo): (Pacman{D} & {D}Safe) -> BestMove{D}
        for d in dirs:
            self.kb.tell(Implication(
                And(Symbol(f"Pacman{d}"), Symbol(f"{d}Safe")), 
                Symbol(f"BestMove{d}")
            ))

        # Regra Secundária (Fallback): {D}Safe -> SafeMove{D}
        for d in dirs:
            self.kb.tell(Implication(Symbol(f"{d}Safe"), Symbol(f"SafeMove{d}")))


        # 3. Decidir o Movimento
        best_moves = []
        safe_moves = []
        
        # Prioridade 1: BestMove (Perseguição Reflexiva)
        for d, (dx, dy) in dirs.items():
            if self.kb.ask(Symbol(f"BestMove{d}")):
                best_moves.append((dx, dy))
        
        if best_moves:
            self.last_move = random.choice(best_moves)
            return (x + self.last_move[0], y + self.last_move[1])

        # Prioridade 2: SafeMove (Exploração de baixo esforço/aleatório seguro)
        for d, (dx, dy) in dirs.items():
            if self.kb.ask(Symbol(f"SafeMove{d}")):
                # Dupla verificação para garantir que o movimento é válido na grelha
                if (x + dx, y + dy) in valid_moves: 
                    safe_moves.append((dx, dy))
                
        if safe_moves:
            self.last_move = random.choice(safe_moves)
            return (x + self.last_move[0], y + self.last_move[1])
        
        return None

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
        self.kb.retract_all() # Limpa a KB do turno anterior
        x, y = self.position
        moves = self.get_valid_moves(grid)
        
        dirs = {'North': (0, -1), 'South': (0, 1), 'East': (1, 0), 'West': (-1, 0)}
        reverse_dir = {
            (0, -1): (0, 1), (0, 1): (0, -1), (1, 0): (-1, 0), (-1, 0): (1, 0)
        }
        
        # 1. Adicionar Factos
        for d_name, (dx, dy) in dirs.items():
            nx, ny = x + dx, y + dy
            
            # Facto: {D}Safe
            if (nx, ny) in moves:
                self.kb.tell(Symbol(f"{d_name}Safe"))
                
                # Facto: {D}Backtrack
                if self.last_move and (dx, dy) == reverse_dir.get(self.last_move):
                     self.kb.tell(Symbol(f"{d_name}Backtrack"))
            else:
                # Se não é Safe, dizer que não o é (útil para o TT-entails)
                self.kb.tell(Not(Symbol(f"{d_name}Safe")))

        # 2. Adicionar Regras
        # Regra Única: {D}Safe & ~{D}Backtrack -> GoodMove{D} (Movimento de Exploração)
        good_moves = []
        for d, (dx, dy) in dirs.items():
            rule = Implication(
                And(Symbol(f"{d}Safe"), Not(Symbol(f"{d}Backtrack"))), 
                Symbol(f"GoodMove{d}")
            )
            self.kb.tell(rule)
            
            # 3. Decidir o Movimento
            if self.kb.ask(Symbol(f"GoodMove{d}")):
                good_moves.append((dx, dy))

        # Prioridade 1: GoodMove (Exploração Anti-Backtrack)
        if good_moves:
            # Escolhe aleatoriamente um movimento que não seja retroceder
            self.last_move = random.choice(good_moves)
            return (x + self.last_move[0], y + self.last_move[1])
        
        # Fallback: Se estiver cercado ou apenas puder retroceder, retrocede
        if moves: 
            mx, my = random.choice(moves)
            self.last_move = (mx - x, my - y)
            return (mx, my)
            
        return None
