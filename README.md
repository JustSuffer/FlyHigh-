# 🏐 FlyHigh! - 3D Arcade Volleyball Game (3v3 Edition)

**FlyHigh!** is a high-tempo, arcade 3D volleyball game inspired by *Just Volleyball* and sports anime. Built with Raylib and Python, it delivers responsive arcade gameplay with full support for both keyboard/mouse and gamepad controllers.

---

## 🌟 Key Features

1. **3v3 Team Matchups:**
   - Full 3 vs 3 roster format:
     - **Your Team (3 Players):** Captain (Player / #5), Setter (AI #2), Wing Blocker (AI #4).
     - **Opponent Team (3 Players):** Rival Captain (#1), Opponent Setter (#3), Libero/Server (#6).
   - **Player Priority System:** AI teammates intelligently yield reception space when you are near the ball's landing point.

2. **NBA 2K-Style Shot Timing Meter:**
   - Visual timing meter appears when jumping for serves and spikes:
     - **Green (Perfect Timing):** Explosive 26 m/s power spike line-drive, or devastating knuckleball Float Serve!
     - **Yellow (Good Timing):** Solid, accurate 18.5 m/s hit.
     - **Red (Off-Time Contact):** Weak, inaccurate mismit popping high and slow.

3. **Authentic Volleyball Moves & Mechanics:**
   - **Hold & Toss Serve:** The ball starts locked in the server's hands at the baseline. Press `SPACE` or `L-CLICK` to toss the ball high into the air, then jump and strike!
   - **Knuckleball Float Serve:** In mid-air, hit with `Left Click + E` on Green timing. The ball produces zero spin with erratic aerodynamic air wobbles and sharp drops over the net!
   - **Acrobatic Roll Dig:** Grounded `L-CTRL + Right Click` triggers a diving roll across the floor to save distant landing balls right before impact, popping the ball towards your reticle (5-second cooldown).
   - **Setter Dump:** Grounded `Right Click + E` executes a surprise tip-over attack directly into the opponent's unguarded court.
   - **Emergency Air Bailout:** In mid-air, `L-CTRL + Left Click` allows an emergency extended one-hand tap/kick over the net to save the rally.
   - **Bump / Receive:** Grounded `L-CTRL` digs the ball towards your mouse cursor reticle.
   - **Overhead Set:** `Right Click` sends a floating, high-arcing pass to your cursor target.

4. **Complete In-Game Settings Menu:**
   - Master Volume slider (0% to 100%) and Mute toggle.
   - Display Mode: Windowed vs Borderless Fullscreen.
   - Resolution presets: 1280x720 (HD), 1600x900, 1920x1080 (FHD).
   - Default Camera angle presets (Behind Player, Side Broadcast, Dynamic Action, Top-Down).

5. **100% English & Volleyball Terminology:**
   - Clean, airy typography with zero character glyph corruption.
   - Authentic terminology (`DIG`, `SET`, `SPIKE`, `FLOAT SERVE`, `SETTER DUMP`, `ROLL DIG`, `ACE!`, `OUT OF BOUNDS!`).

---

## 🎮 Controls Reference

| Action | Keyboard & Mouse | Gamepad / Joystick (Xbox / PS) |
| :--- | :--- | :--- |
| **Move** | `[W, A, S, D]` (`D` = Screen Right) | **Left Stick** / D-Pad |
| **Aim Reticle** | **Mouse Cursor** (Court Floor) | **Right Stick** |
| **Jump** | `[SPACE]` (Always Active) | **(A)** / Cross |
| **Serve Toss** | `[SPACE]` or `[L-CLICK]` | **(A)** or **(X)** |
| **Power Spike (In-Air)** | `[L-CLICK]` (Timing Meter) | **(A)** (Timing Meter) |
| **Float Serve (In-Air)** | `[L-CLICK + E]` (Green Timing) | **(A) + (X)** |
| **Dump / Soft Tip (In-Air)** | `[E]` (Tip over block) | **(X)** |
| **Air Bailout (In-Air)** | `[L-CTRL + L-CLICK]` | **(LT) + (A)** |
| **Overhead Pass / Set** | `[R-CLICK]` | **(Y)** / Triangle |
| **Setter Dump (Grounded)** | `[R-CLICK + E]` | **(Y) + (X)** |
| **Receive / Dig (Grounded)** | `[L-CTRL]` (Aims to cursor) | **(LT)** or **(X)** |
| **Roll Dig (5s Cooldown)** | `[L-CTRL + R-CLICK]` | **(LT) + (Y)** |
| **Camera View** | `[TAB]` | **(BACK / VIEW)** |
| **Pause / Menu** | `[ESC]` (Does not exit game!) | **(START / MENU)** |

---

## 🚀 Running & Building

### 1. Run Pre-Built Standalone Executable
Launch the bundled executable directly:
📁 `dist\FlyHigh_Volleyball\FlyHigh_Volleyball.exe`

### 2. Run via Python
```bash
python main.py
```
*(Or double-click `run_game.bat`)*

### 3. Rebuild Standalone `.exe`
Run the automated build script:
```bash
build_exe.bat
```
This produces an updated, standalone distribution package in `dist\FlyHigh_Volleyball\`.
