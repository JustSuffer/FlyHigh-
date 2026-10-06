"""
FlyHigh! - 3D Volleyball Game
AI Controller for Opponents and Teammate Bots
Provides authentic volleyball rally intelligence (bump, set, spike) and difficulty tuning.
"""
import math
import random
from constants import (
    Team, PlayerAction, AIDifficulty, HALF_WIDTH, HALF_LENGTH, NET_HEIGHT
)

class AIController:
    def __init__(self, character, difficulty=AIDifficulty.MEDIUM):
        self.character = character
        self.difficulty = difficulty
        self.team = character.team
        
        # Base defensive home position
        self.home_x = 0.0
        self.home_z = 5.5 if self.team == Team.OPPONENT else -5.5
        
        # Internal timers
        self.reaction_timer = 0.0
        self.target_x = self.home_x
        self.target_z = self.home_z
        self.has_jumped_for_spike = False

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty

    def update(self, dt, ball, court, match_mgr):
        """Calculates AI movement and actions based on volleyball rally flow."""
        char = self.character
        
        # Speed multiplier based on difficulty
        speed_mult = {
            AIDifficulty.EASY: 0.75,
            AIDifficulty.MEDIUM: 0.95,
            AIDifficulty.HARD: 1.15
        }.get(self.difficulty, 1.0)

        # Spike speed based on difficulty
        spike_speed = {
            AIDifficulty.EASY: 14.0,
            AIDifficulty.MEDIUM: 18.0,
            AIDifficulty.HARD: 22.0
        }.get(self.difficulty, 18.0)

        # 1. Determine target location
        is_ball_on_my_side = (ball.z > 0.0) if self.team == Team.OPPONENT else (ball.z < 0.0)
        
        if is_ball_on_my_side and ball.in_air and not ball.has_bounced:
            # Ball is on AI's half: Rush to predicted landing location!
            pred_x = max(-HALF_WIDTH + 0.4, min(HALF_WIDTH - 0.4, ball.predict_x))
            
            if self.team == Team.OPPONENT:
                pred_z = max(0.6, min(HALF_LENGTH - 0.4, ball.predict_z))
            else:
                pred_z = max(-HALF_LENGTH + 0.4, min(-0.6, ball.predict_z))
                
            self.target_x = pred_x
            self.target_z = pred_z
        else:
            # Ball is on opponent side: reposition to defensive base
            self.target_x = self.home_x
            self.target_z = self.home_z
            self.has_jumped_for_spike = False

        # 2. Movement towards target
        dx = self.target_x - char.x
        dz = self.target_z - char.z
        dist_to_target = math.sqrt(dx * dx + dz * dz)

        move_x = 0.0
        move_z = 0.0
        if dist_to_target > 0.2:
            move_x = (dx / dist_to_target) * speed_mult
            move_z = (dz / dist_to_target) * speed_mult

        # Clamp inside court legal bounds
        clamped_x, clamped_z = court.clamp_player_position(
            char.x + move_x * dt * 7.5,
            char.z + move_z * dt * 7.5,
            self.team
        )
        # Update character with calculated movement and look target (ball)
        char.update(dt, move_x, move_z, look_target=(ball.x, ball.z))

        # 3. Ball interaction logic
        dist_to_ball = char.dist_to_ball(ball)
        horiz_dist_ball = math.sqrt((ball.x - char.x) ** 2 + (ball.z - char.z) ** 2)

        # Only interact if ball is on AI side or within reach near net
        if is_ball_on_my_side and ball.in_air and not ball.has_bounced:
            team_touches = match_mgr.get_touches(self.team)

            # Option A: SPIKE / ATTACK (Touch 3 or aggressive touch 2 near net)
            if (team_touches >= 2 or (team_touches >= 1 and abs(char.z) < 2.5)) and not self.has_jumped_for_spike:
                # Time approach jump when ball is descending toward net
                if horiz_dist_ball < 1.8 and 2.2 < ball.y < 3.8 and ball.time_to_impact < 0.6:
                    char.jump()
                    self.has_jumped_for_spike = True

            # If in air near peak: execute SPIKE!
            if not char.is_grounded and char.y > 0.6:
                if horiz_dist_ball < 1.6 and abs(ball.y - (char.y + 1.6)) < 1.2:
                    char.trigger_action(PlayerAction.SPIKE, 0.3)
                    # Pick an offensive target spot on player's court
                    target_spike_x = random.choice([-2.8, 0.0, 2.8])
                    target_spike_z = -5.5 + random.uniform(-2.0, 2.0)
                    
                    ball.launch_arc(target_spike_x, target_spike_z, is_spike=True, spike_speed=spike_speed)
                    match_mgr.register_hit(self.team, char, "SPIKE")
                    self.has_jumped_for_spike = False
                    return

            # Option B: BUMP / DIG (Receive)
            if char.is_grounded and horiz_dist_ball < 1.6 and 0.4 < ball.y < 2.4:
                if team_touches == 0:
                    # Bump high into setter zone near net (Z = 2.0)
                    char.trigger_action(PlayerAction.BUMP, 0.35)
                    set_target_x = 0.0
                    set_target_z = 2.0 if self.team == Team.OPPONENT else -2.0
                    ball.launch_arc(set_target_x, set_target_z, peak_height=4.2)
                    match_mgr.register_hit(self.team, char, "BUMP")
                    return
                elif team_touches == 1:
                    # Set up high for spike
                    char.trigger_action(PlayerAction.SET, 0.35)
                    spike_setup_x = random.choice([-1.8, 1.8])
                    spike_setup_z = 1.2 if self.team == Team.OPPONENT else -1.2
                    ball.launch_arc(spike_setup_x, spike_setup_z, peak_height=3.8)
                    match_mgr.register_hit(self.team, char, "SET")
                    return
                else:
                    # Final touch return: push deep into player court
                    char.trigger_action(PlayerAction.BUMP, 0.35)
                    ret_x = random.uniform(-3.0, 3.0)
                    ret_z = -7.0 if self.team == Team.OPPONENT else 7.0
                    ball.launch_arc(ret_x, ret_z, peak_height=3.5)
                    match_mgr.register_hit(self.team, char, "BUMP")
                    return
