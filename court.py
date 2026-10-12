"""
FlyHigh! - 3D Volleyball Game
Dynamic Multi-Arena Volleyball Court Renderer
Supports 5 Distinct Court Arenas & Dynamic Sizing (2v2, 3v3, 4v4, 5v5, 6v6):
1. Coastal Beach ("Tropical Beach") - Golden sands, turquoise ocean, palms, resort hotels, beach umbrellas
2. Orange Pro Arena ("Orange Court") - Olympic FIVB Taraflex indoor arena, arena seating, floodlights, referee tower
3. Sky High Clouds ("Sky High") - Floating celestial court in the clouds, golden sunset, marble pillars, sky rings
4. Cruise Ship Deck ("Cruise Ship") - Luxury ocean liner teak wood deck, safety railings, smokestack, open sea
5. High School Gym ("High School Gym") - Haikyuu-style Japanese high school gym, polished hardwood parquet, stage, basketball hoops, clerestory windows
"""
import math
import pyray as pr
from constants import (
    COURT_LENGTH, COURT_WIDTH, HALF_LENGTH, HALF_WIDTH,
    ATTACK_LINE_DIST, NET_HEIGHT, NET_BOTTOM_HEIGHT,
    NET_WIDTH, NET_THICKNESS, POST_DISTANCE, ANTENNA_HEIGHT,
    Team, GameMode, CourtArena, MODE_CONFIGS
)

class Court:
    def __init__(self):
        # Current dimensions (dynamically adjustable)
        self.length = COURT_LENGTH
        self.width = COURT_WIDTH
        self.half_length = HALF_LENGTH
        self.half_width = HALF_WIDTH
        self.current_arena = CourtArena.BEACH

        # Precomputed environmental elements
        self.palm_positions = [
            (-16.5, -14.0), (-17.0, -7.0), (-16.5, 0.0),
            (-17.0, 7.0), (-16.5, 14.0), (-17.2, 21.0), (-17.2, -21.0),
            (16.5, 16.0), (17.5, 6.0), (16.8, -8.0)
        ]
        self.buildings = [
            (-24.0, -18.0, 7.0, 13.0, 7.0, pr.Color(235, 238, 245, 255)),
            (-25.0, -7.0, 8.0, 17.0, 9.0, pr.Color(185, 210, 235, 255)),
            (-24.5, 5.0, 7.5, 14.5, 8.0, pr.Color(245, 235, 220, 255)),
            (-25.5, 17.0, 8.0, 16.0, 9.0, pr.Color(220, 230, 240, 255)),
        ]
        self.umbrellas = [
            (13.0, -10.0, pr.Color(235, 60, 70, 255)),
            (14.5, -4.0, pr.Color(50, 140, 240, 255)),
            (13.5, 8.0, pr.Color(235, 60, 70, 255)),
            (14.0, 14.0, pr.Color(50, 140, 240, 255)),
            (0.0, 19.0, pr.Color(50, 140, 240, 255)),
            (-7.0, 19.5, pr.Color(235, 60, 70, 255)),
        ]

    def set_mode_and_arena(self, mode: GameMode, arena: CourtArena):
        """Dynamically scales court geometry to match match format and selected venue."""
        cfg = MODE_CONFIGS.get(mode, MODE_CONFIGS[GameMode.MODE_3V3])
        self.length = cfg["court_length"]
        self.width = cfg["court_width"]
        self.half_length = self.length / 2.0
        self.half_width = self.width / 2.0
        self.current_arena = arena

    def is_in_bounds(self, x, z):
        """Returns True if (x, z) is strictly inside regulation boundary lines."""
        return (-self.half_width <= x <= self.half_width) and (-self.half_length <= z <= self.half_length)

    def is_player_court(self, z):
        return -self.half_length <= z <= 0.0

    def is_opponent_court(self, z):
        return 0.0 <= z <= self.half_length

    def clamp_player_position(self, x, z, team, allow_freezone=True):
        """Clamps player inside valid movement zone (generous free zone, cannot cross net)."""
        limit_x = self.half_width + (4.5 if allow_freezone else 0.0)
        clamped_x = max(-limit_x, min(limit_x, x))
        
        if team == Team.PLAYER:
            min_z = -self.half_length - (5.5 if allow_freezone else 0.0)
            max_z = -0.28  # Net barrier
            clamped_z = max(min_z, min(max_z, z))
        else:
            min_z = 0.28   # Net barrier
            max_z = self.half_length + (5.5 if allow_freezone else 0.0)
            clamped_z = max(min_z, min(max_z, z))
            
        return clamped_x, clamped_z

    def draw(self):
        """Renders 3D arena environment, court floor, lines, net, and antennae."""
        if self.current_arena == CourtArena.BEACH:
            self._draw_beach()
        elif self.current_arena == CourtArena.ORANGE_ARENA:
            self._draw_orange_arena()
        elif self.current_arena == CourtArena.SKY_HIGH:
            self._draw_sky_high()
        elif self.current_arena == CourtArena.CRUISE_SHIP:
            self._draw_cruise_ship()
        elif self.current_arena == CourtArena.HIGH_SCHOOL_GYM:
            self._draw_high_school_gym()

        # Net, posts, cables, and antennae are always drawn accurately for current court dimensions
        self._draw_net_and_structure()

    # =========================================================================
    # 1. TROPICAL BEACH ARENA
    # =========================================================================
    def _draw_beach(self):
        t = pr.get_time()
        # Golden Sun & Atmospheric Glow
        pr.draw_sphere(pr.Vector3(-24.0, 16.0, 44.0), 4.8, pr.Color(255, 245, 215, 255))
        pr.draw_sphere(pr.Vector3(-24.0, 16.0, 44.0), 8.5, pr.Color(255, 220, 140, 85))
        pr.draw_cube(pr.Vector3(0, 3.5, 48.0), 95.0, 7.5, 1.5, pr.Color(255, 215, 160, 45))

        # Golden Sand Ground
        pr.draw_cube(pr.Vector3(0, -0.06, 0), 75.0, 0.1, 85.0, pr.Color(238, 206, 158, 255))
        pr.draw_cube(pr.Vector3(0, -0.03, 0), 42.0, 0.05, 52.0, pr.Color(245, 218, 172, 255))
        # Playing field perimeter sand
        pr.draw_cube(pr.Vector3(0, -0.01, 0), self.width + 5.0, 0.03, self.length + 6.0, pr.Color(230, 196, 146, 255))

        # Tropical Ocean (+X side)
        wave_offset = math.sin(t * 1.8) * 0.45
        shore_x = max(16.0, self.half_width + 8.0) + wave_offset
        pr.draw_cube(pr.Vector3(shore_x + 6.0, -0.02, 0), 12.0, 0.04, 85.0, pr.Color(65, 195, 230, 245))
        pr.draw_cube(pr.Vector3(shore_x + 23.0, -0.01, 0), 24.0, 0.05, 85.0, pr.Color(22, 105, 195, 255))
        pr.draw_cube(pr.Vector3(shore_x, 0.01, 0), 0.75, 0.03, 85.0, pr.Color(255, 255, 255, 230))
        crest_x = shore_x + 7.5 + math.sin(t * 1.2 + 1.5) * 0.6
        pr.draw_cube(pr.Vector3(crest_x, 0.02, 0), 0.45, 0.03, 85.0, pr.Color(255, 255, 255, 220))

        # Boardwalk Promenade (-X side)
        bw_x = -max(19.0, self.half_width + 9.0)
        pr.draw_cube(pr.Vector3(bw_x, 0.08, 0), 7.0, 0.16, 85.0, pr.Color(190, 145, 105, 255))
        pr.draw_cube(pr.Vector3(bw_x + 3.4, 0.18, 0), 0.22, 0.32, 85.0, pr.Color(140, 100, 70, 255))
        for rz in range(-36, 38, 4):
            pr.draw_cube(pr.Vector3(bw_x + 3.4, 0.38, float(rz)), 0.12, 0.45, 0.12, pr.Color(140, 100, 70, 255))

        # Palms, buildings, umbrellas
        for px, pz in self.palm_positions:
            self._draw_palm_tree(px, pz)
        for bx, bz, bw, bh, bd, bcol in self.buildings:
            self._draw_building(bx, bz, bw, bh, bd, bcol)
        for ux, uz, ucol in self.umbrellas:
            self._draw_beach_umbrella(ux, uz, ucol)

        # Beach Boundary Lines (Vibrant Blue tape on sand)
        self._draw_lines(line_col=pr.Color(35, 120, 245, 255), attack_col=pr.Color(50, 140, 250, 230))

    # =========================================================================
    # 2. ORANGE PRO ARENA (Olympic / FIVB Taraflex)
    # =========================================================================
    def _draw_orange_arena(self):
        # Grand Indoor Stadium Hall
        pr.draw_cube(pr.Vector3(0, -0.06, 0), 85.0, 0.1, 95.0, pr.Color(18, 22, 34, 255))
        
        # Royal Blue / Navy Free Zone Surround
        fz_w = self.width + 8.0
        fz_l = self.length + 9.0
        pr.draw_cube(pr.Vector3(0, 0.005, 0), fz_w, 0.02, fz_l, pr.Color(20, 90, 195, 255))
        pr.draw_cube(pr.Vector3(0, 0.008, 0), fz_w - 0.4, 0.02, fz_l - 0.4, pr.Color(28, 110, 225, 255))

        # Iconic Bright FIVB Orange Court Infield
        pr.draw_cube(pr.Vector3(0, 0.015, 0), self.width, 0.02, self.length, pr.Color(245, 115, 25, 255))
        # Inner warm court glow
        pr.draw_cube(pr.Vector3(0, 0.016, 0), self.width - 0.3, 0.02, self.length - 0.3, pr.Color(255, 130, 35, 255))

        # White Professional Boundary Lines
        self._draw_lines(line_col=pr.Color(255, 255, 255, 255), attack_col=pr.Color(255, 255, 255, 240))

        # LED Sponsor Banners along Sidelines
        led_w = 0.25
        led_h = 0.95
        led_dist_x = self.half_width + 4.2
        pr.draw_cube(pr.Vector3(-led_dist_x, led_h / 2.0, 0), led_w, led_h, self.length + 8.0, pr.Color(15, 20, 30, 255))
        pr.draw_cube(pr.Vector3(led_dist_x, led_h / 2.0, 0), led_w, led_h, self.length + 8.0, pr.Color(15, 20, 30, 255))
        # Animated LED ticker glow
        led_glow = pr.Color(40, 200, 255, 220)
        pr.draw_cube(pr.Vector3(-led_dist_x + 0.14, led_h * 0.5, 0), 0.04, led_h * 0.7, self.length + 7.6, led_glow)
        pr.draw_cube(pr.Vector3(led_dist_x - 0.14, led_h * 0.5, 0), 0.04, led_h * 0.7, self.length + 7.6, led_glow)

        # Referee Tower (Stand) beside net
        ref_x = -self.half_width - 1.6
        pr.draw_cube(pr.Vector3(ref_x, 1.2, 0), 0.7, 2.4, 0.7, pr.Color(230, 235, 245, 255))
        pr.draw_cube(pr.Vector3(ref_x, 2.45, 0), 0.9, 0.1, 0.9, pr.Color(30, 40, 60, 255))
        pr.draw_cylinder(pr.Vector3(ref_x, 2.45, 0), 0.5, 0.5, 0.9, 8, pr.Color(240, 240, 245, 180))

        # Stadium Spectator Bleachers (Cheering Crowd Terraces)
        for tier in range(5):
            tz = self.half_length + 6.0 + tier * 2.8
            th = 0.8 + tier * 1.1
            pr.draw_cube(pr.Vector3(0, th / 2.0, tz), fz_w + 14.0, th, 2.6, pr.Color(35, 45, 65, 255))
            pr.draw_cube(pr.Vector3(0, th / 2.0, -tz), fz_w + 14.0, th, 2.6, pr.Color(35, 45, 65, 255))
            # Crowd silhouettes
            crowd_col = pr.Color(int(60 + tier * 15), int(80 + tier * 18), int(120 + tier * 20), 255)
            for cx in range(int(-fz_w / 2 - 4), int(fz_w / 2 + 5), 2):
                pr.draw_sphere(pr.Vector3(float(cx), th + 0.45, tz), 0.35, crowd_col)
                pr.draw_sphere(pr.Vector3(float(cx), th + 0.45, -tz), 0.35, crowd_col)

        # Stadium Floodlight Towers
        for fx in [-self.half_width - 9.0, self.half_width + 9.0]:
            for fz in [-self.half_length - 4.0, self.half_length + 4.0]:
                pr.draw_cylinder(pr.Vector3(fx, 0, fz), 0.28, 0.22, 12.0, 10, pr.Color(80, 90, 110, 255))
                # Floodlight bank
                pr.draw_cube(pr.Vector3(fx, 12.2, fz), 2.2, 0.8, 1.4, pr.Color(240, 245, 255, 255))
                pr.draw_sphere(pr.Vector3(fx, 12.0, fz), 1.2, pr.Color(255, 250, 230, 200))

    # =========================================================================
    # 3. SKY HIGH ARENA (Above the Clouds)
    # =========================================================================
    def _draw_sky_high(self):
        t = pr.get_time()
        # Brilliant Sunset Horizon & Sun Disk
        pr.draw_sphere(pr.Vector3(0, 18.0, 52.0), 6.5, pr.Color(255, 220, 120, 255))
        pr.draw_sphere(pr.Vector3(0, 18.0, 52.0), 12.0, pr.Color(255, 140, 70, 70))
        pr.draw_cube(pr.Vector3(0, 4.0, 56.0), 110.0, 9.0, 1.5, pr.Color(255, 160, 90, 55))

        # Sea of Puffy Clouds below the floating platform
        cloud_col = pr.Color(245, 248, 255, 235)
        for ci in range(16):
            ang = ci * 0.4 + t * 0.05
            dist = 22.0 + (ci % 4) * 8.0
            cx = math.sin(ang) * dist
            cz = math.cos(ang) * dist
            cy = -1.2 + math.sin(ang * 2.0 + ci) * 0.4
            crad = 5.5 + (ci % 3) * 2.5
            pr.draw_sphere(pr.Vector3(cx, cy, cz), crad, cloud_col)

        # Floating Crystal Court Platform Base
        plat_w = self.width + 6.0
        plat_l = self.length + 7.0
        pr.draw_cube(pr.Vector3(0, -0.4, 0), plat_w, 0.7, plat_l, pr.Color(40, 50, 75, 255))
        pr.draw_cube(pr.Vector3(0, -0.05, 0), plat_w - 0.4, 0.1, plat_l - 0.4, pr.Color(65, 85, 130, 255))
        
        # Celestial Cyan / Teal Court Floor
        pr.draw_cube(pr.Vector3(0, 0.01, 0), self.width, 0.02, self.length, pr.Color(30, 165, 215, 255))
        # Glowing inner celestial pattern
        pr.draw_cube(pr.Vector3(0, 0.012, 0), self.width - 0.4, 0.02, self.length - 0.4, pr.Color(45, 195, 245, 255))

        # Golden Celestial Boundary Lines
        self._draw_lines(line_col=pr.Color(255, 225, 60, 255), attack_col=pr.Color(255, 235, 110, 240))

        # Ancient Floating Marble Pillars at the corners
        for px in [-self.half_width - 3.4, self.half_width + 3.4]:
            for pz in [-self.half_length - 3.6, self.half_length + 3.6]:
                pillar_bob = math.sin(t * 1.5 + px + pz) * 0.25
                pr.draw_cylinder(pr.Vector3(px, pillar_bob, pz), 0.55, 0.50, 7.5, 12, pr.Color(235, 240, 250, 255))
                # Glowing blue energy ring around pillar
                pr.draw_cylinder(pr.Vector3(px, pillar_bob + 3.5, pz), 0.68, 0.68, 0.18, 12, pr.Color(50, 220, 255, 220))
                # Floating crystal orb above pillar
                pr.draw_sphere(pr.Vector3(px, pillar_bob + 8.2, pz), 0.55, pr.Color(255, 215, 0, 240))

        # Floating Celestial Sky Ring in the background
        pr.draw_circle_3d(pr.Vector3(0, 12.0, 38.0), 9.0, pr.Vector3(1, 0, 0), 20.0, pr.Color(255, 215, 0, 120))
        pr.draw_circle_3d(pr.Vector3(0, 12.0, 38.0), 9.2, pr.Vector3(1, 0, 0), 20.0, pr.Color(50, 220, 255, 140))

    # =========================================================================
    # 4. CRUISE SHIP DECK ARENA (Ocean Liner)
    # =========================================================================
    def _draw_cruise_ship(self):
        t = pr.get_time()
        # Sparkling Open Ocean all around the ship
        pr.draw_cube(pr.Vector3(0, -1.8, 0), 95.0, 0.2, 105.0, pr.Color(18, 75, 145, 255))
        # Rolling ocean waves
        for oi in range(-40, 42, 10):
            wv_z = float(oi) + math.sin(t * 1.6 + oi) * 1.2
            pr.draw_cube(pr.Vector3(0, -1.7, wv_z), 95.0, 0.15, 1.8, pr.Color(35, 115, 185, 200))
            pr.draw_cube(pr.Vector3(0, -1.65, wv_z + 0.8), 95.0, 0.08, 0.45, pr.Color(255, 255, 255, 180))

        # Main Teak Wood Ship Deck
        deck_w = self.width + 10.0
        deck_l = self.length + 12.0
        pr.draw_cube(pr.Vector3(0, -0.4, 0), deck_w, 0.7, deck_l, pr.Color(230, 235, 245, 255))
        # Polished Teak Planking
        pr.draw_cube(pr.Vector3(0, 0.005, 0), deck_w - 0.6, 0.02, deck_l - 0.6, pr.Color(165, 120, 80, 255))
        # Longitudinal plank seams
        for lx in range(int(-deck_w / 2 + 1), int(deck_w / 2), 1):
            pr.draw_cube(pr.Vector3(float(lx), 0.012, 0), 0.04, 0.01, deck_l - 0.8, pr.Color(120, 85, 55, 220))

        # Vivid Blue Court Inset on the Wood Deck
        pr.draw_cube(pr.Vector3(0, 0.016, 0), self.width, 0.02, self.length, pr.Color(25, 95, 205, 240))

        # Crisp White Nautical Boundary Lines
        self._draw_lines(line_col=pr.Color(255, 255, 255, 255), attack_col=pr.Color(255, 255, 255, 230))

        # Cruise Ship Safety Railings (Polished White & Mahogany Top Rail)
        rail_x = self.half_width + 4.8
        for rx_sign in [-rail_x, rail_x]:
            pr.draw_cube(pr.Vector3(rx_sign, 0.95, 0), 0.16, 0.08, deck_l - 1.0, pr.Color(110, 65, 35, 255))
            pr.draw_cube(pr.Vector3(rx_sign, 0.55, 0), 0.08, 0.05, deck_l - 1.0, pr.Color(240, 245, 250, 255))
            for rz in range(int(-deck_l / 2 + 2), int(deck_l / 2), 3):
                pr.draw_cylinder(pr.Vector3(rx_sign, 0, float(rz)), 0.05, 0.05, 0.95, 8, pr.Color(240, 245, 250, 255))

        # Lifebuoys (Red and White circular rings) mounted on railings
        for buo_z in [-8.0, 0.0, 8.0]:
            pr.draw_circle_3d(pr.Vector3(rail_x, 0.55, buo_z), 0.35, pr.Vector3(1, 0, 0), 90.0, pr.Color(240, 45, 45, 255))
            pr.draw_circle_3d(pr.Vector3(rail_x, 0.55, buo_z), 0.20, pr.Vector3(1, 0, 0), 90.0, pr.Color(255, 255, 255, 255))
            pr.draw_circle_3d(pr.Vector3(-rail_x, 0.55, buo_z), 0.35, pr.Vector3(1, 0, 0), 90.0, pr.Color(240, 45, 45, 255))
            pr.draw_circle_3d(pr.Vector3(-rail_x, 0.55, buo_z), 0.20, pr.Vector3(1, 0, 0), 90.0, pr.Color(255, 255, 255, 255))

        # Ship Navigation Bridge in Background (+Z side)
        bridge_z = self.half_length + 8.5
        pr.draw_cube(pr.Vector3(0, 3.2, bridge_z), deck_w + 4.0, 6.4, 6.0, pr.Color(245, 248, 252, 255))
        # Bridge tinted windows
        pr.draw_cube(pr.Vector3(0, 4.5, bridge_z - 3.02), deck_w - 2.0, 1.8, 0.05, pr.Color(35, 55, 85, 230))

        # Cruise Ship Smokestack / Chimney (White with Red/Blue stripe)
        stack_z = bridge_z + 6.0
        pr.draw_cylinder(pr.Vector3(0, 6.0, stack_z), 2.2, 1.8, 7.5, 14, pr.Color(245, 248, 255, 255))
        pr.draw_cylinder(pr.Vector3(0, 11.2, stack_z), 2.0, 1.9, 1.4, 14, pr.Color(225, 40, 50, 255))
        pr.draw_cylinder(pr.Vector3(0, 12.6, stack_z), 1.9, 1.8, 1.0, 14, pr.Color(25, 75, 185, 255))

    # =========================================================================
    # 5. HIGH SCHOOL GYMNASIUM ARENA (Haikyuu Anime Style)
    # =========================================================================
    def _draw_high_school_gym(self):
        # Polished Glossy Hardwood Parquet Floor
        gym_w = self.width + 10.0
        gym_l = self.length + 11.0
        pr.draw_cube(pr.Vector3(0, -0.06, 0), gym_w + 4.0, 0.1, gym_l + 4.0, pr.Color(210, 155, 95, 255))
        pr.draw_cube(pr.Vector3(0, 0.005, 0), gym_w, 0.02, gym_l, pr.Color(235, 180, 115, 255))
        
        # Parquet wood plank stripes
        for px in range(int(-gym_w / 2 + 1), int(gym_w / 2), 2):
            plank_col = pr.Color(225, 170, 105, 255) if (px % 4 == 0) else pr.Color(245, 190, 125, 255)
            pr.draw_cube(pr.Vector3(float(px), 0.012, 0), 1.8, 0.01, gym_l - 0.5, plank_col)

        # Crisp Gymnasium Boundary Lines (Green and White classic Japanese gym tape)
        self._draw_lines(line_col=pr.Color(30, 145, 75, 255), attack_col=pr.Color(235, 55, 65, 240))

        # Gymnasium Walls
        wall_h = 10.5
        wall_col = pr.Color(240, 242, 245, 255)
        # End wall (+Z side with Gym Stage)
        stage_z = self.half_length + 6.0
        pr.draw_cube(pr.Vector3(0, wall_h / 2.0, stage_z + 4.0), gym_w + 6.0, wall_h, 0.8, wall_col)
        # Raised Wooden Stage
        pr.draw_cube(pr.Vector3(0, 0.8, stage_z), gym_w - 4.0, 1.6, 6.0, pr.Color(175, 115, 70, 255))
        # Dark Red Velvet Stage Curtains
        pr.draw_cube(pr.Vector3(-gym_w / 2 + 3.0, 4.2, stage_z - 2.8), 2.2, 5.2, 0.4, pr.Color(165, 30, 40, 255))
        pr.draw_cube(pr.Vector3(gym_w / 2 - 3.0, 4.2, stage_z - 2.8), 2.2, 5.2, 0.4, pr.Color(165, 30, 40, 255))

        # Far wall (-Z side)
        pr.draw_cube(pr.Vector3(0, wall_h / 2.0, -stage_z - 4.0), gym_w + 6.0, wall_h, 0.8, wall_col)

        # Side walls (-X and +X)
        sw_x = self.half_width + 5.5
        pr.draw_cube(pr.Vector3(-sw_x, wall_h / 2.0, 0), 0.8, wall_h, gym_l + 8.0, wall_col)
        pr.draw_cube(pr.Vector3(sw_x, wall_h / 2.0, 0), 0.8, wall_h, gym_l + 8.0, wall_col)

        # High Clerestory Windows with Sunlight Rays on Side Wall (+X)
        for wz in range(-int(gym_l / 2 - 4), int(gym_l / 2), 8):
            pr.draw_cube(pr.Vector3(sw_x - 0.35, 7.2, float(wz)), 0.1, 2.5, 4.2, pr.Color(140, 205, 255, 180))
            # Slanted sunbeam polygon/cube
            pr.draw_cube(pr.Vector3(sw_x - 3.5, 3.8, float(wz)), 6.0, 4.5, 3.8, pr.Color(255, 250, 215, 25))

        # Basketball Hoops & Backboards on both end walls
        for bz in [-self.half_length - 5.2, self.half_length + 5.2]:
            b_sign = 1 if bz > 0 else -1
            # Backboard
            pr.draw_cube(pr.Vector3(0, 3.8, bz), 2.2, 1.4, 0.08, pr.Color(255, 255, 255, 255))
            pr.draw_cube(pr.Vector3(0, 3.8, bz), 0.8, 0.6, 0.10, pr.Color(230, 45, 45, 255))
            # Orange Rim
            pr.draw_circle_3d(pr.Vector3(0, 3.25, bz - b_sign * 0.45), 0.35, pr.Vector3(1, 0, 0), 90.0, pr.Color(245, 90, 20, 255))

        # Electronic High School Scoreboard on Side Wall
        pr.draw_cube(pr.Vector3(-sw_x + 0.45, 6.5, 0), 0.12, 1.8, 3.6, pr.Color(25, 28, 38, 255))
        pr.draw_cube(pr.Vector3(-sw_x + 0.48, 6.5, -0.8), 0.08, 0.9, 1.2, pr.Color(235, 45, 45, 230))
        pr.draw_cube(pr.Vector3(-sw_x + 0.48, 6.5, 0.8), 0.08, 0.9, 1.2, pr.Color(45, 220, 90, 230))

    # =========================================================================
    # COURT LINES & NET RENDERING (Dynamically Sized)
    # =========================================================================
    def _draw_lines(self, line_col, attack_col):
        """Draws crisp boundary, center, and attack lines matching dynamic dimensions."""
        lw = 0.075
        lh = 0.02
        # Sidelines
        pr.draw_cube(pr.Vector3(-self.half_width, lh, 0), lw, lh, self.length, line_col)
        pr.draw_cube(pr.Vector3(self.half_width, lh, 0), lw, lh, self.length, line_col)
        # Baselines
        pr.draw_cube(pr.Vector3(0, lh, -self.half_length), self.width, lh, lw, line_col)
        pr.draw_cube(pr.Vector3(0, lh, self.half_length), self.width, lh, lw, line_col)
        # Center Line under net
        pr.draw_cube(pr.Vector3(0, lh, 0), self.width, lh, lw * 1.5, line_col)
        # Attack Lines
        atk_dist = min(3.2, self.half_length * 0.35)
        pr.draw_cube(pr.Vector3(0, lh, -atk_dist), self.width, lh, lw, attack_col)
        pr.draw_cube(pr.Vector3(0, lh, atk_dist), self.width, lh, lw, attack_col)

    def _draw_net_and_structure(self):
        """Draws posts, net mesh, cables, and striped antennae dynamically scaled to court width."""
        net_w = self.width + 1.2
        post_dist = self.half_width + 0.65
        post_rad = 0.095

        # Steel posts on both sides
        post_col = pr.Color(35, 115, 235, 255) if self.current_arena == CourtArena.BEACH else pr.Color(50, 65, 85, 255)
        pr.draw_cylinder(pr.Vector3(-post_dist, 0, 0), post_rad, post_rad, 2.72, 14, post_col)
        pr.draw_cylinder(pr.Vector3(post_dist, 0, 0), post_rad, post_rad, 2.72, 14, post_col)

        # Top White Tape Band (Y = 2.43)
        pr.draw_cube(pr.Vector3(0, NET_HEIGHT, 0), net_w, 0.10, NET_THICKNESS, pr.Color(252, 254, 255, 255))
        # Bottom White Tape Band (Y = 1.43)
        pr.draw_cube(pr.Vector3(0, NET_BOTTOM_HEIGHT, 0), net_w, 0.06, NET_THICKNESS, pr.Color(252, 254, 255, 255))

        # Net Mesh Grid
        mesh_h = NET_HEIGHT - NET_BOTTOM_HEIGHT
        mesh_center_y = (NET_HEIGHT + NET_BOTTOM_HEIGHT) / 2.0
        pr.draw_cube(pr.Vector3(0, mesh_center_y, 0), net_w, mesh_h, 0.02, pr.Color(30, 35, 45, 180))

        # Horizontal cables
        for step in range(1, 6):
            cy = NET_BOTTOM_HEIGHT + (mesh_h * step / 6.0)
            pr.draw_cube(pr.Vector3(0, cy, 0), net_w, 0.016, 0.025, pr.Color(160, 165, 175, 200))

        # Red & White Striped Antennae at court sidelines (+/- self.half_width)
        for ant_x in [-self.half_width, self.half_width]:
            total_ant_h = (NET_HEIGHT + ANTENNA_HEIGHT) - NET_BOTTOM_HEIGHT
            segments = 10
            seg_h = total_ant_h / segments
            for s in range(segments):
                sy = NET_BOTTOM_HEIGHT + s * seg_h + seg_h / 2.0
                scol = pr.Color(235, 45, 45, 255) if (s % 2 == 0) else pr.Color(255, 255, 255, 255)
                pr.draw_cylinder(pr.Vector3(ant_x, sy - seg_h / 2.0, 0), 0.022, 0.022, seg_h, 8, scol)

    def _draw_palm_tree(self, px, pz):
        trunk_h = 5.2
        pr.draw_cylinder(pr.Vector3(px, 0, pz), 0.22, 0.16, trunk_h, 8, pr.Color(140, 95, 58, 255))
        angles = [0.0, 0.78, 1.57, 2.35, 3.14, 3.92, 4.71, 5.49]
        for a in angles:
            frond_len = 2.4
            fx = px + math.cos(a) * frond_len * 0.5
            fz = pz + math.sin(a) * frond_len * 0.5
            fy = trunk_h + 0.35 - 0.35 * (frond_len * 0.5 / frond_len)
            col = pr.Color(55, 165, 65, 255) if int(a * 10) % 2 == 0 else pr.Color(75, 190, 80, 255)
            pr.draw_cube(pr.Vector3(fx, fy, fz), 0.55, 0.08, frond_len, col)
        pr.draw_sphere(pr.Vector3(px + 0.12, trunk_h - 0.1, pz + 0.1), 0.16, pr.Color(90, 60, 35, 255))
        pr.draw_sphere(pr.Vector3(px - 0.12, trunk_h - 0.1, pz + 0.1), 0.16, pr.Color(90, 60, 35, 255))

    def _draw_building(self, bx, bz, bw, bh, bd, bcol):
        pr.draw_cube(pr.Vector3(bx, bh / 2.0, bz), bw, bh, bd, bcol)
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
        pr.draw_cylinder(pr.Vector3(ux, 0, uz), 0.04, 0.04, 2.3, 8, pr.Color(140, 95, 58, 255))
        pr.draw_cylinder(pr.Vector3(ux, 2.1, uz), 1.6, 0.1, 0.45, 12, canopy_col)
        pr.draw_cylinder(pr.Vector3(ux, 2.2, uz), 1.1, 0.05, 0.40, 12, pr.Color(250, 250, 250, 255))
        pr.draw_cube(pr.Vector3(ux + 0.8, 0.12, uz), 0.7, 0.18, 1.6, pr.Color(240, 240, 245, 255))
        pr.draw_cube(pr.Vector3(ux + 0.8, 0.32, uz - 0.5), 0.7, 0.25, 0.5, canopy_col)
