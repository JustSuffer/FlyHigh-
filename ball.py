"""
FlyHigh! - 3D Volleyball Game
Volleyball Physics & Trajectory Prediction System
Includes realistic arc calculation, net bounce, ground shadow,
and predicted landing ring (crucial for 'Just Volleyball' depth perception).
"""
import pyray as pr
import math
from constants import (
    BALL_RADIUS, GRAVITY, BALL_AIR_DRAG, BALL_BOUNCE_RESTITUTION,
    NET_RESTITUTION, NET_HEIGHT, NET_BOTTOM_HEIGHT, HALF_WIDTH, HALF_LENGTH
)

# Colors
COLOR_BALL_WHITE  = pr.Color(250, 250, 250, 255)
COLOR_BALL_BLUE   = pr.Color(35, 95, 210, 255)
COLOR_BALL_YELLOW = pr.Color(245, 200, 35, 255)
COLOR_SHADOW      = pr.Color(20, 20, 30, 140)
COLOR_PREDICT_RING = pr.Color(255, 220, 50, 200)
COLOR_PREDICT_FILL = pr.Color(255, 180, 0, 90)

class Ball:
    def __init__(self, x=0.0, y=1.5, z=-7.0):
        self.x = x
        self.y = y
        self.z = z
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        
        self.rot_x = 0.0
        self.rot_y = 0.0
        self.rot_z = 0.0
        
        self.last_touch_team = None
        self.last_touch_player = None
        self.touch_count = 0
        self.has_bounced = False
        self.bounce_count = 0
        self.in_air = True
        self.net_touched = False
        
        # Predicted landing cache
        self.predict_x = x
        self.predict_z = z
        self.time_to_impact = 0.0

        # Special shot types & trails
        self.is_float = False
        self.is_spike = False
        self.is_green_timing = False
        self.green_vfx_type = "FIRE"
        self.flight_time = 0.0
        self.trail = []  # List of (x, y, z, is_spike, is_float, is_green, vfx_type)
        self.hit_cooldown = 0.0

    def reset(self, x=0.0, y=2.0, z=-7.5, team=None):
        self.x = x
        self.y = y
        self.z = z
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.last_touch_team = team
        self.last_touch_player = None
        self.touch_count = 0
        self.has_bounced = False
        self.bounce_count = 0
        self.in_air = True
        self.net_touched = False
        self.is_float = False
        self.is_spike = False
        self.is_green_timing = False
        self.green_vfx_type = "FIRE"
        self.flight_time = 0.0
        self.trail.clear()
        self.hit_cooldown = 0.0
        self.update_prediction()

    def can_be_hit_by(self, char):
        """Enforces authentic volleyball contact rules:
        - Prevents multiple hits in rapid succession (minimum cooldown)
        - Prevents illegal double-contact (same player touching twice consecutively)
        """
        if self.hit_cooldown > 0.0:
            return False
        if char is not None and char == self.last_touch_player and not self.has_bounced:
            return False
        return True

    def update(self, dt, audio_mgr=None):
        """Advances physics, updates trajectory, checks floor and net collisions."""
        if self.hit_cooldown > 0.0:
            self.hit_cooldown = max(0.0, self.hit_cooldown - dt)
        if not self.in_air:
            return

        self.flight_time += dt

        # 1. Apply gravity, air drag, and special Float Serve Knuckleball physics
        self.vy += GRAVITY * dt
        self.vx *= (BALL_AIR_DRAG ** (dt * 60.0))
        self.vz *= (BALL_AIR_DRAG ** (dt * 60.0))

        # Float Knuckleball Effect: erratic horizontal drift and sharp dip near the net!
        if self.is_float:
            # Knuckleball air-wobble
            wobble_x = math.sin(self.flight_time * 16.0) * 1.6
            self.x += wobble_x * dt
            # Sudden aerodynamic dive when crossing net plane
            if abs(self.z) < 2.2 and self.y > NET_HEIGHT - 0.2:
                self.vy -= 10.0 * dt

        # Record trail points for high-energy visual feedback
        max_trail = 24 if self.is_green_timing else 16
        if len(self.trail) > max_trail:
            self.trail.pop(0)
        self.trail.append((self.x, self.y, self.z, self.is_spike, self.is_float, self.is_green_timing, self.green_vfx_type))

        # 2. Check Net Collision (Z = 0 plane)
        prev_z = self.z
        next_z = self.z + self.vz * dt
        
        # Did ball cross the net plane this frame?
        if (prev_z < 0.0 and next_z >= -BALL_RADIUS) or (prev_z > 0.0 and next_z <= BALL_RADIUS):
            if abs(self.x) <= HALF_WIDTH + 0.3:
                # Check height against net
                if NET_BOTTOM_HEIGHT - 0.1 <= self.y <= NET_HEIGHT:
                    # Net hit!
                    self.vz = -self.vz * NET_RESTITUTION
                    self.vx *= 0.5
                    self.vy *= 0.7
                    self.net_touched = True
                    self.is_float = False
                    if audio_mgr:
                        audio_mgr.play("hit_bump")

        # 3. Apply displacement
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt

        # Visual spin (float serves do NOT spin: true knuckleball!)
        if not self.is_float:
            speed = math.sqrt(self.vx * self.vx + self.vz * self.vz + self.vy * self.vy)
            self.rot_x += speed * 5.0 * dt
            self.rot_y += self.vx * 4.0 * dt

        # 4. Floor Collision (Y = BALL_RADIUS)
        if self.y <= BALL_RADIUS:
            self.y = BALL_RADIUS
            self.is_float = False
            self.is_spike = False
            if not self.has_bounced:
                self.has_bounced = True
                self.bounce_count = 1
                if audio_mgr:
                    audio_mgr.play("floor_bounce")
            else:
                self.bounce_count += 1

            if abs(self.vy) > 2.0:
                self.vy = -self.vy * BALL_BOUNCE_RESTITUTION
                self.vx *= 0.8
                self.vz *= 0.8
            else:
                self.vy = 0.0
                self.vx *= 0.85
                self.vz *= 0.85
                if abs(self.vx) < 0.1 and abs(self.vz) < 0.1:
                    self.in_air = False

        # 5. Update predicted landing point for visual indicators
        self.update_prediction()

    def update_prediction(self):
        """Solves quadratic trajectory equation for ground impact point (y = BALL_RADIUS)."""
        a = 0.5 * GRAVITY
        b = self.vy
        c = self.y - BALL_RADIUS

        disc = b * b - 4 * a * c
        if disc > 0 and a != 0:
            t1 = (-b - math.sqrt(disc)) / (2 * a)
            t2 = (-b + math.sqrt(disc)) / (2 * a)
            t = t1 if t1 > 0 else t2
            if t > 0:
                self.time_to_impact = t
                self.predict_x = self.x + self.vx * t
                self.predict_z = self.z + self.vz * t
                return
                
        self.time_to_impact = 0.0
        self.predict_x = self.x
        self.predict_z = self.z

    def launch_arc(self, target_x, target_z, peak_height=4.8, is_spike=False, is_float=False, is_green_timing=False, green_vfx_type="FIRE", spike_speed=24.0, hitter=None):
        """
        Calculates exact initial velocity vector (vx, vy, vz)
        to arc from current position to (target_x, target_z).
        Spikes are fast and sharp; passes/sets/bumps are gentle, floaty and readable.
        """
        self.has_bounced = False
        self.in_air = True
        self.net_touched = False
        self.is_spike = is_spike
        self.is_float = is_float
        self.is_green_timing = is_green_timing
        self.green_vfx_type = green_vfx_type
        self.flight_time = 0.0
        self.trail.clear()
        self.hit_cooldown = 0.32  # Prevents multi-frame repeated contact!
        if hitter is not None:
            self.last_touch_player = hitter

        dx = target_x - self.x
        dz = target_z - self.z
        horiz_dist = math.sqrt(dx * dx + dz * dz)

        if is_spike:
            # Downward explosive line-drive hammer shot
            dy = BALL_RADIUS - self.y
            flight_time = max(0.28, horiz_dist / spike_speed)
            self.vx = dx / flight_time
            self.vz = dz / flight_time
            self.vy = (dy - 0.5 * GRAVITY * (flight_time ** 2)) / flight_time
        elif is_float:
            # Knuckleball Float Serve: fast, flat, skimming over net height
            h = max(NET_HEIGHT + 0.35, max(self.y + 0.2, peak_height * 0.88))
            vy0 = math.sqrt(2 * abs(GRAVITY) * (h - self.y))
            time_up = vy0 / abs(GRAVITY)
            time_down = math.sqrt(2 * abs(GRAVITY) * (h - BALL_RADIUS)) / abs(GRAVITY)
            total_time = max(0.55, (time_up + time_down) * 0.85)

            self.vx = dx / total_time
            self.vz = dz / total_time
            self.vy = vy0
        else:
            # Gentle, lofty parabolic arc (authentic volleyball pass / set / dig)
            h = max(self.y + 0.6, peak_height)
            vy0 = math.sqrt(2 * abs(GRAVITY) * (h - self.y))
            time_up = vy0 / abs(GRAVITY)
            time_down = math.sqrt(2 * abs(GRAVITY) * (h - BALL_RADIUS)) / abs(GRAVITY)
            total_time = max(0.70, time_up + time_down)

            self.vx = dx / total_time
            self.vz = dz / total_time
            self.vy = vy0

        self.update_prediction()

    def draw(self):
        """Renders the 3D volleyball, dynamic trails, ground shadow, and landing target ring."""
        # 0. High-Energy Particle Trails & Green Timing Anime VFX
        if self.in_air and len(self.trail) > 1:
            for idx, pt in enumerate(self.trail):
                tx, ty, tz, was_spike, was_float, was_green, vfx_type = pt
                prog = idx / len(self.trail)
                rad = BALL_RADIUS * (0.75 if was_green else 0.45) * prog
                
                if was_green:
                    if vfx_type == "FIRE":
                        col_outer = pr.Color(255, int(50 + 170 * prog), 15, int(210 * prog))
                        pr.draw_sphere(pr.Vector3(tx, ty, tz), rad, col_outer)
                        col_inner = pr.Color(255, 235, 60, int(240 * prog))
                        pr.draw_sphere(pr.Vector3(tx, ty, tz), rad * 0.55, col_inner)
                    elif vfx_type == "LIGHTNING":
                        col_outer = pr.Color(30, 210, 255, int(220 * prog))
                        pr.draw_sphere(pr.Vector3(tx, ty, tz), rad, col_outer)
                        col_inner = pr.Color(240, 255, 255, int(250 * prog))
                        pr.draw_sphere(pr.Vector3(tx, ty, tz), rad * 0.5, col_inner)
                    else:  # WATER
                        col_outer = pr.Color(25, 140, 255, int(200 * prog))
                        pr.draw_sphere(pr.Vector3(tx, ty, tz), rad, col_outer)
                        col_inner = pr.Color(160, 235, 255, int(230 * prog))
                        pr.draw_sphere(pr.Vector3(tx, ty, tz), rad * 0.65, col_inner)
                elif was_spike:
                    col = pr.Color(255, int(80 + 140 * prog), 30, int(180 * prog))
                    pr.draw_sphere(pr.Vector3(tx, ty, tz), rad, col)
                elif was_float:
                    col = pr.Color(40, 220, 255, int(170 * prog))
                    pr.draw_sphere(pr.Vector3(tx, ty, tz), rad, col)

        # 1. Ground Shadow (Directly beneath ball)
        shadow_scale = max(0.15, 1.0 - (self.y / 8.0) * 0.6)
        shadow_rad = BALL_RADIUS * 1.4 * shadow_scale
        shadow_alpha = int(max(40, 160 - self.y * 18))
        pr.draw_circle_3d(
            pr.Vector3(self.x, 0.02, self.z),
            shadow_rad,
            pr.Vector3(1, 0, 0), 90.0,
            pr.Color(15, 15, 25, shadow_alpha)
        )

        # 2. Predicted Landing Indicator Ring ("Just Volleyball" Style)
        if self.in_air and self.y > 0.4 and self.time_to_impact > 0.1:
            px = self.predict_x
            pz = self.predict_z
            ring_rad = 0.65
            
            # Outer boundary circle of landing spot
            pr.draw_circle_3d(
                pr.Vector3(px, 0.025, pz),
                ring_rad,
                pr.Vector3(1, 0, 0), 90.0,
                COLOR_PREDICT_RING
            )
            # Inner circle shrinks with time to impact
            shrink_ratio = max(0.05, min(1.0, self.time_to_impact / 1.5))
            pr.draw_circle_3d(
                pr.Vector3(px, 0.027, pz),
                ring_rad * shrink_ratio,
                pr.Vector3(1, 0, 0), 90.0,
                COLOR_PREDICT_FILL
            )
            # Center target bullseye dot
            pr.draw_circle_3d(
                pr.Vector3(px, 0.03, pz),
                0.12,
                pr.Vector3(1, 0, 0), 90.0,
                pr.Color(255, 60, 60, 230)
            )

        # 3. 3D Volleyball Sphere
        pos = pr.Vector3(self.x, self.y, self.z)
        pr.draw_sphere(pos, BALL_RADIUS, COLOR_BALL_WHITE)
        
        # Low-poly stylized swirl panels (Blue & Yellow bands)
        band_offset_y = BALL_RADIUS * 0.35 * math.cos(self.rot_x)
        band_offset_x = BALL_RADIUS * 0.35 * math.sin(self.rot_y)
        pr.draw_sphere(
            pr.Vector3(self.x + band_offset_x, self.y + band_offset_y, self.z),
            BALL_RADIUS * 0.55,
            COLOR_BALL_BLUE
        )
        pr.draw_sphere(
            pr.Vector3(self.x - band_offset_x, self.y - band_offset_y, self.z),
            BALL_RADIUS * 0.5,
            COLOR_BALL_YELLOW
        )

        # Knuckleball Float shimmer halo
        if self.is_float and self.in_air:
            pr.draw_sphere(pos, BALL_RADIUS * 1.25, pr.Color(60, 220, 255, 80))

        # Green Timing Blazing Energy Aura around Ball
        if self.is_green_timing and self.in_air:
            pulse = 1.0 + 0.18 * math.sin(pr.get_time() * 24.0)
            if self.green_vfx_type == "FIRE":
                pr.draw_sphere(pos, BALL_RADIUS * 1.48 * pulse, pr.Color(255, 110, 20, 150))
                pr.draw_sphere(pos, BALL_RADIUS * 1.85 * pulse, pr.Color(255, 50, 10, 85))
            elif self.green_vfx_type == "LIGHTNING":
                pr.draw_sphere(pos, BALL_RADIUS * 1.45 * pulse, pr.Color(50, 230, 255, 160))
                pr.draw_sphere(pos, BALL_RADIUS * 1.80 * pulse, pr.Color(20, 140, 255, 90))
            else:  # WATER
                pr.draw_sphere(pos, BALL_RADIUS * 1.45 * pulse, pr.Color(40, 180, 255, 150))
                pr.draw_sphere(pos, BALL_RADIUS * 1.85 * pulse, pr.Color(180, 240, 255, 95))

