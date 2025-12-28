PROMO HN MODE (TrustCheck)

Environment variables (Render -> Settings -> Environment):
- PROMO_MODE=1
- DEFAULT_MAX_RESULTS=30          # recommended for HN spike (fast + cheaper)
- CACHE_TTL_SECONDS=900           # 15 min cache for identical queries (huge savings)
- RATE_LIMIT_RPM=30               # per-IP requests/minute (set 0 to disable)

Rollback:
- Set PROMO_MODE=0 (or remove)
- DEFAULT_MAX_RESULTS=100
- CACHE_TTL_SECONDS=0
- RATE_LIMIT_RPM=0
