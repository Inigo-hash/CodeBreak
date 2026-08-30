"""
items.py

Everything the player can find, search or talk to, as pure data. This
backs the "Items & Interactables" tab of the stage info panel.

Three kinds of entry live here, told apart by the ``kind`` field:

    "interactable"  - world objects you hold E on (barrels, hay, vases...)
    "collectible"   - things you pick up and keep in the bag
    "npc"           - characters you can talk to

Interactable entries carry an ``action`` that matches the ``actions``
custom property set on the object in Tiled (see the Object Layer in
assets/map/tmx/basic.tmx, which currently uses search_barrel,
search_burrow, search_crate, search_hay and search_vase). That shared
string is the join between the map and this file: when the player
finishes searching something, game.py turns the action back into an item
id through item_id_for_action() and marks it discovered.

Because of that link, renaming an action in Tiled means renaming it here
too - otherwise the object still works in-game, it just stops recording
itself in the panel.
"""

ITEMS = {

    # -- Interactables ------------------------------------------------------
    # These are all searchable containers. game.py currently reports every
    # one of them as empty; the descriptions below say what each is *for*,
    # so the text still holds up once loot tables exist.

    "barrel": {
        "id": "barrel",
        "name": "Wooden Barrel",
        "kind": "interactable",
        "action": "search_barrel",
        "description":
            "A storage barrel left behind by whoever lived here. Most are "
            "empty, but they are the first place worth checking.",
        "hint": "Hold E to search.",
    },

    "burrow": {
        "id": "burrow",
        "name": "Burrow",
        "kind": "interactable",
        "action": "search_burrow",
        "description":
            "A hole dug into the earth. Duwende keep what they take down "
            "one of these, so a burrow is rarely far from its owner.",
        "hint": "Hold E to search. Watch your back while you do.",
    },

    "crate": {
        "id": "crate",
        "name": "Supply Crate",
        "kind": "interactable",
        "action": "search_crate",
        "description":
            "A nailed-shut crate. Sturdier than a barrel, and usually put "
            "somewhere on purpose rather than left lying around.",
        "hint": "Hold E to search.",
    },

    "chest": {
        "id": "chest",
        "name": "Treasure Chest",
        "kind": "interactable",
        "action": "search_chest",
        "description": (
            "A reinforced chest wired into the island's broken timer. Some "
            "grant bonus time; corrupted ones spring a time-draining trap."
        ),
        "hint": "Hold E to open it. Each chest can resolve only once.",
    },

    "hay": {
        "id": "hay",
        "name": "Hay Pile",
        "kind": "interactable",
        "action": "search_hay",
        "description":
            "Loose hay. Easy to hide something small in, which is exactly "
            "why it is worth digging through.",
        "hint": "Hold E to search.",
    },

    "vase": {
        "id": "vase",
        "name": "Clay Vase",
        "kind": "interactable",
        "action": "search_vase",
        "description":
            "An old clay vase. Whatever it was made to hold, it has had a "
            "long time to lose it.",
        "hint": "Hold E to search.",
    },

    # -- Characters ---------------------------------------------------------

    "mang_tahimik": {
        "id": "mang_tahimik",
        "name": "Mang Tahimik",
        "kind": "npc",
        "portrait": "assets/images/characters/mang_tahimik/portrait.png",
        "description":
            "The quiet keeper of the island. He explains what the code "
            "terminals are for and points you at the next thing worth "
            "learning.",
        "hint": "Talk to him when you are stuck on a challenge.",
    },

}


# action string (from Tiled) -> item id. Built once at import time so the
# per-frame interaction code in game.py is a plain dict lookup.
_ITEM_BY_ACTION = {
    entry["action"]: item_id
    for item_id, entry in ITEMS.items()
    if entry.get("action")
}


def get_item(item_id):
    """One item entry, or None when the id is unknown."""

    return ITEMS.get(item_id)


def item_id_for_action(action):
    """
    Turn a Tiled ``actions`` value (e.g. "search_vase") into the item id
    it describes (e.g. "vase"), or None if no entry claims that action.

    None is the normal answer for map objects that have not been written
    up here yet, so callers should treat it as "nothing to record".
    """

    return _ITEM_BY_ACTION.get(action)
