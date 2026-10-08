"""
FlyHigh! - 3D Volleyball Game
3v3 Team AI Controller
Enforces strict authentic volleyball tactics:
- Touch 1 (Bump / Dig): Receiver lofts a high, floaty ball (5.8m+ peak) directly to the SETTER.
- Touch 2 (The Set): The SETTER exclusively takes the ball and delivers a high lofting set (5.4m+ peak) to the SPIKER.
- Touch 3 (The Attack): The SPIKER approaches, leaps into the air, and spikes over the net!
- Dynamic Net Blocking: Frontline blocker jumps and blocks when the opposing team attacks at the net!
"""
import math
import random
from constants import (
    Team, PlayerAction, AIDifficulty, HALF_WIDTH, HALF_LENGTH, NET_HEIGHT
)

class TeamAIController:
    def __init__(self, characters, team=Team.OPPONENT, difficulty=AIDifficulty.MEDIUM, human_player=None):
        """
        characters: list of 3 Character objects [Spiker, Setter, Defender].
        human_player: references user if this is Team.PLAYER.
        """
        self.characters = characters
        self.team = team
        self.difficulty = difficulty
        self.human_player = human_player  # Set if Team.PLAYER
        
        # Formation anchors (Wider court geometry)
        if self.team == Team.PLAYER:
            self.home_positions = [
                (0.0, -7.2),   # Pos 0 (User / Captain / Spiker)
                (-2.4, -2.6),  # Pos 1 (SETTER #2)
                (2.4, -2.6)    # Pos 2 (Wing / Blocker #4)
            ]
        else:
            self.home_positions = [
                (-2.2, 2.6),   # Pos 0 (SPIKER / Rival #1)
                (2.2, 2.6),    # Pos 1 (SETTER #3)
                (0.0, 7.2)     # Pos 2 (DEFENDER / Libero #6)
            ]
            
        self.spike_prep_done = [False, False, False]
        self.block_jump_done = False

    def set_difficulty(self, diff):
        self.difficulty = diff

    def reset_positions(self):
        for i, char in enumerate(self.characters):
            hx, hz = self.home_positions[i]
            char.reset_position(hx, hz)
        self.spike_prep_done = [False, False, False]
        self.block_jump_done = False

    def update(self, dt, ball, court, match_mgr):
        """Updates AI positioning, strict 3-touch coordination, and net blocking."""
        speed_mult = {
            AIDifficulty.EASY: 0.80,
            AIDifficulty.MEDIUM: 1.00,
            AIDifficulty.HARD: 1.20
        }.get(self.difficulty, 1.0)

        spike_speed = {
            AIDifficulty.EASY: 16.0,
            AIDifficulty.MEDIUM: 20.0,
            AIDifficulty.HARD: 24.0
        }.get(self.difficulty, 20.0)

        is_ball_on_my_side = (ball.z > 0.0) if self.team == Team.OPPONENT else (ball.z < 0.0)
        team_touches = match_mgr.get_touches(self.team)
        opp_touches = match_mgr.get_touches(Team.PLAYER if self.team == Team.OPPONENT else Team.OPPONENT)

        setter = self.characters[1]
        spiker = self.characters[0]
        defender = self.characters[2]

        # 1. NET BLOCKING (When ball is on opponent side and they are attacking)
        if not is_ball_on_my_side and ball.in_air:
            # Frontline player near net moves to shadow ball X
            blocker = self.characters[0] if abs(ball.x - self.characters[0].x) < abs(ball.x - self.characters[1].x) else self.characters[1]
            if blocker.is_ai:
                net_z = 1.0 if self.team == Team.OPPONENT else -1.0
                target_bx = max(-HALF_WIDTH + 1.0, min(HALF_WIDTH - 1.0, ball.x))
                dx = target_bx - blocker.x
                dz = net_z - blocker.z
                dist = math.sqrt(dx * dx + dz * dz)
                if dist > 0.15:
                    blocker.x += (dx / dist) * dt * 6.5 * speed_mult
                    blocker.z += (dz / dist) * dt * 6.5 * speed_mult

                # If opponent is spiking or ball is crossing net close to blocker: JUMP & BLOCK!
                if ball.y > 1.8 and abs(ball.z) < 2.5:
                    if blocker.is_grounded and not self.block_jump_done:
                        blocker.jump()
                        blocker.trigger_action(PlayerAction.BLOCK, 0.45)
                        self.block_jump_done = True
                elif blocker.is_grounded:
                    self.block_jump_done = False

        # 2. STRICT 3-TOUCH RESPONDER ASSIGNMENT
        target_char_idx = None
        if is_ball_on_my_side and ball.in_air and not ball.has_bounced:
            pred_x = max(-HALF_WIDTH + 0.5, min(HALF_WIDTH - 0.5, ball.predict_x))
            if self.team == Team.OPPONENT:
                pred_z = max(0.8, min(HALF_LENGTH - 0.8, ball.predict_z))
            else:
                pred_z = max(-HALF_LENGTH + 0.8, min(-0.8, ball.predict_z))

            # User Priority: Yield to human player if human is nearby
            user_taking_ball = False
            if self.human_player is not None:
                user_dist_to_landing = math.sqrt((self.human_player.x - pred_x)**2 + (self.human_player.z - pred_z)**2)
                if user_dist_to_landing < 2.5:
                    user_taking_ball = True

            if not user_taking_ball:
                if team_touches == 0:
                    # Touch 1 (Receive): Closest defender/receiver takes it
                    best_dist = 999.0
                    for i, char in enumerate(self.characters):
                        if char.is_ai:
                            d = math.sqrt((char.x - pred_x)**2 + (char.z - pred_z)**2)
                            if d < best_dist:
                                best_dist = d
                                target_char_idx = i

                elif team_touches == 1:
                    # Touch 2 (The Set): SETTER (Index 1) EXCLUSIVELY takes it!
                    if setter.is_ai:
                        target_char_idx = 1
                    else:
                        target_char_idx = 0  # If user is setter, teammate supports

                else:
                    # Touch 3 (The Attack): Designated SPIKER (Index 0) takes it!
                    if spiker.is_ai:
                        target_char_idx = 0
                    else:
                        target_char_idx = 2

        # 3. UPDATE EACH AI CHARACTER
        for i, char in enumerate(self.characters):
            if not char.is_ai:
                continue

            hx, hz = self.home_positions[i]

            # Tactical Desired Positioning
            if i == target_char_idx and is_ball_on_my_side and ball.in_air and not ball.has_bounced:
                # Responder runs directly to the ball landing spot!
                des_x = max(-HALF_WIDTH + 0.6, min(HALF_WIDTH - 0.6, ball.predict_x))
                if self.team == Team.OPPONENT:
                    des_z = max(0.8, min(HALF_LENGTH - 0.8, ball.predict_z))
                else:
                    des_z = max(-HALF_LENGTH + 0.8, min(-0.8, ball.predict_z))
            else:
                # Off-ball movement based on team touch phase:
                if is_ball_on_my_side:
                    if team_touches == 1 and i == 0:
                        # Spiker approaches attack zone near net while setter sets!
                        des_x = -2.2 if self.team == Team.OPPONENT else 2.2
                        des_z = 1.6 if self.team == Team.OPPONENT else -1.6
                    elif team_touches == 0 and i == 1:
                        # Setter moves towards center net preparing for receive pass
                        des_x = 1.8 if self.team == Team.OPPONENT else -1.8
                        des_z = 2.4 if self.team == Team.OPPONENT else -2.4
                    else:
                        des_x = hx
                        des_z = hz
                else:
                    des_x = hx
                    des_z = hz
                self.spike_prep_done[i] = False

            # Move towards destination
            dx = des_x - char.x
            dz = des_z - char.z
            dist_to_des = math.sqrt(dx * dx + dz * dz)

            move_x = 0.0
            move_z = 0.0
            if dist_to_des > 0.2:
                move_x = (dx / dist_to_des) * speed_mult
                move_z = (dz / dist_to_des) * speed_mult

            clamped_x, clamped_z = court.clamp_player_position(
                char.x + move_x * dt * 7.8,
                char.z + move_z * dt * 7.8,
                self.team
            )
            char.update(dt, move_x, move_z, look_target=(ball.x, ball.z))
            char.x = clamped_x
            char.z = clamped_z

            # 4. BALL CONTACT & EXECUTION (STRICT 3-TOUCH PIPELINE)
            if is_ball_on_my_side and ball.in_air and not ball.has_bounced and ball.can_be_hit_by(char):
                horiz_dist_ball = math.sqrt((ball.x - char.x)**2 + (ball.z - char.z)**2)

                # ==========================================
                # TOUCH 1: BUMP / DIG (RECEIVE -> SETTER)
                # ==========================================
                if team_touches == 0:
                    if horiz_dist_ball < 2.0 and 0.2 < ball.y < 3.2:
                        char.trigger_action(PlayerAction.BUMP, 0.35)
                        # Target is ALWAYS the Setter's position with high floaty arc!
                        tgt_x = setter.x
                        tgt_z = setter.z
                        ball.launch_arc(tgt_x, tgt_z, peak_height=6.0, hitter=char)
                        match_mgr.register_hit(self.team, char, "BUMP")
                        return

                # ==========================================
                # TOUCH 2: THE SET (SETTER -> SPIKER)
                # ==========================================
                elif team_touches == 1:
                    # Enforce Setter priority: only setter hits, or emergency fallback if ball is dropping low
                    is_setter = (char == setter)
                    emergency_hit = (ball.y < 1.2 and ball.time_to_impact < 0.25)
                    
                    if (is_setter or emergency_hit) and horiz_dist_ball < 2.2 and 0.3 < ball.y < 3.4:
                        char.trigger_action(PlayerAction.SET, 0.35)
                        # Target: High lofting set to the Spiker near the net!
                        if self.team == Team.PLAYER:
                            # Sets high for user player (or wing teammate if user is away)
                            tgt_x = self.human_player.x if self.human_player else 2.2
                            tgt_z = min(-1.4, self.human_player.z + 1.2) if self.human_player else -1.6
                        else:
                            tgt_x = spiker.x
                            tgt_z = 1.6
                        ball.launch_arc(tgt_x, tgt_z, peak_height=5.6, hitter=char)
                        match_mgr.register_hit(self.team, char, "SET")
                        return

                # ==========================================
                # TOUCH 3: THE ATTACK / SPIKE OVER THE NET!
                # ==========================================
                elif team_touches >= 2:
                    # Spiker jump preparation as set ball falls
                    if not self.spike_prep_done[i] and char.is_grounded:
                        if horiz_dist_ball < 2.4 and 2.2 < ball.y < 4.8 and ball.time_to_impact < 0.8:
                            char.jump()
                            self.spike_prep_done[i] = True

                    # IN-AIR SPIKE EXECUTION!
                    if not char.is_grounded and char.y > 0.45:
                        if horiz_dist_ball < 2.0 and abs(ball.y - (char.y + 1.6)) < 1.6:
                            char.trigger_action(PlayerAction.SPIKE, 0.35)
                            # Downward power spike directed at opponent court!
                            tgt_x = random.uniform(-HALF_WIDTH + 1.2, HALF_WIDTH - 1.2)
                            tgt_z = -6.8 if self.team == Team.OPPONENT else 6.8
                            ball.launch_arc(tgt_x, tgt_z, is_spike=True, spike_speed=spike_speed, hitter=char)
                            match_mgr.register_hit(self.team, char, "SPIKE")
                            self.spike_prep_done[i] = False
                            return

                    # Grounded Attack / Emergency Bump over the net if jump missed
                    elif char.is_grounded and horiz_dist_ball < 1.9 and 0.3 < ball.y < 3.0:
                        char.trigger_action(PlayerAction.BUMP, 0.35)
                        tgt_x = random.uniform(-HALF_WIDTH + 1.2, HALF_WIDTH - 1.2)
                        tgt_z = -6.5 if self.team == Team.OPPONENT else 6.5
                        ball.launch_arc(tgt_x, tgt_z, peak_height=4.8, hitter=char)
                        match_mgr.register_hit(self.team, char, "BUMP")
                        return
