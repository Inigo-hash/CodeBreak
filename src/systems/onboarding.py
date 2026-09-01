"""Session-level first-time onboarding decisions.

A player with a save has already entered the game, while a brand-new player
needs the short menu walkthrough once. The in-menu HELP button remains the
explicit replay path after that first automatic showing.
"""

_walkthrough_seen = False


def opening_walkthrough_needed(slot_exists, slot_count):
    """Return True once per session, and only when every save slot is empty."""

    global _walkthrough_seen
    if _walkthrough_seen:
        return False
    _walkthrough_seen = True
    return not any(slot_exists(slot) for slot in range(1, slot_count + 1))


def _reset_walkthrough_for_tests():
    """Reset module state for deterministic unit tests."""

    global _walkthrough_seen
    _walkthrough_seen = False
