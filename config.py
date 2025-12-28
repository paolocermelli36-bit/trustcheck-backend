import os


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)).strip())
    except Exception:
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
GOOGLE_CX_ID = os.getenv("GOOGLE_CX_ID", "").strip()

DEFAULT_MAX_RESULTS = _env_int("DEFAULT_MAX_RESULTS", 30)  # frontend chiede 30
CACHE_TTL_SECONDS = _env_int("CACHE_TTL_SECONDS", 3600)
RATE_LIMIT_RPM = _env_int("RATE_LIMIT_RPM", 60)

PROMO_MODE = _env_bool("PROMO_MODE", True)