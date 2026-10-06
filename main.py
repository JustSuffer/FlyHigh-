"""
FlyHigh! - 3D Volleyball Game
Entry Point
"""
import sys
import os

# Ensure current folder is in Python module search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game import VolleyballGame

def main():
    game = VolleyballGame()
    game.run()

if __name__ == "__main__":
    main()
