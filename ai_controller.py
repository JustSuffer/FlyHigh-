"""
FlyHigh! - 3D Volleyball Game
3v3 Team AI Controller
Coordinates 3-player squads on both sides:
- Tactical triangle formations (Defender, Setter, Spiker)
- Player Priority: AI teammates yield to the human player when in range
- Authentic 3-touch flow (Bump to setter -> High floating set -> Explosive spike!)
"""
import math
import random
from constants import (
    Team, PlayerAction, AIDifficulty, HALF_WIDTH, HALF_LENGTH, NET_HEIGHT
)

class TeamAIController:
    def __init__(self, characters, team=Team.OPPONENT, difficulty=AIDifficulty.MEDIUM, human_player=None):
        """
        characters: list of 3 Character objects on this team.
        human_player: if this is Team.PLAYER, references the user-controlled character.
        """
        self.characters = characters
        self.team = team
        self.difficulty = difficulty
        self.human_player = human_player  # Set if Team.PLAYER
        
        # Base formation anchors (Triangle layout)
        if self.team == Team.PLAYER:
            self.home_positions = [
                (0.0, -6.8),   # Pos 0 (User / Defender)
                (-2.2, -2.5),  # Pos 1 (Setter)
                (2.2, -2.5)    # Pos 2 (Wing / Blocker)
            ]
        else:
            self.home_positions = [
                (-2.0, 2.5),   # Pos 0 (Spiker)
                (2.0, 2.5),    # Pos 1 (Setter)
                (0.0, 6.8)     # Pos 2 (Defender)
            ]
            
        self.spike_prep_done = [False, False, False]

    def set_difficulty(self, diff):
        self.difficulty = diff

    def reset_positions(self):
        for i, char in enumerate(self.characters):
            hx, hz = self.home_positions[i]
            char.reset_position(hx, hz)
        self.spike_prep_done = [False, False, False]

    def update(self, dt, ball, court, match_mgr):
        """Updates AI positioning and actions for all AI-controlled characters on this team."""
        speed_mult = {
            AIDifficulty.EASY: 0.75,
            AIDifficulty.MEDIUM: 0.95,
            AIDifficulty.HARD: 1.15
        }.get(self.difficulty, 1.0)

        spike_speed = {
            AIDifficulty.EASY: 15.0,
            AIDifficulty.MEDIUM: 19.0,
            AIDifficulty.HARD: 23.0
        }.get(self.difficulty, 19.0)

        is_ball_on_my_side = (ball.z > 0.0) if self.team == Team.OPPONENT else (ball.z < 0.0)
        team_touches = match_mgr.get_touches(self.team)

        # 1. Determine which player should be the primary ball responder
        target_char_idx = None
        if is_ball_on_my_side and ball.in_air and not ball.has_bounced:
            pred_x = max(-HALF_WIDTH + 0.4, min(HALF_WIDTH - 0.4, ball.predict_x))
            if ball.is_float and self.difficulty != AIDifficulty.HARD:
                # Knuckleball wobbles in the air, creating slight reception misjudgment!
                pred_x += random.uniform(-0.5, 0.5)
            if self.team == Team.OPPONENT:
                pred_z = max(0.5, min(HALF_LENGTH - 0.5, ball.predict_z))
            else:
                pred_z = max(-HALF_LENGTH + 0.5, min(-0.5, ball.predict_z))

            # If user is on this team, check if user is close (User Priority!)
            user_taking_ball = False
            if self.human_player is not None:
                user_dist_to_landing = math.sqrt((self.human_player.x - pred_x)**2 + (self.human_player.z - pred_z)**2)
                if user_dist_to_landing < 2.6:
                    user_taking_ball = True  # Yield to the human player!

            if not user_taking_ball:
                # Find closest AI character to the landing spot
                best_dist = 999.0
                for i, char in enumerate(self.characters):
                    if char.is_ai:
                        d = math.sqrt((char.x - pred_x)**2 + (char.z - pred_z)**2)
                        # Preference for role based on touches
                        if team_touches == 1 and i == 1: # Setter gets priority on 2nd touch
                            d *= 0.6
                        if d < best_dist:
                            best_dist = d
                            target_char_idx = i

        # 2. Update each character
        for i, char in enumerate(self.characters):
            if not char.is_ai:
                continue  # User is handled by input manager

            hx, hz = self.home_positions[i]

            # Determine desired target for this character
            if i == target_char_idx and is_ball_on_my_side and ball.in_air and not ball.has_bounced:
                # Run to ball landing zone!
                des_x = max(-HALF_WIDTH + 0.5, min(HALF_WIDTH - 0.5, ball.predict_x))
                if self.team == Team.OPPONENT:
                    des_z = max(0.5, min(HALF_LENGTH - 0.5, ball.predict_z))
                else:
                    des_z = max(-HALF_LENGTH + 0.5, min(-0.5, ball.predict_z))
            else:
                # Defensive support / return to formation
                des_x = hx
                des_z = hz
                self.spike_prep_done[i] = False

            # Move towards desired target
            dx = des_x - char.x
            dz = des_z - char.z
            dist_to_des = math.sqrt(dx * dx + dz * dz)

            move_x = 0.0
            move_z = 0.0
            if dist_to_des > 0.2:
                move_x = (dx / dist_to_des) * speed_mult
                move_z = (dz / dist_to_des) * speed_mult

            # Clamping
            clamped_x, clamped_z = court.clamp_player_position(
                char.x + move_x * dt * 7.5,
                char.z + move_z * dt * 7.5,
                self.team
            )
            char.update(dt, move_x, move_z, look_target=(ball.x, ball.z))
            char.x = clamped_x
            char.z = clamped_z

            # 3. Ball Interaction if this AI reaches the ball
            if is_ball_on_my_side and ball.in_air and not ball.has_bounced and ball.can_be_hit_by(char):
                horiz_dist_ball = math.sqrt((ball.x - char.x)**2 + (ball.z - char.z)**2)

                # A. SPIKE / ATTACK PREP (Touch 3, or aggressive touch 2 near net)
                if (team_touches >= 2 or (team_touches >= 1 and abs(char.z) < 2.8)) and not self.spike_prep_done[i]:
                    if horiz_dist_ball < 2.2 and 2.0 < ball.y < 4.2 and ball.time_to_impact < 0.8:
                        char.jump()
                        self.spike_prep_done[i] = True

                # In-Air: EXECUTE SPIKE!
                if not char.is_grounded and char.y > 0.45:
                    if horiz_dist_ball < 1.8 and abs(ball.y - (char.y + 1.6)) < 1.4:
                        char.trigger_action(PlayerAction.SPIKE, 0.35)
                        # Aim spike towards open spaces in the other court
                        target_x = random.choice([-2.8, 0.0, 2.8])
                        target_z = -5.8 + random.uniform(-2.0, 1.5) if self.team == Team.OPPONENT else 5.8 + random.uniform(-1.5, 2.0)
                        ball.launch_arc(target_x, target_z, is_spike=True, spike_speed=spike_speed, hitter=char)
                        match_mgr.register_hit(self.team, char, "SPIKE")
                        self.spike_prep_done[i] = False
                        return

                # Grounded Interactions (Authentic 3-Touch Flow)
                if char.is_grounded and horiz_dist_ball < 1.8 and 0.3 < ball.y < 2.8:
                    if team_touches == 0:
                        # TOUCH 1: BUMP / DIG (Receive) -> High float to setter near net
                        char.trigger_action(PlayerAction.BUMP, 0.35)
                        setter_x = -1.8 if self.team == Team.PLAYER else 1.8
                        setter_z = -2.2 if self.team == Team.PLAYER else 2.2
                        ball.launch_arc(setter_x, setter_z, peak_height=5.2, hitter=char)
                        match_mgr.register_hit(self.team, char, "BUMP")
                        return

                    elif team_touches == 1:
                        # TOUCH 2: SET / PASS -> High lofting set for spiker
                        char.trigger_action(PlayerAction.SET, 0.35)
                        spiker_x = 1.8 if self.team == Team.PLAYER else -1.8
                        spiker_z = -1.4 if self.team == Team.PLAYER else 1.4
                        ball.launch_arc(spiker_x, spiker_z, peak_height=4.8, hitter=char)
                        match_mgr.register_hit(self.team, char, "SET")
                        return

                    else:
                        # TOUCH 3: MUST CLEAR OVER THE NET! Deep attack into opposite court
                        char.trigger_action(PlayerAction.BUMP, 0.35)
                        ret_x = random.uniform(-2.5, 2.5)
                        ret_z = -6.5 if self.team == Team.OPPONENT else 6.5
                        ball.launch_arc(ret_x, ret_z, peak_height=4.6, hitter=char)
                        match_mgr.register_hit(self.team, char, "BUMP")
                        return
