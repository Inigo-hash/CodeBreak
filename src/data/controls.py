"""
controls.py

Every key the game listens for, written down in one place.

Three screens tell the player what the controls are - the How To Play
panel, the tutorial's stage manual, and the Stage Manual tab of the
stage information panel - and each of them used to keep its own list.
They disagreed. How To Play offered "F - Interact" for a key nothing is
bound to, listed E as plain "Attack", and never mentioned the bag, the
map, the hotbar or the four panel tabs at all.

Every line below was read off the handler that actually consumes the
key, not off the old manuals:

    move / attack / dodge / bag / map / pause   src/screens/game.py
    hold-to-search                              src/screens/game.py
    hotbar slots                                the toolbar's handle_event
    I J K O panel tabs                          src/ui/stage_panel.py
    editor keys                                 src/ui/code_editor.py

Binding a new key in the game means adding it here as well, or the
manuals start drifting again - which is the whole reason this file
exists.

The F1/F2/F5/F6/F8 preview tools are intentionally kept out of the beginner
manual; F10 is the only function-key action needed for normal play.
"""


# Each section is (heading, [(key, what it does), ...]). The order here
# is the order the manuals print, so it runs from what a player needs in
# the first minute down to what they need once they are inside a
# challenge.
CONTROL_SECTIONS = [

    ("MOVING AND FIGHTING", [
        ("W A S D / Arrows", "Move"),
        ("E", "Attack with your sword"),
        ("Left Shift", "Dodge"),
    ]),

    # Actions are kept short on purpose: the manuals print them in a
    # narrow second column beside the key, and anything much longer than
    # this wraps onto a second row and breaks the table.
    ("SEARCHING AND ITEMS", [
        ("Hold E", "Search a nearby object"),
        ("B", "Open your bag"),
        ("1 - 5 / Wheel", "Pick a hotbar slot"),
    ]),

    ("SCREENS", [
        ("M", "Island map"),
        ("I", "Stage manual"),
        ("J", "Enemies you have met"),
        ("K", "Items you have found"),
        ("O", "Objectives"),
        ("ESC", "Pause"),
        ("F10", "Mute / unmute music"),
    ]),

    ("IN THE CODE EDITOR", [
        ("Ctrl + Z / Y", "Undo / redo"),
        ("Ctrl + C / X / V", "Copy, cut, paste"),
        ("Tab", "Indent"),
        ("ESC", "Close the editor"),
    ]),

]


# The one piece of the scheme a table cannot express: E is context
# sensitive. Standing next to something searchable turns E into a search
# and takes the attack away, which reads as a broken attack key if
# nobody says so out loud.
CONTROL_NOTES = [
    "E attacks - but next to a searchable object, hold E to search instead.",
    "Run and Submit inside the editor are buttons you click.",
]


# Everything that happens out in the world, as flat (key, action) pairs.
# The stage manual in src/data/stages.py points at this rather than
# repeating it, so a stage's manual can never contradict How To Play.
WORLD_CONTROLS = [
    row
    for heading, rows in CONTROL_SECTIONS
    if heading != "IN THE CODE EDITOR"
    for row in rows
]


EDITOR_CONTROLS = [
    row
    for heading, rows in CONTROL_SECTIONS
    if heading == "IN THE CODE EDITOR"
    for row in rows
]


def control_lines(sections=None):
    """
    The control scheme as flat "KEY  -  Action" strings.

    For anywhere that prints a plain list of lines rather than a table
    of key/action columns.
    """

    chosen = CONTROL_SECTIONS if sections is None else [
        (heading, rows) for heading, rows in CONTROL_SECTIONS
        if heading in sections
    ]

    return [
        f"{key}  -  {action}"
        for _, rows in chosen
        for key, action in rows
    ]
