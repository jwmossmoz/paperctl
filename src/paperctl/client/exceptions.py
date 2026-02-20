"""Custom exceptions for SolarWinds Observability client."""


class SWOError(Exception):
    """Base exception for SolarWinds Observability errors."""


class AuthenticationError(SWOError):
    """Raised when authentication fails."""


class RateLimitError(SWOError):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int | None = None) -> None:
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s")


class APIError(SWOError):
    """Raised when API returns an error."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"API error {status_code}: {message}")
