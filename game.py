"""
FlyHigh! - 3D Volleyball Game
Main Game System & Loop
Integrates Court, Ball, Characters, AI, Camera, Audio, Rules, and UI.
"""
import pyray as pr
import math
import random
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_FPS, GAME_TITLE,
    Team, MatchState, PlayerAction, AIDifficulty,
    HALF_WIDTH, HALF_LENGTH, NET_HEIGHT
)
from audio_manager import AudioManager
from input_manager import InputManager
from court import Court
from ball import Ball
from character import Character
from ai_controller import AIController
from camera_controller import CameraController
from match_manager import MatchManager
from ui_renderer import UIRenderer

class VolleyballGame:
    def __init__(self):
        pr.init_window(SCREEN_WIDTH, SCREEN_HEIGHT, GAME_TITLE)
        pr.set_target_fps(TARGET_FPS)

        # Core subsystems
        self.audio_mgr = AudioManager()
        self.input_mgr = InputManager()
        self.court = Court()
        self.ball = Ball()
        self.cam_ctrl = CameraController()
        self.match_mgr = MatchManager(audio_mgr=self.audio_mgr, points_to_win=11)
        self.ui = UIRenderer()

        # Characters
        # Player (Team PLAYER, near court)
        self.player = Character(x=0.0, z=-5.5, team=Team.PLAYER, jersey_num=7, is_ai=False)
        
        # Opponent (Team OPPONENT, far court)
        self.opponent = Character(x=0.0, z=5.5, team=Team.OPPONENT, jersey_num=10, is_ai=True)
        self.ai_diff = AIDifficulty.MEDIUM
        self.opponent_ai = AIController(self.opponent, difficulty=self.ai_diff)

        # Aim Target on opponent court
        self.aim_target_x = 0.0
        self.aim_target_z = 6.0

        # Opponent serve timer
        self.ai_serve_timer = 0.0
        self.is_paused = False

        # Start initial match
        self.match_mgr.reset_match()
        self.setup_serve()

    def setup_serve(self):
        """Positions server and ball for serve phase."""
        if self.match_mgr.serving_team == Team.PLAYER:
            self.player.reset_position(0.0, -9.8)
            self.opponent.reset_position(0.0, 5.5)
            self.ball.reset(x=self.player.x, y=1.4, z=self.player.z + 0.6, team=Team.PLAYER)
        else:
            self.opponent.reset_position(0.0, 9.8)
            self.player.reset_position(0.0, -5.5)
            self.ball.reset(x=self.opponent.x, y=1.4, z=self.opponent.z - 0.6, team=Team.OPPONENT)
            self.ai_serve_timer = random.uniform(1.2, 1.8)

    def run(self):
        """Main game loop."""
        while not pr.window_should_close():
            dt = pr.get_frame_time()
            if dt > 0.05:
                dt = 0.05  # Prevent huge delta spikes

            self.handle_input()
            if not self.is_paused:
                self.update(dt)

            self.render()

        self.cleanup()

    def handle_input(self):
        self.input_mgr.update()

        # Toggle Pause
        if self.input_mgr.pause_pressed:
            if self.match_mgr.state != MatchState.MATCH_OVER:
                self.is_paused = not self.is_paused

        # Cycle Camera
        if self.input_mgr.camera_pressed:
            self.cam_ctrl.cycle_mode()

        # Rematch if Match Over
        if self.match_mgr.state == MatchState.MATCH_OVER:
            if self.input_mgr.jump_pressed or self.input_mgr.select_pressed:
                self.match_mgr.reset_match()
                self.setup_serve()

    def update(self, dt):
        """Updates game state, characters, ball physics, and rules."""
        # 1. Update Match State transitions
        prev_state = self.match_mgr.state
        self.match_mgr.update(dt, self.ball, self.court)

        # If state just reset to SERVE_READY from a point scored
        if prev_state == MatchState.POINT_SCORED and self.match_mgr.state == MatchState.SERVE_READY:
            self.setup_serve()

        # 2. Update Aim Target (Stick / WASD modifies target on opponent court)
        if self.input_mgr.aim_x != 0 or self.input_mgr.aim_z != 0:
            self.aim_target_x += self.input_mgr.aim_x * dt * 8.0
            self.aim_target_z += self.input_mgr.aim_z * dt * 8.0
        else:
            # Gradually center
            self.aim_target_x += (0.0 - self.aim_target_x) * dt * 2.0
            self.aim_target_z += (6.0 - self.aim_target_z) * dt * 2.0

        self.aim_target_x = max(-HALF_WIDTH + 0.5, min(HALF_WIDTH - 0.5, self.aim_target_x))
        self.aim_target_z = max(2.5, min(HALF_LENGTH - 0.5, self.aim_target_z))

        # 3. Serve Logic
        if self.match_mgr.state == MatchState.SERVE_READY:
            if self.match_mgr.serving_team == Team.PLAYER:
                # Keep ball at player's hands until toss
                self.ball.x = self.player.x
                self.ball.y = self.player.y + 1.3
                self.ball.z = self.player.z + 0.6
                self.ball.in_air = False

                # Toss trigger (Jump / Toss button)
                if self.input_mgr.jump_pressed or self.input_mgr.bump_pressed:
                    self.match_mgr.state = MatchState.SERVE_TOSSED
                    self.ball.launch_arc(self.player.x, self.player.z + 0.8, peak_height=3.6)
                    self.audio_mgr.play("whistle")
            else:
                # Opponent AI Serving
                self.ball.x = self.opponent.x
                self.ball.y = self.opponent.y + 1.3
                self.ball.z = self.opponent.z - 0.6
                self.ball.in_air = False
                
                self.ai_serve_timer -= dt
                if self.ai_serve_timer <= 0.0:
                    self.match_mgr.state = MatchState.SERVE_TOSSED
                    self.ball.launch_arc(self.opponent.x, self.opponent.z - 0.8, peak_height=3.8)
                    self.audio_mgr.play("whistle")
                    self.ai_serve_timer = random.uniform(0.55, 0.75)

        elif self.match_mgr.state == MatchState.SERVE_TOSSED:
            # Ball is descending during serve toss: player or CPU can strike!
            if self.match_mgr.serving_team == Team.PLAYER:
                dist_ball = math.sqrt((self.ball.x - self.player.x)**2 + (self.ball.z - self.player.z)**2)
                
                # Check serve hit
                if (self.input_mgr.bump_pressed or self.input_mgr.spike_pressed) and dist_ball < 1.8 and self.ball.y > 1.2:
                    is_jump_serve = not self.player.is_grounded
                    target_x = self.aim_target_x
                    target_z = self.aim_target_z
                    
                    if is_jump_serve:
                        self.player.trigger_action(PlayerAction.SPIKE, 0.35)
                        self.ball.launch_arc(target_x, target_z, is_spike=True, spike_speed=21.0)
                        self.match_mgr.register_hit(Team.PLAYER, self.player, "SPIKE")
                        self.input_mgr.trigger_rumble(0.7, 0.9, 0.25)
                    else:
                        self.player.trigger_action(PlayerAction.BUMP, 0.35)
                        self.ball.launch_arc(target_x, target_z, peak_height=3.4)
                        self.match_mgr.register_hit(Team.PLAYER, self.player, "BUMP")
                        self.input_mgr.trigger_rumble(0.4, 0.4, 0.15)

                    self.match_mgr.state = MatchState.IN_RALLY

            else:
                # Opponent strikes their serve toss
                self.ai_serve_timer -= dt
                if self.ai_serve_timer <= 0.0 and self.ball.y > 1.4:
                    self.opponent.trigger_action(PlayerAction.BUMP, 0.35)
                    srv_x = random.uniform(-3.0, 3.0)
                    srv_z = random.uniform(-7.5, -4.0)
                    self.ball.launch_arc(srv_x, srv_z, peak_height=3.5)
                    self.match_mgr.register_hit(Team.OPPONENT, self.opponent, "BUMP")
                    self.match_mgr.state = MatchState.IN_RALLY

        # 4. In Rally: Player Ball Interaction
        if self.match_mgr.state == MatchState.IN_RALLY:
            self.handle_player_actions(dt)

        # 5. Update Characters
        # Player movement
        move_x = self.input_mgr.move_x
        move_z = self.input_mgr.move_z
        
        # Player jump
        if self.input_mgr.jump_pressed:
            self.player.jump()

        # Update player position with court boundary clamping
        next_px = self.player.x + move_x * dt * 7.5
        next_pz = self.player.z + move_z * dt * 7.5
        clamped_px, clamped_pz = self.court.clamp_player_position(next_px, next_pz, Team.PLAYER)
        self.player.update(dt, move_x, move_z, look_target=(self.ball.x, self.ball.z))
        self.player.x = clamped_px
        self.player.z = clamped_pz

        # Update Opponent AI
        if self.match_mgr.state == MatchState.IN_RALLY:
            self.opponent_ai.update(dt, self.ball, self.court, self.match_mgr)
        else:
            self.opponent.update(dt, 0.0, 0.0, look_target=(self.ball.x, self.ball.z))

        # 6. Update Ball Physics
        if self.ball.in_air:
            self.ball.update(dt, self.audio_mgr)

        # 7. Update Dynamic Camera
        self.cam_ctrl.update(dt, self.player, self.ball)

    def handle_player_actions(self, dt):
        """Processes player bumps, sets, spikes, and dives when ball is near."""
        p = self.player
        b = self.ball
        horiz_dist = math.sqrt((b.x - p.x) ** 2 + (b.z - p.z) ** 2)
        touches = self.match_mgr.get_touches(Team.PLAYER)

        # 1. SPIKE (Mid-air smash)
        if not p.is_grounded and p.y > 0.5:
            if (self.input_mgr.spike_pressed or self.input_mgr.jump_pressed):
                if horiz_dist < 1.8 and abs(b.y - (p.y + 1.5)) < 1.3:
                    p.trigger_action(PlayerAction.SPIKE, 0.35)
                    # Hammer ball down into opponent's court at chosen aim position!
                    self.ball.launch_arc(self.aim_target_x, self.aim_target_z, is_spike=True, spike_speed=23.0)
                    self.match_mgr.register_hit(Team.PLAYER, p, "SPIKE")
                    self.input_mgr.trigger_rumble(0.8, 1.0, 0.3)
                    return

        # 2. BUMP / DIG (Receive)
        if p.is_grounded and self.input_mgr.bump_pressed:
            if horiz_dist < 1.8 and 0.2 < b.y < 2.5:
                p.trigger_action(PlayerAction.BUMP, 0.35)
                if touches == 0:
                    # Bump high into setter position near net
                    self.ball.launch_arc(0.0, -1.8, peak_height=4.2)
                    self.match_mgr.register_hit(Team.PLAYER, p, "BUMP")
                else:
                    # Return across net into opponent court
                    self.ball.launch_arc(self.aim_target_x, self.aim_target_z, peak_height=3.5)
                    self.match_mgr.register_hit(Team.PLAYER, p, "BUMP")
                self.input_mgr.trigger_rumble(0.4, 0.4, 0.15)
                return

        # 3. SET / PAS (Overhead pass)
        if p.is_grounded and self.input_mgr.set_pressed:
            if horiz_dist < 1.8 and 1.5 < b.y < 3.2:
                p.trigger_action(PlayerAction.SET, 0.35)
                # Floats ball high and soft near net for spike
                spike_spot_x = -1.5 if p.x < 0 else 1.5
                self.ball.launch_arc(spike_spot_x, -1.0, peak_height=3.8)
                self.match_mgr.register_hit(Team.PLAYER, p, "SET")
                self.input_mgr.trigger_rumble(0.3, 0.3, 0.12)
                return

        # 4. DIVE / SLIDE (Emergency save)
        if p.is_grounded and self.input_mgr.dive_pressed:
            p.trigger_action(PlayerAction.DIVE, 0.45)
            # Slide in movement direction
            if horiz_dist < 2.4 and b.y < 1.2:
                # Heroic save! Pops ball upward
                self.ball.launch_arc(0.0, -3.5, peak_height=3.5)
                self.match_mgr.register_hit(Team.PLAYER, p, "BUMP")
                self.input_mgr.trigger_rumble(0.6, 0.6, 0.2)

    def render(self):
        """Draws 3D scene and 2D arcade HUD overlay."""
        pr.begin_drawing()
        pr.clear_background(pr.Color(18, 20, 26, 255))

        # --- 3D Scene ---
        pr.begin_mode_3d(self.cam_ctrl.cam)
        
        # Court & Stadium
        self.court.draw()

        # Characters
        self.player.draw()
        self.opponent.draw()

        # Ball & Ground shadow & Landing predictor
        self.ball.draw()

        # Aiming Crosshair on opponent court (during serve or in rally)
        if self.match_mgr.state in [MatchState.SERVE_READY, MatchState.SERVE_TOSSED, MatchState.IN_RALLY]:
            ax, az = self.aim_target_x, self.aim_target_z
            # Crosshair ring
            pr.draw_circle_3d(pr.Vector3(ax, 0.03, az), 0.5, pr.Vector3(1, 0, 0), 90.0, pr.Color(255, 60, 60, 180))
            pr.draw_line_3d(pr.Vector3(ax - 0.7, 0.03, az), pr.Vector3(ax + 0.7, 0.03, az), pr.Color(255, 255, 255, 200))
            pr.draw_line_3d(pr.Vector3(ax, 0.03, az - 0.7), pr.Vector3(ax, 0.03, az + 0.7), pr.Color(255, 255, 255, 200))

        pr.end_mode_3d()

        # --- 2D HUD & Overlay ---
        self.ui.draw_hud(self.match_mgr, self.input_mgr, self.cam_ctrl, self.ai_diff)
        self.ui.draw_serve_prompt(self.match_mgr, self.input_mgr)
        self.ui.draw_point_banner(self.match_mgr)
        self.ui.draw_match_over(self.match_mgr, self.input_mgr)

        if self.is_paused:
            self.ui.draw_pause_menu(self.input_mgr)

        pr.end_drawing()

    def cleanup(self):
        self.audio_mgr.close()
        pr.close_window()
