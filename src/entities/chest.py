"""Persistent, map-authored bonus-time chests."""

import pygame


class Chest:
    """A searchable chest that grants time or triggers a one-shot trap."""

    def __init__(self, rect, reward_seconds=0, trap_seconds=0, opened=False):
        self.rect = pygame.Rect(rect)
        self.reward_seconds = max(0, int(reward_seconds or 0))
        self.trap_seconds = max(0, int(trap_seconds or 0))
        self.opened = bool(opened)

    def open(self, current_bonus_time):
        """Resolve the chest once and return the new timer plus UI message."""

        current = max(0, int(current_bonus_time or 0))
        if self.opened:
            return current, "This chest has already been opened.", False

        self.opened = True
        if self.trap_seconds:
            updated = max(0, current - self.trap_seconds)
            lost = current - updated
            if lost:
                message = f"Trap! You lost {lost} seconds of bonus time."
            else:
                message = "Trap! It snapped shut, but you had no bonus time to lose."
            return updated, message, True

        reward = self.reward_seconds or 30
        return current + reward, f"Chest opened: +{reward} seconds bonus time!", True

    def draw(self, surface, zoom, camera_x, camera_y):
        """Draw a compact gold-trimmed chest at its world-space rectangle."""

        rect = pygame.Rect(
            round(self.rect.x * zoom - camera_x),
            round(self.rect.y * zoom - camera_y),
            max(18, round(self.rect.width * zoom)),
            max(16, round(self.rect.height * zoom)),
        )
        if not rect.colliderect(surface.get_rect()):
            return

        outline = (39, 23, 15)
        wood = (91, 52, 28) if not self.opened else (62, 42, 30)
        wood_light = (132, 78, 36) if not self.opened else (82, 58, 42)
        metal = (218, 170, 62) if not self.opened else (116, 105, 84)
        lid_height = max(6, rect.height // 3)
        body = pygame.Rect(rect.left, rect.top + lid_height - 1,
                           rect.width, rect.height - lid_height + 1)
        lid = pygame.Rect(rect.left, rect.top, rect.width, lid_height + 2)

        if self.opened:
            lid.move_ip(0, -max(3, rect.height // 7))
        pygame.draw.rect(surface, outline, body, border_radius=3)
        pygame.draw.rect(surface, wood, body.inflate(-3, -3), border_radius=2)
        pygame.draw.rect(surface, outline, lid, border_radius=4)
        pygame.draw.rect(surface, wood_light, lid.inflate(-3, -3), border_radius=3)
        pygame.draw.line(surface, metal, (rect.left + 3, body.top + 2),
                         (rect.right - 4, body.top + 2), 3)
        lock = pygame.Rect(0, 0, max(5, rect.width // 7), max(6, rect.height // 5))
        lock.midtop = (rect.centerx, body.top)
        pygame.draw.rect(surface, metal, lock, border_radius=2)
