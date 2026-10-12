"""
FlyHigh! - 3D Volleyball Game
Dynamic Team AI Controller (Supports 2v2, 3v3, 4v4, 5v5, 6v6)
Enforces authentic volleyball tactics & official FIVB regulations:
- Strict Rule: Blocking an opponent service is ILLEGAL (FIVB 14.1.3). AI NEVER attempts to block a serve!
- Touch 1 (Bump / Dig): Receiver lofts a high, floaty ball (6.0m peak) directly to the designated SETTER.
- Touch 2 (The Set): The SETTER delivers a high set (5.6m peak) for spikers to attack.
- Touch 3 (The Attack): Frontline Spikers approach the net, leap high, and spike into opponent court.
- In-Rally Net Blocking: Frontline players jump and block ONLY during genuine 3rd-touch opponent attacks!
"""
import math
import random
from constants import (
    Team, MatchState, PlayerAction, AIDifficulty, NET_HEIGHT
)

class TeamAIController:
    def __init__(self, characters, team=Team.OPPONENT, difficulty=AIDifficulty.MEDIUM, human_player=None):
        """
        characters: list of Character objects for this team (2 to 6 players).
        human_player: references user if this is Team.PLAYER.
        """
        self.characters = characters
        self.team = team
        self.difficulty = difficulty
        self.human_player = human_player  # Set if Team.PLAYER
        self.home_positions = []
        self.spike_prep_done = [False] * len(self.characters)
        self.block_jump_done = False

    def set_difficulty(self, diff):
        self.difficulty = diff

    def set_characters(self, characters, court=None):
        """Updates team character roster and recalculates formation anchors."""
        self.characters = characters
        self.spike_prep_done = [False] * len(self.characters)
        self.block_jump_done = False
        if court:
            self.recalculate_home_positions(court)

    def recalculate_home_positions(self, court):
        """Calculates tactical court anchors based on team size and court dimensions."""
        n = len(self.characters)
        hw = court.half_width
        hl = court.half_length
        z_sign = 1.0 if self.team == Team.OPPONENT else -1.0

        if n == 2:
            # 2v2 Beach: Pos 0 = Spiker/Blocker, Pos 1 = Setter/Defender
            self.home_positions = [
                (0.0, z_sign * hl * 0.35),
                (0.0, z_sign * hl * 0.75),
            ]
        elif n == 3:
            # 3v3 Arcade: Pos 0 = Spiker/Wing, Pos 1 = Setter, Pos 2 = Blocker/Defender
            self.home_positions = [
                (-hw * 0.45, z_sign * hl * 0.35),
                (hw * 0.45, z_sign * hl * 0.35),
                (0.0, z_sign * hl * 0.78),
            ]
        elif n == 4:
            # 4v4: 2 front, 2 back
            self.home_positions = [
                (-hw * 0.50, z_sign * hl * 0.32),
                (hw * 0.50, z_sign * hl * 0.32),
                (-hw * 0.40, z_sign * hl * 0.76),
                (hw * 0.40, z_sign * hl * 0.76),
            ]
        elif n == 5:
            # 5v5: 3 front, 2 back
            self.home_positions = [
                (-hw * 0.55, z_sign * hl * 0.30),
                (0.0, z_sign * hl * 0.30),
                (hw * 0.55, z_sign * hl * 0.30),
                (-hw * 0.45, z_sign * hl * 0.78),
                (hw * 0.45, z_sign * hl * 0.78),
            ]
        else:
            # 6v6 Classic Volleyball (3 front, 3 back)
            self.home_positions = [
                (-hw * 0.58, z_sign * hl * 0.30),  # Left Front (Outside Hitter)
                (0.0, z_sign * hl * 0.28),          # Center Front (Setter / Middle)
                (hw * 0.58, z_sign * hl * 0.30),   # Right Front (Opposite)
                (-hw * 0.55, z_sign * hl * 0.78),  # Left Back
                (0.0, z_sign * hl * 0.82),          # Center Back (Libero)
                (hw * 0.55, z_sign * hl * 0.78),   # Right Back (Server)
            ]
        self.spike_prep_done = [False] * n

    def reset_positions(self):
        for i, char in enumerate(self.characters):
            if i < len(self.home_positions):
                hx, hz = self.home_positions[i]
                char.reset_position(hx, hz)
        self.spike_prep_done = [False] * len(self.characters)
        self.block_jump_done = False

    def update(self, dt, ball, court, match_mgr):
        """Updates AI positioning, strict 3-touch coordination, and legal net blocking."""
        if not self.home_positions or len(self.home_positions) != len(self.characters):
            self.recalculate_home_positions(court)

        speed_mult = {
            AIDifficulty.EASY: 0.80,
            AIDifficulty.MEDIUM: 1.00,
            AIDifficulty.HARD: 1.22
        }.get(self.difficulty, 1.0)

        spike_speed = {
            AIDifficulty.EASY: 16.5,
            AIDifficulty.MEDIUM: 20.5,
            AIDifficulty.HARD: 24.5
        }.get(self.difficulty, 20.5)

        is_ball_on_my_side = (ball.z > 0.0) if self.team == Team.OPPONENT else (ball.z < 0.0)
        team_touches = match_mgr.get_touches(self.team)
        opp_touches = match_mgr.get_touches(Team.PLAYER if self.team == Team.OPPONENT else Team.OPPONENT)

        setter = self.characters[1] if len(self.characters) > 1 else self.characters[0]
        spiker = self.characters[0]

        # -------------------------------------------------------------
        # 1. NET BLOCKING
        # OFFICIAL FIVB RULE: BLOCKING A SERVE IS ILLEGAL!
        # AI MUST NEVER BLOCK A SERVE (opp_touches == 0 or state != IN_RALLY)
        # Only block during genuine opponent attacks (opp_touches >= 2)
        # -------------------------------------------------------------
        if not is_ball_on_my_side and ball.in_air and match_mgr.state == MatchState.IN_RALLY and opp_touches >= 2:
            # Find the best frontline blocker close to the net
            best_blocker = None
            min_bx_dist = 999.0
            for char in self.characters[:min(3, len(self.characters))]:
                if char.is_ai:
                    d = abs(ball.x - char.x)
                    if d < min_bx_dist:
                        min_bx_dist = d
                        best_blocker = char

            if best_blocker:
                net_z = 0.95 if self.team == Team.OPPONENT else -0.95
                target_bx = max(-court.half_width + 0.8, min(court.half_width - 0.8, ball.x))
                dx = target_bx - best_blocker.x
                dz = net_z - best_blocker.z
                dist = math.sqrt(dx * dx + dz * dz)
                if dist > 0.15:
                    best_blocker.x += (dx / dist) * dt * 7.0 * speed_mult
                    best_blocker.z += (dz / dist) * dt * 7.0 * speed_mult

                # If opponent is spiking or ball is crossing net close to blocker: JUMP & BLOCK!
                if ball.y > 1.85 and abs(ball.z) < 2.4:
                    if best_blocker.is_grounded and not self.block_jump_done:
                        best_blocker.jump()
                        best_blocker.trigger_action(PlayerAction.BLOCK, 0.45)
                        self.block_jump_done = True
                elif best_blocker.is_grounded:
                    self.block_jump_done = False

        # -------------------------------------------------------------
        # 2. STRICT 3-TOUCH RESPONDER ASSIGNMENT
        # -------------------------------------------------------------
        target_char_idx = None
        if is_ball_on_my_side and ball.in_air and not ball.has_bounced:
            pred_x = max(-court.half_width + 0.6, min(court.half_width - 0.6, ball.predict_x))
            if self.team == Team.OPPONENT:
                pred_z = max(0.8, min(court.half_length - 0.8, ball.predict_z))
            else:
                pred_z = max(-court.half_length + 0.8, min(-0.8, ball.predict_z))

            # User Priority: Yield to human player if human is nearby
            user_taking_ball = False
            if self.human_player is not None:
                user_dist_to_landing = math.sqrt((self.human_player.x - pred_x)**2 + (self.human_player.z - pred_z)**2)
                if user_dist_to_landing < 2.5:
                    user_taking_ball = True

            if not user_taking_ball:
                if team_touches == 0:
                    # Touch 1 (Receive): Closest player to landing takes it
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
                        target_char_idx = 0

                else:
                    # Touch 3 (The Attack): Designated Spiker or closest frontline spiker takes it!
                    if spiker.is_ai:
                        target_char_idx = 0
                    else:
                        target_char_idx = min(2, len(self.characters) - 1)

        # -------------------------------------------------------------
        # 3. UPDATE EACH AI CHARACTER IN ROSTER
        # -------------------------------------------------------------
        for i, char in enumerate(self.characters):
            if not char.is_ai:
                continue

            hx, hz = self.home_positions[i]

            # Tactical Desired Positioning
            if i == target_char_idx and is_ball_on_my_side and ball.in_air and not ball.has_bounced:
                des_x = max(-court.half_width + 0.6, min(court.half_width - 0.6, ball.predict_x))
                if self.team == Team.OPPONENT:
                    des_z = max(0.8, min(court.half_length - 0.8, ball.predict_z))
                else:
                    des_z = max(-court.half_length + 0.8, min(-0.8, ball.predict_z))
            else:
                # Off-ball tactical positioning
                if is_ball_on_my_side:
                    if team_touches == 1 and i == 0:
                        # Spiker approaches attack zone near net
                        des_x = -court.half_width * 0.35 if self.team == Team.OPPONENT else court.half_width * 0.35
                        des_z = 1.6 if self.team == Team.OPPONENT else -1.6
                    elif team_touches == 0 and i == 1:
                        # Setter positions near net preparing for the receive
                        des_x = court.half_width * 0.25 if self.team == Team.OPPONENT else -court.half_width * 0.25
                        des_z = 2.2 if self.team == Team.OPPONENT else -2.2
                    else:
                        des_x = hx
                        des_z = hz
                else:
                    des_x = hx
                    des_z = hz
                if i < len(self.spike_prep_done):
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

            # -------------------------------------------------------------
            # 4. BALL CONTACT & EXECUTION (STRICT 3-TOUCH PIPELINE)
            # -------------------------------------------------------------
            if is_ball_on_my_side and ball.in_air and not ball.has_bounced and ball.can_be_hit_by(char):
                horiz_dist_ball = math.sqrt((ball.x - char.x)**2 + (ball.z - char.z)**2)

                # TOUCH 1: BUMP / DIG (RECEIVE -> SETTER)
                if team_touches == 0:
                    if horiz_dist_ball < 2.0 and 0.2 < ball.y < 3.2:
                        char.trigger_action(PlayerAction.BUMP, 0.35)
                        tgt_x = setter.x
                        tgt_z = setter.z
                        ball.launch_arc(tgt_x, tgt_z, peak_height=6.0, hitter=char)
                        match_mgr.register_hit(self.team, char, "BUMP")
                        return

                # TOUCH 2: THE SET (SETTER -> SPIKER)
                elif team_touches == 1:
                    is_setter = (char == setter)
                    emergency_hit = (ball.y < 1.2 and ball.time_to_impact < 0.25)

                    if (is_setter or emergency_hit) and horiz_dist_ball < 2.2 and 0.3 < ball.y < 3.4:
                        char.trigger_action(PlayerAction.SET, 0.35)
                        if self.team == Team.PLAYER:
                            tgt_x = self.human_player.x if self.human_player else 2.2
                            tgt_z = min(-1.4, self.human_player.z + 1.2) if self.human_player else -1.6
                        else:
                            tgt_x = spiker.x
                            tgt_z = 1.6
                        ball.launch_arc(tgt_x, tgt_z, peak_height=5.6, hitter=char)
                        match_mgr.register_hit(self.team, char, "SET")
                        return

                # TOUCH 3: THE ATTACK / SPIKE OVER THE NET!
                elif team_touches >= 2:
                    if i < len(self.spike_prep_done) and not self.spike_prep_done[i] and char.is_grounded:
                        if horiz_dist_ball < 2.4 and 2.2 < ball.y < 4.8 and ball.time_to_impact < 0.8:
                            char.jump()
                            self.spike_prep_done[i] = True

                    # In-air spike execution
                    if not char.is_grounded and char.y > 0.45:
                        if horiz_dist_ball < 2.0 and abs(ball.y - (char.y + 1.6)) < 1.6:
                            char.trigger_action(PlayerAction.SPIKE, 0.35)
                            tgt_x = random.uniform(-court.half_width + 1.2, court.half_width - 1.2)
                            tgt_z = -court.half_length * 0.75 if self.team == Team.OPPONENT else court.half_length * 0.75
                            ball.launch_arc(tgt_x, tgt_z, is_spike=True, spike_speed=spike_speed, hitter=char)
                            match_mgr.register_hit(self.team, char, "SPIKE")
                            if i < len(self.spike_prep_done):
                                self.spike_prep_done[i] = False
                            return

                    # Grounded emergency bump over net if jump missed
                    elif char.is_grounded and horiz_dist_ball < 1.9 and 0.3 < ball.y < 3.0:
                        char.trigger_action(PlayerAction.BUMP, 0.35)
                        tgt_x = random.uniform(-court.half_width + 1.2, court.half_width - 1.2)
                        tgt_z = -court.half_length * 0.70 if self.team == Team.OPPONENT else court.half_length * 0.70
                        ball.launch_arc(tgt_x, tgt_z, peak_height=4.8, hitter=char)
                        match_mgr.register_hit(self.team, char, "BUMP")
                        return
