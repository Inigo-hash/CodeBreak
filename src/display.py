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


def _viewport(window_size):
    width, height = window_size
    scale = min(width / BASE_WIDTH, height / BASE_HEIGHT)
    scaled = (max(1, round(BASE_WIDTH * scale)), max(1, round(BASE_HEIGHT * scale)))
    return scale, ((width - scaled[0]) // 2, (height - scaled[1]) // 2), scaled


def window_to_virtual(position):
    if _window is None:
        return position
    scale, offset, scaled = _viewport(_window.get_size())
    x, y = position[0] - offset[0], position[1] - offset[1]
    if x < 0 or y < 0 or x >= scaled[0] or y >= scaled[1]:
        return (-1, -1)
    return (int(x / scale), int(y / scale))


def _present(*_args, **_kwargs):
    if _window is None or _canvas is None:
        return _original_flip()
    _window.fill(LETTERBOX_COLOR)
    _scale, offset, size = _viewport(_window.get_size())
    image = pygame.transform.smoothscale(_canvas, size)
    _window.blit(image, offset)
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
