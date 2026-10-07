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
    PLAYER_JUMP_FORCE, PLAYER_REACH_RADIUS, PLAYER_SPIKE_REACH,
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
        
        # Color Palettes (Photo-inspired: White jersey, Cyan shorts, Blue/Purple shoes)
        if team == Team.PLAYER:
            self.color_jersey = pr.Color(248, 250, 252, 255)    # White Tank Top
            self.color_trim   = pr.Color(25, 28, 35, 255)        # Black Trim
            self.color_shorts = pr.Color(35, 180, 245, 255)      # Cyan Blue Shorts
            self.color_shoes  = pr.Color(25, 75, 225, 255)       # Royal Blue Sneakers
            self.color_socks  = pr.Color(115, 55, 235, 255)      # Purple Ankle Cuffs
            self.color_number = pr.Color(18, 20, 25, 255)       # Bold Black Digit
            # Default hair: Silver/White for captain, or specific color
            if hair_color is not None:
                self.color_hair = hair_color
            elif jersey_num == 5:
                self.color_hair = pr.Color(238, 240, 245, 255)   # Silver/White Anime Spikes
            elif jersey_num == 2:
                self.color_hair = pr.Color(50, 40, 35, 255)      # Dark Chestnut Spikes
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
        self.anim_time = 0.0
        self.roll_dig_cooldown = 0.0
        
        # Trail & Particle effects on spikes
        self.spike_spark_timer = 0.0

    def reset_position(self, x, z):
        self.x = x
        self.y = 0.0
        self.z = z
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.is_grounded = True
        self.action = PlayerAction.IDLE
        self.action_timer = 0.0
        self.action_duration = 0.35
        self.facing_angle = 0.0 if self.team == Team.PLAYER else math.pi

    def jump(self):
        if self.is_grounded and self.action != PlayerAction.ROLL_DIG:
            self.vy = PLAYER_JUMP_FORCE
            self.is_grounded = False
            self.action = PlayerAction.JUMP
            self.action_timer = 0.0
            self.action_duration = 0.35

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
                self.action = PlayerAction.IDLE

        if self.spike_spark_timer > 0.0:
            self.spike_spark_timer -= dt

        # Movement physics
        move_mag = math.sqrt(move_dir_x * move_dir_x + move_dir_z * move_dir_z)
        if move_mag > 0.1:
            speed = PLAYER_SPEED
            self.vx = (move_dir_x / move_mag) * speed
            self.vz = (move_dir_z / move_mag) * speed
            if self.is_grounded and self.action in [PlayerAction.IDLE, PlayerAction.RUN]:
                self.action = PlayerAction.RUN
        else:
            self.vx *= 0.65
            self.vz *= 0.65
            if self.is_grounded and self.action == PlayerAction.RUN:
                self.action = PlayerAction.IDLE

        # Jumping physics
        if not self.is_grounded:
            self.vy += GRAVITY * dt
            self.y += self.vy * dt
            if self.y <= 0.0:
                self.y = 0.0
                self.vy = 0.0
                self.is_grounded = True
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
        # Calves (Peach skin)
        pr.draw_cylinder(pr.Vector3(lf_pos.x, base_y + 0.22, lf_pos.z), 0.07, 0.08, 0.22, 8, COLOR_SKIN)
        pr.draw_cylinder(pr.Vector3(rf_pos.x, base_y + 0.22, rf_pos.z), 0.07, 0.08, 0.22, 8, COLOR_SKIN)

        # Black Kneepads (Chunky athletic wraps)
        pr.draw_cylinder(pr.Vector3(lf_pos.x, knee_y, lf_pos.z), 0.11, 0.11, 0.16, 10, COLOR_KNEEPAD)
        pr.draw_cylinder(pr.Vector3(rf_pos.x, knee_y, rf_pos.z), 0.11, 0.11, 0.16, 10, COLOR_KNEEPAD)

        # Thighs (Peach skin up to shorts)
        pr.draw_cylinder(pr.Vector3(lf_pos.x, knee_y + 0.14, lf_pos.z), 0.08, 0.10, 0.20, 8, COLOR_SKIN)
        pr.draw_cylinder(pr.Vector3(rf_pos.x, knee_y + 0.14, rf_pos.z), 0.08, 0.10, 0.20, 8, COLOR_SKIN)

        # 4. VOLLEYBALL SHORTS (Cyan / Bright Blue athletic shorts)
        shorts_y = base_y + 0.72
        pr.draw_cylinder(pr.Vector3(px, shorts_y, pz), 0.22, 0.25, 0.28, 12, self.color_shorts)
        # Shorts leg cuffs
        pr.draw_cylinder(pr.Vector3(px - right_x * 0.13, shorts_y - 0.06, pz - right_z * 0.13), 0.12, 0.12, 0.14, 10, self.color_shorts)
        pr.draw_cylinder(pr.Vector3(px + right_x * 0.13, shorts_y - 0.06, pz + right_z * 0.13), 0.12, 0.12, 0.14, 10, self.color_shorts)

        # 5. ATHLETIC SLEEVELESS TANK TOP (Contoured athletic waist, white jersey)
        torso_y = base_y + 1.12
        # Slimmer athletic waist
        pr.draw_cylinder(pr.Vector3(px, base_y + 0.86, pz), 0.20, 0.23, 0.26, 12, self.color_jersey)
        # Upper chest & shoulders
        pr.draw_cylinder(pr.Vector3(px, base_y + 1.05, pz), 0.23, 0.25, 0.30, 12, self.color_jersey)
        
        # Black border trim along armholes and collar
        pr.draw_cylinder(pr.Vector3(px, base_y + 1.32, pz), 0.14, 0.14, 0.04, 10, self.color_trim)

        # JERSEY NUMBER (Rendered on chest)
        num_pos = pr.Vector3(px + forward_x * 0.24, torso_y + 0.05, pz + forward_z * 0.24)
        self._draw_digit(num_pos, forward_x, forward_z, right_x, right_z, self.jersey_num, self.color_number)

        # 6. SLENDER NECK
        neck_y = base_y + 1.36
        pr.draw_cylinder(pr.Vector3(px, neck_y, pz), 0.08, 0.08, 0.14, 8, COLOR_SKIN)

        # 7. CHIBI ROUND HEAD (Warm anime peach skin)
        head_y = base_y + 1.62
        head_pos = pr.Vector3(px, head_y, pz)
        pr.draw_sphere(head_pos, 0.26, COLOR_SKIN)

        # Chibi rounded ears on sides
        pr.draw_sphere(pr.Vector3(px - right_x * 0.26, head_y - 0.02, pz - right_z * 0.26), 0.08, COLOR_SKIN)
        pr.draw_sphere(pr.Vector3(px + right_x * 0.26, head_y - 0.02, pz + right_z * 0.26), 0.08, COLOR_SKIN)

        # 8. EXPRESSIVE ANIME FACE (Eyes, eyebrows, nose, mouth)
        face_fwd = 0.24
        # Left Eye (Almond with dark iris & white highlight)
        le_pos = pr.Vector3(px + forward_x * face_fwd - right_x * 0.08, head_y + 0.03, pz + forward_z * face_fwd - right_z * 0.08)
        re_pos = pr.Vector3(px + forward_x * face_fwd + right_x * 0.08, head_y + 0.03, pz + forward_z * face_fwd + right_z * 0.08)
        
        # Sclera (White base)
        pr.draw_sphere(le_pos, 0.05, pr.Color(255, 255, 255, 255))
        pr.draw_sphere(re_pos, 0.05, pr.Color(255, 255, 255, 255))
        # Black Iris / Pupil
        pr.draw_sphere(pr.Vector3(le_pos.x + forward_x * 0.02, le_pos.y, le_pos.z + forward_z * 0.02), 0.035, pr.Color(20, 20, 25, 255))
        pr.draw_sphere(pr.Vector3(re_pos.x + forward_x * 0.02, re_pos.y, re_pos.z + forward_z * 0.02), 0.035, pr.Color(20, 20, 25, 255))
        # White anime sparkle highlight
        pr.draw_sphere(pr.Vector3(le_pos.x + forward_x * 0.035 - right_x * 0.015, le_pos.y + 0.015, le_pos.z + forward_z * 0.035 - right_z * 0.015), 0.012, pr.Color(255, 255, 255, 255))
        pr.draw_sphere(pr.Vector3(re_pos.x + forward_x * 0.035 - right_x * 0.015, re_pos.y + 0.015, re_pos.z + forward_z * 0.035 - right_z * 0.015), 0.012, pr.Color(255, 255, 255, 255))

        # Eyebrows (Arched dark lines)
        pr.draw_cube(pr.Vector3(le_pos.x, head_y + 0.10, le_pos.z), 0.08, 0.02, 0.02, COLOR_OUTLINE)
        pr.draw_cube(pr.Vector3(re_pos.x, head_y + 0.10, re_pos.z), 0.08, 0.02, 0.02, COLOR_OUTLINE)

        # Small nose dot
        pr.draw_sphere(pr.Vector3(px + forward_x * (face_fwd + 0.01), head_y - 0.03, pz + forward_z * (face_fwd + 0.01)), 0.018, COLOR_SKIN_SHADOW)
        # Focused mouth line
        pr.draw_cube(pr.Vector3(px + forward_x * (face_fwd + 0.01), head_y - 0.09, pz + forward_z * (face_fwd + 0.01)), 0.07, 0.018, 0.02, pr.Color(50, 30, 25, 255))

        # 9. SPIKY ANIME HAIR (Signature Silver/White Jagged Spikes from Reference Photo!)
        # Back and base volume
        pr.draw_sphere(pr.Vector3(px - forward_x * 0.05, head_y + 0.10, pz - forward_z * 0.05), 0.25, self.color_hair)

        # Prominent Upward Spiky Tufts (Crown Horns)
        # Center Peak Spike
        pr.draw_cylinder(pr.Vector3(px + forward_x * 0.02, head_y + 0.14, pz + forward_z * 0.02), 0.14, 0.02, 0.26, 6, self.color_hair)
        # Left Horn Spike (Angled up-left)
        lh_x = px - right_x * 0.16 + forward_x * 0.04
        lh_z = pz - right_z * 0.16 + forward_z * 0.04
        pr.draw_cylinder(pr.Vector3(lh_x, head_y + 0.12, lh_z), 0.13, 0.02, 0.28, 6, self.color_hair)
        # Right Horn Spike (Angled up-right)
        rh_x = px + right_x * 0.16 + forward_x * 0.04
        rh_z = pz + right_z * 0.16 + forward_z * 0.04
        pr.draw_cylinder(pr.Vector3(rh_x, head_y + 0.12, rh_z), 0.13, 0.02, 0.28, 6, self.color_hair)
        # Side Cheek Bangs (Framing the face)
        pr.draw_cylinder(pr.Vector3(px - right_x * 0.22, head_y + 0.02, pz - right_z * 0.22), 0.09, 0.02, 0.18, 5, self.color_hair)
        pr.draw_cylinder(pr.Vector3(px + right_x * 0.22, head_y + 0.02, pz + right_z * 0.22), 0.09, 0.02, 0.18, 5, self.color_hair)
        # Forehead Bang Tufts
        pr.draw_cylinder(pr.Vector3(px + forward_x * 0.18, head_y + 0.16, pz + forward_z * 0.18), 0.08, 0.02, 0.12, 5, self.color_hair)

        # 10. FLOATING SPHERICAL HANDS (Rayman / Chibi style, exactly as in reference photo!)
        # 10. FLOATING SPHERICAL HANDS & PROCEDURAL POSES
        hand_rad = 0.135
        arm_bob = math.sin(self.anim_time * 15.0) * 0.12 if self.action == PlayerAction.RUN else idle_bob * 2.0
        prog = 1.0 - (self.action_timer / max(0.001, self.action_duration)) if self.action_timer > 0.0 else 0.0

        if self.action == PlayerAction.BUMP:
            # Bump / Receive (Manşet): Knees deeply bent, hands clasped rigidly in front
            h1 = pr.Vector3(px + forward_x * 0.44 - right_x * 0.07, base_y + 0.80, pz + forward_z * 0.44 - right_z * 0.07)
            h2 = pr.Vector3(px + forward_x * 0.44 + right_x * 0.07, base_y + 0.80, pz + forward_z * 0.44 + right_z * 0.07)
            pr.draw_sphere(h1, hand_rad, COLOR_SKIN)
            pr.draw_sphere(h2, hand_rad, COLOR_SKIN)
            # Energy link / forearm platform between hands
            pr.draw_cylinder(h1, 0.07, 0.07, 0.14, 6, pr.Color(255, 230, 180, 220))

        elif self.action == PlayerAction.SET:
            # Set / Overhead Pass: Hands raised high in overhead triangular setting cup
            set_lift = 0.05 * math.sin(prog * math.pi)
            h1 = pr.Vector3(px + forward_x * 0.20 - right_x * 0.19, head_y + 0.30 + set_lift, pz + forward_z * 0.20 - right_z * 0.19)
            h2 = pr.Vector3(px + forward_x * 0.20 + right_x * 0.19, head_y + 0.30 + set_lift, pz + forward_z * 0.20 + right_z * 0.19)
            pr.draw_sphere(h1, hand_rad, COLOR_SKIN)
            pr.draw_sphere(h2, hand_rad, COLOR_SKIN)

        elif self.action == PlayerAction.SPIKE:
            # Dynamic Spike Swing: Wind-up -> Explosive downward whip!
            if prog < 0.32:
                # Wind-up: Right hitting hand cocked back high over shoulder, off hand aiming
                spike_hand = pr.Vector3(px - forward_x * 0.18 + right_x * 0.30, head_y + 0.42, pz - forward_z * 0.18 + right_z * 0.30)
                off_hand   = pr.Vector3(px + forward_x * 0.42 - right_x * 0.16, head_y + 0.18, pz + forward_z * 0.42 - right_z * 0.16)
            else:
                # Power Whip follow-through across the body
                whip_t = (prog - 0.32) / 0.68
                sh_fwd = 0.15 + 0.50 * (1.0 - math.cos(whip_t * math.pi * 0.5))
                sh_h = head_y + 0.42 - 0.70 * whip_t
                spike_hand = pr.Vector3(px + forward_x * sh_fwd + right_x * (0.30 - 0.45 * whip_t), sh_h, pz + forward_z * sh_fwd + right_z * (0.30 - 0.45 * whip_t))
                off_hand   = pr.Vector3(px - forward_x * 0.20 - right_x * 0.30, base_y + 0.95, pz - forward_z * 0.20 - right_z * 0.30)

            pr.draw_sphere(spike_hand, hand_rad * 1.18, COLOR_SKIN)
            pr.draw_sphere(off_hand, hand_rad, COLOR_SKIN)

            if self.spike_spark_timer > 0.0:
                pr.draw_sphere(spike_hand, hand_rad * 1.5, pr.Color(255, 215, 0, 150))
                pr.draw_sphere(spike_hand, hand_rad * 2.2, pr.Color(255, 90, 20, 90))

        elif self.action == PlayerAction.DUMP:
            # Dump / Soft Tip: Subtle high touch feathering ball over net
            dump_hand = pr.Vector3(px + forward_x * 0.40 + right_x * 0.12, head_y + 0.32, pz + forward_z * 0.40 + right_z * 0.12)
            off_hand  = pr.Vector3(px - forward_x * 0.10 - right_x * 0.28, base_y + 1.05, pz - forward_z * 0.10 - right_z * 0.28)
            pr.draw_sphere(dump_hand, hand_rad, COLOR_SKIN)
            pr.draw_sphere(off_hand, hand_rad, COLOR_SKIN)
            # Soft touch cyan aura
            pr.draw_sphere(dump_hand, hand_rad * 1.3, pr.Color(40, 220, 255, 120))

        elif self.action == PlayerAction.SETTER_DUMP:
            # Setter Dump: Deceptive swift push straight over net
            dump_hand = pr.Vector3(px + forward_x * 0.52 + right_x * 0.08, head_y + 0.15, pz + forward_z * 0.52 + right_z * 0.08)
            off_hand  = pr.Vector3(px - forward_x * 0.15 - right_x * 0.25, base_y + 0.95, pz - forward_z * 0.15 - right_z * 0.25)
            pr.draw_sphere(dump_hand, hand_rad * 1.1, COLOR_SKIN)
            pr.draw_sphere(off_hand, hand_rad, COLOR_SKIN)
            pr.draw_sphere(dump_hand, hand_rad * 1.4, pr.Color(255, 215, 0, 130))

        elif self.action == PlayerAction.ROLL_DIG:
            # Acrobatic Roll Dig: Diving tumble roll across floor, scoops ball up
            roll_angle = prog * 2.0 * math.pi
            reach_dist = 0.55 + 0.35 * math.sin(roll_angle)
            h1 = pr.Vector3(px + forward_x * reach_dist + right_x * 0.12, base_y + 0.20, pz + forward_z * reach_dist + right_z * 0.12)
            h2 = pr.Vector3(px - forward_x * 0.20 - right_x * 0.22, base_y + 0.35, pz - forward_z * 0.20 - right_z * 0.22)
            pr.draw_sphere(h1, hand_rad * 1.1, COLOR_SKIN)
            pr.draw_sphere(h2, hand_rad, COLOR_SKIN)
            # Gold speed ring during roll
            pr.draw_circle_3d(pr.Vector3(px, 0.08, pz), 0.7, pr.Vector3(0, 1, 0), 0.0, pr.Color(255, 215, 0, 130))

        elif self.action == PlayerAction.AIR_BAILOUT:
            # Emergency Air Bailout: One-hand / foot reach in mid-air
            reach_hand = pr.Vector3(px + forward_x * 0.70 + right_x * 0.10, head_y + 0.40, pz + forward_z * 0.70 + right_z * 0.10)
            off_hand   = pr.Vector3(px - forward_x * 0.30 - right_x * 0.30, base_y + 0.90, pz - forward_z * 0.30 - right_z * 0.30)
            pr.draw_sphere(reach_hand, hand_rad * 1.1, COLOR_SKIN)
            pr.draw_sphere(off_hand, hand_rad, COLOR_SKIN)
            pr.draw_sphere(reach_hand, hand_rad * 1.4, pr.Color(255, 120, 60, 130))

        elif self.action == PlayerAction.CELEBRATE:
            # Celebrate: Hands held high in victory
            h1 = pr.Vector3(px - right_x * 0.36, head_y + 0.32, pz - right_z * 0.36)
            h2 = pr.Vector3(px + right_x * 0.36, head_y + 0.32, pz + right_z * 0.36)
            pr.draw_sphere(h1, hand_rad, COLOR_SKIN)
            pr.draw_sphere(h2, hand_rad, COLOR_SKIN)

        else:
            # Idle & Running: Spheres float playfully beside the hips
            h1 = pr.Vector3(px - right_x * 0.38 + forward_x * arm_bob, base_y + 0.95 - arm_bob, pz - right_z * 0.38 + forward_z * arm_bob)
            h2 = pr.Vector3(px + right_x * 0.38 - forward_x * arm_bob, base_y + 0.95 + arm_bob, pz + right_z * 0.38 - forward_z * arm_bob)
            pr.draw_sphere(h1, hand_rad, COLOR_SKIN)
            pr.draw_sphere(h2, hand_rad, COLOR_SKIN)

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
