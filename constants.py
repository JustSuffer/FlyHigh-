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

# Court Geometry (Expanded & Wider for Exciting Arcade Action)
COURT_LENGTH = 19.0
COURT_WIDTH = 10.4
HALF_LENGTH = COURT_LENGTH / 2.0  # 9.5m
HALF_WIDTH = COURT_WIDTH / 2.0    # 5.2m
ATTACK_LINE_DIST = 3.2            # 3.2m from net

# Net Specifications
NET_HEIGHT = 2.43                 # Men's regulation net top height
NET_BOTTOM_HEIGHT = 1.43          # Bottom tape height (1.0m mesh height)
NET_WIDTH = 11.2                  # Extends beyond expanded court sidelines
NET_THICKNESS = 0.08
POST_DISTANCE = 5.8               # Net posts X position (+/- 5.8m)
ANTENNA_HEIGHT = 0.8              # Extends 80cm above net

# Ball Physics
BALL_RADIUS = 0.28
BALL_MASS = 0.27                  # kg
GRAVITY = -11.5                   # m/s^2 (floaty, realistic arcade volleyball gravity)
BALL_AIR_DRAG = 0.995
BALL_BOUNCE_RESTITUTION = 0.65    # Floor bounciness
NET_RESTITUTION = 0.35            # Net bounce absorption

# Player Specifications
PLAYER_RADIUS = 0.45
PLAYER_HEIGHT = 1.85
PLAYER_SPEED = 7.8                # Running speed (m/s)
PLAYER_SPRINT_SPEED = 10.8        # Dive / Sprint speed
PLAYER_JUMP_FORCE = 7.4           # Standard jump velocity (m/s)
PLAYER_SUPER_JUMP_FORCE = 10.5     # Charged Super Jump velocity (clears net height easily!)
PLAYER_REACH_RADIUS = 1.8         # Hit reach sphere
PLAYER_SPIKE_REACH = 2.3          # Reach in air for spikes
BLOCK_REACH_RADIUS = 1.45         # Net block reach radius

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
    MENU_IDLE = auto()   # Posed in main menu holding ball under arm
    RUN = auto()
    JUMP = auto()
    SERVE_HOLD = auto()   # Ready stance holding ball in hands at baseline
    SERVE_TOSS = auto()   # Upward toss release animation
    BUMP = auto()         # Bump / Dig / Receive (L-CTRL or Bump)
    SET = auto()          # Overhead Set / Pass (RMB)
    SPIKE = auto()        # Spike Attack / Power Serve (LMB in air)
    DUMP = auto()         # Dump / Soft Tip (E in air)
    SETTER_DUMP = auto()  # Setter Dump Surprise Attack (RMB + E grounded)
    ROLL_DIG = auto()     # Acrobatic Diving Roll Dig (L-CTRL + RMB, 5s CD)
    AIR_BAILOUT = auto()  # Emergency Mid-Air Tap/Bailout (L-CTRL + LMB in air)
    BLOCK = auto()        # Net Block
    DIVE = auto()         # Dive
    CELEBRATE = auto()
    DISAPPOINT = auto()

class TimingRating(Enum):
    GREEN = "PERFECT!"    # Flawless timing
    YELLOW = "GOOD"       # Standard timing
    RED = "OFF-TIME"      # Mistimed / Mismit

ROLL_DIG_COOLDOWN = 5.0

# Supported Screen Resolutions
RESOLUTIONS = [
    (1280, 720, "1280x720 (HD)"),
    (1600, 900, "1600x900 (HD+)"),
    (1920, 1080, "1920x1080 (FHD)")
]

class GameMode(Enum):
    TEAM_3V3 = "3 vs 3 (Full Team Match)"
    SOLO_1V1 = "1 vs 1 (Solo Match)"
    PRACTICE = "Free Practice"

class AIDifficulty(Enum):
    EASY = "Easy (Casual)"
    MEDIUM = "Normal (Arcade)"
    HARD = "Hard (Challenger)"

