"""
FlyHigh! - 3D Volleyball Game
Modern Arcade UI & HUD Renderer (100% English & Authentic Volleyball Terminology)
Features:
- Pixel-perfect mouse hover and click detection on menu buttons
- 100% clean ASCII text formatting (zero '?' character glyph bugs)
- Full Settings Menu (Master Volume, Sound FX, Fullscreen, Resolution, Camera)
- NBA 2K-Style Shot Timing Meter (Green / Yellow / Red contact windows)
- Roll Dig 5-second cooldown indicator badge
- Dynamic animated arcade popups ("PERFECT TIMING!", "BOOM SPIKE!!", "FLOAT SERVE!", "ROLL DIG!")
- Comprehensive card-based "How to Play" controls guide
"""
import pyray as pr
import math
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, Team, MatchState, AIDifficulty,
    TimingRating, ROLL_DIG_COOLDOWN, RESOLUTIONS
)

# Modern Arcade Color Palette
COLOR_GLASS_BG      = pr.Color(16, 20, 30, 235)
COLOR_GLASS_BORDER  = pr.Color(65, 80, 115, 255)
COLOR_TEXT_MAIN     = pr.Color(245, 248, 255, 255)
COLOR_TEXT_MUTED    = pr.Color(160, 175, 200, 255)
COLOR_CYAN_ACCENT   = pr.Color(35, 200, 245, 255)
COLOR_GOLD_ACCENT   = pr.Color(255, 215, 0, 255)
COLOR_CORAL_ACCENT  = pr.Color(255, 75, 90, 255)
COLOR_GREEN_PERFECT = pr.Color(50, 240, 120, 255)
COLOR_BTN_NORMAL    = pr.Color(25, 32, 48, 240)
COLOR_BTN_HOVER     = pr.Color(45, 60, 95, 255)
COLOR_BTN_BORDER    = pr.Color(80, 105, 150, 255)

class UIRenderer:
    # Title Menu Layout
    CARD_W = 520
    CARD_H = 540
    CARD_X = (SCREEN_WIDTH - CARD_W) // 2
    CARD_Y = 80

    BTN_W = CARD_W - 70
    BTN_H = 48
    BTN_START_Y = 175
    BTN_SPACING = 58
    BTN_X = CARD_X + 35

    def __init__(self):
        self.menu_index = 0
        self.menu_items = [
            "PLAY MATCH (3v3)",
            "DIFFICULTY",
            "SETTINGS",
            "HOW TO PLAY",
            "QUIT GAME"
        ]
        self.show_controls_modal = False
        self.show_settings_modal = False
        self.anim_timer = 0.0

        # Settings Menu Navigation
        self.settings_index = 0
        self.settings_items = [
            "MASTER VOLUME",
            "SOUND FX",
            "DISPLAY MODE",
            "RESOLUTION",
            "CAMERA ANGLE",
            "BACK TO MENU"
        ]
        self.res_index = 0
        self.is_fullscreen = False

        # Arcade Popup Banner
        self.arcade_popup_text = ""
        self.arcade_popup_timer = 0.0
        self.arcade_popup_col = COLOR_CYAN_ACCENT

        # NBA 2K-Style Shot Meter State
        self.shot_meter_feedback = ""
        self.shot_meter_feedback_timer = 0.0
        self.shot_meter_feedback_col = COLOR_GREEN_PERFECT

    def trigger_arcade_popup(self, text, col=COLOR_CYAN_ACCENT, duration=1.0):
        self.arcade_popup_text = text
        self.arcade_popup_timer = duration
        self.arcade_popup_col = col

    def trigger_shot_feedback(self, rating: TimingRating):
        if rating == TimingRating.GREEN:
            self.shot_meter_feedback = "PERFECT TIMING! (GREEN)"
            self.shot_meter_feedback_col = COLOR_GREEN_PERFECT
        elif rating == TimingRating.YELLOW:
            self.shot_meter_feedback = "GOOD TIMING (YELLOW)"
            self.shot_meter_feedback_col = COLOR_GOLD_ACCENT
        else:
            self.shot_meter_feedback = "OFF-TIME CONTACT! (RED)"
            self.shot_meter_feedback_col = COLOR_CORAL_ACCENT
        self.shot_meter_feedback_timer = 0.9

    def update_menu(self, input_mgr, audio_mgr, current_diff, cam_ctrl=None):
        """Handles Title and Settings menus via mouse, keyboard, and gamepad."""
        dt = pr.get_frame_time()
        self.anim_timer += dt

        # 1. Controls Dialog Active
        if self.show_controls_modal:
            if input_mgr.pause_pressed or input_mgr.jump_pressed or input_mgr.select_pressed or pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                self.show_controls_modal = False
                audio_mgr.play("hit_set")
            return "NONE", current_diff

        # 2. Settings Modal Active
        if self.show_settings_modal:
            return self._update_settings_menu(input_mgr, audio_mgr, current_diff, cam_ctrl)

        # 3. Main Title Screen Navigation
        mouse_pos = pr.get_mouse_position()

        # Mouse Hover & Click
        for i in range(len(self.menu_items)):
            by = self.BTN_START_Y + i * self.BTN_SPACING
            rec = pr.Rectangle(self.BTN_X, by, self.BTN_W, self.BTN_H)
            
            if pr.check_collision_point_rec(mouse_pos, rec):
                if self.menu_index != i:
                    self.menu_index = i
                    audio_mgr.play("hit_set")
                if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                    return self._activate_menu_item(i, current_diff, audio_mgr)

        # Keyboard / Gamepad Navigation
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
            self.show_settings_modal = True
            self.settings_index = 0
            return "SETTINGS", current_diff
        elif index == 3:
            self.show_controls_modal = True
            return "CONTROLS", current_diff
        elif index == 4:
            return "QUIT", current_diff
        return "NONE", current_diff

    def _update_settings_menu(self, input_mgr, audio_mgr, current_diff, cam_ctrl):
        """Interactions within the dedicated Settings modal."""
        # Navigation
        nav_up = pr.is_key_pressed(pr.KEY_W) or pr.is_key_pressed(pr.KEY_UP)
        nav_down = pr.is_key_pressed(pr.KEY_S) or pr.is_key_pressed(pr.KEY_DOWN)
        left = pr.is_key_pressed(pr.KEY_A) or pr.is_key_pressed(pr.KEY_LEFT)
        right = pr.is_key_pressed(pr.KEY_D) or pr.is_key_pressed(pr.KEY_RIGHT)
        enter = input_mgr.select_pressed or pr.is_key_pressed(pr.KEY_ENTER)
        esc = pr.is_key_pressed(pr.KEY_ESCAPE) or pr.is_key_pressed(pr.KEY_BACKSPACE)

        if nav_up:
            self.settings_index = (self.settings_index - 1) % len(self.settings_items)
            audio_mgr.play("hit_set")
        elif nav_down:
            self.settings_index = (self.settings_index + 1) % len(self.settings_items)
            audio_mgr.play("hit_set")

        # 0: MASTER VOLUME
        if self.settings_index == 0:
            if left:
                audio_mgr.change_volume(-0.1)
                audio_mgr.play("hit_bump")
            elif right:
                audio_mgr.change_volume(0.1)
                audio_mgr.play("hit_bump")

        # 1: SOUND FX
        elif self.settings_index == 1:
            if left or right or enter:
                audio_mgr.toggle_mute()
                audio_mgr.play("hit_bump")

        # 2: DISPLAY MODE (Windowed vs Borderless Fullscreen)
        elif self.settings_index == 2:
            if left or right or enter:
                self.is_fullscreen = not self.is_fullscreen
                pr.toggle_borderless_windowed()
                audio_mgr.play("hit_bump")

        # 3: RESOLUTION
        elif self.settings_index == 3:
            if left or right or enter:
                dir_step = 1 if (right or enter) else -1
                self.res_index = (self.res_index + dir_step) % len(RESOLUTIONS)
                w, h, _ = RESOLUTIONS[self.res_index]
                pr.set_window_size(w, h)
                audio_mgr.play("hit_bump")

        # 4: CAMERA ANGLE
        elif self.settings_index == 4:
            if (left or right or enter) and cam_ctrl:
                cam_ctrl.cycle_mode()
                audio_mgr.play("hit_bump")

        # 5: BACK
        elif self.settings_index == 5:
            if enter or pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                self.show_settings_modal = False
                audio_mgr.play("hit_set")

        if esc:
            self.show_settings_modal = False
            audio_mgr.play("hit_set")

        return "NONE", current_diff

    def draw_title_screen(self, current_diff, audio_mgr, input_mgr, cam_ctrl=None):
        """Draws Title screen matching pixel-perfect bounds."""
        card_w = self.CARD_W
        card_h = self.CARD_H
        card_x = self.CARD_X
        card_y = self.CARD_Y

        # Frosted Glass Card Background
        pr.draw_rectangle_rounded(pr.Rectangle(card_x, card_y, card_w, card_h), 0.12, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(card_x, card_y, card_w, card_h), 0.12, 10, 2, COLOR_GLASS_BORDER)

        # Title Header with 3D Drop Shadow
        title = "FLYHIGH!"
        tw = pr.measure_text(title, 52)
        pr.draw_text(title, card_x + (card_w - tw) // 2 + 2, card_y + 24 + 2, 52, pr.Color(10, 12, 18, 200))
        pr.draw_text(title, card_x + (card_w - tw) // 2, card_y + 24, 52, COLOR_CYAN_ACCENT)

        # Subtitle Tag (Clean ASCII)
        sub = "* 3v3 ARCADE VOLLEYBALL *"
        sw = pr.measure_text(sub, 15)
        tag_bg = pr.Rectangle(card_x + (card_w - sw - 32) // 2, card_y + 86, sw + 32, 26)
        pr.draw_rectangle_rounded(tag_bg, 0.4, 6, pr.Color(22, 32, 50, 240))
        pr.draw_rectangle_rounded_lines_ex(tag_bg, 0.4, 6, 1, COLOR_GOLD_ACCENT)
        pr.draw_text(sub, card_x + (card_w - sw) // 2, card_y + 91, 15, COLOR_GOLD_ACCENT)

        # Menu Buttons
        for i, item_text in enumerate(self.menu_items):
            by = self.BTN_START_Y + i * self.BTN_SPACING
            is_selected = (i == self.menu_index)

            bg_col = COLOR_BTN_HOVER if is_selected else COLOR_BTN_NORMAL
            border_col = COLOR_CYAN_ACCENT if is_selected else COLOR_BTN_BORDER
            border_thick = 2 if is_selected else 1

            rec = pr.Rectangle(self.BTN_X, by, self.BTN_W, self.BTN_H)
            pr.draw_rectangle_rounded(rec, 0.35, 8, bg_col)
            pr.draw_rectangle_rounded_lines_ex(rec, 0.35, 8, border_thick, border_col)

            # Button Content (100% English)
            if i == 0:
                txt = "> PLAY MATCH (3v3)"
                tcol = COLOR_GOLD_ACCENT if is_selected else COLOR_TEXT_MAIN
            elif i == 1:
                diff_label = current_diff.name
                txt = f"[=] DIFFICULTY: < {diff_label} >"
                tcol = COLOR_CYAN_ACCENT if is_selected else COLOR_TEXT_MAIN
            elif i == 2:
                txt = "[*] SETTINGS (AUDIO & VIDEO)"
                tcol = COLOR_TEXT_MAIN
            elif i == 3:
                txt = "[?] HOW TO PLAY & CONTROLS"
                tcol = COLOR_TEXT_MAIN
            else:
                txt = "[X] QUIT GAME"
                tcol = COLOR_CORAL_ACCENT if is_selected else COLOR_TEXT_MUTED

            tw_btn = pr.measure_text(txt, 17)
            pr.draw_text(txt, self.BTN_X + (self.BTN_W - tw_btn) // 2, by + 15, 17, tcol)

            if is_selected:
                pr.draw_circle(self.BTN_X + 22, by + self.BTN_H // 2, 4, COLOR_GOLD_ACCENT)
                pr.draw_circle(self.BTN_X + self.BTN_W - 22, by + self.BTN_H // 2, 4, COLOR_GOLD_ACCENT)

        # Pulsing prompt
        pulse_alpha = int(180 + 75 * math.sin(self.anim_timer * 5.0))
        prompt_txt = "PRESS [ENTER], [SPACE] OR CLICK TO SELECT"
        pw = pr.measure_text(prompt_txt, 13)
        pr.draw_text(prompt_txt, card_x + (card_w - pw) // 2, card_y + card_h - 26, 13, pr.Color(255, 215, 0, pulse_alpha))

        # Modals
        if self.show_settings_modal:
            self._draw_settings_modal(audio_mgr, cam_ctrl)
        elif self.show_controls_modal:
            self._draw_controls_modal()

    def _draw_settings_modal(self, audio_mgr, cam_ctrl):
        """Draws full-featured settings configuration panel."""
        pr.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, pr.Color(8, 10, 16, 220))

        mw = 620
        mh = 490
        mx = (SCREEN_WIDTH - mw) // 2
        my = (SCREEN_HEIGHT - mh) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(mx, my, mw, mh), 0.12, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(mx, my, mw, mh), 0.12, 10, 2, COLOR_GOLD_ACCENT)

        title = "GAME SETTINGS"
        tw = pr.measure_text(title, 26)
        pr.draw_text(title, mx + (mw - tw) // 2, my + 24, 26, COLOR_GOLD_ACCENT)

        # Settings rows
        start_y = my + 75
        row_h = 56
        for idx, item in enumerate(self.settings_items):
            ry = start_y + idx * row_h
            is_sel = (idx == self.settings_index)

            r_bg = COLOR_BTN_HOVER if is_sel else pr.Color(22, 28, 42, 210)
            r_border = COLOR_CYAN_ACCENT if is_sel else COLOR_GLASS_BORDER

            rec = pr.Rectangle(mx + 30, ry, mw - 60, 48)
            pr.draw_rectangle_rounded(rec, 0.28, 6, r_bg)
            pr.draw_rectangle_rounded_lines_ex(rec, 0.28, 6, 2 if is_sel else 1, r_border)

            lbl_col = COLOR_GOLD_ACCENT if is_sel else COLOR_TEXT_MAIN
            pr.draw_text(item, mx + 50, ry + 15, 16, lbl_col)

            # Option value column
            if idx == 0:
                # Volume bar
                vol_pct = int(audio_mgr.volume * 100)
                val_txt = f"< {vol_pct}% >"
                # Visual volume level ticks
                for b in range(10):
                    bar_col = COLOR_CYAN_ACCENT if (b * 10) < vol_pct else pr.Color(60, 70, 90, 200)
                    pr.draw_rectangle(mx + mw - 250 + b * 11, ry + 18, 8, 14, bar_col)
            elif idx == 1:
                val_txt = "[ ENABLED ]" if audio_mgr.enabled else "[ MUTED ]"
            elif idx == 2:
                val_txt = "< FULLSCREEN >" if self.is_fullscreen else "< WINDOWED >"
            elif idx == 3:
                _, _, res_lbl = RESOLUTIONS[self.res_index]
                val_txt = f"< {res_lbl} >"
            elif idx == 4:
                cam_name = cam_ctrl.get_mode_name() if cam_ctrl else "DEFAULT"
                val_txt = f"< {cam_name} >"
            else:
                val_txt = "[ PRESS ENTER ]"

            vw = pr.measure_text(val_txt, 15)
            val_col = COLOR_CYAN_ACCENT if is_sel else COLOR_TEXT_MUTED
            pr.draw_text(val_txt, mx + mw - vw - 50, ry + 16, 15, val_col)

        footer_txt = "[A / D] Adjust Option  |  [W / S] Navigate  |  [ESC] Close"
        fw = pr.measure_text(footer_txt, 14)
        pr.draw_text(footer_txt, mx + (mw - fw) // 2, my + mh - 30, 14, COLOR_TEXT_MUTED)

    def _draw_controls_modal(self):
        """Draws card-based How-to-Play controls guide in 100% English."""
        pr.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, pr.Color(8, 10, 16, 220))

        mw = 720
        mh = 540
        mx = (SCREEN_WIDTH - mw) // 2
        my = (SCREEN_HEIGHT - mh) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(mx, my, mw, mh), 0.12, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(mx, my, mw, mh), 0.12, 10, 2, COLOR_CYAN_ACCENT)

        title = "HOW TO PLAY - 3v3 VOLLEYBALL"
        tw = pr.measure_text(title, 24)
        pr.draw_text(title, mx + (mw - tw) // 2, my + 20, 24, COLOR_GOLD_ACCENT)

        controls = [
            ("MOVEMENT", "[W, A, S, D] (D = Screen Right)", "Left Analog / D-Pad"),
            ("AIM RETICLE", "Mouse Cursor (Court Floor)", "Right Stick"),
            ("JUMP", "[SPACE] (Always Active)", "(A) Button"),
            ("SERVE TOSS", "[SPACE] or [L-CLICK] to Toss", "(A) or (X)"),
            ("IN-AIR SPIKE", "[L-CLICK] (Shot Meter Timing)", "In-Air (A)"),
            ("FLOAT SERVE", "[L-CLICK + E] (Green Timing)", "In-Air (A) + (X)"),
            ("IN-AIR DUMP / TIP", "[E] (Soft Feather over Net)", "In-Air (X)"),
            ("AIR BAILOUT", "[L-CTRL + L-CLICK] (Emergency)", "In-Air (LT) + (A)"),
            ("PASS / SET", "[R-CLICK] (Overhead Pass)", "(Y) Button"),
            ("SETTER DUMP", "[R-CLICK + E] (Surprise Attack)", "(Y) + (X)"),
            ("RECEIVE / DIG", "[L-CTRL] (Directs to Cursor)", "(LT) / (X)"),
            ("ROLL DIG (5s CD)", "[L-CTRL + R-CLICK] (Dive Roll)", "(LT) + (Y)"),
        ]

        start_y = my + 60
        for idx, (label, kb, gp) in enumerate(controls):
            col_idx = idx % 2
            row_idx = idx // 2
            card_x = mx + 24 + col_idx * 340
            card_y = start_y + row_idx * 72

            c_rec = pr.Rectangle(card_x, card_y, 330, 64)
            pr.draw_rectangle_rounded(c_rec, 0.22, 6, pr.Color(22, 28, 42, 220))
            pr.draw_rectangle_rounded_lines_ex(c_rec, 0.22, 6, 1, COLOR_GLASS_BORDER)

            pr.draw_text(label, card_x + 12, card_y + 8, 13, COLOR_CYAN_ACCENT)
            pr.draw_text(f"PC: {kb}", card_x + 12, card_y + 26, 12, COLOR_TEXT_MAIN)
            pr.draw_text(f"Gamepad: {gp}", card_x + 12, card_y + 44, 12, COLOR_TEXT_MUTED)

        close_txt = "Press [ESC], [ENTER], or Click Anywhere to Close"
        cw = pr.measure_text(close_txt, 14)
        pr.draw_text(close_txt, mx + (mw - cw) // 2, my + mh - 26, 14, COLOR_GOLD_ACCENT)

    def draw_shot_meter(self, timing_ratio, is_visible):
        """Renders NBA 2K-Style Shot Timing Meter for jump serves and spikes."""
        dt = pr.get_frame_time()
        if self.shot_meter_feedback_timer > 0.0:
            self.shot_meter_feedback_timer -= dt

        # Feedback notification banner
        if self.shot_meter_feedback_timer > 0.0:
            fb_txt = self.shot_meter_feedback
            fw = pr.measure_text(fb_txt, 22)
            fx = (SCREEN_WIDTH - fw) // 2
            fy = SCREEN_HEIGHT // 2 + 65

            pr.draw_rectangle_rounded(pr.Rectangle(fx - 16, fy - 6, fw + 32, 34), 0.4, 6, pr.Color(16, 20, 30, 220))
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(fx - 16, fy - 6, fw + 32, 34), 0.4, 6, 2, self.shot_meter_feedback_col)
            pr.draw_text(fb_txt, fx, fy, 22, self.shot_meter_feedback_col)

        if not is_visible:
            return

        # Vertical Shot Meter Gauge
        gauge_w = 26
        gauge_h = 130
        gx = SCREEN_WIDTH // 2 + 160
        gy = SCREEN_HEIGHT // 2 - 80

        # Background track
        pr.draw_rectangle_rounded(pr.Rectangle(gx, gy, gauge_w, gauge_h), 0.5, 6, pr.Color(18, 22, 32, 230))
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(gx, gy, gauge_w, gauge_h), 0.5, 6, 2, COLOR_GLASS_BORDER)

        # Zones (Bottom = Red, Middle = Yellow, Top Sweet Spot = Neon Green)
        # 1. Red Zone (0.0 to 0.50)
        red_h = int(gauge_h * 0.50)
        pr.draw_rectangle(gx + 4, gy + gauge_h - red_h - 4, gauge_w - 8, red_h, pr.Color(220, 50, 60, 160))

        # 2. Yellow Zone (0.50 to 0.82)
        yel_h = int(gauge_h * 0.32)
        pr.draw_rectangle(gx + 4, gy + gauge_h - red_h - yel_h - 4, gauge_w - 8, yel_h, pr.Color(245, 200, 30, 180))

        # 3. Green Sweet-Spot Notch (0.82 to 1.0)
        grn_h = int(gauge_h * 0.18)
        pr.draw_rectangle(gx + 4, gy + 4, gauge_w - 8, grn_h, COLOR_GREEN_PERFECT)
        pr.draw_rectangle_lines(gx + 4, gy + 4, gauge_w - 8, grn_h, pr.Color(255, 255, 255, 240))

        # Dynamic Needle based on timing ratio (0.0 at bottom, 1.0 at top)
        clamped_ratio = max(0.0, min(1.0, timing_ratio))
        needle_y = gy + gauge_h - 4 - int((gauge_h - 8) * clamped_ratio)
        
        # Glow color based on current needle position
        needle_col = COLOR_GREEN_PERFECT if clamped_ratio >= 0.82 else (COLOR_GOLD_ACCENT if clamped_ratio >= 0.50 else COLOR_CORAL_ACCENT)
        pr.draw_rectangle(gx - 4, needle_y - 2, gauge_w + 8, 5, needle_col)
        pr.draw_circle(gx + gauge_w // 2, needle_y, 4, pr.Color(255, 255, 255, 255))

        # Header tag
        pr.draw_text("TIMING", gx - 8, gy - 20, 12, COLOR_GOLD_ACCENT)

    def draw_hud(self, match_mgr, input_mgr, cam_ctrl, ai_difficulty, player):
        """Draws scoreboard, touch counter, Roll Dig cooldown badge, and bottom control helper."""
        dt = pr.get_frame_time()
        if self.arcade_popup_timer > 0.0:
            self.arcade_popup_timer -= dt

        # 1. Top Scoreboard Pill
        bar_w = 540
        bar_h = 62
        bar_x = (SCREEN_WIDTH - bar_w) // 2
        bar_y = 12

        pr.draw_rectangle_rounded(pr.Rectangle(bar_x, bar_y, bar_w, bar_h), 0.4, 8, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bar_x, bar_y, bar_w, bar_h), 0.4, 8, 2, COLOR_GLASS_BORDER)

        # Team Player (Cyan Pill)
        pr.draw_rectangle_rounded(pr.Rectangle(bar_x + 14, bar_y + 10, 180, 42), 0.4, 6, pr.Color(20, 60, 110, 200))
        pr.draw_text("YOU (3v3)", bar_x + 28, bar_y + 22, 16, COLOR_CYAN_ACCENT)
        p_score = f"{match_mgr.score_player:02d}"
        pr.draw_text(p_score, bar_x + 140, bar_y + 14, 34, COLOR_CYAN_ACCENT)
        if match_mgr.serving_team == Team.PLAYER:
            pr.draw_circle(bar_x + 12, bar_y + bar_h // 2, 5, COLOR_GOLD_ACCENT)

        # Center Divider & Target
        pr.draw_text("VS", bar_x + bar_w // 2 - 12, bar_y + 12, 18, pr.GRAY)
        target_str = f"TO {match_mgr.points_to_win}"
        pr.draw_text(target_str, bar_x + bar_w // 2 - 22, bar_y + 36, 13, COLOR_GOLD_ACCENT)

        # Team Opponent (Crimson Pill)
        pr.draw_rectangle_rounded(pr.Rectangle(bar_x + bar_w - 194, bar_y + 10, 180, 42), 0.4, 6, pr.Color(110, 25, 40, 200))
        o_score = f"{match_mgr.score_opponent:02d}"
        pr.draw_text(o_score, bar_x + bar_w - 180, bar_y + 14, 34, COLOR_CORAL_ACCENT)
        pr.draw_text("CPU (3v3)", bar_x + bar_w - 124, bar_y + 22, 16, COLOR_CORAL_ACCENT)
        if match_mgr.serving_team == Team.OPPONENT:
            pr.draw_circle(bar_x + bar_w - 12, bar_y + bar_h // 2, 5, COLOR_GOLD_ACCENT)

        # 2. Touch Counter Badge
        if match_mgr.state == MatchState.IN_RALLY:
            touches = match_mgr.get_touches(Team.PLAYER)
            badge_w = 240
            badge_h = 36
            bx = (SCREEN_WIDTH - badge_w) // 2
            by = bar_y + bar_h + 10

            pr.draw_rectangle_rounded(pr.Rectangle(bx, by, badge_w, badge_h), 0.45, 6, COLOR_GLASS_BG)
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bx, by, badge_w, badge_h), 0.45, 6, 1, COLOR_GLASS_BORDER)

            if touches == 0:
                t_lbl = "TOUCH: 0/3 (READY)"
                t_col = COLOR_TEXT_MAIN
            elif touches == 1:
                t_lbl = "TOUCH: 1/3 (RECEIVE / DIG)"
                t_col = COLOR_CYAN_ACCENT
            elif touches == 2:
                t_lbl = "TOUCH: 2/3 (SET / OVERHEAD)"
                t_col = COLOR_GOLD_ACCENT
            else:
                t_lbl = "TOUCH: 3/3 (SPIKE ATTACK!)"
                t_col = COLOR_CORAL_ACCENT

            tw = pr.measure_text(t_lbl, 14)
            pr.draw_text(t_lbl, bx + (badge_w - tw) // 2, by + 11, 14, t_col)

        # 3. Dynamic Arcade Popup Banner
        if self.arcade_popup_timer > 0.0:
            p_text = self.arcade_popup_text
            pw = pr.measure_text(p_text, 36)
            p_x = (SCREEN_WIDTH - pw) // 2
            p_y = 145
            pr.draw_text(p_text, p_x + 2, p_y + 2, 36, pr.Color(10, 10, 15, 220))
            pr.draw_text(p_text, p_x, p_y, 36, self.arcade_popup_col)

        # 4. Roll Dig 5-Second Cooldown Badge
        cd = player.roll_dig_cooldown
        cd_w = 190
        cd_h = 32
        cd_x = 24
        cd_y = SCREEN_HEIGHT - 82

        pr.draw_rectangle_rounded(pr.Rectangle(cd_x, cd_y, cd_w, cd_h), 0.35, 6, COLOR_GLASS_BG)
        cd_border = COLOR_CYAN_ACCENT if cd <= 0.0 else COLOR_GLASS_BORDER
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cd_x, cd_y, cd_w, cd_h), 0.35, 6, 1, cd_border)

        if cd <= 0.0:
            cd_txt = "ROLL DIG: READY"
            pr.draw_text(cd_txt, cd_x + 12, cd_y + 9, 13, COLOR_CYAN_ACCENT)
            pr.draw_circle(cd_x + cd_w - 18, cd_y + 16, 5, COLOR_GREEN_PERFECT)
        else:
            cd_txt = f"ROLL DIG: {cd:.1f}s"
            pr.draw_text(cd_txt, cd_x + 12, cd_y + 9, 13, COLOR_TEXT_MUTED)
            # Refill progress bar
            prog = 1.0 - (cd / ROLL_DIG_COOLDOWN)
            pr.draw_rectangle(cd_x + cd_w - 55, cd_y + 12, int(40 * prog), 8, COLOR_GOLD_ACCENT)
            pr.draw_rectangle_lines(cd_x + cd_w - 55, cd_y + 12, 40, 8, COLOR_GLASS_BORDER)

        # 5. Bottom Control Helper Bar (100% English)
        bot_h = 38
        bot_y = SCREEN_HEIGHT - bot_h - 8
        bot_w = SCREEN_WIDTH - 48
        bot_x = 24

        pr.draw_rectangle_rounded(pr.Rectangle(bot_x, bot_y, bot_w, bot_h), 0.35, 6, pr.Color(12, 16, 24, 220))
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bot_x, bot_y, bot_w, bot_h), 0.35, 6, 1, COLOR_GLASS_BORDER)

        device = input_mgr.active_device
        if device == "GAMEPAD":
            ctrl_str = "[L-STICK] Move | (A) Jump/Spike | (X) Dump | (Y) Set | (LT) Dig | (LT+Y) Roll Dig | (BACK) Cam"
        else:
            ctrl_str = "[WASD] Move | [SPACE] Jump | [LMB] Spike | [LMB+E] Float Serve | [E] Dump | [RMB] Set | [L-CTRL] Dig | [L-CTRL+RMB] Roll Dig"

        pr.draw_text(f"CONTROLS ({device}):", bot_x + 14, bot_y + 12, 12, COLOR_GOLD_ACCENT)
        pr.draw_text(ctrl_str, bot_x + 165, bot_y + 12, 12, COLOR_TEXT_MAIN)

        # Top-left and Top-right info
        cam_info = f"CAM: {cam_ctrl.get_mode_name()} [TAB]"
        pr.draw_text(cam_info, 18, 16, 13, COLOR_TEXT_MUTED)
        diff_info = f"AI: {ai_difficulty.name}"
        dw = pr.measure_text(diff_info, 13)
        pr.draw_text(diff_info, SCREEN_WIDTH - dw - 18, 16, 13, COLOR_TEXT_MUTED)

    def draw_serve_prompt(self, match_mgr, input_mgr):
        """Displays clear serving prompt with 100% clean English text."""
        if match_mgr.state == MatchState.SERVE_READY:
            card_w = 540
            card_h = 54
            cx = (SCREEN_WIDTH - card_w) // 2
            cy = 135

            pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, COLOR_GLASS_BG)
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, 2, COLOR_GOLD_ACCENT)

            if match_mgr.serving_team == Team.PLAYER:
                txt = "YOUR SERVE: Press [SPACE] or [L-CLICK] to Toss the Ball!"
                col = COLOR_GOLD_ACCENT
            else:
                txt = "OPPONENT SERVING... Get Ready to Dig with [L-CTRL]!"
                col = COLOR_CORAL_ACCENT

            tw = pr.measure_text(txt, 15)
            pr.draw_text(txt, cx + (card_w - tw) // 2, cy + 18, 15, col)

        elif match_mgr.state == MatchState.SERVE_TOSSED:
            card_w = 600
            card_h = 54
            cx = (SCREEN_WIDTH - card_w) // 2
            cy = 135

            pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, COLOR_GLASS_BG)
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, 2, COLOR_CYAN_ACCENT)

            if match_mgr.serving_team == Team.PLAYER:
                txt = "HIT: Jump [SPACE] -> [L-CLICK] Power Spike | [L-CLICK + E] Float Serve"
                col = COLOR_CYAN_ACCENT
            else:
                txt = "BALL INCOMING! Aim Cursor and Hold [L-CTRL] to Dig!"
                col = COLOR_CORAL_ACCENT

            tw = pr.measure_text(txt, 14)
            pr.draw_text(txt, cx + (card_w - tw) // 2, cy + 18, 14, col)

    def draw_point_banner(self, match_mgr):
        """Displays point award banner in 100% English."""
        if match_mgr.state == MatchState.POINT_SCORED:
            banner_w = 540
            banner_h = 95
            bx = (SCREEN_WIDTH - banner_w) // 2
            by = SCREEN_HEIGHT // 2 - 95

            pr.draw_rectangle_rounded(pr.Rectangle(bx, by, banner_w, banner_h), 0.3, 8, COLOR_GLASS_BG)
            winner_col = COLOR_CYAN_ACCENT if match_mgr.point_winner == Team.PLAYER else COLOR_CORAL_ACCENT
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bx, by, banner_w, banner_h), 0.3, 8, 3, winner_col)

            win_title = "POINT FOR YOU! (3v3)" if match_mgr.point_winner == Team.PLAYER else "POINT FOR OPPONENT"
            tw1 = pr.measure_text(win_title, 25)
            pr.draw_text(win_title, bx + (banner_w - tw1) // 2, by + 16, 25, winner_col)

            reason_str = match_mgr.point_reason
            tw2 = pr.measure_text(reason_str, 17)
            pr.draw_text(reason_str, bx + (banner_w - tw2) // 2, by + 56, 17, COLOR_TEXT_MAIN)

    def draw_match_over(self, match_mgr, input_mgr):
        """Draws match end screen in 100% English."""
        if match_mgr.state == MatchState.MATCH_OVER:
            pr.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, pr.Color(8, 10, 16, 220))

            card_w = 580
            card_h = 290
            cx = (SCREEN_WIDTH - card_w) // 2
            cy = (SCREEN_HEIGHT - card_h) // 2

            pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, COLOR_GLASS_BG)
            win_col = COLOR_GOLD_ACCENT if match_mgr.winner == Team.PLAYER else COLOR_CORAL_ACCENT
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, 3, win_col)

            main_text = "MATCH WON! (VICTORY)" if match_mgr.winner == Team.PLAYER else "MATCH OVER (DEFEAT)"
            tw = pr.measure_text(main_text, 30)
            pr.draw_text(main_text, cx + (card_w - tw) // 2, cy + 30, 30, win_col)

            score_text = f"Final Score: YOU {match_mgr.score_player} - {match_mgr.score_opponent} CPU"
            sw = pr.measure_text(score_text, 22)
            pr.draw_text(score_text, cx + (card_w - sw) // 2, cy + 95, 22, COLOR_TEXT_MAIN)

            rematch_text = "[SPACE] or [L-CLICK] for Rematch"
            rw = pr.measure_text(rematch_text, 19)
            pr.draw_text(rematch_text, cx + (card_w - rw) // 2, cy + 160, 19, COLOR_GOLD_ACCENT)

            quit_text = "[ESC] / (START) Return to Title Menu"
            qw = pr.measure_text(quit_text, 15)
            pr.draw_text(quit_text, cx + (card_w - qw) // 2, cy + 220, 15, COLOR_TEXT_MUTED)

    def draw_pause_menu(self, input_mgr, audio_mgr, cam_ctrl=None):
        """Draws Pause overlay with settings option."""
        if self.show_settings_modal:
            self._draw_settings_modal(audio_mgr, cam_ctrl)
            return

        pr.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, pr.Color(8, 10, 16, 190))
        
        card_w = 500
        card_h = 300
        cx = (SCREEN_WIDTH - card_w) // 2
        cy = (SCREEN_HEIGHT - card_h) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, 2, COLOR_GLASS_BORDER)

        title = "MATCH PAUSED"
        tw = pr.measure_text(title, 26)
        pr.draw_text(title, cx + (card_w - tw) // 2, cy + 24, 26, COLOR_TEXT_MAIN)

        pr.draw_text("[ESC] / (START)  Resume Match", cx + 75, cy + 80, 16, COLOR_GOLD_ACCENT)
        pr.draw_text("[S]              Settings (Audio & Video)", cx + 75, cy + 120, 16, COLOR_CYAN_ACCENT)
        pr.draw_text("[TAB] / (BACK)   Change Camera Angle", cx + 75, cy + 160, 16, COLOR_TEXT_MAIN)
        pr.draw_text("[M]              Mute Sound Toggle", cx + 75, cy + 200, 16, COLOR_TEXT_MAIN)
        pr.draw_text("[Q]              Quit to Title Menu", cx + 75, cy + 240, 16, COLOR_CORAL_ACCENT)
