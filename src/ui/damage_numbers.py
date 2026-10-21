"""Short-lived hit feedback anchored in world coordinates."""

from src.ui.theme import body_font


class DamageNumbers:
    def __init__(self, color=(255, 221, 117)):
        self.hits = []
        self.color = color

    def apply_damage(self, target, position, amount):
        """Show actual HP lost, excluding dodges and invulnerable hits."""
        before = target.hp
        if not target.take_damage(amount):
            return False
        self.add(position, before - target.hp)
        return True

    def add(self, position, damage):
        if damage > 0:
            self.hits.append((tuple(position), damage, 0.0))

    def update(self, dt):
        self.hits = [(pos, damage, age + dt) for pos, damage, age in self.hits
                     if age + dt < 0.85]

    def draw(self, screen, zoom, camera_x, camera_y):
        font = body_font(25, bold=True)
        for (x, y), damage, age in self.hits:
            text = font.render(f"-{damage:g}", True, self.color)
            shadow = font.render(f"-{damage:g}", True, (15, 12, 15))
            alpha = round(255 * min(1, (0.85 - age) / 0.3))
            text.set_alpha(alpha)
            shadow.set_alpha(alpha)
            rect = text.get_rect(midbottom=(round(x * zoom - camera_x),
                                           round(y * zoom - camera_y - 45 - age * 65)))
            screen.blit(shadow, rect.move(2, 2))
            screen.blit(text, rect)
