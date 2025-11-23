import random

class Ghost:
    def __init__(self, color="Red"):
        self.position = (0, 0)
        self.color = color
        self.last_known_pacman_pos = None
        # Belief map: (x,y) -> 'Wall', 'Empty', 'Unknown'
        self.belief_map = {} 
        self.visited = set()
        # Possible Pacman Locations: Set of (x,y) where Pacman COULD be.
        # Initially, we don't know the grid size, so we can't populate this fully.
        # We will assume Pacman can be anywhere we haven't seen recently.
        # Actually, let's just track where we have seen 'Empty' but not Pacman.
        self.possible_pacman_locations = set()

    def set_position(self, pos):
        self.position = pos
        self.visited.add(pos)
        self.belief_map[pos] = 'Empty' # We are standing here, so it's empty

    def update(self, view, pacman_pos):
        """
        view: dict of {(x,y): 'Wall'/'Empty'} currently visible
        pacman_pos: (x,y) if visible, else None
        """
        # Update belief map with what we see
        for pos, cell_type in view.items():
            self.belief_map[pos] = cell_type
            if cell_type == 'Empty':
                # If we see an empty cell and Pacman is NOT there, remove from possible
                if pos != pacman_pos:
                    self.possible_pacman_locations.discard(pos)
                else:
                    # If we see Pacman, he is definitely here
                    self.possible_pacman_locations = {pos}
        
        if pacman_pos:
            self.last_known_pacman_pos = pacman_pos
            # If we see him, we know exactly where he is
            self.possible_pacman_locations = {pacman_pos}
        else:
            # If we don't see him, he could be in any 'Empty' cell in our belief map 
            # that is NOT in our current view.
            # Plus any 'Unknown' cells.
            # For simplicity, let's just say:
            # If we had a set of possible locations, we remove those currently visible (and empty).
            # We also need to add neighbors of existing possible locations (movement model)?
            # That's complex. Let's stick to: 
            # 1. If we see him -> Set = {pos}
            # 2. If we don't see him -> Remove visible cells from Set.
            # But we need to add cells back if he moves?
            # Let's just track "Last Known" and "Exploration" for now.
            # The "Possible Locations" is useful for "I know he is NOT here".
            pass

    def decide_move(self, grid):
        """
        Returns a tuple (x, y) for the new position.
        """
        raise NotImplementedError

    def get_valid_moves(self, grid):
        x, y = self.position
        moves = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if grid.is_in_bounds(nx, ny) and not grid.is_wall(nx, ny):
                moves.append((nx, ny))
        return moves
