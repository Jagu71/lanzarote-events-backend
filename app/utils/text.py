import hashlib
import re
import unicodedata


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return clean or "evento"


def compact_spaces(value: str | None) -> str | None:
    if value is None:
        return None
    return re.sub(r"\s+", " ", value).strip()


def build_fingerprint(*parts: str | None) -> str:
    normalized = "|".join((compact_spaces(part) or "").lower() for part in parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
