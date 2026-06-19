"""Project-specific exceptions."""


class AlphaDropperError(Exception):
    """Base exception for the application."""


class DependencyMissingError(AlphaDropperError):
    """Raised when an optional runtime dependency is missing."""


class ProcessingError(AlphaDropperError):
    """Raised when an image cannot be processed."""


class ValidationError(AlphaDropperError):
    """Raised when user input is invalid."""


class ResolumeApiError(AlphaDropperError):
    """Raised when local Resolume communication fails."""
