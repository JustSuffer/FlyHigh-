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

        kb_active = (kb_move_x != 0.0 or kb_move_z != 0.0 or
                     pr.is_key_pressed(pr.KEY_SPACE) or
                     pr.is_key_pressed(pr.KEY_J) or pr.is_key_pressed(pr.KEY_K) or
                     pr.is_key_pressed(pr.KEY_L) or pr.is_key_pressed(pr.KEY_LEFT_SHIFT) or
                     pr.is_key_pressed(pr.KEY_TAB) or pr.is_key_pressed(pr.KEY_ESCAPE) or
                     pr.is_key_pressed(pr.KEY_ENTER) or
                     pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT) or
                     pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_RIGHT))

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

        # BUMP (J / Left Click / Gamepad X)
        self.bump_pressed = (
            pr.is_key_pressed(pr.KEY_J) or
            pr.is_key_pressed(pr.KEY_Z) or
            pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT) or
            (has_gamepad and pr.is_gamepad_button_pressed(self.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_FACE_LEFT))
        )

        # SET (K / Right Click / Gamepad Y)
        self.set_pressed = (
            pr.is_key_pressed(pr.KEY_K) or
            pr.is_key_pressed(pr.KEY_X) or
            pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_RIGHT) or
            (has_gamepad and pr.is_gamepad_button_pressed(self.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_FACE_UP))
        )

        # SPIKE (Space in air or L or Gamepad B / A)
        self.spike_pressed = (
            pr.is_key_pressed(pr.KEY_L) or
            pr.is_key_pressed(pr.KEY_SPACE) or
            (has_gamepad and (
                pr.is_gamepad_button_pressed(self.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_FACE_DOWN) or
                pr.is_gamepad_button_pressed(self.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_FACE_RIGHT)
            ))
        )

        # DIVE (Shift / C / Gamepad RB or B)
        self.dive_pressed = (
            pr.is_key_pressed(pr.KEY_LEFT_SHIFT) or
            pr.is_key_pressed(pr.KEY_C) or
            (has_gamepad and (
                pr.is_gamepad_button_pressed(self.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_TRIGGER_1) or
                pr.is_gamepad_button_pressed(self.gamepad_id, pr.GAMEPAD_BUTTON_RIGHT_FACE_RIGHT)
            ))
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
                "BUMP": "(X)",
                "SET": "(Y)",
                "SPIKE": "(A) / (B)",
                "DIVE": "(RB)",
                "SERVE": "Toss: (A) | Hit: (A)/(B)",
                "CAMERA": "(BACK)",
                "PAUSE": "(START)",
            }
        else:
            prompts = {
                "JUMP": "[SPACE]",
                "BUMP": "[J] / L-Click",
                "SET": "[K] / R-Click",
                "SPIKE": "[SPACE] / [L]",
                "DIVE": "[SHIFT]",
                "SERVE": "Toss: [SPACE] | Hit: [SPACE]/[L]",
                "CAMERA": "[TAB] / [V]",
                "PAUSE": "[ESC]",
            }
        return prompts.get(action_name, "")
