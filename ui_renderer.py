"""
FlyHigh! - 3D Volleyball Game
Modern Arcade UI & HUD Renderer
Features:
- Sweet, high-polish title screen with frosted glassmorphic cards and hover buttons
- Responsive controls (Keyboard, Mouse, Gamepad)
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
    def __init__(self):
        # Menu state
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
        """Handles menu navigation via keyboard, mouse, and gamepad."""
        self.anim_timer += pr.get_frame_time()
        
        if self.show_controls_modal:
            if input_mgr.pause_pressed or input_mgr.jump_pressed or input_mgr.select_pressed:
                self.show_controls_modal = False
                audio_mgr.play("hit_set")
            return "NONE", current_diff

        # Mouse hover detection
        mouse_pos = pr.get_mouse_position()
        card_w = 460
        card_x = (SCREEN_WIDTH - card_w) // 2
        btn_start_y = 280
        btn_h = 52
        btn_spacing = 64

        for i in range(len(self.menu_items)):
            by = btn_start_y + i * btn_spacing
            rec = pr.Rectangle(card_x + 30, by, card_w - 60, btn_h)
            if pr.check_collision_point_rec(mouse_pos, rec):
                if self.menu_index != i:
                    self.menu_index = i
                    audio_mgr.play("hit_set")
                if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                    return self._activate_menu_item(i, current_diff, audio_mgr)

        # Keyboard / Gamepad navigation
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
        """Draws the modern arcade title menu with glassmorphism and animated badges."""
        card_w = 520
        card_h = 580
        card_x = (SCREEN_WIDTH - card_w) // 2
        card_y = 65

        # Frosted Glass Card Background
        pr.draw_rectangle_rounded(pr.Rectangle(card_x, card_y, card_w, card_h), 0.12, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(card_x, card_y, card_w, card_h), 0.12, 10, 2, COLOR_GLASS_BORDER)

        # Modern Title Header with 3D Drop Shadow
        title = "FLYHIGH!"
        tw = pr.measure_text(title, 54)
        # Drop shadow
        pr.draw_text(title, card_x + (card_w - tw) // 2 + 3, card_y + 32 + 3, 54, pr.Color(10, 12, 18, 200))
        # Gradient title text
        pr.draw_text(title, card_x + (card_w - tw) // 2, card_y + 32, 54, COLOR_CYAN_ACCENT)

        # Arcade Subtitle Tag
        sub = "★ 3v3 VOLLEYBALL ARCADE ★"
        sw = pr.measure_text(sub, 18)
        tag_bg = pr.Rectangle(card_x + (card_w - sw - 36) // 2, card_y + 98, sw + 36, 28)
        pr.draw_rectangle_rounded(tag_bg, 0.4, 6, pr.Color(25, 35, 55, 240))
        pr.draw_rectangle_rounded_lines_ex(tag_bg, 0.4, 6, 1, COLOR_GOLD_ACCENT)
        pr.draw_text(sub, card_x + (card_w - sw) // 2, card_y + 104, 18, COLOR_GOLD_ACCENT)

        # Menu Buttons
        btn_start_y = 160
        btn_w = card_w - 70
        btn_h = 54
        btn_spacing = 66
        bx = card_x + 35

        for i, item_text in enumerate(self.menu_items):
            by = btn_start_y + i * btn_spacing
            is_selected = (i == self.menu_index)

            # Button Background
            bg_col = COLOR_BTN_HOVER if is_selected else COLOR_BTN_NORMAL
            border_col = COLOR_CYAN_ACCENT if is_selected else COLOR_BTN_BORDER
            border_thick = 2 if is_selected else 1

            rec = pr.Rectangle(bx, by, btn_w, btn_h)
            pr.draw_rectangle_rounded(rec, 0.35, 8, bg_col)
            pr.draw_rectangle_rounded_lines_ex(rec, 0.35, 8, border_thick, border_col)

            # Button Content
            if i == 0:
                txt = "▶  PLAY MATCH (3v3)"
                tcol = COLOR_GOLD_ACCENT if is_selected else COLOR_TEXT_MAIN
            elif i == 1:
                diff_label = current_diff.name
                txt = f"⚙  DIFFICULTY: < {diff_label} >"
                tcol = COLOR_CYAN_ACCENT if is_selected else COLOR_TEXT_MAIN
            elif i == 2:
                txt = "📖  HOW TO PLAY & CONTROLS"
                tcol = COLOR_TEXT_MAIN
            elif i == 3:
                status = "ON" if audio_mgr.enabled else "OFF"
                txt = f"🔊  SOUND: [ {status} ]"
                tcol = COLOR_TEXT_MAIN
            else:
                txt = "✕  EXIT GAME"
                tcol = COLOR_CORAL_ACCENT if is_selected else COLOR_TEXT_MUTED

            tw_btn = pr.measure_text(txt, 19)
            pr.draw_text(txt, bx + (btn_w - tw_btn) // 2, by + 17, 19, tcol)

            # Selected indicator dot
            if is_selected:
                pr.draw_circle(bx + 24, by + btn_h // 2, 5, COLOR_GOLD_ACCENT)
                pr.draw_circle(bx + btn_w - 24, by + btn_h // 2, 5, COLOR_GOLD_ACCENT)

        # Bottom Pulsing Prompt
        pulse_alpha = int(180 + 75 * math.sin(self.anim_timer * 5.0))
        prompt_txt = "PRESS [ENTER] or (A) TO SELECT"
        pw = pr.measure_text(prompt_txt, 15)
        pr.draw_text(prompt_txt, card_x + (card_w - pw) // 2, card_y + card_h - 45, 15, pr.Color(255, 215, 0, pulse_alpha))

        # Bottom Version Tag
        ver = "v1.2 ARCADE EDITION | KEYBOARD & GAMEPAD READY"
        vw = pr.measure_text(ver, 12)
        pr.draw_text(ver, (SCREEN_WIDTH - vw) // 2, SCREEN_HEIGHT - 28, 12, pr.Color(160, 175, 200, 180))

        # If Controls Modal is active, draw it on top
        if self.show_controls_modal:
            self._draw_controls_modal(input_mgr)

    def _draw_controls_modal(self, input_mgr):
        """Draws clean modern controls modal dialog."""
        # Dim background
        pr.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, pr.Color(8, 10, 16, 210))

        mw = 660
        mh = 500
        mx = (SCREEN_WIDTH - mw) // 2
        my = (SCREEN_HEIGHT - mh) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(mx, my, mw, mh), 0.14, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(mx, my, mw, mh), 0.14, 10, 2, COLOR_CYAN_ACCENT)

        # Modal Title
        title = "HOW TO PLAY - 3v3 VOLLEYBALL"
        tw = pr.measure_text(title, 26)
        pr.draw_text(title, mx + (mw - tw) // 2, my + 25, 26, COLOR_GOLD_ACCENT)

        # Controls Cards Grid
        controls = [
            ("🏃 HAREKET / MOVE", "[W, A, S, D] / Ok Tuşları", "Sol Analog Çubuk / D-Pad"),
            ("🎯 HEDEF ALMA / AIM", "Yön Tuşları / Mouse", "Sağ Analog Çubuk"),
            ("🏐 SERVİS / TOSS", "[SPACE] veya [J]", "(A) veya (X) Butonu"),
            ("🛡️ MANŞET / DIG (1. Vuruş)", "[J] / Fare Sol Tık", "(X) / Kare Butonu"),
            ("🤲 PAS / SET (2. Vuruş)", "[K] / Fare Sağ Tık", "(Y) / Üçgen Butonu"),
            ("⚡ SMAÇ / SPIKE (3. Vuruş)", "Havada [SPACE] / [L]", "Havada (A) / (B) Butonu"),
            ("💨 PLONJON / DIVE", "[SOL SHIFT] / [C]", "(RB) / R1 Butonu"),
            ("🎥 KAMERA DEĞİŞTİR", "[TAB] / [V]", "(BACK / VIEW) Butonu"),
        ]

        start_y = my + 80
        for idx, (label, kb, gp) in enumerate(controls):
            col_idx = idx % 2
            row_idx = idx // 2
            card_x = mx + 30 + col_idx * 305
            card_y = start_y + row_idx * 78

            c_rec = pr.Rectangle(card_x, card_y, 295, 68)
            pr.draw_rectangle_rounded(c_rec, 0.25, 6, pr.Color(22, 28, 42, 220))
            pr.draw_rectangle_rounded_lines_ex(c_rec, 0.25, 6, 1, COLOR_GLASS_BORDER)

            pr.draw_text(label, card_x + 12, card_y + 8, 14, COLOR_CYAN_ACCENT)
            pr.draw_text(f"Klavye: {kb}", card_x + 12, card_y + 28, 13, COLOR_TEXT_MAIN)
            pr.draw_text(f"Gamepad: {gp}", card_x + 12, card_y + 46, 13, COLOR_TEXT_MUTED)

        # Bottom close prompt
        close_txt = "Press [ESC] / (B) or Click to Close"
        cw = pr.measure_text(close_txt, 16)
        pr.draw_text(close_txt, mx + (mw - cw) // 2, my + mh - 35, 16, COLOR_GOLD_ACCENT)

    def draw_hud(self, match_mgr, input_mgr, cam_ctrl, ai_difficulty):
        """Draws sleek top scoreboard, 3v3 team labels, and touch counter."""
        dt = pr.get_frame_time()
        if self.arcade_popup_timer > 0.0:
            self.arcade_popup_timer -= dt

        # 1. Top Scoreboard Pill Container
        bar_w = 520
        bar_h = 66
        bar_x = (SCREEN_WIDTH - bar_w) // 2
        bar_y = 15

        pr.draw_rectangle_rounded(pr.Rectangle(bar_x, bar_y, bar_w, bar_h), 0.4, 8, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bar_x, bar_y, bar_w, bar_h), 0.4, 8, 2, COLOR_GLASS_BORDER)

        # Team Player (Cyan Pill)
        pr.draw_rectangle_rounded(pr.Rectangle(bar_x + 14, bar_y + 12, 170, 42), 0.4, 6, pr.Color(20, 60, 110, 200))
        pr.draw_text("YOU (3v3)", bar_x + 30, bar_y + 24, 16, COLOR_CYAN_ACCENT)
        p_score = f"{match_mgr.score_player:02d}"
        pr.draw_text(p_score, bar_x + 130, bar_y + 16, 34, COLOR_CYAN_ACCENT)
        if match_mgr.serving_team == Team.PLAYER:
            pr.draw_circle(bar_x + 12, bar_y + bar_h // 2, 5, COLOR_GOLD_ACCENT)

        # Center Divider & Target
        pr.draw_text("VS", bar_x + bar_w // 2 - 12, bar_y + 14, 18, pr.GRAY)
        target_str = f"TO {match_mgr.points_to_win}"
        pr.draw_text(target_str, bar_x + bar_w // 2 - 20, bar_y + 38, 13, COLOR_GOLD_ACCENT)

        # Team Opponent (Crimson Pill)
        pr.draw_rectangle_rounded(pr.Rectangle(bar_x + bar_w - 184, bar_y + 12, 170, 42), 0.4, 6, pr.Color(110, 25, 40, 200))
        o_score = f"{match_mgr.score_opponent:02d}"
        pr.draw_text(o_score, bar_x + bar_w - 170, bar_y + 16, 34, COLOR_CORAL_ACCENT)
        pr.draw_text("CPU (3v3)", bar_x + bar_w - 118, bar_y + 24, 16, COLOR_CORAL_ACCENT)
        if match_mgr.serving_team == Team.OPPONENT:
            pr.draw_circle(bar_x + bar_w - 12, bar_y + bar_h // 2, 5, COLOR_GOLD_ACCENT)

        # 2. Touch Counter Badge
        if match_mgr.state == MatchState.IN_RALLY:
            touches = match_mgr.get_touches(Team.PLAYER)
            badge_w = 220
            badge_h = 38
            bx = (SCREEN_WIDTH - badge_w) // 2
            by = bar_y + bar_h + 12

            pr.draw_rectangle_rounded(pr.Rectangle(bx, by, badge_w, badge_h), 0.45, 6, COLOR_GLASS_BG)
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bx, by, badge_w, badge_h), 0.45, 6, 1, COLOR_GLASS_BORDER)

            if touches == 0:
                t_lbl = "TOUCH: 0/3 (READY)"
                t_col = COLOR_TEXT_MAIN
            elif touches == 1:
                t_lbl = "TOUCH: 1/3 (BUMP / PASÖR)"
                t_col = COLOR_CYAN_ACCENT
            elif touches == 2:
                t_lbl = "TOUCH: 2/3 (SET / HAVADA)"
                t_col = COLOR_GOLD_ACCENT
            else:
                t_lbl = "TOUCH: 3/3 (SMAÇ VUR!)"
                t_col = COLOR_CORAL_ACCENT

            tw = pr.measure_text(t_lbl, 15)
            pr.draw_text(t_lbl, bx + (badge_w - tw) // 2, by + 11, 15, t_col)

        # 3. Dynamic Arcade Popup Banner on hits ("NICE DIG!", "BOOM SPIKE!!")
        if self.arcade_popup_timer > 0.0:
            p_text = self.arcade_popup_text
            pw = pr.measure_text(p_text, 36)
            p_x = (SCREEN_WIDTH - pw) // 2
            p_y = 150
            # Energetic bounce scale
            pr.draw_text(p_text, p_x + 2, p_y + 2, 36, pr.Color(10, 10, 15, 220))
            pr.draw_text(p_text, p_x, p_y, 36, self.arcade_popup_col)

        # 4. Bottom Control Helper Bar
        bot_h = 42
        bot_y = SCREEN_HEIGHT - bot_h - 10
        bot_w = SCREEN_WIDTH - 60
        bot_x = 30

        pr.draw_rectangle_rounded(pr.Rectangle(bot_x, bot_y, bot_w, bot_h), 0.35, 6, pr.Color(12, 16, 24, 210))
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bot_x, bot_y, bot_w, bot_h), 0.35, 6, 1, COLOR_GLASS_BORDER)

        device = input_mgr.active_device
        if device == "GAMEPAD":
            ctrl_str = "[L-STICK] Hareket | (A) Sıçra/Smaç | (X) Manşet | (Y) Pas | (RB) Plonjon | (BACK) Kamera"
        else:
            ctrl_str = "[WASD] Hareket | [SPACE] Sıçra/Smaç | [J] Manşet | [K] Pas | [SHIFT] Plonjon | [TAB] Kamera"

        pr.draw_text(f"KONTROL: {device}", bot_x + 18, bot_y + 13, 13, COLOR_GOLD_ACCENT)
        pr.draw_text(ctrl_str, bot_x + 180, bot_y + 13, 14, COLOR_TEXT_MAIN)

        # Camera & Difficulty indicators
        cam_info = f"CAM: {cam_ctrl.get_mode_name()} [TAB]"
        pr.draw_text(cam_info, 20, 20, 13, COLOR_TEXT_MUTED)
        diff_info = f"AI: {ai_difficulty.name}"
        dw = pr.measure_text(diff_info, 13)
        pr.draw_text(diff_info, SCREEN_WIDTH - dw - 20, 20, 13, COLOR_TEXT_MUTED)

    def draw_serve_prompt(self, match_mgr, input_mgr):
        """Displays serve prompt."""
        if match_mgr.state == MatchState.SERVE_READY:
            card_w = 440
            card_h = 56
            cx = (SCREEN_WIDTH - card_w) // 2
            cy = 135

            pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, COLOR_GLASS_BG)
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, 2, COLOR_GOLD_ACCENT)

            if match_mgr.serving_team == Team.PLAYER:
                btn_name = input_mgr.get_prompt_text("JUMP")
                txt = f"SERVİS SENDE: {btn_name} ile Topu Fırlat ve Vur!"
                col = COLOR_GOLD_ACCENT
            else:
                txt = "RAKİP SERVİS ATIYOR... Karşılamaya Hazırlan!"
                col = COLOR_CORAL_ACCENT

            tw = pr.measure_text(txt, 17)
            pr.draw_text(txt, cx + (card_w - tw) // 2, cy + 18, 17, col)

    def draw_point_banner(self, match_mgr):
        """Displays celebratory banner when a point is scored."""
        if match_mgr.state == MatchState.POINT_SCORED:
            banner_w = 540
            banner_h = 100
            bx = (SCREEN_WIDTH - banner_w) // 2
            by = SCREEN_HEIGHT // 2 - 100

            pr.draw_rectangle_rounded(pr.Rectangle(bx, by, banner_w, banner_h), 0.3, 8, COLOR_GLASS_BG)
            winner_col = COLOR_CYAN_ACCENT if match_mgr.point_winner == Team.PLAYER else COLOR_CORAL_ACCENT
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bx, by, banner_w, banner_h), 0.3, 8, 3, winner_col)

            win_title = "SAYI BİZİM! (POINT FOR YOU)" if match_mgr.point_winner == Team.PLAYER else "RAKİP SAYI ALDI (CPU POINT)"
            tw1 = pr.measure_text(win_title, 26)
            pr.draw_text(win_title, bx + (banner_w - tw1) // 2, by + 18, 26, winner_col)

            reason_str = match_mgr.point_reason
            tw2 = pr.measure_text(reason_str, 18)
            pr.draw_text(reason_str, bx + (banner_w - tw2) // 2, by + 60, 18, COLOR_TEXT_MAIN)

    def draw_match_over(self, match_mgr, input_mgr):
        """Draws match end screen."""
        if match_mgr.state == MatchState.MATCH_OVER:
            pr.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, pr.Color(8, 10, 16, 220))

            card_w = 580
            card_h = 300
            cx = (SCREEN_WIDTH - card_w) // 2
            cy = (SCREEN_HEIGHT - card_h) // 2

            pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, COLOR_GLASS_BG)
            win_col = COLOR_GOLD_ACCENT if match_mgr.winner == Team.PLAYER else COLOR_CORAL_ACCENT
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, 3, win_col)

            main_text = "🏆 MAÇI KAZANDINIZ!" if match_mgr.winner == Team.PLAYER else "MAÇ BİTTİ (KAYBETTİNİZ)"
            tw = pr.measure_text(main_text, 34)
            pr.draw_text(main_text, cx + (card_w - tw) // 2, cy + 32, 34, win_col)

            score_text = f"Skor: BİZ {match_mgr.score_player} - {match_mgr.score_opponent} RAKİP"
            sw = pr.measure_text(score_text, 22)
            pr.draw_text(score_text, cx + (card_w - sw) // 2, cy + 105, 22, COLOR_TEXT_MAIN)

            rematch_text = "[SPACE] veya (A) ile TEKRAR OYNA"
            rw = pr.measure_text(rematch_text, 20)
            pr.draw_text(rematch_text, cx + (card_w - rw) // 2, cy + 175, 20, COLOR_GOLD_ACCENT)

            quit_text = "[ESC] veya (START) ile Ana Menüye Dön"
            qw = pr.measure_text(quit_text, 16)
            pr.draw_text(quit_text, cx + (card_w - qw) // 2, cy + 235, 16, COLOR_TEXT_MUTED)

    def draw_pause_menu(self, input_mgr):
        """Draws Pause overlay."""
        pr.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, pr.Color(8, 10, 16, 190))
        
        card_w = 480
        card_h = 280
        cx = (SCREEN_WIDTH - card_w) // 2
        cy = (SCREEN_HEIGHT - card_h) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, 2, COLOR_GLASS_BORDER)

        pr.draw_text("OYUN DURAKLATILDI", cx + 115, cy + 28, 26, COLOR_TEXT_MAIN)
        pr.draw_text("[ESC] / (START) ile Devam Et", cx + 80, cy + 90, 18, COLOR_GOLD_ACCENT)
        pr.draw_text("[TAB] / (BACK) ile Kamera Değiştir", cx + 80, cy + 130, 18, COLOR_TEXT_MAIN)
        pr.draw_text("[M] ile Sesi Aç/Kapat", cx + 80, cy + 170, 18, COLOR_TEXT_MAIN)
        pr.draw_text("[Q] ile Ana Menüye Dön", cx + 80, cy + 210, 18, COLOR_CORAL_ACCENT)
