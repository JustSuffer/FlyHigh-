"""
FlyHigh! - 3D Volleyball Game
2D Arcade UI & HUD Renderer
Displays sleek glassmorphic scoreboard, touch counter, aim reticle,
gamepad/keyboard control hints, and victory/pause dialogs.
"""
import pyray as pr
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, Team, MatchState
)

# UI Colors
COLOR_HUD_BG       = pr.Color(20, 24, 34, 220)
COLOR_HUD_BORDER   = pr.Color(60, 70, 95, 255)
COLOR_TEXT_WHITE   = pr.Color(245, 245, 250, 255)
COLOR_TEXT_GOLD    = pr.Color(255, 215, 0, 255)
COLOR_PLAYER_BLUE  = pr.Color(45, 140, 235, 255)
COLOR_OPPONENT_RED = pr.Color(235, 55, 55, 255)
COLOR_BANNER_BG    = pr.Color(15, 18, 25, 235)

class UIRenderer:
    def __init__(self):
        pass

    def draw_hud(self, match_mgr, input_mgr, cam_ctrl, ai_difficulty):
        """Draws top scoreboard, touch counter, and bottom control prompts."""
        # 1. Top Scoreboard
        bar_w = 460
        bar_h = 60
        bar_x = (SCREEN_WIDTH - bar_w) // 2
        bar_y = 15

        # Background
        pr.draw_rectangle_rounded(pr.Rectangle(bar_x, bar_y, bar_w, bar_h), 0.35, 8, COLOR_HUD_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bar_x, bar_y, bar_w, bar_h), 0.35, 8, 2, COLOR_HUD_BORDER)

        # Player side (Left)
        p_name = "YOU"
        p_score = f"{match_mgr.score_player:02d}"
        pr.draw_text(p_name, bar_x + 25, bar_y + 12, 16, COLOR_PLAYER_BLUE)
        pr.draw_text(p_score, bar_x + 95, bar_y + 8, 38, COLOR_PLAYER_BLUE)
        if match_mgr.serving_team == Team.PLAYER:
            pr.draw_circle(bar_x + 15, bar_y + 20, 4, COLOR_TEXT_GOLD)

        # Center Divider & Target Points
        pr.draw_text("VS", bar_x + bar_w // 2 - 12, bar_y + 12, 18, pr.GRAY)
        target_str = f"TO {match_mgr.points_to_win}"
        pr.draw_text(target_str, bar_x + bar_w // 2 - 18, bar_y + 36, 12, COLOR_TEXT_GOLD)

        # Opponent side (Right)
        o_name = "CPU"
        o_score = f"{match_mgr.score_opponent:02d}"
        pr.draw_text(o_score, bar_x + bar_w - 140, bar_y + 8, 38, COLOR_OPPONENT_RED)
        pr.draw_text(o_name, bar_x + bar_w - 65, bar_y + 12, 16, COLOR_OPPONENT_RED)
        if match_mgr.serving_team == Team.OPPONENT:
            pr.draw_circle(bar_x + bar_w - 75, bar_y + 20, 4, COLOR_TEXT_GOLD)

        # 2. Touch Counter Badge (Shows active team's touches)
        if match_mgr.state == MatchState.IN_RALLY:
            touches = match_mgr.get_touches(Team.PLAYER)
            badge_w = 200
            badge_h = 36
            bx = (SCREEN_WIDTH - badge_w) // 2
            by = bar_y + bar_h + 10

            pr.draw_rectangle_rounded(pr.Rectangle(bx, by, badge_w, badge_h), 0.4, 6, COLOR_HUD_BG)
            
            # Touch label
            touch_txt = f"TOUCH: {touches}/3"
            if touches == 0:
                t_sub = "READY"
                col = COLOR_TEXT_WHITE
            elif touches == 1:
                t_sub = "BUMP"
                col = COLOR_PLAYER_BLUE
            elif touches == 2:
                t_sub = "SET"
                col = COLOR_TEXT_GOLD
            else:
                t_sub = "SPIKE!"
                col = pr.Color(255, 80, 80, 255)

            full_touch_str = f"{touch_txt} ({t_sub})"
            tw = pr.measure_text(full_touch_str, 16)
            pr.draw_text(full_touch_str, bx + (badge_w - tw) // 2, by + 10, 16, col)

        # 3. Bottom Control Helper Bar
        bot_h = 42
        bot_y = SCREEN_HEIGHT - bot_h - 10
        bot_w = SCREEN_WIDTH - 60
        bot_x = 30

        pr.draw_rectangle_rounded(pr.Rectangle(bot_x, bot_y, bot_w, bot_h), 0.3, 6, pr.Color(15, 18, 25, 200))
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bot_x, bot_y, bot_w, bot_h), 0.3, 6, 1, COLOR_HUD_BORDER)

        # Context-aware controls string
        device = input_mgr.active_device
        if device == "GAMEPAD":
            ctrl_str = "[L-STICK] Move | (A) Jump / Spike | (X) Bump | (Y) Set | (RB) Dive | (BACK) Camera | (START) Pause"
        else:
            ctrl_str = "[WASD] Move | [SPACE] Jump / Spike | [J] Bump | [K] Set | [SHIFT] Dive | [TAB] Camera | [ESC] Pause"

        pr.draw_text(f"DEVICE: {device}", bot_x + 16, bot_y + 13, 13, COLOR_TEXT_GOLD)
        pr.draw_text(ctrl_str, bot_x + 180, bot_y + 13, 14, COLOR_TEXT_WHITE)

        # Camera Mode indicator top-left
        cam_info = f"CAM: {cam_ctrl.get_mode_name()} [TAB/(BACK)]"
        pr.draw_text(cam_info, 20, 20, 13, pr.Color(200, 210, 225, 200))
        # Difficulty indicator top-right
        diff_info = f"AI: {ai_difficulty.value}"
        dw = pr.measure_text(diff_info, 13)
        pr.draw_text(diff_info, SCREEN_WIDTH - dw - 20, 20, 13, pr.Color(200, 210, 225, 200))

    def draw_serve_prompt(self, match_mgr, input_mgr):
        """Displays intuitive serve prompt."""
        if match_mgr.state == MatchState.SERVE_READY:
            card_w = 420
            card_h = 55
            cx = (SCREEN_WIDTH - card_w) // 2
            cy = 140

            pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, COLOR_BANNER_BG)
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, 2, COLOR_TEXT_GOLD)

            if match_mgr.serving_team == Team.PLAYER:
                prompt_btn = input_mgr.get_prompt_text("JUMP")
                txt = f"YOUR SERVE: Press {prompt_btn} to Toss & Hit!"
                col = COLOR_TEXT_GOLD
            else:
                txt = "OPPONENT SERVING... Get Ready!"
                col = COLOR_OPPONENT_RED

            tw = pr.measure_text(txt, 18)
            pr.draw_text(txt, cx + (card_w - tw) // 2, cy + 18, 18, col)

    def draw_point_banner(self, match_mgr):
        """Displays animated celebratory banner when a point is scored."""
        if match_mgr.state == MatchState.POINT_SCORED:
            banner_w = 540
            banner_h = 95
            bx = (SCREEN_WIDTH - banner_w) // 2
            by = SCREEN_HEIGHT // 2 - 100

            pr.draw_rectangle_rounded(pr.Rectangle(bx, by, banner_w, banner_h), 0.3, 8, COLOR_BANNER_BG)
            winner_col = COLOR_PLAYER_BLUE if match_mgr.point_winner == Team.PLAYER else COLOR_OPPONENT_RED
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bx, by, banner_w, banner_h), 0.3, 8, 3, winner_col)

            win_title = "POINT FOR YOU!" if match_mgr.point_winner == Team.PLAYER else "POINT FOR CPU!"
            tw1 = pr.measure_text(win_title, 28)
            pr.draw_text(win_title, bx + (banner_w - tw1) // 2, by + 16, 28, winner_col)

            reason_str = match_mgr.point_reason
            tw2 = pr.measure_text(reason_str, 18)
            pr.draw_text(reason_str, bx + (banner_w - tw2) // 2, by + 56, 18, COLOR_TEXT_WHITE)

    def draw_match_over(self, match_mgr, input_mgr):
        """Draws victorious match end celebration screen."""
        if match_mgr.state == MatchState.MATCH_OVER:
            # Darkened backdrop
            pr.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, pr.Color(10, 12, 18, 220))

            card_w = 560
            card_h = 280
            cx = (SCREEN_WIDTH - card_w) // 2
            cy = (SCREEN_HEIGHT - card_h) // 2

            pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, COLOR_HUD_BG)
            win_col = COLOR_TEXT_GOLD if match_mgr.winner == Team.PLAYER else COLOR_OPPONENT_RED
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, 3, win_col)

            main_text = "MATCH VICTORY!" if match_mgr.winner == Team.PLAYER else "MATCH DEFEAT"
            tw = pr.measure_text(main_text, 36)
            pr.draw_text(main_text, cx + (card_w - tw) // 2, cy + 30, 36, win_col)

            # Final Score line
            score_text = f"Final Score: YOU {match_mgr.score_player} - {match_mgr.score_opponent} CPU"
            sw = pr.measure_text(score_text, 22)
            pr.draw_text(score_text, cx + (card_w - sw) // 2, cy + 95, 22, COLOR_TEXT_WHITE)

            # Rematch prompt
            prompt_btn = input_mgr.get_prompt_text("JUMP")
            rematch_text = f"Press {prompt_btn} to PLAY AGAIN"
            rw = pr.measure_text(rematch_text, 20)
            pr.draw_text(rematch_text, cx + (card_w - rw) // 2, cy + 160, 20, COLOR_TEXT_GOLD)

            quit_text = "Press [ESC] / (START) to Quit"
            qw = pr.measure_text(quit_text, 16)
            pr.draw_text(quit_text, cx + (card_w - qw) // 2, cy + 215, 16, pr.GRAY)

    def draw_pause_menu(self, input_mgr):
        """Draws Pause / Settings overlay."""
        pr.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, pr.Color(10, 12, 18, 190))
        
        card_w = 460
        card_h = 260
        cx = (SCREEN_WIDTH - card_w) // 2
        cy = (SCREEN_HEIGHT - card_h) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, COLOR_HUD_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, 2, COLOR_HUD_BORDER)

        pr.draw_text("GAME PAUSED", cx + 130, cy + 25, 28, COLOR_TEXT_WHITE)
        pr.draw_text("Press [ESC] / (START) to Resume", cx + 80, cy + 85, 18, COLOR_TEXT_GOLD)
        pr.draw_text("Press [TAB] / (BACK) to Cycle Camera", cx + 80, cy + 125, 18, COLOR_TEXT_WHITE)
        pr.draw_text("Press [M] to Toggle Audio", cx + 80, cy + 165, 18, COLOR_TEXT_WHITE)
        pr.draw_text("Press [Q] to Exit Game", cx + 80, cy + 205, 18, pr.Color(230, 90, 90, 255))
