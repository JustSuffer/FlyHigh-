"""
FlyHigh! - 3D Volleyball Game
Stylized Low-Poly 3D Player Character
Procedural animation, dynamic poses, jersey colors, and physics.
"""
import pyray as pr
import math
from constants import (
    PLAYER_RADIUS, PLAYER_HEIGHT, PLAYER_SPEED, PLAYER_SPRINT_SPEED,
    PLAYER_JUMP_FORCE, PLAYER_REACH_RADIUS, PLAYER_SPIKE_REACH,
    Team, PlayerAction, GRAVITY
)

# Team Color Palettes
PALETTE_PLAYER = {
    "jersey": pr.Color(30, 110, 220, 255),    # Vibrant Royal Blue
    "shorts": pr.Color(20, 30, 50, 255),      # Navy
    "skin":   pr.Color(235, 190, 150, 255),   # Skin tone
    "hair":   pr.Color(45, 30, 20, 255),      # Dark hair
    "shoes":  pr.Color(245, 245, 245, 255),   # Clean white sneakers
    "kneepad":pr.Color(30, 30, 35, 255),
    "trim":   pr.Color(255, 215, 0, 255)      # Gold accents
}

PALETTE_OPPONENT = {
    "jersey": pr.Color(220, 45, 45, 255),     # Crimson Red
    "shorts": pr.Color(40, 20, 25, 255),      # Dark Maroon
    "skin":   pr.Color(225, 180, 140, 255),
    "hair":   pr.Color(35, 35, 40, 255),
    "shoes":  pr.Color(245, 245, 245, 255),
    "kneepad":pr.Color(30, 30, 35, 255),
    "trim":   pr.Color(255, 255, 255, 255)
}

class Character:
    def __init__(self, x=0.0, z=-5.0, team=Team.PLAYER, jersey_num=7, is_ai=False):
        self.x = x
        self.y = 0.0
        self.z = z
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        
        self.team = team
        self.jersey_num = jersey_num
        self.is_ai = is_ai
        self.palette = PALETTE_PLAYER if team == Team.PLAYER else PALETTE_OPPONENT
        
        # Orientation (radians, 0 means facing +Z toward opponent court)
        self.facing_angle = 0.0 if team == Team.PLAYER else math.pi
        
        # State & Animation
        self.action = PlayerAction.IDLE
        self.action_timer = 0.0
        self.is_grounded = True
        self.anim_time = 0.0
        self.stamina = 1.0

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
        self.facing_angle = 0.0 if self.team == Team.PLAYER else math.pi

    def jump(self):
        if self.is_grounded:
            self.vy = PLAYER_JUMP_FORCE
            self.is_grounded = False
            self.action = PlayerAction.JUMP
            self.action_timer = 0.0

    def trigger_action(self, action, duration=0.35):
        self.action = action
        self.action_timer = duration

    def update(self, dt, move_dir_x=0.0, move_dir_z=0.0, look_target=None):
        """Updates character physics, movement, and procedural animation timer."""
        self.anim_time += dt

        # Update action timer
        if self.action_timer > 0.0:
            self.action_timer -= dt
            if self.action_timer <= 0.0 and self.is_grounded:
                self.action = PlayerAction.IDLE

        # Movement physics
        move_mag = math.sqrt(move_dir_x * move_dir_x + move_dir_z * move_dir_z)
        if move_mag > 0.1:
            speed = PLAYER_SPEED
            self.vx = (move_dir_x / move_mag) * speed
            self.vz = (move_dir_z / move_mag) * speed
            if self.is_grounded and self.action in [PlayerAction.IDLE, PlayerAction.RUN]:
                self.action = PlayerAction.RUN
        else:
            self.vx *= 0.7
            self.vz *= 0.7
            if self.is_grounded and self.action == PlayerAction.RUN:
                self.action = PlayerAction.IDLE

        # Vertical jumping / gravity physics
        if not self.is_grounded:
            self.vy += GRAVITY * dt
            self.y += self.vy * dt
            if self.y <= 0.0:
                self.y = 0.0
                self.vy = 0.0
                self.is_grounded = True
                if self.action == PlayerAction.JUMP:
                    self.action = PlayerAction.IDLE

        # Apply position
        self.x += self.vx * dt
        self.z += self.vz * dt

        # Orientation / Facing direction
        if look_target is not None:
            # Face specific 3D point (e.g. ball or opponent net)
            dx = look_target[0] - self.x
            dz = look_target[1] - self.z
            if dx != 0 or dz != 0:
                self.facing_angle = math.atan2(dx, dz)
        elif move_mag > 0.1:
            # Face movement direction
            self.facing_angle = math.atan2(move_dir_x, move_dir_z)
        else:
            # Default face net (Z=0)
            default_angle = 0.0 if self.team == Team.PLAYER else math.pi
            self.facing_angle = default_angle

    def dist_to_ball(self, ball):
        dx = ball.x - self.x
        dy = ball.y - (self.y + PLAYER_HEIGHT * 0.7)
        dz = ball.z - self.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def can_reach_ball(self, ball):
        """Checks if ball is within hitting distance."""
        horiz_dist = math.sqrt((ball.x - self.x) ** 2 + (ball.z - self.z) ** 2)
        # Player hit reach: cylinder around player from ground up to hands
        max_reach = PLAYER_SPIKE_REACH if not self.is_grounded else PLAYER_REACH_RADIUS
        return horiz_dist <= max_reach and (ball.y >= self.y) and (ball.y <= self.y + 3.2)

    def draw(self):
        """Renders 3D stylized low-poly player character with animation poses."""
        px, py, pz = self.x, self.y, self.z
        angle = self.facing_angle
        p = self.palette

        # 1. Ground Shadow (Oval under player feet)
        pr.draw_circle_3d(
            pr.Vector3(px, 0.02, pz),
            PLAYER_RADIUS * 1.1,
            pr.Vector3(1, 0, 0), 90.0,
            pr.Color(20, 20, 25, 120)
        )

        # Direction offsets based on facing angle
        forward_x = math.sin(angle)
        forward_z = math.cos(angle)
        right_x = math.cos(angle)
        right_z = -math.sin(angle)

        # Procedural limb oscillation for running
        run_cycle = math.sin(self.anim_time * 14.0) if self.action == PlayerAction.RUN else 0.0
        leg_offset = run_cycle * 0.22

        # 2. Shoes / Feet (Gym sneakers)
        foot_y = py + 0.1
        # Left foot
        pr.draw_cube(
            pr.Vector3(px - right_x * 0.18 + forward_x * leg_offset, foot_y, pz - right_z * 0.18 + forward_z * leg_offset),
            0.16, 0.14, 0.32, p["shoes"]
        )
        # Right foot
        pr.draw_cube(
            pr.Vector3(px + right_x * 0.18 - forward_x * leg_offset, foot_y, pz + right_z * 0.18 - forward_z * leg_offset),
            0.16, 0.14, 0.32, p["shoes"]
        )

        # 3. Legs & Kneepads
        leg_mid_y = py + 0.42
        pr.draw_cylinder(
            pr.Vector3(px - right_x * 0.18 + forward_x * (leg_offset * 0.5), py + 0.15, pz - right_z * 0.18 + forward_z * (leg_offset * 0.5)),
            0.08, 0.09, 0.5, 8, p["skin"]
        )
        pr.draw_cylinder(
            pr.Vector3(px + right_x * 0.18 - forward_x * (leg_offset * 0.5), py + 0.15, pz + right_z * 0.18 - forward_z * (leg_offset * 0.5)),
            0.08, 0.09, 0.5, 8, p["skin"]
        )
        # Kneepads
        pr.draw_cylinder(
            pr.Vector3(px - right_x * 0.18, py + 0.45, pz - right_z * 0.18),
            0.11, 0.11, 0.18, 8, p["kneepad"]
        )
        pr.draw_cylinder(
            pr.Vector3(px + right_x * 0.18, py + 0.45, pz + right_z * 0.18),
            0.11, 0.11, 0.18, 8, p["kneepad"]
        )

        # 4. Shorts (Navy / Dark)
        shorts_y = py + 0.8
        pr.draw_cylinder(
            pr.Vector3(px, shorts_y, pz),
            0.26, 0.28, 0.38, 10, p["shorts"]
        )

        # 5. Torso / Volleyball Jersey
        torso_y = py + 1.25
        pr.draw_cube(
            pr.Vector3(px, torso_y, pz),
            0.52, 0.65, 0.32, p["jersey"]
        )
        # Number back / front accent
        pr.draw_cube(
            pr.Vector3(px + forward_x * 0.17, torso_y + 0.05, pz + forward_z * 0.17),
            0.18, 0.22, 0.02, p["trim"]
        )

        # 6. Arms & Hands (Pose based on Action)
        shoulder_y = py + 1.45
        left_shoulder  = pr.Vector3(px - right_x * 0.32, shoulder_y, pz - right_z * 0.32)
        right_shoulder = pr.Vector3(px + right_x * 0.32, shoulder_y, pz + right_z * 0.32)

        if self.action == PlayerAction.BUMP:
            # Bump / Manşet: Both arms clasped straight in front, angled up at 45 deg
            hands_pos = pr.Vector3(px + forward_x * 0.45, shoulder_y - 0.25, pz + forward_z * 0.45)
            pr.draw_cylinder(left_shoulder, 0.07, 0.07, 0.45, 6, p["skin"])
            pr.draw_cylinder(right_shoulder, 0.07, 0.07, 0.45, 6, p["skin"])
            pr.draw_sphere(hands_pos, 0.12, p["skin"])
        elif self.action == PlayerAction.SET:
            # Set / Pas: Hands raised high above forehead
            hands_pos = pr.Vector3(px + forward_x * 0.2, shoulder_y + 0.55, pz + forward_z * 0.2)
            pr.draw_cylinder(left_shoulder, 0.07, 0.07, 0.5, 6, p["skin"])
            pr.draw_cylinder(right_shoulder, 0.07, 0.07, 0.5, 6, p["skin"])
            pr.draw_sphere(hands_pos, 0.14, p["skin"])
        elif self.action == PlayerAction.SPIKE:
            # Spike / Smaç: Dominant right arm extended high and forward, left arm for balance
            spike_hand = pr.Vector3(px + right_x * 0.2 + forward_x * 0.45, shoulder_y + 0.75, pz + right_z * 0.2 + forward_z * 0.45)
            pr.draw_cylinder(right_shoulder, 0.07, 0.08, 0.65, 6, p["skin"])
            pr.draw_sphere(spike_hand, 0.14, p["skin"])
            # Left arm back
            pr.draw_cylinder(left_shoulder, 0.07, 0.07, 0.45, 6, p["skin"])
        elif self.action == PlayerAction.CELEBRATE:
            # Celebrate: Both hands raised in victory \o/
            pr.draw_cylinder(left_shoulder, 0.07, 0.07, 0.6, 6, p["skin"])
            pr.draw_cylinder(right_shoulder, 0.07, 0.07, 0.6, 6, p["skin"])
            pr.draw_sphere(pr.Vector3(left_shoulder.x, shoulder_y + 0.6, left_shoulder.z), 0.12, p["skin"])
            pr.draw_sphere(pr.Vector3(right_shoulder.x, shoulder_y + 0.6, right_shoulder.z), 0.12, p["skin"])
        else:
            # Normal Running / Idle arms
            arm_swing = run_cycle * 0.3
            pr.draw_cylinder(
                pr.Vector3(left_shoulder.x - forward_x * arm_swing, shoulder_y - 0.2, left_shoulder.z - forward_z * arm_swing),
                0.07, 0.07, 0.45, 6, p["skin"]
            )
            pr.draw_cylinder(
                pr.Vector3(right_shoulder.x + forward_x * arm_swing, shoulder_y - 0.2, right_shoulder.z + forward_z * arm_swing),
                0.07, 0.07, 0.45, 6, p["skin"]
            )

        # 7. Head & Hair
        head_y = py + 1.72
        head_pos = pr.Vector3(px, head_y, pz)
        pr.draw_sphere(head_pos, 0.22, p["skin"])
        
        # Hair / Cap (low-poly dome)
        pr.draw_sphere(pr.Vector3(px, head_y + 0.08, pz - forward_z * 0.05), 0.21, p["hair"])
        # Headband accent
        pr.draw_cylinder(pr.Vector3(px, head_y + 0.02, pz), 0.23, 0.23, 0.06, 10, p["trim"])
