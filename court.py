"""
FlyHigh! - 3D Volleyball Game
Beach Volleyball Court & Coastal Arena Renderer
Sunny arcade beach aesthetic matching the reference screenshots:
- Golden sand court with vibrant blue boundary lines
- Sparkling tropical ocean and animated shoreline on the right
- Palm trees, wooden promenade, and coastal buildings on the left
- Colorful beach umbrellas, sun loungers, and picnic benches
- Blue net posts with crisp mesh and red/white striped antennae
"""
import math
import pyray as pr
from constants import (
    COURT_LENGTH, COURT_WIDTH, HALF_LENGTH, HALF_WIDTH,
    ATTACK_LINE_DIST, NET_HEIGHT, NET_BOTTOM_HEIGHT,
    NET_WIDTH, NET_THICKNESS, POST_DISTANCE, ANTENNA_HEIGHT,
    Team
)

# Color Palette: Sunny Tropical Beach
COLOR_SAND_BASE     = pr.Color(238, 206, 158, 255)  # Warm golden beach sand
COLOR_SAND_WARM     = pr.Color(245, 218, 172, 255)  # Sunlit sand dunes
COLOR_SAND_DAMP     = pr.Color(215, 180, 135, 255)  # Moist shoreline sand
COLOR_COURT_LINES   = pr.Color(35, 120, 245, 255)   # Crisp vibrant beach blue lines
COLOR_ATTACK_LINES  = pr.Color(50, 140, 250, 230)
COLOR_OCEAN_SHALLOW = pr.Color(65, 195, 230, 245)   # Turquoise shore water
COLOR_OCEAN_DEEP    = pr.Color(22, 105, 195, 255)   # Deep tropical azure
COLOR_OCEAN_FOAM    = pr.Color(255, 255, 255, 230)  # Sparkling wave crests
COLOR_BOARDWALK     = pr.Color(190, 145, 105, 255)  # Wooden promenade walkway
COLOR_WOOD_RAIL     = pr.Color(140, 100, 70, 255)
COLOR_PALM_TRUNK    = pr.Color(140, 95, 58, 255)
COLOR_PALM_LEAF_1   = pr.Color(55, 165, 65, 255)
COLOR_PALM_LEAF_2   = pr.Color(75, 190, 80, 255)
COLOR_NET_POST      = pr.Color(35, 115, 235, 255)   # Vibrant blue steel posts
COLOR_NET_MESH      = pr.Color(30, 35, 45, 175)     # Dark athletic mesh
COLOR_NET_TAPE      = pr.Color(250, 252, 255, 255)  # Crisp white tape bands
COLOR_ANTENNA_RED   = pr.Color(235, 45, 45, 255)
COLOR_ANTENNA_WHT   = pr.Color(255, 255, 255, 255)
COLOR_UMBRELLA_RED  = pr.Color(235, 60, 70, 255)
COLOR_UMBRELLA_BLU  = pr.Color(50, 140, 240, 255)
COLOR_UMBRELLA_WHT  = pr.Color(250, 250, 250, 255)

class Court:
    def __init__(self):
        # Precomputed palm tree positions along the boardwalk and tropical beach shoreline
        self.palm_positions = [
            (-15.5, -14.0), (-16.0, -7.0), (-15.5, 0.0),
            (-16.0, 7.0), (-15.5, 14.0), (-16.2, 21.0), (-16.2, -21.0),
            (14.5, 16.0), (16.0, 6.0), (15.0, -8.0)
        ]
        # City building footprints on the promenade
        self.buildings = [
            (-23.0, -18.0, 7.0, 12.0, 7.0, pr.Color(235, 238, 245, 255)),
            (-24.0, -7.0, 8.0, 16.0, 9.0, pr.Color(185, 210, 235, 255)),
            (-23.5, 5.0, 7.5, 13.5, 8.0, pr.Color(245, 235, 220, 255)),
            (-24.5, 17.0, 8.0, 15.0, 9.0, pr.Color(220, 230, 240, 255)),
        ]
        # Beach umbrellas and loungers scattered along the shore
        self.umbrellas = [
            (11.0, -10.0, COLOR_UMBRELLA_RED),
            (12.5, -4.0, COLOR_UMBRELLA_BLU),
            (11.5, 8.0, COLOR_UMBRELLA_RED),
            (12.0, 14.0, COLOR_UMBRELLA_BLU),
            (0.0, 18.0, COLOR_UMBRELLA_BLU),
            (-6.0, 18.5, COLOR_UMBRELLA_RED),
        ]

    def is_in_bounds(self, x, z):
        """Returns True if (x, z) is strictly inside regulation boundary lines."""
        return (-HALF_WIDTH <= x <= HALF_WIDTH) and (-HALF_LENGTH <= z <= HALF_LENGTH)

    def is_player_court(self, z):
        return -HALF_LENGTH <= z <= 0.0

    def is_opponent_court(self, z):
        return 0.0 <= z <= HALF_LENGTH

    def clamp_player_position(self, x, z, team, allow_freezone=True):
        """Clamps player inside valid movement zone (generous free zone, cannot cross net)."""
        limit_x = HALF_WIDTH + (4.0 if allow_freezone else 0.0)
        clamped_x = max(-limit_x, min(limit_x, x))
        
        if team == Team.PLAYER:
            min_z = -HALF_LENGTH - (5.0 if allow_freezone else 0.0)
            max_z = -0.28  # Net barrier
            clamped_z = max(min_z, min(max_z, z))
        else:
            min_z = 0.28   # Net barrier
            max_z = HALF_LENGTH + (5.0 if allow_freezone else 0.0)
            clamped_z = max(min_z, min(max_z, z))
            
        return clamped_x, clamped_z

    def draw(self):
        """Renders 3D beach volleyball court, tropical ocean, palm trees, and coastal resort."""
        t = pr.get_time()

        # Golden Hour Beach Sun & Tropical Sky Glow (Matching reference photo)
        pr.draw_sphere(pr.Vector3(-22.0, 15.0, 42.0), 4.6, pr.Color(255, 245, 215, 255))
        pr.draw_sphere(pr.Vector3(-22.0, 15.0, 42.0), 8.2, pr.Color(255, 220, 140, 90))
        # Warm golden-hour horizon haze
        pr.draw_cube(pr.Vector3(0, 3.5, 46.0), 90.0, 7.0, 1.5, pr.Color(255, 215, 160, 45))

        # 1. EXPANSIVE GOLDEN SAND BEACH (Extends across the whole scene)
        pr.draw_cube(pr.Vector3(0, -0.06, 0), 70.0, 0.1, 80.0, COLOR_SAND_BASE)
        # Gentle sunlit sand mounds
        pr.draw_cube(pr.Vector3(0, -0.03, 0), 38.0, 0.05, 48.0, COLOR_SAND_WARM)
        # Slightly darker playing field perimeter
        pr.draw_cube(pr.Vector3(0, -0.01, 0), COURT_WIDTH + 4.5, 0.03, COURT_LENGTH + 5.5, pr.Color(230, 196, 146, 255))

        # 2. TROPICAL OCEAN & ANIMATED SHORELINE (+X side)
        wave_offset = math.sin(t * 1.8) * 0.45
        shore_x = 15.0 + wave_offset
        # Shallow water shelf
        pr.draw_cube(pr.Vector3(shore_x + 6.0, -0.02, 0), 12.0, 0.04, 80.0, COLOR_OCEAN_SHALLOW)
        # Deep ocean plane
        pr.draw_cube(pr.Vector3(shore_x + 22.0, -0.01, 0), 22.0, 0.05, 80.0, COLOR_OCEAN_DEEP)
        # Animated white foam wave ribbon
        pr.draw_cube(pr.Vector3(shore_x, 0.01, 0), 0.75, 0.03, 80.0, COLOR_OCEAN_FOAM)
        # Secondary rolling wave crest
        crest_x = shore_x + 7.5 + math.sin(t * 1.2 + 1.5) * 0.6
        pr.draw_cube(pr.Vector3(crest_x, 0.02, 0), 0.45, 0.03, 80.0, COLOR_OCEAN_FOAM)

        # 3. WOODEN BOARDWALK PROMENADE (-X side)
        pr.draw_cube(pr.Vector3(-18.5, 0.08, 0), 6.5, 0.16, 80.0, COLOR_BOARDWALK)
        # Boardwalk edge curbs & safety rails
        pr.draw_cube(pr.Vector3(-15.2, 0.18, 0), 0.22, 0.32, 80.0, COLOR_WOOD_RAIL)
        for rz in range(-36, 38, 4):
            pr.draw_cube(pr.Vector3(-15.2, 0.38, float(rz)), 0.12, 0.45, 0.12, COLOR_WOOD_RAIL)

        # 4. PALM TREES ALONG PROMENADE
        for px, pz in self.palm_positions:
            self._draw_palm_tree(px, pz)

        # 5. COASTAL RESORT BUILDINGS & HOTELS
        for bx, bz, bw, bh, bd, bcol in self.buildings:
            self._draw_building(bx, bz, bw, bh, bd, bcol)

        # 6. BEACH UMBRELLAS & LOUNGERS
        for ux, uz, ucol in self.umbrellas:
            self._draw_beach_umbrella(ux, uz, ucol)

        # 7. COURT BOUNDARY LINES (Crisp Blue Lines on the Sand, matching screenshot)
        lw = 0.075
        lh = 0.02
        # Sidelines (X = -HALF_WIDTH and X = +HALF_WIDTH)
        pr.draw_cube(pr.Vector3(-HALF_WIDTH, lh, 0), lw, lh, COURT_LENGTH, COLOR_COURT_LINES)
        pr.draw_cube(pr.Vector3(HALF_WIDTH, lh, 0), lw, lh, COURT_LENGTH, COLOR_COURT_LINES)

        # Baselines (Z = -HALF_LENGTH and Z = +HALF_LENGTH)
        pr.draw_cube(pr.Vector3(0, lh, -HALF_LENGTH), COURT_WIDTH, lh, lw, COLOR_COURT_LINES)
        pr.draw_cube(pr.Vector3(0, lh, HALF_LENGTH), COURT_WIDTH, lh, lw, COLOR_COURT_LINES)

        # Center Line directly under the net (Z = 0.0)
        pr.draw_cube(pr.Vector3(0, lh, 0), COURT_WIDTH, lh, lw * 1.4, COLOR_COURT_LINES)

        # Attack Lines (3.2m from the net: Z = -ATTACK_LINE_DIST and Z = +ATTACK_LINE_DIST)
        pr.draw_cube(pr.Vector3(0, lh, -ATTACK_LINE_DIST), COURT_WIDTH, lh, lw, COLOR_ATTACK_LINES)
        pr.draw_cube(pr.Vector3(0, lh, ATTACK_LINE_DIST), COURT_WIDTH, lh, lw, COLOR_ATTACK_LINES)

        # 8. BLUE NET POSTS & VOLLEYBALL NET STRUCTURE
        post_rad = 0.09
        # Blue posts on both sides
        pr.draw_cylinder(pr.Vector3(-POST_DISTANCE, 0, 0), post_rad, post_rad, 2.70, 14, COLOR_NET_POST)
        pr.draw_cylinder(pr.Vector3(POST_DISTANCE, 0, 0), post_rad, post_rad, 2.70, 14, COLOR_NET_POST)

        # Top White Tape Band (Y = 2.43)
        pr.draw_cube(pr.Vector3(0, NET_HEIGHT, 0), NET_WIDTH, 0.10, NET_THICKNESS, COLOR_NET_TAPE)
        # Bottom White Tape Band (Y = 1.43)
        pr.draw_cube(pr.Vector3(0, NET_BOTTOM_HEIGHT, 0), NET_WIDTH, 0.06, NET_THICKNESS, COLOR_NET_TAPE)

        # Net Mesh Grid
        mesh_h = NET_HEIGHT - NET_BOTTOM_HEIGHT
        mesh_center_y = (NET_HEIGHT + NET_BOTTOM_HEIGHT) / 2.0
        pr.draw_cube(pr.Vector3(0, mesh_center_y, 0), NET_WIDTH, mesh_h, 0.02, COLOR_NET_MESH)

        # Crisp horizontal net cables
        for step in range(1, 6):
            cy = NET_BOTTOM_HEIGHT + (mesh_h * step / 6.0)
            pr.draw_cube(pr.Vector3(0, cy, 0), NET_WIDTH, 0.016, 0.025, pr.Color(160, 165, 175, 200))

        # 9. RED & WHITE STRIPED ANTENNAE
        for ant_x in [-HALF_WIDTH, HALF_WIDTH]:
            total_ant_h = (NET_HEIGHT + ANTENNA_HEIGHT) - NET_BOTTOM_HEIGHT
            segments = 10
            seg_h = total_ant_h / segments
            for s in range(segments):
                sy = NET_BOTTOM_HEIGHT + s * seg_h + seg_h / 2.0
                scol = COLOR_ANTENNA_RED if (s % 2 == 0) else COLOR_ANTENNA_WHT
                pr.draw_cylinder(pr.Vector3(ant_x, sy - seg_h/2.0, 0), 0.022, 0.022, seg_h, 8, scol)

    def _draw_palm_tree(self, px, pz):
        """Draws a stylized arcade tropical palm tree."""
        # Curved trunk segments
        trunk_h = 5.2
        pr.draw_cylinder(pr.Vector3(px, 0, pz), 0.22, 0.16, trunk_h, 8, COLOR_PALM_TRUNK)
        top_y = trunk_h

        # Palm fronds radiating outwards
        angles = [0.0, 0.78, 1.57, 2.35, 3.14, 3.92, 4.71, 5.49]
        for a in angles:
            frond_len = 2.4
            fx = px + math.cos(a) * frond_len * 0.5
            fz = pz + math.sin(a) * frond_len * 0.5
            fy = top_y + 0.35 - 0.35 * (frond_len * 0.5 / frond_len)
            col = COLOR_PALM_LEAF_1 if int(a * 10) % 2 == 0 else COLOR_PALM_LEAF_2
            pr.draw_cube(pr.Vector3(fx, fy, fz), 0.55, 0.08, frond_len, col)

        # Coconut cluster at the top
        pr.draw_sphere(pr.Vector3(px + 0.12, top_y - 0.1, pz + 0.1), 0.16, pr.Color(90, 60, 35, 255))
        pr.draw_sphere(pr.Vector3(px - 0.12, top_y - 0.1, pz + 0.1), 0.16, pr.Color(90, 60, 35, 255))
        pr.draw_sphere(pr.Vector3(px, top_y - 0.1, pz - 0.14), 0.16, pr.Color(90, 60, 35, 255))

    def _draw_building(self, bx, bz, bw, bh, bd, bcol):
        """Draws a clean low-poly coastal hotel / apartment building with windows."""
        # Building mass
        pr.draw_cube(pr.Vector3(bx, bh / 2.0, bz), bw, bh, bd, bcol)
        # Dark windows along the facade facing the beach (+X side)
        win_col = pr.Color(40, 55, 80, 220)
        floors = int(bh / 2.2)
        cols = int(bd / 2.2)
        fw_x = bx + bw / 2.0 + 0.02
        for fl in range(1, floors):
            wy = fl * 2.2
            for c in range(cols):
                wz = bz - bd / 2.0 + 1.2 + c * 2.0
                pr.draw_cube(pr.Vector3(fw_x, wy, wz), 0.04, 1.1, 1.2, win_col)

    def _draw_beach_umbrella(self, ux, uz, canopy_col):
        """Draws a striped beach umbrella and sun lounger."""
        # Wooden pole
        pr.draw_cylinder(pr.Vector3(ux, 0, uz), 0.04, 0.04, 2.3, 8, COLOR_PALM_TRUNK)
        # Umbrella cone canopy
        pr.draw_cylinder(pr.Vector3(ux, 2.1, uz), 1.6, 0.1, 0.45, 12, canopy_col)
        pr.draw_cylinder(pr.Vector3(ux, 2.2, uz), 1.1, 0.05, 0.40, 12, COLOR_UMBRELLA_WHT)
        # Sun lounger beside umbrella
        pr.draw_cube(pr.Vector3(ux + 0.8, 0.12, uz), 0.7, 0.18, 1.6, pr.Color(240, 240, 245, 255))
        pr.draw_cube(pr.Vector3(ux + 0.8, 0.32, uz - 0.5), 0.7, 0.25, 0.5, canopy_col)
