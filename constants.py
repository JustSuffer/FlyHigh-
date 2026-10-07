"""
FlyHigh! - 3D Volleyball Game
Game Constants and Configuration
"""
from enum import Enum, auto

# Screen Settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TARGET_FPS = 60
GAME_TITLE = "FlyHigh! - 3D Volleyball"

# Court Geometry (Standard Volleyball Proportions in Meters)
# Court is 18m long (Z from -9 to +9), 9m wide (X from -4.5 to +4.5)
COURT_LENGTH = 18.0
COURT_WIDTH = 9.0
HALF_LENGTH = COURT_LENGTH / 2.0  # 9.0m
HALF_WIDTH = COURT_WIDTH / 2.0    # 4.5m
ATTACK_LINE_DIST = 3.0            # 3.0m from net

# Net Specifications
NET_HEIGHT = 2.43                 # Men's regulation net top height
NET_BOTTOM_HEIGHT = 1.43          # Bottom tape height (1.0m mesh height)
NET_WIDTH = 9.5                   # Extends slightly beyond court sidelines
NET_THICKNESS = 0.08
POST_DISTANCE = 5.2               # Net posts X position (+/- 5.2m)
ANTENNA_HEIGHT = 0.8              # Extends 80cm above net

# Ball Physics
BALL_RADIUS = 0.28
BALL_MASS = 0.27                  # kg
GRAVITY = -19.6                   # m/s^2 (snappy arcade gravity)
BALL_AIR_DRAG = 0.994
BALL_BOUNCE_RESTITUTION = 0.65    # Floor bounciness
NET_RESTITUTION = 0.35            # Net bounce absorption

# Player Specifications
PLAYER_RADIUS = 0.45
PLAYER_HEIGHT = 1.85
PLAYER_SPEED = 7.5                # Running speed (m/s)
PLAYER_SPRINT_SPEED = 10.5        # Dive / Sprint speed
PLAYER_JUMP_FORCE = 8.5           # Jump velocity (m/s)
PLAYER_REACH_RADIUS = 1.6         # Hit reach sphere
PLAYER_SPIKE_REACH = 2.1          # Reach in air for spikes

# Aiming System
AIM_OFFSET_MAX_X = 3.8
AIM_OFFSET_MAX_Z = 7.8

# Teams and Roles
class Team(Enum):
    PLAYER = 0      # Near side (Z negative: -9 to 0)
    OPPONENT = 1    # Far side (Z positive: 0 to +9)

class MatchState(Enum):
    TITLE_SCREEN = auto()
    SERVE_READY = auto()
    SERVE_TOSSED = auto()
    IN_RALLY = auto()
    POINT_SCORED = auto()
    SET_OVER = auto()
    MATCH_OVER = auto()
    PAUSED = auto()

class PlayerAction(Enum):
    IDLE = auto()
    RUN = auto()
    JUMP = auto()
    BUMP = auto()     # Manşet (Dig / Receive)
    SET = auto()      # Pas (Set / Overhead pass)
    SPIKE = auto()    # Smaç (Attack / Spike)
    BLOCK = auto()    # Blok
    DIVE = auto()     # Plonjon / Dive
    CELEBRATE = auto()
    DISAPPOINT = auto()

class GameMode(Enum):
    TEAM_3V3 = "3 vs 3 (Full Team Match)"
    SOLO_1V1 = "1 vs 1 (Solo Match)"
    PRACTICE = "Free Practice"

class AIDifficulty(Enum):
    EASY = "Easy (Casual)"
    MEDIUM = "Normal (Arcade)"
    HARD = "Hard (Challenger)"
