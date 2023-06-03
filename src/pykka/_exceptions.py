__all__ = ["ActorDeadError", "Timeout"]


class ActorDeadError(Exception):
    """Exception raised when trying to use a dead or unavailable actor."""


class Timeout(Exception):
    """Exception raised at future timeout."""
