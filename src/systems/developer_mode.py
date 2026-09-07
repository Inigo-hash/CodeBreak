"""Session-only exploration switch; never stored as campaign progress."""


class DeveloperMode:
    def __init__(self):
        self.enabled = False

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled


developer_mode = DeveloperMode()
