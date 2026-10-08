"""
FlyHigh! - 3D Volleyball Game
Match & Volleyball Rules Engine
Handles serves, 3-touch regulations, boundary & net collision scoring,
rotation, set points, and celebratory transitions.
"""
from constants import (
    Team, MatchState, PlayerAction, HALF_WIDTH, HALF_LENGTH
)

class MatchManager:
    def __init__(self, audio_mgr=None, points_to_win=11):
        self.audio_mgr = audio_mgr
        self.points_to_win = points_to_win
        
        # State
        self.state = MatchState.TITLE_SCREEN
        self.serving_team = Team.PLAYER
        self.serving_player = None
        
        # Scores
        self.score_player = 0
        self.score_opponent = 0
        self.sets_player = 0
        self.sets_opponent = 0
        self.current_set = 1
        
        # Rallies and touches
        self.touches_player = 0
        self.touches_opponent = 0
        self.last_touch_team = None
        self.last_touch_player = None
        
        # Timers
        self.state_timer = 0.0
        self.point_reason = ""
        self.point_winner = None
        self.winner = None

    def reset_match(self):
        self.score_player = 0
        self.score_opponent = 0
        self.sets_player = 0
        self.sets_opponent = 0
        self.current_set = 1
        self.serving_team = Team.PLAYER
        self.winner = None
        self.start_serve_phase()

    def start_serve_phase(self):
        self.state = MatchState.SERVE_READY
        self.touches_player = 0
        self.touches_opponent = 0
        self.last_touch_team = None
        self.last_touch_player = None
        self.point_reason = ""
        self.point_winner = None
        self.state_timer = 0.0

    def get_touches(self, team):
        return self.touches_player if team == Team.PLAYER else self.touches_opponent

    def register_hit(self, team, player, hit_type="BUMP"):
        """Called whenever a player contacts the ball."""
        if team == Team.PLAYER:
            self.touches_player += 1
            self.touches_opponent = 0  # Opponent touches reset
        else:
            self.touches_opponent += 1
            self.touches_player = 0

        self.last_touch_team = team
        self.last_touch_player = player

        # Audio feedback
        if self.audio_mgr:
            if hit_type == "SPIKE":
                self.audio_mgr.play("hit_spike")
            elif hit_type == "SET":
                self.audio_mgr.play("hit_set")
            else:
                self.audio_mgr.play("hit_bump")

        # Check 4-touch fault
        touches = self.get_touches(team)
        if touches > 3:
            other_team = Team.OPPONENT if team == Team.PLAYER else Team.PLAYER
            self.award_point(other_team, "4 Touches Fault!")

    def award_point(self, winner_team, reason=""):
        if self.state == MatchState.POINT_SCORED or self.state == MatchState.MATCH_OVER:
            return

        self.point_winner = winner_team
        self.point_reason = reason
        self.state = MatchState.POINT_SCORED
        self.state_timer = 2.0  # Duration of point banner
        
        if winner_team == Team.PLAYER:
            self.score_player += 1
            self.serving_team = Team.PLAYER
        else:
            self.score_opponent += 1
            self.serving_team = Team.OPPONENT

        if self.audio_mgr:
            self.audio_mgr.play("whistle")
            self.audio_mgr.play("point")
            self.audio_mgr.play("cheer")

        # Check Match Victory
        if self.score_player >= self.points_to_win and (self.score_player - self.score_opponent) >= 2:
            self.winner = Team.PLAYER
            self.state = MatchState.MATCH_OVER
        elif self.score_opponent >= self.points_to_win and (self.score_opponent - self.score_player) >= 2:
            self.winner = Team.OPPONENT
            self.state = MatchState.MATCH_OVER

    def update(self, dt, ball, court):
        """Monitors ball position, bounces, out-of-bounds, and phase timers."""
        if self.state == MatchState.POINT_SCORED:
            self.state_timer -= dt
            if self.state_timer <= 0.0:
                self.start_serve_phase()
            return

        if self.state == MatchState.IN_RALLY:
            # 1. Did the ball bounce on the floor?
            if ball.has_bounced:
                is_in = court.is_in_bounds(ball.x, ball.z)
                ball_on_player_side = ball.z < 0.0
                
                if is_in:
                    # Ball landed IN! Point goes to the opposite side of where it landed
                    if ball_on_player_side:
                        if self.last_touch_team == Team.OPPONENT and self.touches_player == 0:
                            self.award_point(Team.OPPONENT, "SERVICE ACE!")
                        else:
                            self.award_point(Team.OPPONENT, "In Bounds!")
                    else:
                        if self.last_touch_team == Team.PLAYER and self.touches_opponent == 0:
                            self.award_point(Team.PLAYER, "SERVICE ACE!")
                        else:
                            self.award_point(Team.PLAYER, "In Bounds!")
                else:
                    # Ball landed OUT! Point goes to defending team (opposite of last hitter)
                    if self.last_touch_team == Team.PLAYER:
                        self.award_point(Team.OPPONENT, "Out of Bounds!")
                    elif self.last_touch_team == Team.OPPONENT:
                        self.award_point(Team.PLAYER, "Out of Bounds!")
                    else:
                        self.award_point(Team.PLAYER if ball_on_player_side else Team.OPPONENT, "Out of Bounds!")

            # 2. Check if ball dropped too far out
            if abs(ball.x) > 9.0 or abs(ball.z) > 14.0 or ball.y < -1.0:
                if self.last_touch_team == Team.PLAYER:
                    self.award_point(Team.OPPONENT, "Out of Bounds!")
                else:
                    self.award_point(Team.PLAYER, "Out of Bounds!")
