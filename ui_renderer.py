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
    # Modern Left-Aligned Menu Layout matching reference screenshot
    BTN_X = 55
    BTN_START_Y = 195
    BTN_W = 325
    BTN_H = 54
    BTN_SPACING = 66

    def __init__(self):
        # Load high-resolution smooth vector fonts
        self.font_regular = None
        self.font_bold = None
        self._init_fonts()

        self.menu_index = 0
        self.menu_items = [
            {"title": "PLAY", "subtitle": "Jump into a match", "action": "PLAY"},
            {"title": "PLAYER CUSTOMIZE", "subtitle": "Create your own style", "action": "CUSTOMIZE"},
            {"title": "SETTINGS", "subtitle": "Audio, Video & Controls", "action": "SETTINGS"},
            {"title": "STATS", "subtitle": "Track your progress", "action": "STATS"},
            {"title": "HOW TO PLAY", "subtitle": "Learn the basics", "action": "HOW_TO_PLAY"},
            {"title": "QUIT GAME", "subtitle": "See you soon!", "action": "QUIT"}
        ]
        self.show_customize_modal = False
        self.show_settings_modal = False
        self.show_stats_modal = False
        self.show_controls_modal = False
        self.customize_index = 0
        self.is_dragging_rotate = False
        self.last_mouse_x = 0.0
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

    def update_menu(self, input_mgr, audio_mgr, current_diff, cam_ctrl=None, profile=None, player=None):
        """Handles Title and Settings menus via mouse, keyboard, and gamepad."""
        dt = pr.get_frame_time()
        self.anim_timer += dt

        # 1. Player Customization Modal Active
        if self.show_customize_modal:
            return self._update_customize_menu(input_mgr, audio_mgr, current_diff, profile, player)

        # 2. Controls / How-to-Play Dialog Active
        if self.show_controls_modal:
            if input_mgr.pause_pressed or input_mgr.jump_pressed or input_mgr.select_pressed or pr.is_key_pressed(pr.KEY_ESCAPE) or pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                self.show_controls_modal = False
                audio_mgr.play("hit_set")
            return "NONE", current_diff

        # 3. Stats Modal Active
        if self.show_stats_modal:
            if input_mgr.pause_pressed or input_mgr.jump_pressed or input_mgr.select_pressed or pr.is_key_pressed(pr.KEY_ESCAPE) or pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                self.show_stats_modal = False
                audio_mgr.play("hit_set")
            return "NONE", current_diff

        # 4. Settings Modal Active
        if self.show_settings_modal:
            return self._update_settings_menu(input_mgr, audio_mgr, current_diff, cam_ctrl)

        # 5. Main Title Screen Navigation
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

        # Mouse Click on Featured 3v3 Banner Card (Bottom-Right)
        fw = 350
        fh = 135
        fx = SCREEN_WIDTH - fw - 40
        fy = SCREEN_HEIGHT - fh - 45
        featured_rec = pr.Rectangle(fx, fy, fw, fh)
        if pr.check_collision_point_rec(mouse_pos, featured_rec):
            if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                audio_mgr.play("whistle")
                return "PLAY", current_diff

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

    def _update_customize_menu(self, input_mgr, audio_mgr, current_diff, profile, player):
        """Interactions inside the Player Customization screen."""
        dt = pr.get_frame_time()
        nav_up = pr.is_key_pressed(pr.KEY_W) or pr.is_key_pressed(pr.KEY_UP)
        nav_down = pr.is_key_pressed(pr.KEY_S) or pr.is_key_pressed(pr.KEY_DOWN)
        left = pr.is_key_pressed(pr.KEY_A) or pr.is_key_pressed(pr.KEY_LEFT)
        right = pr.is_key_pressed(pr.KEY_D) or pr.is_key_pressed(pr.KEY_RIGHT)
        randomize = pr.is_key_pressed(pr.KEY_R)
        esc = pr.is_key_pressed(pr.KEY_ESCAPE) or pr.is_key_pressed(pr.KEY_BACKSPACE)

        # Rotate character with Q / E
        if pr.is_key_down(pr.KEY_Q) and player:
            player.facing_angle -= 3.0 * dt
        elif pr.is_key_down(pr.KEY_E) and player:
            player.facing_angle += 3.0 * dt

        # Mouse Drag Rotation on 3D View Area
        mouse_pos = pr.get_mouse_position()
        if mouse_pos.x > 490:
            if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                self.is_dragging_rotate = True
                self.last_mouse_x = mouse_pos.x
            elif pr.is_mouse_button_released(pr.MOUSE_BUTTON_LEFT):
                self.is_dragging_rotate = False
            
            if self.is_dragging_rotate and player:
                dx = mouse_pos.x - self.last_mouse_x
                self.last_mouse_x = mouse_pos.x
                player.facing_angle += dx * 0.018
        else:
            if pr.is_mouse_button_released(pr.MOUSE_BUTTON_LEFT):
                self.is_dragging_rotate = False

        if nav_up:
            self.customize_index = (self.customize_index - 1) % len(CUSTOMIZE_CATEGORIES)
            audio_mgr.play("hit_set")
        elif nav_down:
            self.customize_index = (self.customize_index + 1) % len(CUSTOMIZE_CATEGORIES)
            audio_mgr.play("hit_set")

        # Cycle selected category
        if profile and (left or right):
            audio_mgr.play("hit_bump")
            cat = CUSTOMIZE_CATEGORIES[self.customize_index]
            field = cat["field"]
            cur_val = getattr(profile, field)
            if field == "jersey_number":
                step = 1 if right else -1
                setattr(profile, field, max(1, min(99, cur_val + step)))
            else:
                max_v = cat["max"]
                setattr(profile, field, (cur_val + (1 if right else -1)) % max_v)
            if player:
                player.apply_profile(profile)
            profile.save()

        # Randomize style
        if randomize and profile:
            audio_mgr.play("whistle")
            import random
            profile.skin_tone_idx = random.randint(0, len(SKIN_TONES) - 1)
            profile.hair_style_idx = random.randint(0, len(HAIR_STYLES) - 1)
            profile.hair_color_idx = random.randint(0, len(HAIR_COLORS) - 1)
            profile.headband_idx = random.randint(0, len(HEADBAND_COLORS) - 1)
            profile.jersey_color_idx = random.randint(0, len(JERSEY_COLORS) - 1)
            profile.jersey_trim_idx = random.randint(0, len(TRIM_COLORS) - 1)
            profile.back_logo_idx = random.randint(0, len(BACK_LOGOS) - 1)
            profile.jersey_number = random.randint(1, 99)
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
                player.facing_angle = 0.0  # Face towards net again
            if profile:
                profile.save()
            audio_mgr.play("hit_set")

        return "NONE", current_diff

    def _activate_menu_item(self, index, current_diff, audio_mgr):
        audio_mgr.play("hit_bump")
        action = self.menu_items[index]["action"]
        if action == "PLAY":
            return "PLAY", current_diff
        elif action == "CUSTOMIZE":
            self.show_customize_modal = True
            return "CUSTOMIZE", current_diff
        elif action == "SETTINGS":
            self.show_settings_modal = True
            self.settings_index = 0
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

    def draw_title_screen(self, current_diff, audio_mgr, input_mgr, cam_ctrl=None, profile=None, player=None):
        """Draws the modern arcade Title Screen matching the reference screenshot."""
        mouse_pos = pr.get_mouse_position()

        # Soft dark atmospheric vignette on left side behind UI text (matching reference photo)
        for vi in range(0, 480, 2):
            alpha = int(145 * (1.0 - vi / 480.0)**1.2)
            pr.draw_rectangle(vi, 0, 2, SCREEN_HEIGHT, pr.Color(10, 14, 24, alpha))

        # 1. Top-Left Energetic Logo & Title ("FLYHIGH! 3v3 ARCADE VOLLEYBALL")
        self._draw_top_left_title()

        # 2. Left Menu Navigation Buttons
        for i, item in enumerate(self.menu_items):
            by = self.BTN_START_Y + i * self.BTN_SPACING
            is_selected = (i == self.menu_index)
            action = item["action"]
            title_text = item["title"]
            sub_text = item["subtitle"]

            if action == "PLAY" and is_selected:
                # Signature Yellow Jagged Brush Banner from Reference Photo!
                self._draw_yellow_brush_banner(self.BTN_X - 10, by - 4, self.BTN_W + 20, self.BTN_H + 8)
                # Black Play Icon
                self._draw_icon("PLAY", self.BTN_X + 16, by + 13, 22, pr.Color(16, 20, 28, 255), is_selected=True)
                # Black Bold Text
                self.draw_text(title_text, self.BTN_X + 54, by + 8, 21, pr.Color(16, 20, 28, 255), bold=True)
                self.draw_text(sub_text, self.BTN_X + 54, by + 32, 11, pr.Color(45, 52, 65, 255), bold=False)
            else:
                # Modern Glass Row
                btn_rec = pr.Rectangle(self.BTN_X - 6, by - 2, self.BTN_W + 12, self.BTN_H + 4)
                if is_selected:
                    pr.draw_rectangle_rounded(btn_rec, 0.35, 6, pr.Color(30, 42, 65, 235))
                    pr.draw_rectangle_rounded_lines_ex(btn_rec, 0.35, 6, 1.5, COLOR_GOLD_ACCENT)
                
                # Icon
                icon_col = COLOR_GOLD_ACCENT if is_selected else pr.Color(245, 248, 255, 255)
                self._draw_icon(action, self.BTN_X + 16, by + 14, 20, icon_col, is_selected=is_selected)

                # Text
                t_col = COLOR_GOLD_ACCENT if is_selected else pr.Color(255, 255, 255, 255)
                sub_col = COLOR_CYAN_ACCENT if is_selected else COLOR_TEXT_MUTED
                self.draw_text(title_text, self.BTN_X + 54, by + 9, 18, t_col, bold=is_selected)
                self.draw_text(sub_text, self.BTN_X + 54, by + 32, 11, sub_col, bold=False)

        # 3. Bottom-Left Footer: Globe Icon + "Play • Customize • Compete"
        globe_x = self.BTN_X
        globe_y = SCREEN_HEIGHT - 34
        pr.draw_circle(globe_x + 8, globe_y + 8, 7, pr.Color(160, 180, 215, 220))
        pr.draw_circle_lines(globe_x + 8, globe_y + 8, 7, pr.Color(25, 32, 45, 255))
        pr.draw_line(globe_x + 1, globe_y + 8, globe_x + 15, globe_y + 8, pr.Color(25, 32, 45, 255))
        pr.draw_line(globe_x + 8, globe_y + 1, globe_x + 8, globe_y + 15, pr.Color(25, 32, 45, 255))
        self.draw_text("Play   •   Customize   •   Compete", globe_x + 24, globe_y + 2, 11, pr.Color(180, 195, 225, 220), bold=False)

        # 4. Top-Right Profile / Level Card
        self._draw_top_right_profile(profile)

        # 5. Bottom-Right Featured 3v3 Arcade Banner Card
        self._draw_bottom_right_featured_card(mouse_pos)

        # 6. Active Modals
        if self.show_customize_modal:
            self._draw_player_customize_modal(profile, player, mouse_pos)
        elif self.show_settings_modal:
            self._draw_settings_modal(audio_mgr, cam_ctrl)
        elif self.show_stats_modal:
            self._draw_stats_modal(profile)
        elif self.show_controls_modal:
            self._draw_controls_modal()

    def _draw_icon(self, icon_name, x, y, size, color, is_selected=False):
        """Draws clean vector icons for menu items."""
        if icon_name == "PLAY":
            pr.draw_triangle(
                pr.Vector2(x, y),
                pr.Vector2(x, y + size),
                pr.Vector2(x + size * 0.9, y + size * 0.5),
                color
            )
        elif icon_name == "CUSTOMIZE":
            # Athletic sleeveless jersey shape
            pr.draw_rectangle_rounded(pr.Rectangle(x + 2, y + 2, size - 4, size - 4), 0.25, 4, color)
            # Neck cut
            cut_col = pr.Color(16, 20, 28, 255) if is_selected else pr.Color(16, 20, 30, 255)
            pr.draw_circle(int(x + size * 0.5), int(y + 3), int(size * 0.24), cut_col)
        elif icon_name == "SETTINGS":
            # Gear cogwheel
            pr.draw_circle(int(x + size * 0.5), int(y + size * 0.5), int(size * 0.45), color)
            cut_col = pr.Color(16, 20, 28, 255) if is_selected else pr.Color(16, 20, 30, 255)
            pr.draw_circle(int(x + size * 0.5), int(y + size * 0.5), int(size * 0.22), cut_col)
            for ang in [0, 45, 90, 135]:
                rad = math.radians(ang)
                ox = math.cos(rad) * (size * 0.48)
                oy = math.sin(rad) * (size * 0.48)
                pr.draw_circle(int(x + size * 0.5 + ox), int(y + size * 0.5 + oy), 3, color)
        elif icon_name == "STATS":
            # 3 vertical bar chart pillars
            pr.draw_rectangle(int(x + 1), int(y + size * 0.55), int(size * 0.24), int(size * 0.45), color)
            pr.draw_rectangle(int(x + size * 0.38), int(y + size * 0.30), int(size * 0.24), int(size * 0.70), color)
            pr.draw_rectangle(int(x + size * 0.75), int(y + 2), int(size * 0.24), int(size - 2), color)
        elif icon_name == "HOW_TO_PLAY":
            # Open book pages
            pr.draw_rectangle_rounded(pr.Rectangle(x, y + 2, size * 0.46, size - 4), 0.3, 4, color)
            pr.draw_rectangle_rounded(pr.Rectangle(x + size * 0.52, y + 2, size * 0.46, size - 4), 0.3, 4, color)
        elif icon_name == "QUIT":
            # Exit door with arrow
            pr.draw_rectangle_lines_ex(pr.Rectangle(x + 1, y + 1, size * 0.55, size - 2), 2, color)
            pr.draw_line_ex(pr.Vector2(x + size * 0.35, y + size * 0.5), pr.Vector2(x + size, y + size * 0.5), 2.5, color)
            pr.draw_triangle(
                pr.Vector2(x + size, y + size * 0.5),
                pr.Vector2(x + size * 0.72, y + size * 0.25),
                pr.Vector2(x + size * 0.72, y + size * 0.75),
                color
            )

    def _draw_yellow_brush_banner(self, x, y, w, h):
        """Draws signature yellow jagged paint banner for selected PLAY button."""
        # Shadow
        pr.draw_rectangle(x + 4, y + 5, w, h, pr.Color(12, 16, 24, 180))
        # Main Yellow Body
        y_col = pr.Color(255, 218, 12, 255)
        pr.draw_rectangle(x, y, w - 24, h, y_col)
        # Jagged paint splatter cuts on right edge (matching reference photo)
        pr.draw_triangle(pr.Vector2(x + w - 24, y), pr.Vector2(x + w + 16, y + h * 0.25), pr.Vector2(x + w - 24, y + h * 0.55), y_col)
        pr.draw_triangle(pr.Vector2(x + w - 24, y + h * 0.45), pr.Vector2(x + w + 8, y + h * 0.8), pr.Vector2(x + w - 24, y + h), y_col)
        pr.draw_triangle(pr.Vector2(x + w - 10, y + h * 0.1), pr.Vector2(x + w + 28, y + h * 0.35), pr.Vector2(x + w - 5, y + h * 0.4), y_col)
        # Jagged paint splatter cuts on left edge
        pr.draw_triangle(pr.Vector2(x, y), pr.Vector2(x - 14, y + h * 0.45), pr.Vector2(x, y + h * 0.9), y_col)
        pr.draw_triangle(pr.Vector2(x, y + h * 0.2), pr.Vector2(x - 8, y + h * 0.75), pr.Vector2(x, y + h), y_col)

    def _draw_top_left_title(self):
        """Draws stylized FLYHIGH! title, crown icon, and subtitle."""
        # Blue splash accent behind logo
        pr.draw_triangle(pr.Vector2(0, 0), pr.Vector2(0, 160), pr.Vector2(260, 0), pr.Color(22, 120, 235, 180))
        pr.draw_triangle(pr.Vector2(0, 35), pr.Vector2(175, 115), pr.Vector2(245, 0), pr.Color(32, 145, 255, 130))
        pr.draw_circle(40, 40, 55, pr.Color(35, 155, 255, 100))

        # Golden Crown Icon above title
        cx = 210
        cy = 48
        # Peaks
        pr.draw_triangle(pr.Vector2(cx, cy - 22), pr.Vector2(cx - 10, cy + 8), pr.Vector2(cx + 10, cy + 8), COLOR_GOLD_ACCENT)
        pr.draw_triangle(pr.Vector2(cx - 20, cy - 14), pr.Vector2(cx - 24, cy + 8), pr.Vector2(cx - 6, cy + 8), COLOR_GOLD_ACCENT)
        pr.draw_triangle(pr.Vector2(cx + 20, cy - 14), pr.Vector2(cx + 6, cy + 8), pr.Vector2(cx + 24, cy + 8), COLOR_GOLD_ACCENT)
        # Base Band
        pr.draw_rectangle_rounded(pr.Rectangle(cx - 26, cy + 6, 52, 9), 0.4, 4, COLOR_GOLD_ACCENT)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(cx - 26, cy + 6, 52, 9), 0.4, 4, 2, pr.Color(18, 22, 30, 255))
        pr.draw_line_ex(pr.Vector2(cx - 20, cy - 14), pr.Vector2(cx, cy - 22), 2, pr.Color(18, 22, 30, 255))
        pr.draw_line_ex(pr.Vector2(cx, cy - 22), pr.Vector2(cx + 20, cy - 14), 2, pr.Color(18, 22, 30, 255))
        # Pearl tips
        pr.draw_circle(cx - 20, cy - 14, 3, pr.Color(255, 255, 255, 255))
        pr.draw_circle(cx, cy - 22, 3.5, pr.Color(255, 255, 255, 255))
        pr.draw_circle(cx + 20, cy - 14, 3, pr.Color(255, 255, 255, 255))

        # "FLYHIGH!" Text (White with bold dark drop shadow)
        self.draw_text("FLYHIGH!", 73, 78, 52, pr.Color(10, 14, 22, 240), bold=True)
        self.draw_text("FLYHIGH!", 70, 75, 52, pr.Color(255, 255, 255, 255), bold=True)

        # Subtitle
        self.draw_text("3 v 3   A R C A D E   V O L L E Y B A L L", 74, 136, 12, pr.Color(240, 246, 255, 240), bold=True)

    def _draw_top_right_profile(self, profile):
        """Draws User Profile, Level bar, and Crown counter card."""
        pw = 230
        ph = 56
        px = SCREEN_WIDTH - pw - 35
        py = 24

        pr.draw_rectangle_rounded(pr.Rectangle(px, py, pw, ph), 0.45, 8, pr.Color(16, 20, 30, 215))
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(px, py, pw, ph), 0.45, 8, 1, pr.Color(65, 80, 115, 130))

        # Avatar
        pr.draw_circle(px + 28, py + 28, 16, pr.Color(35, 45, 65, 255))
        pr.draw_circle(px + 28, py + 24, 6, pr.Color(245, 248, 255, 255))
        pr.draw_rectangle_rounded(pr.Rectangle(px + 20, py + 32, 16, 8), 0.4, 4, pr.Color(245, 248, 255, 255))

        # Name & Level
        p_name = profile.name if profile else "Player"
        p_lvl = profile.level if profile else 1
        p_cr = profile.crowns if profile else 0
        xp_pct = min(1.0, (profile.xp / max(1, profile.xp_max))) if profile else 0.35

        self.draw_text(p_name, px + 54, py + 11, 13, COLOR_TEXT_MAIN, bold=True)
        self.draw_text(f"LV {p_lvl}", px + 54, py + 27, 10, COLOR_TEXT_MUTED, bold=False)

        # XP progress bar
        pr.draw_rectangle_rounded(pr.Rectangle(px + 54, py + 41, 82, 4), 0.5, 4, pr.Color(40, 50, 70, 255))
        pr.draw_rectangle_rounded(pr.Rectangle(px + 54, py + 41, max(4, int(82 * xp_pct)), 4), 0.5, 4, COLOR_CYAN_ACCENT)

        # Crown Counter
        pr.draw_triangle(pr.Vector2(px + 175, py + 19), pr.Vector2(px + 168, py + 31), pr.Vector2(px + 182, py + 31), COLOR_GOLD_ACCENT)
        self.draw_text(str(p_cr), px + 188, py + 18, 13, COLOR_GOLD_ACCENT, bold=True)

    def _draw_bottom_right_featured_card(self, mouse_pos):
        """Draws 3v3 featured match preview card on bottom-right matching reference photo."""
        fw = 360
        fh = 135
        fx = SCREEN_WIDTH - fw - 35
        fy = SCREEN_HEIGHT - fh - 50

        card_rec = pr.Rectangle(fx, fy, fw, fh)
        is_hov = pr.check_collision_point_rec(mouse_pos, card_rec)

        # Yellow corner brush strokes around card frame (matching photo)
        pr.draw_triangle(pr.Vector2(fx - 8, fy + 8), pr.Vector2(fx + 24, fy - 6), pr.Vector2(fx, fy + 32), COLOR_GOLD_ACCENT)
        pr.draw_triangle(pr.Vector2(fx + fw + 8, fy + fh - 8), pr.Vector2(fx + fw - 24, fy + fh + 6), pr.Vector2(fx + fw, fy + fh - 32), COLOR_GOLD_ACCENT)

        # Base Card Frame
        pr.draw_rectangle_rounded(card_rec, 0.14, 8, pr.Color(16, 22, 34, 255))

        # Miniature Scenic Beach Court Landscape (Right half of the card)
        th_x = fx + 6
        th_y = fy + 6
        th_w = fw - 12
        th_h = fh - 12

        # Card base dark navy
        pr.draw_rectangle_rounded(pr.Rectangle(th_x, th_y, th_w, th_h), 0.12, 6, pr.Color(16, 22, 34, 255))

        # Right 70% Panoramic Thumbnail Graphic
        lx = fx + 105
        lw = fw - 111
        ly = fy + 6
        lh = fh - 12

        # Tropical sunset sky
        pr.draw_rectangle(lx, ly, lw, int(lh * 0.48), pr.Color(70, 160, 235, 255))
        # Warm golden sunset horizon
        pr.draw_rectangle(lx, ly + int(lh * 0.32), lw, int(lh * 0.16), pr.Color(255, 215, 145, 220))
        # Deep blue tropical sea
        pr.draw_rectangle(lx, ly + int(lh * 0.48), lw, int(lh * 0.14), pr.Color(30, 120, 200, 255))
        # Golden sand court
        pr.draw_rectangle(lx, ly + int(lh * 0.62), lw, int(lh * 0.38), pr.Color(235, 202, 150, 255))
        
        # Beach Volleyball Court & Net in thumbnail
        # Perspective sand court
        pr.draw_triangle(
            pr.Vector2(lx + 30, ly + lh),
            pr.Vector2(lx + lw - 20, ly + lh),
            pr.Vector2(lx + lw - 40, ly + int(lh * 0.64)),
            pr.Color(228, 192, 138, 255)
        )
        # Blue lines
        pr.draw_line_ex(pr.Vector2(lx + 45, ly + int(lh * 0.88)), pr.Vector2(lx + lw - 25, ly + int(lh * 0.88)), 2.0, pr.Color(35, 115, 235, 230))
        pr.draw_line_ex(pr.Vector2(lx + 60, ly + int(lh * 0.70)), pr.Vector2(lx + lw - 45, ly + int(lh * 0.70)), 1.5, pr.Color(35, 115, 235, 200))
        
        # Distant resort buildings / green palms
        pr.draw_rectangle(lx + lw - 45, ly + int(lh * 0.38), 28, int(lh * 0.22), pr.Color(220, 230, 240, 240))
        pr.draw_circle(lx + 35, ly + int(lh * 0.42), 14, pr.Color(40, 150, 55, 240))
        pr.draw_circle(lx + lw - 55, ly + int(lh * 0.44), 11, pr.Color(45, 160, 60, 240))

        # Soft horizontal shadow gradient over the left side to keep text crisp
        for gi in range(85):
            alpha = int(255 * (1.0 - gi / 85.0)**0.75)
            pr.draw_rectangle(lx + gi, ly, 1, lh, pr.Color(16, 22, 34, alpha))

        # Card Border
        border_col = COLOR_GOLD_ACCENT if is_hov else pr.Color(65, 80, 115, 180)
        pr.draw_rectangle_rounded_lines_ex(card_rec, 0.14, 8, 2 if is_hov else 1.2, border_col)

        # Typography
        self.draw_text("3v3", fx + 22, fy + 16, 36, pr.Color(255, 255, 255, 255), bold=True)
        self.draw_text("ARCADE VOLLEYBALL", fx + 22, fy + 58, 14, COLOR_GOLD_ACCENT, bold=True)
        self.draw_text("Fast matches. Real fun.", fx + 22, fy + 88, 12, pr.Color(235, 240, 250, 220), bold=False)

        # Yellow Chevron Button on Bottom-Right of Card
        cx = fx + fw - 35
        cy = fy + fh - 34
        r = 19 if is_hov else 17
        pr.draw_circle(cx, cy, r, COLOR_GOLD_ACCENT)
        pr.draw_line_ex(pr.Vector2(cx - 4, cy - 6), pr.Vector2(cx + 4, cy), 3.0, pr.Color(16, 20, 28, 255))
        pr.draw_line_ex(pr.Vector2(cx + 4, cy), pr.Vector2(cx - 4, cy + 6), 3.0, pr.Color(16, 20, 28, 255))

        # Bottom-Right Corner Screen Splatter & Version Tag
        # Yellow artistic paint splash in bottom-right corner of screen (matching photo)
        sp_x = SCREEN_WIDTH
        sp_y = SCREEN_HEIGHT
        pr.draw_triangle(pr.Vector2(sp_x, sp_y - 65), pr.Vector2(sp_x - 70, sp_y), pr.Vector2(sp_x, sp_y), COLOR_GOLD_ACCENT)
        pr.draw_triangle(pr.Vector2(sp_x, sp_y - 95), pr.Vector2(sp_x - 35, sp_y - 45), pr.Vector2(sp_x, sp_y - 25), COLOR_GOLD_ACCENT)
        pr.draw_triangle(pr.Vector2(sp_x - 45, sp_y), pr.Vector2(sp_x - 110, sp_y), pr.Vector2(sp_x - 65, sp_y - 22), COLOR_GOLD_ACCENT)
        # Version Tag
        self.draw_text("v1.0.0", SCREEN_WIDTH - 65, SCREEN_HEIGHT - 22, 11, pr.Color(18, 24, 35, 240), bold=True)

    def _draw_player_customize_modal(self, profile, character, mouse_pos):
        """Draws player cosmetic customization studio panel on the left."""
        mx = 45
        my = 40
        mw = 440
        mh = 640

        panel_rec = pr.Rectangle(mx, my, mw, mh)
        pr.draw_rectangle_rounded(panel_rec, 0.12, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(panel_rec, 0.12, 10, 2, COLOR_GOLD_ACCENT)

        # Header
        self.draw_text("PLAYER CUSTOMIZATION", mx + 24, my + 18, 22, COLOR_GOLD_ACCENT, bold=True)
        self.draw_text("Create your own unique arcade style", mx + 24, my + 44, 12, COLOR_TEXT_MUTED, bold=False)

        start_y = my + 72
        row_h = 42

        for idx, cat in enumerate(CUSTOMIZE_CATEGORIES):
            ry = start_y + idx * row_h
            is_sel = (idx == self.customize_index)

            row_rec = pr.Rectangle(mx + 16, ry, mw - 32, 36)
            r_bg = COLOR_BTN_HOVER if is_sel else pr.Color(24, 30, 46, 180)
            r_border = COLOR_CYAN_ACCENT if is_sel else COLOR_GLASS_BORDER

            pr.draw_rectangle_rounded(row_rec, 0.3, 6, r_bg)
            pr.draw_rectangle_rounded_lines_ex(row_rec, 0.3, 6, 1.5 if is_sel else 1, r_border)

            # Category Title
            cat_col = COLOR_GOLD_ACCENT if is_sel else COLOR_TEXT_MAIN
            self.draw_text(cat["name"], mx + 28, ry + 9, 13, cat_col, bold=is_sel)

            # Current Value Option
            field = cat["field"]
            cur_val = getattr(profile, field, 0)
            if cat["options"] is not None:
                val_str = cat["options"][cur_val % len(cat["options"])]
            else:
                val_str = f"#{cur_val}"

            full_val_txt = f"<  {val_str}  >"
            vw = self.measure_text(full_val_txt, 13, bold=is_sel)
            val_col = COLOR_CYAN_ACCENT if is_sel else COLOR_TEXT_MUTED
            self.draw_text(full_val_txt, mx + mw - vw - 28, ry + 9, 13, val_col, bold=is_sel)

        # Bottom Instructions & Action Buttons
        bot_y = my + mh - 90
        pr.draw_rectangle_rounded(pr.Rectangle(mx + 16, bot_y, mw - 32, 74), 0.25, 6, pr.Color(20, 26, 40, 220))
        self.draw_text("[W / S] Select Category   •   [A / D] Change Option", mx + 28, bot_y + 10, 11, COLOR_TEXT_MAIN, bold=False)
        self.draw_text("[R] Randomize Style   •   [Q / E] Rotate Character", mx + 28, bot_y + 28, 11, COLOR_CYAN_ACCENT, bold=False)
        self.draw_text("Press [ESC] to Save & Return to Menu", mx + 28, bot_y + 48, 12, COLOR_GOLD_ACCENT, bold=True)

    def _draw_stats_modal(self, profile):
        """Draws player career statistics modal."""
        pr.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, pr.Color(8, 10, 16, 225))

        mw = 620
        mh = 480
        mx = (SCREEN_WIDTH - mw) // 2
        my = (SCREEN_HEIGHT - mh) // 2

        pr.draw_rectangle_rounded(pr.Rectangle(mx, my, mw, mh), 0.12, 10, COLOR_GLASS_BG)
        pr.draw_rectangle_rounded_lines_ex(pr.Rectangle(mx, my, mw, mh), 0.12, 10, 2, COLOR_GOLD_ACCENT)

        title = "CAREER STATISTICS"
        tw = self.measure_text(title, 24, bold=True)
        self.draw_text(title, mx + (mw - tw) // 2, my + 24, 24, COLOR_GOLD_ACCENT, bold=True)

        if profile:
            win_rate = int((profile.matches_won / max(1, profile.matches_played)) * 100)
            stats = [
                ("Matches Played", str(profile.matches_played)),
                ("Matches Won", str(profile.matches_won)),
                ("Win Rate", f"{win_rate}%"),
                ("Spikes Scored", str(profile.spikes_scored)),
                ("Service Aces", str(profile.aces_scored)),
                ("Net Blocks Made", str(profile.blocks_made)),
                ("Diving Digs", str(profile.digs_made)),
                ("Player Level / Crowns", f"LV {profile.level}  |  {profile.crowns} 👑"),
            ]
        else:
            stats = []

        start_y = my + 75
        for idx, (label, val) in enumerate(stats):
            col_idx = idx % 2
            row_idx = idx // 2
            card_x = mx + 30 + col_idx * 285
            card_y = start_y + row_idx * 78

            c_rec = pr.Rectangle(card_x, card_y, 275, 66)
            pr.draw_rectangle_rounded(c_rec, 0.25, 6, pr.Color(22, 28, 44, 220))
            pr.draw_rectangle_rounded_lines_ex(c_rec, 0.25, 6, 1, COLOR_GLASS_BORDER)

            self.draw_text(label, card_x + 16, card_y + 12, 12, COLOR_TEXT_MUTED, bold=False)
            self.draw_text(val, card_x + 16, card_y + 32, 18, COLOR_GOLD_ACCENT, bold=True)

        close_txt = "Press [ESC], [Enter], or Click Anywhere to Close"
        cw = self.measure_text(close_txt, 14, bold=False)
        self.draw_text(close_txt, mx + (mw - cw) // 2, my + mh - 30, 14, COLOR_CYAN_ACCENT, bold=False)

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
