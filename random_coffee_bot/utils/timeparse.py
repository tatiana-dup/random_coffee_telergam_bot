from datetime import datetime, timezone


class TimeParseError(ValueError):
    pass


def parse_iso_to_utc(value: str) -> datetime:
    """
    Принимает строку в ISO-8601:
      - '2025-10-15T08:00:00Z'            (UTC)
      - '2025-10-15T10:00:00+02:00'       (с любым смещением)
      - '2025-10-15T08:00:00'             (наивное время) -> трактуем как UTC
    Возвращает timezone-aware datetime в UTC.
    """
    if not value:
        raise TimeParseError("empty datetime string")

    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(s)
    except ValueError as e:
        raise TimeParseError(f"Invalid ISO-8601 datetime: {value!r}") from e

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)
