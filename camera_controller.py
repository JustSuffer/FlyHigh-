"""
FlyHigh! - 3D Volleyball Game
Dynamic 3D Camera System
Includes third-person behind-the-court tracking, broadcast sideline view,
and high isometric overview angles with smooth interpolation.
"""
import pyray as pr
import math

class CameraController:
    MODE_BEHIND = 0      # Primary: Dynamic Chase behind player court
    MODE_BROADCAST = 1   # TV Broadcast sideline view
    MODE_OVERVIEW = 2    # High tactical overview

    def __init__(self):
        self.mode = self.MODE_BEHIND
        
        # Camera current vectors (Comfortable wide angle showing backcourt and baseline)
        self.pos_x = 0.0
        self.pos_y = 6.8
        self.pos_z = -19.2
        
        self.target_x = 0.0
        self.target_y = 1.4
        self.target_z = 0.5
        
        # Raylib Camera3D struct (FOV 60.0 for panoramic coastal beach court visibility)
        self.cam = pr.Camera3D(
            pr.Vector3(self.pos_x, self.pos_y, self.pos_z),
            pr.Vector3(self.target_x, self.target_y, self.target_z),
            pr.Vector3(0.0, 1.0, 0.0),
            60.0,
            pr.CAMERA_PERSPECTIVE
        )

    def cycle_mode(self):
        self.mode = (self.mode + 1) % 3

    def update(self, dt, player, ball):
        """Smoothly interpolates camera position and target based on gameplay action."""
        smooth = 1.0 - math.exp(-7.0 * dt)
        
        if self.mode == self.MODE_BEHIND:
            # Behind player court: wide view showing baseline, backcourt, and full coastal scene
            desired_target_x = player.x * 0.15 + ball.x * 0.15
            desired_target_y = 1.3 + min(1.0, ball.y * 0.10)
            desired_target_z = 1.2

            desired_pos_x = player.x * 0.12
            desired_pos_y = 6.2 + min(1.2, ball.y * 0.10)
            desired_pos_z = -18.2

        elif self.mode == self.MODE_BROADCAST:
            # TV Broadcast sideline view (classic side angle)
            desired_target_x = ball.x * 0.3
            desired_target_y = 1.8 + min(3.0, ball.y * 0.3)
            desired_target_z = ball.z * 0.4

            desired_pos_x = -17.0
            desired_pos_y = 7.8
            desired_pos_z = 0.0

        else: # MODE_OVERVIEW
            # High court overview
            desired_target_x = 0.0
            desired_target_y = 1.0
            desired_target_z = 0.0

            desired_pos_x = 0.0
            desired_pos_y = 16.0
            desired_pos_z = -16.5

        # Smooth interpolation
        self.pos_x += (desired_pos_x - self.pos_x) * smooth
        self.pos_y += (desired_pos_y - self.pos_y) * smooth
        self.pos_z += (desired_pos_z - self.pos_z) * smooth

        self.target_x += (desired_target_x - self.target_x) * smooth
        self.target_y += (desired_target_y - self.target_y) * smooth
        self.target_z += (desired_target_z - self.target_z) * smooth

        # Update raylib camera
        self.cam.position = pr.Vector3(self.pos_x, self.pos_y, self.pos_z)
        self.cam.target = pr.Vector3(self.target_x, self.target_y, self.target_z)

    def get_mode_name(self):
        names = ["Behind Court (Dynamic)", "TV Broadcast (Side)", "High Overview"]
        return names[self.mode]
