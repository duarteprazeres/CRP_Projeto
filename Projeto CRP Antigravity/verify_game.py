import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from pacman import Environment, generate_maze, StalkerGhost, AmbushGhost, StrategicGhost

def verify():
    print("Initializing Environment...")
    width, height = 20, 15
    walls, pellets, pacman_start = generate_maze(w=width, h=height)

    env = Environment(
        width, height,
        walls=walls,
        pellets=pellets,
        start_pos=pacman_start
    )
    
    print("Adding Ghosts...")
    try:
        env.add_ghost(StalkerGhost(color="Red"))
        print("Added StalkerGhost (Red)")
        env.add_ghost(AmbushGhost(color="Pink"))
        print("Added AmbushGhost (Pink)")
        env.add_ghost(StrategicGhost(color="Orange"))
        print("Added StrategicGhost (Orange)")
    except Exception as e:
        print(f"FAILED to add ghosts: {e}")
        return

    print("Running Game Loop for 10 steps...")
    try:
        for i in range(10):
            print(f"Step {i+1}")
            env.step("WAIT")
            # print(env.render()) # Optional: print render to see grid
            
            # Check if ghosts moved (optional, but good to know)
            for g in env.ghosts:
                print(f"  {g.color} Ghost at {g.position}")
                
    except Exception as e:
        print(f"CRASH during game loop: {e}")
        import traceback
        traceback.print_exc()
        return

    print("Verification Successful!")

if __name__ == "__main__":
    verify()
