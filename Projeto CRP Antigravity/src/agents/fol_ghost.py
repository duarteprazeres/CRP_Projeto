from src.agents.ghost import Ghost
from src.logic.first_order import FOLKB, Predicate, Variable, Constant, fol_bc_ask
import random

# Fact Predicate: The cell (x, y) was visited
class Visited(Predicate): pass 

# Fact Predicate: The cell (x, y) was visited
class LastSeen(Predicate): pass 

# Conclusion Predicate: The best move for chasing
class BestChaseMove(Predicate): pass 

# Conclusion Predicate: The best move for exploration (avoiding visited cells)
class PossibleExploreMove(Predicate): pass 

# Variables (for use in rules)
v_me = Constant("Me")
v_curr = Variable("curr")
v_next = Variable("next")
v_target = Variable("target")

class FOLGhost(Ghost):
    def __init__(self, color="Pink"):
        super().__init__(color)
        self.kb = FOLKB()
        # We might want to keep a persistent KB for the map
        # But for movement decisions, we might clear the transient state

    # EM src/agents/fol_ghost.py, dentro da classe FOLGhost:

    def decide_move(self, grid):
        # 1. Limpar KB para estado transitório (mantendo apenas memória de Visited)
        self.kb.clauses = [] 
        
        x, y = self.position
        me = Constant("Me")
        curr_c = Constant(f"C_{x}_{y}")
        
        # Adicionar Fato: O Fantasma está na posição atual
        self.kb.tell((Predicate("At", [me, curr_c]), [])) 
        
        neighbors = [(0, -1), (0, 1), (1, 0), (-1, 0)]
        valid_moves = []
        
        # 1. Adicionar Factos (Percepção e Memória)
        for dx, dy in neighbors:
            nx, ny = x + dx, y + dy
            next_c = Constant(f"C_{nx}_{ny}")
            cell_type = self.belief_map.get((nx, ny), 'Unknown')
            
            if cell_type != 'Wall':
                valid_moves.append((nx, ny))
                
                # Fato 1: Conectividade (Relação entre células)
                self.kb.tell((Predicate("Connected", [curr_c, next_c]), []))
                # Fato 2: Segurança (Predicado Unário)
                self.kb.tell((Predicate("Safe", [next_c]), []))
            
            # Fato 3 (Memória FOL): Adicionar 'Visited' se a célula foi visitada (usa self.visited)
            if (nx, ny) in self.visited:
                self.kb.tell((Predicate("Visited", [next_c]), []))
            
            # Fato 4 (Percepção de Pacman): Se Pacman está adjacente
            if self.last_known_pacman_pos == (nx, ny):
                 self.kb.tell((Predicate("PacmanAt", [next_c]), []))
        
        # 2. Adicionar Regras (Lógica de Primeira Ordem)
        v_next = Variable("m") # Usamos 'm' como variável para o movimento

        # Regra 1 (BestMove - CHASE): PacmanAt(?m) & Safe(?m) -> BestMove(?m)
        self.kb.tell((Predicate("BestMove", [v_next]), [
            Predicate("PacmanAt", [v_next]),
            Predicate("Safe", [v_next])
        ]))

        # Regra 2 (ExploreMove - EXPLORER #7): Safe(?m) -> PossibleMove(?m)
        # Este é o nosso conjunto de movimentos seguros base. A lógica de "não visitado" será no Python.
        self.kb.tell((Predicate("PossibleMove", [v_next]), [
            Predicate("Safe", [v_next])
        ]))
        
        
        # 3. Decidir o Movimento (Query)
        
        # Prioridade 1: BestMove (Perseguição imediata)
        query_chase = Predicate("BestMove", [Variable("m")])
        results_chase = list(self.kb.ask(query_chase))
        if results_chase:
            choice = results_chase[0][Variable("m")]
            parts = choice.name.split('_')
            return (int(parts[1]), int(parts[2]))

        # Prioridade 2: ExploreMove (Explorador #7) - Tentar NÃO visitar
        query_explore = Predicate("PossibleMove", [Variable("m")])
        results_explore = list(self.kb.ask(query_explore))
        
        # Filtrar os movimentos seguros para escolher apenas os que NÃO foram visitados.
        unvisited_moves = []
        for res in results_explore:
            choice = res[Variable("m")]
            parts = choice.name.split('_')
            nx, ny = int(parts[1]), int(parts[2])
            
            # Se o predicado Visited(C_nx_ny) NÃO está na KB, é um movimento de Exploração
            if (nx, ny) not in self.visited:
                unvisited_moves.append((nx, ny))

        if unvisited_moves:
            # Escolhe aleatoriamente uma célula não visitada (Exploração pura)
            mx, my = random.choice(unvisited_moves)
            self.last_move = (mx - x, my - y)
            return (mx, my)

        # Prioridade 3: Fallback (Mover para qualquer célula segura, mesmo que visitada)
        if valid_moves:
            mx, my = random.choice(valid_moves)
            self.last_move = (mx - x, my - y)
            return (mx, my)
        
        self.last_move = None
        return None