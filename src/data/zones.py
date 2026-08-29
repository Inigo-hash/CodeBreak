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
F6 prints the player's current fractional position for placement work.
"""

ZONES = [
    {
        "name": "The Corrupted Core",
        "rect": (
            0.363830,
            0.187500,
            0.299574,
            0.200000
        ),
        "is_boss_zone": True,
    },

    {
        "name": "Whispering Thicket",
        "rect": (
            0.241277,
            0.206250,
            0.108936,
            0.112500
        ),
    },

    {
        "name": "Sunfall Grove",
        "rect": (
            0.745106,
            0.187500,
            0.095319,
            0.112500
        ),
    },

    {
        "name": "Mosswood Hollow",
        "rect": (
            0.193617,
            0.312500,
            0.095319,
            0.100000
        ),
    },

    {
        "name": "Ferngate Clearing",
        "rect": (
            0.254894,
            0.437500,
            0.081702,
            0.093750
        ),
    },

    {
        "name": "Stonebrook Rise",
        "rect": (
            0.683830,
            0.412500,
            0.074894,
            0.100000
        ),
    },

    {
        "name": "Driftwood Crossing",
        "rect": (
            0.588511,
            0.512500,
            0.088511,
            0.087500
        ),
    },

    {
        "name": "Hollow Pine Thicket",
        "rect": (
            0.751915,
            0.475000,
            0.088511,
            0.125000
        ),
    },

    {
        "name": "Willowmere Fields",
        "rect": (
            0.159574,
            0.675000,
            0.149787,
            0.137500
        ),
    },

    {
        "name": "Amber Hollow",
        "rect": (
            0.677021,
            0.656250,
            0.163404,
            0.156250
        ),
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
