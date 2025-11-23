import os
import sys
import time
from src.grid import Grid

# Simple map for testing
DEFAULT_MAP = """
#####################
#                   #
# ### ## ### ## ### #
# #   #       #   # #
# ### ## ### ## ### #
#                   #
# ### ##     ## ### #
#       #   #       #
###     #   #     ###
#       #GGG#       #
###     #   #     ###
#       #   #       #
# ### ##  ##### ### #
#                   #
# ### ## ### ## ### #
# #   #       #   # #
# ### ## ### ## ### #
#         P         #
#####################
"""

class Game:
    def __init__(self):
        self.grid = Grid(DEFAULT_MAP)
        self.grid.randomize_pellets(50) # Randomly place 50 pellets
        self.pacman_pos = self.grid.pacman_start
        self.ghosts = [] # Will be populated with agent objects
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.won = False

    def add_ghost(self, ghost):
        self.ghosts.append(ghost)
        # Set ghost start pos if not already set?
        # Assuming ghost knows its start pos or we set it here
        if len(self.grid.ghost_starts) >= len(self.ghosts):
             start_pos = self.grid.ghost_starts[len(self.ghosts)-1]
             ghost.set_position(start_pos)
        else:
             # Fallback if not enough start spots
             ghost.set_position((1, 1)) 

    def handle_input(self, key):
        dx, dy = 0, 0
        if key == 'UP': dy = -1
        elif key == 'DOWN': dy = 1
        elif key == 'LEFT': dx = -1
        elif key == 'RIGHT': dx = 1
        
        new_x, new_y = self.pacman_pos[0] + dx, self.pacman_pos[1] + dy
        
        if self.grid.is_in_bounds(new_x, new_y) and not self.grid.is_wall(new_x, new_y):
            self.pacman_pos = (new_x, new_y)
            if self.grid.remove_pellet(new_x, new_y):
                self.score += 10
                if not self.grid.pellets:
                    self.won = True
                    self.game_over = True

    def update(self):
        if self.game_over: return

        # Check collisions
        ghost_positions = [g.position for g in self.ghosts]
        if self.pacman_pos in ghost_positions:
            self.handle_death()
            return

        # Update ghosts
        for ghost in self.ghosts:
            # Get perception
            view = self.grid.get_view(ghost.position[0], ghost.position[1])
            ghost.update(view, self.pacman_pos if self.pacman_pos in view else None)
            
            # Move ghost
            new_pos = ghost.decide_move(self.grid)
            if new_pos:
                ghost.position = new_pos

        # Check collisions again after movement
        ghost_positions = [g.position for g in self.ghosts]
        if self.pacman_pos in ghost_positions:
            self.handle_death()

    def handle_death(self):
        self.lives -= 1
        print("Pac-Man died!")
        if self.lives <= 0:
            self.game_over = True
        else:
            # Reset positions
            self.pacman_pos = self.grid.pacman_start
            for i, ghost in enumerate(self.ghosts):
                if i < len(self.grid.ghost_starts):
                    ghost.set_position(self.grid.ghost_starts[i])

    def render(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"Score: {self.score}  Lives: {self.lives}")
        ghost_positions = [g.position for g in self.ghosts]
        self.grid.print_grid(self.pacman_pos, ghost_positions)
        if self.game_over:
            if self.won:
                print("YOU WIN!")
            else:
                print("GAME OVER")

