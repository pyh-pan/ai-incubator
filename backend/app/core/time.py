from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return a naive UTC datetime for SQLAlchemy DateTime columns and JWT payloads."""
    return datetime.now(UTC).replace(tzinfo=None)
