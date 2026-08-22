"""
zones.py

Named regions of the world map, used to label areas on the minimap -
the same way most RPGs name their overworld regions.

Each zone's rect is stored as FRACTIONS of the map's total width and
height (0.0 - 1.0), not raw pixel coordinates. A zone positioned at
"the top-left 20% of the map" stays correct even if the map's actual
pixel size ever changes. game.py converts these fractions into real
pixel rects once, at load time.

To adjust a zone: nudge x, y (top-left corner) or width, height,
all as values between 0.0 and 1.0, then reload and check the minimap.
Use the F6 debug key in game.py to print your current position as a
fraction, so you can walk to a landmark and read off exact numbers.
"""

ZONES = [
    {
        "name": "The Corrupted Core",
        "rect": (0.30, 0.00, 0.44, 0.32),
        "is_boss_zone": True,
    },
    {
        "name": "Whispering Thicket",
        "rect": (0.12, 0.03, 0.16, 0.18),
    },
    {
        "name": "Sunfall Grove",
        "rect": (0.86, 0.00, 0.14, 0.18),
    },
    {
        "name": "Mosswood Hollow",
        "rect": (0.05, 0.20, 0.14, 0.16),
    },
    {
        "name": "Ferngate Clearing",
        "rect": (0.14, 0.40, 0.12, 0.15),
    },
    {
        "name": "Stonebrook Rise",
        "rect": (0.77, 0.36, 0.11, 0.16),
    },
    {
        "name": "Driftwood Crossing",
        "rect": (0.63, 0.52, 0.13, 0.14),
    },
    {
        "name": "Hollow Pine Thicket",
        "rect": (0.87, 0.46, 0.13, 0.20),
    },
    {
        "name": "Willowmere Fields",
        "rect": (0.00, 0.78, 0.22, 0.22),
    },
    {
        "name": "Amber Hollow",
        "rect": (0.76, 0.75, 0.24, 0.25),
    },
]


def get_zone_at(world_x, world_y, map_width, map_height):
    """
    Returns the name of the zone containing the given world-space
    point, or "Wilderness" if the point falls outside every defined
    zone. Earlier entries in ZONES take priority if two ever overlap.
    """

    for zone in ZONES:
        frac_x, frac_y, frac_w, frac_h = zone["rect"]

        left = frac_x * map_width
        top = frac_y * map_height
        width = frac_w * map_width
        height = frac_h * map_height

        if left <= world_x <= left + width and top <= world_y <= top + height:
            return zone["name"]

    return "Wilderness"


def get_zone_record_at(world_x, world_y, map_width, map_height):
    """Return the authored zone record and its world-space rectangle."""
    for zone in ZONES:
        frac_x, frac_y, frac_w, frac_h = zone["rect"]
        rect = (
            round(frac_x * map_width), round(frac_y * map_height),
            round(frac_w * map_width), round(frac_h * map_height),
        )
        if (rect[0] <= world_x <= rect[0] + rect[2]
                and rect[1] <= world_y <= rect[1] + rect[3]):
            return zone, rect
    return None, None
