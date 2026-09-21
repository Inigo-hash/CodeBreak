"""Atlas landmarks. Citadel is a hook for a future STAGES['citadel'] map."""

STAGE_MAP_NODES = (
    {
        "id": "island", "number": 1, "name": "The Forgotten Village",
        "unlock_after": None,
        "plaque": (0.424, 0.772), "marker": (0.424, 0.826),
        "region": ((.08, .66), (.28, .59), (.50, .66), (.73, .83),
                   (.76, .94), (.55, .98), (.12, .95)),
        "glow": (.40, .80, .56, .36),
        "description": "Follow village trails into the island forest. Learn Python's foundations and face the Kapre at the Corrupted Core.",
        "content": "9 lessons / 9 keys / Kapre boss",
        "map_note": "Plays the existing Stage 1 Island map.",
    },
    {
        "id": "castle", "number": 2, "name": "The Ancient Depths",
        "unlock_after": "island",
        "plaque": (0.481, 0.455), "marker": (0.482, 0.500),
        "region": ((.20, .31), (.44, .26), (.64, .30), (.77, .38),
                   (.77, .60), (.57, .66), (.30, .58), (.18, .44)),
        "glow": (.49, .46, .48, .34),
        "description": "Ancient paths lead through forest, waterfalls and temple ruins. A new chapter of Python awaits.",
        "content": "Exploration preview",
        "map_note": "Currently opens the Castle lobby. The Ancient Depths lesson map is coming later.",
    },
    {
        "id": "citadel", "number": 3, "name": "The Corrupted Citadel",
        "unlock_after": "castle",
        "plaque": (0.645, 0.136), "marker": (0.645, 0.181),
        "region": ((.39, .055), (.64, .01), (.87, .025), (.94, .16),
                   (.79, .29), (.66, .30), (.45, .23)),
        "glow": (.67, .15, .48, .28),
        "description": "Beyond the mountain pass, the corrupted fortress waits. This final chapter is still being built.",
        "content": "Future chapter",
        "map_note": "No playable map is connected yet.",
    },
)


def stage_map_node(stage_id):
    return next((node for node in STAGE_MAP_NODES if node["id"] == stage_id), None)
