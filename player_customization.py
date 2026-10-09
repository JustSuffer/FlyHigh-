"""
FlyHigh! - 3D Volleyball Game
Player Profile & Character Customization Engine
Manages player identity, stats, level progression, and customized 3D cosmetic styles.
"""
import json
import os
import pyray as pr

PROFILE_FILE = "user_profile.json"

# --- Cosmetic Palettes ---
SKIN_TONES = [
    {"name": "Sun Peach",     "color": pr.Color(252, 218, 185, 255), "shadow": pr.Color(228, 188, 155, 255)},
    {"name": "Golden Tan",    "color": pr.Color(238, 188, 145, 255), "shadow": pr.Color(210, 160, 120, 255)},
    {"name": "Beach Bronze",  "color": pr.Color(205, 150, 110, 255), "shadow": pr.Color(175, 125,  85, 255)},
    {"name": "Fair Anime",    "color": pr.Color(255, 232, 214, 255), "shadow": pr.Color(230, 202, 182, 255)},
    {"name": "Deep Bronze",   "color": pr.Color(165, 115,  80, 255), "shadow": pr.Color(135,  88,  55, 255)},
]

HAIR_COLORS = [
    {"name": "Chestnut Brown", "color": pr.Color(95, 60, 42, 255)},
    {"name": "Jet Black",      "color": pr.Color(30, 32, 38, 255)},
    {"name": "Silver White",   "color": pr.Color(240, 242, 248, 255)},
    {"name": "Golden Blonde",  "color": pr.Color(245, 198, 85, 255)},
    {"name": "Ruby Red",       "color": pr.Color(215, 45, 55, 255)},
    {"name": "Ocean Cyan",     "color": pr.Color(35, 185, 235, 255)},
]

HAIR_STYLES = [
    {"name": "Spiky Crown",     "id": 0},
    {"name": "Wild Anime",      "id": 1},
    {"name": "Athletic Crop",   "id": 2},
    {"name": "Swept Flow",      "id": 3},
]

HEADBAND_COLORS = [
    {"name": "Pure White",      "color": pr.Color(250, 252, 255, 255)},
    {"name": "Midnight Black",  "color": pr.Color(25, 28, 35, 255)},
    {"name": "Electric Cyan",   "color": pr.Color(35, 200, 245, 255)},
    {"name": "Crimson Red",     "color": pr.Color(235, 45, 65, 255)},
    {"name": "Sunshine Gold",   "color": pr.Color(255, 215, 0, 255)},
    {"name": "None",            "color": None},
]

JERSEY_COLORS = [
    {"name": "Crisp White",     "color": pr.Color(248, 250, 252, 255)},
    {"name": "Midnight Black",  "color": pr.Color(26, 28, 36, 255)},
    {"name": "Sky Cyan",        "color": pr.Color(35, 180, 245, 255)},
    {"name": "Sunset Orange",   "color": pr.Color(255, 120, 40, 255)},
    {"name": "Crimson Red",     "color": pr.Color(225, 40, 60, 255)},
    {"name": "Royal Navy",      "color": pr.Color(25, 45, 115, 255)},
]

TRIM_COLORS = [
    {"name": "Jet Black",      "color": pr.Color(25, 28, 35, 255)},
    {"name": "Pure White",     "color": pr.Color(250, 252, 255, 255)},
    {"name": "Electric Cyan",  "color": pr.Color(35, 200, 245, 255)},
    {"name": "Golden Yellow",  "color": pr.Color(255, 215, 0, 255)},
]

BACK_LOGOS = [
    {"name": "FlyHigh Crown",  "id": 0},
    {"name": "Angel Wings",    "id": 1},
    {"name": "Flame",          "id": 2},
    {"name": "Lightning",      "id": 3},
    {"name": "None",           "id": 4},
]

SHORTS_COLORS = [
    {"name": "Midnight Black", "color": pr.Color(26, 28, 36, 255)},
    {"name": "Pure White",     "color": pr.Color(248, 250, 252, 255)},
    {"name": "Ocean Cyan",     "color": pr.Color(35, 180, 245, 255)},
    {"name": "Crimson Red",    "color": pr.Color(225, 40, 60, 255)},
    {"name": "Royal Navy",     "color": pr.Color(25, 45, 115, 255)},
]

WRISTBAND_COLORS = [
    {"name": "Jet Black",      "color": pr.Color(25, 28, 35, 255)},
    {"name": "Pure White",     "color": pr.Color(250, 252, 255, 255)},
    {"name": "Electric Cyan",  "color": pr.Color(35, 200, 245, 255)},
    {"name": "None",           "color": None},
]


class PlayerProfile:
    def __init__(self):
        # Identity
        self.name = "Player"
        self.level = 1
        self.xp = 140
        self.xp_max = 500
        self.crowns = 0

        # Stats
        self.matches_played = 0
        self.matches_won = 0
        self.spikes_scored = 0
        self.aces_scored = 0
        self.blocks_made = 0
        self.digs_made = 0

        # Cosmetics (Defaults strictly matching reference photo!)
        self.skin_tone_idx = 0       # Sun Peach
        self.hair_style_idx = 0      # Spiky Crown
        self.hair_color_idx = 0      # Chestnut Brown
        self.headband_idx = 0        # Pure White headband
        self.jersey_color_idx = 0    # Crisp White singlet
        self.jersey_trim_idx = 0     # Jet Black trim
        self.back_logo_idx = 0       # FlyHigh Crown
        self.jersey_number = 7       # #7
        self.shorts_color_idx = 0    # Midnight Black shorts
        self.shorts_trim_idx = 1     # Pure White trim
        self.wristband_idx = 0       # Jet Black wristbands

        self.load()

    def get_skin(self):
        idx = max(0, min(len(SKIN_TONES) - 1, self.skin_tone_idx))
        return SKIN_TONES[idx]["color"], SKIN_TONES[idx]["shadow"]

    def get_hair_color(self):
        idx = max(0, min(len(HAIR_COLORS) - 1, self.hair_color_idx))
        return HAIR_COLORS[idx]["color"]

    def get_headband_color(self):
        idx = max(0, min(len(HEADBAND_COLORS) - 1, self.headband_idx))
        return HEADBAND_COLORS[idx]["color"]

    def get_jersey_color(self):
        idx = max(0, min(len(JERSEY_COLORS) - 1, self.jersey_color_idx))
        return JERSEY_COLORS[idx]["color"]

    def get_jersey_trim(self):
        idx = max(0, min(len(TRIM_COLORS) - 1, self.jersey_trim_idx))
        return TRIM_COLORS[idx]["color"]

    def get_shorts_color(self):
        idx = max(0, min(len(SHORTS_COLORS) - 1, self.shorts_color_idx))
        return SHORTS_COLORS[idx]["color"]

    def get_shorts_trim(self):
        idx = max(0, min(len(TRIM_COLORS) - 1, self.shorts_trim_idx))
        return TRIM_COLORS[idx]["color"]

    def get_wristband_color(self):
        idx = max(0, min(len(WRISTBAND_COLORS) - 1, self.wristband_idx))
        return WRISTBAND_COLORS[idx]["color"]

    def to_dict(self):
        return {
            "name": self.name,
            "level": self.level,
            "xp": self.xp,
            "xp_max": self.xp_max,
            "crowns": self.crowns,
            "matches_played": self.matches_played,
            "matches_won": self.matches_won,
            "spikes_scored": self.spikes_scored,
            "aces_scored": self.aces_scored,
            "blocks_made": self.blocks_made,
            "digs_made": self.digs_made,
            "skin_tone_idx": self.skin_tone_idx,
            "hair_style_idx": self.hair_style_idx,
            "hair_color_idx": self.hair_color_idx,
            "headband_idx": self.headband_idx,
            "jersey_color_idx": self.jersey_color_idx,
            "jersey_trim_idx": self.jersey_trim_idx,
            "back_logo_idx": self.back_logo_idx,
            "jersey_number": self.jersey_number,
            "shorts_color_idx": self.shorts_color_idx,
            "shorts_trim_idx": self.shorts_trim_idx,
            "wristband_idx": self.wristband_idx,
        }

    def save(self):
        try:
            with open(PROFILE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=4)
        except Exception as e:
            print(f"[PlayerProfile] Error saving profile: {e}")

    def load(self):
        if not os.path.exists(PROFILE_FILE):
            return
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.name = data.get("name", self.name)
                self.level = data.get("level", self.level)
                self.xp = data.get("xp", self.xp)
                self.xp_max = data.get("xp_max", self.xp_max)
                self.crowns = data.get("crowns", self.crowns)
                self.matches_played = data.get("matches_played", self.matches_played)
                self.matches_won = data.get("matches_won", self.matches_won)
                self.spikes_scored = data.get("spikes_scored", self.spikes_scored)
                self.aces_scored = data.get("aces_scored", self.aces_scored)
                self.blocks_made = data.get("blocks_made", self.blocks_made)
                self.digs_made = data.get("digs_made", self.digs_made)
                self.skin_tone_idx = data.get("skin_tone_idx", self.skin_tone_idx)
                self.hair_style_idx = data.get("hair_style_idx", self.hair_style_idx)
                self.hair_color_idx = data.get("hair_color_idx", self.hair_color_idx)
                self.headband_idx = data.get("headband_idx", self.headband_idx)
                self.jersey_color_idx = data.get("jersey_color_idx", self.jersey_color_idx)
                self.jersey_trim_idx = data.get("jersey_trim_idx", self.jersey_trim_idx)
                self.back_logo_idx = data.get("back_logo_idx", self.back_logo_idx)
                self.jersey_number = data.get("jersey_number", self.jersey_number)
                self.shorts_color_idx = data.get("shorts_color_idx", self.shorts_color_idx)
                self.shorts_trim_idx = data.get("shorts_trim_idx", self.shorts_trim_idx)
                self.wristband_idx = data.get("wristband_idx", self.wristband_idx)
        except Exception as e:
            print(f"[PlayerProfile] Error loading profile: {e}")
