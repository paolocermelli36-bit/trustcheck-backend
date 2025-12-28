from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config import DEFAULT_MAX_RESULTS, RATE_LIMIT_RPM
from search_engine import google_search, GoogleSearchError
from reputation_engine import analyze

import time

app = FastAPI(title="TrustCheck Backend")

_last_call_ts = 0.0


class AnalyzeRequest(BaseModel):
    query: str
    maxResults: int | None = None


def _rate_limit():
    global _last_call_ts
    if RATE_LIMIT_RPM <= 0:
        return
    min_interval = 60.0 / float(RATE_LIMIT_RPM)
    now = time.time()
    wait = (_last_call_ts + min_interval) - now
    if wait > 0:
        time.sleep(wait)
    _last_call_ts = time.time()


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/analyze")
def analyze_endpoint(req: AnalyzeRequest):
    q = (req.query or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Missing query")

    max_results = int(req.maxResults or DEFAULT_MAX_RESULTS)
    max_results = max(10, min(100, max_results))

    _rate_limit()

    # fetch up to max_results (in batches of 10)
    collected = []
    start = 1
    while len(collected) < max_results:
        try:
            data = google_search(q, start_index=start, num_results=10)
        except GoogleSearchError as e:
            raise HTTPException(status_code=502, detail=str(e))

        batch = data.get("items", []) or []
        if not batch:
            break
        collected.extend(batch)

        start += 10
        if start > 100:  # API hard cap for pagination
            break

    google_results = {"items": collected[:max_results]}
    return analyze(q, google_results)