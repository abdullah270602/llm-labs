


class WorkspaceLimitExceeded(Exception):
    def __init__(self, message: str = "Cannot have more than 5 workspaces"):
        self.message = message
        super().__init__(self.message)

class MovementError(Exception):
    def __init__(self, message: str = "Error moving item"):
        self.message = message
        super().__init__(self.message)