"""Common Postgres helpers: JSON-safe row conversion, uuid short IDs."""
import uuid
from datetime import datetime, timezone


def short_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def json_safe(row) -> dict:
    """Convert an asyncpg Record (or dict) into a JSON-serialisable dict."""
    if row is None:
        return None
    d = dict(row) if not isinstance(row, dict) else dict(row)
    for k, v in list(d.items()):
        if hasattr(v, "isoformat"):
            d[k] = v.isoformat()
        elif isinstance(v, uuid.UUID):
            d[k] = str(v)
    return d


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
