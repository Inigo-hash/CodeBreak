"""Guard window close events throughout nested gameplay menus."""
import sys
import pygame


def has_unsaved_progress(current, saved):
    if saved is None:
        return True
    return any(value != saved.get(key) for key, value in current.items() if key != '_security')


class EventExitGuard:
    def __init__(self, source, confirm, owner_code):
        self.source, self.confirm, self.owner_code = source, confirm, owner_code
        self.busy = False

    def __call__(self, *args, **kwargs):
        events = self.source(*args, **kwargs)
        frame = sys._getframe(1)
        while frame and frame.f_code is not self.owner_code:
            frame = frame.f_back
        if frame is None:
            # Gameplay returned. Release its state and restore the normal pump.
            if pygame.event.get is self:
                pygame.event.get = self.source
            self.confirm = None
            return events
        if not self.busy and any(event.type == pygame.QUIT for event in events):
            self.busy = True
            try:
                allowed = self.confirm('exit the game')
            finally:
                self.busy = False
            if not allowed:
                return []
        return events


def install_exit_guard(confirm, owner_code):
    source = pygame.event.get
    if isinstance(source, EventExitGuard):
        source = source.source
    pygame.event.get = EventExitGuard(source, confirm, owner_code)
