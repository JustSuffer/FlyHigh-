"""
FlyHigh! - 3D Volleyball Game
Unified Input System for Keyboard & Gamepad/Joystick
Seamless automatic switching, deadzone calibration, and vibration feedback.
"""
import pyray as pr
import math

class InputManager:
    DEADZONE = 0.22

    def __init__(self, gamepad_id=0):
        self.gamepad_id = gamepad_id
        self.active_device = "KEYBOARD"  # "KEYBOARD" or "GAMEPAD"
        
        # State values
        self.move_x = 0.0
        self.move_z = 0.0
        self.aim_x = 0.0
        self.aim_z = 0.0
        
        # Action triggers (down, pressed, released)
        self.jump_pressed = False
        self.jump_down = False
        self.ctrl_down = False
        self.ctrl_pressed = False
        self.e_down = False
        self.e_pressed = False
        self.lmb_pressed = False
        self.lmb_down = False
        self.rmb_pressed = False
        self.rmb_down = False

        self.bump_pressed = False
        self.set_pressed = False
        self.spike_pressed = False
        self.dive_pressed = False
        self.camera_pressed = False
        self.pause_pressed = False
        self.select_pressed = False

    def update(self):
        """Polls input from both keyboard and gamepad, unifying states."""
        # 1. Check if gamepad is available
        has_gamepad = pr.is_gamepad_available(self.gamepad_id)
        
        # Reset frame variables
        kb_move_x = 0.0
        kb_move_z = 0.0
        gp_move_x = 0.0
        gp_move_z = 0.0
        
        # --- Keyboard Movement ---
        # Screen perspective: D is Right, A is Left.
        # In court world coordinates from camera view: World -X is Screen Right, World +X is Screen Left.
        if pr.is_key_down(pr.KEY_W) or pr.is_key_down(pr.KEY_UP):
            kb_move_z += 1.0  # Towards net (+Z)
        if pr.is_key_down(pr.KEY_S) or pr.is_key_down(pr.KEY_DOWN):
            kb_move_z -= 1.0  # Away from net (-Z)
        if pr.is_key_down(pr.KEY_D) or pr.is_key_down(pr.KEY_RIGHT):
            kb_move_x -= 1.0  # Screen Right -> World -X
        if pr.is_key_down(pr.KEY_A) or pr.is_key_down(pr.KEY_LEFT):
            kb_move_x += 1.0  # Screen Left  -> World +X

        # Raw key & mouse button polling
        self.ctrl_down = (
            pr.is_key_down(pr.KEY_LEFT_CONTROL) or
            pr.is_key_down(pr.KEY_RIGHT_CONTROL) or
            (has_gamepad and (
                pr.is_gamepad_button_down(self.gamepad_id, pr.GAMEPAD_BUTTON_LEFT_TRIGGER_1) or
                pr.get_gamepad_axis_movement(self.gamepad_id, pr.GAMEPAD_AXIS_LEFT_TRIGGER) > 0.3
            ))
        )
        self.ctrl_pressed = (
            pr.is_key_pressed(pr.KEY_LEFT_CONTROL) or
            pr.is_key_pressed(pr.KEY_RIGHT_CONTROL) or
            (has_gamepad and pr.is_gamepad_button_pressed(self.gamepad_id, pr.GAMEPAD_BUTTON_LEFT_TRIGGER_1))
        )

        self.e_down = (
            pr.is_key_down(pr.KEY_E) or
            (has_gamepad and pr.is_gamepad_button_down(self.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_FACE_LEFT))
        )
        self.e_pressed = (
            pr.is_key_pressed(pr.KEY_E) or
            (has_gamepad and pr.is_gamepad_button_pressed(self.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_FACE_LEFT))
        )

        self.lmb_pressed = pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT)
        self.lmb_down = pr.is_mouse_button_down(pr.MOUSE_BUTTON_LEFT)
        self.rmb_pressed = pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_RIGHT)
        self.rmb_down = pr.is_mouse_button_down(pr.MOUSE_BUTTON_RIGHT)

        kb_active = (kb_move_x != 0.0 or kb_move_z != 0.0 or
                     pr.is_key_pressed(pr.KEY_SPACE) or
                     pr.is_key_pressed(pr.KEY_E) or
                     pr.is_key_pressed(pr.KEY_LEFT_CONTROL) or
                     pr.is_key_pressed(pr.KEY_J) or pr.is_key_pressed(pr.KEY_K) or
                     pr.is_key_pressed(pr.KEY_L) or pr.is_key_pressed(pr.KEY_LEFT_SHIFT) or
                     pr.is_key_pressed(pr.KEY_TAB) or pr.is_key_pressed(pr.KEY_ESCAPE) or
                     pr.is_key_pressed(pr.KEY_ENTER) or
                     self.lmb_pressed or self.rmb_pressed)

        # --- Gamepad Movement & Aiming ---
        gp_active = False
        gp_aim_x = 0.0
        gp_aim_z = 0.0

        if has_gamepad:
            raw_lx = pr.get_gamepad_axis_movement(self.gamepad_id, pr.GAMEPAD_AXIS_LEFT_X)
            raw_ly = pr.get_gamepad_axis_movement(self.gamepad_id, pr.GAMEPAD_AXIS_LEFT_Y)
            
            # Left Stick: Right stick -> World -X (Screen Right)
            if abs(raw_lx) > self.DEADZONE:
                gp_move_x = -raw_lx
                gp_active = True
            if abs(raw_ly) > self.DEADZONE:
                gp_move_z = -raw_ly  # Up on stick is towards net (+Z)
                gp_active = True

            # D-pad support
            if pr.is_gamepad_button_down(self.gamepad_id, pr.GAMEPAD_BUTTON_LEFT_FACE_UP):
                gp_move_z = 1.0
                gp_active = True
            if pr.is_gamepad_button_down(self.gamepad_id, pr.GAMEPAD_BUTTON_LEFT_FACE_DOWN):
                gp_move_z = -1.0
                gp_active = True
            if pr.is_gamepad_button_down(self.gamepad_id, pr.GAMEPAD_BUTTON_LEFT_FACE_LEFT):
                gp_move_x = 1.0   # Screen Left -> World +X
                gp_active = True
            if pr.is_gamepad_button_down(self.gamepad_id, pr.GAMEPAD_BUTTON_LEFT_FACE_RIGHT):
                gp_move_x = -1.0  # Screen Right -> World -X
                gp_active = True

            # Right Stick for precise aiming
            raw_rx = pr.get_gamepad_axis_movement(self.gamepad_id, pr.GAMEPAD_AXIS_RIGHT_X)
            raw_ry = pr.get_gamepad_axis_movement(self.gamepad_id, pr.GAMEPAD_AXIS_RIGHT_Y)
            if abs(raw_rx) > self.DEADZONE or abs(raw_ry) > self.DEADZONE:
                gp_aim_x = -raw_rx
                gp_aim_z = -raw_ry
                gp_active = True

            # Any gamepad button pressed?
            for btn in [
                pr.GAMEPAD_BUTTON_RIGHT_FACE_DOWN,  # A
                pr.GAMEPAD_BUTTON_RIGHT_FACE_LEFT,  # X
                pr.GAMEPAD_BUTTON_RIGHT_FACE_UP,    # Y
                pr.GAMEPAD_BUTTON_RIGHT_FACE_RIGHT, # B
                pr.GAMEPAD_BUTTON_RIGHT_TRIGGER_1,  # RB
                pr.GAMEPAD_BUTTON_LEFT_TRIGGER_1,   # LB
                pr.GAMEPAD_BUTTON_MIDDLE_RIGHT,     # START
                pr.GAMEPAD_BUTTON_MIDDLE_LEFT       # BACK
            ]:
                if pr.is_gamepad_button_pressed(self.gamepad_id, btn):
                    gp_active = True
                    break

        # Determine active device
        if gp_active:
            self.active_device = "GAMEPAD"
        elif kb_active:
            self.active_device = "KEYBOARD"

        # Combine movement vector
        if self.active_device == "GAMEPAD" and has_gamepad:
            self.move_x = gp_move_x
            self.move_z = gp_move_z
            self.aim_x = gp_aim_x if (gp_aim_x != 0 or gp_aim_z != 0) else gp_move_x
            self.aim_z = gp_aim_z if (gp_aim_x != 0 or gp_aim_z != 0) else gp_move_z
        else:
            self.move_x = kb_move_x
            self.move_z = kb_move_z
            self.aim_x = self.move_x
            self.aim_z = self.move_z

        # Normalize movement length if > 1.0
        mag = math.sqrt(self.move_x * self.move_x + self.move_z * self.move_z)
        if mag > 1.0:
            self.move_x /= mag
            self.move_z /= mag

        # Combine Actions
        # JUMP (Space / Gamepad A)
        self.jump_pressed = pr.is_key_pressed(pr.KEY_SPACE) or (
            has_gamepad and pr.is_gamepad_button_pressed(self.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_FACE_DOWN)
        )
        self.jump_down = pr.is_key_down(pr.KEY_SPACE) or (
            has_gamepad and pr.is_gamepad_button_down(self.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_FACE_DOWN)
        )

        # BUMP / RECEIVE (L-CTRL / J / Gamepad LB / X)
        self.bump_pressed = (
            self.ctrl_pressed or
            pr.is_key_pressed(pr.KEY_J) or
            (has_gamepad and pr.is_gamepad_button_pressed(self.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_FACE_LEFT))
        )

        # SET / PASS (Right Click / K / Gamepad Y)
        self.set_pressed = (
            self.rmb_pressed or
            pr.is_key_pressed(pr.KEY_K) or
            (has_gamepad and pr.is_gamepad_button_pressed(self.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_FACE_UP))
        )

        # SPIKE / HIT (Left Click / Space in air / Gamepad B or A)
        self.spike_pressed = (
            self.lmb_pressed or
            pr.is_key_pressed(pr.KEY_L) or
            (has_gamepad and (
                pr.is_gamepad_button_pressed(self.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_FACE_RIGHT)
            ))
        )

        # DIVE (Shift / C / Gamepad RB)
        self.dive_pressed = (
            pr.is_key_pressed(pr.KEY_LEFT_SHIFT) or
            pr.is_key_pressed(pr.KEY_C) or
            (has_gamepad and pr.is_gamepad_button_pressed(self.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_TRIGGER_1))
        )

        # CAMERA (Tab / V / Gamepad Select)
        self.camera_pressed = (
            pr.is_key_pressed(pr.KEY_TAB) or
            pr.is_key_pressed(pr.KEY_V) or
            (has_gamepad and pr.is_gamepad_button_pressed(self.gamepad_id, pr.GAMEPAD_BUTTON_MIDDLE_LEFT))
        )

        # PAUSE / MENU (Escape / P / Gamepad Start)
        self.pause_pressed = (
            pr.is_key_pressed(pr.KEY_ESCAPE) or
            pr.is_key_pressed(pr.KEY_P) or
            (has_gamepad and pr.is_gamepad_button_pressed(self.gamepad_id, pr.GAMEPAD_BUTTON_MIDDLE_RIGHT))
        )

        # SELECT / ENTER (Enter / Space / Gamepad A)
        self.select_pressed = (
            pr.is_key_pressed(pr.KEY_ENTER) or
            pr.is_key_pressed(pr.KEY_SPACE) or
            (has_gamepad and pr.is_gamepad_button_pressed(self.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_FACE_DOWN))
        )

    # --- Compound Action Helpers ---
    @property
    def is_roll_dig_triggered(self):
        """L-CTRL held + Right Click: Acrobatic diving roll dig towards landing spot."""
        return self.ctrl_down and self.rmb_pressed

    @property
    def is_air_bailout_triggered(self):
        """L-CTRL held + Left Click in air: Emergency tap/bailout when out of reach."""
        return self.ctrl_down and self.lmb_pressed

    @property
    def is_float_serve_triggered(self):
        """In-air: Left Click + E simultaneously or E held with Left Click."""
        return (self.lmb_pressed and self.e_down) or (self.e_pressed and self.lmb_down)

    @property
    def is_setter_dump_triggered(self):
        """Grounded: Right Click held + E pressed (or E held + Right Click)."""
        return (self.rmb_down and self.e_pressed) or (self.e_down and self.rmb_pressed)

    def trigger_rumble(self, left_motor=0.6, right_motor=0.8, duration=0.25):
        """Vibrates the connected gamepad if supported."""
        if pr.is_gamepad_available(self.gamepad_id):
            try:
                pr.set_gamepad_vibration(self.gamepad_id, left_motor, right_motor, duration)
            except Exception:
                pass

    def get_prompt_text(self, action_name):
        """Returns button label based on currently active device."""
        if self.active_device == "GAMEPAD":
            prompts = {
                "JUMP": "(A)",
                "TOSS": "(Y)",
                "RECEIVE": "(LT) / (X)",
                "PASS": "(Y)",
                "SPIKE": "(A) / (B)",
                "DUMP": "(X)",
                "SETTER_DUMP": "(Y) + (X)",
                "ROLL_DIG": "(LT) + (Y)",
                "AIR_BAILOUT": "(LT) + (A)",
                "FLOAT_SERVE": "(A) + (X)",
                "CAMERA": "(BACK)",
                "PAUSE": "(START)",
            }
        else:
            prompts = {
                "JUMP": "[SPACE]",
                "TOSS": "[R-CLICK]",
                "RECEIVE": "[L-CTRL]",
                "PASS": "[R-CLICK]",
                "SPIKE": "[L-CLICK]",
                "DUMP": "[E]",
                "SETTER_DUMP": "[R-CLICK + E]",
                "ROLL_DIG": "[L-CTRL + R-CLICK]",
                "AIR_BAILOUT": "[L-CTRL + L-CLICK]",
                "FLOAT_SERVE": "[L-CLICK + E]",
                "CAMERA": "[TAB]",
                "PAUSE": "[ESC]",
            }
        return prompts.get(action_name, "")
