"""
FlyHigh! - 3D Volleyball Game
Modern Arcade Anime Character (Inspired by 'Just Volleyball' & Anime Sports)
Features:
- Spiky geometric anime hair (silver/white for captain, customizable)
- Expressive anime chibi face (almond eyes with pupils & highlights, eyebrows, nose, mouth)
- Floating spherical hands (Rayman / Chibi arcade style with dynamic volleyball poses)
- Athletic sleeveless jersey tank top with bold player numbers
- Cyan volleyball shorts, black kneepads, cobalt sneakers with purple socks
- Smooth procedural animations (Run, Jump, Bump, Set, Spike, Dive, Celebrate)
"""
import pyray as pr
import math
from constants import (
    PLAYER_RADIUS, PLAYER_HEIGHT, PLAYER_SPEED, PLAYER_SPRINT_SPEED,
    PLAYER_JUMP_FORCE, PLAYER_SUPER_JUMP_FORCE, PLAYER_REACH_RADIUS, PLAYER_SPIKE_REACH,
    Team, PlayerAction, GRAVITY
)

# Colors
COLOR_SKIN = pr.Color(252, 218, 185, 255)       # Anime Peach Skin
COLOR_SKIN_SHADOW = pr.Color(230, 190, 160, 255)
COLOR_KNEEPAD = pr.Color(20, 22, 28, 255)        # Solid Black Kneepads
COLOR_OUTLINE = pr.Color(18, 18, 24, 255)        # Toon Outline Dark

class Character:
    def __init__(self, x=0.0, z=-5.0, team=Team.PLAYER, jersey_num=5, name="CAPTAIN", hair_color=None, is_ai=False):
        self.x = x
        self.y = 0.0
        self.z = z
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        
        self.team = team
        self.jersey_num = jersey_num
        self.name = name
        self.is_ai = is_ai
        
        # Customization attributes
        self.color_skin = COLOR_SKIN
        self.color_skin_shadow = COLOR_SKIN_SHADOW
        self.hair_style = 0
        self.headband_color = pr.Color(250, 252, 255, 255) if team == Team.PLAYER else None
        self.back_logo = 0 if team == Team.PLAYER else 4
        self.color_shorts_trim = pr.Color(250, 252, 255, 255) if team == Team.PLAYER else pr.Color(235, 45, 65, 255)
        self.color_wristband = pr.Color(25, 28, 35, 255) if team == Team.PLAYER else pr.Color(20, 20, 25, 255)
        
        # Color Palettes (Photo-inspired: White jersey, Cyan/Black shorts, Blue/Purple shoes)
        if team == Team.PLAYER:
            self.color_jersey = pr.Color(248, 250, 252, 255)    # White Tank Top
            self.color_trim   = pr.Color(25, 28, 35, 255)        # Black Trim
            self.color_shorts = pr.Color(26, 28, 36, 255)        # Midnight Black Shorts
            self.color_shoes  = pr.Color(25, 75, 225, 255)       # Royal Blue Sneakers
            self.color_socks  = pr.Color(115, 55, 235, 255)      # Purple Ankle Cuffs
            self.color_number = pr.Color(18, 20, 25, 255)       # Bold Black Digit
            # Default hair: Chestnut Brown (matching reference photo) or Silver
            if hair_color is not None:
                self.color_hair = hair_color
            elif jersey_num == 5 or jersey_num == 7:
                self.color_hair = pr.Color(95, 60, 42, 255)      # Chestnut Brown Spikes
            elif jersey_num == 2:
                self.color_hair = pr.Color(238, 240, 245, 255)   # Silver/White Anime Spikes
            else:
                self.color_hair = pr.Color(235, 190, 90, 255)    # Sandy Blonde Spikes
        else:
            # Opponent Team: Dark Crimson & Midnight aesthetic
            self.color_jersey = pr.Color(30, 32, 40, 255)        # Dark Charcoal Jersey
            self.color_trim   = pr.Color(235, 45, 65, 255)       # Red Trim
            self.color_shorts = pr.Color(225, 40, 60, 255)       # Crimson Red Shorts
            self.color_shoes  = pr.Color(20, 20, 25, 255)        # Dark Shoes
            self.color_socks  = pr.Color(235, 45, 65, 255)       # Crimson Socks
            self.color_number = pr.Color(255, 255, 255, 255)     # Crisp White Digit
            if hair_color is not None:
                self.color_hair = hair_color
            elif jersey_num == 1:
                self.color_hair = pr.Color(35, 35, 42, 255)      # Jet Black Spikes
            elif jersey_num == 3:
                self.color_hair = pr.Color(210, 215, 225, 255)   # Silver Spikes
            else:
                self.color_hair = pr.Color(180, 50, 45, 255)     # Crimson Spikes

        # Facing angle (0 = facing +Z toward net, pi = facing -Z toward player net)
        self.facing_angle = 0.0 if team == Team.PLAYER else math.pi
        
        # Action & Animation
        self.action = PlayerAction.IDLE
        self.action_timer = 0.0
        self.action_duration = 0.35
        self.is_grounded = True
        self.is_super_jump = False
        self.jump_charge = 0.0
        self.anim_time = 0.0
        self.roll_dig_cooldown = 0.0
        
        # Trail & Particle effects on spikes
        self.spike_spark_timer = 0.0

    def apply_profile(self, profile):
        """Applies player cosmetic choices from PlayerProfile."""
        self.name = profile.name
        self.jersey_num = profile.jersey_number
        skin_c, skin_s = profile.get_skin()
        self.color_skin = skin_c
        self.color_skin_shadow = skin_s
        self.color_hair = profile.get_hair_color()
        self.hair_style = profile.hair_style_idx
        self.headband_color = profile.get_headband_color()
        self.color_jersey = profile.get_jersey_color()
        self.color_trim = profile.get_jersey_trim()
        self.back_logo = profile.back_logo_idx
        self.color_shorts = profile.get_shorts_color()
        self.color_shorts_trim = profile.get_shorts_trim()
        self.color_wristband = profile.get_wristband_color()

    def reset_position(self, x, z):
        self.x = x
        self.y = 0.0
        self.z = z
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.is_grounded = True
        self.is_super_jump = False
        self.jump_charge = 0.0
        self.action = PlayerAction.IDLE
        self.action_timer = 0.0
        self.action_duration = 0.35
        self.facing_angle = 0.0 if self.team == Team.PLAYER else math.pi

    def jump(self, is_super=False):
        if self.is_grounded and self.action != PlayerAction.ROLL_DIG:
            self.vy = PLAYER_SUPER_JUMP_FORCE if is_super else PLAYER_JUMP_FORCE
            self.is_super_jump = is_super
            self.is_grounded = False
            self.action = PlayerAction.JUMP
            self.action_timer = 0.0
            self.action_duration = 0.45 if is_super else 0.35

    def trigger_action(self, action, duration=0.35):
        self.action = action
        self.action_duration = duration
        self.action_timer = duration
        if action == PlayerAction.SPIKE:
            self.spike_spark_timer = 0.35
        elif action == PlayerAction.ROLL_DIG:
            self.roll_dig_cooldown = 5.0

    def update(self, dt, move_dir_x=0.0, move_dir_z=0.0, look_target=None):
        self.anim_time += dt

        if self.roll_dig_cooldown > 0.0:
            self.roll_dig_cooldown = max(0.0, self.roll_dig_cooldown - dt)

        if self.action_timer > 0.0:
            self.action_timer -= dt
            if self.action_timer <= 0.0 and self.is_grounded:
                if self.action != PlayerAction.SERVE_HOLD:
                    self.action = PlayerAction.IDLE

        if self.spike_spark_timer > 0.0:
            self.spike_spark_timer -= dt

        # Movement physics
        move_mag = math.sqrt(move_dir_x * move_dir_x + move_dir_z * move_dir_z)
        if not self.is_grounded:
            if self.is_super_jump:
                # Reduced mid-air steering / heavy momentum carries you
                if move_mag > 0.1:
                    self.vx += (move_dir_x / move_mag) * PLAYER_SPEED * dt * 2.2
                    self.vz += (move_dir_z / move_mag) * PLAYER_SPEED * dt * 2.2
                self.vx *= 0.985
                self.vz *= 0.985
            else:
                if move_mag > 0.1:
                    speed = PLAYER_SPEED
                    self.vx = (move_dir_x / move_mag) * speed * 0.88
                    self.vz = (move_dir_z / move_mag) * speed * 0.88
                else:
                    self.vx *= 0.88
                    self.vz *= 0.88
        else:
            if move_mag > 0.1:
                speed = PLAYER_SPEED
                self.vx = (move_dir_x / move_mag) * speed
                self.vz = (move_dir_z / move_mag) * speed
                if self.action in [PlayerAction.IDLE, PlayerAction.RUN]:
                    self.action = PlayerAction.RUN
            else:
                self.vx *= 0.65
                self.vz *= 0.65
                if self.action == PlayerAction.RUN:
                    self.action = PlayerAction.IDLE

        # Jumping physics
        if not self.is_grounded:
            self.vy += GRAVITY * dt
            self.y += self.vy * dt
            if self.y <= 0.0:
                self.y = 0.0
                self.vy = 0.0
                self.is_grounded = True
                self.is_super_jump = False
                if self.action == PlayerAction.JUMP:
                    self.action = PlayerAction.IDLE

        self.x += self.vx * dt
        self.z += self.vz * dt

        # Orientation / Facing
        if look_target is not None:
            dx = look_target[0] - self.x
            dz = look_target[1] - self.z
            if (dx * dx + dz * dz) > 0.05:
                self.facing_angle = math.atan2(dx, dz)
        elif move_mag > 0.1:
            self.facing_angle = math.atan2(move_dir_x, move_dir_z)
        else:
            self.facing_angle = 0.0 if self.team == Team.PLAYER else math.pi

    def dist_to_ball(self, ball):
        dx = ball.x - self.x
        dy = ball.y - (self.y + PLAYER_HEIGHT * 0.7)
        dz = ball.z - self.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def draw(self):
        """Renders the stylized arcade anime player character matching the reference image."""
        px, py, pz = self.x, self.y, self.z
        angle = self.facing_angle

        # Orientation vectors
        forward_x = math.sin(angle)
        forward_z = math.cos(angle)
        right_x = math.cos(angle)
        right_z = -math.sin(angle)

        # 1. Ground Shadow (Smooth dark circle under player)
        shadow_rad = PLAYER_RADIUS * (1.1 - min(0.4, (py / 3.0) * 0.4))
        shadow_alpha = int(max(40, 140 - py * 30))
        pr.draw_circle_3d(
            pr.Vector3(px, 0.02, pz),
            shadow_rad,
            pr.Vector3(1, 0, 0), 90.0,
            pr.Color(15, 18, 25, shadow_alpha)
        )

        # Super Jump High Leap Aura Ring
        if self.is_super_jump and not self.is_grounded:
            glow_pulse = 0.55 + 0.1 * math.sin(self.anim_time * 20.0)
            pr.draw_circle_3d(pr.Vector3(px, 0.05, pz), glow_pulse, pr.Vector3(1, 0, 0), 90.0, pr.Color(255, 220, 60, 160))
            pr.draw_circle_3d(pr.Vector3(px, py * 0.5, pz), 0.35, pr.Vector3(1, 0, 0), 90.0, pr.Color(80, 220, 255, 120))

        # Procedural animation cycles
        run_cycle = math.sin(self.anim_time * 15.0) if self.action == PlayerAction.RUN else 0.0
        idle_bob  = math.sin(self.anim_time * 4.0) * 0.02 if self.action == PlayerAction.IDLE else 0.0
        leg_swing = run_cycle * 0.22

        base_y = py + idle_bob

        # 2. SNEAKERS & SOCKS (Blue base, purple collar, white sole)
        # Left Foot
        lf_pos = pr.Vector3(
            px - right_x * 0.16 + forward_x * leg_swing,
            base_y + 0.1,
            pz - right_z * 0.16 + forward_z * leg_swing
        )
        # Right Foot
        rf_pos = pr.Vector3(
            px + right_x * 0.16 - forward_x * leg_swing,
            base_y + 0.1,
            pz + right_z * 0.16 - forward_z * leg_swing
        )

        # Shoe body (Rounded capsule / spheres)
        pr.draw_sphere(lf_pos, 0.13, self.color_shoes)
        pr.draw_sphere(rf_pos, 0.13, self.color_shoes)
        # Front toe cap
        pr.draw_sphere(pr.Vector3(lf_pos.x + forward_x * 0.08, base_y + 0.08, lf_pos.z + forward_z * 0.08), 0.11, self.color_shoes)
        pr.draw_sphere(pr.Vector3(rf_pos.x + forward_x * 0.08, base_y + 0.08, rf_pos.z + forward_z * 0.08), 0.11, self.color_shoes)
        # Purple socks cuff
        pr.draw_cylinder(pr.Vector3(lf_pos.x, base_y + 0.14, lf_pos.z), 0.08, 0.08, 0.12, 8, self.color_socks)
        pr.draw_cylinder(pr.Vector3(rf_pos.x, base_y + 0.14, rf_pos.z), 0.08, 0.08, 0.12, 8, self.color_socks)

        # 3. LEGS & KNEEPADS
        knee_y = base_y + 0.42
        # Calves (Skin tone)
        pr.draw_cylinder(pr.Vector3(lf_pos.x, base_y + 0.22, lf_pos.z), 0.07, 0.08, 0.22, 8, self.color_skin)
        pr.draw_cylinder(pr.Vector3(rf_pos.x, base_y + 0.22, rf_pos.z), 0.07, 0.08, 0.22, 8, self.color_skin)

        # Black Kneepads (Chunky athletic wraps)
        pr.draw_cylinder(pr.Vector3(lf_pos.x, knee_y, lf_pos.z), 0.11, 0.11, 0.16, 10, COLOR_KNEEPAD)
        pr.draw_cylinder(pr.Vector3(rf_pos.x, knee_y, rf_pos.z), 0.11, 0.11, 0.16, 10, COLOR_KNEEPAD)

        # Thighs (Skin tone up to shorts)
        pr.draw_cylinder(pr.Vector3(lf_pos.x, knee_y + 0.14, lf_pos.z), 0.08, 0.10, 0.20, 8, self.color_skin)
        pr.draw_cylinder(pr.Vector3(rf_pos.x, knee_y + 0.14, rf_pos.z), 0.08, 0.10, 0.20, 8, self.color_skin)

        # 4. VOLLEYBALL SHORTS (Athletic shorts with trim accents)
        shorts_y = base_y + 0.72
        pr.draw_cylinder(pr.Vector3(px, shorts_y, pz), 0.22, 0.25, 0.28, 12, self.color_shorts)
        # Shorts leg cuffs
        pr.draw_cylinder(pr.Vector3(px - right_x * 0.13, shorts_y - 0.06, pz - right_z * 0.13), 0.12, 0.12, 0.14, 10, self.color_shorts)
        pr.draw_cylinder(pr.Vector3(px + right_x * 0.13, shorts_y - 0.06, pz + right_z * 0.13), 0.12, 0.12, 0.14, 10, self.color_shorts)
        # Bottom trim border & curved side stripes
        if self.color_shorts_trim:
            pr.draw_cylinder(pr.Vector3(px - right_x * 0.13, shorts_y - 0.12, pz - right_z * 0.13), 0.124, 0.124, 0.025, 10, self.color_shorts_trim)
            pr.draw_cylinder(pr.Vector3(px + right_x * 0.13, shorts_y - 0.12, pz + right_z * 0.13), 0.124, 0.124, 0.025, 10, self.color_shorts_trim)
            # Athletic side piping stripes along outer thigh (matching reference photo)
            pr.draw_cylinder(pr.Vector3(px - right_x * 0.22, shorts_y - 0.04, pz - right_z * 0.22), 0.024, 0.024, 0.20, 6, self.color_shorts_trim)
            pr.draw_cylinder(pr.Vector3(px + right_x * 0.22, shorts_y - 0.04, pz + right_z * 0.22), 0.024, 0.024, 0.20, 6, self.color_shorts_trim)

        # 5. ATHLETIC SLEEVELESS TANK TOP (Contoured athletic singlet matching reference photo)
        torso_y = base_y + 1.12
        # Slimmer athletic waist
        pr.draw_cylinder(pr.Vector3(px, base_y + 0.86, pz), 0.20, 0.23, 0.26, 12, self.color_jersey)
        # Upper chest & shoulders
        pr.draw_cylinder(pr.Vector3(px, base_y + 1.05, pz), 0.23, 0.25, 0.30, 12, self.color_jersey)
        
        # Border trim along armholes and collar
        pr.draw_cylinder(pr.Vector3(px, base_y + 1.32, pz), 0.14, 0.14, 0.04, 10, self.color_trim)

        # JERSEY NUMBER (Rendered on chest)
        num_pos = pr.Vector3(px + forward_x * 0.24, torso_y + 0.05, pz + forward_z * 0.24)
        self._draw_digit(num_pos, forward_x, forward_z, right_x, right_z, self.jersey_num, self.color_number)

        # BACK EMBLEM (Signature FlyHigh Crown or custom emblem on upper back)
        if self.back_logo < 4:
            back_pos = pr.Vector3(px - forward_x * 0.24, torso_y + 0.08, pz - forward_z * 0.24)
            self._draw_back_emblem(back_pos, forward_x, forward_z, right_x, right_z, self.back_logo, self.color_trim)

        # 6. SLENDER ATHLETIC NECK
        neck_y = base_y + 1.36
        pr.draw_cylinder(pr.Vector3(px, neck_y, pz), 0.08, 0.08, 0.14, 8, self.color_skin)

        # 7. ANIME HEAD & NAPE HAIR VOLUME
        head_y = base_y + 1.62
        head_pos = pr.Vector3(px, head_y, pz)
        pr.draw_sphere(head_pos, 0.26, self.color_skin)

        # Subtle athletic ears tucked behind side hair
        pr.draw_sphere(pr.Vector3(px - right_x * 0.24, head_y - 0.01, pz - right_z * 0.24), 0.045, self.color_skin)
        pr.draw_sphere(pr.Vector3(px + right_x * 0.24, head_y - 0.01, pz + right_z * 0.24), 0.045, self.color_skin)

        # 8. EXPRESSIVE ANIME FACE (Eyes, eyebrows, nose, mouth)
        face_fwd = 0.24
        le_pos = pr.Vector3(px + forward_x * face_fwd - right_x * 0.08, head_y + 0.03, pz + forward_z * face_fwd - right_z * 0.08)
        re_pos = pr.Vector3(px + forward_x * face_fwd + right_x * 0.08, head_y + 0.03, pz + forward_z * face_fwd + right_z * 0.08)
        
        # Sclera (White base)
        pr.draw_sphere(le_pos, 0.05, pr.Color(255, 255, 255, 255))
        pr.draw_sphere(re_pos, 0.05, pr.Color(255, 255, 255, 255))
        # Black Iris / Pupil
        pr.draw_sphere(pr.Vector3(le_pos.x + forward_x * 0.02, le_pos.y, le_pos.z + forward_z * 0.02), 0.035, pr.Color(20, 20, 25, 255))
        pr.draw_sphere(pr.Vector3(re_pos.x + forward_x * 0.02, re_pos.y, re_pos.z + forward_z * 0.02), 0.035, pr.Color(20, 20, 25, 255))
        # Sparkle highlight
        pr.draw_sphere(pr.Vector3(le_pos.x + forward_x * 0.035 - right_x * 0.015, le_pos.y + 0.015, le_pos.z + forward_z * 0.035 - right_z * 0.015), 0.012, pr.Color(255, 255, 255, 255))
        pr.draw_sphere(pr.Vector3(re_pos.x + forward_x * 0.035 - right_x * 0.015, re_pos.y + 0.015, re_pos.z + forward_z * 0.035 - right_z * 0.015), 0.012, pr.Color(255, 255, 255, 255))

        # Eyebrows
        pr.draw_cube(pr.Vector3(le_pos.x, head_y + 0.10, le_pos.z), 0.08, 0.02, 0.02, COLOR_OUTLINE)
        pr.draw_cube(pr.Vector3(re_pos.x, head_y + 0.10, re_pos.z), 0.08, 0.02, 0.02, COLOR_OUTLINE)

        # Small nose dot & mouth
        pr.draw_sphere(pr.Vector3(px + forward_x * (face_fwd + 0.01), head_y - 0.03, pz + forward_z * (face_fwd + 0.01)), 0.018, self.color_skin_shadow)
        pr.draw_cube(pr.Vector3(px + forward_x * (face_fwd + 0.01), head_y - 0.09, pz + forward_z * (face_fwd + 0.01)), 0.07, 0.018, 0.02, pr.Color(50, 30, 25, 255))

        # 9. RICH BACK & NAPE HAIR VOLUME (Seamlessly covers back of head down to neck)
        # Upper & back skull dome
        pr.draw_sphere(pr.Vector3(px - forward_x * 0.04, head_y + 0.06, pz - forward_z * 0.04), 0.272, self.color_hair)
        # Nape volume covering lower occipital bone down to neck collar
        pr.draw_cylinder(pr.Vector3(px - forward_x * 0.08, head_y - 0.04, pz - forward_z * 0.08), 0.22, 0.16, 0.18, 12, self.color_hair)
        pr.draw_sphere(pr.Vector3(px - forward_x * 0.12, head_y - 0.09, pz - forward_z * 0.12), 0.16, self.color_hair)
        # Tapered nape hair spikes at the back (visible from behind matching reference photo)
        pr.draw_cylinder(pr.Vector3(px - forward_x * 0.16, head_y - 0.12, pz - forward_z * 0.16), 0.08, 0.02, 0.16, 6, self.color_hair)
        pr.draw_cylinder(pr.Vector3(px - forward_x * 0.14 - right_x * 0.07, head_y - 0.10, pz - forward_z * 0.14 - right_z * 0.07), 0.07, 0.02, 0.14, 5, self.color_hair)
        pr.draw_cylinder(pr.Vector3(px - forward_x * 0.14 + right_x * 0.07, head_y - 0.10, pz - forward_z * 0.14 + right_z * 0.07), 0.07, 0.02, 0.14, 5, self.color_hair)

        # 10. ATHLETIC HEADBAND (Wrapped around forehead and back hair)
        if self.headband_color is not None:
            hb_y = head_y + 0.03
            pr.draw_cylinder(pr.Vector3(px, hb_y, pz), 0.292, 0.292, 0.075, 24, self.headband_color)

        # 11. SPIKY ANIME HAIR CLUMPS (Stylized 3D hair clumps)
        if self.hair_style == 0:  # Spiky Crown (Photo Default)
            # Center Crown Peak
            pr.draw_cylinder(pr.Vector3(px + forward_x * 0.01, head_y + 0.18, pz + forward_z * 0.01), 0.15, 0.02, 0.32, 6, self.color_hair)
            # Back-top Spike Clumps (leaning back slightly)
            pr.draw_cylinder(pr.Vector3(px - forward_x * 0.10, head_y + 0.16, pz - forward_z * 0.10), 0.14, 0.02, 0.28, 6, self.color_hair)
            pr.draw_cylinder(pr.Vector3(px - forward_x * 0.10 - right_x * 0.11, head_y + 0.14, pz - forward_z * 0.10 - right_z * 0.11), 0.12, 0.02, 0.26, 6, self.color_hair)
            pr.draw_cylinder(pr.Vector3(px - forward_x * 0.10 + right_x * 0.11, head_y + 0.14, pz - forward_z * 0.10 + right_z * 0.11), 0.12, 0.02, 0.26, 6, self.color_hair)
            # Left & Right Horn Spikes
            lh_x = px - right_x * 0.16 + forward_x * 0.04
            lh_z = pz - right_z * 0.16 + forward_z * 0.04
            pr.draw_cylinder(pr.Vector3(lh_x, head_y + 0.12, lh_z), 0.13, 0.02, 0.28, 6, self.color_hair)
            rh_x = px + right_x * 0.16 + forward_x * 0.04
            rh_z = pz + right_z * 0.16 + forward_z * 0.04
            pr.draw_cylinder(pr.Vector3(rh_x, head_y + 0.12, rh_z), 0.13, 0.02, 0.28, 6, self.color_hair)
            # Side Bangs
            pr.draw_cylinder(pr.Vector3(px - right_x * 0.22, head_y + 0.02, pz - right_z * 0.22), 0.09, 0.02, 0.18, 5, self.color_hair)
            pr.draw_cylinder(pr.Vector3(px + right_x * 0.22, head_y + 0.02, pz + right_z * 0.22), 0.09, 0.02, 0.18, 5, self.color_hair)
            # Forehead bangs
            pr.draw_cylinder(pr.Vector3(px + forward_x * 0.18, head_y + 0.16, pz + forward_z * 0.18), 0.08, 0.02, 0.12, 5, self.color_hair)
        elif self.hair_style == 1:  # Wild Anime Spikes
            for ang in [-0.28, -0.14, 0.0, 0.14, 0.28]:
                sp_x = px + right_x * (ang * 0.8) + forward_x * 0.02
                sp_z = pz + right_z * (ang * 0.8) + forward_z * 0.02
                pr.draw_cylinder(pr.Vector3(sp_x, head_y + 0.15, sp_z), 0.11, 0.02, 0.32, 5, self.color_hair)
        elif self.hair_style == 2:  # Athletic Crop
            pr.draw_sphere(pr.Vector3(px, head_y + 0.11, pz), 0.27, self.color_hair)
            pr.draw_cylinder(pr.Vector3(px, head_y + 0.15, pz), 0.16, 0.03, 0.16, 6, self.color_hair)
        else:  # Swept Flow
            pr.draw_cylinder(pr.Vector3(px + right_x * 0.10, head_y + 0.14, pz + right_z * 0.10), 0.18, 0.02, 0.26, 6, self.color_hair)
            pr.draw_cylinder(pr.Vector3(px - right_x * 0.12, head_y + 0.10, pz - right_z * 0.12), 0.14, 0.02, 0.22, 6, self.color_hair)

        # 10. ATHLETIC ANIME ARMS & PROCEDURAL VOLLEYBALL POSES
        hand_rad = 0.135
        arm_bob = math.sin(self.anim_time * 15.0) * 0.12 if self.action == PlayerAction.RUN else idle_bob * 2.0
        prog = 1.0 - (self.action_timer / max(0.001, self.action_duration)) if self.action_timer > 0.0 else 0.0

        # Shoulder attachment points
        s1 = pr.Vector3(px - right_x * 0.22, base_y + 1.14, pz - right_z * 0.22)
        s2 = pr.Vector3(px + right_x * 0.22, base_y + 1.14, pz + right_z * 0.22)

        if self.action == PlayerAction.SERVE_HOLD:
            # Server Stance: Ready crouch holding the ball firmly in both hands
            hold_bob = math.sin(self.anim_time * 3.5) * 0.02
            bc_x = px + forward_x * 0.52
            bc_y = base_y + 1.25 + hold_bob
            bc_z = pz + forward_z * 0.52

            # Left hand cradling bottom-left of ball
            h1 = pr.Vector3(bc_x - right_x * 0.20, bc_y - 0.05, bc_z - right_z * 0.20)
            # Right hand resting on bottom-right of ball
            h2 = pr.Vector3(bc_x + right_x * 0.20, bc_y - 0.05, bc_z + right_z * 0.20)

            self._draw_arm(s1, h1, hand_rad, is_right=False)
            self._draw_arm(s2, h2, hand_rad, is_right=True)

        elif self.action == PlayerAction.SERVE_TOSS:
            # Dynamic Toss Animation: Hands thrust upward to release ball into air
            if prog < 0.45:
                toss_t = prog / 0.45
                t_y = (base_y + 1.25) + (head_y + 0.48 - (base_y + 1.25)) * math.sin(toss_t * math.pi * 0.5)
                t_fwd = 0.52 - 0.24 * toss_t
                h1 = pr.Vector3(px + forward_x * t_fwd - right_x * 0.18, t_y, pz + forward_z * t_fwd - right_z * 0.18)
                h2 = pr.Vector3(px + forward_x * t_fwd + right_x * 0.18, t_y, pz + forward_z * t_fwd + right_z * 0.18)
            else:
                # Follow-through high overhead
                h1 = pr.Vector3(px + forward_x * 0.28 - right_x * 0.22, head_y + 0.48, pz + forward_z * 0.28 - right_z * 0.22)
                h2 = pr.Vector3(px + forward_x * 0.28 + right_x * 0.22, head_y + 0.48, pz + forward_z * 0.28 + right_z * 0.22)

            self._draw_arm(s1, h1, hand_rad, is_right=False)
            self._draw_arm(s2, h2, hand_rad, is_right=True)

        elif self.action == PlayerAction.BUMP:
            # Bump / Receive (Manşet): Knees deeply bent, hands clasped rigidly in front
            h1 = pr.Vector3(px + forward_x * 0.44 - right_x * 0.07, base_y + 0.80, pz + forward_z * 0.44 - right_z * 0.07)
            h2 = pr.Vector3(px + forward_x * 0.44 + right_x * 0.07, base_y + 0.80, pz + forward_z * 0.44 + right_z * 0.07)
            self._draw_arm(s1, h1, hand_rad, is_right=False)
            self._draw_arm(s2, h2, hand_rad, is_right=True)
            # Forearm contact bridge
            pr.draw_cylinder(h1, 0.07, 0.07, 0.14, 6, pr.Color(255, 230, 180, 220))

        elif self.action == PlayerAction.SET:
            # Set / Overhead Pass: Hands raised high in overhead triangular setting cup
            set_lift = 0.05 * math.sin(prog * math.pi)
            h1 = pr.Vector3(px + forward_x * 0.20 - right_x * 0.19, head_y + 0.30 + set_lift, pz + forward_z * 0.20 - right_z * 0.19)
            h2 = pr.Vector3(px + forward_x * 0.20 + right_x * 0.19, head_y + 0.30 + set_lift, pz + forward_z * 0.20 + right_z * 0.19)
            self._draw_arm(s1, h1, hand_rad, is_right=False)
            self._draw_arm(s2, h2, hand_rad, is_right=True)

        elif self.action == PlayerAction.SPIKE:
            # Dynamic Spike Swing: Wind-up -> Explosive downward whip!
            if prog < 0.32:
                spike_hand = pr.Vector3(px - forward_x * 0.18 + right_x * 0.30, head_y + 0.42, pz - forward_z * 0.18 + right_z * 0.30)
                off_hand   = pr.Vector3(px + forward_x * 0.42 - right_x * 0.16, head_y + 0.18, pz + forward_z * 0.42 - right_z * 0.16)
            else:
                whip_t = (prog - 0.32) / 0.68
                sh_fwd = 0.15 + 0.50 * (1.0 - math.cos(whip_t * math.pi * 0.5))
                sh_h = head_y + 0.42 - 0.70 * whip_t
                spike_hand = pr.Vector3(px + forward_x * sh_fwd + right_x * (0.30 - 0.45 * whip_t), sh_h, pz + forward_z * sh_fwd + right_z * (0.30 - 0.45 * whip_t))
                off_hand   = pr.Vector3(px - forward_x * 0.20 - right_x * 0.30, base_y + 0.95, pz - forward_z * 0.20 - right_z * 0.30)

            self._draw_arm(s1, off_hand, hand_rad, is_right=False)
            self._draw_arm(s2, spike_hand, hand_rad * 1.18, is_right=True)

            if self.spike_spark_timer > 0.0:
                pr.draw_sphere(spike_hand, hand_rad * 1.5, pr.Color(255, 215, 0, 150))
                pr.draw_sphere(spike_hand, hand_rad * 2.2, pr.Color(255, 90, 20, 90))

        elif self.action == PlayerAction.DUMP:
            # Dump / Soft Tip: Subtle high touch feathering ball over net
            dump_hand = pr.Vector3(px + forward_x * 0.40 + right_x * 0.12, head_y + 0.32, pz + forward_z * 0.40 + right_z * 0.12)
            off_hand  = pr.Vector3(px - forward_x * 0.10 - right_x * 0.28, base_y + 1.05, pz - forward_z * 0.10 - right_z * 0.28)
            self._draw_arm(s1, off_hand, hand_rad, is_right=False)
            self._draw_arm(s2, dump_hand, hand_rad, is_right=True)
            pr.draw_sphere(dump_hand, hand_rad * 1.3, pr.Color(40, 220, 255, 120))

        elif self.action == PlayerAction.SETTER_DUMP:
            # Setter Dump: Deceptive swift push straight over net
            dump_hand = pr.Vector3(px + forward_x * 0.52 + right_x * 0.08, head_y + 0.15, pz + forward_z * 0.52 + right_z * 0.08)
            off_hand  = pr.Vector3(px - forward_x * 0.15 - right_x * 0.25, base_y + 0.95, pz - forward_z * 0.15 - right_z * 0.25)
            self._draw_arm(s1, off_hand, hand_rad, is_right=False)
            self._draw_arm(s2, dump_hand, hand_rad * 1.1, is_right=True)
            pr.draw_sphere(dump_hand, hand_rad * 1.4, pr.Color(255, 215, 0, 130))

        elif self.action == PlayerAction.ROLL_DIG:
            # Acrobatic Roll Dig: Diving tumble roll across floor, scoops ball up
            roll_angle = prog * 2.0 * math.pi
            reach_dist = 0.55 + 0.35 * math.sin(roll_angle)
            h1 = pr.Vector3(px + forward_x * reach_dist + right_x * 0.12, base_y + 0.20, pz + forward_z * reach_dist + right_z * 0.12)
            h2 = pr.Vector3(px - forward_x * 0.20 - right_x * 0.22, base_y + 0.35, pz - forward_z * 0.20 - right_z * 0.22)
            self._draw_arm(s1, h2, hand_rad, is_right=False)
            self._draw_arm(s2, h1, hand_rad * 1.1, is_right=True)
            pr.draw_circle_3d(pr.Vector3(px, 0.08, pz), 0.7, pr.Vector3(0, 1, 0), 0.0, pr.Color(255, 215, 0, 130))

        elif self.action == PlayerAction.AIR_BAILOUT:
            # Emergency Air Bailout: One-hand / foot reach in mid-air
            reach_hand = pr.Vector3(px + forward_x * 0.70 + right_x * 0.10, head_y + 0.40, pz + forward_z * 0.70 + right_z * 0.10)
            off_hand   = pr.Vector3(px - forward_x * 0.30 - right_x * 0.30, base_y + 0.90, pz - forward_z * 0.30 - right_z * 0.30)
            self._draw_arm(s1, off_hand, hand_rad, is_right=False)
            self._draw_arm(s2, reach_hand, hand_rad * 1.1, is_right=True)
            pr.draw_sphere(reach_hand, hand_rad * 1.4, pr.Color(255, 120, 60, 130))

        elif self.action == PlayerAction.CELEBRATE:
            # Celebrate: Hands held high in victory
            h1 = pr.Vector3(px - right_x * 0.36, head_y + 0.32, pz - right_z * 0.36)
            h2 = pr.Vector3(px + right_x * 0.36, head_y + 0.32, pz + right_z * 0.36)
            self._draw_arm(s1, h1, hand_rad, is_right=False)
            self._draw_arm(s2, h2, hand_rad, is_right=True)

        elif self.action == PlayerAction.BLOCK:
            # Block Pose: Hands thrust rigidly upward and slightly forward over net with fingers spread
            bh_y = head_y + 0.58
            bh_fwd = 0.28
            h1 = pr.Vector3(px + forward_x * bh_fwd - right_x * 0.17, bh_y, pz + forward_z * bh_fwd - right_z * 0.17)
            h2 = pr.Vector3(px + forward_x * bh_fwd + right_x * 0.17, bh_y, pz + forward_z * bh_fwd + right_z * 0.17)
            self._draw_arm(s1, h1, hand_rad * 1.15, is_right=False)
            self._draw_arm(s2, h2, hand_rad * 1.15, is_right=True)
            # Energy blocking shield between palms
            shield_c = pr.Vector3(px + forward_x * bh_fwd, bh_y, pz + forward_z * bh_fwd)
            pr.draw_cube(shield_c, 0.65, 0.35, 0.08, pr.Color(60, 220, 255, 150))
            pr.draw_cube_wires(shield_c, 0.65, 0.35, 0.08, pr.Color(255, 255, 255, 220))

        elif self.action == PlayerAction.MENU_IDLE:
            # Menu Hero Pose: Standing tall, looking at the court, holding volleyball tucked at right hip!
            breath = math.sin(self.anim_time * 2.8) * 0.015
            
            # Left arm (screen-left) hangs relaxed at the side
            h2 = pr.Vector3(px + right_x * 0.28, base_y + 0.74 + breath, pz - right_z * 0.28)
            self._draw_arm(s2, h2, hand_rad * 0.95, is_right=False)
            
            # Right arm (screen-right) bent inward, supporting the volleyball against hip
            vb_pos = pr.Vector3(px - right_x * 0.29, base_y + 0.90 + breath, pz + forward_z * 0.04)
            h1 = pr.Vector3(vb_pos.x - right_x * 0.03, vb_pos.y - 0.10, vb_pos.z)
            self._draw_arm(s1, h1, hand_rad * 0.95, is_right=True)
            
            # THE VOLLEYBALL HELD UNDER ARM (Mikasa Blue, Yellow, White with Mini Crown Logo matching reference photo)
            pr.draw_sphere(vb_pos, 0.21, pr.Color(250, 252, 255, 255))
            # Bold Royal Blue Curved Panel
            pr.draw_sphere(pr.Vector3(vb_pos.x - 0.04, vb_pos.y + 0.03, vb_pos.z - 0.02), 0.175, pr.Color(25, 80, 225, 255))
            # Bold Golden Yellow Curved Panel
            pr.draw_sphere(pr.Vector3(vb_pos.x + 0.04, vb_pos.y - 0.03, vb_pos.z - 0.02), 0.175, pr.Color(255, 215, 0, 255))
            # Crisp Panel Swirl Seams
            pr.draw_circle_3d(vb_pos, 0.212, pr.Vector3(0, 1, 0), 40.0, pr.Color(255, 215, 0, 255))
            pr.draw_circle_3d(vb_pos, 0.212, pr.Vector3(1, 0, 0), 45.0, pr.Color(25, 80, 225, 255))
            pr.draw_circle_3d(vb_pos, 0.212, pr.Vector3(0, 0, 1), 35.0, pr.Color(255, 255, 255, 255))
            # Center crown emblem on ball facing camera (-forward_z)
            pr.draw_circle_3d(pr.Vector3(vb_pos.x, vb_pos.y, vb_pos.z - 0.212), 0.052, pr.Vector3(0, 0, -1), 0.0, pr.Color(20, 25, 35, 255))
            pr.draw_circle_3d(pr.Vector3(vb_pos.x, vb_pos.y, vb_pos.z - 0.214), 0.026, pr.Vector3(0, 0, -1), 0.0, pr.Color(255, 215, 0, 255))

        else:
            # Idle & Running: Arms extend gracefully down to hands beside hips
            h1 = pr.Vector3(px - right_x * 0.34 + forward_x * arm_bob, base_y + 0.95 - arm_bob, pz - right_z * 0.34 + forward_z * arm_bob)
            h2 = pr.Vector3(px + right_x * 0.34 - forward_x * arm_bob, base_y + 0.95 + arm_bob, pz + right_z * 0.34 - forward_z * arm_bob)
            self._draw_arm(s1, h1, hand_rad, is_right=False)
            self._draw_arm(s2, h2, hand_rad, is_right=True)

    def _draw_arm(self, shoulder, hand, hand_rad, is_right=False):
        """Draws athletic character arm connecting shoulder to hand with athletic wristband."""
        pr.draw_capsule(shoulder, hand, 0.058, 8, 8, self.color_skin)
        wrist = pr.Vector3(
            hand.x * 0.74 + shoulder.x * 0.26,
            hand.y * 0.74 + shoulder.y * 0.26,
            hand.z * 0.74 + shoulder.z * 0.26
        )
        if self.color_wristband is not None:
            pr.draw_cylinder(wrist, 0.076, 0.076, 0.05, 8, self.color_wristband)
        else:
            pr.draw_sphere(wrist, 0.074, pr.Color(248, 250, 255, 255))
        pr.draw_sphere(hand, hand_rad, self.color_skin)

    def _draw_back_emblem(self, pos, fwd_x, fwd_z, rt_x, rt_z, logo_id, col):
        """Draws stylized logo on upper back of the jersey (FlyHigh Crown, Wings, etc.)."""
        if logo_id == 0:  # FlyHigh Crown Emblem (Signature from reference image)
            # Center Crown Peak (tallest)
            pr.draw_cube(pr.Vector3(pos.x, pos.y + 0.042, pos.z), 0.034, 0.09, 0.02, col)
            # Left Crown Peak (angled)
            pr.draw_cube(pr.Vector3(pos.x - rt_x * 0.048, pos.y + 0.032, pos.z - rt_z * 0.048), 0.028, 0.076, 0.02, col)
            # Right Crown Peak (angled)
            pr.draw_cube(pr.Vector3(pos.x + rt_x * 0.048, pos.y + 0.032, pos.z + rt_z * 0.048), 0.028, 0.076, 0.02, col)
            # Connecting web chevrons
            pr.draw_cube(pr.Vector3(pos.x - rt_x * 0.025, pos.y + 0.005, pos.z - rt_z * 0.025), 0.026, 0.04, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x + rt_x * 0.025, pos.y + 0.005, pos.z + rt_z * 0.025), 0.026, 0.04, 0.02, col)
            # Solid Base Band
            pr.draw_cube(pr.Vector3(pos.x, pos.y - 0.028, pos.z), 0.125, 0.028, 0.02, col)
            # Bottom Point / V-Crest
            pr.draw_cube(pr.Vector3(pos.x, pos.y - 0.052, pos.z), 0.038, 0.028, 0.02, col)
        elif logo_id == 1:  # Angel Wings
            pr.draw_cube(pr.Vector3(pos.x, pos.y, pos.z), 0.03, 0.08, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x - rt_x * 0.06, pos.y + 0.02, pos.z - rt_z * 0.06), 0.08, 0.03, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x + rt_x * 0.06, pos.y + 0.02, pos.z + rt_z * 0.06), 0.08, 0.03, 0.02, col)
        elif logo_id == 2:  # Flame
            pr.draw_cube(pr.Vector3(pos.x, pos.y + 0.03, pos.z), 0.04, 0.10, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x, pos.y - 0.04, pos.z), 0.09, 0.04, 0.02, col)
        elif logo_id == 3:  # Lightning
            pr.draw_cube(pr.Vector3(pos.x - rt_x * 0.025, pos.y + 0.04, pos.z - rt_z * 0.025), 0.035, 0.07, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x, pos.y, pos.z), 0.08, 0.03, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x + rt_x * 0.025, pos.y - 0.04, pos.z + rt_z * 0.025), 0.035, 0.07, 0.02, col)

    def _draw_digit(self, pos, fwd_x, fwd_z, rt_x, rt_z, digit, col):
        """Draws athletic jersey number in bold 3D geometry on chest."""
        d_scale = 0.035
        # Digits 1-9 simplified geometric glyphs
        if digit == 5:
            # Top bar
            pr.draw_cube(pr.Vector3(pos.x, pos.y + 0.08, pos.z), 0.12, 0.03, 0.02, col)
            # Left upper stem
            pr.draw_cube(pr.Vector3(pos.x - rt_x * 0.045, pos.y + 0.045, pos.z - rt_z * 0.045), 0.03, 0.05, 0.02, col)
            # Mid bar
            pr.draw_cube(pr.Vector3(pos.x, pos.y + 0.01, pos.z), 0.11, 0.028, 0.02, col)
            # Right lower stem
            pr.draw_cube(pr.Vector3(pos.x + rt_x * 0.045, pos.y - 0.035, pos.z + rt_z * 0.045), 0.03, 0.06, 0.02, col)
            # Bottom bar
            pr.draw_cube(pr.Vector3(pos.x, pos.y - 0.07, pos.z), 0.12, 0.03, 0.02, col)
        elif digit == 1:
            pr.draw_cube(pr.Vector3(pos.x, pos.y, pos.z), 0.04, 0.16, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x, pos.y - 0.08, pos.z), 0.10, 0.03, 0.02, col)
        elif digit == 2:
            pr.draw_cube(pr.Vector3(pos.x, pos.y + 0.07, pos.z), 0.12, 0.03, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x + rt_x * 0.045, pos.y + 0.035, pos.z + rt_z * 0.045), 0.03, 0.05, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x, pos.y, pos.z), 0.11, 0.028, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x - rt_x * 0.045, pos.y - 0.035, pos.z - rt_z * 0.045), 0.03, 0.05, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x, pos.y - 0.07, pos.z), 0.12, 0.03, 0.02, col)
        elif digit == 3:
            pr.draw_cube(pr.Vector3(pos.x, pos.y + 0.07, pos.z), 0.12, 0.03, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x + rt_x * 0.045, pos.y, pos.z + rt_z * 0.045), 0.03, 0.16, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x, pos.y, pos.z), 0.10, 0.028, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x, pos.y - 0.07, pos.z), 0.12, 0.03, 0.02, col)
        elif digit == 4:
            pr.draw_cube(pr.Vector3(pos.x - rt_x * 0.045, pos.y + 0.03, pos.z - rt_z * 0.045), 0.03, 0.09, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x, pos.y, pos.z), 0.11, 0.03, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x + rt_x * 0.045, pos.y, pos.z + rt_z * 0.045), 0.03, 0.16, 0.02, col)
        else: # 6 or default
            pr.draw_cube(pr.Vector3(pos.x, pos.y + 0.07, pos.z), 0.12, 0.03, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x - rt_x * 0.045, pos.y, pos.z - rt_z * 0.045), 0.03, 0.16, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x, pos.y, pos.z), 0.11, 0.028, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x + rt_x * 0.045, pos.y - 0.035, pos.z + rt_z * 0.045), 0.03, 0.06, 0.02, col)
            pr.draw_cube(pr.Vector3(pos.x, pos.y - 0.07, pos.z), 0.12, 0.03, 0.02, col)
