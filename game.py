"""
FlyHigh! - 3D Volleyball Game
Main Game System & Loop
Integrates 2v2 to 6v6 Volleyball, 5 Multi-Arena Courts, Dynamic Viewport Scaling,
BAM Jump & Charge Mechanics, Green Timing Anime Elemental VFX, Strict FIVB Serve Block Rules,
and NBA 2K-Style Shot Timing.
"""
import pyray as pr
import math
import random
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_FPS, GAME_TITLE,
    Team, MatchState, PlayerAction, AIDifficulty, TimingRating,
    NET_HEIGHT, BALL_RADIUS, BLOCK_REACH_RADIUS,
    GameMode, CourtArena, MODE_CONFIGS
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
from player_customization import PlayerProfile

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

        # Player Career Profile & Custom Cosmetics
        self.profile = PlayerProfile()
        self.match_stats_recorded = False

        # Current match format & venue
        self.current_mode = GameMode.MODE_3V3
        self.current_arena = CourtArena.BEACH

        # Captain (User Player, initialized with custom profile)
        self.player = Character(x=0.0, z=-8.2, team=Team.PLAYER, jersey_num=self.profile.jersey_number, name=self.profile.name, is_ai=False)
        self.player.apply_profile(self.profile)

        # Rosters
        self.team_player = [self.player]
        self.team_opponent = []
        self.player_ai_mgr = TeamAIController(self.team_player, team=Team.PLAYER, difficulty=self.ai_diff, human_player=self.player)
        self.opponent_ai_mgr = TeamAIController(self.team_opponent, team=Team.OPPONENT, difficulty=self.ai_diff)

        # Initialize Default 3v3 Teams
        self.start_match(GameMode.MODE_3V3, CourtArena.BEACH, self.ai_diff, 11, start_serving=False)

        # Aim Target on court floor (Mouse raycast or stick)
        self.aim_target_x = 0.0
        self.aim_target_z = 5.5

        # Timing shot meter cache
        self.shot_meter_timing = 0.0
        self.shot_meter_visible = False

        # Timers & Camera Orbit in Menu
        self.ai_serve_timer = 0.0
        self.serve_toss_timer = 0.0
        self.is_paused = False

        # Start in TITLE_SCREEN
        self.match_mgr.state = MatchState.TITLE_SCREEN
        self.player.action = PlayerAction.MENU_IDLE

    def start_match(self, mode: GameMode, arena: CourtArena, difficulty: AIDifficulty, points_to_win: int, start_serving=True):
        """Builds player & opponent rosters dynamically for selected match mode and venue."""
        self.current_mode = mode
        self.current_arena = arena
        self.court.set_mode_and_arena(mode, arena)
        self.match_mgr.points_to_win = points_to_win
        self.ai_diff = difficulty

        cfg = MODE_CONFIGS.get(mode, MODE_CONFIGS[GameMode.MODE_3V3])
        team_size = cfg["team_size"]

        # 1. Build Team Player (User Captain + Teammates)
        self.player.apply_profile(self.profile)
        self.team_player = [self.player]
        teammate_specs = [
            (2, "SETTER"),
            (4, "WING"),
            (7, "BLOCKER"),
            (9, "LIBERO"),
            (11, "OPPOSITE")
        ]
        for idx in range(team_size - 1):
            num, role = teammate_specs[idx]
            tm = Character(x=-2.0, z=-4.0, team=Team.PLAYER, jersey_num=num, name=role, is_ai=True)
            self.team_player.append(tm)

        # 2. Build Team Opponent
        self.team_opponent = []
        opp_specs = [
            (1, "RIVAL"),
            (3, "OPP_SETTER"),
            (5, "OPP_BLOCK"),
            (8, "OPP_WING"),
            (6, "OPP_LIBERO"),
            (10, "OPP_ACE")
        ]
        for idx in range(team_size):
            num, role = opp_specs[idx]
            opp = Character(x=2.0, z=4.0, team=Team.OPPONENT, jersey_num=num, name=role, is_ai=True)
            self.team_opponent.append(opp)

        self.player_ai_mgr.set_characters(self.team_player, self.court)
        self.opponent_ai_mgr.set_characters(self.team_opponent, self.court)
        self.player_ai_mgr.set_difficulty(difficulty)
        self.opponent_ai_mgr.set_difficulty(difficulty)

        if start_serving:
            self.match_mgr.reset_match()
            self.setup_serve()

    def setup_serve(self):
        """Cleanly positions dynamic teams and locks ball in server hands."""
        self.serve_toss_timer = 0.0
        self.match_stats_recorded = False
        self.player.apply_profile(self.profile)

        # Reset all players to their home formation positions
        self.player_ai_mgr.reset_positions()
        self.opponent_ai_mgr.reset_positions()

        hl = self.court.half_length
        if self.match_mgr.serving_team == Team.PLAYER:
            # User serves at baseline
            self.player.reset_position(0.0, -hl + 0.35)
            self.player.action = PlayerAction.SERVE_HOLD
            fwd_x = math.sin(self.player.facing_angle)
            fwd_z = math.cos(self.player.facing_angle)
            self.ball.reset(x=self.player.x + fwd_x * 0.52, y=self.player.y + 1.25, z=self.player.z + fwd_z * 0.52, team=Team.PLAYER)
            self.ball.in_air = False
        else:
            # Opponent server is the backcourt server in roster
            srv = self.team_opponent[-1]
            srv.reset_position(0.0, hl - 0.35)
            srv.action = PlayerAction.SERVE_HOLD
            fwd_x = math.sin(srv.facing_angle)
            fwd_z = math.cos(srv.facing_angle)
            self.ball.reset(x=srv.x + fwd_x * 0.52, y=srv.y + 1.25, z=srv.z + fwd_z * 0.52, team=Team.OPPONENT)
            self.ball.in_air = False
            self.ai_serve_timer = random.uniform(1.2, 1.8)

    def run(self):
        """Main game loop with exception guard to prevent unexpected crashes."""
        while not pr.window_should_close():
            try:
                dt = pr.get_frame_time()
                if dt > 0.05:
                    dt = 0.05

                self.handle_input()
                if not self.is_paused:
                    self.update(dt)

                self.render()
            except Exception as e:
                import traceback
                print(f"[GAME LOOP ERROR]: {e}")
                traceback.print_exc()

        self.cleanup()

    def handle_input(self):
        self.input_mgr.update()

        # Title / Settings Menu Navigation
        if self.match_mgr.state == MatchState.TITLE_SCREEN:
            action, new_diff = self.ui.update_menu(self.input_mgr, self.audio_mgr, self.ai_diff, self.cam_ctrl, self.profile, self.player)
            if new_diff != self.ai_diff:
                self.ai_diff = new_diff
                self.player_ai_mgr.set_difficulty(new_diff)
                self.opponent_ai_mgr.set_difficulty(new_diff)

            if isinstance(action, tuple) and action[0] == "START_MATCH":
                _, sel_mode, sel_arena, sel_diff, sel_pts = action
                self.start_match(sel_mode, sel_arena, sel_diff, sel_pts)
            elif action == "PLAY":
                self.start_match(GameMode.MODE_3V3, CourtArena.BEACH, self.ai_diff, 11)
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
                self.ui.pending_res_index = self.ui.res_index
                self.ui.pending_fullscreen = self.ui.is_fullscreen
                self.audio_mgr.play("hit_bump")
                return
            if pr.is_key_pressed(pr.KEY_Q):
                self.is_paused = False
                self.match_mgr.state = MatchState.TITLE_SCREEN
                self.player.action = PlayerAction.MENU_IDLE
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
                self.player.action = PlayerAction.MENU_IDLE

    def update(self, dt):
        if self.match_mgr.state == MatchState.TITLE_SCREEN:
            # Menu character holds volleyball tucked at hip
            self.player.action = PlayerAction.MENU_IDLE
            self.player.update(dt, 0.0, 0.0, look_target=None)
            return

        # Record Career Stats upon match completion
        if self.match_mgr.state == MatchState.MATCH_OVER and not self.match_stats_recorded:
            self.match_stats_recorded = True
            self.profile.matches_played += 1
            if self.match_mgr.winner == Team.PLAYER:
                self.profile.matches_won += 1
                self.profile.crowns += 50
                self.profile.xp += 150
            else:
                self.profile.crowns += 10
                self.profile.xp += 50
            if self.profile.xp >= self.profile.xp_max:
                self.profile.level += 1
                self.profile.xp -= self.profile.xp_max
                self.profile.xp_max = int(self.profile.xp_max * 1.3)
            self.profile.save()

        # 1. Update Match State transitions
        prev_state = self.match_mgr.state
        self.match_mgr.update(dt, self.ball, self.court)

        if prev_state == MatchState.POINT_SCORED and self.match_mgr.state == MatchState.SERVE_READY:
            self.setup_serve()

        # 2. CURSOR-BASED AIMING: Mouse Raycast onto Court Floor (Y = 0)
        mouse_pos = pr.get_mouse_position()
        ray = pr.get_screen_to_world_ray(mouse_pos, self.cam_ctrl.cam)
        hw = self.court.half_width
        hl = self.court.half_length
        
        if ray.direction.y < -0.0001:
            t = -ray.position.y / ray.direction.y
            hit_x = ray.position.x + t * ray.direction.x
            hit_z = ray.position.z + t * ray.direction.z
            self.aim_target_x = max(-hw - 0.6, min(hw + 0.6, hit_x))
            self.aim_target_z = max(-hl - 1.5, min(hl + 1.5, hit_z))
        elif self.input_mgr.active_device == "GAMEPAD":
            if abs(self.input_mgr.aim_x) > 0.1 or abs(self.input_mgr.aim_z) > 0.1:
                self.aim_target_x += self.input_mgr.aim_x * dt * 9.5
                self.aim_target_z += self.input_mgr.aim_z * dt * 9.5
                self.aim_target_x = max(-hw + 0.4, min(hw - 0.4, self.aim_target_x))
                self.aim_target_z = max(-hl + 0.4, min(hl - 0.4, self.aim_target_z))

        # 3. CALCULATE NBA 2K-STYLE SHOT METER TIMING
        if self.match_mgr.state == MatchState.SERVE_TOSSED and self.match_mgr.serving_team == Team.PLAYER:
            self.serve_toss_timer += dt
            t = self.serve_toss_timer
            # Smooth progression: rises to green sweet spot (0.50s - 1.30s), then decays
            if t < 0.50:
                self.shot_meter_timing = 0.20 + (t / 0.50) * 0.68
            elif t <= 1.30:
                sweet_progress = (t - 0.50) / 0.80
                self.shot_meter_timing = 0.88 + 0.12 * math.sin(sweet_progress * math.pi)
            elif t <= 1.60:
                fall_progress = (t - 1.30) / 0.30
                self.shot_meter_timing = 0.85 - fall_progress * 0.35
            else:
                self.shot_meter_timing = max(0.1, 0.50 - (t - 1.60) * 0.8)

            if not self.player.is_grounded:
                reach_y = self.player.y + 1.95
                diff = abs(self.ball.y - reach_y)
                if diff < 0.70:
                    self.shot_meter_timing = max(self.shot_meter_timing, 0.86 + 0.14 * (1.0 - diff / 0.70))

            self.shot_meter_visible = True

        elif not self.player.is_grounded and self.ball.in_air and self.ball.y > 1.2:
            reach_y = self.player.y + 1.95
            diff_y = abs(self.ball.y - reach_y)
            if diff_y < 0.70:
                self.shot_meter_timing = 0.85 + 0.15 * (1.0 - diff_y / 0.70)
            elif diff_y < 1.40:
                self.shot_meter_timing = 0.52 + 0.33 * (1.0 - (diff_y - 0.70) / 0.70)
            else:
                self.shot_meter_timing = max(0.1, 0.50 * (1.0 - (diff_y - 1.40) / 1.0))

            self.shot_meter_visible = True
        else:
            self.shot_meter_timing = 0.0
            self.shot_meter_visible = False

        # 4. SERVE MECHANICS
        if self.match_mgr.state == MatchState.SERVE_READY:
            if self.match_mgr.serving_team == Team.PLAYER:
                self.player.action = PlayerAction.SERVE_HOLD
                fwd_x = math.sin(self.player.facing_angle)
                fwd_z = math.cos(self.player.facing_angle)
                hold_bob = math.sin(self.player.anim_time * 3.5) * 0.02
                self.ball.x = self.player.x + fwd_x * 0.52
                self.ball.y = self.player.y + 1.25 + hold_bob
                self.ball.z = self.player.z + fwd_z * 0.52
                self.ball.vx = 0.0
                self.ball.vy = 0.0
                self.ball.vz = 0.0
                self.ball.in_air = False

                # EXCLUSIVE TOSS TRIGGER: Right Click (or Gamepad Y)
                toss_triggered = (
                    pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_RIGHT) or
                    (pr.is_gamepad_available(self.input_mgr.gamepad_id) and
                     pr.is_gamepad_button_pressed(self.input_mgr.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_FACE_UP))
                )
                if toss_triggered:
                    self.serve_toss_timer = 0.0
                    self.player.trigger_action(PlayerAction.SERVE_TOSS, 0.45)
                    self.match_mgr.state = MatchState.SERVE_TOSSED
                    self.ball.launch_arc(self.player.x, self.player.z + 0.85, peak_height=5.4, hitter=self.player)
                    self.audio_mgr.play("whistle")
                    self.ui.trigger_arcade_popup("BALL TOSSED! JUMP & HIT!", COLOR_GOLD_ACCENT, 1.2)
            else:
                srv = self.team_opponent[-1]
                srv.action = PlayerAction.SERVE_HOLD
                fwd_x = math.sin(srv.facing_angle)
                fwd_z = math.cos(srv.facing_angle)
                hold_bob = math.sin(srv.anim_time * 3.5) * 0.02
                self.ball.x = srv.x + fwd_x * 0.52
                self.ball.y = srv.y + 1.25 + hold_bob
                self.ball.z = srv.z + fwd_z * 0.52
                self.ball.vx = 0.0
                self.ball.vy = 0.0
                self.ball.vz = 0.0
                self.ball.in_air = False

                self.ai_serve_timer -= dt
                if self.ai_serve_timer <= 0.0:
                    srv.trigger_action(PlayerAction.SERVE_TOSS, 0.45)
                    self.match_mgr.state = MatchState.SERVE_TOSSED
                    self.ball.launch_arc(srv.x, srv.z - 0.85, peak_height=5.2, hitter=srv)
                    self.audio_mgr.play("whistle")
                    self.ai_serve_timer = 0.85

        elif self.match_mgr.state == MatchState.SERVE_TOSSED:
            if self.match_mgr.serving_team == Team.PLAYER:
                if self.ball.has_bounced or (self.ball.y <= BALL_RADIUS + 0.06 and self.ball.vy <= 0):
                    self.setup_serve()
                    self.ui.trigger_arcade_popup("MISSED TOSS! RIGHT-CLICK TO RETOSS", COLOR_CORAL_ACCENT, 1.2)
                    return

                dist_ball = math.sqrt((self.ball.x - self.player.x)**2 + (self.ball.z - self.player.z)**2)
                hit_attempt = (
                    self.input_mgr.is_float_serve_triggered or
                    self.input_mgr.lmb_pressed or
                    self.input_mgr.spike_pressed or
                    self.input_mgr.e_pressed or
                    self.input_mgr.rmb_pressed
                )

                if hit_attempt and dist_ball < 2.6 and self.ball.y > 1.2:
                    target_x = self.aim_target_x
                    target_z = max(2.5, self.aim_target_z)
                    rating = self._evaluate_timing(self.shot_meter_timing)
                    self.ui.trigger_shot_feedback(rating)

                    # 1. FLOAT SERVE: [L-CLICK + E]
                    if self.input_mgr.is_float_serve_triggered or (self.input_mgr.e_pressed and not self.player.is_grounded):
                        if rating == TimingRating.GREEN:
                            self.player.trigger_action(PlayerAction.SPIKE, 0.35)
                            self.ball.launch_arc(target_x, target_z, is_float=True, is_green_timing=True, green_vfx_type="WATER", peak_height=3.0, hitter=self.player)
                            self.match_mgr.register_hit(Team.PLAYER, self.player, "SPIKE")
                            self.ui.trigger_arcade_popup("PERFECT FLOAT SERVE!!", COLOR_CYAN_ACCENT)
                            self.input_mgr.trigger_rumble(0.7, 0.9, 0.25)
                        elif rating == TimingRating.YELLOW:
                            self.player.trigger_action(PlayerAction.SPIKE, 0.35)
                            self.ball.launch_arc(target_x, target_z, peak_height=4.4, hitter=self.player)
                            self.match_mgr.register_hit(Team.PLAYER, self.player, "SPIKE")
                            self.ui.trigger_arcade_popup("GOOD SERVE", COLOR_GOLD_ACCENT)
                            self.input_mgr.trigger_rumble(0.4, 0.4, 0.15)
                        else:
                            self.player.trigger_action(PlayerAction.BUMP, 0.35)
                            rx = target_x + random.uniform(-1.8, 1.8)
                            rz = target_z + random.uniform(-1.8, 1.8)
                            self.ball.launch_arc(rx, rz, peak_height=5.2, hitter=self.player)
                            self.match_mgr.register_hit(Team.PLAYER, self.player, "BUMP")
                            self.ui.trigger_arcade_popup("MISTIMED SERVE!", COLOR_CORAL_ACCENT)

                        self.match_mgr.state = MatchState.IN_RALLY

                    # 2. POWER JUMP SERVE: [L-CLICK] or [SPACE in air]
                    elif self.input_mgr.lmb_pressed or self.input_mgr.spike_pressed:
                        self.player.trigger_action(PlayerAction.SPIKE, 0.35)
                        if rating == TimingRating.GREEN:
                            vfx = random.choice(["FIRE", "LIGHTNING"])
                            self.ball.launch_arc(target_x, target_z, is_spike=True, is_green_timing=True, green_vfx_type=vfx, spike_speed=27.0, hitter=self.player)
                            self.ui.trigger_arcade_popup(f"ACE JUMP SERVE!! ({vfx})", COLOR_CORAL_ACCENT)
                            self.input_mgr.trigger_rumble(1.0, 1.0, 0.35)
                        elif rating == TimingRating.YELLOW:
                            self.ball.launch_arc(target_x, target_z, is_spike=True, spike_speed=19.5, hitter=self.player)
                            self.ui.trigger_arcade_popup("GOOD SERVE", COLOR_GOLD_ACCENT)
                            self.input_mgr.trigger_rumble(0.5, 0.6, 0.2)
                        else:
                            rx = target_x + random.uniform(-1.6, 1.6)
                            rz = target_z + random.uniform(-1.6, 1.6)
                            self.ball.launch_arc(rx, rz, peak_height=5.4, hitter=self.player)
                            self.ui.trigger_arcade_popup("OFF-TIME HIT", COLOR_CORAL_ACCENT)

                        self.match_mgr.register_hit(Team.PLAYER, self.player, "SPIKE")
                        self.match_mgr.state = MatchState.IN_RALLY

                    # 3. DUMP SERVE: [E]
                    elif self.input_mgr.e_pressed:
                        self.player.trigger_action(PlayerAction.DUMP, 0.35)
                        self.ball.launch_arc(target_x, 2.0, peak_height=3.2, hitter=self.player)
                        self.match_mgr.register_hit(Team.PLAYER, self.player, "SET")
                        self.ui.trigger_arcade_popup("DUMP SERVE!", COLOR_GOLD_ACCENT)
                        self.match_mgr.state = MatchState.IN_RALLY

                    # 4. PASS SERVE: [R-CLICK]
                    elif self.input_mgr.rmb_pressed:
                        self.player.trigger_action(PlayerAction.SET, 0.35)
                        self.ball.launch_arc(target_x, target_z, peak_height=4.8, hitter=self.player)
                        self.match_mgr.register_hit(Team.PLAYER, self.player, "SET")
                        self.ui.trigger_arcade_popup("PASS SERVE", COLOR_CYAN_ACCENT)
                        self.match_mgr.state = MatchState.IN_RALLY

            else:
                # Opponent AI strikes serve
                srv = self.team_opponent[-1]
                self.ai_serve_timer -= dt
                if self.ai_serve_timer <= 0.0:
                    srv.trigger_action(PlayerAction.SPIKE, 0.35)
                    srv_x = random.uniform(-self.court.half_width * 0.6, self.court.half_width * 0.6)
                    srv_z = random.uniform(-self.court.half_length * 0.8, -self.court.half_length * 0.45)
                    self.ball.launch_arc(srv_x, srv_z, peak_height=4.8, hitter=srv)
                    self.match_mgr.register_hit(Team.OPPONENT, srv, "BUMP")
                    self.match_mgr.state = MatchState.IN_RALLY

        # 5. IN RALLY: Complete Volleyball Control Pipeline
        if self.match_mgr.state == MatchState.IN_RALLY:
            self.handle_rally_actions(dt)

        # 6. Human Player Movement & BAM Jump Charging
        move_x = self.input_mgr.move_x
        move_z = self.input_mgr.move_z

        if self.player.is_grounded:
            if self.input_mgr.jump_down:
                self.player.jump_charge += dt * 2.4
                self.player.action = PlayerAction.BAM_CHARGE
            else:
                if self.player.jump_charge > 0.05:
                    if self.player.jump_charge >= 0.70:
                        # BAM JUMP! Explosive leap clearing well above the net!
                        self.player.jump(is_bam=True)
                        self.ui.trigger_arcade_popup("BAM JUMP!!", COLOR_GOLD_ACCENT, 1.0)
                        self.audio_mgr.play("hit_spike")
                        self.input_mgr.trigger_rumble(0.9, 0.9, 0.35)
                    elif self.player.jump_charge >= 0.25:
                        # SUPER JUMP!
                        self.player.jump(is_super=True)
                        self.ui.trigger_arcade_popup("SUPER JUMP!", COLOR_CYAN_ACCENT, 0.7)
                        self.audio_mgr.play("hit_spike")
                        self.input_mgr.trigger_rumble(0.6, 0.6, 0.2)
                    self.player.jump_charge = 0.0
                elif self.input_mgr.jump_pressed:
                    # Standard jump tap
                    self.player.jump(is_super=False)

        next_px = self.player.x + move_x * dt * 7.8
        next_pz = self.player.z + move_z * dt * 7.8
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
        """Processes precise user actions in rally (Spike, Float, Dump, Bailout, Dig, Set, Roll Dig, Block)."""
        p = self.player
        b = self.ball

        if not b.can_be_hit_by(p) and b.hit_cooldown > 0.08:
            return

        horiz_dist = math.sqrt((b.x - p.x) ** 2 + (b.z - p.z) ** 2)
        target_x = self.aim_target_x
        target_z = self.aim_target_z

        # ---------------- IN-AIR ACTIONS (JUMPING) ----------------
        if not p.is_grounded and p.y > 0.35:
            # A. Emergency Air Bailout: [L-CTRL + L-CLICK]
            if self.input_mgr.is_air_bailout_triggered:
                if horiz_dist < 2.8 and b.y < p.y + 2.5:
                    p.trigger_action(PlayerAction.AIR_BAILOUT, 0.40)
                    self.ball.launch_arc(target_x, max(2.5, target_z), peak_height=4.4, hitter=p)
                    self.match_mgr.register_hit(Team.PLAYER, p, "BUMP")
                    self.ui.trigger_arcade_popup("EMERGENCY TAP!", COLOR_CORAL_ACCENT)
                    self.input_mgr.trigger_rumble(0.5, 0.5, 0.18)
                    return

            # B. In-Air Dump: [E] (Soft feather over block)
            if self.input_mgr.e_pressed:
                if horiz_dist < 2.2 and abs(b.y - (p.y + 1.5)) < 1.6:
                    p.trigger_action(PlayerAction.DUMP, 0.35)
                    self.ball.launch_arc(target_x, max(1.5, target_z), peak_height=3.0, hitter=p)
                    self.match_mgr.register_hit(Team.PLAYER, p, "SET")
                    self.ui.trigger_arcade_popup("DUMP OVER BLOCK!", COLOR_GOLD_ACCENT)
                    self.input_mgr.trigger_rumble(0.3, 0.3, 0.12)
                    return

            # C. In-Air Block (Near Net: Z > -3.0): [R-CLICK]
            if self.input_mgr.rmb_pressed or (self.input_mgr.rmb_down and p.z > -3.0):
                if p.z > -3.0:
                    p.trigger_action(PlayerAction.BLOCK, 0.45)
                    
                    # PHYSICAL NET BLOCK DETECTION VOLUME:
                    is_in_block_zone = (
                        abs(b.x - p.x) <= 1.65 and
                        1.95 <= b.y <= p.y + 2.8 and
                        (abs(b.z) <= 1.85 or abs(b.z - p.z) <= 2.2)
                    )

                    if is_in_block_zone:
                        # OFFICIAL FIVB RULE: BLOCKING A SERVE IS ILLEGAL!
                        opp_touches = self.match_mgr.get_touches(Team.OPPONENT)
                        if self.match_mgr.state == MatchState.SERVE_TOSSED or (self.match_mgr.serving_team == Team.OPPONENT and opp_touches == 0):
                            self.match_mgr.award_point(Team.OPPONENT, "FAULT: ILLEGAL SERVE BLOCK!")
                            self.ui.trigger_arcade_popup("ILLEGAL SERVE BLOCK! FAULT!", COLOR_CORAL_ACCENT, 1.5)
                            return

                        self.input_mgr.trigger_rumble(0.85, 0.85, 0.28)
                        if p.y > 0.85 and b.y > 2.05 and target_z > 1.5:
                            # 1. MONSTER ROOF BLOCK: Direct spike rejection back down into opponent court!
                            tx = target_x
                            tz = max(2.0, target_z)
                            self.ball.launch_arc(tx, tz, is_spike=True, spike_speed=23.5, hitter=p)
                            self.ui.trigger_arcade_popup("MONSTER ROOF BLOCK!!", COLOR_GOLD_ACCENT, 1.2)
                            self.audio_mgr.play("hit_spike")
                        elif abs(b.x - p.x) > 0.65:
                            # 2. TOOL / BLOCK OUT: Ricochets sideways off fingertips!
                            tool_x = p.x + (3.8 if b.x > p.x else -3.8)
                            self.ball.launch_arc(tool_x, 6.5, peak_height=4.6, hitter=p)
                            self.ui.trigger_arcade_popup("TOOL OFF BLOCK!", COLOR_CORAL_ACCENT, 1.0)
                            self.audio_mgr.play("hit_bump")
                        else:
                            # 3. SOFT TOUCH: Deflection upwards into own backcourt for counter-attack!
                            self.ball.launch_arc(p.x + random.uniform(-0.8, 0.8), -self.court.half_length * 0.65, peak_height=5.8, hitter=p)
                            self.ui.trigger_arcade_popup("SOFT TOUCH! DIG IT UP!", COLOR_CYAN_ACCENT, 1.0)
                            self.audio_mgr.play("hit_bump")

                        self.match_mgr.register_hit(Team.PLAYER, p, "BLOCK")
                        return

                elif horiz_dist < 2.2 and abs(b.y - (p.y + 1.5)) < 1.6:
                    p.trigger_action(PlayerAction.SET, 0.35)
                    self.ball.launch_arc(target_x, target_z, peak_height=5.2, hitter=p)
                    self.match_mgr.register_hit(Team.PLAYER, p, "SET")
                    self.ui.trigger_arcade_popup("AIR PASS!", COLOR_CYAN_ACCENT)
                    self.input_mgr.trigger_rumble(0.3, 0.3, 0.12)
                    return

            # D. Power Spike Attack: [L-CLICK] or [SPACE]
            if self.input_mgr.lmb_pressed or self.input_mgr.spike_pressed:
                if horiz_dist < 2.3 and abs(b.y - (p.y + 1.5)) < 1.6:
                    rating = self._evaluate_timing(self.shot_meter_timing)
                    self.ui.trigger_shot_feedback(rating)
                    p.trigger_action(PlayerAction.SPIKE, 0.35)

                    if rating == TimingRating.GREEN:
                        # Anime Blazing Power Spike!
                        vfx = random.choice(["FIRE", "LIGHTNING", "WATER"])
                        self.ball.launch_arc(target_x, target_z, is_spike=True, is_green_timing=True, green_vfx_type=vfx, spike_speed=27.5, hitter=p)
                        self.ui.trigger_arcade_popup(f"BOOM SPIKE!! ({vfx})", COLOR_GREEN_PERFECT, 1.2)
                        self.input_mgr.trigger_rumble(1.0, 1.0, 0.35)
                    elif rating == TimingRating.YELLOW:
                        self.ball.launch_arc(target_x, target_z, is_spike=True, spike_speed=19.5, hitter=p)
                        self.ui.trigger_arcade_popup("SOLID SPIKE!", COLOR_GOLD_ACCENT)
                        self.input_mgr.trigger_rumble(0.5, 0.6, 0.2)
                    else:
                        rx = target_x + random.uniform(-1.8, 1.8)
                        rz = target_z + random.uniform(-1.8, 1.8)
                        self.ball.launch_arc(rx, rz, peak_height=4.8, hitter=p)
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
                    dist_to_landing = math.sqrt((self.ball.predict_x - p.x)**2 + (self.ball.predict_z - p.z)**2)
                    if horiz_dist < 3.8 or dist_to_landing < 3.4:
                        p.trigger_action(PlayerAction.ROLL_DIG, 0.60)
                        self.ball.launch_arc(target_x, target_z, peak_height=5.2, hitter=p)
                        self.match_mgr.register_hit(Team.PLAYER, p, "BUMP")
                        self.ui.trigger_arcade_popup("HEROIC ROLL DIG!!", COLOR_GOLD_ACCENT)
                        self.audio_mgr.play("floor_bounce")
                        self.audio_mgr.play("hit_bump")
                        self.input_mgr.trigger_rumble(0.7, 0.9, 0.25)
                        return

            # B. Setter Dump: [R-CLICK + E]
            if self.input_mgr.is_setter_dump_triggered:
                if horiz_dist < 2.4 and 1.2 < b.y < 3.2:
                    p.trigger_action(PlayerAction.SETTER_DUMP, 0.35)
                    self.ball.launch_arc(target_x, max(1.8, target_z), peak_height=3.2, hitter=p)
                    self.match_mgr.register_hit(Team.PLAYER, p, "SET")
                    self.ui.trigger_arcade_popup("TRICK SETTER DUMP!", COLOR_GOLD_ACCENT)
                    self.input_mgr.trigger_rumble(0.4, 0.4, 0.15)
                    return

            # C. Ground Bump / Receive / Dig: [L-CTRL] (Directs to cursor)
            if self.input_mgr.ctrl_down or (self.input_mgr.bump_pressed and not self.input_mgr.rmb_down):
                if horiz_dist < 2.4 and 0.2 < b.y < 3.2:
                    p.trigger_action(PlayerAction.BUMP, 0.35)
                    rating = self._evaluate_timing(self.shot_meter_timing)

                    if rating == TimingRating.GREEN:
                        # High, floaty arching ball directly to setter
                        self.ball.launch_arc(target_x, target_z, peak_height=6.2, hitter=p)
                        self.ui.trigger_arcade_popup("PERFECT DIG!", COLOR_GREEN_PERFECT)
                    else:
                        self.ball.launch_arc(target_x, target_z, peak_height=5.2, hitter=p)
                        self.ui.trigger_arcade_popup("NICE DIG!", COLOR_CYAN_ACCENT)

                    self.match_mgr.register_hit(Team.PLAYER, p, "BUMP")
                    self.input_mgr.trigger_rumble(0.4, 0.4, 0.15)
                    return

            # D. Ground Pass / Set: [R-CLICK]
            if self.input_mgr.rmb_pressed and not self.input_mgr.ctrl_down:
                if horiz_dist < 2.2 and 1.2 < b.y < 3.2:
                    p.trigger_action(PlayerAction.SET, 0.35)
                    self.ball.launch_arc(target_x, target_z, peak_height=4.8, hitter=p)
                    self.match_mgr.register_hit(Team.PLAYER, p, "SET")
                    self.ui.trigger_arcade_popup("PERFECT SET!", COLOR_CYAN_ACCENT)
                    self.input_mgr.trigger_rumble(0.3, 0.3, 0.12)
                    return

    def render(self):
        """Draws 3D stadium, characters, ball, reticle, and 2D modern arcade overlays."""
        pr.begin_drawing()
        pr.clear_background(pr.Color(135, 206, 250, 255))

        # --- 3D Scene ---
        pr.begin_mode_3d(self.cam_ctrl.cam)

        # 1. Multi-Arena Court (Beach, Orange Arena, Sky High, Cruise Ship, High School Gym)
        self.court.draw()

        if self.match_mgr.state == MatchState.TITLE_SCREEN:
            # Main Menu Center Hero
            self.player.draw()
        else:
            # 2. Player Cyan Selection Ring on Floor
            pr.draw_circle_3d(pr.Vector3(self.player.x, 0.02, self.player.z), 0.58, pr.Vector3(1, 0, 0), 90.0, pr.Color(35, 220, 245, 220))
            pr.draw_circle_3d(pr.Vector3(self.player.x, 0.025, self.player.z), 0.44, pr.Vector3(1, 0, 0), 90.0, pr.Color(18, 25, 38, 140))

            # 3. Render Team Characters (Supports 2v2 to 6v6)
            for char in self.team_player:
                char.draw()
            for char in self.team_opponent:
                char.draw()

            # 4. Ball, ground shadow & landing ring
            self.ball.draw()

            # 5. DYNAMIC TRAJECTORY BEAM & LANDING TARGET
            if self.ball.in_air and not self.ball.has_bounced:
                pred_pos = pr.Vector3(self.ball.predict_x, 0.03, self.ball.predict_z)
                ball_pos = pr.Vector3(self.ball.x, self.ball.y, self.ball.z)

                # Red Landing 'X' on court floor
                x_size = 0.48
                pr.draw_line_3d(pr.Vector3(pred_pos.x - x_size, 0.03, pred_pos.z - x_size), pr.Vector3(pred_pos.x + x_size, 0.03, pred_pos.z + x_size), pr.Color(245, 55, 65, 230))
                pr.draw_line_3d(pr.Vector3(pred_pos.x - x_size, 0.03, pred_pos.z + x_size), pr.Vector3(pred_pos.x + x_size, 0.03, pred_pos.z - x_size), pr.Color(245, 55, 65, 230))
                ripple_rad = 0.45 + 0.15 * math.sin(pr.get_time() * 8.0)
                pr.draw_circle_3d(pred_pos, ripple_rad, pr.Vector3(1, 0, 0), 90.0, pr.Color(245, 55, 65, 140))

                # Translucent Pink / Magenta Trajectory Ribbon
                steps = 14
                for s in range(steps):
                    t1 = s / steps
                    t2 = (s + 1) / steps
                    p1_x = ball_pos.x + (pred_pos.x - ball_pos.x) * t1
                    p1_y = ball_pos.y * (1.0 - t1) + 0.05
                    p1_z = ball_pos.z + (pred_pos.z - ball_pos.z) * t1

                    p2_x = ball_pos.x + (pred_pos.x - ball_pos.x) * t2
                    p2_y = ball_pos.y * (1.0 - t2) + 0.05
                    p2_z = ball_pos.z + (pred_pos.z - ball_pos.z) * t2

                    beam_alpha = int(120 + 90 * (1.0 - t1))
                    pr.draw_line_3d(pr.Vector3(p1_x, p1_y, p1_z), pr.Vector3(p2_x, p2_y, p2_z), pr.Color(255, 50, 160, beam_alpha))

            # 6. PINK CROSSHAIR AIMING RETICLE
            if self.match_mgr.state in [MatchState.SERVE_READY, MatchState.SERVE_TOSSED, MatchState.IN_RALLY]:
                ax, az = self.aim_target_x, self.aim_target_z
                pink_col = pr.Color(255, 45, 145, 255)
                cs = 0.55
                pr.draw_line_3d(pr.Vector3(ax - cs, 0.035, az), pr.Vector3(ax + cs, 0.035, az), pink_col)
                pr.draw_line_3d(pr.Vector3(ax, 0.035, az - cs), pr.Vector3(ax, 0.035, az + cs), pink_col)
                pr.draw_circle_3d(pr.Vector3(ax, 0.03, az), 0.16, pr.Vector3(1, 0, 0), 90.0, pr.Color(255, 45, 145, 120))

        pr.end_mode_3d()

        # --- 2D UI & Overlays (Scaled Dynamically to Window Size) ---
        if self.match_mgr.state == MatchState.TITLE_SCREEN:
            self.ui.draw_title_screen(self.ai_diff, self.audio_mgr, self.input_mgr, self.cam_ctrl, self.profile, self.player)
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
