import curses
import time
from src.game import Game
from src.agents.prop_ghosts import StalkerGhost, RandomGhost
from src.agents.fol_ghost import FOLGhost

def draw(stdscr, game, message=None):
    stdscr.erase()
    
    # Colors
    # 1=Wall(Blue), 2=Pellet(White), 3=Pacman(Yellow), 4=Red, 5=Green, 6=Pink/Magenta, 7=Cyan
    curses.init_pair(1, curses.COLOR_BLUE, -1)
    curses.init_pair(2, curses.COLOR_WHITE, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)
    curses.init_pair(5, curses.COLOR_GREEN, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)
    curses.init_pair(7, curses.COLOR_CYAN, -1)

    # Draw Grid
    for y in range(game.grid.height):
        for x in range(game.grid.width):
            char = ' '
            attr = curses.color_pair(0)
            
            if (x, y) == game.pacman_pos:
                char = 'C' # Pacman shape
                attr = curses.color_pair(3) | curses.A_BOLD
            elif (x, y) in [g.position for g in game.ghosts]:
                # Find which ghost
                ghost = next(g for g in game.ghosts if g.position == (x, y))
                char = 'M'
                if ghost.color == "Red":
                    attr = curses.color_pair(4) | curses.A_BOLD
                elif ghost.color == "Green":
                    attr = curses.color_pair(5) | curses.A_BOLD
                elif ghost.color == "Pink":
                    attr = curses.color_pair(6) | curses.A_BOLD
                else:
                    attr = curses.color_pair(4) | curses.A_BOLD
            elif game.grid.is_wall(x, y):
                char = '#'
                attr = curses.color_pair(1)
            elif (x, y) in game.grid.pellets:
                char = '.'
                attr = curses.color_pair(2)
            
            try:
                stdscr.addch(y, x, char, attr)
            except curses.error:
                pass # Ignore errors if terminal is too small

    # HUD
    hud_y = game.grid.height + 1
    try:
        stdscr.addstr(hud_y, 0, f" Score: {game.score} ", curses.color_pair(5) | curses.A_BOLD)
        stdscr.addstr(hud_y, 20, f" Lives: {game.lives} ", curses.color_pair(5) | curses.A_BOLD)
        stdscr.addstr(hud_y, 40, " Controls: Arrow Keys | q=Quit ", curses.color_pair(5))
    except curses.error:
        pass

    # Message
    if message:
        msg_y = game.grid.height // 2
        msg_x = max(0, (game.grid.width // 2) - (len(message) // 2))
        try:
            stdscr.addstr(msg_y, msg_x, message, curses.color_pair(6) | curses.A_BOLD | curses.A_BLINK)
        except curses.error:
            pass

    stdscr.refresh()

def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    stdscr.nodelay(True)
    stdscr.timeout(150) # Game speed

    game = Game()
    
    # Add real ghosts
    game.add_ghost(StalkerGhost(color="Red"))
    game.add_ghost(RandomGhost(color="Green"))
    game.add_ghost(FOLGhost(color="Pink"))

    key_map = {
        curses.KEY_UP: 'UP',
        curses.KEY_DOWN: 'DOWN',
        curses.KEY_LEFT: 'LEFT',
        curses.KEY_RIGHT: 'RIGHT'
    }

    while True:
        msg = None
        if game.game_over:
            msg = " GAME OVER " if not game.won else " VICTORY! "
        
        draw(stdscr, game, msg)

        key = stdscr.getch()
        
        if key == ord('q'):
            break
        
        if game.game_over:
            stdscr.timeout(-1) # Wait for quit
            continue

        if key in key_map:
            game.handle_input(key_map[key])
        
        # Update game state (ghosts move every frame/tick)
        # To make it fair, maybe ghosts move slower? 
        # For now, update every tick.
        game.update()

if __name__ == "__main__":
    curses.wrapper(main)
