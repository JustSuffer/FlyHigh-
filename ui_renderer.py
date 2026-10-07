"""
FlyHigh! - 3D Volleyball Game
Modern Arcade UI & HUD Renderer
Features:
- Pixel-perfect mouse hover and click detection on menu buttons
- 100% clean ASCII text formatting (zero '?' glyph bugs)
- Animated arcade popups ("NICE DIG!", "PERFECT SET!", "BOOM SPIKE!!")
- Modern scoreboard, touch meter, and controls modal dialog
"""
import pyray as pr
import math
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, Team, MatchState, AIDifficulty
)

# Modern Arcade Color Palette
COLOR_GLASS_BG      = pr.Color(16, 20, 30, 230)
COLOR_GLASS_BORDER  = pr.Color(65, 80, 115, 255)
COLOR_TEXT_MAIN     = pr.Color(245, 248, 255, 255)
COLOR_TEXT_MUTED    = pr.Color(160, 175, 200, 255)
COLOR_CYAN_ACCENT   = pr.Color(35, 200, 245, 255)
COLOR_GOLD_ACCENT   = pr.Color(255, 215, 0, 255)
COLOR_CORAL_ACCENT  = pr.Color(255, 75, 90, 255)
COLOR_BTN_NORMAL    = pr.Color(25, 32, 48, 240)
COLOR_BTN_HOVER     = pr.Color(45, 60, 95, 255)
COLOR_BTN_BORDER    = pr.Color(80, 105, 150, 255)

class UIRenderer:
    # Exact Shared Menu Dimensions (used for both collision detection and rendering)
    CARD_W = 500
    CARD_H = 530
    CARD_X = (SCREEN_WIDTH - CARD_W) // 2
    CARD_Y = 85

    BTN_W = CARD_W - 70
    BTN_H = 50
    BTN_START_Y = 180
    BTN_SPACING = 64
    BTN_X = CARD_X + 35

    def __init__(self):
        self.menu_index = 0
        self.menu_items = [
            "PLAY MATCH (3v3)",
            "DIFFICULTY",
            "HOW TO PLAY",
            "AUDIO",
            "QUIT"
        ]
        self.show_controls_modal = False
        self.anim_timer = 0.0
        
        # In-game arcade popup banner
        self.arcade_popup_text = ""
        self.arcade_popup_timer = 0.0
        self.arcade_popup_col = COLOR_CYAN_ACCENT

    def trigger_arcade_popup(self, text, col=COLOR_CYAN_ACCENT, duration=1.0):
        self.arcade_popup_text = text
        self.arcade_popup_timer = duration
        self.arcade_popup_col = col

    def update_menu(self, input_mgr, audio_mgr, current_diff):
        """Handles menu navigation via keyboard, mouse, and gamepad with exact hitboxes."""
        self.anim_timer += pr.get_frame_time()
        
        if self.show_controls_modal:
            if input_mgr.pause_pressed or input_mgr.jump_pressed or input_mgr.select_pressed:
                self.show_controls_modal = False
                audio_mgr.play("hit_set")
            return "NONE", current_diff

        # 1. Exact Mouse Hover & Click Detection
        mouse_pos = pr.get_mouse_position()

        for i in range(len(self.menu_items)):
            by = self.BTN_START_Y + i * self.BTN_SPACING
            rec = pr.Rectangle(self.BTN_X, by, self.BTN_W, self.BTN_H)
            
            if pr.check_collision_point_rec(mouse_pos, rec):
                if self.menu_index != i:
                    self.menu_index = i
                    audio_mgr.play("hit_set")
                if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                    return self._activate_menu_item(i, current_diff, audio_mgr)

        # 2. Keyboard / Gamepad Navigation
        nav_up = pr.is_key_pressed(pr.KEY_W) or pr.is_key_pressed(pr.KEY_UP) or (
            pr.is_gamepad_available(input_mgr.gamepad_id) and pr.is_gamepad_button_pressed(input_mgr.gamepad_id, pr.GAMEPAD_BUTTON_LEFT_FACE_UP)
        )
        nav_down = pr.is_key_pressed(pr.KEY_S) or pr.is_key_pressed(pr.KEY_DOWN) or (
            pr.is_gamepad_available(input_mgr.gamepad_id) and pr.is_gamepad_button_pressed(input_mgr.gamepad_id, pr.GAMEPAD_BUTTON_LEFT_FACE_DOWN)
        )
        
        if nav_up:
            self.menu_index = (self.menu_index - 1) % len(self.menu_items)
            audio_mgr.play("hit_set")
        elif nav_down:
            self.menu_index = (self.menu_index + 1) % len(self.menu_items)
            audio_mgr.play("hit_set")

        # Adjust difficulty with Left / Right
        if self.menu_index == 1:
            diff_left = pr.is_key_pressed(pr.KEY_A) or pr.is_key_pressed(pr.KEY_LEFT) or (
                pr.is_gamepad_available(input_mgr.gamepad_id) and pr.is_gamepad_button_pressed(input_mgr.gamepad_id, pr.GAMEPAD_BUTTON_LEFT_FACE_LEFT)
            )
            diff_right = pr.is_key_pressed(pr.KEY_D) or pr.is_key_pressed(pr.KEY_RIGHT) or (
                pr.is_gamepad_available(input_mgr.gamepad_id) and pr.is_gamepad_button_pressed(input_mgr.gamepad_id, pr.GAMEPAD_BUTTON_LEFT_FACE_RIGHT)
            )
            if diff_left or diff_right:
                diffs = [AIDifficulty.EASY, AIDifficulty.MEDIUM, AIDifficulty.HARD]
                curr_idx = diffs.index(current_diff)
                new_idx = (curr_idx + (1 if diff_right else -1)) % len(diffs)
                current_diff = diffs[new_idx]
                audio_mgr.play("hit_bump")

        # Select action
        if input_mgr.select_pressed or input_mgr.jump_pressed:
            return self._activate_menu_item(self.menu_index, current_diff, audio_mgr)

        return "NONE", current_diff

    def _activate_menu_item(self, index, current_diff, audio_mgr):
        audio_mgr.play("hit_bump")
        if index == 0:
            return "PLAY", current_diff
        elif index == 1:
            diffs = [AIDifficulty.EASY, AIDifficulty.MEDIUM, AIDifficulty.HARD]
            curr_idx = diffs.index(current_diff)
            new_diff = diffs[(curr_idx + 1) % len(diffs)]
            return "DIFF_CHANGED", new_diff
        elif index == 2:
            self.show_controls_modal = True
            return "CONTROLS", current_diff
        elif index == 3:
            audio_mgr.toggle_mute()
            return "AUDIO_TOGGLE", current_diff
        elif index == 4:
            return "QUIT", current_diff
        return "NONE", current_diff

    def draw_title_screen(self, current_diff, audio_mgr, input_mgr):
        """Draws the modern arcade title menu matching the exact collision layout."""
        card_w = self.CARD_W
        card_h = self.CARD_H
        card_x = self.CARD_X
        card_y = self.CARD_Y

        # Frosted Glass Card Background
        pr.draw_rectangle_rounded(pr.Rectangle(card_x, card_y, card_w, card_h), 0.12, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(card_x, card_y, card_w, card_h), 0.12, 10, 2, COLOR_GLASS_BORDER)

        # Title Header with 3D Drop Shadow
        title = "FLYHIGH!"
        tw = pr.measure_text(title, 50)
        pr.draw_text(title, card_x + (card_w - tw) // 2 + 2, card_y + 26 + 2, 50, pr.Color(10, 12, 18, 200))
        pr.draw_text(title, card_x + (card_w - tw) // 2, card_y + 26, 50, COLOR_CYAN_ACCENT)

        # Subtitle Tag (Clean ASCII)
        sub = "* 3v3 VOLLEYBALL ARCADE *"
        sw = pr.measure_text(sub, 16)
        tag_bg = pr.Rectangle(card_x + (card_w - sw - 32) // 2, card_y + 88, sw + 32, 26)
        pr.draw_rectangle_rounded(tag_bg, 0.4, 6, pr.Color(22, 32, 50, 240))
        pr.draw_rectangle_rounded_lines_ex(tag_bg, 0.4, 6, 1, COLOR_GOLD_ACCENT)
        pr.draw_text(sub, card_x + (card_w - sw) // 2, card_y + 93, 16, COLOR_GOLD_ACCENT)

        # Menu Buttons (Exact dimensions: BTN_START_Y, BTN_SPACING, BTN_H)
        for i, item_text in enumerate(self.menu_items):
            by = self.BTN_START_Y + i * self.BTN_SPACING
            is_selected = (i == self.menu_index)

            bg_col = COLOR_BTN_HOVER if is_selected else COLOR_BTN_NORMAL
            border_col = COLOR_CYAN_ACCENT if is_selected else COLOR_BTN_BORDER
            border_thick = 2 if is_selected else 1

            rec = pr.Rectangle(self.BTN_X, by, self.BTN_W, self.BTN_H)
            pr.draw_rectangle_rounded(rec, 0.35, 8, bg_col)
            pr.draw_rectangle_rounded_lines_ex(rec, 0.35, 8, border_thick, border_col)

            # Button Content (Clean ASCII without unicode '?' symbols)
            if i == 0:
                txt = "> PLAY MATCH (3v3)"
                tcol = COLOR_GOLD_ACCENT if is_selected else COLOR_TEXT_MAIN
            elif i == 1:
                diff_label = current_diff.name
                txt = f"[=] DIFFICULTY: < {diff_label} >"
                tcol = COLOR_CYAN_ACCENT if is_selected else COLOR_TEXT_MAIN
            elif i == 2:
                txt = "[?] HOW TO PLAY & CONTROLS"
                tcol = COLOR_TEXT_MAIN
            elif i == 3:
                status = "ON" if audio_mgr.enabled else "OFF"
                txt = f"[S] SOUND: [ {status} ]"
                tcol = COLOR_TEXT_MAIN
            else:
                txt = "[X] EXIT GAME"
                tcol = COLOR_CORAL_ACCENT if is_selected else COLOR_TEXT_MUTED

            tw_btn = pr.measure_text(txt, 18)
            pr.draw_text(txt, self.BTN_X + (self.BTN_W - tw_btn) // 2, by + 16, 18, tcol)

            if is_selected:
                pr.draw_circle(self.BTN_X + 22, by + self.BTN_H // 2, 4, COLOR_GOLD_ACCENT)
                pr.draw_circle(self.BTN_X + self.BTN_W - 22, by + self.BTN_H // 2, 4, COLOR_GOLD_ACCENT)

        # Pulsing selection prompt
        pulse_alpha = int(180 + 75 * math.sin(self.anim_timer * 5.0))
        prompt_txt = "PRESS [ENTER], [SPACE] OR CLICK TO SELECT"
        pw = pr.measure_text(prompt_txt, 14)
        pr.draw_text(prompt_txt, card_x + (card_w - pw) // 2, card_y + card_h - 26, 14, pr.Color(255, 215, 0, pulse_alpha))

        # Controls Modal if active
        if self.show_controls_modal:
            self._draw_controls_modal(input_mgr)

    def _draw_controls_modal(self, input_mgr):
        """Draws clean controls dialog with 100% clean ASCII text."""
        pr.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, pr.Color(8, 10, 16, 210))

        mw = 660
        mh = 500
        mx = (SCREEN_WIDTH - mw) // 2
        my = (SCREEN_HEIGHT - mh) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(mx, my, mw, mh), 0.14, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(mx, my, mw, mh), 0.14, 10, 2, COLOR_CYAN_ACCENT)

        title = "HOW TO PLAY - 3v3 VOLLEYBALL"
        tw = pr.measure_text(title, 24)
        pr.draw_text(title, mx + (mw - tw) // 2, my + 22, 24, COLOR_GOLD_ACCENT)

        controls = [
            ("HAREKET / MOVE", "[W, A, S, D] / Ok Tuslari", "Sol Analog / D-Pad"),
            ("HEDEF / AIM", "Mouse Imleci (Cursor)", "Sag Analog Cubuk"),
            ("SERVIS / TOSS", "[SPACE] veya Sol Tik", "(A) veya (X) Butonu"),
            ("MANSET / DIG (1. Vurus)", "[J] veya Sol Tik", "(X) Butonu"),
            ("PAS / SET (2. Vurus)", "[K] veya Sag Tik", "(Y) Butonu"),
            ("SMAC / SPIKE (3. Vurus)", "Havada [SPACE] / Sol Tik", "Havada (A) Butonu"),
            ("PLONJON / DIVE", "[SOL SHIFT] / [C]", "(RB) Butonu"),
            ("KAMERA / CAMERA", "[TAB] / [V]", "(BACK / VIEW) Butonu"),
        ]

        start_y = my + 68
        for idx, (label, kb, gp) in enumerate(controls):
            col_idx = idx % 2
            row_idx = idx // 2
            card_x = mx + 25 + col_idx * 310
            card_y = start_y + row_idx * 80

            c_rec = pr.Rectangle(card_x, card_y, 300, 70)
            pr.draw_rectangle_rounded(c_rec, 0.25, 6, pr.Color(22, 28, 42, 220))
            pr.draw_rectangle_rounded_lines_ex(c_rec, 0.25, 6, 1, COLOR_GLASS_BORDER)

            pr.draw_text(label, card_x + 12, card_y + 8, 14, COLOR_CYAN_ACCENT)
            pr.draw_text(f"Klavye: {kb}", card_x + 12, card_y + 28, 13, COLOR_TEXT_MAIN)
            pr.draw_text(f"Gamepad: {gp}", card_x + 12, card_y + 48, 13, COLOR_TEXT_MUTED)

        close_txt = "Press [ESC], (B) or Click to Close"
        cw = pr.measure_text(close_txt, 15)
        pr.draw_text(close_txt, mx + (mw - cw) // 2, my + mh - 30, 15, COLOR_GOLD_ACCENT)

    def draw_hud(self, match_mgr, input_mgr, cam_ctrl, ai_difficulty):
        """Draws top scoreboard, touch counter, and bottom hints with clean ASCII text."""
        dt = pr.get_frame_time()
        if self.arcade_popup_timer > 0.0:
            self.arcade_popup_timer -= dt

        # 1. Top Scoreboard Pill Container
        bar_w = 520
        bar_h = 62
        bar_x = (SCREEN_WIDTH - bar_w) // 2
        bar_y = 12

        pr.draw_rectangle_rounded(pr.Rectangle(bar_x, bar_y, bar_w, bar_h), 0.4, 8, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bar_x, bar_y, bar_w, bar_h), 0.4, 8, 2, COLOR_GLASS_BORDER)

        # Team Player (Cyan Pill)
        pr.draw_rectangle_rounded(pr.Rectangle(bar_x + 14, bar_y + 10, 170, 42), 0.4, 6, pr.Color(20, 60, 110, 200))
        pr.draw_text("YOU (3v3)", bar_x + 30, bar_y + 22, 16, COLOR_CYAN_ACCENT)
        p_score = f"{match_mgr.score_player:02d}"
        pr.draw_text(p_score, bar_x + 130, bar_y + 14, 34, COLOR_CYAN_ACCENT)
        if match_mgr.serving_team == Team.PLAYER:
            pr.draw_circle(bar_x + 12, bar_y + bar_h // 2, 5, COLOR_GOLD_ACCENT)

        # Center Divider & Target
        pr.draw_text("VS", bar_x + bar_w // 2 - 12, bar_y + 12, 18, pr.GRAY)
        target_str = f"TO {match_mgr.points_to_win}"
        pr.draw_text(target_str, bar_x + bar_w // 2 - 20, bar_y + 36, 13, COLOR_GOLD_ACCENT)

        # Team Opponent (Crimson Pill)
        pr.draw_rectangle_rounded(pr.Rectangle(bar_x + bar_w - 184, bar_y + 10, 170, 42), 0.4, 6, pr.Color(110, 25, 40, 200))
        o_score = f"{match_mgr.score_opponent:02d}"
        pr.draw_text(o_score, bar_x + bar_w - 170, bar_y + 14, 34, COLOR_CORAL_ACCENT)
        pr.draw_text("CPU (3v3)", bar_x + bar_w - 118, bar_y + 22, 16, COLOR_CORAL_ACCENT)
        if match_mgr.serving_team == Team.OPPONENT:
            pr.draw_circle(bar_x + bar_w - 12, bar_y + bar_h // 2, 5, COLOR_GOLD_ACCENT)

        # 2. Touch Counter Badge
        if match_mgr.state == MatchState.IN_RALLY:
            touches = match_mgr.get_touches(Team.PLAYER)
            badge_w = 230
            badge_h = 36
            bx = (SCREEN_WIDTH - badge_w) // 2
            by = bar_y + bar_h + 10

            pr.draw_rectangle_rounded(pr.Rectangle(bx, by, badge_w, badge_h), 0.45, 6, COLOR_GLASS_BG)
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bx, by, badge_w, badge_h), 0.45, 6, 1, COLOR_GLASS_BORDER)

            if touches == 0:
                t_lbl = "TOUCH: 0/3 (READY)"
                t_col = COLOR_TEXT_MAIN
            elif touches == 1:
                t_lbl = "TOUCH: 1/3 (MANSET / PASOR)"
                t_col = COLOR_CYAN_ACCENT
            elif touches == 2:
                t_lbl = "TOUCH: 2/3 (PAS / HAVADA)"
                t_col = COLOR_GOLD_ACCENT
            else:
                t_lbl = "TOUCH: 3/3 (SMAC VUR!)"
                t_col = COLOR_CORAL_ACCENT

            tw = pr.measure_text(t_lbl, 15)
            pr.draw_text(t_lbl, bx + (badge_w - tw) // 2, by + 10, 15, t_col)

        # 3. Dynamic Arcade Popup Banner
        if self.arcade_popup_timer > 0.0:
            p_text = self.arcade_popup_text
            pw = pr.measure_text(p_text, 36)
            p_x = (SCREEN_WIDTH - pw) // 2
            p_y = 145
            pr.draw_text(p_text, p_x + 2, p_y + 2, 36, pr.Color(10, 10, 15, 220))
            pr.draw_text(p_text, p_x, p_y, 36, self.arcade_popup_col)

        # 4. Bottom Control Helper Bar (Sleek and non-obtrusive)
        bot_h = 38
        bot_y = SCREEN_HEIGHT - bot_h - 8
        bot_w = SCREEN_WIDTH - 80
        bot_x = 40

        pr.draw_rectangle_rounded(pr.Rectangle(bot_x, bot_y, bot_w, bot_h), 0.35, 6, pr.Color(12, 16, 24, 210))
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bot_x, bot_y, bot_w, bot_h), 0.35, 6, 1, COLOR_GLASS_BORDER)

        device = input_mgr.active_device
        if device == "GAMEPAD":
            ctrl_str = "[L-STICK] Hareket | (A) Sicra/Smac | (X) Manset | (Y) Pas | (RB) Plonjon | (BACK) Kamera"
        else:
            ctrl_str = "[WASD] Hareket | [MOUSE] Hedef | [SPACE/SOL TIK] Smac | [J/SAG TIK] Manset/Pas"

        pr.draw_text(f"KONTROL: {device}", bot_x + 16, bot_y + 11, 13, COLOR_GOLD_ACCENT)
        pr.draw_text(ctrl_str, bot_x + 180, bot_y + 11, 13, COLOR_TEXT_MAIN)

        # Top-left and Top-right info
        cam_info = f"CAM: {cam_ctrl.get_mode_name()} [TAB]"
        pr.draw_text(cam_info, 18, 16, 13, COLOR_TEXT_MUTED)
        diff_info = f"AI: {ai_difficulty.name}"
        dw = pr.measure_text(diff_info, 13)
        pr.draw_text(diff_info, SCREEN_WIDTH - dw - 18, 16, 13, COLOR_TEXT_MUTED)

    def draw_serve_prompt(self, match_mgr, input_mgr):
        """Displays clear serving prompt with 100% clean ASCII text."""
        if match_mgr.state == MatchState.SERVE_READY:
            card_w = 480
            card_h = 54
            cx = (SCREEN_WIDTH - card_w) // 2
            cy = 135

            pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, COLOR_GLASS_BG)
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, 2, COLOR_GOLD_ACCENT)

            if match_mgr.serving_team == Team.PLAYER:
                txt = "SERVIS SENDE: [SPACE] veya [SOL TIK] ile Topu Firlat!"
                col = COLOR_GOLD_ACCENT
            else:
                txt = "RAKIP SERVIS ATIYOR... Karsilamaya Hazirlan!"
                col = COLOR_CORAL_ACCENT

            tw = pr.measure_text(txt, 16)
            pr.draw_text(txt, cx + (card_w - tw) // 2, cy + 18, 16, col)

        elif match_mgr.state == MatchState.SERVE_TOSSED:
            card_w = 520
            card_h = 54
            cx = (SCREEN_WIDTH - card_w) // 2
            cy = 135

            pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, COLOR_GLASS_BG)
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, 2, COLOR_CYAN_ACCENT)

            if match_mgr.serving_team == Team.PLAYER:
                txt = "VUR! [SPACE / SOL TIK] Smac Servis | [SAG TIK] Plase Servis"
                col = COLOR_CYAN_ACCENT
            else:
                txt = "RAKIP SERVIS GELIYOR! Manset Pozisyonu Al!"
                col = COLOR_CORAL_ACCENT

            tw = pr.measure_text(txt, 16)
            pr.draw_text(txt, cx + (card_w - tw) // 2, cy + 18, 16, col)

    def draw_point_banner(self, match_mgr):
        """Displays point award banner with clean ASCII text."""
        if match_mgr.state == MatchState.POINT_SCORED:
            banner_w = 540
            banner_h = 95
            bx = (SCREEN_WIDTH - banner_w) // 2
            by = SCREEN_HEIGHT // 2 - 95

            pr.draw_rectangle_rounded(pr.Rectangle(bx, by, banner_w, banner_h), 0.3, 8, COLOR_GLASS_BG)
            winner_col = COLOR_CYAN_ACCENT if match_mgr.point_winner == Team.PLAYER else COLOR_CORAL_ACCENT
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bx, by, banner_w, banner_h), 0.3, 8, 3, winner_col)

            win_title = "SAYI BIZIM! (POINT FOR YOU)" if match_mgr.point_winner == Team.PLAYER else "RAKIP SAYI ALDI (CPU POINT)"
            tw1 = pr.measure_text(win_title, 25)
            pr.draw_text(win_title, bx + (banner_w - tw1) // 2, by + 16, 25, winner_col)

            reason_str = match_mgr.point_reason
            tw2 = pr.measure_text(reason_str, 17)
            pr.draw_text(reason_str, bx + (banner_w - tw2) // 2, by + 56, 17, COLOR_TEXT_MAIN)

    def draw_match_over(self, match_mgr, input_mgr):
        """Draws match end screen with clean ASCII text."""
        if match_mgr.state == MatchState.MATCH_OVER:
            pr.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, pr.Color(8, 10, 16, 220))

            card_w = 580
            card_h = 290
            cx = (SCREEN_WIDTH - card_w) // 2
            cy = (SCREEN_HEIGHT - card_h) // 2

            pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, COLOR_GLASS_BG)
            win_col = COLOR_GOLD_ACCENT if match_mgr.winner == Team.PLAYER else COLOR_CORAL_ACCENT
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, 3, win_col)

            main_text = "MACI KAZANDINIZ! (VICTORY)" if match_mgr.winner == Team.PLAYER else "MAC BITTI (DEFEAT)"
            tw = pr.measure_text(main_text, 30)
            pr.draw_text(main_text, cx + (card_w - tw) // 2, cy + 30, 30, win_col)

            score_text = f"Skor: BIZ {match_mgr.score_player} - {match_mgr.score_opponent} RAKIP"
            sw = pr.measure_text(score_text, 22)
            pr.draw_text(score_text, cx + (card_w - sw) // 2, cy + 95, 22, COLOR_TEXT_MAIN)

            rematch_text = "[SPACE] veya [SOL TIK] ile TEKRAR OYNA"
            rw = pr.measure_text(rematch_text, 19)
            pr.draw_text(rematch_text, cx + (card_w - rw) // 2, cy + 160, 19, COLOR_GOLD_ACCENT)

            quit_text = "[ESC] veya (START) ile Ana Menuye Don"
            qw = pr.measure_text(quit_text, 15)
            pr.draw_text(quit_text, cx + (card_w - qw) // 2, cy + 220, 15, COLOR_TEXT_MUTED)

    def draw_pause_menu(self, input_mgr):
        """Draws Pause overlay with clean ASCII text."""
        pr.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, pr.Color(8, 10, 16, 190))
        
        card_w = 480
        card_h = 270
        cx = (SCREEN_WIDTH - card_w) // 2
        cy = (SCREEN_HEIGHT - card_h) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, 2, COLOR_GLASS_BORDER)

        pr.draw_text("OYUN DURAKLATILDI", cx + 115, cy + 26, 26, COLOR_TEXT_MAIN)
        pr.draw_text("[ESC] / (START) ile Devam Et", cx + 75, cy + 85, 17, COLOR_GOLD_ACCENT)
        pr.draw_text("[TAB] / (BACK) ile Kamera Degistir", cx + 75, cy + 125, 17, COLOR_TEXT_MAIN)
        pr.draw_text("[M] ile Sesi Ac/Kapat", cx + 75, cy + 165, 17, COLOR_TEXT_MAIN)
        pr.draw_text("[Q] ile Ana Menuye Don", cx + 75, cy + 205, 17, COLOR_CORAL_ACCENT)
