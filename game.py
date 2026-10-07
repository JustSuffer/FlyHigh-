"""
FlyHigh! - 3D Volleyball Game
Main Game System & Loop
Integrates 3v3 Team Volleyball, Title & Settings Menus, Court, Ball, Characters, AI, Camera, Audio, Rules, and UI.

Features:
- Ball strictly locked in server's hands during SERVE_READY (never drops to the floor before toss)
- Toss mechanic: Toss high with [SPACE] or [L-CLICK], then jump and time your hit
- NBA 2K-Style Shot Meter with Green / Yellow / Red timing windows:
  - Green (Perfect): [L-CLICK + E] produces a knuckling Float Serve; [L-CLICK] produces a 26 m/s line-drive Power Spike!
  - Yellow (Good): Standard speed (18.5 m/s) accurate hit.
  - Red (Off-Time): Mismit pop-up drifting off target.
- Full Volleyball Control Scheme:
  - In Air: [L-CLICK] Spike | [L-CLICK + E] Float Serve | [E] Dump | [R-CLICK] Air Pass | [L-CTRL + L-CLICK] Air Bailout
  - Grounded: [R-CLICK] Set/Pass | [R-CLICK + E] Setter Dump | [L-CTRL] Receive/Dig | [L-CTRL + R-CLICK] Roll Dig (5s CD)
- Full Settings Menu (Volume, Mute, Fullscreen, Resolution, Camera)
- 100% English & authentic volleyball terminology
- Clean player spacing in 3v3 formations (no overlapping)
"""
import pyray as pr
import math
import random
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_FPS, GAME_TITLE,
    Team, MatchState, PlayerAction, AIDifficulty, TimingRating,
    HALF_WIDTH, HALF_LENGTH, NET_HEIGHT
)
from audio_manager import AudioManager
from input_manager import InputManager
from court import Court
from ball import Ball
from character import Character
from ai_controller import TeamAIController
from camera_controller import CameraController
from match_manager import MatchManager
from ui_renderer import UIRenderer, COLOR_CYAN_ACCENT, COLOR_GOLD_ACCENT, COLOR_CORAL_ACCENT, COLOR_GREEN_PERFECT

class VolleyballGame:
    def __init__(self):
        pr.init_window(SCREEN_WIDTH, SCREEN_HEIGHT, GAME_TITLE)
        pr.set_target_fps(TARGET_FPS)
        # Disable ESC key from closing window automatically
        pr.set_exit_key(0)

        # Core subsystems
        self.audio_mgr = AudioManager()
        self.input_mgr = InputManager()
        self.court = Court()
        self.ball = Ball()
        self.cam_ctrl = CameraController()
        self.match_mgr = MatchManager(audio_mgr=self.audio_mgr, points_to_win=11)
        self.ui = UIRenderer()
        self.ai_diff = AIDifficulty.MEDIUM

        # --- 3v3 ROSTERS ---
        # 1. Team Player (Near Court, Z < 0)
        # Captain #5 (User Player)
        self.player = Character(x=0.0, z=-8.2, team=Team.PLAYER, jersey_num=5, name="CAPTAIN", is_ai=False)
        # Teammate 1: Setter #2
        self.teammate_1 = Character(x=-2.6, z=-4.5, team=Team.PLAYER, jersey_num=2, name="SETTER", is_ai=True)
        # Teammate 2: Wing / Blocker #4
        self.teammate_2 = Character(x=2.6, z=-4.5, team=Team.PLAYER, jersey_num=4, name="WING", is_ai=True)
        
        self.team_player = [self.player, self.teammate_1, self.teammate_2]
        self.player_ai_mgr = TeamAIController(self.team_player, team=Team.PLAYER, difficulty=self.ai_diff, human_player=self.player)

        # 2. Team Opponent (Far Court, Z > 0)
        # Opponent 1: Rival Captain #1
        self.opponent_1 = Character(x=-2.4, z=4.5, team=Team.OPPONENT, jersey_num=1, name="RIVAL", is_ai=True)
        # Opponent 2: Setter #3
        self.opponent_2 = Character(x=2.4, z=4.5, team=Team.OPPONENT, jersey_num=3, name="OPP_SETTER", is_ai=True)
        # Opponent 3: Libero / Server #6
        self.opponent_3 = Character(x=0.0, z=8.2, team=Team.OPPONENT, jersey_num=6, name="LIBERO", is_ai=True)

        self.team_opponent = [self.opponent_1, self.opponent_2, self.opponent_3]
        self.opponent_ai_mgr = TeamAIController(self.team_opponent, team=Team.OPPONENT, difficulty=self.ai_diff)

        # Aim Target on court floor (Mouse raycast or stick)
        self.aim_target_x = 0.0
        self.aim_target_z = 5.5

        # Timing shot meter cache
        self.shot_meter_timing = 0.0
        self.shot_meter_visible = False

        # Timers & Camera Orbit in Menu
        self.ai_serve_timer = 0.0
        self.menu_cam_angle = 0.0
        self.is_paused = False

        # Start in TITLE_SCREEN
        self.match_mgr.state = MatchState.TITLE_SCREEN

    def setup_serve(self):
        """Cleanly positions 3v3 teams with zero overlap and locks ball in server hands."""
        if self.match_mgr.serving_team == Team.PLAYER:
            # User serves at baseline (0.0, -8.2)
            self.player.reset_position(0.0, -8.2)
            self.teammate_1.reset_position(-2.6, -4.5)
            self.teammate_2.reset_position(2.6, -4.5)

            self.opponent_1.reset_position(-2.4, 4.5)
            self.opponent_2.reset_position(2.4, 4.5)
            self.opponent_3.reset_position(0.0, 7.5)

            # Ball strictly attached to player's hands
            self.ball.reset(x=self.player.x, y=1.35, z=self.player.z + 0.65, team=Team.PLAYER)
            self.ball.in_air = False
        else:
            # Opponent Libero (#6) serves at baseline (0.0, 8.2)
            self.opponent_3.reset_position(0.0, 8.2)
            self.opponent_1.reset_position(-2.4, 4.5)
            self.opponent_2.reset_position(2.4, 4.5)

            self.player.reset_position(0.0, -7.0)
            self.teammate_1.reset_position(-2.6, -4.5)
            self.teammate_2.reset_position(2.6, -4.5)

            # Ball strictly attached to opponent's hands
            self.ball.reset(x=self.opponent_3.x, y=1.35, z=self.opponent_3.z - 0.65, team=Team.OPPONENT)
            self.ball.in_air = False
            self.ai_serve_timer = random.uniform(1.2, 1.8)

    def run(self):
        """Main game loop."""
        while not pr.window_should_close():
            dt = pr.get_frame_time()
            if dt > 0.05:
                dt = 0.05

            self.handle_input()
            if not self.is_paused:
                self.update(dt)

            self.render()

        self.cleanup()

    def handle_input(self):
        self.input_mgr.update()

        # Title / Settings Menu Navigation
        if self.match_mgr.state == MatchState.TITLE_SCREEN:
            action, new_diff = self.ui.update_menu(self.input_mgr, self.audio_mgr, self.ai_diff, self.cam_ctrl)
            if new_diff != self.ai_diff:
                self.ai_diff = new_diff
                self.player_ai_mgr.set_difficulty(new_diff)
                self.opponent_ai_mgr.set_difficulty(new_diff)

            if action == "PLAY":
                self.audio_mgr.play("whistle")
                self.match_mgr.reset_match()
                self.setup_serve()
            elif action == "QUIT":
                pr.close_window()
                return
            return

        # In-Game Pause Toggle via ESC or Gamepad Start
        if self.input_mgr.pause_pressed:
            if self.match_mgr.state != MatchState.MATCH_OVER:
                if self.ui.show_settings_modal:
                    self.ui.show_settings_modal = False
                else:
                    self.is_paused = not self.is_paused

        # Pause Menu actions
        if self.is_paused:
            if self.ui.show_settings_modal:
                self.ui._update_settings_menu(self.input_mgr, self.audio_mgr, self.ai_diff, self.cam_ctrl)
                return

            if pr.is_key_pressed(pr.KEY_S):
                self.ui.show_settings_modal = True
                self.ui.settings_index = 0
                self.audio_mgr.play("hit_bump")
                return
            if pr.is_key_pressed(pr.KEY_Q):
                self.is_paused = False
                self.match_mgr.state = MatchState.TITLE_SCREEN
                return
            if pr.is_key_pressed(pr.KEY_M):
                self.audio_mgr.toggle_mute()
            if self.input_mgr.camera_pressed:
                self.cam_ctrl.cycle_mode()
            return

        # Camera cycle in gameplay
        if self.input_mgr.camera_pressed:
            self.cam_ctrl.cycle_mode()

        # Rematch if Match Over
        if self.match_mgr.state == MatchState.MATCH_OVER:
            if self.input_mgr.jump_pressed or self.input_mgr.select_pressed or pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                self.match_mgr.reset_match()
                self.setup_serve()
            elif self.input_mgr.pause_pressed:
                self.match_mgr.state = MatchState.TITLE_SCREEN

    def update(self, dt):
        """Updates game state, cursor raycasting, 3v3 characters, ball physics, and rules."""
        if self.match_mgr.state == MatchState.TITLE_SCREEN:
            # Orbiting camera in title menu
            self.menu_cam_angle += dt * 0.25
            cam_dist = 16.0
            cx = cam_dist * math.sin(self.menu_cam_angle)
            cz = cam_dist * math.cos(self.menu_cam_angle)
            self.cam_ctrl.cam.position = pr.Vector3(cx, 6.8, cz)
            self.cam_ctrl.cam.target = pr.Vector3(0.0, 1.8, 0.0)

            for c in self.team_player + self.team_opponent:
                c.update(dt, 0.0, 0.0, look_target=(0.0, 0.0))
            return

        # 1. Update Match State transitions
        prev_state = self.match_mgr.state
        self.match_mgr.update(dt, self.ball, self.court)

        if prev_state == MatchState.POINT_SCORED and self.match_mgr.state == MatchState.SERVE_READY:
            self.setup_serve()

        # 2. CURSOR-BASED AIMING: Mouse Raycast onto Court Floor (Y = 0)
        mouse_pos = pr.get_mouse_position()
        ray = pr.get_screen_to_world_ray(mouse_pos, self.cam_ctrl.cam)
        
        if ray.direction.y < -0.0001:
            t = -ray.position.y / ray.direction.y
            hit_x = ray.position.x + t * ray.direction.x
            hit_z = ray.position.z + t * ray.direction.z
            self.aim_target_x = max(-HALF_WIDTH - 0.5, min(HALF_WIDTH + 0.5, hit_x))
            self.aim_target_z = max(-HALF_LENGTH - 1.5, min(HALF_LENGTH + 1.5, hit_z))
        elif self.input_mgr.active_device == "GAMEPAD":
            if abs(self.input_mgr.aim_x) > 0.1 or abs(self.input_mgr.aim_z) > 0.1:
                self.aim_target_x += self.input_mgr.aim_x * dt * 9.0
                self.aim_target_z += self.input_mgr.aim_z * dt * 9.0
                self.aim_target_x = max(-HALF_WIDTH + 0.4, min(HALF_WIDTH - 0.4, self.aim_target_x))
                self.aim_target_z = max(-HALF_LENGTH + 0.4, min(HALF_LENGTH - 0.4, self.aim_target_z))

        # 3. CALCULATE NBA 2K-STYLE SHOT METER TIMING
        # Optimal hit point is when the ball is at apex relative to player reach (player.y + 2.1)
        ideal_reach_y = self.player.y + 2.1
        diff_y = abs(self.ball.y - ideal_reach_y)
        self.shot_meter_timing = max(0.0, min(1.0, 1.0 - (diff_y / 1.35)))
        self.shot_meter_visible = (
            (not self.player.is_grounded and self.ball.in_air and self.ball.y > 1.2) or
            (self.match_mgr.state == MatchState.SERVE_TOSSED and self.match_mgr.serving_team == Team.PLAYER)
        )

        # 4. SERVE MECHANICS
        if self.match_mgr.state == MatchState.SERVE_READY:
            if self.match_mgr.serving_team == Team.PLAYER:
                # Keep ball firmly held in server hands until user deliberately tosses
                self.ball.x = self.player.x
                self.ball.y = self.player.y + 1.35
                self.ball.z = self.player.z + 0.65
                self.ball.vx = 0.0
                self.ball.vy = 0.0
                self.ball.vz = 0.0
                self.ball.in_air = False

                # EXCLUSIVE TOSS TRIGGER: Right Click (or Gamepad Y). SPACE or Left Click will NEVER toss!
                toss_triggered = (
                    pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_RIGHT) or
                    (pr.is_gamepad_available(self.input_mgr.gamepad_id) and
                     pr.is_gamepad_button_pressed(self.input_mgr.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_FACE_UP))
                )
                if toss_triggered:
                    self.match_mgr.state = MatchState.SERVE_TOSSED
                    # Toss ball high into the air
                    self.ball.launch_arc(self.player.x, self.player.z + 0.75, peak_height=4.2)
                    self.audio_mgr.play("whistle")
                    self.ui.trigger_arcade_popup("BALL TOSSED! JUMP & HIT!", COLOR_GOLD_ACCENT, 1.0)
            else:
                # Opponent serving: lock in opponent 3 hands
                srv = self.opponent_3
                self.ball.x = srv.x
                self.ball.y = srv.y + 1.35
                self.ball.z = srv.z - 0.65
                self.ball.vx = 0.0
                self.ball.vy = 0.0
                self.ball.vz = 0.0
                self.ball.in_air = False

                self.ai_serve_timer -= dt
                if self.ai_serve_timer <= 0.0:
                    self.match_mgr.state = MatchState.SERVE_TOSSED
                    self.ball.launch_arc(srv.x, srv.z - 0.75, peak_height=4.2)
                    self.audio_mgr.play("whistle")
                    self.ai_serve_timer = 0.55

        elif self.match_mgr.state == MatchState.SERVE_TOSSED:
            if self.match_mgr.serving_team == Team.PLAYER:
                # If player tossed but missed the hit and ball hits the floor: retoss!
                if self.ball.has_bounced or (self.ball.y <= BALL_RADIUS + 0.06 and self.ball.vy <= 0):
                    self.setup_serve()
                    self.ui.trigger_arcade_popup("MISSED TOSS! RIGHT-CLICK TO RETOSS", COLOR_CORAL_ACCENT, 1.2)
                    return

                dist_ball = math.sqrt((self.ball.x - self.player.x)**2 + (self.ball.z - self.player.z)**2)
                
                # Player must jump into air to strike jump serve / float serve!
                hit_attempt = (
                    self.input_mgr.is_float_serve_triggered or
                    self.input_mgr.lmb_pressed or
                    self.input_mgr.spike_pressed or
                    self.input_mgr.e_pressed or
                    self.input_mgr.rmb_pressed
                )

                if hit_attempt and dist_ball < 2.2 and self.ball.y > 1.2:
                    target_x = self.aim_target_x
                    target_z = max(2.5, self.aim_target_z)  # Target opponent court
                    rating = self._evaluate_timing(self.shot_meter_timing)
                    self.ui.trigger_shot_feedback(rating)

                    # 1. FLOAT SERVE: [L-CLICK + E]
                    if self.input_mgr.is_float_serve_triggered or (self.input_mgr.e_pressed and not self.player.is_grounded):
                        if rating == TimingRating.GREEN:
                            # Knuckleball Float Serve! Erratic drift and steep drop!
                            self.player.trigger_action(PlayerAction.SPIKE, 0.35)
                            self.ball.launch_arc(target_x, target_z, is_float=True, peak_height=2.75)
                            self.match_mgr.register_hit(Team.PLAYER, self.player, "SPIKE")
                            self.ui.trigger_arcade_popup("FLOAT SERVE!", COLOR_CYAN_ACCENT)
                            self.input_mgr.trigger_rumble(0.6, 0.8, 0.2)
                        elif rating == TimingRating.YELLOW:
                            # Standard serve (no float)
                            self.player.trigger_action(PlayerAction.SPIKE, 0.35)
                            self.ball.launch_arc(target_x, target_z, peak_height=3.4)
                            self.match_mgr.register_hit(Team.PLAYER, self.player, "SPIKE")
                            self.ui.trigger_arcade_popup("GOOD SERVE", COLOR_GOLD_ACCENT)
                            self.input_mgr.trigger_rumble(0.4, 0.4, 0.15)
                        else:
                            # Red: Mismit, drifts off
                            self.player.trigger_action(PlayerAction.BUMP, 0.35)
                            rx = target_x + random.uniform(-1.8, 1.8)
                            rz = target_z + random.uniform(-1.8, 1.8)
                            self.ball.launch_arc(rx, rz, peak_height=4.8)
                            self.match_mgr.register_hit(Team.PLAYER, self.player, "BUMP")
                            self.ui.trigger_arcade_popup("MISTIMED SERVE!", COLOR_CORAL_ACCENT)

                        self.match_mgr.state = MatchState.IN_RALLY

                    # 2. POWER JUMP SERVE: [L-CLICK] or [SPACE in air]
                    elif self.input_mgr.lmb_pressed or self.input_mgr.spike_pressed:
                        self.player.trigger_action(PlayerAction.SPIKE, 0.35)
                        if rating == TimingRating.GREEN:
                            # Crushing Jump Serve line drive (26 m/s)!
                            self.ball.launch_arc(target_x, target_z, is_spike=True, spike_speed=26.0)
                            self.ui.trigger_arcade_popup("ACE JUMP SERVE!!", COLOR_CORAL_ACCENT)
                            self.input_mgr.trigger_rumble(0.9, 1.0, 0.3)
                        elif rating == TimingRating.YELLOW:
                            # Solid Jump Serve (18.5 m/s)
                            self.ball.launch_arc(target_x, target_z, is_spike=True, spike_speed=18.5)
                            self.ui.trigger_arcade_popup("GOOD SERVE", COLOR_GOLD_ACCENT)
                            self.input_mgr.trigger_rumble(0.5, 0.6, 0.2)
                        else:
                            # Mismit
                            rx = target_x + random.uniform(-1.6, 1.6)
                            rz = target_z + random.uniform(-1.6, 1.6)
                            self.ball.launch_arc(rx, rz, peak_height=4.6)
                            self.ui.trigger_arcade_popup("OFF-TIME SERVE", COLOR_CORAL_ACCENT)

                        self.match_mgr.register_hit(Team.PLAYER, self.player, "SPIKE")
                        self.match_mgr.state = MatchState.IN_RALLY

                    # 3. DUMP SERVE: [E]
                    elif self.input_mgr.e_pressed:
                        self.player.trigger_action(PlayerAction.DUMP, 0.35)
                        self.ball.launch_arc(target_x, 2.0, peak_height=2.7)
                        self.match_mgr.register_hit(Team.PLAYER, self.player, "SET")
                        self.ui.trigger_arcade_popup("DUMP SERVE!", COLOR_GOLD_ACCENT)
                        self.match_mgr.state = MatchState.IN_RALLY

                    # 4. PASS SERVE: [R-CLICK]
                    elif self.input_mgr.rmb_pressed:
                        self.player.trigger_action(PlayerAction.SET, 0.35)
                        self.ball.launch_arc(target_x, target_z, peak_height=3.8)
                        self.match_mgr.register_hit(Team.PLAYER, self.player, "SET")
                        self.ui.trigger_arcade_popup("PASS SERVE", COLOR_CYAN_ACCENT)
                        self.match_mgr.state = MatchState.IN_RALLY

            else:
                # Opponent AI strikes serve
                self.ai_serve_timer -= dt
                if self.ai_serve_timer <= 0.0:
                    self.opponent_3.trigger_action(PlayerAction.SPIKE, 0.35)
                    srv_x = random.uniform(-3.0, 3.0)
                    srv_z = random.uniform(-7.5, -4.0)
                    self.ball.launch_arc(srv_x, srv_z, peak_height=3.5)
                    self.match_mgr.register_hit(Team.OPPONENT, self.opponent_3, "BUMP")
                    self.match_mgr.state = MatchState.IN_RALLY

        # 5. IN RALLY: Complete Volleyball Control Pipeline
        if self.match_mgr.state == MatchState.IN_RALLY:
            self.handle_rally_actions(dt)

        # 6. Human Player Movement
        move_x = self.input_mgr.move_x
        move_z = self.input_mgr.move_z

        if self.input_mgr.jump_pressed:
            self.player.jump()

        next_px = self.player.x + move_x * dt * 7.5
        next_pz = self.player.z + move_z * dt * 7.5
        clamped_px, clamped_pz = self.court.clamp_player_position(next_px, next_pz, Team.PLAYER)
        self.player.update(dt, move_x, move_z, look_target=(self.aim_target_x, self.aim_target_z))
        self.player.x = clamped_px
        self.player.z = clamped_pz

        # 7. Update AI Controllers
        if self.match_mgr.state == MatchState.IN_RALLY:
            self.player_ai_mgr.update(dt, self.ball, self.court, self.match_mgr)
            self.opponent_ai_mgr.update(dt, self.ball, self.court, self.match_mgr)
        else:
            for c in self.team_player[1:] + self.team_opponent:
                c.update(dt, 0.0, 0.0, look_target=(self.ball.x, self.ball.z))

        # 8. Update Ball Physics
        if self.ball.in_air:
            self.ball.update(dt, self.audio_mgr)

        # 9. Update Camera
        self.cam_ctrl.update(dt, self.player, self.ball)

    def _evaluate_timing(self, timing_ratio):
        if timing_ratio >= 0.82:
            return TimingRating.GREEN
        elif timing_ratio >= 0.50:
            return TimingRating.YELLOW
        else:
            return TimingRating.RED

    def handle_rally_actions(self, dt):
        """Processes precise user actions in rally (Spike, Float, Dump, Bailout, Dig, Set, Roll Dig)."""
        p = self.player
        b = self.ball
        horiz_dist = math.sqrt((b.x - p.x) ** 2 + (b.z - p.z) ** 2)
        target_x = self.aim_target_x
        target_z = self.aim_target_z

        # ---------------- IN-AIR ACTIONS (JUMPING) ----------------
        if not p.is_grounded and p.y > 0.35:
            # A. Emergency Air Bailout: [L-CTRL + L-CLICK]
            if self.input_mgr.is_air_bailout_triggered:
                if horiz_dist < 2.8 and b.y < p.y + 2.5:
                    p.trigger_action(PlayerAction.AIR_BAILOUT, 0.40)
                    self.ball.launch_arc(target_x, max(2.5, target_z), peak_height=3.6)
                    self.match_mgr.register_hit(Team.PLAYER, p, "BUMP")
                    self.ui.trigger_arcade_popup("EMERGENCY TAP!", COLOR_CORAL_ACCENT)
                    self.input_mgr.trigger_rumble(0.5, 0.5, 0.18)
                    return

            # B. In-Air Dump: [E] (Soft feather over block)
            if self.input_mgr.e_pressed:
                if horiz_dist < 2.0 and abs(b.y - (p.y + 1.5)) < 1.5:
                    p.trigger_action(PlayerAction.DUMP, 0.35)
                    self.ball.launch_arc(target_x, max(1.5, target_z), peak_height=2.7)
                    self.match_mgr.register_hit(Team.PLAYER, p, "SET")
                    self.ui.trigger_arcade_popup("DUMP OVER BLOCK!", COLOR_GOLD_ACCENT)
                    self.input_mgr.trigger_rumble(0.3, 0.3, 0.12)
                    return

            # C. In-Air Pass / Set: [R-CLICK]
            if self.input_mgr.rmb_pressed:
                if horiz_dist < 2.0 and abs(b.y - (p.y + 1.5)) < 1.5:
                    p.trigger_action(PlayerAction.SET, 0.35)
                    self.ball.launch_arc(target_x, target_z, peak_height=3.8)
                    self.match_mgr.register_hit(Team.PLAYER, p, "SET")
                    self.ui.trigger_arcade_popup("AIR PASS!", COLOR_CYAN_ACCENT)
                    self.input_mgr.trigger_rumble(0.3, 0.3, 0.12)
                    return

            # D. Power Spike Attack: [L-CLICK] or [SPACE]
            if self.input_mgr.lmb_pressed or self.input_mgr.spike_pressed:
                if horiz_dist < 2.1 and abs(b.y - (p.y + 1.5)) < 1.5:
                    rating = self._evaluate_timing(self.shot_meter_timing)
                    self.ui.trigger_shot_feedback(rating)
                    p.trigger_action(PlayerAction.SPIKE, 0.35)

                    if rating == TimingRating.GREEN:
                        # 26 m/s Crushing Power Spike!
                        self.ball.launch_arc(target_x, target_z, is_spike=True, spike_speed=26.0)
                        self.ui.trigger_arcade_popup("BOOM SPIKE!!", COLOR_CORAL_ACCENT)
                        self.input_mgr.trigger_rumble(0.9, 1.0, 0.3)
                    elif rating == TimingRating.YELLOW:
                        # Solid 18.5 m/s Spike
                        self.ball.launch_arc(target_x, target_z, is_spike=True, spike_speed=18.5)
                        self.ui.trigger_arcade_popup("SOLID SPIKE!", COLOR_GOLD_ACCENT)
                        self.input_mgr.trigger_rumble(0.5, 0.6, 0.2)
                    else:
                        # Mismit
                        rx = target_x + random.uniform(-1.8, 1.8)
                        rz = target_z + random.uniform(-1.8, 1.8)
                        self.ball.launch_arc(rx, rz, peak_height=4.6)
                        self.ui.trigger_arcade_popup("OFF-TIME SPIKE", COLOR_CORAL_ACCENT)
                        self.input_mgr.trigger_rumble(0.3, 0.3, 0.1)

                    self.match_mgr.register_hit(Team.PLAYER, p, "SPIKE")
                    return

        # ---------------- GROUNDED ACTIONS ----------------
        if p.is_grounded:
            # A. Roll Dig: [L-CTRL + R-CLICK] (5-second cooldown)
            if self.input_mgr.is_roll_dig_triggered:
                if p.roll_dig_cooldown > 0.0:
                    self.ui.trigger_arcade_popup(f"ROLL DIG COOLDOWN ({p.roll_dig_cooldown:.1f}s)", COLOR_CORAL_ACCENT, 0.5)
                    return
                else:
                    # Check reach to ball or predicted landing ring
                    dist_to_landing = math.sqrt((self.ball.predict_x - p.x)**2 + (self.ball.predict_z - p.z)**2)
                    if horiz_dist < 3.8 or dist_to_landing < 3.4:
                        p.trigger_action(PlayerAction.ROLL_DIG, 0.60)
                        self.ball.launch_arc(target_x, target_z, peak_height=4.4)
                        self.match_mgr.register_hit(Team.PLAYER, p, "BUMP")
                        self.ui.trigger_arcade_popup("HEROIC ROLL DIG!!", COLOR_GOLD_ACCENT)
                        self.audio_mgr.play("floor_bounce")
                        self.audio_mgr.play("hit_bump")
                        self.input_mgr.trigger_rumble(0.7, 0.9, 0.25)
                        return

            # B. Setter Dump: [R-CLICK + E]
            if self.input_mgr.is_setter_dump_triggered:
                if horiz_dist < 2.0 and 1.1 < b.y < 3.2:
                    p.trigger_action(PlayerAction.SETTER_DUMP, 0.35)
                    self.ball.launch_arc(target_x, max(1.6, target_z), peak_height=2.8)
                    self.match_mgr.register_hit(Team.PLAYER, p, "SET")
                    self.ui.trigger_arcade_popup("SETTER DUMP!", COLOR_GOLD_ACCENT)
                    self.input_mgr.trigger_rumble(0.4, 0.4, 0.15)
                    return

            # C. Ground Receive / Dig: [L-CTRL] or [bump_pressed]
            if self.input_mgr.ctrl_down or self.input_mgr.bump_pressed:
                if horiz_dist < 2.0 and 0.2 < b.y < 2.6:
                    p.trigger_action(PlayerAction.BUMP, 0.35)
                    if target_z > 0.0:
                        self.ball.launch_arc(target_x, target_z, peak_height=3.5)
                        self.ui.trigger_arcade_popup("OVER THE NET!", COLOR_CYAN_ACCENT)
                    else:
                        self.ball.launch_arc(target_x, target_z, peak_height=4.2)
                        self.ui.trigger_arcade_popup("NICE DIG!", COLOR_CYAN_ACCENT)

                    self.match_mgr.register_hit(Team.PLAYER, p, "BUMP")
                    self.input_mgr.trigger_rumble(0.4, 0.4, 0.15)
                    return

            # D. Ground Pass / Set: [R-CLICK] (without ctrl and without e)
            if self.input_mgr.rmb_pressed and not self.input_mgr.ctrl_down:
                if horiz_dist < 2.0 and 1.3 < b.y < 3.2:
                    p.trigger_action(PlayerAction.SET, 0.35)
                    self.ball.launch_arc(target_x, target_z, peak_height=3.9)
                    self.match_mgr.register_hit(Team.PLAYER, p, "SET")
                    self.ui.trigger_arcade_popup("PERFECT SET!", COLOR_CYAN_ACCENT)
                    self.input_mgr.trigger_rumble(0.3, 0.3, 0.12)
                    return

    def render(self):
        """Draws 3D stadium, 3v3 characters, ball, reticle, and 2D modern arcade overlays."""
        pr.begin_drawing()
        pr.clear_background(pr.Color(16, 18, 26, 255))

        # --- 3D Scene ---
        pr.begin_mode_3d(self.cam_ctrl.cam)

        # Court & Stadium
        self.court.draw()

        # Render 3v3 Characters
        for char in self.team_player:
            char.draw()
        for char in self.team_opponent:
            char.draw()

        # Ball, ground shadow & landing ring
        self.ball.draw()

        # CURSOR AIMING RETICLE on Court Floor
        if self.match_mgr.state in [MatchState.SERVE_READY, MatchState.SERVE_TOSSED, MatchState.IN_RALLY]:
            ax, az = self.aim_target_x, self.aim_target_z
            pulse_rad = 0.5 + 0.05 * math.sin(pr.get_time() * 8.0)
            pr.draw_circle_3d(pr.Vector3(ax, 0.03, az), pulse_rad, pr.Vector3(1, 0, 0), 90.0, pr.Color(255, 60, 60, 200))
            pr.draw_circle_3d(pr.Vector3(ax, 0.035, az), 0.12, pr.Vector3(1, 0, 0), 90.0, pr.Color(255, 220, 50, 240))
            pr.draw_line_3d(pr.Vector3(ax - 0.75, 0.03, az), pr.Vector3(ax + 0.75, 0.03, az), pr.Color(255, 255, 255, 220))
            pr.draw_line_3d(pr.Vector3(ax, 0.03, az - 0.75), pr.Vector3(ax, 0.03, az + 0.75), pr.Color(255, 255, 255, 220))
            pr.draw_line_3d(pr.Vector3(self.player.x, 0.1, self.player.z), pr.Vector3(ax, 0.03, az), pr.Color(255, 220, 50, 100))

        pr.end_mode_3d()

        # --- 2D UI & Overlays ---
        if self.match_mgr.state == MatchState.TITLE_SCREEN:
            self.ui.draw_title_screen(self.ai_diff, self.audio_mgr, self.input_mgr, self.cam_ctrl)
        else:
            self.ui.draw_hud(self.match_mgr, self.input_mgr, self.cam_ctrl, self.ai_diff, self.player)
            self.ui.draw_serve_prompt(self.match_mgr, self.input_mgr)
            self.ui.draw_shot_meter(self.shot_meter_timing, self.shot_meter_visible)
            self.ui.draw_point_banner(self.match_mgr)
            self.ui.draw_match_over(self.match_mgr, self.input_mgr)

            if self.is_paused:
                self.ui.draw_pause_menu(self.input_mgr, self.audio_mgr, self.cam_ctrl)

        pr.end_drawing()

    def cleanup(self):
        self.ui.cleanup()
        self.audio_mgr.close()
        pr.close_window()
