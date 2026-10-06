"""
FlyHigh! - 3D Volleyball Game
Volleyball Court & Stadium Arena Renderer
Clean arcade low-poly aesthetics inspired by 'Just Volleyball'.
"""
import pyray as pr
from constants import (
    COURT_LENGTH, COURT_WIDTH, HALF_LENGTH, HALF_WIDTH,
    ATTACK_LINE_DIST, NET_HEIGHT, NET_BOTTOM_HEIGHT,
    NET_WIDTH, NET_THICKNESS, POST_DISTANCE, ANTENNA_HEIGHT,
    Team
)

# Color Scheme (Modern International Volleyball Arena)
COLOR_INNER_COURT = pr.Color(42, 134, 204, 255)    # Vibrant Royal Cyan/Blue
COLOR_OUTER_COURT = pr.Color(235, 115, 40, 255)    # Warm Terracotta Orange
COLOR_FLOOR_WOOD  = pr.Color(185, 130, 85, 255)    # Gym floor surrounding
COLOR_COURT_LINES = pr.Color(255, 255, 255, 255)   # Clean White
COLOR_ATTACK_LINE = pr.Color(255, 255, 255, 255)
COLOR_NET_MESH    = pr.Color(25, 25, 25, 160)       # Dark mesh
COLOR_NET_TAPE    = pr.Color(250, 250, 250, 255)   # Crisp white tape
COLOR_NET_POST    = pr.Color(60, 65, 75, 255)      # Sturdy steel posts
COLOR_ANTENNA_RED = pr.Color(230, 40, 40, 255)
COLOR_ANTENNA_WHT = pr.Color(255, 255, 255, 255)
COLOR_BLEACHERS   = pr.Color(70, 75, 88, 255)
COLOR_SEATS_1     = pr.Color(200, 50, 50, 255)
COLOR_SEATS_2     = pr.Color(50, 100, 200, 255)
COLOR_WALL        = pr.Color(35, 38, 48, 255)

class Court:
    def __init__(self):
        pass

    def is_in_bounds(self, x, z):
        """Returns True if (x, z) is strictly inside regulation boundary lines."""
        return (-HALF_WIDTH <= x <= HALF_WIDTH) and (-HALF_LENGTH <= z <= HALF_LENGTH)

    def is_player_court(self, z):
        return -HALF_LENGTH <= z <= 0.0

    def is_opponent_court(self, z):
        return 0.0 <= z <= HALF_LENGTH

    def clamp_player_position(self, x, z, team, allow_freezone=True):
        """Clamps player inside valid movement zone (can step into freezone but not cross net)."""
        limit_x = HALF_WIDTH + (2.5 if allow_freezone else 0.0)
        clamped_x = max(-limit_x, min(limit_x, x))
        
        if team == Team.PLAYER:
            # Player side: Z from (-HALF_LENGTH - 3.5) up to net (-0.25)
            min_z = -HALF_LENGTH - (3.5 if allow_freezone else 0.0)
            max_z = -0.28  # Prevent walking through net
            clamped_z = max(min_z, min(max_z, z))
        else:
            # Opponent side: Z from (+0.25) up to (+HALF_LENGTH + 3.5)
            min_z = 0.28   # Net barrier
            max_z = HALF_LENGTH + (3.5 if allow_freezone else 0.0)
            clamped_z = max(min_z, min(max_z, z))
            
        return clamped_x, clamped_z

    def draw(self):
        """Renders 3D court, lines, net, posts, antennae, and arena stadium."""
        # 1. Base Gym Arena Floor (Huge surrounding hall)
        pr.draw_cube(pr.Vector3(0, -0.08, 0), 38.0, 0.1, 46.0, COLOR_WALL)

        # 2. Outer Court Border / Free Zone (Orange perimeter)
        pr.draw_cube(pr.Vector3(0, -0.04, 0), 15.0, 0.04, 25.0, COLOR_OUTER_COURT)

        # 3. Inner Playing Court (Cyan / Royal Blue)
        pr.draw_cube(pr.Vector3(0, 0.0, 0), COURT_WIDTH, 0.02, COURT_LENGTH, COLOR_INNER_COURT)

        # 4. Court Boundary Lines (0.05m width, elevated slightly to prevent z-fighting)
        lw = 0.06
        # Sidelines (X = -4.5 and X = +4.5)
        pr.draw_cube(pr.Vector3(-HALF_WIDTH, 0.015, 0), lw, 0.02, COURT_LENGTH, COLOR_COURT_LINES)
        pr.draw_cube(pr.Vector3(HALF_WIDTH, 0.015, 0), lw, 0.02, COURT_LENGTH, COLOR_COURT_LINES)
        
        # Endlines / Baselines (Z = -9.0 and Z = +9.0)
        pr.draw_cube(pr.Vector3(0, 0.015, -HALF_LENGTH), COURT_WIDTH, 0.02, lw, COLOR_COURT_LINES)
        pr.draw_cube(pr.Vector3(0, 0.015, HALF_LENGTH), COURT_WIDTH, 0.02, lw, COLOR_COURT_LINES)

        # Center Line under net (Z = 0.0)
        pr.draw_cube(pr.Vector3(0, 0.015, 0), COURT_WIDTH, 0.02, lw * 1.5, COLOR_COURT_LINES)

        # Attack Lines (3m from net: Z = -3.0 and Z = +3.0)
        pr.draw_cube(pr.Vector3(0, 0.015, -ATTACK_LINE_DIST), COURT_WIDTH, 0.02, lw, COLOR_ATTACK_LINE)
        pr.draw_cube(pr.Vector3(0, 0.015, ATTACK_LINE_DIST), COURT_WIDTH, 0.02, lw, COLOR_ATTACK_LINE)

        # 5. Net Structure
        # Steel Posts
        post_rad = 0.08
        pr.draw_cylinder(pr.Vector3(-POST_DISTANCE, 0, 0), post_rad, post_rad, 2.65, 12, COLOR_NET_POST)
        pr.draw_cylinder(pr.Vector3(POST_DISTANCE, 0, 0), post_rad, post_rad, 2.65, 12, COLOR_NET_POST)
        
        # Top White Band (Y = 2.43)
        pr.draw_cube(pr.Vector3(0, NET_HEIGHT, 0), NET_WIDTH, 0.09, NET_THICKNESS, COLOR_NET_TAPE)
        # Bottom White Band (Y = 1.43)
        pr.draw_cube(pr.Vector3(0, NET_BOTTOM_HEIGHT, 0), NET_WIDTH, 0.06, NET_THICKNESS, COLOR_NET_TAPE)

        # Net Mesh Grid (Alternating translucent dark mesh strips)
        mesh_h = NET_HEIGHT - NET_BOTTOM_HEIGHT
        mesh_center_y = (NET_HEIGHT + NET_BOTTOM_HEIGHT) / 2.0
        pr.draw_cube(pr.Vector3(0, mesh_center_y, 0), NET_WIDTH, mesh_h, 0.02, COLOR_NET_MESH)
        
        # Thin Net Cables / Ropes across mesh
        for y_step in range(1, 6):
            cy = NET_BOTTOM_HEIGHT + (mesh_h * y_step / 6.0)
            pr.draw_cube(pr.Vector3(0, cy, 0), NET_WIDTH, 0.015, 0.03, pr.Color(150, 150, 150, 180))

        # 6. Antennae (Striped Red & White, at X = -4.5 and +4.5)
        for ant_x in [-HALF_WIDTH, HALF_WIDTH]:
            # Extends from bottom of net (1.43) to 80cm above top of net (3.23m)
            total_ant_h = (NET_HEIGHT + ANTENNA_HEIGHT) - NET_BOTTOM_HEIGHT
            segments = 10
            seg_h = total_ant_h / segments
            for s in range(segments):
                sy = NET_BOTTOM_HEIGHT + s * seg_h + seg_h / 2.0
                scol = COLOR_ANTENNA_RED if (s % 2 == 0) else COLOR_ANTENNA_WHT
                pr.draw_cylinder(pr.Vector3(ant_x, sy - seg_h/2.0, 0), 0.02, 0.02, seg_h, 8, scol)

        # 7. Referee Stand (Side of the net at X = -POST_DISTANCE)
        pr.draw_cube(pr.Vector3(-POST_DISTANCE - 0.6, 1.1, 0), 0.7, 0.1, 0.8, pr.Color(40, 100, 180, 255))
        pr.draw_cylinder(pr.Vector3(-POST_DISTANCE - 0.6, 0, 0), 0.06, 0.06, 1.1, 8, COLOR_NET_POST)
        # Referee Ladder rungs
        for r in range(4):
            ry = 0.25 * (r + 1)
            pr.draw_cube(pr.Vector3(-POST_DISTANCE - 0.6, ry, 0), 0.35, 0.04, 0.04, COLOR_NET_POST)

        # 8. Stadium Bleachers / Stands (North & South ends and Sidelines)
        # East Stand (+X)
        self._draw_stands(pr.Vector3(12.5, 0, 0), 4.5, 30.0, 1)
        # West Stand (-X)
        self._draw_stands(pr.Vector3(-12.5, 0, 0), 4.5, 30.0, -1)
        # South Stand (-Z)
        self._draw_end_stands(pr.Vector3(0, 0, -17.0), 22.0, 4.0)
        # North Stand (+Z)
        self._draw_end_stands(pr.Vector3(0, 0, 17.0), 22.0, 4.0)

        # Stadium Floodlight Poles
        self._draw_light_tower(pr.Vector3(-11.0, 0, -14.0))
        self._draw_light_tower(pr.Vector3(11.0, 0, -14.0))
        self._draw_light_tower(pr.Vector3(-11.0, 0, 14.0))
        self._draw_light_tower(pr.Vector3(11.0, 0, 14.0))

    def _draw_stands(self, pos, width, length, dir_x):
        steps = 5
        step_h = 0.75
        step_d = width / steps
        for i in range(steps):
            sx = pos.x + dir_x * (i * step_d)
            sy = (i + 1) * step_h / 2.0
            sh = (i + 1) * step_h
            pr.draw_cube(pr.Vector3(sx, sy, pos.z), step_d, sh, length, COLOR_BLEACHERS)
            # Row of spectator seats on step
            seat_col = COLOR_SEATS_1 if (i % 2 == 0) else COLOR_SEATS_2
            pr.draw_cube(pr.Vector3(sx, (i + 1) * step_h + 0.1, pos.z), step_d * 0.7, 0.18, length * 0.95, seat_col)

    def _draw_end_stands(self, pos, width, depth):
        steps = 4
        step_h = 0.8
        step_d = depth / steps
        sign = 1 if pos.z > 0 else -1
        for i in range(steps):
            sz = pos.z + sign * (i * step_d)
            sy = (i + 1) * step_h / 2.0
            sh = (i + 1) * step_h
            pr.draw_cube(pr.Vector3(pos.x, sy, sz), width, sh, step_d, COLOR_BLEACHERS)

    def _draw_light_tower(self, pos):
        # Tower pole
        h = 10.0
        pr.draw_cylinder(pr.Vector3(pos.x, 0, pos.z), 0.18, 0.12, h, 8, pr.Color(80, 85, 95, 255))
        # Lamp frame at top
        pr.draw_cube(pr.Vector3(pos.x, h, pos.z), 1.8, 0.6, 0.5, pr.Color(230, 235, 240, 255))
        # Bright warm glow box
        pr.draw_cube(pr.Vector3(pos.x, h - 0.2, pos.z), 1.6, 0.2, 0.4, pr.Color(255, 255, 210, 240))
