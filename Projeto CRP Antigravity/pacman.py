from typing import Tuple, Set, Dict, List
import random
import os
import sys
import time

# Importar agentes fantasmas existentes
# Assumindo que o pacote src está no python path.
# Como pacman.py está na raiz e src é um subdiretório, isso deve funcionar se executado da raiz.
try:
    from src.agents.prop_ghosts import StalkerGhost, AmbushGhost
except ImportError:
    print("Erro ao importar fantasmas proposicionais.")
    pass

try:
    from src.agents.fol_ghost import StrategicGhost
except ImportError:
    print("Erro ao importar fantasma FOL.")
    pass

Coord = Tuple[int, int]


def get_pressed_key() -> str:
    """Verifica se uma tecla de seta ou 'q' foi pressionada.
        Retorna 'UP', 'DOWN', 'LEFT', 'RIGHT', 'QUIT', ou None."""
    # Verificar tipo de SO primeiro
    if os.name == 'nt':
        # Solução para Windows
        try:
            import msvcrt
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                # Prefixo de tecla de seta
                if ch in [b'\x00', b'\xe0']:
                    ch2 = msvcrt.getch()
                    # Mapear para direção
                    if ch2 == b'H':
                        return 'UP'
                    elif ch2 == b'P':
                        return 'DOWN'
                    elif ch2 == b'M':
                        return 'RIGHT'
                    elif ch2 == b'K':
                        return 'LEFT'
                elif ch.decode('utf-8', errors='ignore').lower() == 'q':
                    return 'QUIT'
            return None
        except ImportError:
            return None
    else:
        # Solução para Unix/Linux/macOS
        try:
            import tty
            import termios
            import select
            tty.setcbreak(sys.stdin.fileno(), termios.TCSANOW)
        
            # Verificar se há entrada disponível (não bloqueante)
            if not select.select([sys.stdin], [], [], 0)[0]:
                return None

            ch = sys.stdin.read(1)
            # Lidar com teclas de seta (sequências de escape)
            if ch == '\x1b':
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    # Mapear para direção
                    if ch3 == 'A':
                        return 'UP'
                    elif ch3 == 'B':
                        return 'DOWN'
                    elif ch3 == 'C':
                        return 'RIGHT'
                    elif ch3 == 'D':
                        return 'LEFT'
            elif ch.lower() == 'q':
                return 'QUIT'
            return None
        except (ImportError, AttributeError):
            return None


class Environment:
    """Grelha representando o ambiente do jogo."""
    def __init__(
        self,
        w: int,
        h: int,
        walls: Set[Coord] = None,
        pellets: Set[Coord] = None,
        start_pos: Coord = (0, 0)
    ):
        self.w, self.h = w, h
        self.walls: Set[Coord] = set(walls or set())
        self.pellets: Set[Coord] = set(pellets or set())
        self.pacman_pos: Coord = start_pos
        self.time: int = 0
        self.finished: bool = False
        self.won: bool = False
        self.ghosts: List = [] # Lista para manter os agentes fantasmas
        self.lives: int = 3
        
        # Posições iniciais dos fantasmas (lógica simples: cantos ou locais específicos)
        # Por enquanto, podemos gerá-los ou apenas escolher espaços vazios
        self.ghost_starts = []

    def add_ghost(self, ghost):
        self.ghosts.append(ghost)
        # Atribuir uma posição inicial para o fantasma
        # Tentar encontrar um local longe do pacman ou apenas um local vazio aleatório
        import random
        while True:
            rx = random.randint(0, self.w - 1)
            ry = random.randint(0, self.h - 1)
            pos = (rx, ry)
            if pos not in self.walls and pos != self.pacman_pos:
                ghost.set_position(pos)
                self.ghost_starts.append(pos)
                break

    def in_bounds(self, c: Coord) -> bool:
        """Retorna True se a coordenada c estiver dentro dos limites da grelha."""
        x, y = c
        return 0 <= x < self.w and 0 <= y < self.h

    def blocked(self, c: Coord) -> bool:
        """Retorna True se a coordenada c estiver bloqueada por paredes ou limites."""
        return (not self.in_bounds(c)) or (c in self.walls)

    # --- Métodos de compatibilidade para Agentes Fantasmas (imitando a classe Grid) ---
    def is_in_bounds(self, x: int, y: int) -> bool:
        return self.in_bounds((x, y))

    def is_wall(self, x: int, y: int) -> bool:
        return (x, y) in self.walls

    def get_view(self, x: int, y: int, radius: int = 4) -> Dict[Coord, str]:
        """
        Retorna uma visão da grelha ao redor de (x, y) para o fantasma.
        Retorna um dicionário: {(nx, ny): 'Wall' ou 'Empty'}
        """
        view = {}
        # Raio quadrado simples ou linha de visão. 
        # A lógica original parecia esperar um dicionário de células visíveis.
        # Vamos fornecer uma área quadrada ao redor do fantasma.
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if self.is_in_bounds(nx, ny):
                    # Verificação simples de Linha de Visão poderia ser adicionada aqui se necessário
                    # Por enquanto, apenas retorna o tipo de célula
                    if self.is_wall(nx, ny):
                        view[(nx, ny)] = 'Wall'
                    else:
                        view[(nx, ny)] = 'Empty'
        return view
    # -------------------------------------------------------------------

    def sense(self) -> Dict:
        """Retorna um dicionário de percepção descrevendo o estado atual."""
        return dict(
            pos=self.pacman_pos,
            pellet_here=(self.pacman_pos in self.pellets),
            time=self.time,
            finished=self.finished
        )

    def step(self, action: str):
        """Avança o ambiente um passo dada uma string de ação.
            Ações suportadas: 'UP', 'DOWN', 'LEFT', 'RIGHT' para mover."""
        if self.finished:
            return

        self.time += 1

        # Mover Pacman
        moves = {'RIGHT': (1, 0), 'LEFT': (-1, 0), 'DOWN': (0, 1), 'UP': (0, -1)}
        if action in moves:
            dx, dy = moves[action]
            nx, ny = self.pacman_pos[0] + dx, self.pacman_pos[1] + dy
            if not self.blocked((nx, ny)):
                self.pacman_pos = (nx, ny)

        # Coletar pastilha se necessário
        if self.pacman_pos in self.pellets:
            self.pellets.remove(self.pacman_pos)
            # Pontuação poderia ser adicionada aqui

        # Verificar condição de vitória
        if len(self.pellets) == 0:
            self.finished = True
            self.won = True
            return

        # Atualizar Fantasmas
        self.update_ghosts()

        # Verificar Colisões
        self.check_collisions()

    def update_ghosts(self):
        for ghost in self.ghosts:
            # Obter percepção
            view = self.get_view(ghost.position[0], ghost.position[1])
            
            # Verificar se o Pacman é visível para o fantasma
            # Verificação simples: o Pacman está na visão?
            pacman_visible_pos = None
            if self.pacman_pos in view:
                # Verificar Linha de Visão se estritamente necessário, mas por enquanto:
                pacman_visible_pos = self.pacman_pos

            ghost.update(view, pacman_visible_pos)
            
            # Decidir movimento
            # O fantasma espera que 'grid' seja passado. 'self' atua como a grelha.
            new_pos = ghost.decide_move(self)
            
            if new_pos:
                # Validar movimento apenas por precaução
                if self.is_in_bounds(new_pos[0], new_pos[1]) and not self.is_wall(new_pos[0], new_pos[1]):
                    ghost.position = new_pos

    def check_collisions(self):
        for ghost in self.ghosts:
            if ghost.position == self.pacman_pos:
                self.handle_death()
                break

    def handle_death(self):
        self.lives -= 1
        if self.lives <= 0:
            self.finished = True
            self.won = False
        else:
            # Reiniciar posições
            # Encontrar uma posição segura para o Pacman (longe dos fantasmas)
            import random
            
            safe_distance = 5
            attempts = 0
            while attempts < 100:
                rx = random.randint(0, self.w - 1)
                ry = random.randint(0, self.h - 1)
                pos = (rx, ry)
                
                if not self.blocked(pos):
                    # Verificar distância de todos os fantasmas
                    is_safe = True
                    for ghost in self.ghosts:
                        gx, gy = ghost.position
                        dist = abs(rx - gx) + abs(ry - gy) # Distância Manhattan
                        if dist < safe_distance:
                            is_safe = False
                            break
                    
                    if is_safe:
                        self.pacman_pos = pos
                        return
                
                attempts += 1
            
            # Fallback se não encontrar posição segura em 100 tentativas
            # Tentar voltar para o início se seguro, ou apenas (0,0)
            self.pacman_pos = (0, 0)
            if self.blocked(self.pacman_pos):
                 self.pacman_pos = (1, 1)

    def render(self) -> str:
        """Retorna uma visualização em string de várias linhas da grelha.

        Legenda:
            'P' - Pac-Man
            '#' - Parede
            '.' - Pastilha
            ' ' - Espaço vazio
            'G' - Fantasma
        """
        # Códigos de cores ANSI
        BLUE = '\033[94m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        PINK = '\033[95m'
        ORANGE = '\033[33m' # Usando amarelo escuro/standard para laranja se 256 cores não for garantido, ou 38;5;208
        # Vamos tentar um laranja mais distinto se possível, mas 33 é seguro.
        # Melhor: Red=91, Pink=95, Orange=33 (pode confundir com Pacman 93).
        # Vamos usar:
        COLOR_MAP = {
            'Red': '\033[91m',
            'Pink': '\033[95m',
            'Orange': '\033[33m', # Amarelo normal
            'Green': '\033[92m',
            'Blue': '\033[94m'
        }
        RESET = '\033[0m'

        buf: List[str] = []
        status_line = f"t={self.time} | pastilhas={len(self.pellets)} | Vidas={self.lives}"
        buf.append(status_line)

        # Criar um mapa de posições de fantasmas para consulta rápida
        ghost_map = {g.position: g for g in self.ghosts}

        for y in range(self.h):
            row = []
            for x in range(self.w):
                c = (x, y)
                if c == self.pacman_pos:
                    ch = f"{YELLOW}P{RESET}"
                elif c in ghost_map:
                    # Cor baseada no fantasma
                    g = ghost_map[c]
                    color_code = COLOR_MAP.get(g.color, GREEN) # Default verde
                    ch = f"{color_code}G{RESET}" 
                elif c in self.walls:
                    ch = f"{BLUE}#{RESET}"
                elif c in self.pellets:
                    ch = f"{YELLOW}.{RESET}"
                else:
                    ch = ' '
                row.append(ch)
            buf.append(''.join(row))

        if self.finished:
            if self.won:
                buf.append(f"{YELLOW}VITÓRIA! VOCÊ COMEU TODAS AS PASTILHAS!{RESET}")
            else:
                buf.append(f"{GREEN}GAME OVER! OS FANTASMAS PEGARAM VOCÊ!{RESET}")

        return '\n'.join(buf)


def generate_maze(
    w: int,
    h: int,
    wall_density: float = 0.15,
    pellet_density: float = 0.15
) -> Tuple[Set[Coord], Set[Coord], Coord]:
    """Gerar paredes, pastilhas e a posição inicial do Pac-Man."""
    # Adicionar paredes aleatórias
    rng = random.Random()
    
    # Definir paredes de borda
    border_walls = set()
    for x in range(w):
        border_walls.add((x, 0))
        border_walls.add((x, h - 1))
    for y in range(h):
        border_walls.add((0, y))
        border_walls.add((w - 1, y))
        
    # Espaço interno para paredes aleatórias
    inner_positions = [(x, y) for y in range(1, h - 1) for x in range(1, w - 1)]
    
    k_walls = int(wall_density * len(inner_positions))
    random_walls = set(rng.sample(inner_positions, k_walls)) if k_walls > 0 else set()
    
    walls = border_walls.union(random_walls)

    # Garantir que a posição inicial do Pac-Man não contenha uma parede
    # Vamos escolher uma posição inicial segura
    pacman_start = (1, 1)
    if pacman_start in walls:
        walls.discard(pacman_start)
    
    # Identificar células livres
    all_positions = [(x, y) for y in range(0, h) for x in range(0, w)]
    free_cells = [c for c in all_positions if c not in walls and c != pacman_start]
    
    # 1. Verificar Conectividade (Flood Fill a partir do Pacman)
    # Para garantir que as pastilhas sejam acessíveis
    reachable = set()
    queue = [pacman_start]
    visited = {pacman_start}
    
    while queue:
        cx, cy = queue.pop(0)
        reachable.add((cx, cy))
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in walls and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))
                
    # 2. Filtrar células para pastilhas
    # Regra: Deve ser acessível (garantido pelo Flood Fill)
    valid_pellet_spots = [c for c in free_cells if c in reachable]

    # Colocar pastilhas em espaços válidos
    k_pellets = max(1, int(pellet_density * len(valid_pellet_spots)))
    pellets = set(rng.sample(valid_pellet_spots, k_pellets)) if k_pellets > 0 else set()

    return walls, pellets, pacman_start


def run_game(
    env: Environment,
    max_steps: int = 500,
    sleep_s: float = 0.2
):
    """Executar o jogo Pac-Man com controles de teclado."""
    action = "WAIT"

    # Renderização inicial
    os.system('cls' if os.name == 'nt' else 'clear')
    print(env.render())

    for _ in range(max_steps):
        if env.finished:
            break

        key = get_pressed_key()
        if key is not None:
            action = key

        if action == 'QUIT':
            break

        env.step(action)

        os.system('cls' if os.name == 'nt' else 'clear')
        print(env.render())
        print()
        time.sleep(sleep_s)


def run_pacman():
    """Ponto de entrada do jogo: criar um labirinto, instanciar o ambiente, executar o jogo."""
    width, height = 20, 15
    walls, pellets, pacman_start = generate_maze(w=width, h=height)

    env = Environment(
        width, height,
        walls=walls,
        pellets=pellets,
        start_pos=pacman_start
    )
    
    # Armazenar posição inicial para reinício
    env.start_pos = pacman_start

    # Adicionar Fantasmas
    # Precisamos garantir que as importações funcionaram
    try:
        if 'StalkerGhost' in globals():
            env.add_ghost(StalkerGhost(color="Red"))
        if 'AmbushGhost' in globals():
            env.add_ghost(AmbushGhost(color="Pink"))
        if 'StrategicGhost' in globals():
            env.add_ghost(StrategicGhost(color="Orange"))
    except Exception as e:
        print(f"Aviso: Erro ao adicionar fantasmas: {e}")

    run_game(env)


if __name__ == "__main__":
    run_pacman()
