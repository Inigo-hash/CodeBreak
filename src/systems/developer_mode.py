"""Password-gated, session-only developer exploration mode."""
import hashlib
import pygame


_PASSWORD_SHA256 = "0f9a4ebc032766020b5beece7492a395b6fb7927a03deea99c73499e9fec1dc8"


def prompt_developer_password(screen):
    """Ask for the developer password without exposing its characters."""
    pygame.key.start_text_input()
    password = ""
    error = ""
    clock = pygame.time.Clock()
    overlay = screen.copy()
    width, height = screen.get_size()
    panel = pygame.Rect(0, 0, min(560, width - 40), 230)
    panel.center = (width // 2, height // 2)
    title_font = pygame.font.SysFont("arial", 28, bold=True)
    body_font = pygame.font.SysFont("arial", 19)
    small_font = pygame.font.SysFont("arial", 15)

    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.key.stop_text_input()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False
                    if event.key == pygame.K_RETURN:
                        digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
                        if digest == _PASSWORD_SHA256:
                            return True
                        error = "Incorrect password. Try again."
                        password = ""
                    elif event.key == pygame.K_BACKSPACE:
                        password = password[:-1]
                elif event.type == pygame.TEXTINPUT:
                    if len(password) < 64 and event.text.isprintable():
                        password += event.text

            screen.blit(overlay, (0, 0))
            shade = pygame.Surface((width, height), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 190))
            screen.blit(shade, (0, 0))
            pygame.draw.rect(screen, (25, 29, 39), panel, border_radius=14)
            pygame.draw.rect(screen, (207, 164, 83), panel, 2, border_radius=14)
            screen.blit(title_font.render("Developer Access", True, (245, 218, 160)),
                        (panel.x + 28, panel.y + 24))
            screen.blit(body_font.render("Enter developer password", True, (230, 230, 230)),
                        (panel.x + 28, panel.y + 78))
            field = pygame.Rect(panel.x + 28, panel.y + 112, panel.width - 56, 38)
            pygame.draw.rect(screen, (12, 15, 22), field, border_radius=6)
            pygame.draw.rect(screen, (115, 128, 150), field, 1, border_radius=6)
            masked = "•" * len(password)
            screen.blit(body_font.render(masked or "Password", True, (240, 240, 240) if password else (130, 135, 145)),
                        (field.x + 10, field.y + 8))
            hint = error or "Enter to confirm  •  Esc to cancel"
            screen.blit(small_font.render(hint, True, (235, 110, 105) if error else (175, 185, 200)),
                        (panel.x + 28, panel.y + 166))
            pygame.display.flip()
            clock.tick(30)
    finally:
        pygame.key.stop_text_input()


class DeveloperMode:
    def __init__(self):
        self.enabled = False

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled

    def request_toggle(self, screen):
        """Disable immediately, or require password before enabling."""
        if self.enabled:
            self.enabled = False
            return False
        if prompt_developer_password(screen):
            self.enabled = True
            return True
        return False


developer_mode = DeveloperMode()
