"""Campaign combat tuning; profiles do not change reach or attack wind-up.

Citadel is reserved for future content, not a playable-stage declaration.
Rewards, body sizes, patrol boundaries and player stats remain independent.
"""
STAGE_COMBAT_TIERS = {"island": 1, "castle": 2, "citadel": 3}

COMBAT_PROFILES = {
    1: {"name": "Beginner", "hp": 1.0, "boss_hp": 1.0, "damage": 1.0,
        "speed": 1.0, "cooldown": 1.0, "committed_attacks": False},
    2: {"name": "Intermediate", "hp": 1.35, "boss_hp": 1.20, "damage": 1.30,
        "speed": 1.10, "cooldown": 0.85, "committed_attacks": True},
    3: {"name": "Advanced", "hp": 1.70, "boss_hp": 1.55, "damage": 1.60,
        "speed": 1.18, "cooldown": 0.74, "committed_attacks": True},
}
