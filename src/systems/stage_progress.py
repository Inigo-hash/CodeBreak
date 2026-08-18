"""
stage_progress.py

What the player has actually seen and done in a stage: which enemies they
have met, which items they have searched, and which objectives are
finished. The Stage Information panel reads this to decide whether to
print a real entry or a "???" placeholder.

Kept apart from the data files on purpose - stages.py describes what
*exists* in a stage and never changes, while this describes what *this
player* has found and changes constantly. Mixing the two would mean the
content files could no longer be shared between save slots.

Ids are held in sets while the game runs (membership tests happen every
frame, and discovering the same barrel twice should be a no-op) and
written out as sorted lists by to_dict(), because sets are not JSON
serialisable and save_manager dumps straight to JSON.
"""

from src.data.items import get_item, item_id_for_action


class StageProgress:
    """
    Discovery and objective state for the current stage.

    Round-trips through the save file:

        progress = StageProgress.from_dict(save_state.get("stage_progress"))
        ...
        save_state["stage_progress"] = progress.to_dict()
    """

    def __init__(self, discovered_enemies=None, discovered_items=None,
                 objectives_done=None):
        self.discovered_enemies = set(discovered_enemies or ())
        self.discovered_items = set(discovered_items or ())
        self.objectives_done = set(objectives_done or ())

    # -- discovery ----------------------------------------------------------
    # Each of these returns True only the *first* time an id is recorded,
    # so a caller can use the return value to fire a "New entry!" toast
    # later without tracking the previous state itself.

    def discover_enemy(self, enemy_id):
        """Record an enemy as met. True if this is the first sighting."""

        if not enemy_id or enemy_id in self.discovered_enemies:
            return False

        self.discovered_enemies.add(enemy_id)
        return True

    def discover_item(self, item_id):
        """Record an item as found. True if this is the first time."""

        if not item_id or item_id in self.discovered_items:
            return False

        self.discovered_items.add(item_id)
        return True

    def knows_enemy(self, enemy_id):
        return enemy_id in self.discovered_enemies

    def knows_item(self, item_id):
        return item_id in self.discovered_items

    # -- objectives ---------------------------------------------------------

    def complete_objective(self, objective_id):
        """Mark an objective done. True if it was not already done."""

        if not objective_id or objective_id in self.objectives_done:
            return False

        self.objectives_done.add(objective_id)
        return True

    def is_objective_done(self, objective_id):
        return objective_id in self.objectives_done

    def sync_objectives(self, stage, challenges_passed=()):
        """
        Complete any objective whose condition is already satisfied, and
        return the list of objective ids newly completed by this call.

        Called after a discovery or a passed challenge rather than every
        frame - it is cheap, but there is no reason to run it constantly.

        "explore" objectives are left alone: nothing records zone entry
        yet, so there is no condition to check against.
        """

        newly_done = []

        for objective in stage.get("objectives", []):

            if self.is_objective_done(objective["id"]):
                continue

            kind = objective.get("kind")
            target = objective.get("target")

            if kind == "interact":
                satisfied = self.knows_item(target)
            elif kind == "challenge":
                satisfied = target in challenges_passed
            else:
                satisfied = False

            if satisfied and self.complete_objective(objective["id"]):
                newly_done.append(objective["id"])

        return newly_done

    def objective_counts(self, stage):
        """
        (done, total) counted over the stage's *required* objectives.

        Optional ones are deliberately excluded so the tracker's "2/3"
        cannot stall at less than full just because a side objective was
        skipped.
        """

        required = [
            o for o in stage.get("objectives", [])
            if not o.get("optional")
        ]

        done = sum(1 for o in required if self.is_objective_done(o["id"]))

        return done, len(required)

    # -- convenience --------------------------------------------------------

    def discover_by_action(self, action):
        """
        Record whatever a Tiled ``actions`` string refers to, e.g.
        "search_vase" -> the "vase" item. Returns True on a first-time
        discovery, False for a repeat or an unmapped action.

        This is the single place that knows searching a map object is
        what counts as discovering an item, which keeps game.py's
        interaction code down to one line.
        """

        item_id = item_id_for_action(action)

        if item_id is None or get_item(item_id) is None:
            return False

        return self.discover_item(item_id)

    # -- persistence --------------------------------------------------------

    def to_dict(self):
        """JSON-friendly snapshot for save_manager."""

        return {
            "discovered_enemies": sorted(self.discovered_enemies),
            "discovered_items": sorted(self.discovered_items),
            "objectives_done": sorted(self.objectives_done),
        }

    @classmethod
    def from_dict(cls, data):
        """
        Rebuild from a save file. A missing or malformed section gives a
        blank progress object rather than an error, so saves written
        before this feature existed still load.
        """

        if not isinstance(data, dict):
            return cls()

        return cls(
            discovered_enemies=data.get("discovered_enemies", []),
            discovered_items=data.get("discovered_items", []),
            objectives_done=data.get("objectives_done", []),
        )
