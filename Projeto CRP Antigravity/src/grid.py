import math

class Grid:
    def __init__(self, layout):
        self.layout = [list(row) for row in layout.strip().split('\n')]
        self.height = len(self.layout)
        self.width = len(self.layout[0])
        self.walls = set()
        self.pellets = set()
        self.pacman_start = (0, 0)
        self.ghost_starts = []
        
        self._parse_layout()

    def _parse_layout(self):
        for y, row in enumerate(self.layout):
            for x, char in enumerate(row):
                if char == '#':
                    self.walls.add((x, y))
                elif char == '.':
                    self.pellets.add((x, y))
                elif char == 'P':
                    self.pacman_start = (x, y)
                elif char == 'G':
                    self.ghost_starts.append((x, y))

    def randomize_pellets(self, count):
        import random
        self.pellets.clear()
        candidates = []
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in self.walls and \
                   (x, y) != self.pacman_start and \
                   (x, y) not in self.ghost_starts:
                    # Avoid ghost house interior (approximate center box)
                    # Map is 21x19, center is roughly (10, 9)
                    # Ghost house x: 8-12, y: 8-10
                    if 8 <= x <= 12 and 8 <= y <= 10:
                        continue
                    candidates.append((x, y))
        
        if count > len(candidates):
            count = len(candidates)
        
        self.pellets = set(random.sample(candidates, count))

    def is_wall(self, x, y):
        return (x, y) in self.walls

    def is_in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def remove_pellet(self, x, y):
        if (x, y) in self.pellets:
            self.pellets.remove((x, y))
            return True
        return False

    def get_view(self, x, y, radius=4):
        """
        Returns a dict of visible coordinates from (x, y) with a given radius.
        Key: (nx, ny), Value: 'Wall' or 'Empty' (or other static features)
        Line of sight is blocked by walls.
        """
        visible = {}
        # Self is always visible
        visible[(x, y)] = 'Wall' if self.is_wall(x, y) else 'Empty'
        
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dx, dy in directions:
            for i in range(1, radius + 1):
                nx, ny = x + dx * i, y + dy * i
                
                if not self.is_in_bounds(nx, ny):
                    break
                
                if self.is_wall(nx, ny):
                    visible[(nx, ny)] = 'Wall'
                    # Wall is visible, but blocks further view
                    break
                else:
                    visible[(nx, ny)] = 'Empty'
        
        return visible

    def print_grid(self, pacman_pos, ghost_positions):
        # Create a copy for rendering
        output = []
        for y in range(self.height):
            row_str = ""
            for x in range(self.width):
                if (x, y) == pacman_pos:
                    row_str += "P"
                elif (x, y) in ghost_positions:
                    # Find which ghost is here? For now just G
                    # If multiple ghosts, just show one
                    idx = ghost_positions.index((x, y))
                    row_str += f"G" 
                elif (x, y) in self.walls:
                    row_str += "#"
                elif (x, y) in self.pellets:
                    row_str += "."
                else:
                    row_str += " "
            output.append(row_str)
        
        print("\n".join(output))
