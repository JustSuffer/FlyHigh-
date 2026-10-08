"""
FlyHigh! - 3D Volleyball Game
Modern Arcade UI & HUD Renderer (100% Smooth Anti-Aliased Vector Fonts & Clean English)
Features:
- High-resolution Segoe UI vector font rendering (zero blocky/pixelated text!)
- Pixel-perfect mouse hover and click detection on menu buttons
- Full Settings Menu (Master Volume, Sound FX, Fullscreen, Resolution, Camera)
- NBA 2K-Style Shot Timing Meter (Green / Yellow / Red contact windows)
- Roll Dig 5-second cooldown indicator badge
- Dynamic animated arcade popups ("PERFECT TIMING!", "BOOM SPIKE!!", "FLOAT SERVE!", "ROLL DIG!")
- Comprehensive card-based "How to Play" controls guide
"""
import pyray as pr
import math
import os
import sys
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, Team, MatchState, AIDifficulty,
    TimingRating, ROLL_DIG_COOLDOWN, RESOLUTIONS
)

def get_asset_path(subpath):
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        p = os.path.join(base_dir, subpath)
        if os.path.exists(p):
            return p
        return os.path.join(os.path.dirname(sys.executable), subpath)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, subpath)

# Modern Arcade Color Palette
COLOR_GLASS_BG      = pr.Color(16, 20, 30, 240)
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
    # Title Menu Layout - Spacious modern arcade design (Zero Overlap)
    CARD_W = 480
    CARD_H = 600
    CARD_X = (SCREEN_WIDTH - 480) // 2
    CARD_Y = (SCREEN_HEIGHT - 600) // 2

    BTN_W = 420
    BTN_H = 50
    BTN_START_Y = (SCREEN_HEIGHT - 600) // 2 + 162
    BTN_SPACING = 64
    BTN_X = (SCREEN_WIDTH - 480) // 2 + 30

    def __init__(self):
        # Load high-resolution smooth vector fonts
        self.font_regular = None
        self.font_bold = None
        self._init_fonts()

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

    def _init_fonts(self):
        """Loads smooth vector TTF fonts with bilinear filtering."""
        try:
            reg_path = get_asset_path(os.path.join("assets", "fonts", "font_regular.ttf"))
            bold_path = get_asset_path(os.path.join("assets", "fonts", "font_bold.ttf"))
            if os.path.exists(reg_path):
                self.font_regular = pr.load_font_ex(reg_path, 64, None, 0)
                pr.set_texture_filter(self.font_regular.texture, pr.TEXTURE_FILTER_BILINEAR)
            if os.path.exists(bold_path):
                self.font_bold = pr.load_font_ex(bold_path, 64, None, 0)
                pr.set_texture_filter(self.font_bold.texture, pr.TEXTURE_FILTER_BILINEAR)
        except Exception as e:
            print(f"[UI] Font loading notice: {e}")

    def cleanup(self):
        if self.font_regular is not None:
            try:
                pr.unload_font(self.font_regular)
            except Exception:
                pass
        if self.font_bold is not None:
            try:
                pr.unload_font(self.font_bold)
            except Exception:
                pass

    def draw_text(self, text, x, y, size, color, bold=False):
        """Draws crisp vector text with smooth bilinear anti-aliasing."""
        font = self.font_bold if bold else (self.font_regular or self.font_bold)
        if font is not None:
            pr.draw_text_ex(font, str(text), pr.Vector2(float(x), float(y)), float(size), 1.0, color)
        else:
            pr.draw_text(str(text), int(x), int(y), int(size), color)

    def measure_text(self, text, size, bold=False) -> int:
        """Measures vector text width accurately."""
        font = self.font_bold if bold else (self.font_regular or self.font_bold)
        if font is not None:
            vec = pr.measure_text_ex(font, str(text), float(size), 1.0)
            return int(vec.x)
        return pr.measure_text(str(text), int(size))

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
        """Draws modern Title screen with smooth vector fonts and zero element overlap."""
        card_w = self.CARD_W
        card_h = self.CARD_H
        card_x = self.CARD_X
        card_y = self.CARD_Y

        # Frosted Glass Card Background with Glowing Border
        pr.draw_rectangle_rounded(pr.Rectangle(card_x, card_y, card_w, card_h), 0.14, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(card_x, card_y, card_w, card_h), 0.14, 10, 2, COLOR_GLASS_BORDER)

        # 1. Stylized Mini Volleyball Emblem at Card Top
        icon_cx = card_x + card_w // 2
        icon_cy = card_y + 32
        pr.draw_circle(icon_cx, icon_cy, 14, pr.Color(250, 252, 255, 255))
        pr.draw_circle_lines(icon_cx, icon_cy, 14, COLOR_GOLD_ACCENT)
        # Curved seams
        pr.draw_line(icon_cx - 8, icon_cy - 5, icon_cx + 8, icon_cy + 5, COLOR_CYAN_ACCENT)
        pr.draw_line(icon_cx - 5, icon_cy + 8, icon_cx + 5, icon_cy - 8, COLOR_GOLD_ACCENT)

        # 2. Title Header with 3D Drop Shadow
        title = "FLYHIGH!"
        tw = self.measure_text(title, 44, bold=True)
        # Soft Drop Shadow
        self.draw_text(title, card_x + (card_w - tw) // 2 + 2, card_y + 54 + 2, 44, pr.Color(10, 12, 18, 220), bold=True)
        # Foreground Title Text
        self.draw_text(title, card_x + (card_w - tw) // 2, card_y + 54, 44, COLOR_CYAN_ACCENT, bold=True)

        # 3. Subtitle Badge (Completely separated with clear margin)
        sub = "3v3 ARCADE VOLLEYBALL"
        sw = self.measure_text(sub, 13, bold=True)
        tag_w = sw + 32
        tag_h = 24
        tag_x = card_x + (card_w - tag_w) // 2
        tag_y = card_y + 108
        pr.draw_rectangle_rounded(pr.Rectangle(tag_x, tag_y, tag_w, tag_h), 0.45, 6, pr.Color(20, 28, 44, 240))
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(tag_x, tag_y, tag_w, tag_h), 0.45, 6, 1, COLOR_GOLD_ACCENT)
        self.draw_text(sub, tag_x + 16, tag_y + 4, 13, COLOR_GOLD_ACCENT, bold=True)

        # 4. Menu Buttons (Strictly start at BTN_START_Y = card_y + 162, zero overlap)
        for i, item_text in enumerate(self.menu_items):
            by = self.BTN_START_Y + i * self.BTN_SPACING
            is_selected = (i == self.menu_index)

            bg_col = COLOR_BTN_HOVER if is_selected else COLOR_BTN_NORMAL
            border_col = COLOR_CYAN_ACCENT if is_selected else COLOR_BTN_BORDER
            border_thick = 2 if is_selected else 1

            rec = pr.Rectangle(self.BTN_X, by, self.BTN_W, self.BTN_H)
            pr.draw_rectangle_rounded(rec, 0.35, 8, bg_col)
            pr.draw_rectangle_rounded_lines_ex(rec, 0.35, 8, border_thick, border_col)

            # Button Content (100% English & cleanly aligned)
            if i == 0:
                txt = "Play Match (3v3)"
                tcol = COLOR_GOLD_ACCENT if is_selected else COLOR_TEXT_MAIN
            elif i == 1:
                diff_label = current_diff.name
                txt = f"Difficulty: < {diff_label} >"
                tcol = COLOR_CYAN_ACCENT if is_selected else COLOR_TEXT_MAIN
            elif i == 2:
                txt = "Settings (Audio & Video)"
                tcol = COLOR_TEXT_MAIN
            elif i == 3:
                txt = "How to Play & Controls"
                tcol = COLOR_TEXT_MAIN
            else:
                txt = "Quit Game"
                tcol = COLOR_CORAL_ACCENT if is_selected else COLOR_TEXT_MUTED

            tw_btn = self.measure_text(txt, 17, bold=is_selected)
            self.draw_text(txt, self.BTN_X + (self.BTN_W - tw_btn) // 2, by + 14, 17, tcol, bold=is_selected)

            # Left Active Accent Pill on selection
            if is_selected:
                pr.draw_rectangle_rounded(pr.Rectangle(self.BTN_X + 10, by + 12, 5, 26), 0.5, 4, COLOR_GOLD_ACCENT)
                pr.draw_circle(self.BTN_X + self.BTN_W - 18, by + self.BTN_H // 2, 4, COLOR_GOLD_ACCENT)

        # 5. Bottom Navigation Hint Badge
        hint_y = card_y + card_h - 40
        hint_txt = "[W / S] Navigate   •   [ENTER] Select   •   [CLICK] Choose"
        hw = self.measure_text(hint_txt, 13, bold=False)
        pr.draw_rectangle_rounded(pr.Rectangle(card_x + 30, hint_y - 4, card_w - 60, 26), 0.35, 6, pr.Color(16, 22, 34, 190))
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(card_x + 30, hint_y - 4, card_w - 60, 26), 0.35, 6, 1, COLOR_GLASS_BORDER)
        self.draw_text(hint_txt, card_x + (card_w - hw) // 2, hint_y + 2, 13, COLOR_TEXT_MUTED, bold=False)

        # Modals
        if self.show_settings_modal:
            self._draw_settings_modal(audio_mgr, cam_ctrl)
        elif self.show_controls_modal:
            self._draw_controls_modal()

    def _draw_settings_modal(self, audio_mgr, cam_ctrl):
        """Draws full-featured settings configuration panel with smooth vector fonts."""
        pr.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, pr.Color(8, 10, 16, 225))

        mw = 640
        mh = 500
        mx = (SCREEN_WIDTH - mw) // 2
        my = (SCREEN_HEIGHT - mh) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(mx, my, mw, mh), 0.12, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(mx, my, mw, mh), 0.12, 10, 2, COLOR_GOLD_ACCENT)

        title = "GAME SETTINGS"
        tw = self.measure_text(title, 26, bold=True)
        self.draw_text(title, mx + (mw - tw) // 2, my + 24, 26, COLOR_GOLD_ACCENT, bold=True)

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
            self.draw_text(item, mx + 50, ry + 14, 16, lbl_col, bold=is_sel)

            if idx == 0:
                vol_pct = int(audio_mgr.volume * 100)
                val_txt = f"< {vol_pct}% >"
                for b in range(10):
                    bar_col = COLOR_CYAN_ACCENT if (b * 10) < vol_pct else pr.Color(60, 70, 90, 200)
                    pr.draw_rectangle(mx + mw - 250 + b * 11, ry + 18, 8, 14, bar_col)
            elif idx == 1:
                val_txt = "[ Enabled ]" if audio_mgr.enabled else "[ Muted ]"
            elif idx == 2:
                val_txt = "< Fullscreen >" if self.is_fullscreen else "< Windowed >"
            elif idx == 3:
                _, _, res_lbl = RESOLUTIONS[self.res_index]
                val_txt = f"< {res_lbl} >"
            elif idx == 4:
                cam_name = cam_ctrl.get_mode_name() if cam_ctrl else "DEFAULT"
                val_txt = f"< {cam_name} >"
            else:
                val_txt = "[ Press Enter ]"

            vw = self.measure_text(val_txt, 15, bold=is_sel)
            val_col = COLOR_CYAN_ACCENT if is_sel else COLOR_TEXT_MUTED
            self.draw_text(val_txt, mx + mw - vw - 50, ry + 14, 15, val_col, bold=is_sel)

        footer_txt = "[A / D] Adjust Option   |   [W / S] Navigate   |   [ESC] Close"
        fw = self.measure_text(footer_txt, 14, bold=False)
        self.draw_text(footer_txt, mx + (mw - fw) // 2, my + mh - 28, 14, COLOR_TEXT_MUTED, bold=False)

    def _draw_controls_modal(self):
        """Draws card-based How-to-Play controls guide in smooth modern vector font."""
        pr.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, pr.Color(8, 10, 16, 225))

        mw = 740
        mh = 550
        mx = (SCREEN_WIDTH - mw) // 2
        my = (SCREEN_HEIGHT - mh) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(mx, my, mw, mh), 0.12, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(mx, my, mw, mh), 0.12, 10, 2, COLOR_CYAN_ACCENT)

        title = "HOW TO PLAY - 3v3 VOLLEYBALL"
        tw = self.measure_text(title, 24, bold=True)
        self.draw_text(title, mx + (mw - tw) // 2, my + 18, 24, COLOR_GOLD_ACCENT, bold=True)

        controls = [
            ("MOVEMENT", "[W, A, S, D] (D = Screen Right)", "Left Stick / D-Pad"),
            ("AIM RETICLE", "Mouse Cursor (Court Floor)", "Right Stick"),
            ("HOLD / TOSS SERVE", "[R-CLICK] to Toss into Air", "(Y) Button"),
            ("JUMP", "[SPACE] (Always Active)", "(A) Button"),
            ("POWER SPIKE (IN-AIR)", "[L-CLICK] (Shot Meter Timing)", "In-Air (A)"),
            ("FLOAT SERVE (IN-AIR)", "[L-CLICK + E] (Green Timing)", "In-Air (A) + (X)"),
            ("DUMP / TIP (IN-AIR)", "[E] (Soft Feather over Net)", "In-Air (X)"),
            ("AIR BAILOUT (IN-AIR)", "[L-CTRL + L-CLICK] (Emergency)", "In-Air (LT) + (A)"),
            ("PASS / SET (GROUND)", "[R-CLICK] (Overhead Pass)", "(Y) Button"),
            ("SETTER DUMP", "[R-CLICK + E] (Surprise Attack)", "(Y) + (X)"),
            ("RECEIVE / DIG", "[L-CTRL] (Directs to Cursor)", "(LT) / (X)"),
            ("ROLL DIG (5s CD)", "[L-CTRL + R-CLICK] (Dive Roll)", "(LT) + (Y)"),
        ]

        start_y = my + 56
        for idx, (label, kb, gp) in enumerate(controls):
            col_idx = idx % 2
            row_idx = idx // 2
            card_x = mx + 22 + col_idx * 350
            card_y = start_y + row_idx * 74

            c_rec = pr.Rectangle(card_x, card_y, 340, 66)
            pr.draw_rectangle_rounded(c_rec, 0.22, 6, pr.Color(22, 28, 42, 220))
            pr.draw_rectangle_rounded_lines_ex(c_rec, 0.22, 6, 1, COLOR_GLASS_BORDER)

            self.draw_text(label, card_x + 12, card_y + 8, 14, COLOR_CYAN_ACCENT, bold=True)
            self.draw_text(f"PC: {kb}", card_x + 12, card_y + 26, 12, COLOR_TEXT_MAIN, bold=False)
            self.draw_text(f"Gamepad: {gp}", card_x + 12, card_y + 44, 12, COLOR_TEXT_MUTED, bold=False)

        close_txt = "Press [ESC], [Enter], or Click Anywhere to Close"
        cw = self.measure_text(close_txt, 14, bold=False)
        self.draw_text(close_txt, mx + (mw - cw) // 2, my + mh - 26, 14, COLOR_GOLD_ACCENT, bold=False)

    def draw_shot_meter(self, timing_ratio, is_visible):
        """Renders NBA 2K-Style Shot Timing Meter with clean fonts."""
        dt = pr.get_frame_time()
        if self.shot_meter_feedback_timer > 0.0:
            self.shot_meter_feedback_timer -= dt

        # Feedback notification banner
        if self.shot_meter_feedback_timer > 0.0:
            fb_txt = self.shot_meter_feedback
            fw = self.measure_text(fb_txt, 22, bold=True)
            fx = (SCREEN_WIDTH - fw) // 2
            fy = SCREEN_HEIGHT // 2 + 65

            pr.draw_rectangle_rounded(pr.Rectangle(fx - 18, fy - 6, fw + 36, 36), 0.4, 6, pr.Color(16, 20, 30, 230))
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(fx - 18, fy - 6, fw + 36, 36), 0.4, 6, 2, self.shot_meter_feedback_col)
            self.draw_text(fb_txt, fx, fy, 22, self.shot_meter_feedback_col, bold=True)

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

        # Dynamic Needle
        clamped_ratio = max(0.0, min(1.0, timing_ratio))
        needle_y = gy + gauge_h - 4 - int((gauge_h - 8) * clamped_ratio)
        
        needle_col = COLOR_GREEN_PERFECT if clamped_ratio >= 0.82 else (COLOR_GOLD_ACCENT if clamped_ratio >= 0.50 else COLOR_CORAL_ACCENT)
        pr.draw_rectangle(gx - 4, needle_y - 2, gauge_w + 8, 5, needle_col)
        pr.draw_circle(gx + gauge_w // 2, needle_y, 4, pr.Color(255, 255, 255, 255))

        self.draw_text("TIMING", gx - 8, gy - 20, 12, COLOR_GOLD_ACCENT, bold=True)

    def draw_hud(self, match_mgr, input_mgr, cam_ctrl, ai_difficulty, player):
        """Draws modern scoreboard, touch counter, and bottom control helper."""
        dt = pr.get_frame_time()
        if self.arcade_popup_timer > 0.0:
            self.arcade_popup_timer -= dt

        # 1. TOP SCOREBOARD PILL (Matching Reference Screenshots)
        main_w = 320
        main_h = 48
        main_x = (SCREEN_WIDTH - main_w) // 2
        main_y = 14

        # Pill background container
        pr.draw_rectangle_rounded(pr.Rectangle(main_x, main_y, main_w, main_h), 0.5, 8, pr.Color(245, 248, 255, 235))
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(main_x, main_y, main_w, main_h), 0.5, 8, 2, pr.Color(20, 24, 35, 60))

        # Left badge: "home" in lime-green pill
        hw = 68
        hh = 34
        pr.draw_rectangle_rounded(pr.Rectangle(main_x + 8, main_y + 7, hw, hh), 0.5, 6, pr.Color(60, 215, 110, 255))
        self.draw_text("home", main_x + 20, main_y + 16, 14, pr.Color(255, 255, 255, 255), bold=True)

        # Center score: "1 - 1" in bold numbers
        score_str = f"{match_mgr.score_player}  -  {match_mgr.score_opponent}"
        sw = self.measure_text(score_str, 24, bold=True)
        self.draw_text(score_str, main_x + (main_w - sw) // 2, main_y + 12, 24, pr.Color(24, 28, 38, 255), bold=True)

        # Right badge: "away" in magenta/pink pill
        aw = 68
        ah = 34
        pr.draw_rectangle_rounded(pr.Rectangle(main_x + main_w - aw - 8, main_y + 7, aw, ah), 0.5, 6, pr.Color(245, 55, 130, 255))
        self.draw_text("away", main_x + main_w - aw + 14, main_y + 16, 14, pr.Color(255, 255, 255, 255), bold=True)

        # Sub-pill 1: Set score ("O  O  set 1  O  O")
        sub1_w = 175
        sub1_h = 24
        sub1_x = (SCREEN_WIDTH - sub1_w) // 2
        sub1_y = main_y + main_h + 4
        pr.draw_rectangle_rounded(pr.Rectangle(sub1_x, sub1_y, sub1_w, sub1_h), 0.5, 6, pr.Color(245, 248, 255, 220))
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(sub1_x, sub1_y, sub1_w, sub1_h), 0.5, 6, 1, pr.Color(20, 24, 35, 40))
        # Home set dot
        sets_p = getattr(match_mgr, 'sets_player', 0)
        sets_o = getattr(match_mgr, 'sets_opponent', 0)
        c_set = getattr(match_mgr, 'current_set', 1)
        pr.draw_circle(sub1_x + 22, sub1_y + 12, 4, pr.Color(60, 215, 110, 255) if sets_p > 0 else pr.Color(180, 190, 200, 255))
        # Text "set 1"
        set_str = f"set {c_set}"
        stw = self.measure_text(set_str, 12, bold=True)
        self.draw_text(set_str, sub1_x + (sub1_w - stw) // 2, sub1_y + 6, 12, pr.Color(40, 45, 55, 255), bold=True)
        # Away set dot
        pr.draw_circle(sub1_x + sub1_w - 22, sub1_y + 12, 4, pr.Color(245, 55, 130, 255) if sets_o > 0 else pr.Color(180, 190, 200, 255))

        # Sub-pill 2: 3-Touch Light Indicator ("● ● ●")
        sub2_w = 64
        sub2_h = 22
        sub2_x = (SCREEN_WIDTH - sub2_w) // 2
        sub2_y = sub1_y + sub1_h + 4
        pr.draw_rectangle_rounded(pr.Rectangle(sub2_x, sub2_y, sub2_w, sub2_h), 0.5, 6, pr.Color(245, 248, 255, 220))
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(sub2_x, sub2_y, sub2_w, sub2_h), 0.5, 6, 1, pr.Color(20, 24, 35, 40))

        # Current touches on the team that currently has the ball
        cur_touches = match_mgr.get_touches(match_mgr.last_touch_team if match_mgr.last_touch_team else Team.PLAYER)
        c1 = pr.Color(60, 215, 110, 255) if cur_touches >= 1 else pr.Color(190, 195, 205, 180)
        c2 = pr.Color(255, 205, 40, 255) if cur_touches >= 2 else pr.Color(190, 195, 205, 180)
        c3 = pr.Color(245, 60, 75, 255) if cur_touches >= 3 else pr.Color(190, 195, 205, 180)
        pr.draw_circle(sub2_x + 16, sub2_y + 11, 4, c1)
        pr.draw_circle(sub2_x + 32, sub2_y + 11, 4, c2)
        pr.draw_circle(sub2_x + 48, sub2_y + 11, 4, c3)

        # 2. Dynamic Arcade Popup Banner
        if self.arcade_popup_timer > 0.0:
            p_text = self.arcade_popup_text
            pw = self.measure_text(p_text, 36, bold=True)
            p_x = (SCREEN_WIDTH - pw) // 2
            p_y = 150
            self.draw_text(p_text, p_x + 2, p_y + 2, 36, pr.Color(10, 10, 15, 220), bold=True)
            self.draw_text(p_text, p_x, p_y, 36, self.arcade_popup_col, bold=True)

        # 3. Roll Dig 5-Second Cooldown Badge
        cd = player.roll_dig_cooldown
        cd_w = 175
        cd_h = 32
        cd_x = 24
        cd_y = SCREEN_HEIGHT - 60

        pr.draw_rectangle_rounded(pr.Rectangle(cd_x, cd_y, cd_w, cd_h), 0.35, 6, pr.Color(16, 20, 30, 210))
        cd_border = COLOR_CYAN_ACCENT if cd <= 0.0 else COLOR_GLASS_BORDER
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cd_x, cd_y, cd_w, cd_h), 0.35, 6, 1, cd_border)

        if cd <= 0.0:
            cd_txt = "ROLL DIG: READY"
            self.draw_text(cd_txt, cd_x + 12, cd_y + 8, 12, COLOR_CYAN_ACCENT, bold=True)
            pr.draw_circle(cd_x + cd_w - 18, cd_y + 16, 4, COLOR_GREEN_PERFECT)
        else:
            cd_txt = f"ROLL DIG: {cd:.1f}s"
            self.draw_text(cd_txt, cd_x + 12, cd_y + 8, 12, COLOR_TEXT_MUTED, bold=False)
            prog = 1.0 - (cd / ROLL_DIG_COOLDOWN)
            pr.draw_rectangle(cd_x + cd_w - 50, cd_y + 12, int(35 * prog), 6, COLOR_GOLD_ACCENT)

        # 4. Modern Vertical Control Helper Stack on Right Screen (Matching Reference Image)
        cw = 170
        ch = 22
        controls = [
            ("camera", "[C] / [TAB]"),
            ("strafe", "[W][A][S][D]"),
            ("jump", "[SPACE] (Hold Super)"),
            ("dive", "[SHIFT] / [L-CTRL+RMB]"),
            ("set", "[R-CLICK]"),
            ("spike", "[L-CLICK]"),
            ("block", "[R-CLICK in air]"),
            ("tip", "[E]"),
        ]
        cy_base = SCREEN_HEIGHT - (len(controls) * 25) - 16
        cx = SCREEN_WIDTH - cw - 16

        for idx, (action_name, key_name) in enumerate(controls):
            item_y = cy_base + idx * 25
            pr.draw_rectangle_rounded(pr.Rectangle(cx, item_y, cw, ch), 0.35, 4, pr.Color(16, 20, 30, 200))
            self.draw_text(action_name, cx + 8, item_y + 5, 11, pr.Color(200, 210, 225, 255), bold=False)
            kw = self.measure_text(key_name, 11, bold=True)
            self.draw_text(key_name, cx + cw - kw - 6, item_y + 5, 11, COLOR_GOLD_ACCENT, bold=True)

        # Top-left camera & AI info
        cam_info = f"CAM: {cam_ctrl.get_mode_name()} [C]"
        self.draw_text(cam_info, 18, 16, 13, COLOR_TEXT_MUTED, bold=False)
        diff_info = f"AI: {ai_difficulty.name}"
        self.draw_text(diff_info, 18, 36, 13, COLOR_TEXT_MUTED, bold=False)

    def draw_serve_prompt(self, match_mgr, input_mgr):
        """Displays clear serving prompt with explicit RIGHT-CLICK toss instruction."""
        if match_mgr.state == MatchState.SERVE_READY:
            card_w = 560
            card_h = 54
            cx = (SCREEN_WIDTH - card_w) // 2
            cy = 135

            pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, COLOR_GLASS_BG)
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, 2, COLOR_GOLD_ACCENT)

            if match_mgr.serving_team == Team.PLAYER:
                txt = "HOLDING BALL: Press [RIGHT CLICK] to Toss the Ball!"
                col = COLOR_GOLD_ACCENT
            else:
                txt = "OPPONENT SERVING... Get Ready to Dig with [L-CTRL]!"
                col = COLOR_CORAL_ACCENT

            tw = self.measure_text(txt, 16, bold=True)
            self.draw_text(txt, cx + (card_w - tw) // 2, cy + 18, 16, col, bold=True)

        elif match_mgr.state == MatchState.SERVE_TOSSED:
            card_w = 640
            card_h = 54
            cx = (SCREEN_WIDTH - card_w) // 2
            cy = 135

            pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, COLOR_GLASS_BG)
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, 2, COLOR_CYAN_ACCENT)

            if match_mgr.serving_team == Team.PLAYER:
                txt = "BALL IN AIR! Jump [SPACE] -> [L-CLICK] Spike | [L-CLICK + E] Float | [E] Dump"
                col = COLOR_CYAN_ACCENT
            else:
                txt = "BALL INCOMING! Aim Cursor and Hold [L-CTRL] to Dig!"
                col = COLOR_CORAL_ACCENT

            tw = self.measure_text(txt, 15, bold=True)
            self.draw_text(txt, cx + (card_w - tw) // 2, cy + 18, 15, col, bold=True)

    def draw_point_banner(self, match_mgr):
        """Displays point award banner with smooth fonts."""
        if match_mgr.state == MatchState.POINT_SCORED:
            banner_w = 540
            banner_h = 95
            bx = (SCREEN_WIDTH - banner_w) // 2
            by = SCREEN_HEIGHT // 2 - 95

            pr.draw_rectangle_rounded(pr.Rectangle(bx, by, banner_w, banner_h), 0.3, 8, COLOR_GLASS_BG)
            winner_col = COLOR_CYAN_ACCENT if match_mgr.point_winner == Team.PLAYER else COLOR_CORAL_ACCENT
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bx, by, banner_w, banner_h), 0.3, 8, 3, winner_col)

            win_title = "POINT FOR YOU! (3v3)" if match_mgr.point_winner == Team.PLAYER else "POINT FOR OPPONENT"
            tw1 = self.measure_text(win_title, 25, bold=True)
            self.draw_text(win_title, bx + (banner_w - tw1) // 2, by + 16, 25, winner_col, bold=True)

            reason_str = match_mgr.point_reason
            tw2 = self.measure_text(reason_str, 17, bold=False)
            self.draw_text(reason_str, bx + (banner_w - tw2) // 2, by + 56, 17, COLOR_TEXT_MAIN, bold=False)

    def draw_match_over(self, match_mgr, input_mgr):
        """Draws match end screen with smooth fonts."""
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
            tw = self.measure_text(main_text, 30, bold=True)
            self.draw_text(main_text, cx + (card_w - tw) // 2, cy + 30, 30, win_col, bold=True)

            score_text = f"Final Score: YOU {match_mgr.score_player} - {match_mgr.score_opponent} CPU"
            sw = self.measure_text(score_text, 22, bold=False)
            self.draw_text(score_text, cx + (card_w - sw) // 2, cy + 95, 22, COLOR_TEXT_MAIN, bold=False)

            rematch_text = "[SPACE] or [L-CLICK] for Rematch"
            rw = self.measure_text(rematch_text, 19, bold=True)
            self.draw_text(rematch_text, cx + (card_w - rw) // 2, cy + 160, 19, COLOR_GOLD_ACCENT, bold=True)

            quit_text = "[ESC] / (START) Return to Title Menu"
            qw = self.measure_text(quit_text, 15, bold=False)
            self.draw_text(quit_text, cx + (card_w - qw) // 2, cy + 220, 15, COLOR_TEXT_MUTED, bold=False)

    def draw_pause_menu(self, input_mgr, audio_mgr, cam_ctrl=None):
        """Draws Pause overlay with smooth modern vector fonts."""
        if self.show_settings_modal:
            self._draw_settings_modal(audio_mgr, cam_ctrl)
            return

        pr.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, pr.Color(8, 10, 16, 200))
        
        card_w = 520
        card_h = 310
        cx = (SCREEN_WIDTH - card_w) // 2
        cy = (SCREEN_HEIGHT - card_h) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, 2, COLOR_GLASS_BORDER)

        title = "MATCH PAUSED"
        tw = self.measure_text(title, 26, bold=True)
        self.draw_text(title, cx + (card_w - tw) // 2, cy + 24, 26, COLOR_TEXT_MAIN, bold=True)

        self.draw_text("[ESC] / (START)  Resume Match", cx + 75, cy + 80, 17, COLOR_GOLD_ACCENT, bold=True)
        self.draw_text("[S]              Settings (Audio & Video)", cx + 75, cy + 122, 17, COLOR_CYAN_ACCENT, bold=True)
        self.draw_text("[TAB] / (BACK)   Change Camera Angle", cx + 75, cy + 164, 17, COLOR_TEXT_MAIN, bold=False)
        self.draw_text("[M]              Mute Sound Toggle", cx + 75, cy + 206, 17, COLOR_TEXT_MAIN, bold=False)
        self.draw_text("[Q]              Quit to Title Menu", cx + 75, cy + 248, 17, COLOR_CORAL_ACCENT, bold=True)
