"""Custom exceptions for codesnap."""


class CodesnapError(Exception):
    """Base exception for codesnap errors."""


class DependencyMissingError(CodesnapError):
    """Raised when a required system utility is missing."""


class CaptureCancelledError(CodesnapError):
    """Raised when user cancels screen selection (e.g. pressed Esc)."""


class CaptureFailedError(CodesnapError):
    """Raised when screenshot capture fails."""


class OCRError(CodesnapError):
    """Raised when OCR extraction fails."""
