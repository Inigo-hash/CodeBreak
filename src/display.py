"""Fixed-resolution presentation with aspect-safe scaling and mouse mapping."""

import pygame

BASE_WIDTH = 1920
BASE_HEIGHT = 1080
LETTERBOX_COLOR = (8, 9, 13)

_window = None
_canvas = None
_original_flip = pygame.display.flip
_original_update = pygame.display.update
_original_get_pos = pygame.mouse.get_pos
_original_event_get = pygame.event.get

# The scaled frame is the same size every frame; allocating a fresh one per
# present churned several megabytes per frame through the allocator.
_scaled_buffer = None
# _viewport is called once per present and again for every mouse event, and
# the window size only changes on a resize.
_viewport_cache = None


def _viewport(window_size):
    global _viewport_cache
    if _viewport_cache is not None and _viewport_cache[0] == window_size:
        return _viewport_cache[1]
    width, height = window_size
    scale = min(width / BASE_WIDTH, height / BASE_HEIGHT)
    scaled = (max(1, round(BASE_WIDTH * scale)), max(1, round(BASE_HEIGHT * scale)))
    result = (scale, ((width - scaled[0]) // 2, (height - scaled[1]) // 2), scaled)
    _viewport_cache = (window_size, result)
    return result


def window_to_virtual(position):
    if _window is None:
        return position
    scale, offset, scaled = _viewport(_window.get_size())
    x, y = position[0] - offset[0], position[1] - offset[1]
    if x < 0 or y < 0 or x >= scaled[0] or y >= scaled[1]:
        return (-1, -1)
    return (int(x / scale), int(y / scale))


def _present(*_args, **_kwargs):
    global _scaled_buffer
    if _window is None or _canvas is None:
        return _original_flip()

    window_size = _window.get_size()
    _scale, offset, size = _viewport(window_size)

    if size == (BASE_WIDTH, BASE_HEIGHT):
        # A window already at the canvas size needs no resample. The
        # unconditional smoothscale spent a full-frame CPU resample
        # (~2.5ms at 1080p) producing a pixel-for-pixel copy of its input.
        _window.blit(_canvas, offset)
    else:
        if _scaled_buffer is None or _scaled_buffer.get_size() != size:
            _scaled_buffer = pygame.Surface(size).convert()
        pygame.transform.smoothscale(_canvas, size, _scaled_buffer)
        _window.blit(_scaled_buffer, offset)

    # Only the letterbox bars need painting - the viewport was just fully
    # overwritten above. Clearing the whole window first wrote two million
    # pixels that the blit immediately covered.
    #
    # Tested against the window size rather than the offset: rounding the
    # scaled size can leave a one-pixel seam with no offset at all (a
    # 1366x768 window scales to 1365x768, offset 0), and that seam still
    # has to be painted or it shows whatever the last frame left there.
    if size != window_size:
        right = offset[0] + size[0]
        bottom = offset[1] + size[1]
        _window.fill(LETTERBOX_COLOR, (0, 0, window_size[0], offset[1]))
        _window.fill(
            LETTERBOX_COLOR,
            (0, bottom, window_size[0], window_size[1] - bottom),
        )
        _window.fill(LETTERBOX_COLOR, (0, offset[1], offset[0], size[1]))
        _window.fill(
            LETTERBOX_COLOR,
            (right, offset[1], window_size[0] - right, size[1]),
        )

    _original_flip()


def _events(*args, **kwargs):
    events = _original_event_get(*args, **kwargs)
    converted = []
    for event in events:
        if hasattr(event, "pos"):
            values = dict(event.dict)
            values["pos"] = window_to_virtual(event.pos)
            event = pygame.event.Event(event.type, values)
        converted.append(event)
    return converted


def create_display(fullscreen=True):
    """Create the real desktop window and return the 1920x1080 game canvas."""
    global _window, _canvas
    flags = pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE
    size = (0, 0) if fullscreen else (1280, 720)
    _window = pygame.display.set_mode(size, flags)
    _canvas = pygame.Surface((BASE_WIDTH, BASE_HEIGHT)).convert()
    pygame.display.flip = _present
    pygame.display.update = _present
    pygame.mouse.get_pos = lambda: window_to_virtual(_original_get_pos())
    pygame.event.get = _events
    return _canvas
