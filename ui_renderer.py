"""
FlyHigh! - 3D Volleyball Game
Modern Arcade UI & HUD Renderer (100% Dynamic Vector Resolution & High-Impact Typography)
Features:
- Dynamic Screen Scaling: Automatically queries pr.get_screen_width() and pr.get_screen_height() (No black bands or misaligned 1080p/fullscreen viewports!)
- Modern Arcade Sports Typography: Large, high-contrast, bold, punchy font hierarchy with animated neon selection brackets
- Explicit Settings Confirmation: Pending Display Mode & Resolution changes applied only upon clicking "APPLY CHANGES"
- Comprehensive Match Setup Modal: Select Match Format (2v2, 3v3, 4v4, 5v5, 6v6), Court Venue (5 Arenas), Difficulty, and Match Points
- Full Volleyball HUD: Dynamic scoreboard pills, 3-touch counters, NBA 2K-Style Shot Meter, Roll Dig CD badge, and instant arcade popups
"""
import pyray as pr
import math
import os
import sys
import random
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, Team, MatchState, AIDifficulty,
    TimingRating, ROLL_DIG_COOLDOWN, RESOLUTIONS,
    GameMode, CourtArena, ARENAS, MODE_CONFIGS
)
from player_customization import (
    PlayerProfile, SKIN_TONES, HAIR_STYLES, HAIR_COLORS,
    HEADBAND_COLORS, JERSEY_COLORS, TRIM_COLORS, BACK_LOGOS,
    SHORTS_COLORS, WRISTBAND_COLORS
)

CUSTOMIZE_CATEGORIES = [
    {"name": "Skin Tone",     "field": "skin_tone_idx",    "max": len(SKIN_TONES),      "options": [o["name"] for o in SKIN_TONES]},
    {"name": "Hair Style",    "field": "hair_style_idx",   "max": len(HAIR_STYLES),     "options": [o["name"] for o in HAIR_STYLES]},
    {"name": "Hair Color",    "field": "hair_color_idx",   "max": len(HAIR_COLORS),     "options": [o["name"] for o in HAIR_COLORS]},
    {"name": "Headband",      "field": "headband_idx",     "max": len(HEADBAND_COLORS), "options": [o["name"] for o in HEADBAND_COLORS]},
    {"name": "Jersey Color",  "field": "jersey_color_idx", "max": len(JERSEY_COLORS),   "options": [o["name"] for o in JERSEY_COLORS]},
    {"name": "Jersey Trim",   "field": "jersey_trim_idx",  "max": len(TRIM_COLORS),     "options": [o["name"] for o in TRIM_COLORS]},
    {"name": "Back Logo",     "field": "back_logo_idx",    "max": len(BACK_LOGOS),      "options": [o["name"] for o in BACK_LOGOS]},
    {"name": "Jersey Number", "field": "jersey_number",    "max": 99,                   "options": None},
    {"name": "Shorts Color",  "field": "shorts_color_idx", "max": len(SHORTS_COLORS),   "options": [o["name"] for o in SHORTS_COLORS]},
    {"name": "Shorts Trim",   "field": "shorts_trim_idx",  "max": len(TRIM_COLORS),     "options": [o["name"] for o in TRIM_COLORS]},
    {"name": "Wristbands",    "field": "wristband_idx",    "max": len(WRISTBAND_COLORS),"options": [o["name"] for o in WRISTBAND_COLORS]},
]

MATCH_MODES = [
    GameMode.MODE_2V2,
    GameMode.MODE_3V3,
    GameMode.MODE_4V4,
    GameMode.MODE_5V5,
    GameMode.MODE_6V6
]

DIFFICULTIES = [
    AIDifficulty.EASY,
    AIDifficulty.MEDIUM,
    AIDifficulty.HARD
]

POINTS_OPTIONS = [7, 11, 15, 21]

def get_asset_path(subpath):
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        p = os.path.join(base_dir, subpath)
        if os.path.exists(p):
            return p
        return os.path.join(os.path.dirname(sys.executable), subpath)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, subpath)

# High-Contrast Arcade Color Palette
COLOR_GLASS_BG      = pr.Color(16, 20, 32, 245)
COLOR_GLASS_BORDER  = pr.Color(70, 90, 130, 255)
COLOR_TEXT_MAIN     = pr.Color(255, 255, 255, 255)
COLOR_TEXT_MUTED    = pr.Color(175, 190, 215, 255)
COLOR_CYAN_ACCENT   = pr.Color(25, 220, 255, 255)
COLOR_GOLD_ACCENT   = pr.Color(255, 215, 0, 255)
COLOR_CORAL_ACCENT  = pr.Color(255, 80, 95, 255)
COLOR_GREEN_PERFECT = pr.Color(50, 245, 125, 255)
COLOR_BTN_NORMAL    = pr.Color(26, 34, 52, 240)
COLOR_BTN_HOVER     = pr.Color(48, 68, 108, 255)
COLOR_BTN_BORDER    = pr.Color(85, 115, 165, 255)

class UIRenderer:
    # Title Menu Button Geometry
    BTN_X = 55
    BTN_START_Y = 195
    BTN_W = 330
    BTN_H = 54
    BTN_SPACING = 66

    def __init__(self):
        # Load high-resolution bold vector fonts
        self.font_regular = None
        self.font_bold = None
        self._init_fonts()

        self.menu_index = 0
        self.menu_items = [
            {"title": "PLAY", "subtitle": "Select format & arena", "action": "PLAY"},
            {"title": "PLAYER CUSTOMIZE", "subtitle": "Create your own style", "action": "CUSTOMIZE"},
            {"title": "SETTINGS", "subtitle": "Audio, Video & Controls", "action": "SETTINGS"},
            {"title": "STATS", "subtitle": "Track your progress", "action": "STATS"},
            {"title": "HOW TO PLAY", "subtitle": "Controls & mechanics guide", "action": "HOW_TO_PLAY"},
            {"title": "QUIT GAME", "subtitle": "See you soon!", "action": "QUIT"}
        ]
        self.show_customize_modal = False
        self.show_settings_modal = False
        self.show_match_setup = False
        self.show_stats_modal = False
        self.show_controls_modal = False
        self.customize_index = 0
        self.is_dragging_rotate = False
        self.last_mouse_x = 0.0
        self.anim_timer = 0.0

        # Match Setup Modal Configuration
        self.match_setup_index = 0
        self.match_setup_items = [
            "MATCH FORMAT",
            "COURT VENUE",
            "AI DIFFICULTY",
            "MATCH LENGTH",
            "START MATCH",
            "BACK TO MENU"
        ]
        self.selected_mode_idx = 1   # Default: 3v3
        self.selected_arena_idx = 0  # Default: Coastal Beach
        self.selected_diff_idx = 1   # Default: Normal
        self.selected_points_idx = 1 # Default: 11 Points

        # Settings Menu Navigation & Pending States
        self.settings_index = 0
        self.settings_items = [
            "MASTER VOLUME",
            "SOUND FX",
            "DISPLAY MODE",
            "RESOLUTION",
            "CAMERA ANGLE",
            "APPLY CHANGES",
            "BACK TO MENU"
        ]
        self.res_index = 0
        self.is_fullscreen = False
        self.pending_res_index = 0
        self.pending_fullscreen = False

        # Arcade Feedback Popups
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

    def update_menu(self, input_mgr, audio_mgr, current_diff, cam_ctrl=None, profile=None, player=None):
        """Handles Title, Match Setup, Customization, Settings, Stats, and How-to-Play menus."""
        dt = pr.get_frame_time()
        self.anim_timer += dt
        sw = pr.get_screen_width()
        sh = pr.get_screen_height()

        # 1. Player Customization Modal Active
        if self.show_customize_modal:
            return self._update_customize_menu(input_mgr, audio_mgr, current_diff, profile, player)

        # 2. Match Setup Modal Active
        if self.show_match_setup:
            return self._update_match_setup_menu(input_mgr, audio_mgr, current_diff)

        # 3. Controls / How-to-Play Dialog Active
        if self.show_controls_modal:
            if input_mgr.pause_pressed or input_mgr.jump_pressed or input_mgr.select_pressed or pr.is_key_pressed(pr.KEY_ESCAPE) or pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                self.show_controls_modal = False
                audio_mgr.play("hit_set")
            return "NONE", current_diff

        # 4. Stats Modal Active
        if self.show_stats_modal:
            if input_mgr.pause_pressed or input_mgr.jump_pressed or input_mgr.select_pressed or pr.is_key_pressed(pr.KEY_ESCAPE) or pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                self.show_stats_modal = False
                audio_mgr.play("hit_set")
            return "NONE", current_diff

        # 5. Settings Modal Active
        if self.show_settings_modal:
            return self._update_settings_menu(input_mgr, audio_mgr, current_diff, cam_ctrl)

        # 6. Main Title Screen Navigation
        mouse_pos = pr.get_mouse_position()

        # Mouse Hover & Click on Left Menu Buttons
        for i in range(len(self.menu_items)):
            by = self.BTN_START_Y + i * self.BTN_SPACING
            rec = pr.Rectangle(self.BTN_X - 10, by - 4, self.BTN_W + 20, self.BTN_H + 8)
            
            if pr.check_collision_point_rec(mouse_pos, rec):
                if self.menu_index != i:
                    self.menu_index = i
                    audio_mgr.play("hit_set")
                if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                    return self._activate_menu_item(i, current_diff, audio_mgr)

        # Mouse Click on Featured Match Card (Bottom-Right)
        fw = 360
        fh = 140
        fx = sw - fw - 40
        fy = sh - fh - 45
        featured_rec = pr.Rectangle(fx, fy, fw, fh)
        if pr.check_collision_point_rec(mouse_pos, featured_rec):
            if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                self.show_match_setup = True
                audio_mgr.play("whistle")
                return "NONE", current_diff

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

        # Select action
        if input_mgr.select_pressed or input_mgr.jump_pressed or pr.is_key_pressed(pr.KEY_ENTER):
            return self._activate_menu_item(self.menu_index, current_diff, audio_mgr)

        return "NONE", current_diff

    def _activate_menu_item(self, index, current_diff, audio_mgr):
        audio_mgr.play("hit_bump")
        action = self.menu_items[index]["action"]
        if action == "PLAY":
            self.show_match_setup = True
            self.match_setup_index = 0
            return "NONE", current_diff
        elif action == "CUSTOMIZE":
            self.show_customize_modal = True
            return "CUSTOMIZE", current_diff
        elif action == "SETTINGS":
            self.show_settings_modal = True
            self.settings_index = 0
            self.pending_res_index = self.res_index
            self.pending_fullscreen = self.is_fullscreen
            return "SETTINGS", current_diff
        elif action == "STATS":
            self.show_stats_modal = True
            return "STATS", current_diff
        elif action == "HOW_TO_PLAY":
            self.show_controls_modal = True
            return "HOW_TO_PLAY", current_diff
        elif action == "QUIT":
            return "QUIT", current_diff
        return "NONE", current_diff

    def _update_match_setup_menu(self, input_mgr, audio_mgr, current_diff):
        """Interactions in the Match Setup screen."""
        nav_up = pr.is_key_pressed(pr.KEY_W) or pr.is_key_pressed(pr.KEY_UP)
        nav_down = pr.is_key_pressed(pr.KEY_S) or pr.is_key_pressed(pr.KEY_DOWN)
        left = pr.is_key_pressed(pr.KEY_A) or pr.is_key_pressed(pr.KEY_LEFT)
        right = pr.is_key_pressed(pr.KEY_D) or pr.is_key_pressed(pr.KEY_RIGHT)
        enter = input_mgr.select_pressed or pr.is_key_pressed(pr.KEY_ENTER)
        esc = pr.is_key_pressed(pr.KEY_ESCAPE) or pr.is_key_pressed(pr.KEY_BACKSPACE)

        if nav_up:
            self.match_setup_index = (self.match_setup_index - 1) % len(self.match_setup_items)
            audio_mgr.play("hit_set")
        elif nav_down:
            self.match_setup_index = (self.match_setup_index + 1) % len(self.match_setup_items)
            audio_mgr.play("hit_set")

        # 0: MATCH FORMAT (2v2, 3v3, 4v4, 5v5, 6v6)
        if self.match_setup_index == 0:
            if left or right:
                step = 1 if right else -1
                self.selected_mode_idx = (self.selected_mode_idx + step) % len(MATCH_MODES)
                audio_mgr.play("hit_bump")

        # 1: COURT VENUE (Beach, Orange Arena, Sky High, Cruise Ship, High School Gym)
        elif self.match_setup_index == 1:
            if left or right:
                step = 1 if right else -1
                self.selected_arena_idx = (self.selected_arena_idx + step) % len(ARENAS)
                audio_mgr.play("hit_bump")

        # 2: AI DIFFICULTY
        elif self.match_setup_index == 2:
            if left or right:
                step = 1 if right else -1
                self.selected_diff_idx = (self.selected_diff_idx + step) % len(DIFFICULTIES)
                audio_mgr.play("hit_bump")

        # 3: MATCH LENGTH (7, 11, 15, 21 Points)
        elif self.match_setup_index == 3:
            if left or right:
                step = 1 if right else -1
                self.selected_points_idx = (self.selected_points_idx + step) % len(POINTS_OPTIONS)
                audio_mgr.play("hit_bump")

        # 4: START MATCH
        elif self.match_setup_index == 4:
            if enter or pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                self.show_match_setup = False
                audio_mgr.play("whistle")
                sel_mode = MATCH_MODES[self.selected_mode_idx]
                sel_arena = ARENAS[self.selected_arena_idx]
                sel_diff = DIFFICULTIES[self.selected_diff_idx]
                sel_pts = POINTS_OPTIONS[self.selected_points_idx]
                return ("START_MATCH", sel_mode, sel_arena, sel_diff, sel_pts), sel_diff

        # 5: BACK
        elif self.match_setup_index == 5:
            if enter or pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                self.show_match_setup = False
                audio_mgr.play("hit_set")

        if esc:
            self.show_match_setup = False
            audio_mgr.play("hit_set")

        return "NONE", current_diff

    def _update_settings_menu(self, input_mgr, audio_mgr, current_diff, cam_ctrl):
        """Interactions in Settings: changes are pending until 'APPLY CHANGES' is clicked."""
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

        # 2: DISPLAY MODE (Pending windowed vs borderless fullscreen)
        elif self.settings_index == 2:
            if left or right:
                self.pending_fullscreen = not self.pending_fullscreen
                audio_mgr.play("hit_bump")

        # 3: RESOLUTION (Pending resolution selection - NOT applied immediately!)
        elif self.settings_index == 3:
            if left or right:
                dir_step = 1 if right else -1
                self.pending_res_index = (self.pending_res_index + dir_step) % len(RESOLUTIONS)
                audio_mgr.play("hit_bump")

        # 4: CAMERA ANGLE
        elif self.settings_index == 4:
            if (left or right or enter) and cam_ctrl:
                cam_ctrl.cycle_mode()
                audio_mgr.play("hit_bump")

        # 5: APPLY CHANGES (Explicit application of Display Mode and Resolution!)
        elif self.settings_index == 5:
            if enter or pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                # Apply Fullscreen if modified
                if self.pending_fullscreen != self.is_fullscreen:
                    self.is_fullscreen = self.pending_fullscreen
                    pr.toggle_borderless_windowed()

                # Apply Resolution if modified
                if self.pending_res_index != self.res_index:
                    self.res_index = self.pending_res_index
                    w, h, _ = RESOLUTIONS[self.res_index]
                    pr.set_window_size(w, h)

                self.trigger_arcade_popup("SETTINGS APPLIED SUCCESSFULLY!", COLOR_GREEN_PERFECT, 1.4)
                audio_mgr.play("whistle")

        # 6: BACK TO MENU
        elif self.settings_index == 6:
            if enter or pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                self.show_settings_modal = False
                audio_mgr.play("hit_set")

        if esc:
            self.show_settings_modal = False
            # Revert unapplied pending settings
            self.pending_res_index = self.res_index
            self.pending_fullscreen = self.is_fullscreen
            audio_mgr.play("hit_set")

        return "NONE", current_diff

    def _update_customize_menu(self, input_mgr, audio_mgr, current_diff, profile, player):
        """Interactions inside the Player Customization screen."""
        dt = pr.get_frame_time()
        nav_up = pr.is_key_pressed(pr.KEY_W) or pr.is_key_pressed(pr.KEY_UP)
        nav_down = pr.is_key_pressed(pr.KEY_S) or pr.is_key_pressed(pr.KEY_DOWN)
        left = pr.is_key_pressed(pr.KEY_A) or pr.is_key_pressed(pr.KEY_LEFT)
        right = pr.is_key_pressed(pr.KEY_D) or pr.is_key_pressed(pr.KEY_RIGHT)
        randomize = pr.is_key_pressed(pr.KEY_R)
        esc = pr.is_key_pressed(pr.KEY_ESCAPE) or pr.is_key_pressed(pr.KEY_BACKSPACE)

        # 360 Character Rotation with [Q] and [E]
        if pr.is_key_down(pr.KEY_Q):
            if player:
                player.facing_angle += dt * 3.2
        if pr.is_key_down(pr.KEY_E):
            if player:
                player.facing_angle -= dt * 3.2

        # Mouse Drag Rotation on Right Side
        mouse_pos = pr.get_mouse_position()
        if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT) and mouse_pos.x > 500:
            self.is_dragging_rotate = True
            self.last_mouse_x = mouse_pos.x
        elif pr.is_mouse_button_released(pr.MOUSE_BUTTON_LEFT):
            self.is_dragging_rotate = False

        if self.is_dragging_rotate and player:
            dx = mouse_pos.x - self.last_mouse_x
            player.facing_angle -= dx * 0.015
            self.last_mouse_x = mouse_pos.x

        if nav_up:
            self.customize_index = (self.customize_index - 1) % len(CUSTOMIZE_CATEGORIES)
            audio_mgr.play("hit_set")
        elif nav_down:
            self.customize_index = (self.customize_index + 1) % len(CUSTOMIZE_CATEGORIES)
            audio_mgr.play("hit_set")

        cat = CUSTOMIZE_CATEGORIES[self.customize_index]
        field = cat["field"]
        max_val = cat["max"]

        if left or right:
            audio_mgr.play("hit_bump")
            cur_val = getattr(profile, field)
            step = 1 if right else -1
            if field == "jersey_number":
                new_val = max(1, min(99, cur_val + step))
            else:
                new_val = (cur_val + step) % max_val
            setattr(profile, field, new_val)
            if player:
                player.apply_profile(profile)
            profile.save()

        # Randomize Outfit with [R]
        if randomize:
            audio_mgr.play("whistle")
            profile.skin_tone_idx = random.randint(0, len(SKIN_TONES) - 1)
            profile.hair_style_idx = random.randint(0, len(HAIR_STYLES) - 1)
            profile.hair_color_idx = random.randint(0, len(HAIR_COLORS) - 1)
            profile.headband_idx = random.randint(0, len(HEADBAND_COLORS) - 1)
            profile.jersey_color_idx = random.randint(0, len(JERSEY_COLORS) - 1)
            profile.jersey_trim_idx = random.randint(0, len(TRIM_COLORS) - 1)
            profile.back_logo_idx = random.randint(0, len(BACK_LOGOS) - 1)
            profile.shorts_color_idx = random.randint(0, len(SHORTS_COLORS) - 1)
            profile.shorts_trim_idx = random.randint(0, len(TRIM_COLORS) - 1)
            profile.wristband_idx = random.randint(0, len(WRISTBAND_COLORS) - 1)
            if player:
                player.apply_profile(profile)
            profile.save()

        # Close and Save
        if esc:
            self.show_customize_modal = False
            if player:
                player.facing_angle = 0.0  # Face net
            if profile:
                profile.save()
            audio_mgr.play("hit_set")

        return "NONE", current_diff

    # =========================================================================
    # DRAWING ROUTINES (100% Dynamic Screen Resolution & Bold Modern Typography)
    # =========================================================================
    def draw_title_screen(self, current_diff, audio_mgr, input_mgr, cam_ctrl=None, profile=None, player=None):
        """Draws the modern arcade Title Screen matching the reference aesthetic."""
        sw = pr.get_screen_width()
        sh = pr.get_screen_height()
        mouse_pos = pr.get_mouse_position()

        # Soft dark atmospheric vignette on left side behind UI text
        for vi in range(0, 520, 2):
            alpha = int(150 * (1.0 - vi / 520.0)**1.2)
            pr.draw_rectangle(vi, 0, 2, sh, pr.Color(10, 14, 24, alpha))

        # 1. Top-Left Energetic Logo & Title
        self._draw_top_left_title()

        # 2. Left Menu Navigation Buttons
        for i, item in enumerate(self.menu_items):
            by = self.BTN_START_Y + i * self.BTN_SPACING
            is_selected = (i == self.menu_index)
            action = item["action"]
            title_text = item["title"]
            sub_text = item["subtitle"]

            if action == "PLAY" and is_selected:
                # Signature Yellow Jagged Brush Banner
                self._draw_yellow_brush_banner(self.BTN_X - 10, by - 4, self.BTN_W + 20, self.BTN_H + 8)
                self._draw_icon("PLAY", self.BTN_X + 16, by + 13, 22, pr.Color(16, 20, 28, 255), is_selected=True)
                self.draw_text(title_text, self.BTN_X + 54, by + 9, 21, pr.Color(16, 20, 28, 255), bold=True)
                self.draw_text(sub_text, self.BTN_X + 54, by + 31, 13, pr.Color(50, 60, 75, 255), bold=False)
            elif is_selected:
                rec = pr.Rectangle(self.BTN_X - 6, by - 2, self.BTN_W + 12, self.BTN_H + 4)
                pr.draw_rectangle_rounded(rec, 0.28, 6, COLOR_BTN_HOVER)
                pr.draw_rectangle_rounded_lines_ex(rec, 0.28, 6, 2, COLOR_CYAN_ACCENT)
                self._draw_icon(action, self.BTN_X + 16, by + 13, 22, COLOR_CYAN_ACCENT, is_selected=True)
                self.draw_text(title_text, self.BTN_X + 54, by + 9, 20, COLOR_TEXT_MAIN, bold=True)
                self.draw_text(sub_text, self.BTN_X + 54, by + 31, 13, COLOR_CYAN_ACCENT, bold=False)
            else:
                self._draw_icon(action, self.BTN_X + 16, by + 13, 20, COLOR_TEXT_MUTED, is_selected=False)
                self.draw_text(title_text, self.BTN_X + 54, by + 10, 19, COLOR_TEXT_MUTED, bold=False)
                self.draw_text(sub_text, self.BTN_X + 54, by + 31, 13, pr.Color(120, 135, 160, 200), bold=False)

        # 3. Top-Right Player Card (Dynamic Position)
        self._draw_top_right_player_card(profile, sw)

        # 4. Bottom-Right Featured Match Card (Dynamic Position)
        self._draw_featured_match_card(sw, sh)

        # 5. Bottom Navigation Bar
        self._draw_bottom_nav_bar(sh)

        # Active Modals
        if self.show_match_setup:
            self._draw_match_setup_modal(sw, sh)
        elif self.show_customize_modal:
            self._draw_customize_modal(profile, sw, sh)
        elif self.show_settings_modal:
            self._draw_settings_modal(audio_mgr, cam_ctrl, sw, sh)
        elif self.show_controls_modal:
            self._draw_controls_modal(sw, sh)
        elif self.show_stats_modal:
            self._draw_stats_modal(profile, sw, sh)

        # Arcade Popup notification
        if self.arcade_popup_timer > 0.0:
            pw = self.measure_text(self.arcade_popup_text, 30, bold=True)
            px = (sw - pw) // 2
            py = 120
            pr.draw_rectangle_rounded(pr.Rectangle(px - 20, py - 6, pw + 40, 44), 0.35, 6, pr.Color(16, 20, 30, 230))
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(px - 20, py - 6, pw + 40, 44), 0.35, 6, 2, self.arcade_popup_col)
            self.draw_text(self.arcade_popup_text, px, py + 4, 30, self.arcade_popup_col, bold=True)

    def _draw_match_setup_modal(self, sw, sh):
        """Draws Match Setup screen: Format (2v2..6v6), Arena (5 courts), Difficulty, Length."""
        pr.draw_rectangle(0, 0, sw, sh, pr.Color(8, 10, 16, 235))

        mw = 760
        mh = 540
        mx = (sw - mw) // 2
        my = (sh - mh) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(mx, my, mw, mh), 0.12, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(mx, my, mw, mh), 0.12, 10, 2, COLOR_GOLD_ACCENT)

        title = "MATCH SETUP"
        tw = self.measure_text(title, 30, bold=True)
        self.draw_text(title, mx + (mw - tw) // 2, my + 24, 30, COLOR_GOLD_ACCENT, bold=True)

        start_y = my + 76
        row_h = 58
        for idx, item in enumerate(self.match_setup_items):
            ry = start_y + idx * row_h
            is_sel = (idx == self.match_setup_index)

            rec = pr.Rectangle(mx + 34, ry, mw - 68, 50)
            if idx == 4:  # START MATCH Action
                r_bg = pr.Color(255, 215, 0, 245) if is_sel else pr.Color(220, 175, 10, 220)
                pr.draw_rectangle_rounded(rec, 0.28, 6, r_bg)
                pr.draw_rectangle_rounded_lines_ex(rec, 0.28, 6, 2, COLOR_TEXT_MAIN)
                lbl = "► START MATCH NOW ◄" if is_sel else "START MATCH NOW"
                lw = self.measure_text(lbl, 22, bold=True)
                self.draw_text(lbl, mx + (mw - lw) // 2, ry + 13, 22, pr.Color(16, 20, 28, 255), bold=True)
                continue
            elif idx == 5:  # BACK
                r_bg = COLOR_BTN_HOVER if is_sel else pr.Color(22, 28, 42, 200)
                pr.draw_rectangle_rounded(rec, 0.28, 6, r_bg)
                pr.draw_rectangle_rounded_lines_ex(rec, 0.28, 6, 2 if is_sel else 1, COLOR_CORAL_ACCENT if is_sel else COLOR_GLASS_BORDER)
                lbl = "BACK TO TITLE MENU"
                lw = self.measure_text(lbl, 19, bold=is_sel)
                self.draw_text(lbl, mx + (mw - lw) // 2, ry + 14, 19, COLOR_CORAL_ACCENT if is_sel else COLOR_TEXT_MUTED, bold=is_sel)
                continue

            r_bg = COLOR_BTN_HOVER if is_sel else pr.Color(22, 28, 42, 210)
            r_border = COLOR_CYAN_ACCENT if is_sel else COLOR_GLASS_BORDER
            pr.draw_rectangle_rounded(rec, 0.28, 6, r_bg)
            pr.draw_rectangle_rounded_lines_ex(rec, 0.28, 6, 2 if is_sel else 1, r_border)

            lbl_col = COLOR_GOLD_ACCENT if is_sel else COLOR_TEXT_MAIN
            self.draw_text(item, mx + 54, ry + 14, 19, lbl_col, bold=is_sel)

            if idx == 0:
                val_txt = f"< {MATCH_MODES[self.selected_mode_idx].value} >"
            elif idx == 1:
                val_txt = f"< {ARENAS[self.selected_arena_idx].value} >"
            elif idx == 2:
                val_txt = f"< {DIFFICULTIES[self.selected_diff_idx].value} >"
            elif idx == 3:
                val_txt = f"< {POINTS_OPTIONS[self.selected_points_idx]} Points to Win >"
            else:
                val_txt = ""

            vw = self.measure_text(val_txt, 19, bold=is_sel)
            val_col = COLOR_CYAN_ACCENT if is_sel else COLOR_TEXT_MUTED
            self.draw_text(val_txt, mx + mw - vw - 54, ry + 14, 19, val_col, bold=is_sel)

        footer_txt = "[A / D] Change Option   |   [W / S] Navigate   |   [ENTER] Confirm   |   [ESC] Back"
        fw = self.measure_text(footer_txt, 16, bold=False)
        self.draw_text(footer_txt, mx + (mw - fw) // 2, my + mh - 26, 16, COLOR_TEXT_MUTED, bold=False)

    def _draw_settings_modal(self, audio_mgr, cam_ctrl, sw, sh):
        """Draws full-featured settings panel with explicit APPLY confirmation."""
        pr.draw_rectangle(0, 0, sw, sh, pr.Color(8, 10, 16, 235))

        mw = 720
        mh = 540
        mx = (sw - mw) // 2
        my = (sh - mh) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(mx, my, mw, mh), 0.12, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(mx, my, mw, mh), 0.12, 10, 2, COLOR_GOLD_ACCENT)

        title = "GAME SETTINGS"
        tw = self.measure_text(title, 30, bold=True)
        self.draw_text(title, mx + (mw - tw) // 2, my + 24, 30, COLOR_GOLD_ACCENT, bold=True)

        start_y = my + 74
        row_h = 58
        for idx, item in enumerate(self.settings_items):
            ry = start_y + idx * row_h
            is_sel = (idx == self.settings_index)

            rec = pr.Rectangle(mx + 32, ry, mw - 64, 48)

            # Special action rows: APPLY CHANGES & BACK TO MENU
            if idx == 5:
                r_bg = pr.Color(35, 200, 245, 240) if is_sel else pr.Color(20, 140, 180, 200)
                pr.draw_rectangle_rounded(rec, 0.28, 6, r_bg)
                pr.draw_rectangle_rounded_lines_ex(rec, 0.28, 6, 2, COLOR_TEXT_MAIN)
                lbl = "► APPLY CHANGES (ENTER) ◄" if is_sel else "APPLY CHANGES"
                lw = self.measure_text(lbl, 20, bold=True)
                self.draw_text(lbl, mx + (mw - lw) // 2, ry + 13, 20, pr.Color(10, 15, 24, 255), bold=True)
                continue
            elif idx == 6:
                r_bg = COLOR_BTN_HOVER if is_sel else pr.Color(22, 28, 42, 210)
                pr.draw_rectangle_rounded(rec, 0.28, 6, r_bg)
                pr.draw_rectangle_rounded_lines_ex(rec, 0.28, 6, 2 if is_sel else 1, COLOR_CORAL_ACCENT if is_sel else COLOR_GLASS_BORDER)
                lbl = "BACK TO MENU"
                lw = self.measure_text(lbl, 19, bold=is_sel)
                self.draw_text(lbl, mx + (mw - lw) // 2, ry + 13, 19, COLOR_CORAL_ACCENT if is_sel else COLOR_TEXT_MUTED, bold=is_sel)
                continue

            r_bg = COLOR_BTN_HOVER if is_sel else pr.Color(22, 28, 42, 210)
            r_border = COLOR_CYAN_ACCENT if is_sel else COLOR_GLASS_BORDER
            pr.draw_rectangle_rounded(rec, 0.28, 6, r_bg)
            pr.draw_rectangle_rounded_lines_ex(rec, 0.28, 6, 2 if is_sel else 1, r_border)

            lbl_col = COLOR_GOLD_ACCENT if is_sel else COLOR_TEXT_MAIN
            self.draw_text(item, mx + 50, ry + 13, 19, lbl_col, bold=is_sel)

            if idx == 0:
                vol_pct = int(audio_mgr.volume * 100)
                val_txt = f"< {vol_pct}% >"
                for b in range(10):
                    bar_col = COLOR_CYAN_ACCENT if (b * 10) < vol_pct else pr.Color(60, 70, 90, 200)
                    pr.draw_rectangle(mx + mw - 260 + b * 11, ry + 17, 8, 14, bar_col)
            elif idx == 1:
                val_txt = "[ Enabled ]" if audio_mgr.enabled else "[ Muted ]"
            elif idx == 2:
                val_txt = "< Fullscreen (Pending) >" if self.pending_fullscreen else "< Windowed (Pending) >"
            elif idx == 3:
                _, _, res_lbl = RESOLUTIONS[self.pending_res_index]
                val_txt = f"< {res_lbl} >"
            elif idx == 4:
                cam_name = cam_ctrl.get_mode_name() if cam_ctrl else "DEFAULT"
                val_txt = f"< {cam_name} >"
            else:
                val_txt = ""

            vw = self.measure_text(val_txt, 18, bold=is_sel)
            val_col = COLOR_CYAN_ACCENT if is_sel else COLOR_TEXT_MUTED
            self.draw_text(val_txt, mx + mw - vw - 50, ry + 13, 18, val_col, bold=is_sel)

        footer_txt = "[A / D] Adjust Setting   |   Click [APPLY CHANGES] to confirm   |   [ESC] Close"
        fw = self.measure_text(footer_txt, 15, bold=False)
        self.draw_text(footer_txt, mx + (mw - fw) // 2, my + mh - 26, 15, COLOR_TEXT_MUTED, bold=False)

    def _draw_customize_modal(self, profile, sw, sh):
        """Draws Player Customization panel with modern vector layout and live preview."""
        card_w = 460
        card_h = sh - 70
        cx = 36
        cy = 35

        rec = pr.Rectangle(cx, cy, card_w, card_h)
        pr.draw_rectangle_rounded(rec, 0.08, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(rec, 0.08, 10, 2, COLOR_GOLD_ACCENT)

        title = "PLAYER CUSTOMIZATION"
        self.draw_text(title, cx + 24, cy + 18, 24, COLOR_GOLD_ACCENT, bold=True)
        sub = "Create your own unique arcade style"
        self.draw_text(sub, cx + 24, cy + 46, 13, COLOR_TEXT_MUTED, bold=False)

        start_y = cy + 72
        row_h = min(46, int((card_h - 150) / len(CUSTOMIZE_CATEGORIES)))
        for idx, cat in enumerate(CUSTOMIZE_CATEGORIES):
            ry = start_y + idx * row_h
            is_sel = (idx == self.customize_index)

            r_bg = COLOR_BTN_HOVER if is_sel else pr.Color(22, 28, 42, 200)
            r_border = COLOR_CYAN_ACCENT if is_sel else COLOR_GLASS_BORDER

            r_rec = pr.Rectangle(cx + 18, ry, card_w - 36, row_h - 6)
            pr.draw_rectangle_rounded(r_rec, 0.22, 6, r_bg)
            pr.draw_rectangle_rounded_lines_ex(r_rec, 0.22, 6, 2 if is_sel else 1, r_border)

            lbl_col = COLOR_GOLD_ACCENT if is_sel else COLOR_TEXT_MAIN
            self.draw_text(cat["name"], cx + 32, ry + (row_h - 26) // 2, 17, lbl_col, bold=is_sel)

            field = cat["field"]
            val_idx = getattr(profile, field)
            if cat["options"]:
                val_txt = f"< {cat['options'][val_idx]} >"
            else:
                val_txt = f"< #{val_idx} >"

            vw = self.measure_text(val_txt, 17, bold=is_sel)
            val_col = COLOR_CYAN_ACCENT if is_sel else COLOR_TEXT_MUTED
            self.draw_text(val_txt, cx + card_w - vw - 32, ry + (row_h - 26) // 2, 17, val_col, bold=is_sel)

        # Footers
        fy = cy + card_h - 64
        self.draw_text("[W / S] Category   |   [A / D] Change Option", cx + 24, fy, 14, COLOR_TEXT_MUTED, bold=False)
        self.draw_text("[R] Randomize   |   [Q / E] Rotate Character", cx + 24, fy + 20, 14, COLOR_CYAN_ACCENT, bold=False)
        self.draw_text("Press [ESC] to Save & Return to Menu", cx + 24, fy + 40, 14, COLOR_GOLD_ACCENT, bold=True)

    def _draw_controls_modal(self, sw, sh):
        """Draws card-based How-to-Play controls guide in clean vector typography."""
        pr.draw_rectangle(0, 0, sw, sh, pr.Color(8, 10, 16, 235))

        mw = 800
        mh = 580
        mx = (sw - mw) // 2
        my = (sh - mh) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(mx, my, mw, mh), 0.12, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(mx, my, mw, mh), 0.12, 10, 2, COLOR_CYAN_ACCENT)

        title = "HOW TO PLAY - VOLLEYBALL CONTROLS"
        tw = self.measure_text(title, 26, bold=True)
        self.draw_text(title, mx + (mw - tw) // 2, my + 18, 26, COLOR_GOLD_ACCENT, bold=True)

        controls = [
            ("MOVEMENT", "[W, A, S, D] (D = Screen Right)", "Left Stick / D-Pad"),
            ("AIM RETICLE", "Mouse Cursor (Court Floor)", "Right Stick"),
            ("HOLD / TOSS SERVE", "[R-CLICK] to Toss into Air", "(Y) Button"),
            ("JUMP / BAM JUMP", "[SPACE] (Hold to BAM Leap)", "(A) Button"),
            ("POWER SPIKE (IN-AIR)", "[L-CLICK] (Shot Meter Timing)", "In-Air (A)"),
            ("FLOAT SERVE (IN-AIR)", "[L-CLICK + E] (Green Timing)", "In-Air (A) + (X)"),
            ("DUMP / TIP (IN-AIR)", "[E] (Soft Feather over Net)", "In-Air (X)"),
            ("NET BLOCK (IN-AIR)", "[R-CLICK] (Near Net Z > -2.8)", "In-Air (Y)"),
            ("PASS / SET (GROUND)", "[R-CLICK] (Overhead Pass)", "(Y) Button"),
            ("SETTER DUMP", "[R-CLICK + E] (Surprise Attack)", "(Y) + (X)"),
            ("RECEIVE / DIG", "[L-CTRL] (Directs to Cursor)", "(LT) / (X)"),
            ("ROLL DIG (5s CD)", "[L-CTRL + R-CLICK] (Dive Roll)", "(LT) + (Y)"),
        ]

        start_y = my + 58
        for idx, (label, kb, gp) in enumerate(controls):
            col_idx = idx % 2
            row_idx = idx // 2
            card_x = mx + 22 + col_idx * 380
            card_y = start_y + row_idx * 78

            c_rec = pr.Rectangle(card_x, card_y, 368, 70)
            pr.draw_rectangle_rounded(c_rec, 0.22, 6, pr.Color(22, 28, 42, 220))
            pr.draw_rectangle_rounded_lines_ex(c_rec, 0.22, 6, 1, COLOR_GLASS_BORDER)

            self.draw_text(label, card_x + 14, card_y + 8, 16, COLOR_CYAN_ACCENT, bold=True)
            self.draw_text(f"PC: {kb}", card_x + 14, card_y + 28, 14, COLOR_TEXT_MAIN, bold=False)
            self.draw_text(f"Gamepad: {gp}", card_x + 14, card_y + 48, 13, COLOR_TEXT_MUTED, bold=False)

        close_txt = "Press [ESC], [Enter], or Click Anywhere to Close"
        cw = self.measure_text(close_txt, 16, bold=False)
        self.draw_text(close_txt, mx + (mw - cw) // 2, my + mh - 26, 16, COLOR_GOLD_ACCENT, bold=False)

    def _draw_stats_modal(self, profile, sw, sh):
        """Draws player stats and career progress modal."""
        pr.draw_rectangle(0, 0, sw, sh, pr.Color(8, 10, 16, 235))

        mw = 680
        mh = 480
        mx = (sw - mw) // 2
        my = (sh - mh) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(mx, my, mw, mh), 0.12, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(mx, my, mw, mh), 0.12, 10, 2, COLOR_GOLD_ACCENT)

        title = "CAREER STATS & ACHIEVEMENTS"
        tw = self.measure_text(title, 26, bold=True)
        self.draw_text(title, mx + (mw - tw) // 2, my + 24, 26, COLOR_GOLD_ACCENT, bold=True)

        stats = [
            ("MATCHES PLAYED", str(profile.matches_played)),
            ("MATCHES WON", str(profile.matches_won)),
            ("WIN RATE", f"{(profile.matches_won / max(1, profile.matches_played) * 100):.1f}%"),
            ("SPIKES LANDED", str(profile.spikes_hit)),
            ("BLOCKS SCORED", str(profile.blocks_scored)),
            ("PERFECT DIGS", str(profile.digs_performed)),
            ("SERVICE ACES", str(profile.aces_served)),
            ("LEVEL / XP", f"Lv.{profile.level} ({profile.xp}/{profile.xp_max} XP)"),
        ]

        start_y = my + 75
        for idx, (label, val) in enumerate(stats):
            col_idx = idx % 2
            row_idx = idx // 2
            card_x = mx + 32 + col_idx * 310
            card_y = start_y + row_idx * 86

            c_rec = pr.Rectangle(card_x, card_y, 290, 74)
            pr.draw_rectangle_rounded(c_rec, 0.25, 6, pr.Color(22, 28, 44, 220))
            pr.draw_rectangle_rounded_lines_ex(c_rec, 0.25, 6, 1, COLOR_GLASS_BORDER)

            self.draw_text(label, card_x + 18, card_y + 12, 14, COLOR_TEXT_MUTED, bold=False)
            self.draw_text(val, card_x + 18, card_y + 36, 22, COLOR_GOLD_ACCENT, bold=True)

        close_txt = "Press [ESC], [Enter], or Click Anywhere to Close"
        cw = self.measure_text(close_txt, 16, bold=False)
        self.draw_text(close_txt, mx + (mw - cw) // 2, my + mh - 28, 16, COLOR_CYAN_ACCENT, bold=False)

    def draw_shot_meter(self, timing_ratio, is_visible):
        """Renders NBA 2K-Style Shot Timing Meter."""
        sw = pr.get_screen_width()
        sh = pr.get_screen_height()
        dt = pr.get_frame_time()
        if self.shot_meter_feedback_timer > 0.0:
            self.shot_meter_feedback_timer -= dt

        # Feedback notification banner
        if self.shot_meter_feedback_timer > 0.0:
            fb_txt = self.shot_meter_feedback
            fw = self.measure_text(fb_txt, 24, bold=True)
            fx = (sw - fw) // 2
            fy = sh // 2 + 75

            pr.draw_rectangle_rounded(pr.Rectangle(fx - 22, fy - 8, fw + 44, 42), 0.4, 6, pr.Color(16, 20, 30, 235))
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(fx - 22, fy - 8, fw + 44, 42), 0.4, 6, 2, self.shot_meter_feedback_col)
            self.draw_text(fb_txt, fx, fy, 24, self.shot_meter_feedback_col, bold=True)

        if not is_visible:
            return

        # Vertical Shot Meter Gauge
        gauge_w = 28
        gauge_h = 135
        gx = sw // 2 + 165
        gy = sh // 2 - 80

        pr.draw_rectangle_rounded(pr.Rectangle(gx, gy, gauge_w, gauge_h), 0.5, 6, pr.Color(18, 22, 32, 235))
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(gx, gy, gauge_w, gauge_h), 0.5, 6, 2, COLOR_GLASS_BORDER)

        # Zones
        red_h = int(gauge_h * 0.50)
        yel_h = int(gauge_h * 0.32)
        grn_h = gauge_h - red_h - yel_h

        pr.draw_rectangle(gx + 3, gy + gauge_h - red_h, gauge_w - 6, red_h - 3, pr.Color(235, 60, 75, 200))
        pr.draw_rectangle(gx + 3, gy + grn_h, gauge_w - 6, yel_h, pr.Color(255, 205, 45, 210))
        pr.draw_rectangle(gx + 3, gy + 3, gauge_w - 6, grn_h, COLOR_GREEN_PERFECT)

        # Indicator Needle
        indicator_y = gy + int(gauge_h * (1.0 - timing_ratio))
        pr.draw_rectangle(gx - 4, indicator_y - 3, gauge_w + 8, 6, pr.Color(255, 255, 255, 255))
        pr.draw_rectangle(gx - 2, indicator_y - 2, gauge_w + 4, 4, COLOR_CYAN_ACCENT)

    def draw_hud(self, match_mgr, input_mgr, cam_ctrl, ai_difficulty, player):
        """Renders match HUD pills and control helpers."""
        sw = pr.get_screen_width()
        sh = pr.get_screen_height()

        # Center Scoreboard Pill
        main_w = 340
        main_h = 50
        main_x = (sw - main_w) // 2
        main_y = 16

        pr.draw_rectangle_rounded(pr.Rectangle(main_x, main_y, main_w, main_h), 0.5, 8, pr.Color(245, 248, 255, 240))
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(main_x, main_y, main_w, main_h), 0.5, 8, 2, pr.Color(20, 24, 35, 60))

        # Home pill
        hw = 72
        hh = 36
        pr.draw_rectangle_rounded(pr.Rectangle(main_x + 8, main_y + 7, hw, hh), 0.5, 6, pr.Color(50, 215, 110, 255))
        self.draw_text("HOME", main_x + 18, main_y + 16, 15, pr.Color(255, 255, 255, 255), bold=True)

        # Score
        score_str = f"{match_mgr.score_player}  -  {match_mgr.score_opponent}"
        sc_w = self.measure_text(score_str, 26, bold=True)
        self.draw_text(score_str, main_x + (main_w - sc_w) // 2, main_y + 12, 26, pr.Color(24, 28, 38, 255), bold=True)

        # Away pill
        aw = 72
        ah = 36
        pr.draw_rectangle_rounded(pr.Rectangle(main_x + main_w - aw - 8, main_y + 7, aw, ah), 0.5, 6, pr.Color(245, 55, 125, 255))
        self.draw_text("AWAY", main_x + main_w - aw + 18, main_y + 16, 15, pr.Color(255, 255, 255, 255), bold=True)

        # Touch Count Lights Pill
        sub_w = 130
        sub_h = 24
        sub_x = (sw - sub_w) // 2
        sub_y = main_y + main_h + 5
        pr.draw_rectangle_rounded(pr.Rectangle(sub_x, sub_y, sub_w, sub_h), 0.5, 6, pr.Color(245, 248, 255, 220))
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(sub_x, sub_y, sub_w, sub_h), 0.5, 6, 1, pr.Color(20, 24, 35, 40))

        cur_touches = match_mgr.get_touches(match_mgr.last_touch_team if match_mgr.last_touch_team else Team.PLAYER)
        c1 = pr.Color(50, 215, 110, 255) if cur_touches >= 1 else pr.Color(190, 195, 205, 180)
        c2 = pr.Color(255, 205, 40, 255) if cur_touches >= 2 else pr.Color(190, 195, 205, 180)
        c3 = pr.Color(245, 60, 75, 255) if cur_touches >= 3 else pr.Color(190, 195, 205, 180)
        pr.draw_circle(sub_x + 30, sub_y + 12, 5, c1)
        pr.draw_circle(sub_x + 65, sub_y + 12, 5, c2)
        pr.draw_circle(sub_x + 100, sub_y + 12, 5, c3)

        # Roll Dig Cooldown Badge (Bottom-Left)
        cd = player.roll_dig_cooldown
        cd_w = 190
        cd_h = 36
        cd_x = 24
        cd_y = sh - 62
        pr.draw_rectangle_rounded(pr.Rectangle(cd_x, cd_y, cd_w, cd_h), 0.35, 6, pr.Color(16, 20, 30, 210))
        cd_border = COLOR_CYAN_ACCENT if cd <= 0.0 else COLOR_GLASS_BORDER
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cd_x, cd_y, cd_w, cd_h), 0.35, 6, 1, cd_border)

        if cd <= 0.0:
            cd_txt = "ROLL DIG: READY"
            self.draw_text(cd_txt, cd_x + 14, cd_y + 9, 14, COLOR_CYAN_ACCENT, bold=True)
            pr.draw_circle(cd_x + cd_w - 20, cd_y + 18, 5, COLOR_GREEN_PERFECT)
        else:
            cd_txt = f"ROLL DIG: {cd:.1f}s"
            self.draw_text(cd_txt, cd_x + 14, cd_y + 9, 14, COLOR_TEXT_MUTED, bold=False)

        # Right-Side Control Helper Stack
        cw = 185
        controls = [
            ("camera", "[C] / [TAB]"),
            ("strafe", "[W][A][S][D]"),
            ("jump / bam", "[SPACE] (Hold)"),
            ("receive", "[L-CTRL]"),
            ("pass / set", "[R-CLICK]"),
            ("spike", "[L-CLICK]"),
            ("block", "[R-CLICK in air]"),
            ("dump / tip", "[E]"),
        ]
        cy_base = sh - (len(controls) * 26) - 16
        cx = sw - cw - 16
        for idx, (action_name, key_name) in enumerate(controls):
            item_y = cy_base + idx * 26
            pr.draw_rectangle_rounded(pr.Rectangle(cx, item_y, cw, 23), 0.35, 4, pr.Color(16, 20, 30, 200))
            self.draw_text(action_name, cx + 8, item_y + 5, 12, pr.Color(200, 210, 225, 255), bold=False)
            kw = self.measure_text(key_name, 12, bold=True)
            self.draw_text(key_name, cx + cw - kw - 6, item_y + 5, 12, COLOR_GOLD_ACCENT, bold=True)

    def draw_serve_prompt(self, match_mgr, input_mgr):
        """Displays clear serving prompt with explicit RIGHT-CLICK toss instruction."""
        sw = pr.get_screen_width()
        if match_mgr.state == MatchState.SERVE_READY:
            card_w = 600
            card_h = 56
            cx = (sw - card_w) // 2
            cy = 135

            pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, COLOR_GLASS_BG)
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, 2, COLOR_GOLD_ACCENT)

            if match_mgr.serving_team == Team.PLAYER:
                txt = "HOLDING BALL: Press [RIGHT CLICK] to Toss the Ball!"
                col = COLOR_GOLD_ACCENT
            else:
                txt = "OPPONENT SERVING... Get Ready to Dig with [L-CTRL]!"
                col = COLOR_CORAL_ACCENT

            tw = self.measure_text(txt, 18, bold=True)
            self.draw_text(txt, cx + (card_w - tw) // 2, cy + 18, 18, col, bold=True)

        elif match_mgr.state == MatchState.SERVE_TOSSED:
            card_w = 680
            card_h = 56
            cx = (sw - card_w) // 2
            cy = 135

            pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, COLOR_GLASS_BG)
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.3, 6, 2, COLOR_CYAN_ACCENT)

            if match_mgr.serving_team == Team.PLAYER:
                txt = "BALL IN AIR! Jump [SPACE] -> [L-CLICK] Spike | [L-CLICK + E] Float | [E] Dump"
                col = COLOR_CYAN_ACCENT
            else:
                txt = "BALL INCOMING! Aim Cursor and Hold [L-CTRL] to Dig!"
                col = COLOR_CORAL_ACCENT

            tw = self.measure_text(txt, 16, bold=True)
            self.draw_text(txt, cx + (card_w - tw) // 2, cy + 18, 16, col, bold=True)

    def draw_point_banner(self, match_mgr):
        """Displays point award banner with smooth fonts."""
        sw = pr.get_screen_width()
        sh = pr.get_screen_height()
        if match_mgr.state == MatchState.POINT_SCORED:
            banner_w = 560
            banner_h = 100
            bx = (sw - banner_w) // 2
            by = sh // 2 - 95

            pr.draw_rectangle_rounded(pr.Rectangle(bx, by, banner_w, banner_h), 0.3, 8, COLOR_GLASS_BG)
            winner_col = COLOR_CYAN_ACCENT if match_mgr.point_winner == Team.PLAYER else COLOR_CORAL_ACCENT
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(bx, by, banner_w, banner_h), 0.3, 8, 3, winner_col)

            win_title = "POINT FOR YOU!" if match_mgr.point_winner == Team.PLAYER else "POINT FOR OPPONENT"
            tw1 = self.measure_text(win_title, 26, bold=True)
            self.draw_text(win_title, bx + (banner_w - tw1) // 2, by + 16, 26, winner_col, bold=True)

            reason_str = match_mgr.point_reason
            tw2 = self.measure_text(reason_str, 18, bold=False)
            self.draw_text(reason_str, bx + (banner_w - tw2) // 2, by + 58, 18, COLOR_TEXT_MAIN, bold=False)

    def draw_match_over(self, match_mgr, input_mgr):
        """Draws match victory or defeat screen."""
        sw = pr.get_screen_width()
        sh = pr.get_screen_height()
        if match_mgr.state == MatchState.MATCH_OVER:
            pr.draw_rectangle(0, 0, sw, sh, pr.Color(8, 10, 16, 230))

            card_w = 600
            card_h = 300
            cx = (sw - card_w) // 2
            cy = (sh - card_h) // 2

            pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, COLOR_GLASS_BG)
            win_col = COLOR_GOLD_ACCENT if match_mgr.winner == Team.PLAYER else COLOR_CORAL_ACCENT
            pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, 3, win_col)

            main_text = "MATCH WON! (VICTORY)" if match_mgr.winner == Team.PLAYER else "MATCH OVER (DEFEAT)"
            tw = self.measure_text(main_text, 32, bold=True)
            self.draw_text(main_text, cx + (card_w - tw) // 2, cy + 30, 32, win_col, bold=True)

            score_text = f"Final Score: YOU {match_mgr.score_player} - {match_mgr.score_opponent} CPU"
            sw2 = self.measure_text(score_text, 24, bold=False)
            self.draw_text(score_text, cx + (card_w - sw2) // 2, cy + 96, 24, COLOR_TEXT_MAIN, bold=False)

            rematch_text = "[SPACE] or [L-CLICK] for Rematch"
            rw = self.measure_text(rematch_text, 20, bold=True)
            self.draw_text(rematch_text, cx + (card_w - rw) // 2, cy + 165, 20, COLOR_GOLD_ACCENT, bold=True)

            quit_text = "[ESC] / (START) Return to Title Menu"
            qw = self.measure_text(quit_text, 16, bold=False)
            self.draw_text(quit_text, cx + (card_w - qw) // 2, cy + 228, 16, COLOR_TEXT_MUTED, bold=False)

    def draw_pause_menu(self, input_mgr, audio_mgr, cam_ctrl=None):
        """Draws Pause overlay."""
        sw = pr.get_screen_width()
        sh = pr.get_screen_height()
        if self.show_settings_modal:
            self._draw_settings_modal(audio_mgr, cam_ctrl, sw, sh)
            return

        pr.draw_rectangle(0, 0, sw, sh, pr.Color(8, 10, 16, 210))
        
        card_w = 540
        card_h = 320
        cx = (sw - card_w) // 2
        cy = (sh - card_h) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, card_w, card_h), 0.25, 8, 2, COLOR_GLASS_BORDER)

        title = "MATCH PAUSED"
        tw = self.measure_text(title, 28, bold=True)
        self.draw_text(title, cx + (card_w - tw) // 2, cy + 24, 28, COLOR_TEXT_MAIN, bold=True)

        self.draw_text("[ESC] / (START)  Resume Match", cx + 80, cy + 85, 18, COLOR_GOLD_ACCENT, bold=True)
        self.draw_text("[S]              Settings (Audio & Video)", cx + 80, cy + 130, 18, COLOR_CYAN_ACCENT, bold=True)
        self.draw_text("[TAB] / (BACK)   Change Camera Angle", cx + 80, cy + 175, 18, COLOR_TEXT_MAIN, bold=False)
        self.draw_text("[M]              Mute Sound Toggle", cx + 80, cy + 220, 18, COLOR_TEXT_MAIN, bold=False)
        self.draw_text("[Q]              Quit to Title Menu", cx + 80, cy + 265, 18, COLOR_CORAL_ACCENT, bold=True)

    # -------------------------------------------------------------------------
    # UI DECORATIVE COMPONENT HELPERS
    # -------------------------------------------------------------------------
    def _draw_top_left_title(self):
        cx = self.BTN_X + 2
        cy = 55
        self._draw_crown(cx + 8, cy - 2, 28, COLOR_GOLD_ACCENT)
        self.draw_text("FLYHIGH!", cx + 46, cy - 8, 40, COLOR_TEXT_MAIN, bold=True)
        self.draw_text("ARCADE VOLLEYBALL", cx + 48, cy + 34, 15, COLOR_GOLD_ACCENT, bold=True)

    def _draw_crown(self, x, y, size, color):
        s = size
        p1 = pr.Vector2(x, y + s)
        p2 = pr.Vector2(x + s, y + s)
        p3 = pr.Vector2(x + s, y + s * 0.4)
        p4 = pr.Vector2(x + s * 0.75, y + s * 0.7)
        p5 = pr.Vector2(x + s * 0.5, y + s * 0.2)
        p6 = pr.Vector2(x + s * 0.25, y + s * 0.7)
        p7 = pr.Vector2(x, y + s * 0.4)
        pr.draw_triangle(p1, p2, p5, color)
        pr.draw_triangle(p1, p5, p7, color)
        pr.draw_triangle(p5, p2, p3, color)
        pr.draw_circle(int(x), int(y + s * 0.35), 2.5, color)
        pr.draw_circle(int(x + s * 0.5), int(y + s * 0.15), 3.0, color)
        pr.draw_circle(int(x + s), int(y + s * 0.35), 2.5, color)

    def _draw_yellow_brush_banner(self, x, y, w, h):
        c_main = pr.Color(255, 215, 0, 255)
        c_glow = pr.Color(255, 235, 60, 255)
        pr.draw_rectangle_rounded(pr.Rectangle(x, y, w, h), 0.24, 6, c_main)
        for offset in [4, 12, 24, 38]:
            pr.draw_triangle(
                pr.Vector2(x + w, y + offset),
                pr.Vector2(x + w + 16, y + offset + 6),
                pr.Vector2(x + w, y + offset + 14),
                c_main
            )
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(x, y, w, h), 0.24, 6, 2, c_glow)

    def _draw_icon(self, action_name, x, y, size, color, is_selected=False):
        s = size
        if action_name == "PLAY":
            p1 = pr.Vector2(x, y)
            p2 = pr.Vector2(x, y + s)
            p3 = pr.Vector2(x + s * 0.9, y + s * 0.5)
            pr.draw_triangle(p1, p2, p3, color)
        elif action_name == "CUSTOMIZE":
            pr.draw_circle(x + s // 2, y + s // 3, s // 3.5, color)
            pr.draw_rectangle_rounded(pr.Rectangle(x, y + s * 0.6, s, s * 0.45), 0.4, 4, color)
        elif action_name == "SETTINGS":
            pr.draw_circle(x + s // 2, y + s // 2, s // 2.2, color)
            pr.draw_circle(x + s // 2, y + s // 2, s // 4, pr.Color(16, 20, 30, 255))
        elif action_name == "STATS":
            pr.draw_rectangle(x, y + s // 2, s // 4, s // 2, color)
            pr.draw_rectangle(x + s // 3, y + s // 4, s // 4, s * 3 // 4, color)
            pr.draw_rectangle(x + s * 2 // 3, y, s // 4, s, color)
        elif action_name == "HOW_TO_PLAY":
            pr.draw_circle(x + s // 2, y + s // 2, s // 2, color)
            self.draw_text("?", x + s // 3, y + s // 6, s * 0.8, pr.Color(16, 20, 30, 255), bold=True)
        elif action_name == "QUIT":
            pr.draw_rectangle_lines(int(x), int(y), int(s * 0.7), int(s), color)
            pr.draw_line(int(x + s * 0.3), int(y + s * 0.5), int(x + s), int(y + s * 0.5), color)

    def _draw_top_right_player_card(self, profile, sw):
        cw = 270
        ch = 56
        cx = sw - cw - 32
        cy = 22

        pr.draw_rectangle_rounded(pr.Rectangle(cx, cy, cw, ch), 0.4, 6, pr.Color(16, 20, 30, 220))
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx, cy, cw, ch), 0.4, 6, 1, COLOR_GLASS_BORDER)

        pr.draw_circle(cx + 28, cy + ch // 2, 17, pr.Color(35, 45, 65, 255))
        self._draw_crown(cx + 17, cy + ch // 2 - 11, 22, COLOR_GOLD_ACCENT)

        name_str = profile.name if profile else "PLAYER"
        self.draw_text(name_str, cx + 56, cy + 9, 16, COLOR_TEXT_MAIN, bold=True)

        lvl_str = f"LV.{profile.level if profile else 1}"
        self.draw_text(lvl_str, cx + 56, cy + 30, 13, COLOR_CYAN_ACCENT, bold=True)

        bar_x = cx + 110
        bar_y = cy + 34
        bar_w = 70
        pr.draw_rectangle(bar_x, bar_y, bar_w, 5, pr.Color(40, 50, 70, 255))
        xp_pct = (profile.xp / max(1, profile.xp_max)) if profile else 0.5
        pr.draw_rectangle(bar_x, bar_y, int(bar_w * xp_pct), 5, COLOR_CYAN_ACCENT)

        crowns_val = str(profile.crowns if profile else 0)
        self._draw_crown(cx + cw - 65, cy + 18, 18, COLOR_GOLD_ACCENT)
        self.draw_text(crowns_val, cx + cw - 42, cy + 18, 15, COLOR_GOLD_ACCENT, bold=True)

    def _draw_featured_match_card(self, sw, sh):
        fw = 360
        fh = 140
        fx = sw - fw - 40
        fy = sh - fh - 45

        pr.draw_rectangle_rounded(pr.Rectangle(fx, fy, fw, fh), 0.16, 8, pr.Color(18, 24, 38, 230))
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(fx, fy, fw, fh), 0.16, 8, 2, COLOR_CYAN_ACCENT)

        banner_w = fw // 2
        pr.draw_rectangle_rounded(pr.Rectangle(fx + 16, fy + 16, banner_w, 36), 0.3, 4, pr.Color(30, 80, 160, 200))
        self.draw_text(MATCH_MODES[self.selected_mode_idx].value.split()[0], fx + 26, fy + 20, 26, COLOR_TEXT_MAIN, bold=True)

        self.draw_text("QUICK MATCH SETUP", fx + 20, fy + 60, 15, COLOR_GOLD_ACCENT, bold=True)
        venue_str = f"Arena: {ARENAS[self.selected_arena_idx].value}"
        self.draw_text(venue_str, fx + 20, fy + 82, 13, COLOR_TEXT_MUTED, bold=False)
        self.draw_text("Click here to customize match!", fx + 20, fy + 104, 13, COLOR_CYAN_ACCENT, bold=False)

        bw = 36
        bx = fx + fw - bw - 20
        by = fy + fh - bw - 20
        pr.draw_circle(bx + bw // 2, by + bw // 2, bw // 2, COLOR_GOLD_ACCENT)
        p1 = pr.Vector2(bx + 14, by + 10)
        p2 = pr.Vector2(bx + 14, by + bw - 10)
        p3 = pr.Vector2(bx + bw - 10, by + bw // 2)
        pr.draw_triangle(p1, p2, p3, pr.Color(16, 20, 28, 255))

    def _draw_bottom_nav_bar(self, sh):
        by = sh - 36
        items = [
            ("Select", "[ENTER] / Click"),
            ("Navigate", "[W / S]"),
            ("Rotate 3D", "[Q / E]"),
            ("Quick Start", "Space"),
            ("Version", "v1.2.0 Modern")
        ]
        cx = self.BTN_X
        for label, key in items:
            pr.draw_circle(cx, by + 6, 3, COLOR_CYAN_ACCENT)
            self.draw_text(label, cx + 8, by, 13, COLOR_TEXT_MUTED, bold=False)
            kw = self.measure_text(key, 13, bold=True)
            self.draw_text(key, cx + self.measure_text(label, 13) + 12, by, 13, COLOR_TEXT_MAIN, bold=True)
            cx += self.measure_text(label, 13) + kw + 34
