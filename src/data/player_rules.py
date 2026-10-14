"""Player recovery rules shared by gameplay and the tutor's game facts.

Keep this module independent of pygame so the tutor server can import it.
"""
PLAYER_MAX_HP = 100
PLAYER_MAX_ENERGY = 100
PLAYER_DODGE_ENERGY_COST = 25
PLAYER_ENERGY_REGEN = 8.0
PLAYER_TORCH_ENERGY_REGEN = 32.0
PLAYER_TORCH_HP_REGEN = 20.0
PLAYER_TORCH_HEAL_DELAY = 2.0
