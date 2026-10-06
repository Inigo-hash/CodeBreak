"""Camera offsets in scaled screen pixels; map bounds remain world pixels."""
def camera_offset(center, viewport, map_size, zoom=2, follow_edges=False):
    x = center[0] * zoom - viewport[0] / 2
    y = center[1] * zoom - viewport[1] / 2
    if not follow_edges:
        x = max(0, min(x, map_size[0] * zoom - viewport[0]))
        y = max(0, min(y, map_size[1] * zoom - viewport[1]))
    # The renderer clears to black before blitting the map. Allowing negative
    # offsets supplies unlimited visual padding without resizing authored maps.
    return round(x), round(y)
