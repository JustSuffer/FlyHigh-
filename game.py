"""
FlyHigh! - 3D Volleyball Game
Main Game System & Loop
Integrates 3v3 Team Volleyball, Title Menu, Court, Ball, Characters, AI, Camera, Audio, Rules, and UI.
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
from ai_controller import TeamAIController
from camera_controller import CameraController
from match_manager import MatchManager
from ui_renderer import UIRenderer, COLOR_CYAN_ACCENT, COLOR_GOLD_ACCENT, COLOR_CORAL_ACCENT

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
        self.ai_diff = AIDifficulty.MEDIUM

        # --- 3v3 ROSTERS ---
        # 1. Team Player (Near Court, Z < 0)
        # Player 1 (User / Captain #5 - Matching reference photo: silver/white spiky hair)
        self.player = Character(x=0.0, z=-6.8, team=Team.PLAYER, jersey_num=5, name="CAPTAIN", is_ai=False)
        # Teammate 1 (Setter #2)
        self.teammate_1 = Character(x=-2.2, z=-2.5, team=Team.PLAYER, jersey_num=2, name="SETTER", is_ai=True)
        # Teammate 2 (Wing / Blocker #4)
        self.teammate_2 = Character(x=2.2, z=-2.5, team=Team.PLAYER, jersey_num=4, name="WING", is_ai=True)
        
        self.team_player = [self.player, self.teammate_1, self.teammate_2]
        self.player_ai_mgr = TeamAIController(self.team_player, team=Team.PLAYER, difficulty=self.ai_diff, human_player=self.player)

        # 2. Team Opponent (Far Court, Z > 0)
        # Opponent 1 (Captain / Spiker #1)
        self.opponent_1 = Character(x=-2.0, z=2.5, team=Team.OPPONENT, jersey_num=1, name="RIVAL", is_ai=True)
        # Opponent 2 (Setter #3)
        self.opponent_2 = Character(x=2.0, z=2.5, team=Team.OPPONENT, jersey_num=3, name="OPP_SETTER", is_ai=True)
        # Opponent 3 (Defender #6)
        self.opponent_3 = Character(x=0.0, z=6.8, team=Team.OPPONENT, jersey_num=6, name="LIBERO", is_ai=True)

        self.team_opponent = [self.opponent_1, self.opponent_2, self.opponent_3]
        self.opponent_ai_mgr = TeamAIController(self.team_opponent, team=Team.OPPONENT, difficulty=self.ai_diff)

        # Aim Target on opponent court
        self.aim_target_x = 0.0
        self.aim_target_z = 6.0

        # Timers & Camera Orbit in Menu
        self.ai_serve_timer = 0.0
        self.menu_cam_angle = 0.0
        self.is_paused = False

        # Start in TITLE_SCREEN by default
        self.match_mgr.state = MatchState.TITLE_SCREEN

    def setup_serve(self):
        """Positions 3v3 teams and ball for serve phase."""
        if self.match_mgr.serving_team == Team.PLAYER:
            # User serves behind baseline
            self.player.reset_position(0.0, -9.8)
            self.teammate_1.reset_position(-2.2, -2.5)
            self.teammate_2.reset_position(2.2, -2.5)

            self.opponent_1.reset_position(-2.0, 2.5)
            self.opponent_2.reset_position(2.0, 2.5)
            self.opponent_3.reset_position(0.0, 6.8)

            self.ball.reset(x=self.player.x, y=1.4, z=self.player.z + 0.6, team=Team.PLAYER)
        else:
            # Opponent 3 (Defender) serves behind baseline
            self.opponent_3.reset_position(0.0, 9.8)
            self.opponent_1.reset_position(-2.0, 2.5)
            self.opponent_2.reset_position(2.0, 2.5)

            self.player.reset_position(0.0, -6.8)
            self.teammate_1.reset_position(-2.2, -2.5)
            self.teammate_2.reset_position(2.2, -2.5)

            self.ball.reset(x=self.opponent_3.x, y=1.4, z=self.opponent_3.z - 0.6, team=Team.OPPONENT)
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

        # Handle Menu in Title Screen
        if self.match_mgr.state == MatchState.TITLE_SCREEN:
            action, new_diff = self.ui.update_menu(self.input_mgr, self.audio_mgr, self.ai_diff)
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

        # In-game Pause
        if self.input_mgr.pause_pressed:
            if self.match_mgr.state != MatchState.MATCH_OVER:
                self.is_paused = not self.is_paused

        # Cycle Camera
        if self.input_mgr.camera_pressed and not self.is_paused:
            self.cam_ctrl.cycle_mode()

        # Rematch if Match Over
        if self.match_mgr.state == MatchState.MATCH_OVER:
            if self.input_mgr.jump_pressed or self.input_mgr.select_pressed:
                self.match_mgr.reset_match()
                self.setup_serve()
            elif self.input_mgr.pause_pressed:
                self.match_mgr.state = MatchState.TITLE_SCREEN

    def update(self, dt):
        """Updates game state, 3v3 characters, ball physics, and rules."""
        if self.match_mgr.state == MatchState.TITLE_SCREEN:
            # Cinematic orbiting camera in title menu
            self.menu_cam_angle += dt * 0.28
            cam_dist = 14.5
            cx = cam_dist * math.sin(self.menu_cam_angle)
            cz = cam_dist * math.cos(self.menu_cam_angle)
            self.cam_ctrl.cam.position = pr.Vector3(cx, 6.5, cz)
            self.cam_ctrl.cam.target = pr.Vector3(0.0, 1.8, 0.0)

            # Characters in idle breathing animation
            for c in self.team_player + self.team_opponent:
                c.update(dt, 0.0, 0.0, look_target=(0.0, 0.0))
            return

        # 1. Update Match State transitions
        prev_state = self.match_mgr.state
        self.match_mgr.update(dt, self.ball, self.court)

        if prev_state == MatchState.POINT_SCORED and self.match_mgr.state == MatchState.SERVE_READY:
            self.setup_serve()

        # 2. Update Aim Target (Aiming reticle on opponent court)
        if self.input_mgr.aim_x != 0 or self.input_mgr.aim_z != 0:
            self.aim_target_x += self.input_mgr.aim_x * dt * 8.0
            self.aim_target_z += self.input_mgr.aim_z * dt * 8.0
        else:
            self.aim_target_x += (0.0 - self.aim_target_x) * dt * 2.0
            self.aim_target_z += (6.0 - self.aim_target_z) * dt * 2.0

        self.aim_target_x = max(-HALF_WIDTH + 0.5, min(HALF_WIDTH - 0.5, self.aim_target_x))
        self.aim_target_z = max(2.5, min(HALF_LENGTH - 0.5, self.aim_target_z))

        # 3. Serve Logic
        if self.match_mgr.state == MatchState.SERVE_READY:
            if self.match_mgr.serving_team == Team.PLAYER:
                # User has the ball at backline
                self.ball.x = self.player.x
                self.ball.y = self.player.y + 1.3
                self.ball.z = self.player.z + 0.6
                self.ball.in_air = False

                if self.input_mgr.jump_pressed or self.input_mgr.bump_pressed:
                    self.match_mgr.state = MatchState.SERVE_TOSSED
                    self.ball.launch_arc(self.player.x, self.player.z + 0.8, peak_height=3.6)
                    self.audio_mgr.play("whistle")
            else:
                # Opponent 3 (Defender) serves
                srv_player = self.opponent_3
                self.ball.x = srv_player.x
                self.ball.y = srv_player.y + 1.3
                self.ball.z = srv_player.z - 0.6
                self.ball.in_air = False

                self.ai_serve_timer -= dt
                if self.ai_serve_timer <= 0.0:
                    self.match_mgr.state = MatchState.SERVE_TOSSED
                    self.ball.launch_arc(srv_player.x, srv_player.z - 0.8, peak_height=3.8)
                    self.audio_mgr.play("whistle")
                    self.ai_serve_timer = random.uniform(0.55, 0.75)

        elif self.match_mgr.state == MatchState.SERVE_TOSSED:
            if self.match_mgr.serving_team == Team.PLAYER:
                dist_ball = math.sqrt((self.ball.x - self.player.x)**2 + (self.ball.z - self.player.z)**2)
                if (self.input_mgr.bump_pressed or self.input_mgr.spike_pressed) and dist_ball < 1.9 and self.ball.y > 1.2:
                    is_jump_serve = not self.player.is_grounded
                    target_x = self.aim_target_x
                    target_z = self.aim_target_z

                    if is_jump_serve:
                        self.player.trigger_action(PlayerAction.SPIKE, 0.35)
                        self.ball.launch_arc(target_x, target_z, is_spike=True, spike_speed=21.0)
                        self.match_mgr.register_hit(Team.PLAYER, self.player, "SPIKE")
                        self.ui.trigger_arcade_popup("ACE SERVE!!", COLOR_CORAL_ACCENT)
                        self.input_mgr.trigger_rumble(0.7, 0.9, 0.25)
                    else:
                        self.player.trigger_action(PlayerAction.BUMP, 0.35)
                        self.ball.launch_arc(target_x, target_z, peak_height=3.4)
                        self.match_mgr.register_hit(Team.PLAYER, self.player, "BUMP")
                        self.ui.trigger_arcade_popup("FLOAT SERVE!", COLOR_GOLD_ACCENT)
                        self.input_mgr.trigger_rumble(0.4, 0.4, 0.15)

                    self.match_mgr.state = MatchState.IN_RALLY
            else:
                self.ai_serve_timer -= dt
                if self.ai_serve_timer <= 0.0 and self.ball.y > 1.4:
                    self.opponent_3.trigger_action(PlayerAction.BUMP, 0.35)
                    srv_x = random.uniform(-3.0, 3.0)
                    srv_z = random.uniform(-7.5, -4.0)
                    self.ball.launch_arc(srv_x, srv_z, peak_height=3.5)
                    self.match_mgr.register_hit(Team.OPPONENT, self.opponent_3, "BUMP")
                    self.match_mgr.state = MatchState.IN_RALLY

        # 4. In Rally: Player Ball Interaction
        if self.match_mgr.state == MatchState.IN_RALLY:
            self.handle_player_actions(dt)

        # 5. Update Human Player Movement
        move_x = self.input_mgr.move_x
        move_z = self.input_mgr.move_z

        if self.input_mgr.jump_pressed:
            self.player.jump()

        next_px = self.player.x + move_x * dt * 7.5
        next_pz = self.player.z + move_z * dt * 7.5
        clamped_px, clamped_pz = self.court.clamp_player_position(next_px, next_pz, Team.PLAYER)
        self.player.update(dt, move_x, move_z, look_target=(self.ball.x, self.ball.z))
        self.player.x = clamped_px
        self.player.z = clamped_pz

        # 6. Update AI Managers (Both Player Teammates and Opponents)
        if self.match_mgr.state == MatchState.IN_RALLY:
            self.player_ai_mgr.update(dt, self.ball, self.court, self.match_mgr)
            self.opponent_ai_mgr.update(dt, self.ball, self.court, self.match_mgr)
        else:
            for c in self.team_player[1:] + self.team_opponent:
                c.update(dt, 0.0, 0.0, look_target=(self.ball.x, self.ball.z))

        # 7. Update Ball Physics
        if self.ball.in_air:
            self.ball.update(dt, self.audio_mgr)

        # 8. Update Dynamic Camera
        self.cam_ctrl.update(dt, self.player, self.ball)

    def handle_player_actions(self, dt):
        """Processes player bumps, sets, spikes, and dives with arcade popups."""
        p = self.player
        b = self.ball
        horiz_dist = math.sqrt((b.x - p.x) ** 2 + (b.z - p.z) ** 2)
        touches = self.match_mgr.get_touches(Team.PLAYER)

        # 1. SPIKE (Mid-air smash)
        if not p.is_grounded and p.y > 0.5:
            if self.input_mgr.spike_pressed or self.input_mgr.jump_pressed:
                if horiz_dist < 1.9 and abs(b.y - (p.y + 1.5)) < 1.4:
                    p.trigger_action(PlayerAction.SPIKE, 0.35)
                    self.ball.launch_arc(self.aim_target_x, self.aim_target_z, is_spike=True, spike_speed=23.0)
                    self.match_mgr.register_hit(Team.PLAYER, p, "SPIKE")
                    self.ui.trigger_arcade_popup("BOOM SPIKE!!", COLOR_CORAL_ACCENT)
                    self.input_mgr.trigger_rumble(0.8, 1.0, 0.3)
                    return

        # 2. BUMP / DIG (Receive)
        if p.is_grounded and self.input_mgr.bump_pressed:
            if horiz_dist < 1.8 and 0.2 < b.y < 2.5:
                p.trigger_action(PlayerAction.BUMP, 0.35)
                if touches == 0:
                    # Bump to setter
                    self.ball.launch_arc(-1.8, -2.0, peak_height=4.2)
                    self.ui.trigger_arcade_popup("NICE DIG!", COLOR_CYAN_ACCENT)
                else:
                    self.ball.launch_arc(self.aim_target_x, self.aim_target_z, peak_height=3.5)
                    self.ui.trigger_arcade_popup("OVER THE NET!", COLOR_CYAN_ACCENT)
                self.match_mgr.register_hit(Team.PLAYER, p, "BUMP")
                self.input_mgr.trigger_rumble(0.4, 0.4, 0.15)
                return

        # 3. SET / PAS (Overhead pass)
        if p.is_grounded and self.input_mgr.set_pressed:
            if horiz_dist < 1.8 and 1.5 < b.y < 3.2:
                p.trigger_action(PlayerAction.SET, 0.35)
                spike_spot_x = 1.8 if p.x < 0 else -1.8
                self.ball.launch_arc(spike_spot_x, -1.2, peak_height=3.9)
                self.match_mgr.register_hit(Team.PLAYER, p, "SET")
                self.ui.trigger_arcade_popup("PERFECT SET!", COLOR_GOLD_ACCENT)
                self.input_mgr.trigger_rumble(0.3, 0.3, 0.12)
                return

        # 4. DIVE / SLIDE (Emergency save)
        if p.is_grounded and self.input_mgr.dive_pressed:
            p.trigger_action(PlayerAction.DIVE, 0.45)
            if horiz_dist < 2.4 and b.y < 1.2:
                self.ball.launch_arc(0.0, -3.5, peak_height=3.5)
                self.match_mgr.register_hit(Team.PLAYER, p, "BUMP")
                self.ui.trigger_arcade_popup("SUPER SAVE!!", COLOR_GOLD_ACCENT)
                self.input_mgr.trigger_rumble(0.6, 0.6, 0.2)

    def render(self):
        """Draws 3D stadium, 3v3 characters, and 2D modern arcade overlay."""
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

        # Aim Reticle on opponent court
        if self.match_mgr.state in [MatchState.SERVE_READY, MatchState.SERVE_TOSSED, MatchState.IN_RALLY]:
            ax, az = self.aim_target_x, self.aim_target_z
            pr.draw_circle_3d(pr.Vector3(ax, 0.03, az), 0.5, pr.Vector3(1, 0, 0), 90.0, pr.Color(255, 60, 60, 180))
            pr.draw_line_3d(pr.Vector3(ax - 0.7, 0.03, az), pr.Vector3(ax + 0.7, 0.03, az), pr.Color(255, 255, 255, 200))
            pr.draw_line_3d(pr.Vector3(ax, 0.03, az - 0.7), pr.Vector3(ax, 0.03, az + 0.7), pr.Color(255, 255, 255, 200))

        pr.end_mode_3d()

        # --- 2D UI & Overlays ---
        if self.match_mgr.state == MatchState.TITLE_SCREEN:
            self.ui.draw_title_screen(self.ai_diff, self.audio_mgr, self.input_mgr)
        else:
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
